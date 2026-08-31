"""订单服务令牌验签：JWKS 拉取（内存缓存 300s）+ 纯标准库 RS256 验签。

安全提示：纯标准库验签（``pow(sig, e, n)`` + EMSA-PKCS1-v1_5 结构校验）为本
sample 的教学实现，兼容任意位数的 RSA 密钥（含真实 2048 位）；**生产环境建议
使用 PyJWT + cryptography**（常量时间实现、更完整的 JOSE 校验）。

校验项：RS256 签名、iss、aud、exp（留 60s 时钟偏移容忍）。
错误映射（供 HTTP 层转换为状态码）：
- ``InvalidTokenError`` → 401 ``{"error": "invalid_token", ...}``（不回显令牌）；
- ``JwksFetchError``  → 503（JWKS 源不可达属服务端依赖故障，不是客户端的错）。
"""

import base64
import hashlib
import json
import ssl
import threading
import time
import urllib.request
from typing import Any, Callable, Dict, Optional

try:
    # 复用 lib/rpc.py 的共享 SSL 上下文（含 certifi 兜底）：部分环境（如 macOS
    # Python 3.12 无系统 CA）下 ssl.create_default_context() 不含任何受信 CA，
    # 直接用会导致 JWKS 拉取全部 CERTIFICATE_VERIFY_FAILED → 验签 503。
    # orders/ 被单独拷走部署（无 lib 包）时回退到默认上下文。
    from lib.rpc import ssl_context as _shared_ssl_context
except ImportError:  # pragma: no cover - orders 独立部署场景
    _shared_ssl_context = None

# SHA-256 DigestInfo DER 前缀（EMSA-PKCS1-v1_5 编码用）
SHA256_DIGESTINFO_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")

# exp 时钟偏移容忍（秒）
CLOCK_SKEW_SECONDS = 60

# JWKS 内存缓存有效期（秒）
JWKS_CACHE_TTL = 300


class InvalidTokenError(Exception):
    """令牌无效（签名/格式/过期/受众/签发方不符）→ HTTP 401。"""

    def __init__(self, description: str):
        super().__init__(description)
        self.description = description


class JwksFetchError(Exception):
    """JWKS 端点拉取失败 → HTTP 503。"""


def _b64url_decode(data: str) -> bytes:
    """base64url 解码（补齐 padding）。"""
    if not isinstance(data, str):
        raise InvalidTokenError("令牌段不是字符串")
    padded = data + "=" * (-len(data) % 4)
    try:
        return base64.urlsafe_b64decode(padded.encode("ascii"))
    except Exception as exc:
        raise InvalidTokenError("base64url 解码失败：{}".format(exc)) from None


def default_fetch_jwks(jwks_uri: str, timeout: int = 10) -> Dict[str, Any]:
    """默认 JWKS 拉取：urllib GET（verify 开启，共享 SSL 上下文含 certifi 兜底）。

    测试可注入 fetch_func 替换。
    """
    if not jwks_uri or not jwks_uri.startswith("https://"):
        # 401 类配置问题（未配置 JWKS 地址）不视为服务端故障
        raise InvalidTokenError("ORDER_SERVICE_JWKS_URI 未配置或不是 https 地址")
    if _shared_ssl_context is not None:
        context = _shared_ssl_context()
    else:  # pragma: no cover - orders 独立部署场景
        context = ssl.create_default_context()
    try:
        req = urllib.request.Request(
            jwks_uri, headers={"accept": "application/json"}, method="GET"
        )
        with urllib.request.urlopen(req, timeout=timeout, context=context) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except InvalidTokenError:
        raise
    except Exception as exc:
        raise JwksFetchError("拉取 JWKS 失败（{}）：{}".format(jwks_uri, exc)) from None


class JwksCache:
    """JWKS 内存缓存：TTL 300s；kid 未命中时强制刷新一次（处理密钥轮换）。

    并发安全：ThreadingHTTPServer 下多个请求线程可能在冷启动/密钥轮换后
    同时未命中同一 kid——无锁会并发重复拉取 JWKS（惊群）。get_key/clear
    全程持锁串行化，未命中路径同一时刻只有一个线程在拉取。
    """

    def __init__(
        self,
        jwks_uri: str,
        fetch_func: Optional[Callable[[str], Dict[str, Any]]] = None,
        ttl: int = JWKS_CACHE_TTL,
    ):
        self.jwks_uri = jwks_uri
        self._fetch = fetch_func or default_fetch_jwks
        self._ttl = ttl
        self._keys: Dict[str, Dict[str, Any]] = {}
        self._loaded_at = 0.0
        self._lock = threading.Lock()

    def _load(self) -> None:
        doc = self._fetch(self.jwks_uri)
        keys = doc.get("keys") if isinstance(doc, dict) else None
        if not isinstance(keys, list):
            raise JwksFetchError("JWKS 响应缺少 keys 数组")
        self._keys = {}
        for key in keys:
            if isinstance(key, dict) and key.get("kid"):
                self._keys[str(key["kid"])] = key
        self._loaded_at = time.time()

    def get_key(self, kid: str) -> Optional[Dict[str, Any]]:
        """取 kid 对应公钥：缓存命中且未过期直接返回；未命中/过期强制刷新一次。"""
        with self._lock:
            fresh = (time.time() - self._loaded_at) < self._ttl
            if self._keys and fresh and kid in self._keys:
                return self._keys[kid]
            # 未命中：强制刷新（密钥可能刚轮换），仍无则返回 None
            self._load()
            return self._keys.get(kid)

    def clear(self) -> None:
        with self._lock:
            self._keys = {}
            self._loaded_at = 0.0


def rsa_pkcs1v15_sha256_verify(n: int, e: int, signature: bytes, message: bytes) -> bool:
    """RS256（RSASSA-PKCS1-v1_5 + SHA-256）验签，纯整数运算，任意模长兼容。

    EM 结构：00 01 FF..FF 00 || DigestInfo(SHA-256) || SHA-256(message)
    """
    k = (n.bit_length() + 7) // 8
    if len(signature) != k or k < 64:
        return False
    s = int.from_bytes(signature, "big")
    if s <= 0 or s >= n:
        return False
    m = pow(s, e, n)
    em = m.to_bytes(k, "big")
    if em[0] != 0x00 or em[1] != 0x01:
        return False
    idx = 2
    while idx < len(em) and em[idx] == 0xFF:
        idx += 1
    # PS（0xFF 串）至少 8 字节，且必须以 0x00 分隔符结尾
    if idx - 2 < 8 or idx >= len(em) or em[idx] != 0x00:
        return False
    digest_info = em[idx + 1:]
    expected = SHA256_DIGESTINFO_PREFIX + hashlib.sha256(message).digest()
    return digest_info == expected


def jwk_to_rsa(key: Dict[str, Any]) -> tuple:
    """JWK（RSA 类型）→ (n, e) 整数对。"""
    if key.get("kty") != "RSA":
        raise InvalidTokenError("JWKS 公钥不是 RSA 类型（kty={}）".format(key.get("kty")))
    try:
        n = int.from_bytes(_b64url_decode(key["n"]), "big")
        e = int.from_bytes(_b64url_decode(key["e"]), "big")
    except KeyError as exc:
        raise InvalidTokenError("JWKS 公钥缺少 {} 字段".format(exc)) from None
    if n <= 0 or e <= 0:
        raise InvalidTokenError("JWKS 公钥 n/e 非法")
    return n, e


def decode_jwt_unverified(token: str) -> tuple:
    """JWT → (header, payload, signing_input, signature)。

    仅做结构拆分与 JSON 解码（不做签名校验）；格式非法抛 InvalidTokenError。
    """
    if not isinstance(token, str):
        raise InvalidTokenError("令牌不是字符串")
    parts = token.split(".")
    if len(parts) != 3 or not all(parts):
        raise InvalidTokenError("令牌不是合法 JWT（三段结构）")
    try:
        header = json.loads(_b64url_decode(parts[0]).decode("utf-8"))
        payload = json.loads(_b64url_decode(parts[1]).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise InvalidTokenError("JWT header/payload 不是合法 JSON") from None
    if not isinstance(header, dict) or not isinstance(payload, dict):
        raise InvalidTokenError("JWT header/payload 结构非法")
    signing_input = "{}.{}".format(parts[0], parts[1]).encode("ascii")
    signature = _b64url_decode(parts[2])
    return header, payload, signing_input, signature


class TokenVerifier:
    """订单服务 Bearer 令牌校验器（iss/aud/exp + RS256 签名）。"""

    def __init__(
        self,
        issuer: str,
        audience: str,
        jwks_uri: str,
        fetch_func: Optional[Callable[[str], Dict[str, Any]]] = None,
        leeway: int = CLOCK_SKEW_SECONDS,
    ):
        self.issuer = issuer
        self.audience = audience
        self.jwks = JwksCache(jwks_uri, fetch_func=fetch_func)
        self.leeway = leeway

    def verify(self, token: str) -> Dict[str, Any]:
        """验签并校验 claims。全部通过返回 payload（claims dict）。"""
        header, payload, signing_input, signature = decode_jwt_unverified(token)

        if header.get("alg") != "RS256":
            raise InvalidTokenError("仅支持 RS256 签名算法（alg={}）".format(header.get("alg")))

        kid = header.get("kid")
        if not kid:
            raise InvalidTokenError("JWT header 缺少 kid")
        key = self.jwks.get_key(kid)
        if key is None:
            raise InvalidTokenError("JWKS 中不存在 kid={!r} 的公钥（刷新后仍未命中）".format(kid))

        n, e = jwk_to_rsa(key)
        if not rsa_pkcs1v15_sha256_verify(n, e, signature, signing_input):
            raise InvalidTokenError("RS256 签名校验失败")

        # exp（留时钟偏移容忍）
        exp = payload.get("exp")
        if not isinstance(exp, (int, float)):
            raise InvalidTokenError("令牌缺少 exp claim")
        if exp + self.leeway < time.time():
            raise InvalidTokenError("令牌已过期（exp={}）".format(int(exp)))

        # iss / aud
        if self.issuer:
            if payload.get("iss") != self.issuer:
                raise InvalidTokenError(
                    "iss 不符：期望 {}，实际 {}".format(self.issuer, payload.get("iss"))
                )
        if self.audience:
            aud = payload.get("aud")
            aud_list = aud if isinstance(aud, list) else [aud]
            if self.audience not in aud_list:
                raise InvalidTokenError("aud 不符：期望 {}，实际 {}".format(self.audience, aud))
        return payload


def scopes_from_claims(claims: Dict[str, Any]) -> list:
    """从 claims 提取 scope 列表（兼容空格分隔字符串与数组两种形态）。"""
    scope = claims.get("scope", [])
    if isinstance(scope, list):
        return [str(s) for s in scope]
    if isinstance(scope, str):
        return scope.split()
    return []
