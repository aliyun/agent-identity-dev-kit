"""`.env` 解析、占位符检测与 `--check` 体检。

约定：
- 解析规则：``KEY=VALUE`` 一行一项；``#`` 开头为注释；值两端引号（成对单/双引号）剥离。
- 占位符检测：值含 ``<YOUR_`` 或为空 → 视为缺失（模板未填）。
- 优先级：进程环境变量 > ``.env`` 文件值（便于 CI / 脚本注入覆盖）。
"""

import os
from typing import Dict, List, Optional, Tuple

SAMPLE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(SAMPLE_DIR, ".env")

PLACEHOLDER_MARK = "<YOUR_"

# 每个键：(是否必填, 用途分组, 「在哪取值」指引文案)
ENV_SCHEMA = {
    # ---- 环境与账号 ----
    "REGION": (
        True,
        "环境与账号",
        "地域 ID（如 cn-hangzhou）：控制台右上角，或产品文档地域列表页。",
    ),
    "ALIYUN_ACCESS_KEY_ID": (
        True,
        "环境与账号",
        "RAM 访问控制 → 用户 → AccessKey 管理创建（建议最小权限子账号）。",
    ),
    "ALIYUN_ACCESS_KEY_SECRET": (
        True,
        "环境与账号",
        "与 ALIYUN_ACCESS_KEY_ID 成对创建，仅创建时展示一次，妥善保存。",
    ),
    "ALIYUN_SECURITY_TOKEN": (
        False,
        "环境与账号",
        "可选：STS 临时凭证的 SecurityToken（用长期 AK 则留空）。",
    ),
    # ---- 服务端点 ----
    "CONTROL_ENDPOINT": (
        True,
        "服务端点",
        "控制面端点，形态 agentidentity.<region>.aliyuncs.com（region 替换为 REGION 值）。",
    ),
    "DATA_ENDPOINT": (
        True,
        "服务端点",
        "数据面端点，形态 agentidentitydata.<region>.aliyuncs.com（注意与控制面域名不同）。",
    ),
    "SIGNIN_BASE_URL": (
        True,
        "服务端点",
        "池 OAuth 登录根地址，形态因环境而异（如 https://signin.<region>.aliyuncs.com "
        "或正式环境的登录域）；控制台用户池详情页展示的地址为准。token 兑换走此域名。",
    ),
    "POOL_JWKS_BASE": (
        False,
        "服务端点",
        "可选：池 discovery / JWKS 的域名根。默认（留空）走 DATA_ENDPOINT（预发行为）；"
        "若所在环境的池 discovery/JWKS 走登录域（如新加坡 ap-southeast-1 正式环境），"
        "填登录域完整地址（如 https://signin-<region>.xxx，可与 SIGNIN_BASE_URL 相同）。",
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
        True,
        "订单服务",
        "订单服务令牌 issuer：GET {IDAAS_ORIGIN}/api/v2/iauths_system/oauth2/"
        ".well-known/openid-configuration 返回 JSON 的 issuer 字段。",
    ),
    "ORDER_SERVICE_JWKS_URI": (
        True,
        "订单服务",
        "订单服务 JWKS 端点：同上 discovery 返回 JSON 的 jwks_uri 字段（公网可达）。",
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
    """
    result: Dict[str, str] = {}
    if not os.path.isfile(path):
        return result
    with open(path, "r", encoding="utf-8") as fh:
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
    """加载 .env 并叠加进程环境变量（环境变量优先）。"""
    env = parse_env_file(env_file or ENV_FILE)
    for key in ENV_SCHEMA:
        if key in os.environ and os.environ[key] != "":
            env[key] = os.environ[key]
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


def derive_defaults(env: Dict[str, str]) -> Dict[str, str]:
    """对可为空的键补默认值，并从端点推导缺失的 REGION（返回新 dict）。"""
    merged = dict(env)
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
    if not merged.get("REGION"):
        region = _fallback_from_endpoint(merged.get("CONTROL_ENDPOINT", ""), "agentidentity")
        if not region:
            region = _fallback_from_endpoint(merged.get("DATA_ENDPOINT", ""), "agentidentitydata")
        if region:
            merged["REGION"] = region
    return merged


def render_check_report(env: Dict[str, str], skip_setup_keys: bool = True) -> str:
    """渲染 --check 逐项报告（含缺失项「在哪取值」指引）。"""
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
            else:
                lines.append("  [OPTIONAL-EMPTY] {}（可选，未填）".format(key))
        else:
            # 密钥类只显示长度，不回显值
            if "SECRET" in key or "ACCESS_KEY" in key or "TOKEN" in key:
                lines.append("  [OK] {} (len={})".format(key, len(value)))
            else:
                lines.append("  [OK] {} = {}".format(key, value))
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
