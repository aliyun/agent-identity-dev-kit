"""管控面：模式 A（控制台点选清单）与模式 B（脚本一键幂等创建）+ cleanup 逆序删除。

控制面 RPC 契约（endpoint 形态 agentidentity.<region>.aliyuncs.com，version 2025-09-01）：
- 参数名以 ``aliyun agentidentity <cmd> --help`` 实测为准（本注释同步记录对照）；
- 幂等查询用 Get*/List*，创建前先查重，[CREATE]/[REUSE] 分明；
- ListOAuth2CredentialProviders **不要带分页参数**（预发实测带分页报 ServiceUnavailable）；
- API 返回体字段名存在版本差异，均做防御式解析（多候选键名）；
- Create* 响应实测存在 ``{"RequestId": ..., "<Entity>": {...}}`` 嵌套形态
  （如 CreateUserPool 返回 ``{"UserPool": {"UserPoolId": ...}}``），取值统一走
  ``_first(..., nested=...)``：顶层候选键优先，再依次查嵌套对象。

cleanup 防误删设计（E2E 误删事故教训）：删除范围以 ``.tokens/created_resources.json``
清单为准，绝不直接按 .env 名称删；清单缺失时拒绝删除（--from-env 为显式逃生通道，
需叠加 --yes 双确认）。

注：模式 A 的控制台点选清单全文与截图步骤详见 docs/control-plane-console.md
（由后续文档任务编写），本模块输出的编号清单与其保持一致。
"""

import json
import os
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import env as env_mod
from . import rpc
from . import tokens as tokens_mod

CONTROL_API_VERSION = "2025-09-01"

# SSO 编排轮询参数
SSO_POLL_INTERVAL = 10
SSO_POLL_TIMEOUT = 600


class SetupError(Exception):
    """管控面错误：message 自带下一步指引。"""


def _log(msg: str) -> None:
    print(msg)


# ---------------------------------------------------------------------------
# 通用调用封装（幂等查询 + 防御式字段解析）
# ---------------------------------------------------------------------------


def _call(
    config: Dict[str, str],
    action: str,
    params: Optional[Dict[str, Any]] = None,
    style: str = "query",
    logger: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    creds = (
        config.get("ALIYUN_ACCESS_KEY_ID", ""),
        config.get("ALIYUN_ACCESS_KEY_SECRET", ""),
        (config.get("ALIYUN_SECURITY_TOKEN") or None)
        if not env_mod.is_placeholder(config.get("ALIYUN_SECURITY_TOKEN", ""))
        else None,
    )
    try:
        return rpc.rpc_call(
            config["CONTROL_ENDPOINT"],
            action,
            CONTROL_API_VERSION,
            params,
            style=style,
            creds=creds,
            logger=logger,
        )
    except rpc.RpcError as exc:
        # from exc 保留异常链（__cause__）——_entity_not_exists / _already_exists 依赖它
        # 判定错误码；丢失链会把「资源不存在（应 [SKIP]）」误报成「请手动清理」。
        raise SetupError(
            "{} 调用失败：{}。\n→ 常见排查：AK 无权限/失效（检查 ALIYUN_ACCESS_KEY_*）、"
            "endpoint 不对（CONTROL_ENDPOINT 应为 agentidentity.<region>.aliyuncs.com）、"
            "参数名以 `aliyun agentidentity <cmd> --help` 输出为准后重试。".format(action, exc)
        ) from exc


def _first(
    resp: Dict[str, Any],
    *keys: str,
    default: Any = None,
    nested: Tuple[str, ...] = (),
) -> Any:
    """防御式取键：按候选顺序返回第一个非空值。

    先在 resp 顶层查找；再依次在 ``resp[outer]``（若为 dict）中查找——Create*/Get*
    响应存在 ``{"RequestId": ..., "<Entity>": {...}}`` 嵌套形态（预发实测
    CreateUserPool 返回 ``{"UserPool": {"UserPoolId": ...}}``，顶层无 UserPoolId）。
    顶层候选键优先，嵌套对象仅作兑底，兼容两种响应形态。
    """
    containers: List[Dict[str, Any]] = [resp]
    for outer in nested:
        inner = resp.get(outer)
        if isinstance(inner, dict):
            containers.append(inner)
    for container in containers:
        for key in keys:
            value = container.get(key)
            if value not in (None, "", [], {}):
                return value
    return default


def _entity_not_exists(exc: SetupError) -> bool:
    """判断底层 RpcError 是否为 EntityNotExists / NotFound（查重用）。"""
    cause = exc.__cause__
    return isinstance(cause, rpc.RpcError) and (
        cause.code.startswith("EntityNotExists") or "NotFound" in cause.code
    )


def _already_exists(exc: SetupError) -> bool:
    cause = exc.__cause__
    return isinstance(cause, rpc.RpcError) and cause.code.startswith("EntityAlreadyExists")


# ---------------------------------------------------------------------------
# 模式 A：控制台点选清单
# ---------------------------------------------------------------------------

CONSOLE_CHECKLIST = """\
==================== 管控面资源准备清单（模式 A：控制台点选） ====================
按编号在阿里云控制台完成以下步骤，把产出抄录进 .env（详见
docs/control-plane-console.md，含每步的入口路径与 CLI 等价命令）。

1. 创建用户池
   控制台「云身份 Agent Identity → 用户池 → 创建」，名称自定（3~64 字符）。
   → 记录 USER_POOL_ID（up_ 前缀）
   （CLI 等价：aliyun agentidentity create-user-pool --user-pool-name <名称>）

2. 绑定 IDaaS（身份源联邦）
   用户池设置 → 身份源 → IDaaS，填 IDaaS 侧应用的 clientId/私钥，
   等待编排相位完成（绑定 → SCIM 配置 → SSO 配置，状态为已启用）。
   → 无需抄录（SSOStatus=Enabled 即可）
   （CLI 等价：aliyun agentidentity set-specific-identity-provider /
    get-specific-identity-provider —— 注意 CLI 帮助标注当前仅支持 DingTalk，
    IDaaS 绑定以控制台操作为准）

3. （可选）开启 SCIM provisioning，记录 SCIM 端点
   本 sample 主线不依赖 SCIM（首次登录自动 JIT 建档），可跳过。

4. 创建池 OAuth 应用（数据面登录客户端）
   用户池详情 → OAuth 客户端 → 创建：回跳地址（redirect_uri 白名单）必须包含
   http://127.0.0.1:8765/callback（含任意一条 loopback 条目即放行且忽略端口），
   建议开启强制 PKCE。
   → 记录 OAUTH_CLIENT_ID 与 OAUTH_CLIENT_SECRET
   （CLI 等价：aliyun agentidentity create-user-pool-client --redirect-ur-is
    http://127.0.0.1:8765/callback --enforce-pkce true --secret-required true；
    密钥用 create-client-secret）

5. 注册出站资源（订单服务应用）
   先在 IDaaS 侧创建企业服务应用（模拟订单服务），再回到 Agent Identity 控制台
   创建 OAuth2 凭证提供商（厂商选 IDaaS、类型 ON_BEHALF_OF，配置指向该应用）。
   → 记录 OBO_PROVIDER_NAME 与 ORDER_SERVICE_AUDIENCE（取 IDaaS 控制台该企业
     服务应用详情页的 audience 标识，如 test-aud；不是 provider 的
     OutboundAudience agent-… 形态，误传报 Forbidden.IdaasRsNotAuthorized）
   （CLI 等价：aliyun agentidentity create-oauth2-credential-provider，配额=1）

6. 创建工作负载身份（OBO 委托主体）并记录令牌验签源
   创建 IdentityProvider（discovery 指向本池）与 WorkloadIdentity
   （务必开启 SessionBindingEnabled，否则 OBO 报 InboundCredentialMissing）。
   → 记录 WI_NAME；
   → 记录 SIGNIN_BASE_URL（用户池详情页登录地址，形态 https://signin.<region>…）；
   → 记录 ORDER_SERVICE_ISSUER / ORDER_SERVICE_JWKS_URI：
     GET {IDAAS_ORIGIN}/api/v2/iauths_system/oauth2/.well-known/openid-configuration
     返回 JSON 的 issuer / jwks_uri 字段（公网可达）。
   （CLI 等价：aliyun agentidentity create-identity-provider /
    create-workload-identity --session-binding-enabled true）

抄录完成后运行：python3 sample.py --check 体检，随后 python3 sample.py login。
================================================================================="""


def run_setup_console() -> None:
    """模式 A：打印控制台点选清单 + env 填空指引。"""
    print(CONSOLE_CHECKLIST)
    print()
    print("提示：所有 <YOUR_...> 占位符在 {} 中替换；SCIM 为可选能力，主线无需配置。".format(env_mod.ENV_FILE))
    print("提示：偏好脚本一键创建可改用：python3 sample.py setup --mode=script")


# ---------------------------------------------------------------------------
# 模式 B：脚本一键（幂等）
# ---------------------------------------------------------------------------


def _find_pool(config: Dict[str, str], pool_name: str, logger) -> Optional[Dict[str, Any]]:
    """ListUserPools 按名查池（不带分页参数）。"""
    resp = _call(config, "ListUserPools", {}, logger=logger)
    pools = _first(resp, "UserPools", "UserPoolList", "Pools", default=[]) or []
    for pool in pools:
        if not isinstance(pool, dict):
            continue
        if pool.get("UserPoolName") == pool_name or pool.get("PoolName") == pool_name:
            return pool
    return None


def _ensure_pool(config: Dict[str, str], logger) -> Tuple[str, str, bool]:
    """步骤 1：创建或复用用户池。返回 (pool_id, pool_name, created)。"""
    pool_name = config["SETUP_POOL_NAME"]
    existing = _find_pool(config, pool_name, logger)
    if existing:
        pool_id = _first(existing, "UserPoolId", "PoolId", default="")
        _log("[REUSE] 用户池 {}（UserPoolId={}）".format(pool_name, pool_id))
        return pool_id, pool_name, False
    resp = _call(
        config,
        "CreateUserPool",
        {"UserPoolName": pool_name, "Description": "idaas-cli-obo sample pool"},
        logger=logger,
    )
    # 预发实测响应为嵌套形态 {"RequestId": ..., "UserPool": {"UserPoolId": ...}}；
    # 顶层形态亦兼容（顶层候选键优先）。
    pool_id = _first(resp, "UserPoolId", "PoolId", nested=("UserPool", "Pool"), default="")
    if not pool_id:
        raise SetupError(
            "CreateUserPool 成功但响应缺少 UserPoolId（顶层键：{}；已尝试嵌套 UserPool/Pool）".format(
                sorted(resp.keys())
            )
        )
    _log("[CREATE] 用户池 {}（UserPoolId={}，RequestId={}）".format(pool_name, pool_id, resp.get("RequestId", "-")))
    return pool_id, pool_name, True


def _bind_idp_and_wait(config: Dict[str, str], pool_name: str, logger) -> None:
    """步骤 2：绑定 IDaaS 身份源（SetSpecificIdentityProvider）并轮询至 SSOStatus=Enabled。

    兑底（新加坡正式环境实测）：SetSpecificIdentityProvider 仅接受
    DingTalk/Feishu/WeCom（InvalidParameter.IdentityProviderType）——IDaaS 绑定只能走
    控制台（模式 A 第 2 步）。此时打印兑底指引并继续后续步骤（客户端/IdP/WI
    与入站绑定无依赖），否则 setup 会在第 2 步中断，剩余资源全部无法创建。
    """
    idp_type = config.get("SETUP_IDP_TYPE", "IDaaS")
    metadata_raw = config.get("SETUP_IDP_METADATA", "")
    params: Dict[str, Any] = {
        "UserPoolName": pool_name,
        "IdentityProviderType": idp_type,
        "SSOStatus": "Enabled",
    }
    if metadata_raw:
        try:
            params["IdPMetadata"] = json.loads(metadata_raw)
        except ValueError:
            params["IdPMetadata"] = metadata_raw  # 非 JSON 则按字符串透传
    try:
        resp = _call(config, "SetSpecificIdentityProvider", params, logger=logger)
    except SetupError as exc:
        cause = exc.__cause__
        if isinstance(cause, rpc.RpcError) and cause.code.startswith("InvalidParameter"):
            _log("[FALLBACK] SetSpecificIdentityProvider 被拒（{}）：".format(cause))
            _log("        入站 IDaaS 绑定请改用控制台完成（模式 A 第 2 步：用户池设置 →")
            _log("        身份源 → IDaaS，填 IDaaS 侧应用 clientId/私钥）；绑定完成后重跑")
            _log("        setup --mode=script（幂等）即可。继续创建后续资源 …")
            return
        raise
    _log("[CREATE] 绑定身份源 type={}（RequestId={}）".format(idp_type, resp.get("RequestId", "-")))
    if idp_type != "DingTalk":
        _log("        注意：CLI 帮助标注该接口当前仅支持 DingTalk；IDaaS 类型若被拒绝，")
        _log("        请改用控制台完成绑定（模式 A 第 2 步）——SSO 编排会继续在后台完成。")

    # 轮询 SSOStatus=Enabled（编排三相位：绑定 → SCIM 配置 → SSO 配置）
    deadline = time.time() + SSO_POLL_TIMEOUT
    while time.time() < deadline:
        try:
            resp = _call(
                config,
                "GetSpecificIdentityProvider",
                {"UserPoolName": pool_name, "IdentityProviderType": idp_type},
                logger=logger,
            )
        except SetupError as exc:
            if _entity_not_exists(exc):
                _log("        [WAIT] 配置尚未可读，{}s 后重试…".format(SSO_POLL_INTERVAL))
                time.sleep(SSO_POLL_INTERVAL)
                continue
            raise
        status = _first(resp, "SSOStatus", nested=("IdentityProvider", "IdP"), default=None)
        if status == "Enabled":
            _log("[OK] SSO 编排完成（SSOStatus=Enabled）")
            return
        _log("        [WAIT] SSOStatus={}（编排进行中），{}s 后重试…".format(status, SSO_POLL_INTERVAL))
        time.sleep(SSO_POLL_INTERVAL)
    raise SetupError(
        "等待 SSOStatus=Enabled 超时（{}s）。→ 可在控制台查看编排相位（绑定/SCIM/SSO），"
        "完成后直接重跑 setup --mode=script（幂等，已完成步骤会跳过）。".format(SSO_POLL_TIMEOUT)
    )


def _ensure_client(
    config: Dict[str, str], pool_name: str, redirect_uri: str, logger
) -> Tuple[str, str, bool]:
    """步骤 3：创建或复用池 OAuth 客户端（loopback redirect_uri + 强制 PKCE）。

    返回 (client_id, client_secret, created)。client_secret 为空表示复用已有客户端
    （密钥只在创建时返回，复用场景提示用户用已有 .env 值或重建密钥）。
    """
    client_name = config["SETUP_CLIENT_NAME"]
    try:
        resp = _call(
            config,
            "GetUserPoolClient",
            {"UserPoolName": pool_name, "ClientName": client_name},
            logger=logger,
        )
        client_id = _first(resp, "ClientId", nested=("UserPoolClient", "Client"), default=None)
        if client_id:
            _log("[REUSE] 池 OAuth 客户端 {}（ClientId={}）".format(client_name, client_id))
            # 复用客户端：确认 loopback 白名单（缺则 update 补齐——整体替换语义，写后必读校验）
            registered = (
                _first(resp, "RedirectURIs", "RedirectUris", nested=("UserPoolClient", "Client"), default=[]) or []
            )
            if redirect_uri not in registered:
                _log("        白名单缺 {}，执行 UpdateUserPoolClient 补齐（保留原有条目）…".format(redirect_uri))
                merged = list(registered) + [redirect_uri]
                upd = _call(
                    config,
                    "UpdateUserPoolClient",
                    {
                        "UserPoolName": pool_name,
                        "ClientName": client_name,
                        "RedirectURIs": merged,
                        "EnforcePKCE": True,
                    },
                    logger=logger,
                )
                _log("        白名单已更新（共 {} 条，RequestId={}）。写后必读校验：".format(
                    len(merged), upd.get("RequestId", "-")
                ))
                verify = _call(
                    config,
                    "GetUserPoolClient",
                    {"UserPoolName": pool_name, "ClientName": client_name},
                    logger=logger,
                )
                now_registered = (
                    _first(verify, "RedirectURIs", "RedirectUris", nested=("UserPoolClient", "Client"), default=[]) or []
                )
                if redirect_uri not in now_registered:
                    raise SetupError(
                        "白名单写后必读校验失败（UpdateUserPoolClient 为整体替换语义，"
                        "缺条目易丢数据）。→ 请到控制台手动补 {} 后重跑（幂等）".format(redirect_uri)
                    )
                _log("        白名单校验通过（含 loopback 条目）")
            return client_id, "", False
    except SetupError as exc:
        if not _entity_not_exists(exc):
            raise

    try:
        resp = _call(
            config,
            "CreateUserPoolClient",
            {
                "UserPoolName": pool_name,
                "ClientName": client_name,
                "RedirectURIs": [redirect_uri],
                "EnforcePKCE": True,
                "SecretRequired": True,
            },
            logger=logger,
        )
    except SetupError as exc:
        if not _already_exists(exc):
            raise
        # 并发/竞态兑底（对齐 _ensure_oauth2_provider 的 [REUSE] 模式）：
        # Create 撞 EntityAlreadyExists → 按名复用，回查拿 ClientId；
        # 密钥只在创建时返回，复用场景用 .env 现值或控制台重建密钥。
        _log("[REUSE] 池 OAuth 客户端 {}（Create 报 EntityAlreadyExists → 复用）".format(client_name))
        resp = _call(
            config,
            "GetUserPoolClient",
            {"UserPoolName": pool_name, "ClientName": client_name},
            logger=logger,
        )
        reused_id = _first(resp, "ClientId", nested=("UserPoolClient", "Client"), default="")
        if not reused_id:
            raise SetupError(
                "客户端 {} 已存在但回查不到 ClientId（顶层键：{}；已尝试嵌套 UserPoolClient/Client）".format(
                    client_name, sorted(resp.keys())
                )
            ) from None
        _log("        复用 ClientId={}；密钥请用 .env 现值（或控制台重建密钥后填入）".format(reused_id))
        return reused_id, "", False
    client_id = _first(resp, "ClientId", nested=("UserPoolClient", "Client"), default="")
    if not client_id:
        raise SetupError(
            "CreateUserPoolClient 成功但响应缺少 ClientId（顶层键：{}；已尝试嵌套 UserPoolClient/Client）".format(
                sorted(resp.keys())
            )
        )
    _log("[CREATE] 池 OAuth 客户端 {}（ClientId={}，RequestId={}）".format(
        client_name, client_id, resp.get("RequestId", "-")
    ))
    secret = _first(resp, "ClientSecret", "Secret", nested=("UserPoolClient", "Client"), default="")
    if isinstance(secret, dict):
        # 形态 {"ClientSecret": {...}}：dict 值再取一层候选键（含 ClientSecretValue：
        # 新加坡正式环境实测 CreateClientSecret 返回
        # {"ClientSecret": {"ClientSecretValue": ...}}，旧候选键未覆盖导致密钥丢失）
        secret = _first(secret, "ClientSecretValue", "ClientSecret", "Secret", default="")
    if not secret:
        # 密钥客户端需单独创建密钥
        resp = _call(
            config,
            "CreateClientSecret",
            {"UserPoolName": pool_name, "ClientName": client_name},
            logger=logger,
        )
        secret = _first(resp, "ClientSecret", "Secret", nested=("ClientSecret", "UserPoolClient"), default="")
        if isinstance(secret, dict):
            # 形态 {"Secret": {"ClientSecret": "..."}}：dict 值再取一层候选键；
            # ClientSecretValue 优先（新加坡正式环境实测响应形态）
            secret = _first(secret, "ClientSecretValue", "ClientSecret", "Secret", default="")
        _log("[CREATE] 客户端密钥（RequestId={}）".format(resp.get("RequestId", "-")))
    return client_id, secret, True


def _pool_wellknown_host(config: Dict[str, str]) -> str:
    """池 discovery / JWKS 的域名根（不含 scheme）。

    预发实测：池 discovery 走 DATA_ENDPOINT 公网路径；但部分正式环境（如新加坡
    ap-southeast-1）池 discovery/JWKS 改走登录域，数据面同路径 404。因此支持
    可配置项 POOL_JWKS_BASE（填登录域，含/不含 https:// 前缀均可），留空则保持
    原默认行为（DATA_ENDPOINT）——向后兼容。
    """
    base = (config.get("POOL_JWKS_BASE") or "").strip()
    if env_mod.is_placeholder(base):
        base = ""
    if not base:
        return config["DATA_ENDPOINT"]
    host = base.split("://")[-1].rstrip("/")
    return host


def _ensure_identity_provider(config: Dict[str, str], pool_id: str, logger) -> Tuple[str, bool]:
    """步骤 4：创建或复用 IdentityProvider（discovery 指向本池）。返回 (idp_name, created)。"""
    idp_name = config["SETUP_IDP_NAME"]
    try:
        resp = _call(config, "GetIdentityProvider", {"IdentityProviderName": idp_name}, logger=logger)
        if _first(
            resp, "IdentityProviderName", "IdPName", nested=("IdentityProvider", "IdP"), default=None
        ):
            _log("[REUSE] IdentityProvider {}".format(idp_name))
            return idp_name, False
    except SetupError as exc:
        if not _entity_not_exists(exc):
            raise
    discovery_url = "https://{}/{}/.well-known/openid-configuration".format(
        _pool_wellknown_host(config), pool_id
    )
    resp = _call(
        config,
        "CreateIdentityProvider",
        {
            "IdentityProviderName": idp_name,
            "DiscoveryURL": discovery_url,
            "Description": "idaas-cli-obo sample: trust this user pool",
        },
        logger=logger,
    )
    _log("[CREATE] IdentityProvider {}（DiscoveryURL=池 discovery，RequestId={}）".format(
        idp_name, resp.get("RequestId", "-")
    ))
    return idp_name, True


def _ensure_workload_identity(config: Dict[str, str], idp_name: str, logger) -> Tuple[str, bool]:
    """步骤 5：创建或复用 WorkloadIdentity（SessionBindingEnabled=true 是 OBO 前提）。

    返回 (wi_name, created)。
    """
    wi_name = config["WI_NAME"]
    try:
        resp = _call(config, "GetWorkloadIdentity", {"WorkloadIdentityName": wi_name}, logger=logger)
        wi = resp.get("WorkloadIdentity") if isinstance(resp.get("WorkloadIdentity"), dict) else resp
        if _first(wi, "WorkloadIdentityName", nested=("WorkloadIdentity",), default=None):
            binding = wi.get("SessionBindingEnabled")
            if binding is not True and str(binding).lower() != "true":
                _log("[WARN] WorkloadIdentity {} 已存在但 SessionBindingEnabled≠true，".format(wi_name))
                _log("       OBO 依赖会话绑定（否则报 InboundCredentialMissing）→ 请在控制台开启后重跑")
            else:
                _log("[REUSE] WorkloadIdentity {}（SessionBindingEnabled=true）".format(wi_name))
            return wi_name, False
    except SetupError as exc:
        if not _entity_not_exists(exc):
            raise
    resp = _call(
        config,
        "CreateWorkloadIdentity",
        {
            "WorkloadIdentityName": wi_name,
            "IdentityProviderName": idp_name,
            "SessionBindingEnabled": True,
            "Description": "idaas-cli-obo sample workload identity",
        },
        logger=logger,
    )
    _log("[CREATE] WorkloadIdentity {}（SessionBindingEnabled=true，RequestId={}）".format(
        wi_name, resp.get("RequestId", "-")
    ))
    return wi_name, True


def _ensure_oauth2_provider(config: Dict[str, str], logger) -> Tuple[str, bool]:
    """步骤 6：创建或复用 OAuth2 凭证提供商（配额=1，EntityAlreadyExists 视为复用）。

    返回 (provider_name, created)。
    """
    provider_name = config["OBO_PROVIDER_NAME"]
    try:
        resp = _call(
            config,
            "GetOAuth2CredentialProvider",
            {"OAuth2CredentialProviderName": provider_name},
            logger=logger,
        )
        if _first(
            resp,
            "OAuth2CredentialProviderName",
            "Name",
            nested=("OAuth2CredentialProvider",),
            default=None,
        ):
            _log("[REUSE] OAuth2 凭证提供商 {}".format(provider_name))
            return provider_name, False
    except SetupError as exc:
        if not _entity_not_exists(exc):
            raise

    vendor = config.get("SETUP_OBO_VENDOR", "IDaaS")
    config_raw = config.get("SETUP_OBO_PROVIDER_CONFIG", "")
    if not config_raw:
        raise SetupError(
            "创建 OAuth2 凭证提供商需要 SETUP_OBO_PROVIDER_CONFIG（JSON：指向 IDaaS 侧"
            "订单服务应用的 clientId/clientSecret 等，字段结构以 "
            "`aliyun agentidentity create-oauth2-credential-provider --help` 为准）。"
            "→ 请在 .env 填好后重跑 setup --mode=script（幂等，已完成步骤会跳过）"
        )
    try:
        provider_config = json.loads(config_raw)
    except ValueError as exc:
        raise SetupError(
            "SETUP_OBO_PROVIDER_CONFIG 不是合法 JSON：{}。→ 请修正 .env 后重跑".format(exc)
        ) from None

    try:
        resp = _call(
            config,
            "CreateOAuth2CredentialProvider",
            {
                "CredentialProviderVendor": vendor,
                "OAuth2CredentialProviderName": provider_name,
                "OAuth2ProviderConfig": provider_config,
                "Description": "idaas-cli-obo sample outbound provider",
            },
            logger=logger,
        )
    except SetupError as exc:
        if _already_exists(exc):
            _log("[REUSE] OAuth2 凭证提供商 {}（已存在，EntityAlreadyExists → 复用；配额=1）".format(provider_name))
            _log("       如需重建：先在控制台删除旧 provider 再重跑（注意：删除会影响引用它的既有链路）")
            return provider_name, False
        raise
    _log("[CREATE] OAuth2 凭证提供商 {}（vendor={}，RequestId={}）".format(
        provider_name, vendor, resp.get("RequestId", "-")
    ))
    return provider_name, True


def writeback_env(updates: Dict[str, str]) -> str:
    """把 setup 产出回写 .env：保留原有行与注释，更新或追加目标键；0600 原子替换。

    注意：更新已有键时整行重写为 ``KEY=新值``（该行原有的行内注释会被替换）；
    未涉及的行（注释行、其他键）原样保留。
    """
    lines: List[str] = []
    if os.path.isfile(env_mod.ENV_FILE):
        with open(env_mod.ENV_FILE, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    seen = set()
    out: List[str] = []
    for line in lines:
        stripped = line.strip()
        if "=" in stripped and not stripped.startswith("#"):
            key = stripped.split("=", 1)[0].strip()
            if key in updates:
                out.append("{}={}".format(key, updates[key]))
                seen.add(key)
                continue
        out.append(line)
    for key, value in updates.items():
        if key not in seen:
            out.append("{}={}".format(key, value))
    tmp = env_mod.ENV_FILE + ".tmp"
    # 权限顺序：O_CREAT 创建即带 0600（而非先写后 chmod，避免短暂的全局可读窗口）；
    # flush + fsync 确保内容落盘后再原子替换。chmod 兑底处理 tmp 残留场景——
    # O_CREAT 的 mode 仅在新建时生效，遗留 tmp 会保留旧权限。
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    try:
        os.chmod(tmp, 0o600)
    except OSError:  # pragma: no cover - 权限收紧失败不应阻断回写
        pass
    os.replace(tmp, env_mod.ENV_FILE)
    return env_mod.ENV_FILE


def run_setup_script(config: Optional[Dict[str, str]] = None, with_scim: bool = False) -> Dict[str, str]:
    """模式 B：一键幂等创建全部资源并回写 .env。返回产出 dict。"""
    config = env_mod.derive_defaults(config or env_mod.load_env())
    _require_setup(config)
    if with_scim:
        _log("[setup] --with-scim：本 sample 未实现 SCIM provisioning 自动化（主线不依赖，")
        _log("       首次联邦登录会自动 JIT 建档）；SCIM 配置请参照 docs/control-plane-console.md 第 3 步。")

    if env_mod.is_placeholder(config.get("WI_NAME", "")):
        config["WI_NAME"] = "idaas-obo-sample-wi"
    if env_mod.is_placeholder(config.get("OBO_PROVIDER_NAME", "")):
        config["OBO_PROVIDER_NAME"] = "idaas-obo-sample-provider"

    logger = lambda msg: _log("        {}".format(msg))  # noqa: E731

    # 逐步执行（幂等：查重 → 创建/复用）。每步「新建」成功后**立即**增量落盘资源清单：
    # 若只在末尾统一落盘，中途失败时已建资源进不了清单；重跑后幂等复用（created=False）
    # 清单永远为空 → 资源沦为只能 --from-env 或手动清理的「受保护孤儿」。
    created_count = 0
    pool_id, pool_name, pool_created = _ensure_pool(config, logger)
    if pool_created:
        _merge_manifest([{"type": "user_pool", "name": pool_name}])
        created_count += 1
    _bind_idp_and_wait(config, pool_name, logger)
    client_id, client_secret, client_created = _ensure_client(
        config, pool_name, config["OAUTH_REDIRECT_URI"], logger
    )
    if client_created:
        _merge_manifest([{
            "type": "pool_client",
            "name": config["SETUP_CLIENT_NAME"],
            "pool_name": pool_name,
        }])
        created_count += 1
    idp_name, idp_created = _ensure_identity_provider(config, pool_id, logger)
    if idp_created:
        _merge_manifest([{"type": "identity_provider", "name": idp_name}])
        created_count += 1
    wi_name, wi_created = _ensure_workload_identity(config, idp_name, logger)
    if wi_created:
        _merge_manifest([{"type": "workload_identity", "name": wi_name}])
        created_count += 1
    provider_name, provider_created = _ensure_oauth2_provider(config, logger)
    if provider_created:
        _merge_manifest([{"type": "oauth2_provider", "name": provider_name}])
        created_count += 1

    # 全部成功才回写 .env（失败场景在上面以 SetupError 中断，不写半份）
    updates: Dict[str, str] = {
        "USER_POOL_ID": pool_id,
        "OAUTH_CLIENT_ID": client_id,
        "WI_NAME": config["WI_NAME"],
        "OBO_PROVIDER_NAME": config["OBO_PROVIDER_NAME"],
    }
    if client_secret:
        updates["OAUTH_CLIENT_SECRET"] = client_secret
    else:
        _log("[setup] 复用已有客户端：OAUTH_CLIENT_SECRET 保持 .env 现值（如无请在控制台重建密钥后填入）")
    path = writeback_env(updates)
    _log("[setup] 产出已回写 {}（0600）：{}".format(path, ", ".join(sorted(updates.keys()))))
    if created_count:
        _log("[setup] 资源清单已更新 {}（新增 {} 项；cleanup 仅删除清单内资源）".format(
            _manifest_path(), created_count
        ))
    else:
        _log("[setup] 本次未新建资源（全部复用），资源清单保持不变：{}".format(_manifest_path()))
    _log("[setup] 还需手动确认 .env：SIGNIN_BASE_URL / ORDER_SERVICE_AUDIENCE / ")
    _log("        ORDER_SERVICE_ISSUER / ORDER_SERVICE_JWKS_URI（见 env.template 注释的取值方法）。")
    _log("        ⚠️ ORDER_SERVICE_AUDIENCE 取「IDaaS 控制台该企业服务应用详情页的")
    _log("        audience 标识」（如 test-aud），不是 OBO provider 的 OutboundAudience")
    _log("        （agent-… 形态，误传报 Forbidden.IdaasRsNotAuthorized）；正式环境另需")
    _log("        确认 POOL_JWKS_BASE 与登录域取值（见 README「区域/环境差异」一节），")
    _log("        然后运行：python3 sample.py --check → python3 sample.py login")
    return updates


def _require_setup(config: Dict[str, str], context: str = "setup --mode=script") -> None:
    required = (
        "ALIYUN_ACCESS_KEY_ID",
        "ALIYUN_ACCESS_KEY_SECRET",
        "CONTROL_ENDPOINT",
        "DATA_ENDPOINT",
        "OAUTH_REDIRECT_URI",
    )
    missing = [k for k in required if env_mod.is_placeholder(config.get(k, ""))]
    if missing:
        raise SetupError(
            "{} 缺少配置：{}。→ 请在 {} 补齐后重跑"
            "（setup 幂等，已创建的资源会按名复用，不会重复创建）".format(
                context, ", ".join(missing), env_mod.ENV_FILE
            )
        )


# ---------------------------------------------------------------------------
# 资源清单（cleanup 防误删的依据）：.tokens/created_resources.json（0600）
# ---------------------------------------------------------------------------

# 清单条目 type → (显示名, 删除 Action)；参数构造见 _delete_params
_MANIFEST_TYPES = {
    "oauth2_provider": ("OAuth2 凭证提供商", "DeleteOAuth2CredentialProvider"),
    "workload_identity": ("工作负载身份", "DeleteWorkloadIdentity"),
    "identity_provider": ("IdentityProvider", "DeleteIdentityProvider"),
    "pool_client": ("池 OAuth 客户端", "DeleteUserPoolClient"),
    "user_pool": ("用户池", "DeleteUserPool"),
}

MANIFEST_NAME = "created_resources.json"


def _manifest_path() -> str:
    return os.path.join(tokens_mod.TOKENS_DIR, MANIFEST_NAME)


def _load_manifest() -> Dict[str, Any]:
    """读取清单（不存在/损坏返回 {}）。复用 tokens 的 0600 目录与原子写设施。"""
    return tokens_mod.load_json(MANIFEST_NAME)


def _save_manifest(resources: List[Dict[str, Any]]) -> str:
    return tokens_mod.save_json(
        MANIFEST_NAME,
        {
            "version": 1,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "note": "setup --mode=script 创建的资源记录；cleanup 仅删除清单内资源",
            "resources": resources,
        },
    )


def _remove_manifest() -> None:
    try:
        os.remove(_manifest_path())
    except FileNotFoundError:
        pass


def _merge_manifest(new_entries: List[Dict[str, str]]) -> None:
    """把本次新建资源合并进清单（幂等）：同 (type, name) 不重复；

    仅记录本样例「新建」的资源——setup 复用的既有资源（可能是手动配置的
    真实资产）不进清单，cleanup 也就不会碰它们（防误删）。
    """
    manifest = _load_manifest()
    resources = manifest.get("resources")
    if not isinstance(resources, list):
        resources = []
    known = {
        (r.get("type"), r.get("name")) for r in resources if isinstance(r, dict)
    }
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for entry in new_entries:
        key = (entry["type"], entry["name"])
        if key in known:
            continue
        resources.append(dict(entry, created_at=now))
        known.add(key)
    _save_manifest(resources)


def _print_manifest(entries: List[Dict[str, Any]]) -> None:
    """打印清单（编号 + 类型 + 名称 + 所属池 + 创建时间）。"""
    for index, entry in enumerate(entries, 1):
        rtype = entry.get("type", "?")
        label = _MANIFEST_TYPES.get(rtype, (rtype,))[0]
        pool = entry.get("pool_name")
        extra = "（池：{}）".format(pool) if pool else ""
        created = entry.get("created_at", "-")
        _log("  {:>2}. [{}] {}{}（创建于 {}）".format(
            index, label, entry.get("name", "?"), extra, created
        ))


def _delete_params(entry: Dict[str, Any]) -> Dict[str, Any]:
    """清单条目 → 删除 Action 的请求参数。"""
    rtype = entry["type"]
    if rtype == "pool_client":
        return {"UserPoolName": entry.get("pool_name", ""), "ClientName": entry["name"]}
    key = {
        "oauth2_provider": "OAuth2CredentialProviderName",
        "workload_identity": "WorkloadIdentityName",
        "identity_provider": "IdentityProviderName",
        "user_pool": "UserPoolName",
    }[rtype]
    return {key: entry["name"]}


def _manifest_entries_from_env(config: Dict[str, str]) -> List[Dict[str, Any]]:
    """--from-env 逃生通道：按 .env 当前名称类配置构造删除清单（旧 cleanup 的范围）。"""
    def _clean(value: str) -> str:
        return "" if env_mod.is_placeholder(value or "") else value

    pool_name = _clean(config.get("SETUP_POOL_NAME", ""))
    client_name = _clean(config.get("SETUP_CLIENT_NAME", ""))
    idp_name = _clean(config.get("SETUP_IDP_NAME", ""))
    wi_name = _clean(config.get("WI_NAME", ""))
    provider_name = _clean(config.get("OBO_PROVIDER_NAME", ""))

    entries: List[Dict[str, Any]] = []
    # 按创建顺序排列（与 setup 清单一致）；cleanup 逆序处理 → 池最后删
    if pool_name:
        entries.append({"type": "user_pool", "name": pool_name})
    if client_name and pool_name:
        entries.append({"type": "pool_client", "name": client_name, "pool_name": pool_name})
    if idp_name:
        entries.append({"type": "identity_provider", "name": idp_name})
    if wi_name:
        entries.append({"type": "workload_identity", "name": wi_name})
    if provider_name:
        entries.append({"type": "oauth2_provider", "name": provider_name})
    return entries


# ---------------------------------------------------------------------------
# cleanup：只删清单内资源（防误删；--from-env 为显式逃生通道）
# ---------------------------------------------------------------------------


def _delete_quiet(
    config: Dict[str, str], action: str, params: Dict[str, Any], what: str, logger
) -> str:
    """删除资源。返回 "deleted" / "skipped"（EntityNotExists）/ "failed"。

    EntityNotExists → [SKIP]（依赖 _call 的 from exc 异常链判定错误码）；
    其余失败打印警告但不阻断（逆序清理尽力而为）。
    """
    try:
        resp = _call(config, action, params, logger=logger)
        _log("[DELETE] {}（RequestId={}）".format(what, resp.get("RequestId", "-")))
        return "deleted"
    except SetupError as exc:
        if _entity_not_exists(exc):
            _log("[SKIP] {}（不存在）".format(what))
            return "skipped"
        _log("[WARN] 删除 {} 失败（{}）——请手动检查后清理".format(what, exc.__cause__ or exc))
        return "failed"


def _entry_key(entry: Dict[str, Any]) -> Tuple[Any, ...]:
    """清单条目的稳定标识 (type, name, pool_name)——回写清单时按原顺序过滤。"""
    return (entry.get("type"), entry.get("name"), entry.get("pool_name"))


def _run_deletes(
    config: Dict[str, str],
    entries: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """逆序执行删除（依赖顺序：池最后删）。

    成功/[SKIP] 的条目视为已处理；failed 与未知类型条目保留。
    返回未处理完的条目（按原传入顺序）——清单持久化由调用方决定。
    """
    logger = lambda msg: _log("        {}".format(msg))  # noqa: E731
    remaining: List[Dict[str, Any]] = []
    for entry in reversed(entries):
        if not isinstance(entry, dict):
            continue
        rtype = entry.get("type", "")
        spec = _MANIFEST_TYPES.get(rtype)
        if spec is None or not entry.get("name"):
            _log("[WARN] 清单含未知类型条目（type={}，已跳过并保留）".format(rtype or "<空>"))
            remaining.append(entry)
            continue
        label, action = spec
        what = "{} {}".format(label, entry["name"])
        status = _delete_quiet(config, action, _delete_params(entry), what, logger)
        if status == "failed":
            remaining.append(entry)  # 删除失败：保留在清单，修复后重跑续删
    remaining.reverse()  # 恢复原顺序
    return remaining


def run_cleanup(
    config: Optional[Dict[str, str]] = None,
    assume_yes: bool = False,
    from_env: bool = False,
    keep_pool: bool = False,
) -> None:
    """cleanup：只删除 setup 记录在 ``.tokens/created_resources.json`` 清单内的资源。

    防误删设计（E2E 误删事故教训）：删除范围以清单为准，绝不直接按 .env 名称删。
    - 清单存在：打印完整清单 → 交互确认（--yes 跳过）→ 逆序删除 → 逐项回写清单，
      全部处理完后删除清单文件（幂等可重跑）；
    - 清单缺失/为空：拒绝删除并给出控制台手动清理指引（不触碰网络）；
    - ``--from-env``：显式逃生通道——按 .env 当前名称类配置构造删除清单，
      必须叠加 ``--yes`` 双确认（不校验资源是否本样例创建，危险）；
    - ``--keep-pool``：跳过清单中 type=user_pool 的条目（保留在清单不删，
      演示迭代可保留池避免重复等待 SSO 编排）；对 --from-env 清单同样生效。
    """
    manifest = _load_manifest()
    resources = manifest.get("resources") if isinstance(manifest, dict) else None
    if isinstance(resources, list) and resources:
        # 路径 1：按清单删（清单存在时 --from-env 被忽略——按清单更安全）
        _log("[cleanup] 依据 setup 资源清单（{}）：".format(_manifest_path()))
        _print_manifest(resources)
        _log("  将逆序删除以上 {} 项（依赖顺序：池最后删）；不存在即 [SKIP]，幂等可重跑。".format(len(resources)))
        _log("  注意：删除用户池会移除池内全部客户端/会话数据；订单服务等 IDaaS 侧应用不在本工具管辖范围。")
        kept: List[Dict[str, Any]] = []
        deletable: List[Dict[str, Any]] = list(resources)
        if keep_pool:
            kept = [r for r in resources if isinstance(r, dict) and r.get("type") == "user_pool"]
            deletable = [r for r in resources if not (isinstance(r, dict) and r.get("type") == "user_pool")]
            if kept:
                _log("  --keep-pool：{} 个用户池条目将跳过删除并保留在清单（演示迭代可保留池，".format(len(kept)))
                _log("            避免下次 setup 重新等待 SSO 编排；不再需要时重跑 cleanup 不带本参数删池）。")
        if not deletable:
            _log("[cleanup] 清单内除保留池外无可删除条目，未做任何删除。")
            return
        if not assume_yes:
            try:
                answer = input("确认删除？输入 yes 继续：").strip().lower()
            except EOFError:
                # 非交互环境（stdin 已关闭/重定向）：失败安全方向——拒绝删除
                answer = "no"
            if answer != "yes":
                _log("[cleanup] 已取消（未做任何删除）。加 --yes 可跳过确认。")
                return
        config = env_mod.derive_defaults(config or env_mod.load_env())
        _require_setup(config, context="cleanup（需删除用的 AK 凭证）")
        remaining = _run_deletes(config, deletable)
        # 回写清单：保留（--keep-pool）+ 未处理完的条目，按原清单顺序
        if remaining or kept:
            keep_keys = {_entry_key(e) for e in list(remaining) + list(kept)}
            final = [r for r in resources if _entry_key(r) in keep_keys]
            _save_manifest(final)
            if remaining:
                _log("[cleanup] {} 项未处理完已保留在清单中，修复问题后重跑 cleanup 即可续删。".format(len(remaining)))
            if kept:
                _log("[cleanup] {} 个用户池条目按 --keep-pool 保留在清单中。".format(len(kept)))
        else:
            _remove_manifest()
            _log("[cleanup] 清单内资源已全部处理完毕，清单文件已删除。")
        _log("[cleanup] 完成。本地令牌产物 .tokens/ 未删除（含敏感值）；如需清理：rm -rf .tokens")
        return

    # 清单缺失/为空
    if not from_env:
        _log("[cleanup] 未发现本样例创建的资源记录（{} 不存在或为空）。".format(_manifest_path()))
        _log("[cleanup] 已拒绝删除：本工具只清理自己创建的资源，避免误删手动配置的真实资产。")
        _log("  → 若资源为手动配置：请按 docs/control-plane-console.md 的「手动删除资源」步骤在控制台删除；")
        _log("  → 若确需按 .env 当前值删除（危险：不校验资源归属，可能波及同名手动资源）：")
        _log("    python3 sample.py cleanup --from-env --yes（--from-env 与 --yes 双确认）")
        return

    # 路径 2：--from-env 逃生通道（清单缺失时才生效）
    config = env_mod.derive_defaults(config or env_mod.load_env())
    _require_setup(config, context="cleanup --from-env")
    entries = _manifest_entries_from_env(config)
    if keep_pool:
        before = len(entries)
        entries = [e for e in entries if e.get("type") != "user_pool"]
        if before != len(entries):
            _log("[cleanup] --keep-pool：--from-env 清单中的用户池条目同样跳过删除。")
    if not entries:
        _log("[cleanup] --from-env：.env 中未发现可删除的名称类配置，未做任何删除。")
        return
    _log("[cleanup] --from-env：按 .env 当前值构造删除清单（清单缺失场景的逃生通道）：")
    _print_manifest(entries)
    _log("  注意：此路径不校验资源是否本样例创建，可能误删同名的手动资源——危险。")
    if not assume_yes:
        _log("[cleanup] --from-env 需叠加 --yes 显式双确认：python3 sample.py cleanup --from-env --yes")
        return
    _run_deletes(config, entries)  # from-env 为内存清单：不落盘
    _log("[cleanup] 完成。本地令牌产物 .tokens/ 未删除（含敏感值）；如需清理：rm -rf .tokens")
