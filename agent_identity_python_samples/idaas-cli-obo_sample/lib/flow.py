"""数据面三步流程：login（浏览器 + loopback 回调）→ exchange-wat（身份升维）→ obo（出站）。

实现要点（对照旧样例 oidc_login.py 的五处缺陷逐一修复）：
- ThreadingHTTPServer 绑定 ``127.0.0.1``（不用 localhost，避免 IPv6 解析歧义）；
- 端口预检：bind 失败即给出「--port 换端口 + 白名单 loopback 忽略端口」指引；
- state 校验下沉到回调 handler 内完成（而非收码后二次校验）；
- 超时默认 300s（可 ``--timeout`` 调整），定时器到点 shutdown；
- 多线程 server：favicon 等额外请求不阻塞回调处理。

契约（预发实测确认）：
- authorize：GET ``{SIGNIN_BASE_URL}/{POOL_ID}/oauth2/authorize``（302 开始登录链）；
- token 兑换：POST ``{SIGNIN_BASE_URL}/{POOL_ID}/oauth2/token``，form 表单
  （grant_type=authorization_code / code / redirect_uri / client_id / client_secret /
  code_verifier），PKCE S256 强制；redirect_uri 必须与 authorize 时逐字符一致；
- GetWorkloadAccessTokenForJWT：query 风格（WorkloadIdentityName / UserToken）；
- GetResourceOAuth2Token：formData 风格，Scopes 传 JSON 数组字符串（禁止逐个传参）。
"""

import base64
import hashlib
import json
import secrets
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple

from . import env as env_mod
from . import rpc
from . import tokens as tokens_mod

DATA_API_VERSION = "2025-11-27"

_PAGE_STYLE = (
    "body{font-family:system-ui,sans-serif;text-align:center;padding:64px 24px;"
    "color:#333}h1{font-size:22px}p{color:#666;line-height:1.8}"
)


class FlowError(Exception):
    """流程错误：message 自带下一步指引。"""


# ---------------------------------------------------------------------------
# 公共辅助
# ---------------------------------------------------------------------------


def require_config(config: Dict[str, str], keys: Tuple[str, ...]) -> None:
    """必填 env 校验：缺失时抛带「在哪取值」指引的 FlowError。"""
    missing = [k for k in keys if env_mod.is_placeholder(config.get(k, ""))]
    if missing:
        hints = []
        for key in missing:
            hint = env_mod.ENV_SCHEMA.get(key, (None, None, "见 env.template 注释"))[2]
            hints.append("  - {}：{}".format(key, hint))
        raise FlowError(
            "缺少必要配置项（共 {} 项）：\n{}\n请编辑 {} 补齐，或先运行 "
            "python3 sample.py setup --mode=console 查看资源准备清单。".format(
                len(missing), "\n".join(hints), env_mod.ENV_FILE
            )
        )


def creds_from_env(config: Dict[str, str]) -> Tuple[str, str, Optional[str]]:
    """从配置构造 RPC 凭证 (AK, SK, SecurityToken|None)。"""
    require_config(config, ("ALIYUN_ACCESS_KEY_ID", "ALIYUN_ACCESS_KEY_SECRET"))
    st = config.get("ALIYUN_SECURITY_TOKEN", "")
    return (
        config["ALIYUN_ACCESS_KEY_ID"],
        config["ALIYUN_ACCESS_KEY_SECRET"],
        st if st and not env_mod.is_placeholder(st) else None,
    )


def client_secret_from_env(config: Dict[str, str]) -> str:
    """池 OAuth 客户端密钥：优先 0600 文件。"""
    try:
        return env_mod.get_secret(
            config, "OAUTH_CLIENT_SECRET", "OAUTH_CLIENT_SECRET_FILE", "池 OAuth 客户端密钥"
        )
    except KeyError as exc:
        raise FlowError(str(exc)) from None


def rpc_error_hint(action: str, exc: rpc.RpcError) -> str:
    """把常见 RpcError 映射为「下一步指引」文案。"""
    code = exc.code or ""
    if code == "Forbidden.InboundCredentialMissing":
        return (
            "region 按 (pool, user, session_id) 查不到入站托管凭证。常见原因：浏览器复用了"
            "旧的池登录会话导致 session_id 不匹配，或登录未走联邦入口。"
            "→ 请用无痕窗口（或先清理浏览器会话）重跑：python3 sample.py login"
        )
    if code.startswith("InvalidParameter.JsonWebToken"):
        return (
            "服务端拒绝 UserToken（通常为 ID Token 过期或 issuer 不匹配）。"
            "→ 请重跑：python3 sample.py login，成功后立即执行后续步骤"
        )
    if code.startswith("InvalidParameter.WorkloadAccessToken") or "expired" in exc.message.lower():
        return (
            "WAT 无效或已过期（实测有效期仅约 5 分钟）。"
            "→ 请重跑：python3 sample.py exchange-wat，随后立即 obo"
        )
    if code == "ServiceUnavailable.UpstreamTokenEndpoint":
        return (
            "region 调上游 IDaaS token 端点失败：通常是出站 provider 侧应用密钥缺失/失效。"
            "→ 检查 OBO_PROVIDER_NAME 对应 provider 的配置（IDaaS 侧订单服务应用密钥）"
        )
    if code.startswith("EntityNotExists"):
        return (
            "资源不存在：检查 .env 的 WI_NAME / OBO_PROVIDER_NAME 是否与控制台一致"
            "（或重跑 setup 确认产出）。若为 OBO_PROVIDER_NAME 失效（provider 被清理"
            "或配额被占）：先用 ListOAuth2CredentialProviders（或控制台「凭证提供商」页）"
            "查现存 provider——若已被删除且配额空闲，重跑 setup --mode=script 重建并"
            "回写 .env；若配额被其他 provider 占用，需先确认旧 provider 可删再重建。"
        )
    if code.startswith("EntityAlreadyExists"):
        return "资源已存在：sample 按名复用即可；provider 配额=1，如需重建先删旧再建"
    if code.startswith("InvalidAccessKeyId") or code.startswith("InvalidSecurityToken"):
        return "AK/STS 凭证无效：检查 .env 的 ALIYUN_ACCESS_KEY_* 配置（注意 STS 时效）"
    if code.startswith("Throttling"):
        return "触发限流：sample 已自动退避重试仍失败，稍等 1 分钟后重跑"
    return "携带 RequestId={} 与上述错误码排查；常见配置见 docs/troubleshooting.md".format(
        exc.request_id or "-"
    )


# ---------------------------------------------------------------------------
# 第 1 步：login（浏览器 + loopback 回调）
# ---------------------------------------------------------------------------


def generate_pkce() -> Tuple[str, str]:
    """PKCE code_verifier / code_challenge(S256)。"""
    verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


class _CallbackState:
    """回调结果容器（handler 与主线程通过它交互）。"""

    def __init__(self, expected_state: str, expected_nonce: str):
        self.expected_state = expected_state
        self.expected_nonce = expected_nonce
        self.code: Optional[str] = None
        self.error: Optional[str] = None
        self.error_description: Optional[str] = None
        self.done = threading.Event()


class _LoginCallbackHandler(BaseHTTPRequestHandler):
    """loopback 回调 handler：state 校验下沉至此，多线程 server。"""

    protocol_version = "HTTP/1.1"

    def _page(self, status: int, title: str, detail: str) -> None:
        html = (
            "<!doctype html><html lang=\"zh\"><head><meta charset=\"utf-8\">"
            "<title>{}</title><style>{}</style></head><body><h1>{}</h1><p>{}</p>"
            "</body></html>"
        ).format(title, _PAGE_STYLE, title, detail)
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _finish(self, ok: bool) -> None:
        state = self.server.cb_state  # type: ignore[attr-defined]
        state.done.set()
        threading.Thread(target=self.server.shutdown, daemon=True).start()  # type: ignore[attr-defined]

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        pass  # 回调 server 不打默认日志（避免刷屏）

    def do_GET(self) -> None:  # noqa: N802
        state = self.server.cb_state  # type: ignore[attr-defined]
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self._page(404, "未知路径", "本服务仅处理 /callback（OAuth loopback 回调）。")
            return
        params = urllib.parse.parse_qs(parsed.query)

        # state 校验先于一切结果处理（含 error 回调）：伪造的 error 回调
        # （恶意网页 <img> 标签或本机进程均可构造）不能打断正在进行的登录。
        returned_state = (params.get("state") or [None])[0]
        if returned_state != state.expected_state:
            if "error" in params:
                # error 回调但 state 不匹配：判定为伪造/陈旧，忽略并继续等待真实回调
                self._page(
                    400,
                    "已忽略",
                    "已忽略：state 不匹配的 error 回调（疑似伪造或陈旧回调）。"
                    "正在继续等待真实的登录回调，请回到浏览器完成登录。",
                )
                return
            state.error = "state_mismatch"
            state.error_description = "回调 state 与发起时不一致（可能被篡改或为陈旧回调）"
            self._page(400, "登录失败", "state 校验未通过，已拒绝该回调。请回到终端重试。")
            self._finish(False)
            return

        if "error" in params:
            state.error = params["error"][0]
            state.error_description = (params.get("error_description") or [state.error])[0]
            self._page(400, "登录失败", "授权服务器返回错误：{}。<br/>请回到终端查看指引。".format(state.error))
            self._finish(False)
            return

        code = (params.get("code") or [None])[0]
        if not code:
            state.error = "missing_code"
            state.error_description = "回调缺少 authorization code"
            self._page(400, "登录失败", "回调中缺少授权码。请回到终端重试。")
            self._finish(False)
            return

        state.code = code
        self._page(
            200,
            "登录成功",
            "已收到授权码并校验通过，正在兑换令牌。<br/>可以关闭本页面并回到终端查看结果。",
        )
        self._finish(True)


def _exchange_code(
    token_endpoint: str,
    code: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str,
    code_verifier: str,
    timeout: int = 30,
) -> Dict[str, Any]:
    """用授权码 + PKCE 兑换池令牌（redirect_uri 必须与 authorize 时逐字符一致）。"""
    form = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
        "code_verifier": code_verifier,
    }
    req = urllib.request.Request(
        token_endpoint,
        data=urllib.parse.urlencode(form).encode("utf-8"),
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=rpc.ssl_context()) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = ""
        try:
            raw = exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        err, desc = "", raw[:300]
        try:
            data = json.loads(raw)
            err = str(data.get("error", ""))
            desc = str(data.get("error_description", ""))[:300] or err
        except (ValueError, TypeError):
            pass
        hint = ""
        if err in ("invalid_grant", "invalid_request") or "redirect" in desc.lower():
            hint = "（提示：兑换时 redirect_uri 必须与 authorize 时逐字符一致；授权码一次性，重试请重新 login）"
        raise FlowError(
            "兑换池令牌失败：HTTP {} error={} description={}{}。请重跑 python3 sample.py login".format(
                exc.code, err or "?", desc, hint
            )
        ) from None
    except (urllib.error.URLError, OSError) as exc:
        raise FlowError(
            "无法连接 token 端点 {}：{}。检查 SIGNIN_BASE_URL 配置与网络。".format(token_endpoint, exc)
        ) from None


def run_login(port: int = 8765, timeout: int = 300, config: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """数据面第 1 步：浏览器联邦登录 → loopback 回调 → 兑换池 ID Token。

    返回 dict：id_token / access_token / id_claims / at_claims / files。
    """
    config = env_mod.derive_defaults(config or env_mod.load_env())
    require_config(config, ("USER_POOL_ID", "OAUTH_CLIENT_ID", "SIGNIN_BASE_URL"))
    client_secret = client_secret_from_env(config)
    signin_base = config["SIGNIN_BASE_URL"].rstrip("/")
    pool_id = config["USER_POOL_ID"]

    # --- 1. 起 loopback server（bind 即端口预检）---
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), _LoginCallbackHandler)
    except OSError as exc:
        raise FlowError(
            "无法监听 127.0.0.1:{}（{}）。端口被占用很常见（如本机 IDE 等常驻进程）。\n"
            "→ 两个办法：① 用 --port 换一个端口（例如 python3 sample.py login --port 8766）；"
            "② 白名单无需同步改——用户池客户端 redirect_uri 白名单含任意一条 loopback 条目"
            "（localhost/127.0.0.1）即放行且忽略端口。".format(port, exc)
        ) from None
    server.daemon_threads = True
    bound_port = server.server_address[1]

    # redirect_uri 从实际绑定端口动态构造：authorize 与兑换两侧保证逐字符一致
    redirect_uri = "http://127.0.0.1:{}/callback".format(bound_port)

    code_verifier, code_challenge = generate_pkce()
    state = secrets.token_urlsafe(24)
    nonce = secrets.token_urlsafe(16)
    server.cb_state = _CallbackState(state, nonce)  # type: ignore[attr-defined]

    authorize_url = "{}/{}/oauth2/authorize?{}".format(
        signin_base,
        pool_id,
        urllib.parse.urlencode(
            {
                "response_type": "code",
                "client_id": config["OAUTH_CLIENT_ID"],
                "redirect_uri": redirect_uri,
                "scope": "openid",
                "state": state,
                "nonce": nonce,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
            }
        ),
    )

    print("[login] 回调服务已就绪：{}（超时 {}s）".format(redirect_uri, timeout))
    print("[login] 正在打开浏览器完成 IDaaS 联邦登录 …")
    print("[login] 若浏览器未自动打开，请手动复制以下地址：")
    print("        {}".format(authorize_url))
    print("[login] 提示：建议使用无痕/隐私窗口——复用浏览器旧池会话会导致 session_id 不匹配，")
    print("        后续 OBO 报 Forbidden.InboundCredentialMissing。")
    print("[login] 提示：IDaaS 登录若启用邮箱 OTP/MFA，请在浏览器内按页面引导完成。")
    try:
        webbrowser.open(authorize_url)
    except Exception:  # pragma: no cover - 无 GUI 环境
        pass

    # --- 2. 等待回调（超时定时 shutdown）---
    timer = threading.Timer(timeout, server.shutdown)
    timer.daemon = True
    timer.start()
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        timer.cancel()
        server.server_close()

    cb: _CallbackState = server.cb_state  # type: ignore[assignment]
    if cb.code is None:
        reason = cb.error or "timeout"
        detail = cb.error_description or "在 {}s 内未收到授权回调".format(timeout)
        raise FlowError(
            "登录未完成：{}（{}）。\n→ 请重跑 python3 sample.py login；"
            "若反复失败，确认用无痕窗口且网络可达 {}。".format(reason, detail, signin_base)
        )

    # --- 3. 兑换池令牌 ---
    print("[login] 授权码已收到（state 校验通过），正在兑换池令牌 …")
    token_resp = _exchange_code(
        "{}/{}/oauth2/token".format(signin_base, pool_id),
        cb.code,
        redirect_uri,
        config["OAUTH_CLIENT_ID"],
        client_secret,
        code_verifier,
    )
    id_token = token_resp.get("id_token") or ""
    access_token = token_resp.get("access_token") or ""
    if not id_token:
        raise FlowError(
            "token 响应缺少 id_token 字段（返回键：{}）。→ 请重跑 login；"
            "若持续缺失检查客户端注册 scope 是否含 openid。".format(
                ", ".join(sorted(token_resp.keys()))
            )
        )

    # --- 4. claims 教学断言（只解码不验签：池 JWKS 公网路径见 troubleshooting 文档）---
    try:
        id_claims = tokens_mod.decode_jwt_payload(id_token)
    except (ValueError, json.JSONDecodeError) as exc:
        raise FlowError("id_token 解码失败：{}。→ 请重跑 login".format(exc)) from None
    at_claims = {}
    if access_token:
        try:
            at_claims = tokens_mod.decode_jwt_payload(access_token)
        except (ValueError, json.JSONDecodeError):
            at_claims = {}

    print("[login] 池 ID Token 已获取（{}）".format(tokens_mod.mask(id_token)))
    print("[login] claims 教学断言（仅解码，不验签——JWKS 公网路径见 docs/troubleshooting.md）：")
    print("        sub        = {}".format(id_claims.get("sub")))
    print("        iss        = {}".format(id_claims.get("iss")))
    print("        aud        = {}（应含 OAUTH_CLIENT_ID）".format(id_claims.get("aud")))
    sid = id_claims.get("session_id") or at_claims.get("session_id")
    print("        session_id = {}".format(sid if sid else "<缺失！OBO 将报 InboundCredentialMissing>"))
    print("                   └─ session_id 是 OBO 的定位键：region 按 (pool, user, session_id) 查托管入站凭证")
    nonce_echo = id_claims.get("nonce")
    nonce_ok = nonce_echo == nonce
    print(
        "        nonce      = {}（回显校验：{}）".format(
            nonce_echo, "通过" if nonce_ok else "失败！id_token 未回显 nonce，可能是响应被替换"
        )
    )
    if not nonce_ok:
        raise FlowError("nonce 回显校验失败（期望 {}，实际 {}）→ 请重跑 login".format(nonce, nonce_echo))

    # --- 5. 落盘 ---
    tokens_mod.save_token("id_token", id_token)
    if access_token:
        tokens_mod.save_token("access_token", access_token)
    tokens_mod.save_json(
        "login.meta",
        {"acquired_at": time.time(), "sub": id_claims.get("sub", "")},
    )
    print("[login] 已落盘 .tokens/id_token（0600）→ 下一步：python3 sample.py exchange-wat")
    return {
        "id_token": id_token,
        "access_token": access_token,
        "id_claims": id_claims,
        "at_claims": at_claims,
    }


# ---------------------------------------------------------------------------
# 第 2 步：exchange-wat（身份升维）
# ---------------------------------------------------------------------------


def run_exchange_wat(config: Optional[Dict[str, str]] = None) -> str:
    """数据面第 2 步：池 ID Token → WAT（GetWorkloadAccessTokenForJWT，query 风格）。"""
    config = env_mod.derive_defaults(config or env_mod.load_env())
    require_config(config, ("DATA_ENDPOINT", "WI_NAME", "ALIYUN_ACCESS_KEY_ID", "ALIYUN_ACCESS_KEY_SECRET"))
    creds = creds_from_env(config)

    try:
        id_token = tokens_mod.load_id_token()
    except tokens_mod.TokenExpiredError as exc:
        raise FlowError(str(exc)) from None

    print("[exchange-wat] 调用 GetWorkloadAccessTokenForJWT（endpoint={}）…".format(config["DATA_ENDPOINT"]))
    print("[exchange-wat] 说明：真实场景中这一步由 Agent 框架自动完成（用户无感）；")
    print("                此处用 CLI 直接调用，仅为演示身份从「人」升维为「工作负载」。")
    try:
        resp = rpc.rpc_call(
            config["DATA_ENDPOINT"],
            "GetWorkloadAccessTokenForJWT",
            DATA_API_VERSION,
            {"WorkloadIdentityName": config["WI_NAME"], "UserToken": id_token},
            style="query",
            creds=creds,
        )
    except rpc.RpcError as exc:
        raise FlowError(
            "GetWorkloadAccessTokenForJWT 失败：{}\n→ {}".format(exc, rpc_error_hint("GetWAT", exc))
        ) from None

    wat = resp.get("WorkloadAccessToken") or ""
    if not wat:
        err_detail = rpc.err_code(resp)
        if err_detail:
            err_detail = "，Code={} Message={}".format(
                err_detail, resp.get("Message") or resp.get("message") or ""
            )
        raise FlowError(
            "响应缺少 WorkloadAccessToken 字段（返回键：{}{}，RequestId={}）".format(
                ", ".join(sorted(resp.keys())), err_detail, resp.get("RequestId", "-")
            )
        )
    tokens_mod.save_wat(wat)
    print("[exchange-wat] 成功（RequestId={}）".format(resp.get("RequestId", "-")))
    print(
        "[exchange-wat] WAT 已落盘（{}）。注意：WAT 为 JWE 加密令牌，本地不可解码，"
        "属设计行为；有效期很短（实测约 5 分钟）→ 请立即执行 obo".format(tokens_mod.mask(wat))
    )
    return wat


# ---------------------------------------------------------------------------
# 第 3 步：obo（出站换令牌）
# ---------------------------------------------------------------------------


def serialize_scopes(scopes_csv: str) -> str:
    """逗号分隔 scope → JSON 数组字符串（契约要求，禁止逐个传参）。"""
    items = [s.strip() for s in (scopes_csv or "").split(",") if s.strip()]
    return json.dumps(items)


def run_obo(config: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """数据面第 3 步：WAT → 订单服务 AT/RT（GetResourceOAuth2Token，formData 风格）。"""
    config = env_mod.derive_defaults(config or env_mod.load_env())
    require_config(
        config,
        (
            "DATA_ENDPOINT",
            "OBO_PROVIDER_NAME",
            "ORDER_SERVICE_AUDIENCE",
            "ALIYUN_ACCESS_KEY_ID",
            "ALIYUN_ACCESS_KEY_SECRET",
        ),
    )
    creds = creds_from_env(config)

    try:
        wat = tokens_mod.load_wat()
    except tokens_mod.TokenExpiredError as exc:
        raise FlowError(str(exc)) from None

    scopes_json = serialize_scopes(config.get("ORDER_SERVICE_SCOPES", "read,write.all"))
    print("[obo] 调用 GetResourceOAuth2Token（OAuth2Flow=ON_BEHALF_OF）…")
    print("      Provider={} Audience={} Scopes={}".format(
        config["OBO_PROVIDER_NAME"], config["ORDER_SERVICE_AUDIENCE"], scopes_json
    ))
    print("      契约：业务参数必须全部放 formData body（Scopes 传 JSON 数组字符串，禁止逐个传参）")
    try:
        resp = rpc.rpc_call(
            config["DATA_ENDPOINT"],
            "GetResourceOAuth2Token",
            DATA_API_VERSION,
            {
                "OAuth2Flow": "ON_BEHALF_OF",
                "WorkloadAccessToken": wat,
                "ResourceCredentialProviderName": config["OBO_PROVIDER_NAME"],
                "Audience": config["ORDER_SERVICE_AUDIENCE"],
                "Scopes": scopes_json,
            },
            style="formData",
            creds=creds,
            wait_window=True,
        )
    except rpc.RpcError as exc:
        raise FlowError(
            "GetResourceOAuth2Token 失败：{}\n→ {}".format(exc, rpc_error_hint("OBO", exc))
        ) from None

    at = resp.get("OAuth2Token") or resp.get("ResourceOAuth2Token") or resp.get("AccessToken") or ""
    rt = resp.get("RefreshToken") or resp.get("OAuth2RefreshToken") or ""
    if not at:
        err_detail = rpc.err_code(resp)
        if err_detail:
            err_detail = "，Code={} Message={}".format(
                err_detail, resp.get("Message") or resp.get("message") or ""
            )
        raise FlowError(
            "响应缺少令牌字段（返回键：{}{}，RequestId={}）".format(
                ", ".join(sorted(resp.keys())), err_detail, resp.get("RequestId", "-")
            )
        )
    tokens_mod.save_token("order_at", at)
    if rt:
        tokens_mod.save_token("order_rt", rt)

    print("[obo] 成功（RequestId={}）：订单服务 AT 已落盘（{}）".format(
        resp.get("RequestId", "-"), tokens_mod.mask(at)
    ))
    if rt:
        print("[obo] 订单服务 RT 已落盘（{}）；刷新令牌仅作演示，sample 不实现刷新流程".format(
            tokens_mod.mask(rt)
        ))

    # --- AT claims 教学断言（OBO 委托语义核心：sub=员工，act.sub=工作负载身份）---
    try:
        claims = tokens_mod.decode_jwt_payload(at)
    except (ValueError, json.JSONDecodeError):
        print("[obo] AT 不是可解码 JWT（不透明令牌），跳过 claims 打印")
        return {"order_at": at, "order_rt": rt, "claims": {}}
    print("[obo] AT claims（on-behalf-of 委托语义）：")
    print("        iss     = {}（令牌由 IDaaS 签发）".format(claims.get("iss")))
    print("        aud     = {}（受众=订单服务应用）".format(claims.get("aud")))
    print("        scope   = {}".format(claims.get("scope")))
    print("        sub     = {}（主体=登录员工）".format(claims.get("sub")))
    act = claims.get("act") or {}
    if isinstance(act, dict):
        print("        act.sub = {}（实际执行者=工作负载身份 ARN：Agent 以用户名义行事）".format(act.get("sub")))
    exp = claims.get("exp")
    if isinstance(exp, (int, float)):
        print("        exp     = {}（余 {} 秒）".format(
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(exp)), int(exp - time.time())
        ))
    print("[obo] 下一步：python3 sample.py serve-orders（或直接 python3 sample.py demo 全链路）")
    return {"order_at": at, "order_rt": rt, "claims": claims}
