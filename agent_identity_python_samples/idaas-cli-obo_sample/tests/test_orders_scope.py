"""订单服务 scope/身份差异化测试：ephemeral port 起真实 HTTP 服务（零外网依赖）。

用测试内生成的 RSA 密钥签发令牌（fetch_func 注入 JWKS，不联网），覆盖：
- read.all → 全量订单 / 无 read.all → 按 sub 过滤本人订单；
- write.all → POST 受理 / 无 write.all → 403 insufficient_scope；
- 401 各分支（无 Authorization / 坏格式 / 篡改签名 / 过期令牌）且响应体不回显令牌；
- JWKS 源故障 → 503。
"""

import json
import os
import socket
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request
import http.client

SAMPLE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (SAMPLE_DIR, os.path.dirname(os.path.abspath(__file__))):
    if path not in sys.path:
        sys.path.insert(0, path)

from orders import mock_data  # noqa: E402
from orders.server import make_server  # noqa: E402
from orders.verify import JwksFetchError, TokenVerifier  # noqa: E402
from test_jwt_verify import generate_rsa, make_jwk, make_jwt  # noqa: E402

ISSUER = "https://eiam.example.com/api/v2/iauths_system/oauth2"
AUDIENCE = "agent-demo-orders-app"
KID = "orders-test-key"


class OrdersServerTestCase(unittest.TestCase):
    """基类：起真实订单服务（ephemeral port）+ 测试密钥签发令牌。"""

    @classmethod
    def setUpClass(cls):
        cls.n, cls.e, cls.d = generate_rsa(bits=1024, seed=2024)
        cls.jwks = {"keys": [make_jwk(KID, cls.n, cls.e)]}
        cls.verifier = TokenVerifier(
            issuer=ISSUER,
            audience=AUDIENCE,
            jwks_uri="https://jwks.example/keys",
            fetch_func=lambda _uri: cls.jwks,
        )
        cls.server = make_server(port=0, verifier=cls.verifier)
        cls.base = "http://127.0.0.1:{}".format(cls.server.server_address[1])
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def setUp(self):
        # mock_data 是模块级状态：每个用例前恢复初始副本（POST 用例会追加订单）
        import copy

        self._orders_backup = copy.deepcopy(mock_data.ORDERS_BY_SUB)
        self._alias_backup = dict(mock_data.SUB_ALIAS)

    def tearDown(self):
        mock_data.ORDERS_BY_SUB.clear()
        mock_data.ORDERS_BY_SUB.update(self._orders_backup)
        mock_data.SUB_ALIAS.clear()
        mock_data.SUB_ALIAS.update(self._alias_backup)

    # ---- 工具 ----

    def token(self, sub="employee-alice", scope="read write.all", exp=None, aud=AUDIENCE):
        claims = {
            "iss": ISSUER,
            "aud": aud,
            "sub": sub,
            "scope": scope,
            "exp": exp or int(time.time()) + 600,
            "iat": int(time.time()),
        }
        return make_jwt(self.n, self.d, KID, claims)

    def request(self, path, method="GET", token=None, body=None):
        url = self.base + path
        data = None
        headers = {"Accept": "application/json"}
        if token is not None:
            headers["Authorization"] = "Bearer {}".format(token)
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            try:
                return exc.code, json.loads(raw)
            except ValueError:
                return exc.code, raw


class TestHealthRoute(OrdersServerTestCase):
    def test_health_no_auth(self):
        status, payload = self.request("/health")
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["issuer"], ISSUER)


class TestGetOrdersScope(OrdersServerTestCase):
    def test_read_all_returns_everyones_orders(self):
        status, payload = self.request("/orders", token=self.token(scope="read read.all write.all"))
        self.assertEqual(status, 200)
        self.assertEqual(payload["scope_view"], "all")
        self.assertEqual(payload["count"], len(mock_data.all_orders()))
        owner_subs = {o["owner_sub"] for o in payload["orders"]}
        self.assertIn("employee-alice", owner_subs)
        self.assertIn("employee-bob", owner_subs)
        self.assertIn("admin", owner_subs)

    def test_no_read_all_filters_own_orders(self):
        status, payload = self.request("/orders", token=self.token(sub="employee-alice", scope="read write.all"))
        self.assertEqual(status, 200)
        self.assertEqual(payload["scope_view"], "own")
        self.assertEqual(payload["count"], 2)
        for order in payload["orders"]:
            self.assertEqual(order["owner_sub"], "employee-alice")

    def test_bob_sees_only_his_orders(self):
        status, payload = self.request("/orders", token=self.token(sub="employee-bob", scope="read"))
        self.assertEqual(status, 200)
        self.assertEqual(payload["scope_view"], "own")
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["orders"][0]["order_id"], "ORD-2001")

    def test_list_scope_claim_supported(self):
        status, payload = self.request("/orders", token=self.token(sub="employee-bob", scope=["read"]))
        self.assertEqual(status, 200)
        self.assertEqual(payload["scope_view"], "own")
        self.assertEqual(payload["count"], 1)

    def test_unknown_sub_gets_empty_own_list(self):
        status, payload = self.request("/orders", token=self.token(sub="user_unknown9999", scope="read"))
        self.assertEqual(status, 200)
        self.assertEqual(payload["scope_view"], "own")
        self.assertEqual(payload["count"], 0)
        self.assertEqual(payload["orders"], [])

    def test_sub_alias_mapping(self):
        mock_data.SUB_ALIAS["user_xxxxxxxx0001"] = "employee-alice"
        status, payload = self.request("/orders", token=self.token(sub="user_xxxxxxxx0001", scope="read"))
        self.assertEqual(status, 200)
        self.assertEqual(payload["count"], 2)


class TestPostOrdersScope(OrdersServerTestCase):
    def test_write_all_creates_order(self):
        status, payload = self.request(
            "/orders",
            method="POST",
            token=self.token(sub="employee-alice", scope="read write.all"),
            body={"title": "测试下单", "amount": 88.5},
        )
        self.assertEqual(status, 201)
        self.assertTrue(payload["accepted"])
        order = payload["order"]
        self.assertEqual(order["owner_sub"], "employee-alice")
        self.assertEqual(order["status"], "ACCEPTED")
        # 创建后本人订单可见
        status, payload = self.request("/orders", token=self.token(sub="employee-alice", scope="read"))
        self.assertEqual(payload["count"], 3)

    def test_without_write_all_gets_403(self):
        status, payload = self.request(
            "/orders",
            method="POST",
            token=self.token(sub="employee-alice", scope="read read.all"),
            body={"title": "越权下单", "amount": 1},
        )
        self.assertEqual(status, 403)
        self.assertEqual(payload["error"], "insufficient_scope")
        self.assertIn("write.all", payload["error_description"])

    def test_missing_title_gets_400(self):
        status, payload = self.request(
            "/orders",
            method="POST",
            token=self.token(scope="read write.all"),
            body={"amount": 1},
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "invalid_request")


class TestAuthFailures(OrdersServerTestCase):
    def test_missing_authorization_401(self):
        status, payload = self.request("/orders")
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "invalid_request")

    def test_bad_scheme_401(self):
        req = urllib.request.Request(self.base + "/orders")
        req.add_header("Authorization", "Basic dXNlcjpwYXNz")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                status, payload = resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            status, payload = exc.code, json.loads(exc.read().decode())
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "invalid_request")

    def test_tampered_token_401_without_echo(self):
        token = self.token()
        head_payload, sig = token.rsplit(".", 1)
        tampered = "{}.{}".format(head_payload, "A" * len(sig))
        status, resp_body = self.request("/orders", token=tampered)
        self.assertEqual(status, 401)
        self.assertEqual(resp_body["error"], "invalid_token")
        # 响应体只有 error/error_description 两个键，绝不回显令牌
        self.assertEqual(set(resp_body.keys()), {"error", "error_description"})
        self.assertNotIn(tampered, json.dumps(resp_body))

    def test_expired_token_401(self):
        status, payload = self.request(
            "/orders", token=self.token(exp=int(time.time()) - 3600)
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "invalid_token")
        self.assertIn("过期", payload["error_description"])

    def test_wrong_audience_401(self):
        status, payload = self.request("/orders", token=self.token(aud="agent-other-app"))
        self.assertEqual(status, 401)
        self.assertIn("aud", payload["error_description"])

    def test_jwks_unreachable_503(self):
        verifier = TokenVerifier(
            issuer=ISSUER,
            audience=AUDIENCE,
            jwks_uri="https://jwks.example/keys",
            fetch_func=lambda _uri: (_ for _ in ()).throw(JwksFetchError("upstream down")),
        )
        server = make_server(port=0, verifier=verifier)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = "http://127.0.0.1:{}".format(server.server_address[1])
            req = urllib.request.Request(base + "/orders")
            req.add_header("Authorization", "Bearer {}".format(self.token()))
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    status, payload = resp.status, json.loads(resp.read().decode())
            except urllib.error.HTTPError as exc:
                status, payload = exc.code, json.loads(exc.read().decode())
            self.assertEqual(status, 503)
            self.assertEqual(payload["error"], "temporarily_unavailable")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_unknown_route_404(self):
        status, payload = self.request("/nope", token=self.token())
        self.assertEqual(status, 404)


class TestHandlerLogicDirect(OrdersServerTestCase):
    """不起网络直接调 handler 逻辑函数（WSGI 风格），验证纯函数行为。"""

    def test_authenticate_returns_claims(self):
        from orders.server import authenticate

        claims, failure = authenticate(self.verifier, "Bearer {}".format(self.token()))
        self.assertIsNone(failure)
        self.assertEqual(claims["sub"], "employee-alice")

    def test_authenticate_missing_header(self):
        from orders.server import authenticate

        claims, failure = authenticate(self.verifier, None)
        self.assertIsNone(claims)
        status, payload = failure
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "invalid_request")


class TestMakeServerPortInUse(OrdersServerTestCase):
    """Major-4：端口被占用时 make_server 抛 FlowError（带 --port 指引），而非裸 OSError 栈。"""

    def test_port_in_use_raises_flow_error(self):
        from lib.flow import FlowError

        blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        blocker.bind(("127.0.0.1", 0))
        blocker.listen(1)
        occupied_port = blocker.getsockname()[1]
        try:
            with self.assertRaises(FlowError) as ctx:
                make_server(port=occupied_port, verifier=self.verifier)
            message = str(ctx.exception)
            self.assertIn(str(occupied_port), message)
            self.assertIn("--port", message)
            self.assertIn("端口被占用", message)
        finally:
            blocker.close()


class TestRequestBodyHandling(OrdersServerTestCase):
    """Minor-7：非法 Content-Length 按空体处理（400）；超 1MB 上限直接 413。"""

    def _raw_post(self, content_length: str):
        """底层 POST：绕过 urllib 以便发送非法 Content-Length 头。"""
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=10)
        try:
            conn.putrequest("POST", "/orders")
            conn.putheader("Authorization", "Bearer {}".format(self.token(scope="read write.all")))
            conn.putheader("Content-Type", "application/json")
            conn.putheader("Content-Length", content_length)
            conn.endheaders()  # 不发送 body：两种分支服务端均不依赖实际 body
            resp = conn.getresponse()
            payload = json.loads(resp.read().decode("utf-8"))
            return resp.status, payload
        finally:
            conn.close()

    def test_invalid_content_length_treated_as_empty_body(self):
        # "abc" 不是合法长度 → 按空体 {} 处理 → title 缺失 → 400 invalid_request
        # （旧行为：int("abc") 抛 ValueError 裸栈，连接被硬断）
        status, payload = self._raw_post("abc")
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "invalid_request")
        self.assertIn("title", payload["error_description"])

    def test_oversized_declared_body_gets_413(self):
        # 声明 2MB 超过 1MB 上限 → 413 request_too_large（连接关闭，不读入超大体）
        status, payload = self._raw_post(str(2 * 1024 * 1024))
        self.assertEqual(status, 413)
        self.assertEqual(payload["error"], "request_too_large")


if __name__ == "__main__":
    unittest.main()
