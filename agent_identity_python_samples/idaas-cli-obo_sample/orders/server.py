"""本地模拟订单企业服务（数据面第 4 步：消费并校验 OBO 出站令牌）。

路由：
- ``GET /health``  无需鉴权，返回服务信息（探活用）；
- ``GET /orders``  Bearer 验签通过后：scope 含 ``read.all`` → 全量订单；
                   否则按 ``sub`` 只返回本人订单；
- ``POST /orders`` scope 含 ``write.all`` → 受理新订单；否则 403。

安全约定：
- 401/403 响应体只含 ``{"error", "error_description"}``，绝不回显令牌本体；
- 日志中的 Authorization 一律脱敏（只打印前若干字符）。
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

from . import mock_data
from .verify import InvalidTokenError, JwksFetchError, TokenVerifier, scopes_from_claims

try:
    # 端口绑定失败时抛 FlowError（文案对齐 login 模式，sample.py main 统一捕获）；
    # orders/ 被单独拷走部署（无 lib 包）时回退 RuntimeError。
    from lib.flow import FlowError
except ImportError:  # pragma: no cover - orders 独立部署场景
    FlowError = None  # type: ignore[assignment,misc]

HOST = "127.0.0.1"
DEFAULT_PORT = 9090

# POST /orders 请求体大小上限（字节）：超出直接 413，避免恶意超大体拖垮本地服务
MAX_BODY_BYTES = 1 * 1024 * 1024


def mask_token(token: str) -> str:
    """日志用脱敏：前 8 字符 + … + 总长度。"""
    if not token:
        return "<empty>"
    return "{}…(len={})".format(token[:8], len(token))


def authenticate(
    verifier: TokenVerifier, auth_header: Optional[str]
) -> Tuple[Optional[Dict[str, Any]], Optional[Tuple[int, Dict[str, Any]]]]:
    """解析并校验 Authorization: Bearer <token>。

    返回 (claims, None) 或 (None, (status, error_body))。
    """
    if not auth_header:
        return None, (
            401,
            {
                "error": "invalid_request",
                "error_description": "缺少 Authorization: Bearer 请求头（令牌本体不会出现在本响应中）",
            },
        )
    parts = auth_header.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        return None, (
            401,
            {
                "error": "invalid_request",
                "error_description": "Authorization 头格式应为 'Bearer <token>'",
            },
        )
    token = parts[1].strip()
    try:
        claims = verifier.verify(token)
        return claims, None
    except InvalidTokenError as exc:
        return None, (401, {"error": "invalid_token", "error_description": str(exc)})
    except JwksFetchError as exc:
        # JWKS 源故障：服务端依赖不可用 → 503（区别于客户端令牌问题）
        return None, (
            503,
            {"error": "temporarily_unavailable", "error_description": "验签公钥暂不可用：{}".format(exc)},
        )


def handle_get_orders(claims: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """GET /orders 业务逻辑：read.all → 全量；否则按 sub 过滤本人订单。"""
    sub = claims.get("sub")
    if not sub:
        return 401, {
            "error": "invalid_token",
            "error_description": "令牌缺少 sub claim，无法识别用户身份",
        }
    scopes = scopes_from_claims(claims)
    if "read.all" in scopes:
        return 200, {
            "scope_view": "all",
            "sub": sub,
            "count": len(mock_data.all_orders()),
            "orders": mock_data.all_orders(),
        }
    own = mock_data.orders_for_sub(sub)
    return 200, {
        "scope_view": "own",
        "sub": sub,
        "count": len(own),
        "orders": own,
    }


def handle_post_orders(claims: Dict[str, Any], body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """POST /orders 业务逻辑：write.all → 受理；否则 403。"""
    sub = claims.get("sub")
    if not sub:
        return 401, {
            "error": "invalid_token",
            "error_description": "令牌缺少 sub claim，无法识别用户身份",
        }
    scopes = scopes_from_claims(claims)
    if "write.all" not in scopes:
        return 403, {
            "error": "insufficient_scope",
            "error_description": "需要 write.all 权限（当前 scope：{}）".format(
                " ".join(scopes) or "<空>"
            ),
        }
    title = body.get("title")
    amount = body.get("amount", 0)
    if not isinstance(title, str) or not title.strip():
        return 400, {
            "error": "invalid_request",
            "error_description": "请求体需为 JSON 且包含非空 title 字段",
        }
    order = mock_data.create_order(sub, title.strip(), amount)
    return 201, {"accepted": True, "order": order}


class OrdersHandler(BaseHTTPRequestHandler):
    """订单服务 HTTP handler（verifier 由 make_server 注入到 server 属性）。"""

    server_version = "OrderServiceSample/1.0"
    protocol_version = "HTTP/1.1"

    # ---- 工具 ----

    def _verifier(self) -> TokenVerifier:
        return self.server.verifier  # type: ignore[attr-defined]

    def _send_json(self, status: int, payload: Dict[str, Any], extra_headers: Optional[Dict[str, str]] = None) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _send_www_auth_json(self, status: int, payload: Dict[str, Any]) -> None:
        """401 响应：附 RFC 6750 风格 WWW-Authenticate 头。

        HTTP 头只允许 ASCII：error_description 统一 percent-encode（RFC 6750 允许），
        中文原文保留在 JSON 响应体里。
        """
        from urllib.parse import quote

        desc = quote(str(payload.get("error_description", "")), safe="")
        header = 'Bearer realm="orders", error="{}", error_description="{}"'.format(
            payload.get("error", "invalid_token"), desc
        )
        self._send_json(status, payload, {"WWW-Authenticate": header})

    def _read_body_json(self) -> Optional[Dict[str, Any]]:
        """读 JSON 请求体。

        返回 dict：非法 Content-Length（如 "abc"）/ 非 JSON / 非对象一律按空体 {}
        处理（后续由业务层给出 400，而非裸栈）；超过 MAX_BODY_BYTES（1MB）时
        直接回 413 并返回 None（调用方收到 None 立即结束本请求处理）。
        """
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return {}
        if length <= 0:
            return {}
        if length > MAX_BODY_BYTES:
            self._send_json(
                413,
                {
                    "error": "request_too_large",
                    "error_description": "请求体超过 1MB 上限（声明长度 {}）".format(length),
                },
                {"Connection": "close"},
            )
            self.close_connection = True  # 超大体不读入内存，直接断开连接
            return None
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except (ValueError, UnicodeDecodeError):
            return {}

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        """默认日志改造：Authorization 脱敏后输出。"""
        rendered = fmt % args
        auth = self.headers.get("Authorization") if self.headers else None
        if auth:
            rendered += " | Authorization: {}".format(mask_token(auth))
        print("[orders] {}".format(rendered))

    # ---- 路由 ----

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/health":
            self._send_json(
                200,
                {
                    "service": "order-service-sample",
                    "status": "ok",
                    "issuer": self._verifier().issuer,
                    "note": "本地模拟订单企业服务；GET /orders 需 Bearer 令牌",
                },
            )
            return
        if path == "/orders":
            claims, failure = authenticate(self._verifier(), self.headers.get("Authorization"))
            if failure:
                status, payload = failure
                if status == 401:
                    self._send_www_auth_json(status, payload)
                else:
                    self._send_json(status, payload)
                return
            status, payload = handle_get_orders(claims)
            self._send_json(status, payload)
            return
        self._send_json(404, {"error": "not_found", "error_description": "未知路由 {}".format(path)})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path != "/orders":
            self._send_json(404, {"error": "not_found", "error_description": "未知路由 {}".format(path)})
            return
        claims, failure = authenticate(self._verifier(), self.headers.get("Authorization"))
        if failure:
            status, payload = failure
            if status == 401:
                self._send_www_auth_json(status, payload)
            else:
                self._send_json(status, payload)
            return
        body = self._read_body_json()
        if body is None:
            return  # 超限已回 413 并关闭连接，不再叠加业务响应
        status, payload = handle_post_orders(claims, body)
        self._send_json(status, payload)


def make_server(
    port: int = DEFAULT_PORT,
    verifier: Optional[TokenVerifier] = None,
    host: str = HOST,
) -> ThreadingHTTPServer:
    """构造订单服务（port=0 时由 OS 分配临时端口，测试用）。

    verifier 缺省时按 .env 配置（ORDER_SERVICE_ISSUER/AUDIENCE/JWKS_URI）构造。
    """
    if verifier is None:
        from lib import env as env_mod

        config = env_mod.derive_defaults(env_mod.load_env())
        verifier = TokenVerifier(
            issuer=config.get("ORDER_SERVICE_ISSUER", ""),
            audience=config.get("ORDER_SERVICE_AUDIENCE", ""),
            jwks_uri=config.get("ORDER_SERVICE_JWKS_URI", ""),
        )
    try:
        server = ThreadingHTTPServer((host, port), OrdersHandler)
    except OSError as exc:
        # 端口占用等绑定失败：对齐 login 的 FlowError 模式（提示 --port 换端口），
        # 避免裸 OSError 栈直接打到用户脸上。
        message = (
            "无法监听 {}:{}（{}）。端口被占用很常见（如本机常驻进程）。\n"
            "→ 用 --port 换一个端口重试（例如 python3 sample.py serve-orders --port 9091）；"
            "订单服务是本地模拟服务，换端口不影响云端配置。".format(host, port, exc)
        )
        if FlowError is not None:
            raise FlowError(message) from None
        raise RuntimeError(message) from None  # pragma: no cover - orders 独立部署场景
    server.daemon_threads = True
    server.verifier = verifier  # type: ignore[attr-defined]
    return server


def serve_foreground(port: int = DEFAULT_PORT) -> None:
    """serve-orders 子命令入口：前台运行直至 Ctrl+C。"""
    server = make_server(port=port)
    bound_host, bound_port = server.server_address[:2]
    print(
        "[orders] 模拟订单服务已启动：http://{}:{}（GET /health | GET /orders | POST /orders）".format(
            bound_host, bound_port
        )
    )
    print("[orders] Ctrl+C 停止。demo 命令会在后台自动起停本服务。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[orders] 收到中断，退出。")
    finally:
        server.server_close()
