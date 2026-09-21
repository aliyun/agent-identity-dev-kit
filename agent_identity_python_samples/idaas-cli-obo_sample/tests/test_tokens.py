"""tokens 模块测试：0600 落盘 / 原子写 / 过期检测分支与「重跑哪一步」文案。"""

import json
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import tokens as tokens_mod  # noqa: E402


def make_jwt(claims: dict) -> str:
    """构造无需验签的三段式 JWT（仅用于 exp 判断）。"""
    import base64

    def b64(part: dict) -> str:
        return base64.urlsafe_b64encode(
            json.dumps(part, separators=(",", ":")).encode()
        ).rstrip(b"=").decode()

    return "{}.{}.{}".format(b64({"alg": "RS256", "kid": "k"}), b64(claims), "c2lnbmF0dXJl")


def make_jwt_raw_payload(payload_json: str) -> str:
    """构造 payload 段为任意 JSON 文本的 JWT（用于非 dict payload 测试）。"""
    import base64

    header = base64.urlsafe_b64encode(b'{"alg":"RS256"}').rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(payload_json.encode()).rstrip(b"=").decode()
    return "{}.{}.sig".format(header, payload)


class TokensDirTestCase(unittest.TestCase):
    """基类：把 .tokens/ 目录重定向到临时目录。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._original_dir = tokens_mod.TOKENS_DIR
        tokens_mod.TOKENS_DIR = self._tmp.name

    def tearDown(self):
        tokens_mod.TOKENS_DIR = self._original_dir
        self._tmp.cleanup()


class TestSaveAndPermissions(TokensDirTestCase):
    def test_save_token_creates_0600_file(self):
        path = tokens_mod.save_token("wat", "abc.def.ghi")
        self.assertTrue(os.path.isfile(path))
        self.assertEqual(oct(os.stat(path).st_mode & 0o777), "0o600")
        with open(path, "r", encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "abc.def.ghi")

    def test_tokens_dir_is_0700(self):
        tokens_mod.save_token("x", "y")
        self.assertEqual(oct(os.stat(self._tmp.name).st_mode & 0o777), "0o700")

    def test_atomic_write_no_tmp_leftover(self):
        tokens_mod.save_token("wat", "v1")
        tokens_mod.save_token("wat", "v2")
        files = os.listdir(self._tmp.name)
        self.assertEqual(files, ["wat"])  # 无 .tmp 残留
        with open(os.path.join(self._tmp.name, "wat"), "r", encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "v2")  # 覆盖为最新值

    def test_save_json_roundtrip(self):
        tokens_mod.save_json("wat.meta", {"acquired_at": 123, "ttl": 240})
        self.assertEqual(tokens_mod.load_json("wat.meta"), {"acquired_at": 123, "ttl": 240})

    def test_load_json_bad_content_returns_empty(self):
        tokens_mod.save_token("wat.meta", "{not json")
        self.assertEqual(tokens_mod.load_json("wat.meta"), {})


class TestMask(TokensDirTestCase):
    def test_mask_shape(self):
        masked = tokens_mod.mask("eyJhbGciOiJIUzI1NiJ9.payload-body.signature")
        self.assertTrue(masked.startswith("eyJhbGci"))
        self.assertIn("(len=", masked)
        self.assertNotIn("payload-body", masked)

    def test_mask_empty(self):
        self.assertEqual(tokens_mod.mask(""), "<empty>")


class TestIdTokenExpiry(TokensDirTestCase):
    def test_missing_id_token_hint(self):
        with self.assertRaises(tokens_mod.TokenExpiredError) as ctx:
            tokens_mod.load_id_token()
        self.assertIn("python3 sample.py login", str(ctx.exception))
        self.assertIn("未找到", str(ctx.exception))

    def test_expired_id_token_hint(self):
        token = make_jwt({"sub": "user_xxxxxxxx0001", "exp": int(time.time()) - 100})
        tokens_mod.save_token("id_token", token)
        with self.assertRaises(tokens_mod.TokenExpiredError) as ctx:
            tokens_mod.load_id_token()
        self.assertIn("python3 sample.py login", str(ctx.exception))
        self.assertIn("过期", str(ctx.exception))

    def test_valid_id_token_loaded(self):
        token = make_jwt({"sub": "user_xxxxxxxx0001", "exp": int(time.time()) + 600})
        tokens_mod.save_token("id_token", token)
        self.assertEqual(tokens_mod.load_id_token(), token)

    def test_no_exp_claim_accepted(self):
        """无 exp 的令牌不做本地过期拦截（交由服务端最终裁决）。"""
        token = make_jwt({"sub": "user_xxxxxxxx0001"})
        tokens_mod.save_token("id_token", token)
        self.assertEqual(tokens_mod.load_id_token(), token)

    def test_corrupted_id_token_hint(self):
        tokens_mod.save_token("id_token", "not-a-jwt")
        with self.assertRaises(tokens_mod.TokenExpiredError) as ctx:
            tokens_mod.load_id_token()
        self.assertIn("python3 sample.py login", str(ctx.exception))


class TestWatExpiry(TokensDirTestCase):
    def test_missing_wat_hint(self):
        with self.assertRaises(tokens_mod.TokenExpiredError) as ctx:
            tokens_mod.load_wat()
        self.assertIn("python3 sample.py exchange-wat", str(ctx.exception))

    def test_fresh_wat_loaded(self):
        tokens_mod.save_wat("jwe-opaque-token-value")
        self.assertEqual(tokens_mod.load_wat(), "jwe-opaque-token-value")

    def test_expired_wat_hint(self):
        tokens_mod.save_token("wat", "jwe-old")
        # 侧车时间戳拨回 10 分钟前（TTL 240s 已超）
        tokens_mod.save_json(
            "wat.meta",
            {"acquired_at": int(time.time()) - 600, "ttl": tokens_mod.WAT_TTL_SECONDS},
        )
        with self.assertRaises(tokens_mod.TokenExpiredError) as ctx:
            tokens_mod.load_wat()
        self.assertIn("python3 sample.py exchange-wat", str(ctx.exception))
        self.assertIn("240", str(ctx.exception))

    def test_save_wat_writes_meta_sidecar(self):
        tokens_mod.save_wat("jwe-token")
        meta = tokens_mod.load_json("wat.meta")
        self.assertIn("acquired_at", meta)
        self.assertEqual(meta.get("ttl"), tokens_mod.WAT_TTL_SECONDS)
        self.assertLessEqual(abs(meta["acquired_at"] - time.time()), 5)

    def test_wat_without_meta_falls_back_to_mtime(self):
        """侧车缺失时按文件 mtime 兜底（异常落盘场景）。"""
        tokens_mod.save_token("wat", "jwe-token")
        # 人为把 mtime 拨回过去
        past = time.time() - (tokens_mod.WAT_TTL_SECONDS + 100)
        os.utime(os.path.join(self._tmp.name, "wat"), (past, past))
        with self.assertRaises(tokens_mod.TokenExpiredError):
            tokens_mod.load_wat()


class TestOrderAtExpiry(TokensDirTestCase):
    def test_missing_order_at_hint(self):
        with self.assertRaises(tokens_mod.TokenExpiredError) as ctx:
            tokens_mod.load_order_at()
        self.assertIn("python3 sample.py obo", str(ctx.exception))

    def test_expired_order_at_hint(self):
        token = make_jwt({"sub": "user_xxxxxxxx0001", "exp": int(time.time()) - 60})
        tokens_mod.save_token("order_at", token)
        with self.assertRaises(tokens_mod.TokenExpiredError) as ctx:
            tokens_mod.load_order_at()
        self.assertIn("python3 sample.py obo", str(ctx.exception))

    def test_valid_order_at(self):
        token = make_jwt({"sub": "user_xxxxxxxx0001", "exp": int(time.time()) + 300})
        tokens_mod.save_token("order_at", token)
        self.assertEqual(tokens_mod.load_order_at(), token)

    def test_opaque_token_accepted(self):
        """非 JWT（不透明）AT 不做本地过期判断，交服务端 401 兜底。"""
        tokens_mod.save_token("order_at", "opaque-token-value")
        self.assertEqual(tokens_mod.load_order_at(), "opaque-token-value")


class TestTokensStatus(TokensDirTestCase):
    def test_status_absent(self):
        status = tokens_mod.tokens_status()
        self.assertFalse(status["id_token"]["exists"])
        self.assertFalse(status["wat"]["exists"])
        self.assertFalse(status["order_at"]["exists"])
        self.assertFalse(status["order_rt_exists"])

    def test_status_valid_and_expired(self):
        tokens_mod.save_token("id_token", make_jwt({"exp": int(time.time()) + 600}))
        tokens_mod.save_wat("jwe")
        tokens_mod.save_token("order_at", make_jwt({"exp": int(time.time()) - 10}))
        status = tokens_mod.tokens_status()
        self.assertFalse(status["id_token"]["expired"])
        self.assertFalse(status["wat"]["expired"])
        self.assertTrue(status["order_at"]["expired"])
        self.assertIn("python3 sample.py obo", status["order_at"]["hint"])


class TestDecodeJwtPayload(TokensDirTestCase):
    def test_decode_payload(self):
        token = make_jwt({"sub": "user_xxxxxxxx0001", "nonce": "n-1"})
        claims = tokens_mod.decode_jwt_payload(token)
        self.assertEqual(claims["sub"], "user_xxxxxxxx0001")
        self.assertEqual(claims["nonce"], "n-1")

    def test_jwe_rejected(self):
        with self.assertRaises(ValueError):
            tokens_mod.decode_jwt_payload("a.b.c.d.e")

    def test_numeric_payload_rejected(self):
        """Minor-9：payload 为纯数字（非 JSON 对象）时抛 ValueError，
        而非返回 int 让下游 claims.get 抛裸 AttributeError。"""
        with self.assertRaises(ValueError) as ctx:
            tokens_mod.decode_jwt_payload(make_jwt_raw_payload("42"))
        self.assertIn("不是 JSON 对象", str(ctx.exception))

    def test_array_payload_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            tokens_mod.decode_jwt_payload(make_jwt_raw_payload('["read","write"]'))
        self.assertIn("不是 JSON 对象", str(ctx.exception))

    def test_string_payload_rejected(self):
        with self.assertRaises(ValueError):
            tokens_mod.decode_jwt_payload(make_jwt_raw_payload('"just a string"'))


if __name__ == "__main__":
    unittest.main()
