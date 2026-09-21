"""凭据链单一入口：三级降级解析阿里云 RPC 三元组 (AK, SK, SecurityToken|None)。

设计目标
--------
消除 ``lib/flow.py:70-78`` 与 ``lib/control_plane.py:56-62`` 两处重复的凭据组装，
统一为一个 ``resolve_creds(config)`` 入口，让 sample 支持三种凭据获取方式：

三级降级链（越靠前优先级越高，命中即返回）
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. **显式优先**：``config`` 的 ``ALIYUN_ACCESS_KEY_ID``/``ALIYUN_ACCESS_KEY_SECRET``
   非占位 → 直接返回（``ALIYUN_SECURITY_TOKEN`` 非占位则并入）。
   向后兼容 / CI 注入 / 教学固定凭证场景。

2. **SDK 主路径**：可选依赖 ``alibabacloud_credentials`` 已安装 →
   懒加载单例 ``CredentialClient()`` 走默认凭据链（含 CLI profile 读
   ``~/.aliyun/config.json``、OAuth refresh_token 非交互后台刷新+回写、
   ECS RAM Role、Environment 变量等）。一次 ``client.get_credential()``
   取回三字段（勿用 3 个 deprecated getter，各自独立触发 provider.get_credentials
   = 3x 成本）。任何异常 → 记降级日志，进第 3 级。

3. **标准库降级**：纯 ``stdlib`` 解析 ``~/.aliyun/config.json``：
   读 ``current`` → ``profiles[]`` 找同名 profile → 按 ``mode`` 分支：
   - ``AK``：``(access_key_id, access_key_secret, None)``。
   - ``StsToken``：``(access_key_id, access_key_secret, sts_token)``，
     校验 ``sts_expiration`` 未过期。
   - ``OAuth``：读缓存三元组（``access_key_id`` 通常带 ``STS.`` 前缀、
     ``access_key_secret``、``sts_token``）+ 校验 ``sts_expiration``；
     **过期即抛 ``CredentialError`` 带指引**（不做 refresh：与 SDK 重复且
     refresh 涉及网络 + PKCE + 写盘，超出降级路径职责）。

环境变量命名差异（务必分清）
----------------------------
- 显式分支认 sample 的 ``ALIYUN_ACCESS_KEY_ID`` / ``ALIYUN_ACCESS_KEY_SECRET``
  / ``ALIYUN_SECURITY_TOKEN``（沿用 sample ``.env`` 模板既有命名）。
- SDK 分支认 ``ALIBABA_CLOUD_ACCESS_KEY_ID`` / ``ALIBABA_CLOUD_ACCESS_KEY_SECRET``
  / ``ALIBABA_CLOUD_SECURITY_TOKEN`` 等（``ALIBABA_CLOUD_*`` 前缀，由 SDK
  内部 EnvironmentVariableCredentialsProvider 处理，本模块不干预）。

零依赖属性
----------
本模块**纯标准库即可独立运行**（第 3 级降级路径不需要任何第三方包）。
检测到 ``alibabacloud_credentials`` 时自动用作凭据链增强（可选，推荐安装以
获得 OAuth 自动刷新能力）。SDK 未装不影响 sample 可跑通。

SDK 版本防御
------------
只用同步 ``get_credential()`` 路径：``alibabacloud_credentials`` v1.0.4 起
OneCallerBlocks 语义为同步刷新，无后台 daemon 线程阻塞 CLI 退出。已验证
版本：v1.0.4（.venv）、v1.0.10（系统 python3.12）。升级前建议跑退出时延测试。

线程防护的正确姿势（重要，勿改回 atexit）
----------------------------------------
真正生效的防护在 ``_get_sdk_client()`` 内**同步**执行：构造 ``CredentialClient()``
前后各快照一次 ``threading.enumerate()``，只对**差集**（可归因于 SDK 构造的线程）
设 ``daemon=True``。之所以不能放到 ``atexit``：

(a) ``Thread.daemon`` setter 对**已启动**线程抛 ``RuntimeError``，而
    ``threading.enumerate()`` 返回的全是已启动线程 —— 无差别遍历恒走 except，
    等价于什么都没做；
(b) CPython ``Py_FinalizeEx`` 先 ``wait_for_thread_shutdown()``（join 非 daemon
    线程）再跑 atexit 钩子 —— 真挂住时 atexit 根本轮不到执行。

``install_atexit_guard()`` / ``ensure_daemon_threads()`` 作为**兼容入口**保留
（``sample.py`` 与既有测试仍引用），但默认不再无差别遍历全部线程，避免误伤
回写 ``~/.aliyun/config.json`` 的线程、以及把 ``sample.py`` 当模块 import 的
宿主进程里的业务线程。

两个公开解析入口的分工
----------------------
``resolve_creds(config)``
    返回裸三元组 ``(access_key_id, access_key_secret, security_token|None)``。
    供 RPC 签名路径（``lib/flow.py``、``lib/control_plane.py``）使用 —— 它们只
    关心凭据本身，不关心命中哪一级。历史签名与行为**完全不变**，内部委托
    ``resolve_creds_detailed``。

``resolve_creds_detailed(config)``
    返回 :class:`ResolvedCreds` namedtuple，在三元组之外多带两个可观测字段：

    - ``level`` ∈ ``"explicit"`` / ``"sdk"`` / ``"stdlib"``（命中的降级级别）；
    - ``source`` 人读来源描述（显式级 → ``.env`` 变量名；SDK 级 →
      ``CredentialModel.provider_name``，取不到时回退 ``alibabacloud_credentials
      默认链``；标准库级 → ``~/.aliyun/config.json(profile=<name>, mode=<mode>)``）。

    供 ``sample.py --check`` 打印凭据链命中详情使用 —— 不要再用
    ``creds[0].startswith("STS.")`` 猜级别（那样区分不出 SDK 与标准库路径）。

离线探测三件套（``probe_*``）与真实解析入口的分工
--------------------------------------------------
上面两个 ``resolve_*`` 是**真实解析**入口：会推进整条三级降级链，其中第 2 级
必须调 ``client.get_credential()`` —— 可能触发 OAuth 后台续期 / AssumeRole /
ECS 元数据探测等**网络副作用**，并可能回写全局 ``~/.aliyun/config.json``。

``sample.py --check`` 的默认口径是**纯离线体检**（不联网、不刷新、不写盘），
既不能用真实解析入口，也不该去掏本模块的私有 helper（私有符号重构会静默打断
调用方，读者还会误以为那是推荐用法）。为此本模块提供三个**只读探测**公开 API：

``probe_explicit(config)``
    探测第 1 级：``.env`` 显式 ``ALIYUN_ACCESS_KEY_*`` 是否可用。命中返回
    :class:`ResolvedCreds`（``level="explicit"``）；两项均缺/占位返回 ``None``；
    **恰好一项非占位（半填）抛 :class:`CredentialError`** —— 与 ``resolve_creds``
    的异常语义完全一致，因为体检必须把这类配置错误暴露给用户，不能静默吞掉。

``probe_sdk_installed()``
    探测第 2 级的**安装态**（``alibabacloud_credentials`` 是否可导入），返回
    ``bool``。**绝不构造 ``CredentialClient``、绝不调用 ``get_credential()``** ——
    构造客户端会 eager 构造整条 provider 链并可能触发 ECS 元数据探测（固定
    ~2.0s 超时），违背离线口径。想知道 SDK 级是否真的命中，只能用
    ``--creds-live``（即 ``resolve_creds_detailed``）。

``probe_stdlib()``
    探测第 3 级：只读解析 ``~/.aliyun/config.json``（含 STS 过期判定）。成功返回
    :class:`ResolvedCreds`（``level="stdlib"``，``source`` 自带
    ``profile=<name>, mode=<mode>`` —— 调用方无需再读模块级私有变量
    ``_LAST_STDLIB_SOURCE``）；失败抛 :class:`CredentialError`，message 与真实
    解析路径逐字一致，便于体检原样透传给用户。不发网络、不做 refresh、不写盘。

三者都是**薄委托**：内部直接调对应的私有 helper，不复制任何判定逻辑（避免两份
实现发散）。因此 ``probe_*`` 返回的 ``level``/``source`` 与
``resolve_creds_detailed`` 在同级上的取值**完全一致**；差别只在于 probe 不推进
降级链、不碰 SDK 的网络路径。

已验证的 ``~/.aliyun/config.json`` 结构
---------------------------------------
::

    {
      "current": "default",
      "profiles": [
        {
          "name": "default",
          "mode": "AK" | "StsToken" | "OAuth" | ...,
          "access_key_id": "LTA..." | "STS....",
          "access_key_secret": "...",
          "sts_token": "...",              # StsToken/OAuth
          "sts_expiration": "2026-09-14T12:00:00Z",  # StsToken/OAuth
          "oauth_refresh_token": "..."     # OAuth（本模块不使用）
        }
      ]
    }
"""

import atexit
import json
import os
import sys
import threading
import time
from collections import namedtuple
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from . import env as env_mod

# ---------------------------------------------------------------------------
# 可选依赖：alibabacloud_credentials（SDK 主路径）。
# 缺失时 _get_sdk_client() 恒返回 None，resolve_creds 自动跳过第 2 级。
# ---------------------------------------------------------------------------

try:
    from alibabacloud_credentials.client import Client as CredentialClient  # type: ignore
except ImportError:  # pragma: no cover - SDK 未安装场景
    CredentialClient = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# 异常
# ---------------------------------------------------------------------------


#: 结构化失败原因常量（``CredentialError.reason`` 取值域）。
#:
#: 消费方（如 ``sample.py --check`` 的退出码判定）**必须**按 reason 分类，
#: 严禁用 ``"某某文案" in str(exc)`` 的跨模块中文子串匹配 —— 本模块与消费方
#: 同批演进，文案一改子串判定就静默 fail-open；reason 是稳定契约。
REASON_STS_EXPIRED = "STS_EXPIRED"
REASON_HALF_FILLED = "HALF_FILLED"
REASON_CONFIG_NOT_FOUND = "CONFIG_NOT_FOUND"
REASON_UNSUPPORTED_MODE = "UNSUPPORTED_MODE"
REASON_MISSING_TRIPLE = "MISSING_TRIPLE"
REASON_SDK_UNAVAILABLE = "SDK_UNAVAILABLE"


class CredentialError(Exception):
    """凭据解析失败（三级链全部落空 / 显式凭据半填 / STS 过期 / config.json 结构非法等）。

    message 内自带下一步指引，供 sample.py 直接透传给用户。

    Attributes:
        reason: 结构化失败原因（:data:`REASON_STS_EXPIRED` 等模块级常量之一），
            供消费方做**稳定**的错误分类（替代中文文案子串匹配）。
            ``None`` 表示历史构造点尚未归类，消费方不得对 ``None`` 做硬失败判定。
    """

    def __init__(self, message: str, reason: Optional[str] = None) -> None:
        # 单参构造保持向后兼容（既有调用点与测试不传 reason）。
        super().__init__(message)
        self.reason = reason


# ---------------------------------------------------------------------------
# 可观测结果类型（resolve_creds_detailed 的返回体）
# ---------------------------------------------------------------------------

#: 命中的降级级别常量（``ResolvedCreds.level`` 取值域）。
LEVEL_EXPLICIT = "explicit"
LEVEL_SDK = "sdk"
LEVEL_STDLIB = "stdlib"


class ResolvedCreds(namedtuple("ResolvedCreds", (
    "access_key_id",
    "access_key_secret",
    "security_token",
    "level",
    "source",
))):
    """凭据解析结果 + 命中级别 + 人读来源描述。

    前三个字段与 ``resolve_creds`` 返回的裸三元组一一对应，所以
    ``tuple(resolved)[:3] == resolve_creds(config)`` 恒成立（namedtuple 本身就是
    tuple，可直接解包）。

    Attributes:
        access_key_id: AK Id（STS 临时凭证带 ``STS.`` 前缀）。
        access_key_secret: AK Secret。
        security_token: STS Token；长期 AK 场景为 ``None``。
        level: 命中的降级级别，∈ ``"explicit"`` / ``"sdk"`` / ``"stdlib"``。
        source: 人读来源描述（具体格式见模块 docstring）。
    """

    __slots__ = ()

    @property
    def triple(self) -> Tuple[str, str, Optional[str]]:
        """返回与 ``resolve_creds`` 同形的裸三元组（供调用方少写解包代码）。"""
        return (self.access_key_id, self.access_key_secret, self.security_token)


# ---------------------------------------------------------------------------
# 进程内缓存与可观测状态（均由 _reset_caches() 复位，供单测隔离）
# ---------------------------------------------------------------------------

#: SDK 路径失败后的**负缓存** TTL（秒）。
#:
#: 背景：无凭据机器上 ``get_credential()`` 会走完整默认链，末尾
#: ``EcsRamRoleCredentialsProvider`` 探 ``100.100.100.200:80`` 两次各 1s 超时，
#: 实测每次解析固定付 ~2.0s。管控面 ``run_setup_script`` 会连续调 ~10 次，
#: 累计 ~20s 白白等超时。故只缓存「SDK 路径已尝试且失败」这一**事实**，
#: TTL 窗口内直接跳过 SDK 级进标准库级。
#:
#: **不对成功结果做缓存** —— 那会破坏 SDK 的 STS 到期自动刷新语义。
SDK_FAILURE_NEGATIVE_TTL = 30.0

#: 时间源（可注入 / 可 patch，便于单测控制 TTL 而不必真 sleep）。
_TIME_SOURCE = time.monotonic

_CRED_CLIENT: Optional[Any] = None
_CRED_LOCK = threading.Lock()

#: SDK 路径最近一次失败的**精确原因**（四种失败态分开记，供聚合错误消息如实填入）。
_LAST_SDK_FAILURE: Optional[str] = None
#: SDK 负缓存的时间戳（``_TIME_SOURCE()`` 读数）；``None`` 表示无生效中的负缓存。
_SDK_FAILED_AT: Optional[float] = None
#: SDK 级命中时的人读来源（``CredentialModel.provider_name``）。
_LAST_SDK_SOURCE: Optional[str] = None
#: 标准库级命中时的人读来源（``~/.aliyun/config.json(profile=..., mode=...)``）。
_LAST_STDLIB_SOURCE: Optional[str] = None

# 四种 SDK 失败态的固定措辞（聚合消息用；勿随意改动，下游测试断言子串）。
_SDK_FAIL_NOT_INSTALLED = "未安装（ImportError）"
_SDK_FAIL_CONSTRUCT = "CredentialClient() 构造失败（配置非法）"
_SDK_FAIL_GET_CREDENTIAL = "get_credential() 异常"
_SDK_FAIL_EMPTY = "get_credential() 返回空 AK/SK"

# provider_name 取不到时的人读回退（SDK 版本差异：v1.0.4 无此字段）。
_SDK_SOURCE_FALLBACK = "alibabacloud_credentials 默认链"


def _now() -> float:
    """读单调时钟（经 ``_TIME_SOURCE`` 间接调用，便于单测 patch）。"""
    return _TIME_SOURCE()


def _reset_caches() -> None:
    """复位本模块全部进程内状态（SDK 单例 + 负缓存 + 来源/失败记录）。

    单测必须在 ``setUp``/``addCleanup`` 调用，否则用例间会串味
    （尤其 SDK 负缓存 TTL 30s 远大于单测运行时长）。
    """
    global _CRED_CLIENT, _LAST_SDK_FAILURE, _SDK_FAILED_AT
    global _LAST_SDK_SOURCE, _LAST_STDLIB_SOURCE
    _CRED_CLIENT = None
    _LAST_SDK_FAILURE = None
    _SDK_FAILED_AT = None
    _LAST_SDK_SOURCE = None
    _LAST_STDLIB_SOURCE = None


def _sdk_negative_cache_active() -> bool:
    """判定 SDK 负缓存是否仍在 TTL 窗口内（过期则自动作废，允许重试 SDK）。"""
    if _SDK_FAILED_AT is None:
        return False
    return (_now() - _SDK_FAILED_AT) < SDK_FAILURE_NEGATIVE_TTL


def _record_sdk_failure(reason: str, negative_cache: bool) -> None:
    """记录 SDK 失败原因；``negative_cache=True`` 时同时开启 TTL 窗口。

    TTL 窗口内的重复失败只刷新原因、不重置时间戳 —— 避免持续失败时
    窗口被无限延长（每 30s 至少给用户一次真实重试 SDK 的机会）。
    """
    global _LAST_SDK_FAILURE, _SDK_FAILED_AT
    _LAST_SDK_FAILURE = reason
    if not negative_cache:
        return
    if not _sdk_negative_cache_active():
        _SDK_FAILED_AT = _now()


def _one_period(text: str) -> str:
    """归一化句尾句号：去掉已有结尾「。」/「.」，交由模板统一补一个（修双句号）。

    只动句尾：前导空白与内部换行/缩进原样保留（多行降级指引的排版不能丢）。
    全是句号的退化输入不会被吃空。
    """
    stripped = str(text).rstrip()
    while stripped.endswith("。") or stripped.endswith("."):
        candidate = stripped[:-1].rstrip()
        if not candidate:
            break  # 退化输入（如 "..."）：原样保留，不得剥成空字符串
        stripped = candidate
    return stripped


# ---------------------------------------------------------------------------
# SDK 懒加载单例（严格镜像 lib/rpc.py:43-59 ssl_context() 双检锁范式）
# 单例与锁定义见上方「进程内缓存」区。
# ---------------------------------------------------------------------------


def _snapshot_threads() -> set:
    """快照当前存活线程集合（``set(threading.enumerate())``）。

    独立成函数而不内联 ``threading.enumerate()``，是为了单测能只 patch 本模块的
    快照函数、而不必去 patch 全局 ``threading`` 模块（后者会波及 unittest 自身）。
    """
    return set(threading.enumerate())


def _get_sdk_client() -> Optional[Any]:
    """返回进程级共享 ``CredentialClient`` 单例；SDK 未安装则恒返回 ``None``。

    双检锁范式（镜像 ``lib/rpc.py:43-59`` ``ssl_context()``）：
    - 首次调用构造 ``CredentialClient()``（内部会 eager 构造整条 provider 链），
      后续调用直接复用同一实例。
    - 避免 ``run_setup_script`` 的 ~10 次 ``_call`` 各自重新实例化。
    - SDK 的 ``reuse_last_provider_enabled`` 语义已提供内部缓存，本模块无需
      再套 memoize 层。

    线程防护（同步执行，不依赖 atexit）：在 ``CredentialClient()`` 构造前后各
    快照一次 ``threading.enumerate()``，只对**差集**（可归因于本次 SDK 构造
    新起的线程）设 ``daemon=True``。这里必须趁主线程还在运行时同步做：
    ``Thread.daemon`` 对已启动线程抛 ``RuntimeError``，而 CPython 退出时先
    ``wait_for_thread_shutdown()``（join 非 daemon 线程）再跑 atexit ——
    放到 atexit 里既改不动属性也轮不到执行（详见模块 docstring）。

    只对差集下手是硬约束：**严禁**把不属于 SDK 的线程标 daemon ——
    那会波及回写 ``~/.aliyun/config.json`` 的线程，以及把 ``sample.py`` 当模块
    import 的宿主进程里的业务线程（被标 daemon 后会被静默强杀）。

    构造失败不缓存 ``None``（下次调用会再次尝试，用户可能已修复配置），
    但会把精确原因写入 ``_LAST_SDK_FAILURE`` 供聚合错误消息使用。
    """
    global _CRED_CLIENT
    if CredentialClient is None:
        return None
    with _CRED_LOCK:
        if _CRED_CLIENT is None:
            threads_before = _snapshot_threads()
            try:
                _CRED_CLIENT = CredentialClient()
            except Exception as exc:  # SDK 构造失败（配置非法等）
                # 构造异常也可能已经起了线程（provider 链 eager 构造中途失败），
                # 同样需要把差集标 daemon，否则短命 CLI 会被它们挂住。
                _daemonize_new_threads(_snapshot_threads() - threads_before)
                # 构造失败不缓存 None：下次调用会再次尝试（用户可能已修复配置）。
                _record_sdk_failure(
                    "{}：{}".format(_SDK_FAIL_CONSTRUCT, exc), negative_cache=False
                )
                print(
                    "[credentials] alibabacloud_credentials 初始化失败，降级到标准库路径：{}".format(exc),
                    file=sys.stderr,
                )
                return None
            _daemonize_new_threads(_snapshot_threads() - threads_before)
        return _CRED_CLIENT


# ---------------------------------------------------------------------------
# 第 1 级：显式 AK/SK（config 内 ALIYUN_*）
# ---------------------------------------------------------------------------

#: 显式级的人读来源描述。
_EXPLICIT_SOURCE = ".env 显式 ALIYUN_ACCESS_KEY_*"


def _creds_from_explicit(config: Dict[str, str]) -> Optional[Tuple[str, str, Optional[str]]]:
    """从 config 读显式 ``ALIYUN_ACCESS_KEY_*``；两项均未填则返回 ``None`` 让下一级接管。

    占位判定复用 ``env.is_placeholder``（覆盖 ``<YOUR_...>`` 模板占位、空值、
    纯空白三种形态）。三种情形：

    - **两项均非占位** → 返回三元组（``ALIYUN_SECURITY_TOKEN`` 非占位则并入）；
    - **两项均为占位/空** → 返回 ``None``，降到 SDK / 标准库凭据链（推荐姿势）；
    - **恰好一项非占位** → **抛 ``CredentialError``**。

    为何半填必须报错而不是静默降级（P0）：
        只填了 AK Id 或只填了 SK 时，若沿用旧的 ``or`` 短路，结果与两项都没填
        完全一致 —— 会静默落到 SDK/标准库凭据链，而那可能是**另一个阿里云
        账号**。本 sample 的管控面会真实创建/删除企业身份资源，用错账号执行
        破坏性操作不可接受。改造前 ``flow.creds_from_env`` 用 ``require_config``
        会立即报错，此处必须保留同等严格度。
    """
    ak = config.get("ALIYUN_ACCESS_KEY_ID", "")
    sk = config.get("ALIYUN_ACCESS_KEY_SECRET", "")
    ak_missing = env_mod.is_placeholder(ak)
    sk_missing = env_mod.is_placeholder(sk)
    if ak_missing and sk_missing:
        # 两项都未填：这是「走 aliyun CLI 凭据链」的新推荐姿势，必须保留降级。
        return None
    if ak_missing != sk_missing:
        missing_key = "ALIYUN_ACCESS_KEY_SECRET" if sk_missing else "ALIYUN_ACCESS_KEY_ID"
        filled_key = "ALIYUN_ACCESS_KEY_ID" if sk_missing else "ALIYUN_ACCESS_KEY_SECRET"
        raise CredentialError(
            ".env 显式凭据半填：{filled} 已填写，但 {missing} 缺失或仍为占位值。\n"
            "拒绝静默降级到 SDK/标准库凭据链 —— 那可能是另一个阿里云账号的身份，\n"
            "而本 sample 的管控面会真实创建/删除企业身份资源，用错账号执行破坏性操作不可接受。\n"
            "下一步（二选一）：\n"
            "  A) 补齐 {missing}，与 {filled} 组成完整凭据（适合 CI / 教学固定凭证）；\n"
            "  B) 或把 {filled} 和 {missing} 两项都清空/改回 <YOUR_...> 占位，\n"
            "     以显式声明「走 aliyun CLI 凭据链」（推荐：先执行 `aliyun configure`）。"
            .format(filled=filled_key, missing=missing_key),
            reason=REASON_HALF_FILLED,
        )
    st_raw = config.get("ALIYUN_SECURITY_TOKEN", "")
    st: Optional[str] = st_raw if (st_raw and not env_mod.is_placeholder(st_raw)) else None
    return (ak, sk, st)


# ---------------------------------------------------------------------------
# 第 2 级：SDK 主路径（alibabacloud_credentials 默认凭据链）
# ---------------------------------------------------------------------------


def _creds_from_sdk() -> Optional[Tuple[str, str, Optional[str]]]:
    """调 SDK 默认链取一次凭据；SDK 未装 / 调用异常 → 返回 ``None`` 让下一级接管。

    严格用 ``client.get_credential()`` 一次取全三字段（``CredentialModel``
    的 ``.access_key_id`` / ``.access_key_secret`` / ``.security_token``），
    避免 3 个 deprecated getter 各自触发 provider.get_credentials = 3x 成本。

    四条返回 ``None`` 的路径各自写入精确的 ``_LAST_SDK_FAILURE``，不再把
    「构造失败（配置非法）」与「返回空值」混为一谈：

    1. SDK 未安装（模块级 ``CredentialClient is None``）—— 不进负缓存（判定零成本）；
    2. ``CredentialClient()`` 构造失败 —— 由 ``_get_sdk_client()`` 写入原因；不进
       负缓存（保留「修好配置后下次重试」语义，已有测试锁定）；
    3. ``get_credential()`` 抛异常 —— **进负缓存**（这是无凭据机器上固定付
       ~2.0s ECS 元数据探测超时的元凶）；
    4. ``get_credential()`` 返回空 AK/SK —— **进负缓存**（同样已付完整链路成本）。

    负缓存 TTL 窗口内（``SDK_FAILURE_NEGATIVE_TTL``）直接跳过本级，且 stderr 降级
    日志只打一次（避免 ``run_setup_script`` 的 ~10 次 ``_call`` 刷屏）。成功结果
    **永不缓存**，否则会破坏 SDK 的 STS 到期自动刷新语义。
    """
    global _LAST_SDK_SOURCE, _LAST_SDK_FAILURE
    _LAST_SDK_SOURCE = None

    if _sdk_negative_cache_active():
        # TTL 窗口内：已试过且失败，直接跳过 SDK 级。不重复探测、不重复打日志。
        return None

    client = _get_sdk_client()
    if client is None:
        if CredentialClient is None:
            _record_sdk_failure(_SDK_FAIL_NOT_INSTALLED, negative_cache=False)
        # else：构造失败，_get_sdk_client() 已写入精确原因（不进负缓存）。
        return None
    try:
        model = client.get_credential()
    except Exception as exc:
        _record_sdk_failure(
            "{}：{}".format(_SDK_FAIL_GET_CREDENTIAL, exc), negative_cache=True
        )
        print(
            "[credentials] SDK get_credential() 失败，降级到标准库路径：{}".format(exc),
            file=sys.stderr,
        )
        return None
    ak = getattr(model, "access_key_id", None) or ""
    sk = getattr(model, "access_key_secret", None) or ""
    st = getattr(model, "security_token", None) or None
    if not ak or not sk:
        _record_sdk_failure(_SDK_FAIL_EMPTY, negative_cache=True)
        print(
            "[credentials] SDK 返回空 AK/SK，降级到标准库路径",
            file=sys.stderr,
        )
        return None
    # 成功：清除失败记录并记下人读来源。provider_name 用防御式 getattr（SDK
    # 版本差异：v1.0.4 的 CredentialModel 可能无此字段）。
    _LAST_SDK_FAILURE = None
    provider_name = getattr(model, "provider_name", None)
    _LAST_SDK_SOURCE = str(provider_name) if provider_name else _SDK_SOURCE_FALLBACK
    return (str(ak), str(sk), str(st) if st else None)


# ---------------------------------------------------------------------------
# 第 3 级：标准库降级（解析 ~/.aliyun/config.json）
# ---------------------------------------------------------------------------

# aliyun CLI 配置文件默认路径（可被 ALIBABA_CLOUD_CLI_CONFIG_FILE 覆盖，与 SDK 对齐）
_ALIYUN_CONFIG_PATH_ENV = "ALIBABA_CLOUD_CLI_CONFIG_FILE"
_DEFAULT_ALIYUN_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".aliyun", "config.json")


def _aliyun_config_path() -> str:
    """返回 aliyun CLI 配置文件路径（优先环境变量覆盖）。"""
    return os.environ.get(_ALIYUN_CONFIG_PATH_ENV) or _DEFAULT_ALIYUN_CONFIG_PATH


def _parse_sts_expiration(raw: Any) -> Optional[datetime]:
    """解析 ``sts_expiration`` 字段为 timezone-aware UTC datetime；无法解析返回 ``None``。

    兼容格式（aliyun CLI 实测）：
    - ``2026-09-14T12:00:00Z``（ISO 8601 + Z）
    - ``2026-09-14T12:00:00+08:00``（带偏移）
    - ``2026-09-14T12:00:00``（无时区，按 UTC 处理，与 SDK 语义一致）
    """
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip()
    # Python 3.9 的 fromisoformat 不支持 'Z'，统一替换为 +00:00
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _is_sts_expired(expiration_raw: Any) -> bool:
    """判定 STS 是否过期。``expiration_raw`` 无法解析视为未过期（宽容，让用户
    在下一次 RPC 401 时才拿到真实错误；避免 CLI 因时间格式差异误伤）。"""
    dt = _parse_sts_expiration(expiration_raw)
    if dt is None:
        return False
    return dt <= datetime.now(timezone.utc)


def _find_profile(data: Dict[str, Any], profile_name: str) -> Optional[Dict[str, Any]]:
    """从 config.json 顶层结构里找同名 profile；找不到返回 ``None``。"""
    profiles = data.get("profiles")
    if not isinstance(profiles, list):
        return None
    for item in profiles:
        if isinstance(item, dict) and item.get("name") == profile_name:
            return item
    return None


def _extract_sts_triple(profile: Dict[str, Any], mode: str) -> Tuple[str, str, Optional[str]]:
    """从 ``StsToken``/``OAuth`` mode 的 profile 抽三元组；过期抛 ``CredentialError``。"""
    ak = str(profile.get("access_key_id") or "")
    sk = str(profile.get("access_key_secret") or "")
    st = str(profile.get("sts_token") or "") or None
    if not ak or not sk or not st:
        raise CredentialError(
            "~/.aliyun/config.json 中 profile mode={} 缺少 access_key_id/"
            "access_key_secret/sts_token 三件套之一，无法降级。请执行 "
            "`aliyun configure --profile <name> --mode StsToken` 重配，或安装 "
            "`alibabacloud-credentials` 走 SDK 主路径。".format(mode),
            reason=REASON_MISSING_TRIPLE,
        )
    if _is_sts_expired(profile.get("sts_expiration")):
        raise CredentialError(
            "~/.aliyun/config.json 中 profile mode={} 的 STS 凭据已过期"
            "（sts_expiration={}）。标准库降级路径不做 refresh。请任选一种方式刷新：\n"
            "  1) 推荐：pip install alibabacloud-credentials，走 SDK 主路径自动"
            "后台刷新（OAuth profile 用 refresh_token 非交互续期）；\n"
            "  2) 或执行：aliyun configure --profile <name> 重新登录以刷新 STS 缓存。"
            .format(mode, profile.get("sts_expiration")),
            reason=REASON_STS_EXPIRED,
        )
    return (ak, sk, st)


def _stdlib_source(profile_name: str, mode: str) -> str:
    """标准库级命中时的人读来源描述（供 ``ResolvedCreds.source``）。"""
    return "~/.aliyun/config.json(profile={}, mode={})".format(profile_name, mode)


def _creds_from_aliyun_config(config_path: Optional[str] = None) -> Tuple[str, str, Optional[str]]:
    """纯标准库解析 ``~/.aliyun/config.json`` 取凭据；失败抛 ``CredentialError``。

    mode 分支：
    - ``AK``：直接返回 (access_key_id, access_key_secret, None)。
    - ``StsToken``：三件套 + 过期校验。
    - ``OAuth``：读缓存三件套（``access_key_id`` 通常带 ``STS.`` 前缀）+ 过期校验。
      **过期不做 refresh**（refresh 需网络 + PKCE + 写盘，与 SDK 重复），
      直接抛带指引错误。
    - 其他 mode（``RamRoleArn``/``EcsRamRole``/``ChainableRamRoleArn``/``External``
      /``CredentialsURI`` 等）：降级路径不支持（这些 mode 都需要网络或子进程），
      抛带指引错误让用户装 SDK 或改配 AK/StsToken profile。

    成功时顺带把人读来源写入 ``_LAST_STDLIB_SOURCE``，供
    ``resolve_creds_detailed`` 组装 ``ResolvedCreds.source``。
    """
    global _LAST_STDLIB_SOURCE
    path = config_path or _aliyun_config_path()
    if not os.path.isfile(path):
        raise CredentialError(
            "未找到 aliyun CLI 配置文件：{}。标准库降级路径需要 `aliyun configure` "
            "生成的 profile。请任选一种方式修复：\n"
            "  1) 执行 `aliyun configure --profile default --mode AK` 配置 AK/SK；\n"
            "  2) 或安装 `alibabacloud-credentials` 走 SDK 主路径（支持更多凭据源）；\n"
            "  3) 或在 sample .env 显式填 ALIYUN_ACCESS_KEY_ID/SECRET（最高优先）。"
            .format(path),
            reason=REASON_CONFIG_NOT_FOUND,
        )
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        raise CredentialError(
            "读取 aliyun CLI 配置 {} 失败：{}。请检查文件权限与 JSON 格式，或"
            "重新执行 `aliyun configure`。".format(path, exc),
            reason=REASON_CONFIG_NOT_FOUND,
        ) from None
    if not isinstance(data, dict):
        raise CredentialError(
            "aliyun CLI 配置 {} 顶层结构非 JSON 对象，无法解析。".format(path),
            reason=REASON_CONFIG_NOT_FOUND,
        )
    profile_name = str(data.get("current") or "").strip()
    if not profile_name:
        raise CredentialError(
            "aliyun CLI 配置 {} 缺少 `current` 字段（当前 profile 名）。请执行 "
            "`aliyun configure switch --profile <name>` 指定当前 profile。".format(path),
            reason=REASON_CONFIG_NOT_FOUND,
        )
    profile = _find_profile(data, profile_name)
    if profile is None:
        raise CredentialError(
            "aliyun CLI 配置 {} 中未找到 current={!r} 对应的 profile。请执行 "
            "`aliyun configure list` 检查，或 `aliyun configure --profile {}` 重配。"
            .format(path, profile_name, profile_name),
            reason=REASON_CONFIG_NOT_FOUND,
        )
    # S9：mode 大小写归一（aliyun CLI 实测写出 "AK"/"StsToken"/"OAuth"，但用户
    # 手改 config.json 可能写成 "ak"/"ststoken" 等；归一后按规范字面值匹配）。
    mode = str(profile.get("mode") or "").strip()
    mode_key = mode.lower()
    triple: Tuple[str, str, Optional[str]]
    if mode_key == "ak":
        ak = str(profile.get("access_key_id") or "")
        sk = str(profile.get("access_key_secret") or "")
        if not ak or not sk:
            raise CredentialError(
                "~/.aliyun/config.json profile={!r} mode=AK 但 access_key_id/"
                "access_key_secret 为空。请 `aliyun configure --profile {} --mode AK` "
                "重配。".format(profile_name, profile_name),
                reason=REASON_MISSING_TRIPLE,
            )
        triple = (ak, sk, None)
    elif mode_key in ("ststoken", "oauth"):
        triple = _extract_sts_triple(profile, mode)
    else:
        raise CredentialError(
            "~/.aliyun/config.json profile={!r} mode={!r} 不在标准库降级路径支持范围"
            "（仅支持 \"AK\" / \"StsToken\" / \"OAuth\"，大小写不敏感）。请任选一种方式：\n"
            "  1) 推荐：pip install alibabacloud-credentials，SDK 主路径支持全部 mode"
            "（含 RamRoleArn / EcsRamRole / CredentialsURI 等）；\n"
            "  2) 或改配 AK / StsToken profile：`aliyun configure --profile {} --mode AK`；\n"
            "  3) 或在 sample .env 显式填 ALIYUN_ACCESS_KEY_ID/SECRET。"
            .format(profile_name, mode, profile_name),
            reason=REASON_UNSUPPORTED_MODE,
        )
    _LAST_STDLIB_SOURCE = _stdlib_source(profile_name, mode)
    return triple


# ---------------------------------------------------------------------------
# 主入口：三级链
# ---------------------------------------------------------------------------


def _sdk_failure_summary() -> str:
    """聚合错误消息里第 [2] 级的**如实**描述（四种失败态不再混为一谈）。

    优先用 ``_creds_from_sdk`` / ``_get_sdk_client`` 写下的精确原因；拿不到
    （比如消费点直接 mock 了 ``_creds_from_sdk``）时回退到模块级安装态判定。
    """
    if _LAST_SDK_FAILURE:
        return _LAST_SDK_FAILURE
    if CredentialClient is None:
        return _SDK_FAIL_NOT_INSTALLED
    return "{}，见 stderr".format(_SDK_FAIL_GET_CREDENTIAL)


def _resolve_chain(config: Dict[str, str]) -> ResolvedCreds:
    """三级降级链的**唯一实现**；两个公开入口均委托它。

    保持只调一次 ``_creds_from_explicit`` / ``_creds_from_sdk`` /
    ``_creds_from_aliyun_config``（且均无参），以便消费方与单测可精确打桩。
    """
    global _LAST_SDK_SOURCE, _LAST_STDLIB_SOURCE
    # 每次解析前先清来源，避免上一次（甚至上一个用例）的来源泄漏到本次结果。
    _LAST_SDK_SOURCE = None
    _LAST_STDLIB_SOURCE = None

    # 第 1 级：显式（半填会直接抛 CredentialError，拒绝静默降级）
    explicit = _creds_from_explicit(config)
    if explicit is not None:
        return ResolvedCreds(
            explicit[0], explicit[1], explicit[2], LEVEL_EXPLICIT, _EXPLICIT_SOURCE
        )
    # 第 2 级：SDK
    sdk_creds = _creds_from_sdk()
    if sdk_creds is not None:
        return ResolvedCreds(
            sdk_creds[0],
            sdk_creds[1],
            sdk_creds[2],
            LEVEL_SDK,
            _LAST_SDK_SOURCE or _SDK_SOURCE_FALLBACK,
        )
    # 第 3 级：标准库降级
    try:
        stdlib_creds = _creds_from_aliyun_config()
    except CredentialError as exc:
        # 三级全败：抛统一 CredentialError（保留第 3 级的具体原因，前置总纲指引）。
        # reason 透传第 3 级的结构化原因（如 STS 过期），供消费方稳定分类。
        raise CredentialError(
            "凭据链三级降级全部失败，无法解析 AK/SK。已尝试：\n"
            "  [1] sample .env 显式 ALIYUN_ACCESS_KEY_ID/SECRET —— 未填或占位；\n"
            "  [2] alibabacloud_credentials SDK 默认凭据链 —— {sdk}；\n"
            "  [3] 标准库解析 ~/.aliyun/config.json —— {stdlib}。\n"
            "下一步（任选其一即可）：\n"
            "  A) 推荐：pip install alibabacloud-credentials 并执行 `aliyun configure`"
            "（OAuth 登录一次，SDK 后台自动刷新）；\n"
            "  B) 或 `aliyun configure --profile default --mode AK` 配长期 AK；\n"
            "  C) 或在 sample .env 显式填 ALIYUN_ACCESS_KEY_ID/SECRET（最高优先，"
            "适合 CI / 教学固定凭证）。".format(
                # 两侧均经 _one_period 归一，模板再补唯一句号（修双句号）。
                sdk=_one_period(_sdk_failure_summary()),
                stdlib=_one_period(str(exc)),
            ),
            reason=exc.reason or REASON_SDK_UNAVAILABLE,
        ) from None
    return ResolvedCreds(
        stdlib_creds[0],
        stdlib_creds[1],
        stdlib_creds[2],
        LEVEL_STDLIB,
        _LAST_STDLIB_SOURCE or "~/.aliyun/config.json",
    )


def resolve_creds_detailed(config: Dict[str, str]) -> ResolvedCreds:
    """三级降级解析凭据，**额外返回命中级别与人读来源**。

    供需要可观测性的调用方使用（典型：``sample.py --check`` 要把「凭据从哪里来」
    说清楚）。返回 :class:`ResolvedCreds`，它本身就是 tuple，前三个字段与
    ``resolve_creds`` 的返回值逐位相等，可直接解包：

    ::

        resolved = credentials.resolve_creds_detailed(config)
        ak, sk, token = resolved[:3]          # 等价于 resolve_creds(config)
        print(resolved.level, resolved.source) # "sdk" / "EcsRamRoleCredentialsProvider"

    level 取值域：``"explicit"`` / ``"sdk"`` / ``"stdlib"``（常量
    :data:`LEVEL_EXPLICIT` / :data:`LEVEL_SDK` / :data:`LEVEL_STDLIB`）。

    异常语义与 ``resolve_creds`` 完全一致：显式凭据半填、三级全败、STS 过期
    均抛 :class:`CredentialError`（message 自带下一步指引）。
    """
    return _resolve_chain(config)


def resolve_creds(config: Dict[str, str]) -> Tuple[str, str, Optional[str]]:
    """三级降级解析 RPC 凭据三元组 ``(access_key_id, access_key_secret, security_token|None)``。

    优先级：
    1. ``config`` 显式 ``ALIYUN_ACCESS_KEY_*`` **两项均**非占位（向后兼容 / CI）；
       两项均未填则降级，**恰好一项非填则抛 ``CredentialError``**（拒绝静默
       降级到可能是另一个阿里云账号的凭据链）；
    2. ``alibabacloud_credentials`` SDK 默认凭据链（OAuth 自动刷新，主路径）；
    3. 纯标准库解析 ``~/.aliyun/config.json``（AK / StsToken / OAuth 三 mode）。

    三级全部落空 → 抛 :class:`CredentialError`，message 内自带三途径下一步指引。
    调用方（``flow.creds_from_env`` / ``control_plane._call``）应把异常透传给
    ``sample.py`` 顶层的统一错误出口。

    本函数签名与行为向后兼容（内部委托 :func:`resolve_creds_detailed`）。需要
    知道命中哪一级、凭据从哪里来 → 用 :func:`resolve_creds_detailed`。
    """
    resolved = _resolve_chain(config)
    return (resolved.access_key_id, resolved.access_key_secret, resolved.security_token)


# ---------------------------------------------------------------------------
# 离线探测公开 API（probe_* 三件套）：供 sample.py --check 纯离线体检使用
#
# 三者均为薄委托：只把上面已有的私有只读逻辑用公开名字暴露出来，绝不复制判定
# 逻辑（两份实现必然发散）。硬约束：不联网、不刷新、不写盘、不构造 SDK 客户端。
# ---------------------------------------------------------------------------


def probe_explicit(config: Dict[str, str]) -> Optional[ResolvedCreds]:
    """**离线探测**第 1 级：``.env`` 显式 ``ALIYUN_ACCESS_KEY_*`` 是否可用（只读）。

    与 :func:`resolve_creds` 第 1 级的语义**完全一致**（同一份实现，薄委托
    :func:`_creds_from_explicit`），三种情形：

    - 两项均非占位 → 返回 :class:`ResolvedCreds`（``level="explicit"``、
      ``source=".env 显式 ALIYUN_ACCESS_KEY_*"``，与 ``resolve_creds_detailed``
      在显式级上的取值逐字相同）；
    - 两项均缺/占位 → 返回 ``None``（表示本级不可用，交凭据链降级）；
    - **恰好一项非占位（半填）→ 抛 :class:`CredentialError`**，message 与真实
      解析路径逐字相同。体检必须把这类配置错误暴露给用户（拒绝静默降级到可能
      是另一个阿里云账号的凭据链），故此处**不得**改成返回 ``None``。

    无副作用：只读 ``config``，不触碰 SDK、不读 ``~/.aliyun/config.json``、不写盘。
    """
    explicit = _creds_from_explicit(config)
    if explicit is None:
        return None
    return ResolvedCreds(
        explicit[0], explicit[1], explicit[2], LEVEL_EXPLICIT, _EXPLICIT_SOURCE
    )


def probe_sdk_installed() -> bool:
    """**离线探测**第 2 级：``alibabacloud_credentials`` 是否已安装（只读，返回 bool）。

    只判定模块级 ``CredentialClient`` 是否为 ``None``（import 失败时置 ``None``）。
    **绝不构造 ``CredentialClient()``、绝不调用 ``get_credential()``**：构造客户端会
    eager 构造整条 provider 链，末尾的 ``EcsRamRoleCredentialsProvider`` 在无凭据
    机器上会探 ``100.100.100.200:80``（固定 ~2.0s 超时），OAuth profile 还可能
    触发后台续期并回写 ``~/.aliyun/config.json`` —— 全部违背离线口径。

    因此本函数只能回答「装没装」，回答不了「SDK 级是否真的命中」。后者请用
    :func:`resolve_creds_detailed`（``sample.py --check --creds-live``）。
    """
    return CredentialClient is not None


def probe_stdlib() -> ResolvedCreds:
    """**离线探测**第 3 级：纯标准库只读解析 ``~/.aliyun/config.json``。

    薄委托 :func:`_creds_from_aliyun_config`（与真实解析路径同一份实现），成功返回
    :class:`ResolvedCreds`：

    - ``level`` 恒为 ``"stdlib"``；
    - ``source`` 为 ``~/.aliyun/config.json(profile=<name>, mode=<mode>)``，与
      ``resolve_creds_detailed`` 在标准库级上的取值逐字相同 —— 调用方**无需**再读
      模块级私有变量 ``_LAST_STDLIB_SOURCE``；
    - 前三字段即该 profile 的三元组（AK / StsToken / OAuth 三 mode，含 STS 过期判定）。

    失败（文件缺失 / JSON 非法 / 缺 ``current`` / profile 不存在 / mode 不支持 /
    STS 已过期等）抛 :class:`CredentialError`，message 与真实解析路径逐字相同，
    便于体检原样逐行透传给用户。**不做 refresh**（refresh 需网络 + PKCE + 写盘，
    超出离线探测职责）；唯一写入的是进程内可观测状态 ``_LAST_STDLIB_SOURCE``
    （与真实解析路径一致，不写盘）。

    配置路径解析同真实路径：优先 ``ALIBABA_CLOUD_CLI_CONFIG_FILE``，否则
    ``~/.aliyun/config.json``。
    """
    global _LAST_STDLIB_SOURCE
    # 与 _resolve_chain 同一纪律：先清来源再解析，避免上一次（甚至上一个用例）
    # 的来源泄漏到本次结果；委托方未写来源时回退到通用描述。
    _LAST_STDLIB_SOURCE = None
    stdlib = _creds_from_aliyun_config()
    return ResolvedCreds(
        stdlib[0],
        stdlib[1],
        stdlib[2],
        LEVEL_STDLIB,
        _LAST_STDLIB_SOURCE or "~/.aliyun/config.json",
    )


# ---------------------------------------------------------------------------
# SDK 线程防护：只对可归因于 SDK 构造的线程标 daemon=True
# ---------------------------------------------------------------------------


def _daemonize_new_threads(candidates: Iterable[Any]) -> List[str]:
    """把候选线程标 ``daemon=True``（best-effort），返回成功标记者的名字列表。

    ``candidates`` **必须是 ``threading.enumerate()`` 的差集**（即「构造 SDK 后
    多出来的线程」），由 :func:`_get_sdk_client` 在构造前后各快照一次得出。
    严禁传全量线程列表 —— 那会把回写 ``~/.aliyun/config.json`` 的线程、以及宿主
    进程（把 ``sample.py`` 当模块 import）的业务线程一并标 daemon，而 daemon
    线程会在主线程退出时被静默强杀（可能丢数据）。

    局限（诚实记录）：``Thread.daemon`` setter 对 ``_started`` 已置位的线程抛
    ``RuntimeError``，而 ``threading.enumerate()`` 只收录已 ``start()`` 的线程。
    仅当线程还停在 ``threading._limbo``（``start()`` 已登记、``_bootstrap_inner``
    尚未 ``_started.set()``）的短窗口内才改得动。所以本函数是**尽力而为**：
    它的真实价值在于（1）趁主线程还在运行时立即试（放到 atexit 则 100% 试
    不中），（2）把作用域收敛到 SDK 可归因线程。若 SDK 真起了阻塞退出的非
    daemon 线程，本兜底救不了 —— 那种情况需要升级 SDK 或换 profile mode。
    """
    current = threading.current_thread()
    marked: List[str] = []
    for th in list(candidates):
        # 双保险：即使调用方误传了全量集合，也至少不碰主线程。
        if th is current or getattr(th, "name", None) == "MainThread":
            continue
        try:
            if th.daemon:
                continue  # 已是 daemon：无需处理，也避免无意义的异常
            th.daemon = True
        except (RuntimeError, AttributeError):
            # 已启动线程（或不允许改属性的伪线程对象）：忽略，见上方「局限」。
            continue
        marked.append(str(getattr(th, "name", th)))
    return marked


def ensure_daemon_threads(candidate_threads: Optional[Iterable[Any]] = None) -> List[str]:
    """**兼容入口**：把给定候选集合内的线程标 ``daemon=True``，返回标记成功的名字。

    行为变更（重要）：``candidate_threads=None``（默认）时**什么都不做**，不再
    无差别遍历 ``threading.enumerate()``。理由：

    (a) ``Thread.daemon`` setter 对已启动线程抛 ``RuntimeError``，而
        ``threading.enumerate()`` 返回的全是已启动线程 —— 旧的无差别遍历恒走
        except，等价于什么都没做（结构性无效的假兜底）；
    (b) 即使能改，无差别遍历也会误伤不属于 SDK 的线程（回写
        ``~/.aliyun/config.json`` 的线程、宿主进程的业务线程）。

    真正生效的防护在 :func:`_get_sdk_client` 里于 ``CredentialClient()`` 构造
    前后各快照一次 ``threading.enumerate()``，只对**差集**调本模块的
    :func:`_daemonize_new_threads`，同步执行、不依赖 atexit。

    本函数保留为公开 API，供调用方显式传入自己认定的候选集合（比如自己
    构造 SDK 客户端前后的快照差集）。
    """
    if candidate_threads is None:
        return []
    return _daemonize_new_threads(candidate_threads)


def install_atexit_guard() -> None:
    """**兼容入口**：把 :func:`ensure_daemon_threads` 注册到 ``atexit``（幂等）。

    ``sample.py`` 头部调一次即可：``credentials.install_atexit_guard()``。

    **真正生效的防护在 SDK 构造时同步执行**（见 :func:`_get_sdk_client`），本函数
    仅为兼容保留。不要指望它兜住 CLI 挂住：

    (a) atexit 运行时 ``threading.enumerate()`` 里的线程全部早已 ``_started``，
        ``daemon`` setter 恒抛 ``RuntimeError``；
    (b) CPython ``Py_FinalizeEx`` 先 ``wait_for_thread_shutdown()``（join 非 daemon
        线程）再跑 atexit 钩子 —— 真挂住时本钩子根本轮不到执行。
    """
    atexit.register(ensure_daemon_threads)
