"""`.env` 解析、占位符检测与 `--check` 体检。

约定：
- 解析规则：``KEY=VALUE`` 一行一项；``#`` 开头为注释；值两端引号（成对单/双引号）剥离。
- 占位符检测：值含 ``<YOUR_`` 或为空 → 视为缺失（模板未填）。
- 优先级：进程环境变量 > ``.env`` 文件值（便于 CI / 脚本注入覆盖）；两侧取值都 ``strip()``。
- 派生：``derive_defaults`` **纯离线**（仅字典运算，无网络/文件 IO），显式值永远优先。
- ``ENVIRONMENT`` 会做 strip+lower 归一化与白名单校验，非法值抛 ``EnvError``
  （继承 ``lib.rpc.RpcError``，已在 ``sample.py`` 的统一错误出口白名单内 → 用户看到
  一行带指引的 ``[error]``，而非裸栈）。
"""

import os
import sys
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlsplit

from .rpc import RpcError

SAMPLE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(SAMPLE_DIR, ".env")

PLACEHOLDER_MARK = "<YOUR_"

#: ``ENVIRONMENT`` 的合法取值（归一化后比较：``strip().lower()``）。
#: 不在白名单的值一律报错——绝不静默按 production 派生登录域：
#: ``SIGNIN_BASE_URL`` 是 OAuth authorize + token 兑换端点，派生错域名会把 PKCE
#: 授权码/client_secret 发往另一套环境，失败表现为 invalid_client / redirect_uri
#: 不匹配 / audience 不符，与真因（拼写）完全无关，排障成本极高。
_VALID_ENVIRONMENTS = ("production", "pre-release")

#: ``ENVIRONMENT`` 缺失/占位时的默认值（等价于 production 形态的 ``SIGNIN_BASE_URL``
#: 派生，但**不**触发 ``POOL_JWKS_BASE`` 镜像——见 ``derive_defaults`` 步骤 5）。
DEFAULT_ENVIRONMENT = "production"

#: W2 幂等标记键：``derive_defaults`` 把 ENVIRONMENT 默认值写回输出 dict 时，
#: 同时写入本标记（值恒为 "1"）。二次派生时凭标记识别「这个 production 是上次
#: 默认化的产物，不是用户声明」，从而保持 ``environment_declared=False``，
#: ``POOL_JWKS_BASE`` 不会在 re-derive 时从空翻转为登录域（f(f(x)) == f(x)）。
#: 内部键不在 ENV_SCHEMA 内：render_check_report/check_env/writeback_env 均只
#: 遍历 ENV_SCHEMA 或显式 updates，不会泄漏到报告或 .env 回写。
ENVIRONMENT_DEFAULTED_MARKER = "_ENVIRONMENT_DEFAULTED"

#: D-Minor3：「未填 = 走凭据链」的可选凭据类键（render_check_report 的
#: [OPTIONAL-EMPTY] 行对它们额外标注语义，与 ENV_SCHEMA 的 hint 口径一致）。
_CRED_CHAIN_OPTIONAL_KEYS = frozenset((
    "ALIYUN_ACCESS_KEY_ID",
    "ALIYUN_ACCESS_KEY_SECRET",
    "ALIYUN_SECURITY_TOKEN",
))


class EnvError(RpcError):
    """``.env`` 配置非法（如 ``ENVIRONMENT`` 取值不在白名单）：message 自带修正指引。

    继承 ``lib.rpc.RpcError`` 而非裸 ``Exception``：``sample.py`` 的统一错误出口
    （``main()`` 的 except 白名单）已捕获 ``RpcError``，因此无需改动 ``sample.py``
    即可让用户看到一行 ``[error] …`` + 下一步指引，而不是裸栈。
    ``rpc`` 模块只依赖标准库且不反向 import ``env``，故无循环依赖风险。

    ``RpcError.__init__`` 的签名是 ``(status, code, message, request_id, retryable)``，
    配置错误没有 HTTP 语义，这里固定 ``status=0`` / ``code=InvalidConfiguration``，
    并重写 ``__str__`` 只回显 message（避免带上 ``HTTP 0`` 这类误导性前缀）。
    """

    def __init__(self, message: str):
        Exception.__init__(self, message)
        self.status = 0
        self.code = "InvalidConfiguration"
        self.message = message
        self.request_id = ""
        self.retryable = False

    def __str__(self) -> str:
        return self.message


def _warn(msg: str) -> None:
    """派生类提示：写 stderr（不污染 stdout 上的 ``--check`` 报告与 JSON 输出）。"""
    print("[env] {}".format(msg), file=sys.stderr)


# 每个键：(是否必填, 用途分组, 「在哪取值」指引文案)
ENV_SCHEMA = {
    # ---- 环境与账号 ----
    "REGION": (
        True,
        "环境与账号",
        "地域 ID（如 cn-hangzhou）：控制台右上角，或产品文档地域列表页。",
    ),
    "ENVIRONMENT": (
        False,
        "环境与账号",
        "环境维度，合法取值只有 production / pre-release（大小写与首尾空格自动归一化，"
        "其余值直接报错）；缺失/留空按 production 处理。决定 SIGNIN_BASE_URL 的派生形态"
        "（production → https://signin-<region>.aliyunagentid.com；"
        "pre-release → https://signin.<region>.aliyuncs.com），显式填则覆盖。"
        "POOL_JWKS_BASE 仅在**显式声明** ENVIRONMENT=production 时才镜像为 SIGNIN_BASE_URL；"
        "删除本行/留空 = 存量 .env 的向后兼容行为（POOL_JWKS_BASE 留空走 DATA_ENDPOINT）。",
    ),
    "ALIYUN_ACCESS_KEY_ID": (
        False,
        "环境与账号",
        "可选：留空则走 aliyun CLI 凭据链（推荐，aliyun configure 一次即可，"
        "凭据从 ~/.aliyun/config.json 或 SDK 默认链解析）；显式填写则最高优先"
        "（向后兼容/CI）。两项必须同时填或同时留空；只填一项会直接报错，不再静默"
        "降级到凭据链。取值：RAM 访问控制 → 用户 → AccessKey 管理。",
    ),
    "ALIYUN_ACCESS_KEY_SECRET": (
        False,
        "环境与账号",
        "可选：留空则走 aliyun CLI 凭据链（推荐）；显式填写则与 "
        "ALIYUN_ACCESS_KEY_ID 成对生效，最高优先（向后兼容/CI）。两项必须同时填"
        "或同时留空；只填一项会直接报错，不再静默降级到凭据链。",
    ),
    "ALIYUN_SECURITY_TOKEN": (
        False,
        "环境与账号",
        "可选：STS 临时凭证的 SecurityToken（用长期 AK 则留空）。",
    ),
    # ---- 服务端点 ----
    "CONTROL_ENDPOINT": (
        False,
        "服务端点",
        "控制面端点，形态 agentidentity.<region>.aliyuncs.com（region 替换为 REGION 值）；"
        "留空将由 REGION+ENVIRONMENT 自动派生。",
    ),
    "DATA_ENDPOINT": (
        False,
        "服务端点",
        "数据面端点，形态 agentidentitydata.<region>.aliyuncs.com（注意与控制面域名不同）；"
        "留空将由 REGION+ENVIRONMENT 自动派生。",
    ),
    "SIGNIN_BASE_URL": (
        False,
        "服务端点",
        "池 OAuth 登录根地址，形态因环境而异（如 https://signin.<region>.aliyuncs.com "
        "或正式环境的登录域）；控制台用户池详情页展示的地址为准。token 兑换走此域名。"
        "留空将由 REGION+ENVIRONMENT 自动派生。",
    ),
    "POOL_JWKS_BASE": (
        False,
        "服务端点",
        "可选：池 discovery / JWKS 的域名根（setup 创建 IdentityProvider 的 "
        "DiscoveryURL 用它）。留空时按 ENVIRONMENT 分两种情形："
        "① 未显式声明 ENVIRONMENT（存量 .env 形态）或 ENVIRONMENT=pre-release → "
        "保持原默认行为走 DATA_ENDPOINT（预发实测池 discovery 在数据面公网路径）；"
        "② 显式声明 ENVIRONMENT=production → 自动镜像为 SIGNIN_BASE_URL"
        "（新加坡 ap-southeast-1 等正式环境池 discovery/JWKS 走登录域，数据面同路径 404）。"
        "显式填写则最高优先（含/不含 https:// 前缀均可）。",
    ),
    # ---- 管控面产出 ----
    "USER_POOL_ID": (
        True,
        "管控面产出",
        "用户池 ID（up_ 前缀）：setup 产出，或控制台「用户池」列表抄录。",
    ),
    "OAUTH_CLIENT_ID": (
        True,
        "管控面产出",
        "池 OAuth 客户端 ID（client_ 前缀）：setup 产出，或控制台用户池详情"
        "「OAuth 客户端」页抄录。",
    ),
    "OAUTH_CLIENT_SECRET": (
        True,
        "管控面产出",
        "池 OAuth 客户端密钥：setup 产出，或控制台客户端详情创建密钥后抄录；"
        "也可只填 OAUTH_CLIENT_SECRET_FILE（0600 文件优先）。",
    ),
    "OAUTH_CLIENT_SECRET_FILE": (
        False,
        "管控面产出",
        "可选：密钥文件（单行、0600），填了则优先于 OAUTH_CLIENT_SECRET。",
    ),
    "OAUTH_REDIRECT_URI": (
        True,
        "管控面产出",
        "回调地址，默认 http://127.0.0.1:8765/callback；需在池 OAuth 客户端"
        " redirect_uri 白名单内（含任意一条 loopback 条目即放行且忽略端口）。",
    ),
    # ---- 身份升维与出站 ----
    "WI_NAME": (
        True,
        "身份升维与出站",
        "工作负载身份名：setup 产出，或控制台「工作负载身份」列表抄录"
        "（须 SessionBindingEnabled=true，否则 OBO 报 InboundCredentialMissing）。",
    ),
    "OBO_PROVIDER_NAME": (
        True,
        "身份升维与出站",
        "出站资源凭证提供商名：setup 产出，或控制台「凭证提供商」列表抄录"
        "（配额=1，若已存在将提示复用）。",
    ),
    # ---- 订单服务 ----
    "ORDER_SERVICE_AUDIENCE": (
        True,
        "订单服务",
        "订单服务受众：IDaaS 控制台该企业服务应用详情页的 audience 标识"
        "（如 test-aud）；不是 OBO provider 的 OutboundAudience（agent-… 形态），"
        "误传报 Forbidden.IdaasRsNotAuthorized。",
    ),
    "ORDER_SERVICE_SCOPES": (
        False,
        "订单服务",
        "申请的 scope，逗号分隔，默认 read,write.all。",
    ),
    "ORDER_SERVICE_ISSUER": (
        False,
        "订单服务",
        "订单服务令牌 issuer：GET {IDAAS_ORIGIN}/api/v2/iauths_system/oauth2/"
        ".well-known/openid-configuration 返回 JSON 的 issuer 字段；"
        "留空将由 IDAAS_ORIGIN 运行时拉 discovery 自动填充。",
    ),
    "ORDER_SERVICE_JWKS_URI": (
        False,
        "订单服务",
        "订单服务 JWKS 端点：同上 discovery 返回 JSON 的 jwks_uri 字段（公网可达）；"
        "留空将由 IDAAS_ORIGIN 运行时拉 discovery 自动填充。",
    ),
    "IDAAS_ORIGIN": (
        True,
        "订单服务",
        "IDaaS 实例域名根（如 https://xxx.cloud-idaas.com），用于自动拉 discovery 文档"
        "填充 ORDER_SERVICE_ISSUER/ORDER_SERVICE_JWKS_URI；若已显式填 "
        "ORDER_SERVICE_ISSUER 可留空，将反向推导。",
    ),
    # ---- 仅 setup --mode=script ----
    "SETUP_POOL_NAME": (False, "setup 脚本", "模式 B 用户池名，默认 idaas-obo-sample-pool。"),
    "SETUP_CLIENT_NAME": (False, "setup 脚本", "模式 B 池 OAuth 客户端名，默认 idaas-obo-sample-cli。"),
    "SETUP_IDP_NAME": (False, "setup 脚本", "模式 B 身份提供商名，默认 idaas-obo-sample-idp。"),
    "SETUP_IDP_TYPE": (False, "setup 脚本", "绑定 IDaaS 的身份源类型（默认 IDaaS，以产品实际支持为准）。"),
    "SETUP_IDP_METADATA": (False, "setup 脚本", "绑定身份源的 IdP 元数据 JSON（以产品文档字段为准）。"),
    "SETUP_OBO_VENDOR": (False, "setup 脚本", "出站凭证提供商厂商类型（默认 IDaaS）。"),
    "SETUP_OBO_PROVIDER_CONFIG": (
        False,
        "setup 脚本",
        "出站提供商配置 JSON（clientId/clientSecret 等，指向 IDaaS 侧订单服务应用）。",
    ),
}

SETUP_ONLY_KEYS = {
    "SETUP_POOL_NAME",
    "SETUP_CLIENT_NAME",
    "SETUP_IDP_NAME",
    "SETUP_IDP_TYPE",
    "SETUP_IDP_METADATA",
    "SETUP_OBO_VENDOR",
    "SETUP_OBO_PROVIDER_CONFIG",
}


def parse_env_file(path: str) -> Dict[str, str]:
    """解析 .env 文件：KEY=VALUE、# 注释、值两端成对引号剥离。

    解析失败的行（无 = 、空键）直接跳过，不抛异常——.env 是用户手填文件，
    容错优先，缺项由 check_env 统一给出指引。

    文件存在但不可读（权限不足/是目录等 OSError）时抛 :class:`EnvError`
    并附权限指引（I-S2）：旧实现裸抛 PermissionError 栈，而 EnvError 继承
    RpcError、已在 sample.py main 的异常白名单内，用户看到的是一行
    ``[error] …`` + 下一步指引而非裸栈。文件不存在仍返回空 dict（合法形态）。
    """
    result: Dict[str, str] = {}
    if not os.path.isfile(path):
        return result
    try:
        fh = open(path, "r", encoding="utf-8")
    except OSError as exc:
        raise EnvError(
            "无法读取 .env 文件 {}：{}。请检查文件权限（建议 0600，如："
            "chmod 600 {}）与路径是否正确后重跑。".format(path, exc, path)
        ) from None
    with fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # 剥离两端成对的单/双引号
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            if key:
                result[key] = value
    return result


def load_env(env_file: Optional[str] = None) -> Dict[str, str]:
    """加载 .env 并叠加进程环境变量（环境变量优先）。

    进程环境变量的值同样做 ``strip()``：与 ``parse_env_file`` 的解析语义对齐，
    避免 CI/脚本注入的 ``ENVIRONMENT=" pre-release "`` 这类带首尾空白的值逃过
    归一化（其余键也按原值使用，如带空白的 endpoint 会直接拼进 URL）。
    strip 后为空则视为未注入，保留 ``.env`` 里的值。
    """
    env = parse_env_file(env_file or ENV_FILE)
    for key in ENV_SCHEMA:
        if key in os.environ:
            value = (os.environ[key] or "").strip()
            if value != "":
                env[key] = value
    return env


def is_placeholder(value: str) -> bool:
    """占位符/空值检测。

    两种占位形态均视为未填：
    - 模板尖括号占位（``<YOUR_...>``、``<agentidentity.YOUR_REGION...>``）；
    - 空值/纯空白。
    """
    if value is None:
        return True
    value = value.strip()
    if not value:
        return True
    if PLACEHOLDER_MARK in value:
        return True
    # 模板占位语法：<...>（真实配置值不会含尖括号）
    return value.startswith("<") and value.endswith(">")


def check_env(
    env: Dict[str, str],
    skip_setup_keys: bool = True,
) -> Tuple[bool, List[str]]:
    """逐项体检。返回 (全部通过, 缺失键列表)。

    - skip_setup_keys=True（默认）：跳过 SETUP_* 键（仅 setup --mode=script
      需要，且大多有默认值兜底，数据面四步不依赖）。
    - skip_setup_keys=False（setup 预检模式）：SETUP_* 键视为必填，
      未填/占位符同样计入缺失——提示用户从模板抄录显式值。
    """
    missing: List[str] = []
    for key, (required, _group, _hint) in ENV_SCHEMA.items():
        if skip_setup_keys and key in SETUP_ONLY_KEYS:
            continue
        effective_required = required or (
            not skip_setup_keys and key in SETUP_ONLY_KEYS
        )
        if not effective_required:
            continue
        if key not in env or is_placeholder(env.get(key, "")):
            missing.append(key)
    return (not missing), missing


def _fallback_from_endpoint(endpoint: str, prefix: str) -> str:
    """从 endpoint 兜底推断 region（agentidentity.<region>.aliyuncs.com → <region>）。"""
    if not endpoint:
        return ""
    host = endpoint.split("://")[-1].split("/")[0]
    parts = host.split(".")
    if len(parts) >= 3 and parts[0].startswith(prefix):
        return parts[1]
    return ""


def _extract_origin(url: str) -> str:
    """从 URL 反向提取 origin（scheme://host[:port]）。

    用于 IDAAS_ORIGIN 反向兜底：从 ORDER_SERVICE_ISSUER 提取域名根。
    解析失败（无 scheme/无 host，或 ``urlsplit`` 对畸形 URL 抛 ``ValueError``，
    如 ``https://[::1/x`` 这类残缺的 IPv6 方括号）一律返回空串，由调用方决定
    是否回填——本函数处于 ``derive_defaults`` 路径上，而后者是每个子命令入口
    的第一道调用，绝不能因用户写错的 issuer 而裸栈崩溃。
    """
    if not url or is_placeholder(url):
        return ""
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return ""
    if not parts.scheme or not parts.netloc:
        return ""
    return "{}://{}".format(parts.scheme, parts.netloc)


def derive_defaults(env: Dict[str, str]) -> Dict[str, str]:
    """对可为空的键补默认值与正向/反向派生（纯离线，仅字典运算，无网络/文件 IO）。

    派生顺序：
    1. ENVIRONMENT 归一化（``strip().lower()``）+ 白名单校验；缺失/占位 → production；
    2. 固定默认值（scopes/redirect_uri/setup_*）；
    3. REGION 反向兜底（从 CONTROL_ENDPOINT/DATA_ENDPOINT 推断）；
    4. 正向派生 CONTROL_ENDPOINT/DATA_ENDPOINT（REGION 非空且目标为占位）；
    5. 正向派生 SIGNIN_BASE_URL（REGION+ENVIRONMENT）；POOL_JWKS_BASE 仅在
       **显式声明** ENVIRONMENT=production 时镜像为 SIGNIN_BASE_URL；
    6. IDAAS_ORIGIN 反向兜底（从 ORDER_SERVICE_ISSUER 提取 scheme+host）。

    所有正向派生仅当目标键为占位/空时才填，显式值永远优先（向后兼容）。
    归一化后的 ENVIRONMENT 会写回返回 dict，下游一律用归一化值。

    幂等契约（W2）：``f(f(x)) == f(x)``——对同一输入重复派生结果不变，尤其
    「未声明 ENVIRONMENT → 默认 production」的存量形态在二次派生时**不会**被
    误判为「显式声明 production」而把 POOL_JWKS_BASE 从空翻转为登录域。
    实现：默认化写回 ENVIRONMENT 的同时写入内部标记键
    :data:`ENVIRONMENT_DEFAULTED_MARKER`，re-derive 时凭标记识别「默认化产物
    ≠ 用户声明」；显式声明（含归一化写回，如 ``" Pre-Release "`` →
    ``pre-release``）则移除标记。标记键不在 ENV_SCHEMA 内，不泄漏到报告/.env 回写。

    注意：discovery 网络拉取不在此处——由 lib/discovery.py 的 apply_discovery 承担，
    sample.py 在 demo/serve-orders 入口显式触发。

    Raises:
        EnvError: ENVIRONMENT 显式填了白名单（``_VALID_ENVIRONMENTS``）之外的值。
            绝不静默当 production：否则预发用户一个拼写就会把 OAuth authorize/
            token 兑换发往正式登录域，报错却是 invalid_client / redirect_uri 不匹配。
    """
    merged = dict(env)

    # 1. ENVIRONMENT 归一化 + 白名单校验
    #    environment_declared 记录「用户是否显式声明了这个键」（默认化之前）：
    #    步骤 5 的 POOL_JWKS_BASE 镜像门控靠它区分「显式声明 production」与
    #    「键缺失被默认成 production」——后者正是存量 .env 的形态（本仓 .env
    #    就没有 ENVIRONMENT 这个键），必须保持旧行为（POOL_JWKS_BASE 留空 →
    #    control_plane._pool_wellknown_host() 走 DATA_ENDPOINT），否则零操作下
    #    静默翻转会把 setup 的 DiscoveryURL 打到登录域（预发登录域同路径可能
    #    404，或返回 VPC 专用域名 → NXDOMAIN，故障延迟到 login/JIT 建档才暴露）。
    raw_environment = (merged.get("ENVIRONMENT") or "").strip()
    # W2 幂等：上次派生默认化产物（带标记）视同未声明，否则二次派生会把
    # 「默认 production」误判为「显式声明 production」→ POOL_JWKS_BASE 翻转。
    environment_declared = (
        not is_placeholder(raw_environment)
        and not merged.get(ENVIRONMENT_DEFAULTED_MARKER)
    )
    if environment_declared:
        environment = raw_environment.lower()
        if environment not in _VALID_ENVIRONMENTS:
            raise EnvError(
                "ENVIRONMENT 取值非法：{!r}。合法取值只有：{}（大小写与首尾空格会自动"
                "归一化，如 Pre-Release / \" pre-release \" 均可）。请修正 {} 里的 "
                "ENVIRONMENT 行后重跑；若要沿用存量默认行为，删除该行或留空即可。".format(
                    raw_environment,
                    " / ".join(_VALID_ENVIRONMENTS),
                    ENV_FILE,
                )
            )
        # 显式声明：写回归一化值并清除默认化标记（声明覆盖一切历史标记）。
        merged.pop(ENVIRONMENT_DEFAULTED_MARKER, None)
    else:
        environment = DEFAULT_ENVIRONMENT
        # 默认化产物带标记写回：下游能拿到生效值，re-derive 能识别非用户声明。
        merged[ENVIRONMENT_DEFAULTED_MARKER] = "1"
    merged["ENVIRONMENT"] = environment

    # 2. 固定默认值
    if not merged.get("ORDER_SERVICE_SCOPES"):
        merged["ORDER_SERVICE_SCOPES"] = "read,write.all"
    if not merged.get("OAUTH_REDIRECT_URI"):
        merged["OAUTH_REDIRECT_URI"] = "http://127.0.0.1:8765/callback"
    if not merged.get("SETUP_POOL_NAME"):
        merged["SETUP_POOL_NAME"] = "idaas-obo-sample-pool"
    if not merged.get("SETUP_CLIENT_NAME"):
        merged["SETUP_CLIENT_NAME"] = "idaas-obo-sample-cli"
    if not merged.get("SETUP_IDP_NAME"):
        merged["SETUP_IDP_NAME"] = "idaas-obo-sample-idp"
    if not merged.get("SETUP_IDP_TYPE"):
        merged["SETUP_IDP_TYPE"] = "IDaaS"
    if not merged.get("SETUP_OBO_VENDOR"):
        merged["SETUP_OBO_VENDOR"] = "IDaaS"

    # 3. REGION 反向兜底（从 endpoint 推断）
    if is_placeholder(merged.get("REGION", "")):
        region = _fallback_from_endpoint(merged.get("CONTROL_ENDPOINT", ""), "agentidentity")
        if not region:
            region = _fallback_from_endpoint(merged.get("DATA_ENDPOINT", ""), "agentidentitydata")
        if region:
            merged["REGION"] = region

    region = merged.get("REGION", "")

    # 4. 正向派生 CONTROL_ENDPOINT / DATA_ENDPOINT
    if not is_placeholder(region):
        if is_placeholder(merged.get("CONTROL_ENDPOINT", "")):
            merged["CONTROL_ENDPOINT"] = "agentidentity.{}.aliyuncs.com".format(region)
        if is_placeholder(merged.get("DATA_ENDPOINT", "")):
            merged["DATA_ENDPOINT"] = "agentidentitydata.{}.aliyuncs.com".format(region)

    # 5. 正向派生 SIGNIN_BASE_URL / POOL_JWKS_BASE
    #    SIGNIN_BASE_URL 可以继续用「默认化后的 environment」：改造前它是
    #    required=True，存量 .env 必然显式填了它，is_placeholder 守卫会保证不覆盖；
    #    只有 POOL_JWKS_BASE（改造前就是可选、存量普遍留空）需要显式声明门控。
    if not is_placeholder(region):
        if environment == "pre-release":
            if is_placeholder(merged.get("SIGNIN_BASE_URL", "")):
                merged["SIGNIN_BASE_URL"] = "https://signin.{}.aliyuncs.com".format(region)
            # pre-release 形态：POOL_JWKS_BASE 留空 → 走 DATA_ENDPOINT（预发实测行为）
        else:
            # production（显式声明或默认）
            if is_placeholder(merged.get("SIGNIN_BASE_URL", "")):
                merged["SIGNIN_BASE_URL"] = "https://signin-{}.aliyunagentid.com".format(region)
            if environment_declared and is_placeholder(merged.get("POOL_JWKS_BASE", "")):
                merged["POOL_JWKS_BASE"] = merged["SIGNIN_BASE_URL"]
                _warn(
                    "POOL_JWKS_BASE 由 SIGNIN_BASE_URL 派生为 {}（因显式声明 "
                    "ENVIRONMENT=production）；如需旧行为（池 discovery/JWKS 走 "
                    "DATA_ENDPOINT），请清空/删除 ENVIRONMENT 或显式设置 POOL_JWKS_BASE。".format(
                        merged["POOL_JWKS_BASE"]
                    )
                )

    # 6. IDAAS_ORIGIN 反向兜底（从 ORDER_SERVICE_ISSUER 提取 scheme+host）
    if is_placeholder(merged.get("IDAAS_ORIGIN", "")):
        issuer = merged.get("ORDER_SERVICE_ISSUER", "")
        if not is_placeholder(issuer):
            origin = _extract_origin(issuer)
            if origin:
                merged["IDAAS_ORIGIN"] = origin

    return merged


def _is_derived(key: str, value: str, raw_env: Optional[Dict[str, str]]) -> bool:
    """判定某键的生效值是「派生值」还是「用户在 .env/环境变量里实填的值」。

    规则：派生后（``value``）非占位，但派生前（``raw_env``）缺失或为占位 → 派生值。
    ``raw_env`` 为 ``None``（调用方未提供派生前快照）时无法判定，一律按实填处理
    ——与历史行为完全一致，保证既有调用点与测试不破。
    """
    if raw_env is None or is_placeholder(value):
        return False
    return is_placeholder(raw_env.get(key, ""))


def _render_environment_line(env: Dict[str, str], raw_env: Optional[Dict[str, str]]) -> str:
    """报告尾部回显 ENVIRONMENT 的生效值及来源（显式填写 / 默认 production）。

    来源判定需要派生前快照 ``raw_env``；未提供时只回显生效值，不臆断来源
    （派生后的 dict 里 ENVIRONMENT 总有值，无从区分「我配的」与「程序猜的」）。
    """
    value = env.get("ENVIRONMENT", "")
    if is_placeholder(value):
        value = DEFAULT_ENVIRONMENT
    if raw_env is None:
        return "[check] ENVIRONMENT 生效值：{}".format(value)
    if is_placeholder(raw_env.get("ENVIRONMENT", "")):
        source = "未在 .env/环境变量声明，默认 {}".format(DEFAULT_ENVIRONMENT)
    else:
        source = ".env/环境变量显式填写"
    return "[check] ENVIRONMENT 生效值：{}（来源：{}）".format(value, source)


def render_check_report(
    env: Dict[str, str],
    skip_setup_keys: bool = True,
    raw_env: Optional[Dict[str, str]] = None,
) -> str:
    """渲染 --check 逐项报告（含缺失项「在哪取值」指引 + 派生值标记）。

    参数：
    - ``env``：**派生后**的配置（通常是 ``derive_defaults(load_env())`` 的返回值）。
    - ``skip_setup_keys``：默认跳过仅 setup --mode=script 需要的 SETUP_* 键。
    - ``raw_env``（可选，末位）：**派生前**的原始快照（即 ``load_env()`` 的返回值）。
      传入后报告能区分「用户在 .env 里实填的值」与「程序派生的值」：后者输出
      ``[OK] KEY = value（已派生）``。不传时行为与历史完全一致（不加标记），
      因此既有调用点（如 ``sample.py:cmd_check``）与测试不会破。
      为何重要：``cmd_check`` 已改为体检派生后的配置，若不区分，用户会把
      ``POOL_JWKS_BASE``/``CONTROL_ENDPOINT`` 这类自己根本没写的派生值当成自己的
      配置（遇 404/NXDOMAIN 时不会怀疑到它）。

    敏感值掩码策略保持不变：含 SECRET/ACCESS_KEY/TOKEN 的键只显示长度，不回显值。
    """
    lines = ["[check] 环境体检（.env 文件：{}）".format(ENV_FILE), ""]
    ok = True
    for key, (required, group, hint) in ENV_SCHEMA.items():
        if skip_setup_keys and key in SETUP_ONLY_KEYS:
            continue
        value = env.get(key, "")
        if is_placeholder(value):
            if required:
                ok = False
                lines.append("  [MISSING] {}".format(key))
                lines.append("            -> 在哪取值：{}".format(hint))
            elif key in _CRED_CHAIN_OPTIONAL_KEYS:
                # D-Minor3：凭据类可选键未填 = 走凭据链（推荐姿势），把语义说透，
                # 避免用户把「未填」误读为配置缺失。
                lines.append("  [OPTIONAL-EMPTY] {}（可选，未填，走凭据链）".format(key))
            else:
                lines.append("  [OPTIONAL-EMPTY] {}（可选，未填）".format(key))
        else:
            derived_mark = "（已派生）" if _is_derived(key, value, raw_env) else ""
            # 密钥类只显示长度，不回显值；S7：``*_FILE`` 后缀键除外——
            # OAUTH_CLIENT_SECRET_FILE 的值是文件路径不是密钥，掩码反而妨碍诊断。
            if (
                not key.endswith("_FILE")
                and ("SECRET" in key or "ACCESS_KEY" in key or "TOKEN" in key)
            ):
                lines.append("  [OK] {} (len={}){}".format(key, len(value), derived_mark))
            else:
                lines.append("  [OK] {} = {}{}".format(key, value, derived_mark))
    lines.append("")
    lines.append(_render_environment_line(env, raw_env))
    lines.append("")
    if ok:
        lines.append("[check] 体检通过：必填项齐全。下一步可运行 python3 sample.py login")
    else:
        lines.append(
            "[check] 体检未通过：存在缺失项。请编辑 {} 补齐上述 [MISSING] 项后重试；"
            "若用控制台准备资源，先运行 python3 sample.py setup --mode=console 查看点选清单。".format(
                ENV_FILE
            )
        )
    return "\n".join(lines)


def get_secret(env: Dict[str, str], key: str, file_key: str, what: str) -> str:
    """读取密钥：优先 0600 文件（file_key 指向路径），其次 env 值。

    找不到时抛 KeyError（调用方统一转成带指引的友好错误）。
    """
    file_path = env.get(file_key, "")
    if file_path:
        if not os.path.isfile(file_path):
            raise KeyError(
                "{}={} 指向的文件不存在。请检查路径，或清空该项改填 {}。".format(
                    file_key, file_path, key
                )
            )
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                value = fh.read().strip()
        except OSError as exc:
            raise KeyError("读取 {} 失败：{}。请检查文件权限（建议 0600）。".format(file_path, exc))
        if not value:
            raise KeyError("{} 文件内容为空：{}。".format(file_key, file_path))
        return value
    value = env.get(key, "")
    if is_placeholder(value):
        raise KeyError(
            "缺少 {}（或 {} 指向的文件）。在哪取值：{}".format(
                key, file_key, ENV_SCHEMA.get(key, (None, None, "见 env.template 注释"))[2]
            )
        )
    return value
