"""flow.py login 回调 handler 单测：state 校验先于 error 处理（评审 Major-1）。

攻击面：恶意网页 ``<img src="http://127.0.0.1:8765/callback?error=...&state=...">``
或本机任意进程都可构造 error 回调。修复前 error 分支在 state 校验之前执行——
伪造回调即可打断进行中的登录（本地 DoS）。修复后：

- state 不匹配的 error 回调 → 400「已忽略」页，**不**终止等待（server 继续运行）；
- state 匹配的 error 回调 → 原有处理（记录 error 并终止登录等待）；
- code 回调的 state 校验语义保持不变（不匹配 → state_mismatch 终止）。

起真实 loopback 回调 server（ephemeral port），零网络外联。
"""

import os
import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.flow import _CallbackState, _LoginCallbackHandler  # noqa: E402


class LoginCallbackServerTestCase(unittest.TestCase):
    """基类：起真实 loopback 回调 server（ephemeral port）。"""

    EXPECTED_STATE = "expected-state-unit"

    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _LoginCallbackHandler)
        self.server.daemon_threads = True
        self.server.cb_state = _CallbackState(self.EXPECTED_STATE, "expected-nonce")
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self._shutdown)

    def _shutdown(self):
        # 幂等收尾：部分用例中 handler 已通过 _finish 自行 shutdown
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def get(self, query: str):
        """GET /callback?<query>，返回 (status, body_text)。"""
        url = "http://127.0.0.1:{}/callback?{}".format(self.port, query)
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                return resp.status, resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8")


class TestForgedErrorCallback(LoginCallbackServerTestCase):
    """伪造 error 回调（state 不匹配）不终止登录等待。"""

    def test_forged_error_callback_ignored_and_server_keeps_waiting(self):
        status, body = self.get(
            "error=access_denied&error_description=forged&state=attacker-state"
        )
        self.assertEqual(status, 400)
        self.assertIn("已忽略", body)
        self.assertIn("state 不匹配", body)
        cb = self.server.cb_state
        self.assertFalse(cb.done.wait(timeout=0.2), "伪造 error 回调不应终止登录等待")
        self.assertIsNone(cb.error)
        # server 仍在服务：后续请求仍可正常到达（未被 shutdown）
        status2, _body2 = self.get("error=server_error&state=attacker-state-2")
        self.assertEqual(status2, 400)

    def test_error_callback_with_matching_state_terminates(self):
        status, body = self.get(
            "error=access_denied&error_description=user+denied&state=" + self.EXPECTED_STATE
        )
        self.assertEqual(status, 400)
        self.assertIn("授权服务器返回错误", body)
        self.assertIn("access_denied", body)
        cb = self.server.cb_state
        self.assertTrue(cb.done.wait(timeout=5), "匹配 state 的 error 回调应终止登录等待")
        self.assertEqual(cb.error, "access_denied")
        self.assertEqual(cb.error_description, "user denied")

    def test_forged_then_real_error_callback_sequence(self):
        """完整时序：伪造回调被忽略（登录不中断）→ 真实 error 回调正常终止。"""
        status, _ = self.get("error=access_denied&state=wrong-state")
        self.assertEqual(status, 400)
        self.assertFalse(self.server.cb_state.done.is_set())
        status, _ = self.get("error=access_denied&state=" + self.EXPECTED_STATE)
        self.assertEqual(status, 400)
        self.assertTrue(self.server.cb_state.done.wait(timeout=5))


class TestCodeCallbackStateValidation(LoginCallbackServerTestCase):
    """code 回调的 state 校验语义保持不变（回归保护）。"""

    def test_code_callback_with_wrong_state_terminates_as_mismatch(self):
        status, body = self.get("code=ac-fake&state=wrong-state")
        self.assertEqual(status, 400)
        self.assertIn("state 校验未通过", body)
        cb = self.server.cb_state
        self.assertTrue(cb.done.wait(timeout=5))
        self.assertEqual(cb.error, "state_mismatch")

    def test_code_callback_with_matching_state_succeeds(self):
        status, body = self.get("code=ac-real&state=" + self.EXPECTED_STATE)
        self.assertEqual(status, 200)
        self.assertIn("登录成功", body)
        cb = self.server.cb_state
        self.assertTrue(cb.done.wait(timeout=5))
        self.assertEqual(cb.code, "ac-real")
        self.assertIsNone(cb.error)


if __name__ == "__main__":
    unittest.main()
