"""OIDC Discovery 拉取 + 内存 TTL 缓存。

职责
----
在 sample 需要 issuer/jwks_uri 时（demo / serve-orders 入口），从
``{IDAAS_ORIGIN}/api/v2/iauths_system/oauth2/.well-known/openid-configuration``
拉一次 OIDC discovery 文档，解析出 ``issuer`` 与 ``jwks_uri`` 字段，回填到
config 的空位（``ORDER_SERVICE_ISSUER`` / ``ORDER_SERVICE_JWKS_URI``）。

设计约束
--------
- **不做持久化缓存**（``.tokens/discovery.json``）：sample 主要是短命 CLI 进程，
  每次拉一次的成本可以接受；serve-orders 长驻进程由内存 TTL 缓存兜住。持久化
  会引入失效/陈旧/并发写等额外复杂度，对本 sample 属过度设计。
- **绝不进 ``derive_defaults``**：``derive_defaults`` 必须保持纯离线（无网络
  副作用），否则会破坏 172 个离线单测，且让 ``login``/``--check`` 平白多一次
  网络往返。discovery 只在 ``apply_discovery`` 里被显式调用，由 ``sample.py``
  在 demo/serve-orders 入口触发。
- **显式值永远优先**：``apply_discovery`` 只填空位（``env.is_placeholder`` 判定），
  已有值的 ``ORDER_SERVICE_ISSUER``/``ORDER_SERVICE_JWKS_URI`` 一律不覆盖。

复用范式
--------
- ``urllib.request.build_opener`` + ``lib.rpc.ssl_context()``：镜像 ``orders/verify.py``
  ``default_fetch_jwks`` 的共享 SSL 上下文（含 certifi 兜底，macOS Python 3.12
  无系统 CA 场景下必需），但额外挂载自定义重定向 handler（见「安全校验」第 4 条）。
- ``DiscoveryCache``：镜像 ``orders/verify.py:88-134`` ``JwksCache`` 的
  TTL(此处取 3600s，discovery 文档比 JWKS 更稳定) + ``threading.Lock`` +
  ``force_refresh`` 范式。
- 可注入 ``fetch_func``：沿用 ``verify.py`` 的离线测试友好风格；注入函数**绝不会被
  调用两次**（``inspect.signature`` + ``Signature.bind`` 做真实可绑定性预判，
  而非只数参数个数），其内部异常按原样传播；签名与 ``(url)``/``(url, timeout)``
  契约均不兼容时收敛为 ``DiscoveryError``（不让裸 TypeError 逃逸）。

安全校验（信任边界）
--------------------
discovery 拉到的 ``issuer``/``jwks_uri`` 会被 ``writeback_env`` 持久化进 ``.env``，并被
塞进 ``orders/server.py`` 的 ``TokenVerifier``——在**每次 Bearer 验签**时由 ``JwksCache``
向 ``jwks_uri`` 发起服务端外呼。改造前这两个值由人工从控制台抄录（人在环内），改造后
程序自动信任远端内容，信任边界被放宽，故补齐五道校验：

1. ``IDAAS_ORIGIN`` 入参用 ``urlsplit`` 校验（scheme=https、netloc/hostname 非空、端口
   为数字、不含路径），并以 ``netloc`` 重建 URL（修复裸 ``rstrip("/")`` 把 ``https://``
   削成 ``https:`` 的畸形拼接）。
2. ``fetch_func`` 用 ``Signature.bind`` **可绑定性预判**决定调用形态，绝不二次
   调用、不吞内部异常；两种契约均不可绑定时抛 ``DiscoveryError``。
3. ``_default_fetch_discovery`` 的异常白名单补齐 ``http.client.HTTPException``（非 OSError
   子类）与 ``ValueError``（含 UnicodeDecodeError），一律包装成 ``DiscoveryError``（整条
   链路唯一接盘类型）；``decode(errors="replace")`` 让非法编码落到「不是合法 JSON」分支。
4. 自定义 ``_HttpsOnlyRedirectHandler`` 阻止 https→http 重定向降级（CPython 默认白名单
   ``('http','https','ftp','')`` 允许降级），并校验最终 URL 仍为 https 且 host 与
   ``IDAAS_ORIGIN`` 一致（防跨域重定向 / SSRF）。
5. ``get_issuer_jwks`` 对响应做同源校验：``jwks_uri`` 必须 https，``issuer``/``jwks_uri``
   必须与 ``IDAAS_ORIGIN`` **同源**（``_normalize_origin`` 归一后的 ``(host, port)``
   比较：显式 ``:443``、末尾点 FQDN、IDNA punycode、IPv6 字面量等语义等价写法
   不再被字面比较误杀；跨 host、非 https、userinfo 嵌入仍拒绝；防 SSRF / issuer
   混淆）。**不要求 issuer 与 IDAAS_ORIGIN 字符串全等**——真实部署 issuer 常带路径
   前缀，RFC 8414 §3.3 的一致性以「同 scheme + 同 host」为准，严格全等会误杀正常环境。
"""

import http.client
import inspect
import json
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, Optional, Tuple

from . import env as env_mod

try:
    # 复用 lib/rpc.py 的共享 SSL 上下文（含 certifi 兜底）：镜像 orders/verify.py:22-29
    # 的可选 import 隔离范式。lib/rpc.py 缺失时（不该发生，同包内）回退到默认上下文。
    from .rpc import ssl_context as _shared_ssl_context
except ImportError:  # pragma: no cover - 同包内不该触发
    _shared_ssl_context = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

# discovery 文档相对路径（契约由 env.template L81 / control_plane.py L170 /
# env.py L122 多处印证：GET {IDAAS_ORIGIN}/api/v2/iauths_system/oauth2/
# .well-known/openid-configuration）
DISCOVERY_PATH = "/api/v2/iauths_system/oauth2/.well-known/openid-configuration"

# discovery 内存缓存 TTL（秒）：3600s。discovery 文档比 JWKS 更稳定（issuer/
# jwks_uri 变更频率极低，通常只在服务侧重大迁移时才变），TTL 取 1 小时。
DISCOVERY_CACHE_TTL = 3600

# 网络超时（秒）：默认 10s，与 orders/verify.py:64 default_fetch_jwks 一致
DEFAULT_TIMEOUT = 10


# ---------------------------------------------------------------------------
# 异常
# ---------------------------------------------------------------------------


class DiscoveryError(Exception):
    """OIDC discovery 拉取或解析失败。message 内自带排查指引。"""


# ---------------------------------------------------------------------------
# 网络层：SSL 上下文 / 防降级 opener / 默认 fetch
# ---------------------------------------------------------------------------


def _get_ssl_context() -> ssl.SSLContext:
    """返回**证书校验开启**的 SSL 上下文（复用 ``lib.rpc.ssl_context``，含 certifi 兜底）。

    安全红线：绝不设置 ``check_hostname=False`` 或 ``verify_mode=CERT_NONE``——
    discovery 文档驱动订单服务的 JWKS 外呼，TLS 证书校验是防在途篡改的第一道闸。
    ``lib.rpc`` 缺失时（同包内不应发生）回退到 ``ssl.create_default_context()``
    （同样默认开启校验）。
    """
    if _shared_ssl_context is not None:
        return _shared_ssl_context()
    return ssl.create_default_context()  # pragma: no cover - 同包内不应触发


class _HttpsOnlyRedirectHandler(urllib.request.HTTPRedirectHandler):
    """重定向防降级：阻止 ``https`` → 非 ``https`` 的重定向。

    CPython ``HTTPRedirectHandler.http_error_302`` 的 scheme 白名单是
    ``('http', 'https', 'ftp', '')``，**明确允许 https → http 降级**。discovery
    文档的 ``jwks_uri`` 会驱动订单服务每次验签的外呼，若最后一跳被降级为明文
    HTTP，可被在途篡改（把 jwks_uri 换成攻击者主机）。故重写 ``redirect_request``：
    原请求为 https 而目标非 https → 抛 :class:`DiscoveryError`；其余交 super() 标准处理。
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        original = getattr(req, "full_url", "") or ""
        if original.startswith("https://") and not newurl.startswith("https://"):
            raise DiscoveryError(
                "OIDC discovery 重定向试图从 HTTPS 降级到非 HTTPS（{} → {}），已阻止"
                "以防在途篡改。请检查 IDAAS_ORIGIN 与 IDaaS 实例配置。".format(original, newurl)
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _build_opener() -> urllib.request.OpenerDirector:
    """构造仅走 https、防降级重定向的 opener（证书校验保持开启）。

    ``build_opener`` 见到自定义 ``HTTPRedirectHandler`` 子类会跳过默认重定向
    handler；``HTTPSHandler(context=...)`` 复用 ``lib.rpc`` 的共享 SSL 上下文。
    """
    return urllib.request.build_opener(
        _HttpsOnlyRedirectHandler(),
        urllib.request.HTTPSHandler(context=_get_ssl_context()),
    )


def _default_fetch_discovery(url: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """默认 discovery 拉取：防降级 opener GET（镜像 ``orders/verify.py:76-85`` 范式）。

    - 复用 ``lib.rpc.ssl_context()``（含 certifi 兜底，证书校验保持开启）；
    - 自定义 opener 阻止 https→http 重定向降级，并校验最终 URL 仍为 https 且
      host 与入参一致（防跨域重定向 / SSRF）；
    - 网络异常 / HTTP 4xx-5xx / ``http.client.HTTPException``（含 IncompleteRead /
      BadStatusLine，**不是 OSError 子类**）/ ``ValueError``（含 UnicodeDecodeError）
      → 一律包装成 :class:`DiscoveryError`（整条链路唯一接盘类型，``control_plane.py``
      与 ``sample.py`` 的统一错误出口只认它）。
    """
    opener = _build_opener()
    try:
        expected_host = urllib.parse.urlsplit(url).hostname
        req = urllib.request.Request(
            url, headers={"accept": "application/json"}, method="GET"
        )
        with opener.open(req, timeout=timeout) as resp:
            # errors="replace"：网关返回 GBK/latin-1 错误页时不让 decode 抛
            # UnicodeDecodeError，而是替换非法字节，落到下面「不是合法 JSON」分支。
            body = resp.read().decode("utf-8", errors="replace")
            final_url = resp.geturl()
    except urllib.error.HTTPError as exc:
        raise DiscoveryError(
            "拉取 OIDC discovery 失败：HTTP {} （url={}）。请检查 IDAAS_ORIGIN 是否"
            "正确、实例是否已启用 OAuth 服务，或该 URL 是否需要白名单放行。".format(
                exc.code, url
            )
        ) from None
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise DiscoveryError(
            "拉取 OIDC discovery 网络错误：{} （url={}）。请检查网络连通性、代理设置、"
            "或 IDAAS_ORIGIN 拼写。".format(reason, url)
        ) from None
    except (TimeoutError, ConnectionError, OSError) as exc:
        raise DiscoveryError(
            "拉取 OIDC discovery 连接超时/中断：{} （url={}）。可增大 timeout 或"
            "检查网络。".format(exc, url)
        ) from None
    except (http.client.HTTPException, ValueError, UnicodeError) as exc:
        # HTTPException（IncompleteRead/BadStatusLine/InvalidURL）不是 OSError 子类；
        # ValueError（含 UnicodeDecodeError）来自畸形响应——两者都会绕过上面的网络
        # 异常包装而裸逃逸，必须在此兜住，否则 DiscoveryError 接盘链断裂。
        raise DiscoveryError(
            "拉取 OIDC discovery 失败：{}（{}）（url={}）。请检查 IDAAS_ORIGIN 格式"
            "是否为 https://<host>[:<数字端口>]，以及响应是否为 UTF-8 编码的合法 JSON。".format(
                type(exc).__name__, exc, url
            )
        ) from None
    except DiscoveryError:
        # 先放行 DiscoveryError 自身（如 _HttpsOnlyRedirectHandler 在 opener.open
        # 内部抛出的降级拦截）——避免被下面的 catch-all 二次包装丢失原始语义。
        raise
    except Exception as exc:
        # 契约外异常兜底（O5）：上面的捕获矩阵已覆盖 urllib/ssl/http.client 的
        # 常见异常，但裸 RuntimeError 等契约外异常若逃逸会变成裸栈（DiscoveryError
        # 接盘链断裂）。防御性包装成 DiscoveryError，保留异常类型名 + 原因 + url +
        # 既有指引文案，让整条链路仍只有 DiscoveryError 一种接盘类型。
        raise DiscoveryError(
            "拉取 OIDC discovery 失败：{}（{}）（url={}）。请检查 IDAAS_ORIGIN 格式"
            "是否为 https://<host>[:<数字端口>]，以及响应是否为 UTF-8 编码的合法 JSON。".format(
                type(exc).__name__, exc, url
            )
        ) from None
    # 重定向后置校验：最终 URL 必须仍是 https，且 host 与 IDAAS_ORIGIN 一致。
    # （_HttpsOnlyRedirectHandler 已阻止 https→http 降级，此处再防 https→https 跨域。）
    if not final_url.startswith("https://"):
        raise DiscoveryError(
            "OIDC discovery 最终 URL 非 https（{}，原始 url={}）。已阻止以防在途篡改。".format(
                final_url, url
            )
        )
    final_host = urllib.parse.urlsplit(final_url).hostname
    if final_host != expected_host:
        raise DiscoveryError(
            "OIDC discovery 重定向后 host 改变（最终 host={}，期望={}，url={}）。已阻止"
            "以防跨域重定向 / SSRF。请检查 IDAAS_ORIGIN 配置。".format(
                final_host, expected_host, url
            )
        )
    try:
        data = json.loads(body)
    except ValueError as exc:
        raise DiscoveryError(
            "OIDC discovery 响应不是合法 JSON：{} （url={}）。可能是网关返回了 HTML"
            " 错误页——请打开该 URL 手动确认。".format(exc, url)
        ) from None
    if not isinstance(data, dict):
        raise DiscoveryError(
            "OIDC discovery 响应顶层结构非 JSON 对象（url={}）。".format(url)
        )
    return data


# IDAAS_ORIGIN 非法时的统一指引文案
_ORIGIN_GUIDE = "IDAAS_ORIGIN 须为 https://<host>[:<数字端口>]，不含路径"


def _build_discovery_url(idaas_origin: str) -> str:
    """拼接 discovery 完整 URL；``idaas_origin`` 非法一律抛 :class:`DiscoveryError`。

    用 ``urllib.parse.urlsplit`` 校验（不再只 ``startswith("https://")``）：
    - scheme 必须为 ``https``（discovery 拉取强制走 TLS）；
    - ``netloc`` / ``hostname`` 非空——拦截 ``https://`` 这类输入：裸 ``rstrip("/")``
      会把它削成 ``https:`` 再拼出畸形 URL；
    - 端口（若存在）必须为数字——拦截 ``https://host:notaport``：它会让
      ``http.client`` 抛 ``InvalidURL: nonnumeric port``（不是 OSError 子类，
      会绕过网络异常包装）；
    - 不含路径——``IDAAS_ORIGIN`` 是 IDaaS 实例域名根，discovery 路径由本函数拼接。

    重建用 ``netloc`` 而非裸 ``rstrip("/")``：天然去尾斜杠、保留端口、丢弃
    query/fragment，彻底规避把 ``https://`` 削成 ``https:`` 的拼接 bug。
    """
    if not idaas_origin or env_mod.is_placeholder(idaas_origin):
        raise DiscoveryError(
            "IDAAS_ORIGIN 未配置或为占位符。请在 sample .env 填 IDAAS_ORIGIN（如 "
            "`https://xxx.cloud-idaas.com`），或直接显式填 ORDER_SERVICE_ISSUER "
            "与 ORDER_SERVICE_JWKS_URI（跳过 discovery 自动拉取）。"
        )
    origin = idaas_origin.strip()
    try:
        parts = urllib.parse.urlsplit(origin)
    except ValueError as exc:
        # 如 https://[::1（畸形 IPv6）→ urlsplit 抛 ValueError: Invalid IPv6 URL
        raise DiscoveryError(
            "IDAAS_ORIGIN={!r} 不是合法 URL（{}）。{}".format(idaas_origin, exc, _ORIGIN_GUIDE)
        ) from None
    if parts.scheme != "https":
        raise DiscoveryError(
            "IDAAS_ORIGIN={!r} 不是 https 地址。{}（discovery 拉取强制走 TLS，IDaaS "
            "实例域名根须以 https:// 开头）。".format(idaas_origin, _ORIGIN_GUIDE)
        )
    if not parts.netloc:
        raise DiscoveryError(
            "IDAAS_ORIGIN={!r} 缺少主机名（netloc 为空）。{}".format(idaas_origin, _ORIGIN_GUIDE)
        )
    # S1：拒绝 userinfo 嵌入（user:password@host）——IDAAS_ORIGIN 是实例域名根，
    # 不应携带凭据；且同源校验只看 host，userinfo 可构造视觉混淆（钓鱼面）。
    try:
        _userinfo = (parts.username, parts.password)
    except ValueError as exc:
        raise DiscoveryError(
            "IDAAS_ORIGIN={!r} 的主机/端口非法（{}）。{}".format(idaas_origin, exc, _ORIGIN_GUIDE)
        ) from None
    if _userinfo[0] is not None or _userinfo[1] is not None:
        raise DiscoveryError(
            "IDAAS_ORIGIN={!r} 不应包含 user:password@ 形式的用户信息。{}"
            "（实例域名根只填主机与可选端口；嵌入凭据会形成视觉混淆，已拒绝）。".format(
                idaas_origin, _ORIGIN_GUIDE
            )
        )
    try:
        host = parts.hostname
        _port = parts.port  # 访问即触发端口校验：非数字端口（:notaport）抛 ValueError
    except ValueError as exc:
        raise DiscoveryError(
            "IDAAS_ORIGIN={!r} 的主机/端口非法（{}）。{}".format(idaas_origin, exc, _ORIGIN_GUIDE)
        ) from None
    # O4：收紧端口范围到 1–65535。``parts.port`` 只校验「可转数字 + 0–65535」，
    # 会放行 ``:0``（保留端口，不可实际连接）；越界（如 ``:70000``）已由上面
    # 的 ValueError 分支兜住。此处显式拒绝 0 与任何越界值，避免畸形 origin 流到下游。
    if _port is not None and not (1 <= _port <= 65535):
        raise DiscoveryError(
            "IDAAS_ORIGIN={!r} 的端口越界（port={}，须在 1–65535）。{}".format(
                idaas_origin, _port, _ORIGIN_GUIDE
            )
        )
    if not host:
        raise DiscoveryError(
            "IDAAS_ORIGIN={!r} 缺少主机名。{}".format(idaas_origin, _ORIGIN_GUIDE)
        )
    if parts.path not in ("", "/"):
        raise DiscoveryError(
            "IDAAS_ORIGIN={!r} 不应包含路径（path={!r}）。{}（实例域名根不含路径，"
            "discovery 路径由本函数拼接）。".format(idaas_origin, parts.path, _ORIGIN_GUIDE)
        )
    # 用 netloc 重建：去尾斜杠 + 保留端口 + 丢弃 query/fragment
    return "https://{}{}".format(parts.netloc, DISCOVERY_PATH)


# ---------------------------------------------------------------------------
# 公共 API：fetch_oidc_discovery / get_issuer_jwks
# ---------------------------------------------------------------------------


def _normalize_origin(url: str) -> Optional[Tuple[str, int]]:
    """把 URL 归一为可比较的同源三元组 ``(host, port)``；不可归一返回 ``None``（W3）。

    语义等价但字面不同的写法不再被 netloc 字面比较误杀：
    - scheme 非 https（大小写不敏感）或 URL 不可解析 → ``None``；
    - host 取 ``urlsplit().hostname``（已去 userinfo、已小写、IPv6 已去方括号），
      再 ``rstrip(".")`` 吃掉末尾点 FQDN（DNS 语义等价）；尝试 IDNA 编码把
      Unicode 域名归一为 punycode（与已小写的 punycode 写法同源），编码失败
      （IPv6 字面量/非法域名）退回原值；
    - port 取 ``urlsplit().port``，缺省补 443（https 默认端口，显式 ``:443``
      与缺省写法同源）。

    安全面不放宽：跨 host、非 https、非数字端口、畸形 URL 仍归一失败/不相等。
    """
    try:
        parts = urllib.parse.urlsplit((url or "").strip())
        if parts.scheme.lower() != "https":
            return None
        host = parts.hostname
        if not host:
            return None
        port = parts.port
    except ValueError:
        # 畸形 URL（如非法 IPv6 / 非数字端口）：不可归一。
        return None
    host = host.rstrip(".")
    try:
        host = host.encode("idna").decode("ascii").lower().rstrip(".")
    except (UnicodeError, ValueError):
        pass  # IPv6 字面量/非法域名：IDNA 不适用，退回原值（已小写）
    return (host, 443 if port is None else port)


def _call_fetch_func(
    fetch_func: Callable[..., Dict[str, Any]], url: str, timeout: int
) -> Dict[str, Any]:
    """按真实可绑定性预判调用注入的 ``fetch_func``（W4）。

    旧实现只数参数个数不看 kind：``def fetch(url, *, timeout=10)`` 会被当成
    双参位置调用触发裸 TypeError 逃逸（orders/server.py 的 ``except
    DiscoveryError`` 接不住，main 白名单也不含 TypeError）；``def fetch(url,
    *args)`` 反向漏判，timeout 被静默丢弃。现改用 ``inspect.signature`` +
    ``Signature.bind`` 做真实可绑定性预判：

    1. 可内省且 ``bind(url, timeout)`` 成功 → 双参调用；
    2. 否则 ``bind(url)`` 成功 → 单参调用；
    3. 两种契约均不可绑定 → 抛 :class:`DiscoveryError`（带修复指引）；
    4. 不可内省（部分 C 实现，signature 抛 TypeError/ValueError）→ 回落双参调用。

    bind 只做形参匹配，**不执行函数体**：注入体内部自己抛的 TypeError 仍按
    原样传播（只调一次，不吞、不重试）。
    """
    try:
        sig = inspect.signature(fetch_func)
    except (TypeError, ValueError):
        sig = None  # 无法内省（如部分 C 实现）
    if sig is not None:
        try:
            sig.bind(url, timeout)
            two_args = True
        except TypeError:
            try:
                sig.bind(url)
            except TypeError:
                raise DiscoveryError(
                    "注入的 fetch_func 签名与 (url) / (url, timeout) 契约均不兼容"
                    "（如 keyword-only 形参无法接收位置实参），请改为 "
                    "def fetch(url, timeout=10) 形态。"
                ) from None
            two_args = False
        return fetch_func(url, timeout) if two_args else fetch_func(url)
    return fetch_func(url, timeout)


def fetch_oidc_discovery(
    idaas_origin: str,
    timeout: int = DEFAULT_TIMEOUT,
    fetch_func: Optional[Callable[..., Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """拉取并解析 OIDC discovery 文档；返回原始 JSON dict。

    参数
    ----
    idaas_origin:
        IDaaS 实例域名根（如 ``https://xxx.cloud-idaas.com``），必须 https。
    timeout:
        网络超时（秒），默认 10s。仅在 ``fetch_func`` 未注入时生效。
    fetch_func:
        可选注入：签名 ``(url: str, timeout: int) -> Dict[str, Any]`` 或
        ``(url: str) -> Dict[str, Any]``。用于离线测试（沿用 verify.py
        可注入风格）；注入时不再走网络。

    异常
    ----
    DiscoveryError:
        - ``idaas_origin`` 空/占位/非 https；
        - 网络失败 / HTTP 非 2xx / JSON 解析失败；
        - 响应顶层非 dict。

        字段级校验（``issuer``/``jwks_uri`` 是否存在）交由 :func:`get_issuer_jwks`
        负责——本函数只保证拉到合法 JSON 对象，方便测试注入 fixture。
    """
    url = _build_discovery_url(idaas_origin)
    if fetch_func is not None:
        # W4：用 Signature.bind 可绑定性预判决定调用形态（见 _call_fetch_func）。
        # 保证 fetch_func **绝不被调用两次**，注入体内部异常按原样传播
        # （不吞、不重试——那是注入者的 bug，应 fail-fast 暴露）；签名与两种
        # 契约均不兼容时收敛为 DiscoveryError，不让裸 TypeError 逃逸到
        # 只认 DiscoveryError 的消费方（orders/server.py / sample.py main）。
        data = _call_fetch_func(fetch_func, url, timeout)
        if not isinstance(data, dict):
            raise DiscoveryError(
                "注入的 fetch_func 返回值非 dict（url={}）。".format(url)
            )
        return data
    return _default_fetch_discovery(url, timeout=timeout)


def get_issuer_jwks(
    idaas_origin: str,
    timeout: int = DEFAULT_TIMEOUT,
    fetch_func: Optional[Callable[..., Dict[str, Any]]] = None,
) -> Tuple[str, str]:
    """拉 discovery 并提取 ``(issuer, jwks_uri)`` 二元组（含同源安全校验）。

    校验失败一律抛 :class:`DiscoveryError` 带指引：
    - 缺字段 / 字段非 str / 空白；
    - ``jwks_uri`` 非 https；``issuer`` 非 https；
    - ``issuer`` / ``jwks_uri`` 与 ``IDAAS_ORIGIN`` **不同源**（``_normalize_origin``
      归一后的 ``(host, port)`` 不一致，W3）——
      防 SSRF / issuer 混淆：这两个值会被 ``writeback_env`` 持久化进 ``.env``，并被
      塞进订单服务的 ``TokenVerifier``，在**每次 Bearer 验签**时由 ``JwksCache`` 向
      ``jwks_uri`` 发起服务端外呼。若放任远端返回任意主机（如内网
      ``https://169.254.169.254/...``），本地长驻订单服务会沦为 SSRF 跳板。
      归一比较只放行语义等价写法（显式 ``:443``、末尾点 FQDN、punycode、IPv6），
      不放宽安全面（跨 host、http、userinfo 嵌入仍拒绝）。

    **issuer 不要求与 IDAAS_ORIGIN 字符串全等**：真实部署的 issuer 常带路径前缀
    （如 ``/api/v2/iauths_system/oauth2``）。RFC 8414 §3.3 的一致性以「同 scheme +
    同 host」为准；严格全等会误杀正常环境，故此处只校验同源。
    """
    data = fetch_oidc_discovery(idaas_origin, timeout=timeout, fetch_func=fetch_func)
    # fetch_oidc_discovery 成功 ⇒ idaas_origin 已过 _build_discovery_url 校验
    # （scheme=https、netloc/hostname 非空、端口合法、不含路径、无 userinfo），
    # 故此处归一必成功（防御式判定仅为契约自洽）。
    expected_origin = _normalize_origin(idaas_origin)
    if expected_origin is None:  # pragma: no cover - 防御分支：上游校验已拦截
        raise DiscoveryError(
            "IDAAS_ORIGIN={!r} 无法归一为合法 https 源。{}".format(idaas_origin, _ORIGIN_GUIDE)
        )

    issuer = data.get("issuer")
    jwks_uri = data.get("jwks_uri")
    if not isinstance(issuer, str) or not issuer.strip():
        raise DiscoveryError(
            "OIDC discovery 响应缺少合法 `issuer` 字段（值={!r}）。请打开 "
            "{}/{} 手动确认响应结构，或在 sample .env 显式填 "
            "ORDER_SERVICE_ISSUER 跳过 discovery。".format(
                issuer, idaas_origin.rstrip("/"), DISCOVERY_PATH
            )
        )
    if not isinstance(jwks_uri, str) or not jwks_uri.strip():
        raise DiscoveryError(
            "OIDC discovery 响应缺少合法 `jwks_uri` 字段（值={!r}）。请打开 "
            "{}/{} 手动确认响应结构，或在 sample .env 显式填 "
            "ORDER_SERVICE_JWKS_URI 跳过 discovery。".format(
                jwks_uri, idaas_origin.rstrip("/"), DISCOVERY_PATH
            )
        )
    issuer = issuer.strip()
    jwks_uri = jwks_uri.strip()

    # W3：issuer/jwks_uri 先做 URL 解析（畸形 URL 的专用错误消息保留），再统一用
    # _normalize_origin 归一后的 (host, port) 做同源与 https 判定 —— 旧实现
    # jwks 用大小写敏感的 startswith("https://")、issuer 用不敏感的 scheme 比较，
    # 同目的两口径；归一后两者一致（scheme 大小写不敏感）。
    try:
        urllib.parse.urlsplit(issuer)
        urllib.parse.urlsplit(jwks_uri)
    except ValueError as exc:
        raise DiscoveryError(
            "OIDC discovery 返回的 issuer/jwks_uri 不是合法 URL（{}）。issuer={!r} "
            "jwks_uri={!r}。".format(exc, issuer, jwks_uri)
        ) from None
    issuer_origin = _normalize_origin(issuer)
    jwks_origin = _normalize_origin(jwks_uri)
    # jwks_uri 必须 https（它驱动订单服务验签外呼，绝不允许明文；不可归一含非 https）
    if jwks_origin is None:
        raise DiscoveryError(
            "OIDC discovery 返回的 jwks_uri={!r} 不是合法 https 地址。订单服务验签外呼强制"
            "走 TLS——请检查 IDAAS_ORIGIN 与实例配置，或在 .env 显式填合法的 "
            "ORDER_SERVICE_JWKS_URI。".format(jwks_uri)
        )
    # issuer 必须是合法 https URL（path 可空——同源性已保证它归属 IDAAS_ORIGIN）
    if issuer_origin is None:
        raise DiscoveryError(
            "OIDC discovery 返回的 issuer={!r} 不是 https 地址。issuer 混淆攻击可伪造"
            "签发方——已阻止。请检查 IDAAS_ORIGIN 与实例配置。".format(issuer)
        )
    # 同源校验：归一后的 (host, port) 必须与 IDAAS_ORIGIN 一致（host 大小写/
    # 末尾点/punycode/默认端口均归一；userinfo 已被 hostname 剥离，不影响同源判定）
    if issuer_origin != expected_origin:
        raise DiscoveryError(
            "OIDC discovery 返回的 issuer 与 IDAAS_ORIGIN 不同源（issuer host={!r}，"
            "期望 host={!r}）。这可能是 issuer 混淆 / SSRF——已阻止。请确认 IDAAS_ORIGIN "
            "指向正确的 IDaaS 实例。".format(
                urllib.parse.urlsplit(issuer).netloc,
                urllib.parse.urlsplit(idaas_origin.strip()).netloc,
            )
        )
    if jwks_origin != expected_origin:
        raise DiscoveryError(
            "OIDC discovery 返回的 jwks_uri 与 IDAAS_ORIGIN 不同源（jwks host={!r}，"
            "期望 host={!r}）。jwks_uri 会驱动订单服务每次验签的外呼，跨源即 SSRF 风险"
            "——已阻止。请确认 IDAAS_ORIGIN 指向正确的 IDaaS 实例。".format(
                urllib.parse.urlsplit(jwks_uri).netloc,
                urllib.parse.urlsplit(idaas_origin.strip()).netloc,
            )
        )
    return (issuer, jwks_uri)


# ---------------------------------------------------------------------------
# 内存 TTL 缓存（镜像 orders/verify.py:88-134 JwksCache 范式）
# ---------------------------------------------------------------------------


class DiscoveryCache:
    """Discovery 内存缓存：TTL 3600s + 并发安全 + ``force_refresh`` 旁路。

    并发安全：``serve-orders`` 长驻进程下多个请求线程可能在冷启动同时未命中——
    无锁会并发重复拉 discovery（惊群）。``get`` 全程持锁串行化，同一时刻只有
    一个线程在拉取。

    读顺序
    ------
    1. 内存（未过 TTL 且已有值）→ 直接返回；
    2. 网络拉取 → 回填内存 + 返回；
    3. ``force_refresh=True`` → 无视 TTL 直接走网络（用于验签失败时清缓存重拉，
       复用 JwksCache kid-miss 强刷范式）。

    **不做持久化**：不写 ``.tokens/discovery.json``。短命 CLI 进程每次一次网络
    往返可接受；长驻进程内存 TTL 已足够。持久化会引入失效/陈旧/并发写等额外
    复杂度，对本 sample 过度设计。
    """

    def __init__(
        self,
        idaas_origin: str,
        fetch_func: Optional[Callable[..., Dict[str, Any]]] = None,
        ttl: int = DISCOVERY_CACHE_TTL,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.idaas_origin = idaas_origin
        self._fetch_func = fetch_func
        self._ttl = ttl
        self._timeout = timeout
        self._issuer: Optional[str] = None
        self._jwks_uri: Optional[str] = None
        self._loaded_at = 0.0
        self._lock = threading.Lock()

    def _load(self) -> None:
        """从网络拉一次并回填内存。调用方必须已持锁。"""
        issuer, jwks_uri = get_issuer_jwks(
            self.idaas_origin, timeout=self._timeout, fetch_func=self._fetch_func
        )
        self._issuer = issuer
        self._jwks_uri = jwks_uri
        self._loaded_at = time.time()

    def get(self, force_refresh: bool = False) -> Tuple[str, str]:
        """取 ``(issuer, jwks_uri)``：内存命中且未过期直接返回；否则网络拉取回填。"""
        with self._lock:
            fresh = (time.time() - self._loaded_at) < self._ttl
            if (
                not force_refresh
                and self._issuer is not None
                and self._jwks_uri is not None
                and fresh
            ):
                return (self._issuer, self._jwks_uri)
            self._load()
            # _load 成功后两字段必非空（get_issuer_jwks 已校验）
            assert self._issuer is not None and self._jwks_uri is not None
            return (self._issuer, self._jwks_uri)

    def clear(self) -> None:
        """清空缓存（下次 get 必走网络）。用于验签失败时清缓存重拉。"""
        with self._lock:
            self._issuer = None
            self._jwks_uri = None
            self._loaded_at = 0.0


# ---------------------------------------------------------------------------
# 进程级默认缓存（按 idaas_origin 分桶，支持多实例场景）
# ---------------------------------------------------------------------------

_DEFAULT_CACHES: Dict[Any, DiscoveryCache] = {}
_DEFAULT_CACHES_LOCK = threading.Lock()


def _default_cache_key(idaas_origin: str) -> Any:
    """S10：默认缓存分桶 key 用 ``_normalize_origin`` 归一后的 ``(host, port)``。

    语义等价写法（显式 ``:443``、末尾点 FQDN、punycode、大小写）共享同一缓存，
    避免多实例长驻进程重复拉取；归一失败（非法 origin）退回原始字符串
    （后续 get_issuer_jwks 会拒，不会污染正常分桶）。
    """
    normalized = _normalize_origin(idaas_origin)
    if normalized is None:
        return idaas_origin
    return normalized


def _get_default_cache(idaas_origin: str) -> DiscoveryCache:
    """返回按 ``idaas_origin``（归一后）分桶的进程级默认缓存（懒构造 + 双检锁）。"""
    key = _default_cache_key(idaas_origin)
    with _DEFAULT_CACHES_LOCK:
        cache = _DEFAULT_CACHES.get(key)
        if cache is None:
            cache = DiscoveryCache(idaas_origin)
            _DEFAULT_CACHES[key] = cache
        return cache


# ---------------------------------------------------------------------------
# 公共 API：apply_discovery（回填 config 空位）
# ---------------------------------------------------------------------------


def apply_discovery(
    config: Dict[str, str],
    force_refresh: bool = False,
    fetch_func: Optional[Callable[..., Dict[str, Any]]] = None,
) -> Dict[str, str]:
    """若 ``config`` 的 ``ORDER_SERVICE_ISSUER``/``ORDER_SERVICE_JWKS_URI`` 为空/占位
    且 ``IDAAS_ORIGIN`` 非空 → 拉 discovery 回填（仅填空，显式值优先）。

    **返回新 dict，不改原 config**（保持与 ``env.derive_defaults`` 一致的语义）。

    参数
    ----
    config:
        原配置 dict（不会被修改）。
    force_refresh:
        是否强制绕过 TTL 缓存重拉（默认 False）。验签失败清缓存重拉时用 True。
    fetch_func:
        可选注入：仅本次调用生效（用于离线测试）；缓存路径不共享此注入，
        避免测试污染进程级默认缓存。

    异常
    ----
    DiscoveryError:
        IDAAS_ORIGIN 非法 / 网络失败 / 字段缺失时抛出。**不静默吞异常**——
        sample.py 入口应捕获后给出友好错误（用户显式填 issuer/jwks 即可绕过）。

    副作用
    ------
    - **有网络副作用**（拉 discovery），**绝不进 ``env.derive_defaults``**。
    - 由 ``sample.py`` 在 ``demo``/``serve-orders`` 入口显式调用；``login``
      /``--check`` 不调用（它们不需要 issuer/jwks，避免平白多一次网络往返）。
    """
    merged = dict(config)
    issuer_raw = merged.get("ORDER_SERVICE_ISSUER", "")
    jwks_raw = merged.get("ORDER_SERVICE_JWKS_URI", "")
    issuer_empty = env_mod.is_placeholder(issuer_raw)
    jwks_empty = env_mod.is_placeholder(jwks_raw)
    # 两项都已显式填 → 无需 discovery，直接返回副本
    if not issuer_empty and not jwks_empty:
        return merged
    idaas_origin = merged.get("IDAAS_ORIGIN", "")
    if env_mod.is_placeholder(idaas_origin):
        # IDAAS_ORIGIN 也没配：无法 discovery；若 issuer/jwks 有空位，让下游
        # require_config 抛缺项错误（此处不抛，保持 apply_discovery 的宽容语义——
        # 只要用户显式填齐 issuer/jwks 就绕开 discovery）
        return merged

    # 拉 discovery（走进程级默认缓存 or 注入 fetch_func 的一次性拉取）
    if fetch_func is not None:
        issuer, jwks_uri = get_issuer_jwks(
            idaas_origin, fetch_func=fetch_func
        )
    else:
        cache = _get_default_cache(idaas_origin)
        issuer, jwks_uri = cache.get(force_refresh=force_refresh)

    # 仅填空，显式值优先
    if issuer_empty:
        merged["ORDER_SERVICE_ISSUER"] = issuer
    if jwks_empty:
        merged["ORDER_SERVICE_JWKS_URI"] = jwks_uri
    return merged
