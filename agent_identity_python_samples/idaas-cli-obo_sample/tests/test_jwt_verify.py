"""JWT/RS256 验签测试：测试内动态生成 RSA 密钥对（纯 Python Miller-Rabin）。

验签实现按模长自适应（k = n.bit_length()/8），测试用 512/1024 位密钥即可，
真实 JWKS 的 2048 位密钥走同一代码路径。覆盖 401 各分支与 kid 轮换刷新逻辑。
"""

import base64
import hashlib
import json
import os
import random
import sys
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orders.verify import (  # noqa: E402
    InvalidTokenError,
    JwksFetchError,
    JwksCache,
    TokenVerifier,
    decode_jwt_unverified,
    jwk_to_rsa,
    rsa_pkcs1v15_sha256_verify,
    scopes_from_claims,
)

DIGESTINFO = bytes.fromhex("3031300d060960864801650304020105000420")


# ---------------------------------------------------------------------------
# 纯 Python RSA 工具（仅测试用；sample 运行时不需要）
# ---------------------------------------------------------------------------


def _is_probable_prime(n: int, rng: random.Random, rounds: int = 24) -> bool:
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for _ in range(rounds):
        a = rng.randrange(2, n - 1)
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def _gen_prime(bits: int, rng: random.Random) -> int:
    while True:
        cand = rng.getrandbits(bits) | (1 << (bits - 1)) | 1
        if _is_probable_prime(cand, rng):
            return cand


def _modinv(a: int, m: int) -> int:
    """模逆元（扩展欧几里得）。"""
    def _egcd(a: int, b: int):
        if b == 0:
            return a, 1, 0
        g, x1, y1 = _egcd(b, a % b)
        return g, y1, x1 - (a // b) * y1

    g, x, _ = _egcd(a % m, m)
    if g != 1:
        raise ValueError("modular inverse does not exist")
    return x % m


def generate_rsa(bits: int = 1024, seed: int = 42):
    """生成测试用 RSA 密钥对：返回 (n, e, d)。"""
    rng = random.Random(seed)
    e = 65537
    while True:
        p = _gen_prime(bits // 2, rng)
        q = _gen_prime(bits // 2, rng)
        if p == q:
            continue
        n = p * q
        phi = (p - 1) * (q - 1)
        if phi % e == 0:
            continue
        d = _modinv(e, phi)
        return n, e, d


def rsa_sign_pkcs1v15_sha256(n: int, d: int, message: bytes) -> bytes:
    """测试用签名器：EMSA-PKCS1-v1_5 + SHA-256。"""
    k = (n.bit_length() + 7) // 8
    digest = hashlib.sha256(message).digest()
    digest_info = DIGESTINFO + digest
    ps = b"\xff" * (k - len(digest_info) - 3)
    em = b"\x00\x01" + ps + b"\x00" + digest_info
    m = int.from_bytes(em, "big")
    return pow(m, d, n).to_bytes(k, "big")


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def int_to_b64url(value: int) -> str:
    size = (value.bit_length() + 7) // 8
    return b64url(value.to_bytes(size, "big"))


def make_jwk(kid: str, n: int, e: int) -> dict:
    return {"kty": "RSA", "kid": kid, "n": int_to_b64url(n), "e": int_to_b64url(e), "alg": "RS256", "use": "sig"}


def make_jwt(n: int, d: int, kid: str, claims: dict, alg: str = "RS256") -> str:
    header = {"alg": alg, "kid": kid, "typ": "JWT"}
    signing_input = "{}.{}".format(
        b64url(json.dumps(header, separators=(",", ":")).encode()),
        b64url(json.dumps(claims, separators=(",", ":")).encode()),
    )
    signature = rsa_sign_pkcs1v15_sha256(n, d, signing_input.encode("ascii"))
    return "{}.{}".format(signing_input, b64url(signature))


# ---------------------------------------------------------------------------
# 测试
# ---------------------------------------------------------------------------


class TestRsaVerifyPrimitives(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.n, cls.e, cls.d = generate_rsa(bits=1024, seed=7)

    def test_sign_then_verify_ok(self):
        msg = b"hello world"
        sig = rsa_sign_pkcs1v15_sha256(self.n, self.d, msg)
        self.assertTrue(rsa_pkcs1v15_sha256_verify(self.n, self.e, sig, msg))

    def test_tampered_message_fails(self):
        sig = rsa_sign_pkcs1v15_sha256(self.n, self.d, b"hello world")
        self.assertFalse(rsa_pkcs1v15_sha256_verify(self.n, self.e, sig, b"hello world!"))

    def test_tampered_signature_fails(self):
        sig = bytearray(rsa_sign_pkcs1v15_sha256(self.n, self.d, b"msg"))
        sig[-1] ^= 0x01
        self.assertFalse(rsa_pkcs1v15_sha256_verify(self.n, self.e, bytes(sig), b"msg"))

    def test_wrong_signature_length_fails(self):
        sig = rsa_sign_pkcs1v15_sha256(self.n, self.d, b"msg")
        self.assertFalse(rsa_pkcs1v15_sha256_verify(self.n, self.e, sig[:-1], b"msg"))

    def test_signature_too_large_fails(self):
        # 签名整数 >= n 的病态输入（长度对齐但值越界）
        k = (self.n.bit_length() + 7) // 8
        bad = (self.n + 1).to_bytes(k + 1, "big")[-k:]
        self.assertFalse(rsa_pkcs1v15_sha256_verify(self.n, self.e, bad, b"msg"))

    def test_jwk_to_rsa_roundtrip(self):
        jwk = make_jwk("kid-1", self.n, self.e)
        n2, e2 = jwk_to_rsa(jwk)
        self.assertEqual((n2, e2), (self.n, self.e))

    def test_jwk_non_rsa_rejected(self):
        with self.assertRaises(InvalidTokenError):
            jwk_to_rsa({"kty": "EC", "kid": "k", "n": "AA", "e": "AQAB"})


class TestJwksCacheKidRotation(unittest.TestCase):
    def test_unknown_kid_triggers_single_refresh(self):
        key1 = make_jwk("kid-a", *generate_rsa(bits=512, seed=1)[:2])
        key2 = make_jwk("kid-b", *generate_rsa(bits=512, seed=2)[:2])
        state = {"keys": [key1], "fetches": 0}

        def fetch(_uri):
            state["fetches"] += 1
            return {"keys": list(state["keys"])}

        cache = JwksCache("https://jwks.example/keys", fetch_func=fetch)
        # 命中 kid-a：1 次拉取
        self.assertIsNotNone(cache.get_key("kid-a"))
        self.assertEqual(state["fetches"], 1)
        # 再次命中：缓存内不再拉取
        self.assertIsNotNone(cache.get_key("kid-a"))
        self.assertEqual(state["fetches"], 1)
        # kid-b 未命中 → 强制刷新一次（服务端密钥刚轮换）
        self.assertIsNone(cache.get_key("kid-b"))
        self.assertEqual(state["fetches"], 2)
        # 服务端轮换完成后 kid-b 可见
        state["keys"].append(key2)
        self.assertIsNotNone(cache.get_key("kid-b"))
        self.assertEqual(state["fetches"], 3)

    def test_fetch_failure_raises_jwks_fetch_error(self):
        def fetch(_uri):
            raise JwksFetchError("upstream down")

        cache = JwksCache("https://jwks.example/keys", fetch_func=fetch)
        with self.assertRaises(JwksFetchError):
            cache.get_key("kid-a")


class TestTokenVerifierBranches(unittest.TestCase):
    """正例与各 401 分支（篡改/错 kid/过期/错 aud/错 iss/错 alg/坏格式）+ 503 分支。"""

    ISSUER = "https://eiam.example.com/api/v2/iauths_system/oauth2"
    AUDIENCE = "agent-demo-orders-app"
    KID = "test-key-1"

    @classmethod
    def setUpClass(cls):
        cls.n, cls.e, cls.d = generate_rsa(bits=1024, seed=99)
        cls.jwks = {"keys": [make_jwk(cls.KID, cls.n, cls.e)]}

    def make_verifier(self, fetch_func=None):
        fetch = fetch_func or (lambda _uri: self.jwks)
        return TokenVerifier(
            issuer=self.ISSUER, audience=self.AUDIENCE,
            jwks_uri="https://jwks.example/keys", fetch_func=fetch,
        )

    def base_claims(self, **overrides):
        now = int(time.time())
        claims = {
            "iss": self.ISSUER,
            "aud": self.AUDIENCE,
            "sub": "user_xxxxxxxx0001",
            "scope": "read write.all",
            "exp": now + 600,
            "iat": now,
        }
        claims.update(overrides)
        return claims

    def test_happy_path(self):
        token = make_jwt(self.n, self.d, self.KID, self.base_claims())
        claims = self.make_verifier().verify(token)
        self.assertEqual(claims["sub"], "user_xxxxxxxx0001")

    def test_exp_leeway_tolerance(self):
        # exp 已过 30s 但在 60s 容忍窗口内 → 通过
        token = make_jwt(self.n, self.d, self.KID, self.base_claims(exp=int(time.time()) - 30))
        claims = self.make_verifier().verify(token)
        self.assertIn("sub", claims)

    def test_expired_token_rejected(self):
        token = make_jwt(self.n, self.d, self.KID, self.base_claims(exp=int(time.time()) - 3600))
        with self.assertRaises(InvalidTokenError) as ctx:
            self.make_verifier().verify(token)
        self.assertIn("过期", str(ctx.exception))

    def test_tampered_signature_rejected(self):
        token = make_jwt(self.n, self.d, self.KID, self.base_claims())
        head_payload, sig = token.rsplit(".", 1)
        sig_bytes = bytearray(base64.urlsafe_b64decode(sig + "=" * (-len(sig) % 4)))
        sig_bytes[0] ^= 0xFF
        tampered = "{}.{}".format(head_payload, b64url(bytes(sig_bytes)))
        with self.assertRaises(InvalidTokenError) as ctx:
            self.make_verifier().verify(tampered)
        self.assertIn("签名", str(ctx.exception))

    def test_wrong_kid_rejected(self):
        token = make_jwt(self.n, self.d, "kid-not-in-jwks", self.base_claims())
        with self.assertRaises(InvalidTokenError) as ctx:
            self.make_verifier().verify(token)
        self.assertIn("kid", str(ctx.exception))

    def test_wrong_audience_rejected(self):
        token = make_jwt(self.n, self.d, self.KID, self.base_claims(aud="agent-other-app"))
        with self.assertRaises(InvalidTokenError) as ctx:
            self.make_verifier().verify(token)
        self.assertIn("aud", str(ctx.exception))

    def test_audience_list_accepted(self):
        token = make_jwt(self.n, self.d, self.KID, self.base_claims(aud=[self.AUDIENCE, "extra"]))
        claims = self.make_verifier().verify(token)
        self.assertEqual(claims["aud"][0], self.AUDIENCE)

    def test_wrong_issuer_rejected(self):
        token = make_jwt(self.n, self.d, self.KID, self.base_claims(iss="https://other.example.com"))
        with self.assertRaises(InvalidTokenError) as ctx:
            self.make_verifier().verify(token)
        self.assertIn("iss", str(ctx.exception))

    def test_wrong_alg_rejected(self):
        token = make_jwt(self.n, self.d, self.KID, self.base_claims(), alg="HS256")
        with self.assertRaises(InvalidTokenError) as ctx:
            self.make_verifier().verify(token)
        self.assertIn("RS256", str(ctx.exception))

    def test_malformed_token_rejected(self):
        verifier = self.make_verifier()
        for bad in ("", "abc", "a.b", "a.b.c.d.e", "...."):
            with self.assertRaises(InvalidTokenError):
                verifier.verify(bad)

    def test_missing_exp_rejected(self):
        claims = self.base_claims()
        claims.pop("exp")
        token = make_jwt(self.n, self.d, self.KID, claims)
        with self.assertRaises(InvalidTokenError) as ctx:
            self.make_verifier().verify(token)
        self.assertIn("exp", str(ctx.exception))

    def test_jwks_fetch_failure_maps_to_503_class(self):
        token = make_jwt(self.n, self.d, self.KID, self.base_claims())

        def fetch(_uri):
            raise JwksFetchError("connection refused")

        verifier = self.make_verifier(fetch_func=fetch)
        with self.assertRaises(JwksFetchError):
            verifier.verify(token)

    def test_decode_jwt_unverified_parts(self):
        token = make_jwt(self.n, self.d, self.KID, self.base_claims())
        header, payload, signing_input, signature = decode_jwt_unverified(token)
        self.assertEqual(header["kid"], self.KID)
        self.assertEqual(payload["sub"], "user_xxxxxxxx0001")
        self.assertEqual(signing_input.decode(), token.rsplit(".", 1)[0])
        self.assertTrue(signature)


class TestScopeParsing(unittest.TestCase):
    def test_string_scope(self):
        self.assertEqual(scopes_from_claims({"scope": "read write.all"}), ["read", "write.all"])

    def test_list_scope(self):
        self.assertEqual(scopes_from_claims({"scope": ["read", "write.all"]}), ["read", "write.all"])

    def test_missing_scope(self):
        self.assertEqual(scopes_from_claims({}), [])


class TestDefaultFetchJwksSslContext(unittest.TestCase):
    """缺陷修复：默认 JWKS 拉取须复用 lib.rpc 的共享 SSL 上下文（certifi 兜底）。

    部分 Python 环境（如 macOS Python 3.12 无系统 CA）下
    ssl.create_default_context() 不含任何受信 CA，直接用会导致 JWKS 拉取全部
    CERTIFICATE_VERIFY_FAILED → 验签 503。
    """

    def _capture_urlopen_context(self):
        captured = {}

        class _FakeResp:
            """最小响应对象：read() 返回真实 bytes（decode/json.loads 可用）。"""

            def __init__(self, payload: bytes):
                self._payload = payload

            def read(self):
                return self._payload

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        fake_resp = _FakeResp(json.dumps({"keys": []}).encode("utf-8"))

        def fake_urlopen(req, timeout=None, context=None):
            captured["context"] = context
            return fake_resp

        return captured, fake_urlopen

    def test_uses_shared_ssl_context_from_lib_rpc(self):
        import ssl

        from orders import verify as verify_mod

        sentinel_ctx = ssl.create_default_context()  # 仅作标识对象
        captured, fake_urlopen = self._capture_urlopen_context()
        with mock.patch.object(verify_mod, "_shared_ssl_context", lambda: sentinel_ctx), \
                mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            doc = verify_mod.default_fetch_jwks("https://jwks.example/keys")
        self.assertEqual(doc, {"keys": []})
        self.assertIs(captured["context"], sentinel_ctx)

    def test_falls_back_to_default_context_when_lib_missing(self):
        from orders import verify as verify_mod

        captured, fake_urlopen = self._capture_urlopen_context()
        with mock.patch.object(verify_mod, "_shared_ssl_context", None), \
                mock.patch.object(verify_mod.ssl, "create_default_context", return_value="DEFAULT_CTX"), \
                mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            verify_mod.default_fetch_jwks("https://jwks.example/keys")
        self.assertEqual(captured["context"], "DEFAULT_CTX")

    def test_non_https_uri_rejected_before_network(self):
        from orders import verify as verify_mod

        with self.assertRaises(InvalidTokenError):
            verify_mod.default_fetch_jwks("http://jwks.example/keys")


if __name__ == "__main__":
    unittest.main()
