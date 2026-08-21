#!/usr/bin/env python3
"""
OIDC 用户池登录脚本 — 通过 OAuth2 Authorization Code + PKCE 获取 ID Token

用法：
    python3 oidc_login.py \
        --discovery-url https://xxx.auth.aliyuncs.com/.well-known/openid-configuration \
        --client-id YOUR_CLIENT_ID \
        --client-secret YOUR_CLIENT_SECRET
"""

import argparse
import base64
import hashlib
import json
import os
import secrets
import sys
import threading
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

import urllib.request

# ── ANSI 颜色 ────────────────────────────────────────────────────────────────
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_RED = "\033[31m"
C_GREEN = "\033[32m"
C_YELLOW = "\033[33m"
C_BLUE = "\033[34m"
C_CYAN = "\033[36m"
C_DIM = "\033[2m"


def _color(text: str, color: str) -> str:
    return f"{color}{text}{C_RESET}"


def _info(msg: str) -> None:
    print(f"{C_CYAN}▸{C_RESET} {msg}", file=sys.stderr)


def _success(msg: str) -> None:
    print(f"{C_GREEN}✔{C_RESET} {msg}", file=sys.stderr)


def _warn(msg: str) -> None:
    print(f"{C_YELLOW}⚠{C_RESET} {msg}", file=sys.stderr)


def _error(msg: str) -> None:
    print(f"{C_RED}✘{C_RESET} {msg}", file=sys.stderr)


# ── SSL Context ──────────────────────────────────────────────────────────────
def _make_ssl_context():
    """构建 SSL context：优先 certifi → 系统默认 → 禁用验证（最后回退）。"""
    import ssl
    # 1. 尝试 certifi 提供的 CA 证书包
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except (ImportError, OSError):
        pass
    # 2. 使用系统默认 CA 证书
    ctx = ssl.create_default_context()
    if ctx.cert_store_stats()["x509"] > 0:
        return ctx
    # 3. 最后回退：禁用 SSL 验证并打印警告
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    _warn("SSL 证书验证不可用，已跳过。建议安装 certifi: pip install certifi")
    return ctx


# ── OIDC Discovery ───────────────────────────────────────────────────────────
def fetch_oidc_config(discovery_url: str, ssl_context=None) -> dict:
    """获取 OIDC 配置（authorization_endpoint, token_endpoint 等）"""
    _info(f"正在获取 OIDC 配置: {C_DIM}{discovery_url}{C_RESET}")
    req = urllib.request.Request(discovery_url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15, context=ssl_context) as resp:
        config = json.loads(resp.read().decode("utf-8"))
    _success("OIDC 配置获取成功")
    return config


# ── PKCE ─────────────────────────────────────────────────────────────────────
def generate_pkce() -> tuple:
    """生成 PKCE code_verifier 和 code_challenge (S256)"""
    # code_verifier: 43-128 个随机字符 (URL-safe)
    code_verifier = secrets.token_urlsafe(64)[:128]
    # code_challenge: SHA-256(verifier) 的 base64url 编码
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


# ── 构建授权 URL ─────────────────────────────────────────────────────────────
def build_auth_url(
    auth_endpoint: str,
    client_id: str,
    redirect_uri: str,
    scope: str,
    state: str,
    code_challenge: str,
) -> str:
    """构建 OAuth2 授权 URL"""
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    if scope:
        params["scope"] = scope
    return f"{auth_endpoint}?{urllib.parse.urlencode(params)}"


# ── 回调 HTTP Handler ────────────────────────────────────────────────────────
class CallbackHandler(BaseHTTPRequestHandler):
    """处理 OAuth2 回调，提取 authorization code"""

    auth_code: str | None = None
    returned_state: str | None = None

    def do_GET(self):  # noqa: N802
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        if "error" in params:
            error_desc = params.get("error_description", params["error"])[0]
            _error(f"授权服务器返回错误: {error_desc}")
            self._send_response(
                "<h1>登录失败</h1><p>授权服务器返回错误，请查看终端日志。</p>"
            )
            return

        code = params.get("code", [None])[0]
        state = params.get("state", [None])[0]

        if not code:
            _error("回调中缺少 authorization code")
            self._send_response("<h1>登录失败</h1><p>缺少 authorization code。</p>")
            return

        CallbackHandler.auth_code = code
        CallbackHandler.returned_state = state
        _success("收到授权回调")

        self._send_response(
            "<h1>登录成功 ✔</h1>"
            "<p>已获取授权码，你可以关闭此页面并返回终端。</p>"
            f"<style>body{{font-family:sans-serif;text-align:center;padding:60px;}}"
            f"h1{{color:#22c55e;}}p{{color:#666;}}</style>"
        )

        # 处理完一次请求后关闭服务器
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def _send_response(self, html_body: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_body.encode("utf-8"))

    def log_message(self, fmt, *args):  # noqa: ARG002
        # 抑制默认的 HTTP 日志输出
        pass


# ── Token 交换 ───────────────────────────────────────────────────────────────
def exchange_code_for_token(
    token_endpoint: str,
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code_verifier: str,
    ssl_context=None,
) -> dict:
    """用 authorization code 换取 token"""
    _info("正在用授权码换取 Token …")
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
        "code_verifier": code_verifier,
    }).encode("utf-8")
    req = urllib.request.Request(
        token_endpoint,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15, context=ssl_context) as resp:
        token_data = json.loads(resp.read().decode("utf-8"))
    _success("Token 获取成功")
    return token_data


# ── JWT 解码 ─────────────────────────────────────────────────────────────────
def decode_jwt_payload(jwt_token: str) -> dict:
    """解码 JWT payload（不做签名验证）"""
    parts = jwt_token.split(".")
    if len(parts) != 3:
        raise ValueError("无效的 JWT 格式")
    # base64url 解码，补齐 padding
    payload_b64 = parts[1]
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding
    payload_bytes = base64.urlsafe_b64decode(payload_b64)
    return json.loads(payload_bytes)


# ── 参数解析 ─────────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OIDC 用户池登录 — 通过 OAuth2 Authorization Code + PKCE 获取 ID Token"
    )
    parser.add_argument(
        "--discovery-url",
        required=True,
        help="OIDC Discovery 地址，如 https://xxx.auth.aliyuncs.com/.well-known/openid-configuration",
    )
    parser.add_argument("--client-id", required=True, help="OAuth2 Client ID")
    parser.add_argument("--client-secret", required=True, help="OAuth2 Client Secret")
    parser.add_argument(
        "--redirect-port",
        type=int,
        default=int(os.environ.get("OIDC_REDIRECT_PORT", "18080")),
        help="本地回调端口（默认 18080）",
    )
    parser.add_argument(
        "--scope",
        default=os.environ.get("OIDC_SCOPE", ""),
        help="OAuth2 scope（默认不传，如需指定可用 --scope 'openid' 等）",
    )
    return parser.parse_args()


# ── 主流程 ────────────────────────────────────────────────────────────────────
def main() -> None:
    args = parse_args()
    redirect_uri = f"http://localhost:{args.redirect_port}/callback"
    timeout_seconds = 60

    print(file=sys.stderr)
    print(_color("  OIDC 用户池登录", C_BOLD), file=sys.stderr)
    print(_color("  ─────────────────────────────────", C_DIM), file=sys.stderr)
    print(file=sys.stderr)

    # 构建 SSL context
    ssl_context = _make_ssl_context()

    # 1. 获取 OIDC 配置
    try:
        oidc_config = fetch_oidc_config(args.discovery_url, ssl_context=ssl_context)
    except Exception as e:
        _error(f"获取 OIDC 配置失败: {e}")
        sys.exit(1)

    auth_endpoint = oidc_config["authorization_endpoint"]
    token_endpoint = oidc_config["token_endpoint"]
    _info(f"Authorization Endpoint: {C_DIM}{auth_endpoint}{C_RESET}")
    _info(f"Token Endpoint:         {C_DIM}{token_endpoint}{C_RESET}")
    print(file=sys.stderr)

    # 2. 生成 PKCE + state
    code_verifier, code_challenge = generate_pkce()
    state = secrets.token_urlsafe(32)
    _info(f"PKCE code_challenge: {C_DIM}{code_challenge[:24]}…{C_RESET}")
    _info(f"State:               {C_DIM}{state[:24]}…{C_RESET}")
    print(file=sys.stderr)

    # 3. 构建授权 URL
    auth_url = build_auth_url(
        auth_endpoint, args.client_id, redirect_uri, args.scope, state, code_challenge
    )

    # 4. 启动本地回调服务器
    _info(f"启动本地回调服务器 (端口 {args.redirect_port}) …")
    server = HTTPServer(("localhost", args.redirect_port), CallbackHandler)
    server.timeout = timeout_seconds
    _success(f"回调服务器已就绪: {C_DIM}{redirect_uri}{C_RESET}")

    # 5. 打开浏览器
    _info("正在打开浏览器进行授权 …")
    print(f"\n  {_color('授权链接:', C_BOLD)}\n  {C_DIM}{auth_url}{C_RESET}\n", file=sys.stderr)
    webbrowser.open(auth_url)
    _info(f"等待回调（超时 {timeout_seconds} 秒）…")

    # 6. 等待回调获取 code
    try:
        server.handle_request()  # 阻塞直到收到一次请求或超时
    except KeyboardInterrupt:
        print(file=sys.stderr)
        _warn("用户中断 (Ctrl+C)")
        server.server_close()
        sys.exit(0)

    server.server_close()

    # 检查是否收到 code
    if not CallbackHandler.auth_code:
        _error(f"在 {timeout_seconds} 秒内未收到授权回调，请重试。")
        sys.exit(1)

    # 校验 state
    if CallbackHandler.returned_state != state:
        _error("State 参数不匹配，可能存在 CSRF 攻击！")
        sys.exit(1)
    _success("State 校验通过")

    auth_code = CallbackHandler.auth_code
    _info(f"Authorization Code: {C_DIM}{auth_code[:16]}…{C_RESET}")
    print(file=sys.stderr)

    # 7. 换取 token
    try:
        token_data = exchange_code_for_token(
            token_endpoint,
            auth_code,
            args.client_id,
            args.client_secret,
            redirect_uri,
            code_verifier,
            ssl_context=ssl_context,
        )
    except Exception as e:
        _error(f"换取 Token 失败: {e}")
        sys.exit(1)

    # 8. 输出 ID Token
    id_token = token_data.get("id_token")
    if not id_token:
        _error("Token 响应中缺少 id_token 字段")
        _info(f"响应内容: {json.dumps(token_data, indent=2, ensure_ascii=False)}")
        sys.exit(1)

    print(file=sys.stderr)
    print(_color("  ── ID Token ──────────────────────────────────", C_DIM), file=sys.stderr)
    print(file=sys.stderr)
    # 纯 JWT token 输出到 stdout（供串联脚本捕获）
    print(id_token)
    print(file=sys.stderr)

    # 9. 解码并显示用户信息
    try:
        payload = decode_jwt_payload(id_token)
        print(_color("  ── Token Payload ─────────────────────────────", C_DIM), file=sys.stderr)
        print(file=sys.stderr)

        display_fields = [
            ("sub", "Subject"),
            ("name", "Name"),
            ("email", "Email"),
            ("preferred_username", "Username"),
            ("iss", "Issuer"),
            ("aud", "Audience"),
            ("exp", "Expires At"),
            ("iat", "Issued At"),
        ]
        for key, label in display_fields:
            if key in payload:
                print(f"  {C_BOLD}{label:>12}{C_RESET}  {payload[key]}", file=sys.stderr)

        # 打印完整 payload
        print(file=sys.stderr)
        print(_color("  ── 完整 Payload (JSON) ───────────────────────", C_DIM), file=sys.stderr)
        print(file=sys.stderr)
        print(f"  {C_DIM}{json.dumps(payload, indent=2, ensure_ascii=False)}{C_RESET}", file=sys.stderr)
        print(file=sys.stderr)
    except Exception as e:
        _warn(f"解码 JWT payload 失败: {e}")

    _success("完成！")
    print(file=sys.stderr)


if __name__ == "__main__":
    main()
