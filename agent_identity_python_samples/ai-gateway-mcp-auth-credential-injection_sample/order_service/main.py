"""
order-service-oauth: 带 OAuth2 授权的订单服务（单文件，内存存储）

⚠️ 仅限测试用途，请勿直接暴露公网！
本示例服务使用固定测试凭据与内存存储，无生产级安全防护，
仅用于演示 AI 网关凭据注入流程，测试完成后请及时释放。

启动:
    uvicorn main:app --port 8001

环境变量（部署到 ECS 等远程场景时配置）:
    OAUTH_BASE_URL   — 对外可访问的地址，如 http://1.2.3.4:8001
                        不设置则从请求中自动推断（本地开发）
    CLIENT_ID        — OAuth client_id，默认 order-client
    CLIENT_SECRET    — OAuth client_secret，默认 order-secret
    PORT             — 监听端口，默认 8001
    ALLOWED_REDIRECT_PREFIXES — redirect_uri 白名单前缀（逗号分隔），
                        默认含 Agent Identity 数据面回调与本地调试地址

OAuth 流程:
    1. 浏览器打开 /oauth/authorize 页面，点击授权
    2. 回调时拿到 code，POST /oauth/token 换 access_token
    3. 用 Bearer token 访问订单 API
"""

import html
import os
import secrets
import sys
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional
from urllib.parse import urlencode

from fastapi import Depends, FastAPI, Form, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Order Service with OAuth", version="1.0.0")

# ══════════════════════════════════════════════════════════════════════
#  配置（环境变量 → 默认值）
# ══════════════════════════════════════════════════════════════════════

# 对外可访问的 base URL（ECS 部署时设为公网域名，如 https://orders.example.com）
# 不设置则从请求 header 自动推断（本地开发场景）
OAUTH_BASE_URL: Optional[str] = os.getenv("OAUTH_BASE_URL") or None

CLIENT_ID = os.getenv("CLIENT_ID", "order-client")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "order-secret")
PORT = int(os.getenv("PORT", "8001"))

TOKEN_EXPIRES_IN = 3600           # 1 小时
REFRESH_TOKEN_EXPIRES_IN = 86400  # 24 小时
CODE_EXPIRES_IN = 300             # 5 分钟

# redirect_uri 前缀白名单（防开放重定向）：
# 默认允许 Agent Identity 数据面回调地址与本地调试地址，
# 其他合法回调可通过环境变量 ALLOWED_REDIRECT_PREFIXES（逗号分隔的 URL 前缀）配置。
_DEFAULT_REDIRECT_PREFIXES = (
    "https://agentidentitydata.cn-beijing.aliyuncs.com/oauth2/callback/,"
    "http://localhost:,http://127.0.0.1:"
)
ALLOWED_REDIRECT_PREFIXES = [
    p.strip()
    for p in os.getenv("ALLOWED_REDIRECT_PREFIXES", _DEFAULT_REDIRECT_PREFIXES).split(",")
    if p.strip()
]
# OAUTH_BASE_URL 是部署方设置的可信配置，允许回跳到服务自身（首页快速开始流程用）
if OAUTH_BASE_URL:
    ALLOWED_REDIRECT_PREFIXES.append(OAUTH_BASE_URL.rstrip("/") + "/")


def _validate_redirect_uri(redirect_uri: str) -> None:
    """校验 redirect_uri 命中白名单前缀，防止开放重定向。不匹配时返回 400，不做跳转。"""
    if not any(redirect_uri.startswith(p) for p in ALLOWED_REDIRECT_PREFIXES):
        raise HTTPException(
            400,
            "Invalid redirect_uri: not in the allowed list. "
            "Set ALLOWED_REDIRECT_PREFIXES (comma-separated URL prefixes) to allow it.",
        )


@app.on_event("startup")
def log_config():
    print(f"=== Order Service Config ===")
    print(f"  OAUTH_BASE_URL: {OAUTH_BASE_URL or '(auto-detect from request)'}")
    print(f"  CLIENT_ID:      {CLIENT_ID}")
    print(f"  PORT:           {PORT}")
    print(f"============================")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件：打印所有请求的 method、path、全部 headers。"""
    path = request.url.path
    # 跳过 favicon 和健康检查噪音
    if path in ("/favicon.ico",):
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"

    print(f"\n>>> {request.method} {path}", flush=True)
    print(f"    client_ip: {client_ip}", flush=True)
    print(f"    --- all headers ---", flush=True)
    for name, value in request.headers.items():
        # 对 authorization 做脱敏，只显示前 20 字符
        if name.lower() == "authorization" and len(value) > 20:
            value = value[:20] + "..."
        print(f"    {name}: {value}", flush=True)
    print(f"    --- end headers ---", flush=True)

    response = await call_next(request)

    print(f"    << status: {response.status_code}", flush=True)

    return response


def _base_url(request: Request) -> str:
    """获取对外可访问的 base URL。优先用环境变量，否则从请求推断。"""
    if OAUTH_BASE_URL:
        return OAUTH_BASE_URL.rstrip("/")
    return str(request.base_url).rstrip("/")


# ══════════════════════════════════════════════════════════════════════
#  内存存储
# ══════════════════════════════════════════════════════════════════════

orders: dict[str, dict] = {}
auth_codes: dict[str, dict] = {}
access_tokens: dict[str, dict] = {}
refresh_tokens: dict[str, dict] = {}


# ══════════════════════════════════════════════════════════════════════
#  OAuth2 授权服务器
# ══════════════════════════════════════════════════════════════════════


@app.get("/.well-known/oauth-authorization-server", tags=["OAuth"])
def authorization_server_metadata(request: Request):
    """RFC 8414 授权服务器元数据。"""
    base = _base_url(request)
    return {
        "issuer": base,
        "authorization_endpoint": f"{base}/oauth/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["client_secret_post"],
        "scopes_supported": ["orders:read", "orders:write"],
    }


@app.get("/oauth/authorize", tags=["OAuth"])
def authorize_page(
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    response_type: str = Query("code"),
    scope: str = Query("orders:read orders:write"),
    state: str = Query(""),
):
    """展示授权页面（简单 HTML）。"""
    if client_id != CLIENT_ID:
        raise HTTPException(400, "Invalid client_id")
    if response_type != "code":
        raise HTTPException(400, "Only response_type=code is supported")
    _validate_redirect_uri(redirect_uri)

    # 用户可控参数插入 HTML 前统一转义，防反射型 XSS
    client_id = html.escape(client_id)
    redirect_uri = html.escape(redirect_uri)
    scope = html.escape(scope)
    state = html.escape(state)

    page = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>授权</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; display: flex;
               justify-content: center; align-items: center; min-height: 100vh;
               margin: 0; background: #f5f5f5; }}
        .card {{ background: white; padding: 2rem; border-radius: 12px;
                 box-shadow: 0 2px 12px rgba(0,0,0,0.1); max-width: 400px; width: 100%; }}
        h2 {{ margin-top: 0; }}
        .scope {{ background: #f0f0f0; padding: 0.5rem 1rem; border-radius: 6px;
                  margin: 0.5rem 0; font-size: 0.9rem; }}
        button {{ width: 100%; padding: 0.8rem; border: none; border-radius: 8px;
                  font-size: 1rem; cursor: pointer; margin-top: 0.5rem; }}
        .approve {{ background: #0066ff; color: white; }}
        .deny {{ background: #eee; color: #666; }}
    </style></head>
    <body><div class="card">
        <h2>🔐 应用授权</h2>
        <p><strong>{client_id}</strong> 请求以下权限：</p>
        <div class="scope">📖 orders:read — 读取订单</div>
        <div class="scope">✏️ orders:write — 创建/修改订单</div>
        <form method="post" action="/oauth/authorize">
            <input type="hidden" name="client_id" value="{client_id}">
            <input type="hidden" name="redirect_uri" value="{redirect_uri}">
            <input type="hidden" name="scope" value="{scope}">
            <input type="hidden" name="state" value="{state}">
            <button type="submit" name="action" value="approve" class="approve">授权</button>
            <button type="submit" name="action" value="deny" class="deny">拒绝</button>
        </form>
    </div></body></html>
    """
    return HTMLResponse(page)


@app.post("/oauth/authorize", tags=["OAuth"])
async def authorize_post(request: Request):
    form = await request.form()
    client_id = form.get("client_id", "")
    redirect_uri = form.get("redirect_uri", "")
    scope = form.get("scope", "orders:read orders:write")
    state = form.get("state", "")
    action = form.get("action", "")

    # 跳转前校验 redirect_uri 白名单，防止开放重定向
    _validate_redirect_uri(redirect_uri)

    if action == "deny":
        params = {"error": "access_denied", "error_description": "User denied"}
        if state:
            params["state"] = state
        return RedirectResponse(f"{redirect_uri}?{urlencode(params)}", status_code=302)

    # 生成授权码
    code = secrets.token_urlsafe(32)
    auth_codes[code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "expires_at": time.time() + CODE_EXPIRES_IN,
    }

    params = {"code": code}
    if state:
        params["state"] = state
    return RedirectResponse(f"{redirect_uri}?{urlencode(params)}", status_code=302)


@app.post("/oauth/token", tags=["OAuth"])
async def token(request: Request):
    """换取 access_token（支持 authorization_code 和 refresh_token）。"""
    form = await request.form()
    grant_type = form.get("grant_type", "authorization_code")
    code = form.get("code")
    redirect_uri = form.get("redirect_uri")
    client_id = form.get("client_id")
    client_secret = form.get("client_secret")
    refresh_tok = form.get("refresh_token")

    # 验证 client 凭据
    if client_id != CLIENT_ID or client_secret != CLIENT_SECRET:
        raise HTTPException(401, "Invalid client credentials")

    if grant_type == "authorization_code":
        if not code or code not in auth_codes:
            raise HTTPException(400, "Invalid or expired authorization code")

        auth = auth_codes.pop(code)  # 一次性使用
        if auth["expires_at"] < time.time():
            raise HTTPException(400, "Authorization code expired")

        # 生成 token
        at = secrets.token_urlsafe(32)
        rt = secrets.token_urlsafe(32)
        access_tokens[at] = {
            "scope": auth["scope"],
            "expires_at": time.time() + TOKEN_EXPIRES_IN,
        }
        refresh_tokens[rt] = {
            "scope": auth["scope"],
        }

        return {
            "access_token": at,
            "token_type": "Bearer",
            "expires_in": TOKEN_EXPIRES_IN,
            "refresh_token": rt,
            "scope": auth["scope"],
        }

    elif grant_type == "refresh_token":
        if not refresh_tok or refresh_tok not in refresh_tokens:
            raise HTTPException(400, "Invalid refresh token")

        old = refresh_tokens.pop(refresh_tok)  # 轮换

        at = secrets.token_urlsafe(32)
        rt = secrets.token_urlsafe(32)
        access_tokens[at] = {
            "scope": old["scope"],
            "expires_at": time.time() + TOKEN_EXPIRES_IN,
        }
        refresh_tokens[rt] = {"scope": old["scope"]}

        return {
            "access_token": at,
            "token_type": "Bearer",
            "expires_in": TOKEN_EXPIRES_IN,
            "refresh_token": rt,
            "scope": old["scope"],
        }

    else:
        raise HTTPException(400, f"Unsupported grant_type: {grant_type}")


# ══════════════════════════════════════════════════════════════════════
#  Token 校验
# ══════════════════════════════════════════════════════════════════════


def verify_token(authorization: str = Header("")) -> dict:
    """从 Authorization header 中提取并校验 Bearer token。"""
    print(f"    [verify_token] authorization value: '{authorization[:60]}{'...' if len(authorization) > 60 else ''}' (len={len(authorization)})", flush=True)

    if not authorization.startswith("Bearer "):
        print(f"    [verify_token] REJECT: does not start with 'Bearer '", flush=True)
        raise HTTPException(401, "Missing or invalid Authorization header")

    token = authorization[7:]
    info = access_tokens.get(token)
    if not info:
        print(f"    [verify_token] REJECT: token not found in store (token={token[:16]}...)", flush=True)
        raise HTTPException(401, "Invalid token")
    if info["expires_at"] < time.time():
        access_tokens.pop(token, None)
        print(f"    [verify_token] REJECT: token expired", flush=True)
        raise HTTPException(401, "Token expired")

    print(f"    [verify_token] OK: scope={info.get('scope')}", flush=True)
    return info


# ══════════════════════════════════════════════════════════════════════
#  订单 API（需要 Bearer token）
# ══════════════════════════════════════════════════════════════════════


class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class OrderItemIn(BaseModel):
    name: str = Field(..., description="商品名称")
    quantity: int = Field(..., gt=0, description="数量")
    unit_price: float = Field(..., gt=0, description="单价")


class OrderCreate(BaseModel):
    customer_name: str = Field(..., description="客户姓名")
    items: list[OrderItemIn] = Field(..., min_length=1, description="订单明细")


def _make_order(data: OrderCreate) -> dict:
    items = [
        {"name": i.name, "quantity": i.quantity, "unit_price": i.unit_price}
        for i in data.items
    ]
    total = sum(i["quantity"] * i["unit_price"] for i in items)
    now = datetime.now().isoformat()
    return {
        "id": uuid.uuid4().hex[:8],
        "customer_name": data.customer_name,
        "status": OrderStatus.PENDING.value,
        "items": items,
        "total_amount": round(total, 2),
        "created_at": now,
        "updated_at": now,
    }


@app.post("/orders", status_code=201, tags=["Orders"])
def create_order(body: OrderCreate, info: dict = Depends(verify_token)):
    """创建订单（需要 orders:write 权限）"""
    if "orders:write" not in info.get("scope", ""):
        raise HTTPException(403, "Insufficient scope: orders:write required")
    order = _make_order(body)
    orders[order["id"]] = order
    return order


@app.get("/orders", tags=["Orders"])
def list_orders(
    customer_name: Optional[str] = Query(None),
    status: Optional[OrderStatus] = Query(None),
    info: dict = Depends(verify_token),
):
    """列出订单"""
    if "orders:read" not in info.get("scope", ""):
        raise HTTPException(403, "Insufficient scope: orders:read required")
    result = list(orders.values())
    if customer_name:
        result = [o for o in result if o["customer_name"] == customer_name]
    if status:
        result = [o for o in result if o["status"] == status.value]
    return result


@app.get("/orders/{order_id}", tags=["Orders"])
def get_order(order_id: str, info: dict = Depends(verify_token)):
    """查询单个订单"""
    if "orders:read" not in info.get("scope", ""):
        raise HTTPException(403, "Insufficient scope: orders:read required")
    order = orders.get(order_id)
    if not order:
        raise HTTPException(404, f"Order {order_id} not found")
    return order


@app.delete("/orders/{order_id}", status_code=204, tags=["Orders"])
def delete_order(order_id: str, info: dict = Depends(verify_token)):
    """删除订单（需要 orders:write 权限）"""
    if "orders:write" not in info.get("scope", ""):
        raise HTTPException(403, "Insufficient scope: orders:write required")
    if order_id not in orders:
        raise HTTPException(404, f"Order {order_id} not found")
    del orders[order_id]


# ══════════════════════════════════════════════════════════════════════
#  便捷入口
# ══════════════════════════════════════════════════════════════════════


@app.get("/", tags=["Meta"])
def index(request: Request):
    """首页：展示快速测试链接。"""
    base = _base_url(request)
    auth_url = (
        f"{base}/oauth/authorize?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={base}/docs&"  # 授权后跳到 Swagger 文档页
        f"response_type=code&"
        f"scope=orders:read+orders:write&"
        f"state=test123"
    )
    # base 可能来自请求 Host 推断，插入 HTML 前转义
    base = html.escape(base)
    auth_url = html.escape(auth_url)
    page = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>Order Service</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; max-width: 600px;
               margin: 2rem auto; padding: 0 1rem; }}
        a {{ color: #0066ff; }}
        code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 4px; }}
    </style></head>
    <body>
        <h1>📦 Order Service with OAuth</h1>
        <p>一个简单的带 OAuth2 授权的订单管理服务。</p>
        <h3>快速开始</h3>
        <ol>
            <li><a href="{auth_url}">点击这里完成 OAuth 授权</a>（会跳转到 Swagger 文档页）</li>
            <li>从浏览器地址栏复制 <code>code</code> 参数</li>
            <li>用 Swagger 文档页的 <code>POST /oauth/token</code> 换取 access_token</li>
            <li>复制 access_token，在 Swagger 里点 "Authorize" 填入，然后测试 API</li>
        </ol>
        <h3>凭据</h3>
        <p>client_id: <code>{CLIENT_ID}</code></p>
        <h3>链接</h3>
        <ul>
            <li><a href="{base}/docs">Swagger 文档</a></li>
            <li><a href="{base}/.well-known/oauth-authorization-server">OAuth 元数据</a></li>
        </ul>
    </body></html>
    """
    return HTMLResponse(page)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
