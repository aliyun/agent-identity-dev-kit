"""RPC V1 签名固定向量测试（期望值由独立脚本对参考实现口径预先计算后写死）。

参考口径（预发实测通过）：
- canonical query：percent_encode(safe="~") 按 key 排序 & 拼接；
- string_to_sign = METHOD & %2F & quote_plus(cqs, safe="~")；
- 签名 = base64(HMAC-SHA1(secret + "&", string_to_sign))；
- formData 风格：业务参数展开并入签名集合、body urlencode 发送、签名放 query。
"""

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import rpc  # noqa: E402


class TestPercentEncode(unittest.TestCase):
    def test_basic_ascii(self):
        self.assertEqual(rpc.percent_encode("abcXYZ019"), "abcXYZ019")

    def test_space_slash_tilde_plus_chinese(self):
        # 空格→%20；/→%2F；~ 保留；中文按 UTF-8；+→%2B
        self.assertEqual(
            rpc.percent_encode("hello world/~中文/a+b"),
            "hello%20world%2F~%E4%B8%AD%E6%96%87%2Fa%2Bb",
        )

    def test_timestamp_colons(self):
        self.assertEqual(rpc.percent_encode("2026-08-29T00:00:00Z"), "2026-08-29T00%3A00%3A00Z")

    def test_non_str_input_casted(self):
        self.assertEqual(rpc.percent_encode(123), "123")


class TestCanonicalAndSignature(unittest.TestCase):
    VECTOR = {
        "AccessKeyId": "testAK",
        "Action": "TestAction",
        "Format": "json",
        "SignatureMethod": "HMAC-SHA1",
        "SignatureNonce": "nonce-001",
        "SignatureVersion": "1.0",
        "Timestamp": "2026-08-29T00:00:00Z",
        "Version": "2025-09-01",
    }

    EXPECTED_CQS = (
        "AccessKeyId=testAK&Action=TestAction&Format=json&SignatureMethod=HMAC-SHA1"
        "&SignatureNonce=nonce-001&SignatureVersion=1.0"
        "&Timestamp=2026-08-29T00%3A00%3A00Z&Version=2025-09-01"
    )
    EXPECTED_STS = (
        "POST&%2F&AccessKeyId%3DtestAK%26Action%3DTestAction%26Format%3Djson"
        "%26SignatureMethod%3DHMAC-SHA1%26SignatureNonce%3Dnonce-001"
        "%26SignatureVersion%3D1.0%26Timestamp%3D2026-08-29T00%253A00%253A00Z"
        "%26Version%3D2025-09-01"
    )
    EXPECTED_SIG = "75/QYq1PTemR1YplYVR2UvtcAOY="

    def test_canonical_query_string_sorted_and_encoded(self):
        # 乱序输入也按 key 排序输出
        shuffled = dict(reversed(list(self.VECTOR.items())))
        self.assertEqual(rpc.canonical_query_string(shuffled), self.EXPECTED_CQS)

    def test_string_to_sign(self):
        self.assertEqual(rpc.string_to_sign("POST", self.VECTOR), self.EXPECTED_STS)

    def test_signature_deterministic_known_vector(self):
        sig = rpc.get_rpc_signature(self.VECTOR, "POST", "testSK")
        self.assertEqual(sig, self.EXPECTED_SIG)

    def test_signature_method_changes_result(self):
        sig_get = rpc.get_rpc_signature(self.VECTOR, "GET", "testSK")
        self.assertNotEqual(sig_get, self.EXPECTED_SIG)

    def test_signature_secret_changes_result(self):
        sig2 = rpc.get_rpc_signature(self.VECTOR, "POST", "otherSK")
        self.assertNotEqual(sig2, self.EXPECTED_SIG)

    def test_none_values_skipped_in_cqs(self):
        params = {"B": "2", "A": None}
        self.assertEqual(rpc.canonical_query_string(params), "B=2")


class TestFormExpansion(unittest.TestCase):
    def test_utils_query_dict_list_scalar(self):
        flat = rpc.utils_query(
            {
                "OAuth2Flow": "ON_BEHALF_OF",
                "Scopes": '["read","write.all"]',
                "Nested": {"Level2": "v"},
                "Items": ["a", "b"],
            }
        )
        self.assertEqual(flat["OAuth2Flow"], "ON_BEHALF_OF")
        self.assertEqual(flat["Nested.Level2"], "v")
        # list → k.N 从 1 起
        self.assertEqual(flat["Items.1"], "a")
        self.assertEqual(flat["Items.2"], "b")

    def test_to_form_string_sorted_and_urlencoded(self):
        form = rpc.to_form_string(
            {
                "OAuth2Flow": "ON_BEHALF_OF",
                "WorkloadAccessToken": "fake.wat.value",
                "Scopes": '["read","write.all"]',
            }
        )
        self.assertEqual(
            form,
            "OAuth2Flow=ON_BEHALF_OF&Scopes=%5B%22read%22%2C%22write.all%22%5D"
            "&WorkloadAccessToken=fake.wat.value",
        )

    def test_formdata_merged_signature_vector(self):
        """formData 风格签名集合 = query meta ∪ Utils.query(body)。"""
        meta = {
            "Action": "GetResourceOAuth2Token",
            "Format": "json",
            "Version": "2025-11-27",
            "Timestamp": "2026-08-29T12:00:00Z",
            "SignatureNonce": "nonce-002",
            "SignatureMethod": "HMAC-SHA1",
            "SignatureVersion": "1.0",
            "AccessKeyId": "testAK",
        }
        body = {
            "OAuth2Flow": "ON_BEHALF_OF",
            "WorkloadAccessToken": "fake.wat.value",
            "Scopes": '["read","write.all"]',
        }
        merged = dict(meta)
        merged.update(rpc.utils_query(body))
        self.assertEqual(
            rpc.get_rpc_signature(merged, "POST", "testSK"),
            "enDWFRkPr9ZD/h1LXzwycSiQKvE=",
        )

    def test_sts_token_enters_signature_set(self):
        """STS 双凭证：SecurityToken 参与签名（加入后签名值改变）。"""
        meta = {
            "Action": "GetResourceOAuth2Token",
            "Format": "json",
            "Version": "2025-11-27",
            "Timestamp": "2026-08-29T12:00:00Z",
            "SignatureNonce": "nonce-002",
            "SignatureMethod": "HMAC-SHA1",
            "SignatureVersion": "1.0",
            "AccessKeyId": "testAK",
        }
        with_sts = dict(meta, SecurityToken="sts-token-xyz")
        self.assertEqual(
            rpc.get_rpc_signature(with_sts, "POST", "anotherSK"),
            "Fz7wNj1/yKmaJJ95ZyqHB+Q1en8=",
        )
        self.assertNotEqual(
            rpc.get_rpc_signature(meta, "POST", "anotherSK"),
            rpc.get_rpc_signature(with_sts, "POST", "anotherSK"),
        )


class TestBuildSignedRequest(unittest.TestCase):
    def test_formdata_style_shape(self):
        req = rpc.build_signed_request(
            "agentidentitydata.cn-hangzhou.aliyuncs.com",
            "GetResourceOAuth2Token",
            "2025-11-27",
            {
                "OAuth2Flow": "ON_BEHALF_OF",
                "WorkloadAccessToken": "fake.wat.value",
                "Scopes": '["read","write.all"]',
            },
            style="formData",
            creds=("testAK", "testSK", "sts-token-xyz"),
            timestamp="2026-08-29T12:00:00Z",
            nonce="nonce-002",
        )
        # 签名放 query，业务参数放 body（不进最终 query）
        self.assertIn("Signature=", req["url"])
        self.assertNotIn("OAuth2Flow", req["url"])
        self.assertNotIn("WorkloadAccessToken", req["url"])
        # body 是 urlencoded form，且不含签名
        body = req["body"].decode("utf-8")
        self.assertIn("OAuth2Flow=ON_BEHALF_OF", body)
        self.assertIn("Scopes=%5B%22read%22%2C%22write.all%22%5D", body)
        self.assertNotIn("Signature=", body)
        self.assertEqual(req["headers"]["content-type"], "application/x-www-form-urlencoded")
        # STS：SecurityToken 进 query
        self.assertIn("SecurityToken=sts-token-xyz", req["url"])
        self.assertEqual(
            req["url"],
            "https://agentidentitydata.cn-hangzhou.aliyuncs.com?"
            "Action=GetResourceOAuth2Token&Format=json&Version=2025-11-27"
            "&Timestamp=2026-08-29T12%3A00%3A00Z&SignatureNonce=nonce-002"
            "&SecurityToken=sts-token-xyz&SignatureMethod=HMAC-SHA1"
            "&SignatureVersion=1.0&AccessKeyId=testAK"
            "&Signature=rkmT1WNlHNu0kb9vcwF33ldOtII%3D",
        )

    def test_query_style_shape(self):
        req = rpc.build_signed_request(
            "agentidentitydata.cn-hangzhou.aliyuncs.com",
            "GetWorkloadAccessTokenForJWT",
            "2025-11-27",
            {"WorkloadIdentityName": "demo-wi", "UserToken": "eyJhbGciOi.J5.d"},
            style="query",
            creds=("testAK", "testSK", None),
            timestamp="2026-08-29T00:00:00Z",
            nonce="nonce-001",
        )
        # query 风格：业务参数在 query、无 body
        self.assertIn("WorkloadIdentityName=demo-wi", req["url"])
        self.assertIn("UserToken=eyJhbGciOi.J5.d", req["url"])
        self.assertIsNone(req["body"])
        self.assertNotIn("content-type", req["headers"])
        self.assertEqual(
            req["url"],
            "https://agentidentitydata.cn-hangzhou.aliyuncs.com?"
            "Action=GetWorkloadAccessTokenForJWT&Format=json&Version=2025-11-27"
            "&Timestamp=2026-08-29T00%3A00%3A00Z&SignatureNonce=nonce-001"
            "&WorkloadIdentityName=demo-wi&UserToken=eyJhbGciOi.J5.d"
            "&SignatureMethod=HMAC-SHA1&SignatureVersion=1.0&AccessKeyId=testAK"
            "&Signature=LUNRJ9stEmTK0jHOkZTMh7TX3rM%3D",
        )

    def test_invalid_style_rejected(self):
        with self.assertRaises(ValueError):
            rpc.build_signed_request("x", "A", "V", {}, style="json")


class TestWaitWindowRetryBudget(unittest.TestCase):
    """Minor-6：窗口抖动不消耗普通退避预算。

    旧行为：窗口分支也递增 attempt → N 次窗口抖动后，后续普通可重试错误
    （Throttling/5xx）被 ``attempt <= max_retries`` 提前放弃。修复后窗口分支
    归零 attempt，窗口结束后仍保留完整的 3 次退避预算。
    """

    def _run_script(self, script, **rpc_kwargs):
        """按脚本顺序让 _do_call 返回/抛出；返回 (最终结果, 调用次数, sleep 序列)。"""
        calls = []

        def fake_call(*_args, **_kwargs):
            outcome = script[len(calls)]
            calls.append(1)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        with mock.patch.object(rpc, "_do_call", side_effect=fake_call):
            with mock.patch.object(rpc.time, "sleep") as fake_sleep:
                result = rpc.rpc_call("ep.example.com", "GetResourceOAuth2Token", "2025-11-27", **rpc_kwargs)
        sleeps = [c.args[0] for c in fake_sleep.call_args_list]
        return result, len(calls), sleeps

    def test_window_jitter_preserves_full_retry_budget(self):
        # 2 次窗口抖动（MissingParameter）后接 3 次限流，第 6 次成功。
        # 旧行为在第 2 次 Throttling 就会因预算耗尽而放弃。
        script = [
            rpc.RpcError(400, "MissingParameter.Scopes", "window jitter", "req-1", False),
            rpc.RpcError(400, "MissingParameter.Scopes", "window jitter", "req-2", False),
            rpc.RpcError(429, "Throttling.User", "slow down", "req-3", True),
            rpc.RpcError(429, "Throttling.User", "slow down", "req-4", True),
            rpc.RpcError(429, "Throttling.User", "slow down", "req-5", True),
            {"RequestId": "req-6", "Data": "ok"},
        ]
        result, call_count, sleeps = self._run_script(script, wait_window=True)
        self.assertEqual(result["RequestId"], "req-6")
        self.assertEqual(call_count, 6)  # 2 窗口 + 3 限流退避 + 1 成功，一步不少
        # 窗口等待 5s×2；退避 1s → 2s → 4s（预算从头开始）
        self.assertEqual(sleeps, [5, 5, 1, 2, 4])

    def test_window_attempts_capped_at_30(self):
        # 窗口预算 30 次用尽后 MissingParameter 正常抛出（不会被无限重试包裹）
        err = rpc.RpcError(400, "MissingParameter.Scopes", "persistent", "req-x", False)
        with mock.patch.object(rpc, "_do_call", side_effect=err) as fake_call:
            with mock.patch.object(rpc.time, "sleep"):
                with self.assertRaises(rpc.RpcError):
                    rpc.rpc_call("ep.example.com", "A", "V", wait_window=True)
        self.assertEqual(fake_call.call_count, 31)  # 首次 + 30 次窗口重试


class TestTimestampTimezoneAware(unittest.TestCase):
    """Minor-13：get_timestamp timezone-aware（与 utcnow 老接口等值，3.9+ 兼容）。"""

    def test_known_epoch_value(self):
        # 2026-08-29T00:00:00Z（UTC）对应的 epoch 秒，与 utcfromtimestamp 老接口等值
        self.assertEqual(rpc.get_timestamp(1787961600), "2026-08-29T00:00:00Z")

    def test_default_call_returns_utc_z_format(self):
        import re

        ts = rpc.get_timestamp()
        self.assertTrue(re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", ts), ts)


class TestErrorClassification(unittest.TestCase):
    def test_server_errors_retryable(self):
        self.assertTrue(rpc.classify_error(500, "InternalError")[0])
        self.assertTrue(rpc.classify_error(503, "ServiceUnavailable")[0])
        self.assertTrue(rpc.classify_error(0, "NetworkError")[0])
        self.assertTrue(rpc.classify_error(429, "Throttling")[0])
        self.assertTrue(rpc.classify_error(400, "Throttling.User")[0])

    def test_deterministic_errors_not_retryable(self):
        for code in (
            "SignatureDoesNotMatch",
            "InvalidAccessKeyId.NotFound",
            "InvalidSecurityToken.Expired",
            "InvalidParameter.JsonWebToken",
            "Forbidden.InboundCredentialMissing",
            "MissingParameter.Scopes",
        ):
            self.assertFalse(rpc.classify_error(400, code)[0], code)

    def test_rpc_error_attributes(self):
        err = rpc.RpcError(400, "InvalidParameter.X", "bad param", "req-123", False)
        self.assertEqual((err.status, err.code, err.request_id, err.retryable), (400, "InvalidParameter.X", "req-123", False))
        self.assertIn("req-123", str(err))
        self.assertIn("InvalidParameter.X", str(err))


if __name__ == "__main__":
    unittest.main()
