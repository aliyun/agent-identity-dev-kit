"""discovery（OIDC discovery 拉取 + 内存 TTL 缓存）单测（全程离线，零网络）。

覆盖 ``lib/discovery.py`` 的核心契约，含本轮加固的 5 个安全维度：

- **URL 拼装与入参校验（问题 2）**：``{IDAAS_ORIGIN}/api/v2/.../openid-configuration``；
  用 ``urlsplit`` 校验 scheme=https、netloc/hostname 非空、端口为数字、不含路径；
  ``netloc`` 重建修复裸 ``rstrip("/")`` 把 ``https://`` 削成 ``https:`` 的 bug。
- **可注入 fetch_func（问题 1）**：签名预判替代异常嗅探——fetch_func **绝不被调用
  两次**；注入体内部抛出的异常（含 TypeError）按原样传播（不吞、不重试）。
- **默认 fetch 异常白名单（问题 3）**：``HTTPError``/``URLError``/``OSError`` 之外，
  新增 ``http.client.HTTPException``（含 IncompleteRead/BadStatusLine，非 OSError 子类）
  与 ``ValueError``（含 UnicodeDecodeError）一律包装成 ``DiscoveryError``；
  ``decode(errors="replace")`` 让非法编码落到「不是合法 JSON」分支。
- **重定向防降级（问题 4）**：``_HttpsOnlyRedirectHandler`` 阻止 https→http 降级；
  最终 URL 必须仍是 https 且 host 与 IDAAS_ORIGIN 一致（防跨域重定向 / SSRF）。
- **响应内容同源校验（问题 5）**：``jwks_uri`` 必须 https；``issuer``/``jwks_uri`` 的
  netloc 必须等于 IDAAS_ORIGIN 的 netloc（防 SSRF / issuer 混淆）；issuer 带路径前缀
  或恰为域名根均接受（不做与 IDAAS_ORIGIN 的字符串全等比对，避免误杀正常环境）。
- **apply_discovery / DiscoveryCache**：仅填空位、显式值优先、返回新 dict、
  IDAAS_ORIGIN 占位时宽容返回、TTL 命中只拉一次、force_refresh 旁路、错误不入缓存、
  并发冷启动只拉一次。

离线保证：
- 注入 ``fetch_func`` 的用例不触发 ``_default_fetch_discovery``；
- ``DiscoveryTestCase`` 基类把 ``_default_fetch_discovery`` 打桩为 AssertionError，
  任何真实网络拉取都会让用例失败；
- ``TestDefaultFetchDiscovery`` / ``TestRedirectHandler`` 直接测网络层，但通过
  ``mock.patch`` 替换 ``_build_opener``（fake opener）或直接调 handler，零真实网络。
"""

import http.client
import json
import os
import sys
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import discovery as disc  # noqa: E402
from lib.discovery import DiscoveryError  # noqa: E402

ORIGIN = "https://idaas-unit-test.example.com"
ISSUER = "https://idaas-unit-test.example.com/api/v2/iauths_system/oauth2"
JWKS_URI = "https://idaas-unit-test.example.com/api/v2/iauths_system/oauth2/jwks"
EXPECTED_URL = ORIGIN + "/api/v2/iauths_system/oauth2/.well-known/openid-configuration"


def make_fetch_func(payload=None, exc=None):
    """构造计数版注入 fetch_func：返回 (fetch_func, calls 列表)。

    签名 ``(url, timeout=DEFAULT_TIMEOUT)`` → arity=2 → 被以 ``fetch_func(url, timeout)``
    调用。用于断言「绝不调用两次」与 timeout 转发。
    """
    calls = []
    body = payload if payload is not None else {"issuer": ISSUER, "jwks_uri": JWKS_URI}

    def _fetch(url, timeout=disc.DEFAULT_TIMEOUT):
        calls.append((url, timeout))
        if exc is not None:
            raise exc
        return body

    return _fetch, calls


# ---------------------------------------------------------------------------
# 网络层替身（供 TestDefaultFetchDiscovery 离线驱动 _default_fetch_discovery）
# ---------------------------------------------------------------------------


class _FakeResponse:
    """替身 HTTP 响应：支持上下文管理器 + read()/geturl()。"""

    def __init__(self, body=b"", final_url=None):
        self._body = body
        self._final_url = final_url

    def read(self):
        return self._body

    def geturl(self):
        return self._final_url

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class _FakeOpener:
    """替身 opener：``open()`` 返回预设响应或抛预设异常（模拟网络层各种失败）。"""

    def __init__(self, resp=None, exc=None):
        self._resp = resp
        self._exc = exc
        self.opened = []

    def open(self, req, timeout=None):
        self.opened.append((req, timeout))
        if self._exc is not None:
            raise self._exc
        return self._resp


class DiscoveryTestCase(unittest.TestCase):
    """基类：兜底封死真实网络（默认 fetch 被调用即失败）+ 清理进程级缓存注册表。"""

    def setUp(self):
        patcher = mock.patch.object(
            disc,
            "_default_fetch_discovery",
            side_effect=AssertionError("离线测试不得触发真实网络拉取"),
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        disc._DEFAULT_CACHES.clear()
        self.addCleanup(disc._DEFAULT_CACHES.clear)


# ---------------------------------------------------------------------------
# URL 拼装与 origin 校验（问题 2）
# ---------------------------------------------------------------------------


class TestBuildDiscoveryUrl(DiscoveryTestCase):
    def test_contract_path(self):
        # discovery 文档路径契约（env.template / control_plane / env.py 多处印证）
        self.assertEqual(
            disc.DISCOVERY_PATH,
            "/api/v2/iauths_system/oauth2/.well-known/openid-configuration",
        )
        self.assertEqual(disc._build_discovery_url(ORIGIN), EXPECTED_URL)

    def test_trailing_slash_not_doubled(self):
        url = disc._build_discovery_url(ORIGIN + "/")
        self.assertEqual(url, EXPECTED_URL)
        self.assertNotIn("//api", url)

    def test_surrounding_whitespace_stripped(self):
        self.assertEqual(disc._build_discovery_url("  " + ORIGIN + "  "), EXPECTED_URL)

    def test_http_origin_rejected(self):
        with self.assertRaises(DiscoveryError) as ctx:
            disc._build_discovery_url("http://idaas-unit-test.example.com")
        self.assertIn("https", str(ctx.exception))

    def test_empty_origin_rejected(self):
        with self.assertRaises(DiscoveryError) as ctx:
            disc._build_discovery_url("")
        self.assertIn("IDAAS_ORIGIN", str(ctx.exception))

    def test_placeholder_origin_rejected(self):
        with self.assertRaises(DiscoveryError) as ctx:
            disc._build_discovery_url("<YOUR_IDAAS_ORIGIN>")
        msg = str(ctx.exception)
        self.assertIn("IDAAS_ORIGIN", msg)
        self.assertIn("ORDER_SERVICE_ISSUER", msg)  # 指引：显式填 issuer 可跳过 discovery

    def test_bare_host_rejected(self):
        with self.assertRaises(DiscoveryError):
            disc._build_discovery_url("idaas-unit-test.example.com")

    # ---- 问题 2 新增：urlsplit 校验 netloc/hostname/port/path ----

    def test_nonnumeric_port_rejected(self):
        # 旧代码只 startswith("https://") 放行 → http.client.InvalidURL: nonnumeric port
        # （不是 OSError 子类，会绕过网络异常包装裸逃逸）。现在 build 阶段即拦截。
        with self.assertRaises(DiscoveryError) as ctx:
            disc._build_discovery_url("https://idaas-unit-test.example.com:notaport")
        self.assertIn("IDAAS_ORIGIN", str(ctx.exception))

    def test_port_zero_rejected(self):
        # O4：:0 是保留端口，parts.port 会放行（0 在 0–65535 内）；显式收紧到 1–65535。
        with self.assertRaises(DiscoveryError) as ctx:
            disc._build_discovery_url("https://idaas-unit-test.example.com:0")
        msg = str(ctx.exception)
        self.assertIn("IDAAS_ORIGIN", msg)
        self.assertIn("端口越界", msg)

    def test_port_out_of_range_rejected(self):
        # O4：:70000 越界，parts.port 抛 ValueError → 既有分支包装成 DiscoveryError。
        with self.assertRaises(DiscoveryError) as ctx:
            disc._build_discovery_url("https://idaas-unit-test.example.com:70000")
        self.assertIn("IDAAS_ORIGIN", str(ctx.exception))

    def test_malformed_ipv6_rejected(self):
        # https://[::1 → urlsplit 抛 ValueError: Invalid IPv6 URL → 包装成 DiscoveryError
        with self.assertRaises(DiscoveryError) as ctx:
            disc._build_discovery_url("https://[::1")
        self.assertIn("IDAAS_ORIGIN", str(ctx.exception))

    def test_empty_netloc_rejected(self):
        # https:// → 旧 rstrip("/") 削成 "https:" 拼出畸形 URL；现 netloc 非空校验拦截
        with self.assertRaises(DiscoveryError) as ctx:
            disc._build_discovery_url("https://")
        self.assertIn("主机名", str(ctx.exception))

    def test_origin_with_path_rejected(self):
        # IDAAS_ORIGIN 是实例域名根，不含路径（discovery 路径由本函数拼接）
        with self.assertRaises(DiscoveryError) as ctx:
            disc._build_discovery_url("https://idaas-unit-test.example.com/base")
        self.assertIn("路径", str(ctx.exception))

    def test_valid_port_accepted_and_preserved(self):
        url = disc._build_discovery_url("https://idaas-unit-test.example.com:8443")
        self.assertEqual(
            url, "https://idaas-unit-test.example.com:8443" + disc.DISCOVERY_PATH
        )

    def test_ipv6_literal_accepted(self):
        # 合法 IPv6 字面量（带括号）→ netloc 重建保留括号
        url = disc._build_discovery_url("https://[::1]")
        self.assertEqual(url, "https://[::1]" + disc.DISCOVERY_PATH)

    def test_guide_message_present_on_reject(self):
        # 统一指引文案：告知正确格式
        with self.assertRaises(DiscoveryError) as ctx:
            disc._build_discovery_url("http://idaas-unit-test.example.com")
        self.assertIn("不含路径", str(ctx.exception))


# ---------------------------------------------------------------------------
# fetch_oidc_discovery（注入 fetch_func，问题 1）
# ---------------------------------------------------------------------------


class TestFetchOidcDiscovery(DiscoveryTestCase):
    def test_injected_fetch_returns_payload(self):
        fetch, calls = make_fetch_func()
        data = disc.fetch_oidc_discovery(ORIGIN, fetch_func=fetch)
        self.assertEqual(data, {"issuer": ISSUER, "jwks_uri": JWKS_URI})
        self.assertEqual(calls, [(EXPECTED_URL, disc.DEFAULT_TIMEOUT)])

    def test_custom_timeout_forwarded(self):
        fetch, calls = make_fetch_func()
        disc.fetch_oidc_discovery(ORIGIN, timeout=3, fetch_func=fetch)
        self.assertEqual(calls[0][1], 3)

    def test_single_arg_fetch_func_supported(self):
        """兼容只接 url 一个参数的 fetch_func（verify.py 风格）：签名预判 arity=1。"""
        seen = []

        def _fetch(url):
            seen.append(url)
            return {"issuer": ISSUER, "jwks_uri": JWKS_URI}

        data = disc.fetch_oidc_discovery(ORIGIN, fetch_func=_fetch)
        self.assertEqual(seen, [EXPECTED_URL])
        self.assertEqual(data["issuer"], ISSUER)

    def test_non_dict_payload_rejected(self):
        fetch, _calls = make_fetch_func(payload=["not", "a", "dict"])
        with self.assertRaises(DiscoveryError) as ctx:
            disc.fetch_oidc_discovery(ORIGIN, fetch_func=fetch)
        self.assertIn("非 dict", str(ctx.exception))

    def test_fetch_error_propagates(self):
        fetch, _calls = make_fetch_func(exc=DiscoveryError("HTTP 404"))
        with self.assertRaises(DiscoveryError) as ctx:
            disc.fetch_oidc_discovery(ORIGIN, fetch_func=fetch)
        self.assertIn("HTTP 404", str(ctx.exception))

    def test_invalid_origin_checked_before_fetch(self):
        fetch, calls = make_fetch_func()
        with self.assertRaises(DiscoveryError):
            disc.fetch_oidc_discovery("http://insecure.example.com", fetch_func=fetch)
        self.assertEqual(calls, [])  # origin 非法 → 连 fetch 都不该发生

    # ---- 问题 1 新增：签名预判，绝不调用两次，内部异常原样传播 ----

    def test_injected_body_typeerror_called_once_and_propagates(self):
        """注入体内部抛 TypeError → 只调用 1 次 + 裸 TypeError 原样传播（不吞、不重试）。

        旧的 ``except TypeError: fetch_func(url)`` 会误判此为「签名不兼容」而二次调用，
        既执行两遍副作用，又让二次抛出的裸 TypeError 逃出 DiscoveryError 接盘链。
        """
        calls = []

        def _fetch(url, timeout=disc.DEFAULT_TIMEOUT):
            calls.append((url, timeout))
            raise TypeError("None.strip() 模拟注入体内部 bug")

        with self.assertRaises(TypeError):  # 原样传播为裸 TypeError（非 DiscoveryError）
            disc.fetch_oidc_discovery(ORIGIN, fetch_func=_fetch)
        self.assertEqual(len(calls), 1)  # 绝不调用两次

    def test_injected_body_typeerror_single_arg_called_once(self):
        """单参 fetch_func 内部抛 TypeError 同样只调 1 次、原样传播。"""
        calls = []

        def _fetch(url):
            calls.append(url)
            raise TypeError("int('x') 模拟内部 bug")

        with self.assertRaises(TypeError):
            disc.fetch_oidc_discovery(ORIGIN, fetch_func=_fetch)
        self.assertEqual(len(calls), 1)

    def test_unintrospectable_fetch_func_falls_back_to_two_args(self):
        """inspect.signature 抛 ValueError（如部分 C 实现）→ fallback arity=2，仍只调 1 次。"""
        calls = []

        def _fetch(url, timeout=None):
            calls.append((url, timeout))
            return {"issuer": ISSUER, "jwks_uri": JWKS_URI}

        with mock.patch.object(disc.inspect, "signature", side_effect=ValueError("no sig")):
            data = disc.fetch_oidc_discovery(ORIGIN, fetch_func=_fetch)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1], disc.DEFAULT_TIMEOUT)  # fallback 走双参契约
        self.assertEqual(data["issuer"], ISSUER)

    def test_discovery_error_from_fetch_body_propagates(self):
        """注入体抛 DiscoveryError → 原样传播（仍是 DiscoveryError，链路接得住），只调 1 次。"""
        calls = []

        def _fetch(url, timeout=disc.DEFAULT_TIMEOUT):
            calls.append(url)
            raise DiscoveryError("HTTP 503")

        with self.assertRaises(DiscoveryError):
            disc.fetch_oidc_discovery(ORIGIN, fetch_func=_fetch)
        self.assertEqual(len(calls), 1)


# ---------------------------------------------------------------------------
# get_issuer_jwks（字段提取 + 同源安全校验，问题 5）
# ---------------------------------------------------------------------------


class TestGetIssuerJwks(DiscoveryTestCase):
    def test_returns_tuple(self):
        fetch, _calls = make_fetch_func()
        self.assertEqual(disc.get_issuer_jwks(ORIGIN, fetch_func=fetch), (ISSUER, JWKS_URI))

    def test_values_stripped(self):
        fetch, _calls = make_fetch_func(payload={"issuer": "  " + ISSUER, "jwks_uri": JWKS_URI + " "})
        self.assertEqual(disc.get_issuer_jwks(ORIGIN, fetch_func=fetch), (ISSUER, JWKS_URI))

    def test_extra_fields_ignored(self):
        fetch, _calls = make_fetch_func(
            payload={
                "issuer": ISSUER,
                "jwks_uri": JWKS_URI,
                "authorization_endpoint": "https://x.example.com/authorize",
                "token_endpoint": "https://x.example.com/token",
            }
        )
        self.assertEqual(disc.get_issuer_jwks(ORIGIN, fetch_func=fetch), (ISSUER, JWKS_URI))

    def test_missing_issuer_raises_with_guidance(self):
        fetch, _calls = make_fetch_func(payload={"jwks_uri": JWKS_URI})
        with self.assertRaises(DiscoveryError) as ctx:
            disc.get_issuer_jwks(ORIGIN, fetch_func=fetch)
        msg = str(ctx.exception)
        self.assertIn("issuer", msg)
        self.assertIn("ORDER_SERVICE_ISSUER", msg)  # 指引：显式填 issuer 跳过 discovery
        self.assertIn(disc.DISCOVERY_PATH, msg)  # 指引里给出可手动打开的 URL 路径

    def test_non_string_issuer_raises(self):
        fetch, _calls = make_fetch_func(payload={"issuer": 12345, "jwks_uri": JWKS_URI})
        with self.assertRaises(DiscoveryError):
            disc.get_issuer_jwks(ORIGIN, fetch_func=fetch)

    def test_blank_issuer_raises(self):
        fetch, _calls = make_fetch_func(payload={"issuer": "   ", "jwks_uri": JWKS_URI})
        with self.assertRaises(DiscoveryError):
            disc.get_issuer_jwks(ORIGIN, fetch_func=fetch)

    def test_missing_jwks_uri_raises_with_guidance(self):
        fetch, _calls = make_fetch_func(payload={"issuer": ISSUER})
        with self.assertRaises(DiscoveryError) as ctx:
            disc.get_issuer_jwks(ORIGIN, fetch_func=fetch)
        msg = str(ctx.exception)
        self.assertIn("jwks_uri", msg)
        self.assertIn("ORDER_SERVICE_JWKS_URI", msg)

    def test_non_string_jwks_uri_raises(self):
        fetch, _calls = make_fetch_func(payload={"issuer": ISSUER, "jwks_uri": {"url": JWKS_URI}})
        with self.assertRaises(DiscoveryError):
            disc.get_issuer_jwks(ORIGIN, fetch_func=fetch)

    # ---- 问题 5 新增：jwks_uri https + issuer/jwks_uri 同源校验 ----

    def test_jwks_uri_must_be_https(self):
        fetch, _calls = make_fetch_func(
            payload={"issuer": ISSUER, "jwks_uri": "http://idaas-unit-test.example.com/jwks"}
        )
        with self.assertRaises(DiscoveryError) as ctx:
            disc.get_issuer_jwks(ORIGIN, fetch_func=fetch)
        self.assertIn("https", str(ctx.exception))

    def test_issuer_must_be_https(self):
        fetch, _calls = make_fetch_func(
            payload={"issuer": "http://idaas-unit-test.example.com/i", "jwks_uri": JWKS_URI}
        )
        with self.assertRaises(DiscoveryError) as ctx:
            disc.get_issuer_jwks(ORIGIN, fetch_func=fetch)
        self.assertIn("issuer", str(ctx.exception))

    def test_jwks_uri_ssrf_metadata_ip_rejected(self):
        # SSRF：jwks_uri 指向云内网元数据地址（不同源）→ 拒绝，防订单服务沦为跳板
        fetch, _calls = make_fetch_func(
            payload={"issuer": ISSUER, "jwks_uri": "https://169.254.169.254/latest/meta-data"}
        )
        with self.assertRaises(DiscoveryError) as ctx:
            disc.get_issuer_jwks(ORIGIN, fetch_func=fetch)
        msg = str(ctx.exception)
        self.assertIn("不同源", msg)
        self.assertIn("169.254.169.254", msg)  # 消息含实际值

    def test_issuer_cross_origin_rejected(self):
        fetch, _calls = make_fetch_func(
            payload={"issuer": "https://evil.example.com/issuer", "jwks_uri": JWKS_URI}
        )
        with self.assertRaises(DiscoveryError) as ctx:
            disc.get_issuer_jwks(ORIGIN, fetch_func=fetch)
        msg = str(ctx.exception)
        self.assertIn("不同源", msg)
        self.assertIn("evil.example.com", msg)
        self.assertIn("idaas-unit-test.example.com", msg)  # 消息含期望值

    def test_issuer_with_path_prefix_accepted(self):
        # 真实部署 issuer 常带路径前缀（同 netloc）→ 必须接受，绝不因「与 ORIGIN 不全等」误杀
        issuer = ORIGIN + "/api/v2/iauths_system/oauth2"
        fetch, _calls = make_fetch_func(payload={"issuer": issuer, "jwks_uri": JWKS_URI})
        self.assertEqual(disc.get_issuer_jwks(ORIGIN, fetch_func=fetch), (issuer, JWKS_URI))

    def test_issuer_equal_to_origin_root_accepted(self):
        # issuer 恰为域名根（无路径，同 netloc）→ 合法 https URL，接受
        fetch, _calls = make_fetch_func(payload={"issuer": ORIGIN, "jwks_uri": JWKS_URI})
        self.assertEqual(disc.get_issuer_jwks(ORIGIN, fetch_func=fetch)[0], ORIGIN)

    def test_different_port_is_different_origin(self):
        # netloc 含端口：端口不同即不同源
        fetch, _calls = make_fetch_func(
            payload={"issuer": ISSUER, "jwks_uri": "https://idaas-unit-test.example.com:9999/jwks"}
        )
        with self.assertRaises(DiscoveryError):
            disc.get_issuer_jwks(ORIGIN, fetch_func=fetch)

    def test_host_case_insensitive_same_origin(self):
        # host 大小写不敏感：issuer 用大写 host 仍视为同源（netloc.lower() 比较）
        upper_issuer = "https://IDAAS-UNIT-TEST.example.com/i"
        fetch, _calls = make_fetch_func(payload={"issuer": upper_issuer, "jwks_uri": JWKS_URI})
        self.assertEqual(disc.get_issuer_jwks(ORIGIN, fetch_func=fetch)[0], upper_issuer)

    def test_malformed_issuer_url_rejected(self):
        # issuer 畸形（urlsplit 抛 ValueError）→ 包装成 DiscoveryError，不裸逃逸
        fetch, _calls = make_fetch_func(payload={"issuer": "https://[::1", "jwks_uri": JWKS_URI})
        with self.assertRaises(DiscoveryError):
            disc.get_issuer_jwks(ORIGIN, fetch_func=fetch)


# ---------------------------------------------------------------------------
# apply_discovery（仅填空位 + 返回新 dict）
# ---------------------------------------------------------------------------


class TestApplyDiscovery(DiscoveryTestCase):
    def test_fills_empty_issuer_and_jwks(self):
        config = {"IDAAS_ORIGIN": ORIGIN, "ORDER_SERVICE_ISSUER": "", "ORDER_SERVICE_JWKS_URI": ""}
        fetch, calls = make_fetch_func()
        merged = disc.apply_discovery(config, fetch_func=fetch)
        self.assertEqual(merged["ORDER_SERVICE_ISSUER"], ISSUER)
        self.assertEqual(merged["ORDER_SERVICE_JWKS_URI"], JWKS_URI)
        self.assertEqual(len(calls), 1)

    def test_original_config_not_mutated(self):
        config = {"IDAAS_ORIGIN": ORIGIN}
        fetch, _calls = make_fetch_func()
        merged = disc.apply_discovery(config, fetch_func=fetch)
        self.assertIsNot(merged, config)  # 返回新 dict（与 derive_defaults 语义一致）
        self.assertNotIn("ORDER_SERVICE_ISSUER", config)
        self.assertEqual(merged["ORDER_SERVICE_ISSUER"], ISSUER)

    def test_missing_keys_treated_as_empty(self):
        config = {"IDAAS_ORIGIN": ORIGIN}  # 完全没有 issuer/jwks 两个键
        fetch, _calls = make_fetch_func()
        merged = disc.apply_discovery(config, fetch_func=fetch)
        self.assertEqual(merged["ORDER_SERVICE_ISSUER"], ISSUER)
        self.assertEqual(merged["ORDER_SERVICE_JWKS_URI"], JWKS_URI)

    def test_placeholder_values_treated_as_empty(self):
        config = {
            "IDAAS_ORIGIN": ORIGIN,
            "ORDER_SERVICE_ISSUER": "<YOUR_ORDER_SERVICE_ISSUER>",
            "ORDER_SERVICE_JWKS_URI": "<YOUR_ORDER_SERVICE_JWKS_URI>",
        }
        fetch, _calls = make_fetch_func()
        merged = disc.apply_discovery(config, fetch_func=fetch)
        self.assertEqual(merged["ORDER_SERVICE_ISSUER"], ISSUER)
        self.assertEqual(merged["ORDER_SERVICE_JWKS_URI"], JWKS_URI)

    def test_explicit_values_win_and_skip_fetch(self):
        config = {
            "IDAAS_ORIGIN": ORIGIN,
            "ORDER_SERVICE_ISSUER": "https://explicit-issuer.example.com",
            "ORDER_SERVICE_JWKS_URI": "https://explicit-issuer.example.com/jwks",
        }
        fetch, calls = make_fetch_func()
        merged = disc.apply_discovery(config, fetch_func=fetch)
        self.assertEqual(merged, config)
        self.assertEqual(calls, [])  # 显式值齐全 → 完全不触发 discovery

    def test_partial_explicit_only_fills_gap(self):
        config = {
            "IDAAS_ORIGIN": ORIGIN,
            "ORDER_SERVICE_ISSUER": "https://explicit-issuer.example.com",
            "ORDER_SERVICE_JWKS_URI": "",
        }
        fetch, calls = make_fetch_func()
        merged = disc.apply_discovery(config, fetch_func=fetch)
        self.assertEqual(merged["ORDER_SERVICE_ISSUER"], "https://explicit-issuer.example.com")
        self.assertEqual(merged["ORDER_SERVICE_JWKS_URI"], JWKS_URI)  # 仅填空位
        self.assertEqual(len(calls), 1)

    def test_no_idaas_origin_returns_copy_without_fetch(self):
        config = {"ORDER_SERVICE_ISSUER": "", "ORDER_SERVICE_JWKS_URI": ""}
        fetch, calls = make_fetch_func()
        merged = disc.apply_discovery(config, fetch_func=fetch)
        self.assertEqual(merged, config)  # 宽容语义：留给下游 require_config 报缺项
        self.assertEqual(calls, [])

    def test_placeholder_idaas_origin_returns_copy_without_fetch(self):
        config = {"IDAAS_ORIGIN": "<YOUR_IDAAS_ORIGIN>"}
        fetch, calls = make_fetch_func()
        merged = disc.apply_discovery(config, fetch_func=fetch)
        self.assertEqual(merged, config)
        self.assertEqual(calls, [])

    def test_explicit_issuer_jwks_without_origin_ok(self):
        """向后兼容：老 .env 只有显式 issuer/jwks、没有 IDAAS_ORIGIN → 原样返回。"""
        config = {
            "ORDER_SERVICE_ISSUER": "https://legacy.example.com/issuer",
            "ORDER_SERVICE_JWKS_URI": "https://legacy.example.com/jwks",
        }
        fetch, calls = make_fetch_func()
        self.assertEqual(disc.apply_discovery(config, fetch_func=fetch), config)
        self.assertEqual(calls, [])

    def test_discovery_error_propagates(self):
        config = {"IDAAS_ORIGIN": ORIGIN}
        fetch, _calls = make_fetch_func(exc=DiscoveryError("HTTP 503"))
        with self.assertRaises(DiscoveryError) as ctx:
            disc.apply_discovery(config, fetch_func=fetch)
        self.assertIn("HTTP 503", str(ctx.exception))  # 不静默吞异常

    def test_cross_origin_discovery_error_propagates(self):
        """问题 5：apply_discovery 经 get_issuer_jwks 拒绝跨源响应（SSRF 防护贯通到回填层）。"""
        config = {"IDAAS_ORIGIN": ORIGIN}
        fetch, _calls = make_fetch_func(
            payload={"issuer": ISSUER, "jwks_uri": "https://169.254.169.254/jwks"}
        )
        with self.assertRaises(DiscoveryError):
            disc.apply_discovery(config, fetch_func=fetch)

    def test_uses_process_cache_when_no_fetch_func(self):
        config = {"IDAAS_ORIGIN": ORIGIN}
        fetch, calls = make_fetch_func()
        cache = disc.DiscoveryCache(ORIGIN, fetch_func=fetch)
        with mock.patch.object(disc, "_get_default_cache", return_value=cache) as m_get:
            first = disc.apply_discovery(config)
            second = disc.apply_discovery(config)
        m_get.assert_called_with(ORIGIN)
        self.assertEqual(first["ORDER_SERVICE_ISSUER"], ISSUER)
        self.assertEqual(second["ORDER_SERVICE_JWKS_URI"], JWKS_URI)
        self.assertEqual(len(calls), 1)  # 第二次命中内存缓存

    def test_force_refresh_bypasses_cache(self):
        config = {"IDAAS_ORIGIN": ORIGIN}
        fetch, calls = make_fetch_func()
        cache = disc.DiscoveryCache(ORIGIN, fetch_func=fetch)
        with mock.patch.object(disc, "_get_default_cache", return_value=cache):
            disc.apply_discovery(config)
            disc.apply_discovery(config, force_refresh=True)
            disc.apply_discovery(config)
        self.assertEqual(len(calls), 2)  # 仅 force_refresh 那次重拉
        self.assertEqual([c[0] for c in calls], [EXPECTED_URL, EXPECTED_URL])

    def test_force_refresh_ignored_when_explicit_values_present(self):
        config = {
            "IDAAS_ORIGIN": ORIGIN,
            "ORDER_SERVICE_ISSUER": ISSUER,
            "ORDER_SERVICE_JWKS_URI": JWKS_URI,
        }
        fetch, calls = make_fetch_func()
        cache = disc.DiscoveryCache(ORIGIN, fetch_func=fetch)
        with mock.patch.object(disc, "_get_default_cache", return_value=cache):
            merged = disc.apply_discovery(config, force_refresh=True)
        self.assertEqual(merged, config)
        self.assertEqual(calls, [])


# ---------------------------------------------------------------------------
# DiscoveryCache（TTL + 锁 + force_refresh）
# ---------------------------------------------------------------------------


class TestDiscoveryCache(DiscoveryTestCase):
    def test_ttl_hit_fetches_once(self):
        fetch, calls = make_fetch_func()
        cache = disc.DiscoveryCache(ORIGIN, fetch_func=fetch, ttl=3600)
        for _ in range(3):
            self.assertEqual(cache.get(), (ISSUER, JWKS_URI))
        self.assertEqual(len(calls), 1)

    def test_ttl_expiry_refetches(self):
        fetch, calls = make_fetch_func()
        cache = disc.DiscoveryCache(ORIGIN, fetch_func=fetch, ttl=3600)
        cache.get()
        cache._loaded_at = time.time() - 3601  # 模拟 TTL 过期（避免真实等待）
        cache.get()
        self.assertEqual(len(calls), 2)

    def test_zero_ttl_always_refetches(self):
        fetch, calls = make_fetch_func()
        cache = disc.DiscoveryCache(ORIGIN, fetch_func=fetch, ttl=0)
        cache.get()
        cache.get()
        self.assertEqual(len(calls), 2)

    def test_force_refresh_within_ttl(self):
        fetch, calls = make_fetch_func()
        cache = disc.DiscoveryCache(ORIGIN, fetch_func=fetch, ttl=3600)
        cache.get()
        cache.get(force_refresh=True)  # 验签失败清缓存重拉场景（kid-miss 强刷范式）
        cache.get()
        self.assertEqual(len(calls), 2)

    def test_clear_forces_refetch(self):
        fetch, calls = make_fetch_func()
        cache = disc.DiscoveryCache(ORIGIN, fetch_func=fetch, ttl=3600)
        cache.get()
        cache.clear()
        self.assertIsNone(cache._issuer)
        self.assertIsNone(cache._jwks_uri)
        self.assertEqual(cache._loaded_at, 0.0)
        cache.get()
        self.assertEqual(len(calls), 2)

    def test_reflects_upstream_change_after_refresh(self):
        payload = {"issuer": ISSUER, "jwks_uri": JWKS_URI}
        fetch, calls = make_fetch_func(payload=payload)
        cache = disc.DiscoveryCache(ORIGIN, fetch_func=fetch, ttl=3600)
        self.assertEqual(cache.get(), (ISSUER, JWKS_URI))
        payload["issuer"] = ORIGIN + "/rotated"  # 上游轮换（仍同源，带路径前缀）
        self.assertEqual(cache.get(), (ISSUER, JWKS_URI))  # 仍吃缓存
        self.assertEqual(cache.get(force_refresh=True)[0], ORIGIN + "/rotated")
        self.assertEqual(len(calls), 2)

    def test_error_not_cached(self):
        """拉取失败不写缓存：修复后下次 get 应重新尝试（而非缓存坏值）。"""
        fetch, calls = make_fetch_func(exc=DiscoveryError("HTTP 500"))
        cache = disc.DiscoveryCache(ORIGIN, fetch_func=fetch, ttl=3600)
        with self.assertRaises(DiscoveryError):
            cache.get()
        self.assertIsNone(cache._issuer)
        self.assertEqual(cache._loaded_at, 0.0)

    def test_cross_origin_error_not_cached(self):
        """问题 5：跨源响应被拒（DiscoveryError）且不写缓存。"""
        fetch, calls = make_fetch_func(
            payload={"issuer": ISSUER, "jwks_uri": "https://evil.example.com/jwks"}
        )
        cache = disc.DiscoveryCache(ORIGIN, fetch_func=fetch, ttl=3600)
        with self.assertRaises(DiscoveryError):
            cache.get()
        self.assertIsNone(cache._jwks_uri)
        self.assertEqual(cache._loaded_at, 0.0)

    def test_concurrent_cold_start_fetches_once(self):
        """并发冷启动只拉一次（持锁串行化，防惊群——serve-orders 多线程场景）。"""
        fetch, calls = make_fetch_func()
        cache = disc.DiscoveryCache(ORIGIN, fetch_func=fetch, ttl=3600)
        results = []
        errors = []
        barrier = threading.Barrier(8)

        def worker():
            try:
                barrier.wait(timeout=5)
                results.append(cache.get())
            except Exception as exc:  # pragma: no cover - 断言在主线程序言 errors
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for th in threads:
            th.start()
        for th in threads:
            th.join(timeout=10)
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 8)
        self.assertEqual(set(results), {(ISSUER, JWKS_URI)})
        self.assertEqual(len(calls), 1)

    def test_default_ttl_and_timeout_constants(self):
        self.assertEqual(disc.DISCOVERY_CACHE_TTL, 3600)
        cache = disc.DiscoveryCache(ORIGIN)
        self.assertEqual(cache._ttl, disc.DISCOVERY_CACHE_TTL)
        self.assertEqual(cache._timeout, disc.DEFAULT_TIMEOUT)


class TestDefaultCacheRegistry(DiscoveryTestCase):
    def test_same_origin_reuses_cache_instance(self):
        self.assertIs(disc._get_default_cache(ORIGIN), disc._get_default_cache(ORIGIN))

    def test_different_origin_gets_own_bucket(self):
        other = "https://other-instance.example.com"
        self.assertIsNot(disc._get_default_cache(ORIGIN), disc._get_default_cache(other))
        # S10：缓存 key 已归一为 (host, port) 元组（_normalize_origin 语义）
        self.assertEqual(
            set(disc._DEFAULT_CACHES),
            {("idaas-unit-test.example.com", 443), ("other-instance.example.com", 443)},
        )

    def test_registry_cache_has_no_injected_fetch(self):
        """进程级默认缓存走真实网络路径（不得携带测试注入的 fetch_func）。"""
        cache = disc._get_default_cache(ORIGIN)
        self.assertIsNone(cache._fetch_func)
        self.assertEqual(cache.idaas_origin, ORIGIN)


# ---------------------------------------------------------------------------
# 重定向防降级 handler（问题 4）
# ---------------------------------------------------------------------------


class TestRedirectHandler(unittest.TestCase):
    """``_HttpsOnlyRedirectHandler``：阻止 https→非 https 降级，放行 https→https。

    直接测 handler，不经网络。CPython 默认 ``HTTPRedirectHandler`` 白名单允许
    https→http 降级，本 handler 重写 ``redirect_request`` 堵死该降级面。
    """

    def _req(self, url="https://idaas-unit-test.example.com/x"):
        return urllib.request.Request(url, method="GET")

    def test_blocks_https_to_http_downgrade(self):
        handler = disc._HttpsOnlyRedirectHandler()
        with self.assertRaises(DiscoveryError) as ctx:
            handler.redirect_request(
                self._req(), None, 302, "Found", {}, "http://evil.example.com/"
            )
        self.assertIn("降级", str(ctx.exception))

    def test_blocks_https_to_ftp_downgrade(self):
        # 非 https 的其它 scheme（ftp 在 CPython 默认白名单内）同样阻止
        handler = disc._HttpsOnlyRedirectHandler()
        with self.assertRaises(DiscoveryError):
            handler.redirect_request(
                self._req(), None, 302, "Found", {}, "ftp://evil.example.com/"
            )

    def test_allows_https_to_https(self):
        handler = disc._HttpsOnlyRedirectHandler()
        new = handler.redirect_request(
            self._req(), None, 302, "Found", {}, "https://idaas-unit-test.example.com/y"
        )
        self.assertIsNotNone(new)  # 未被降级防护阻止，super() 正常返回新 Request

    def test_non_https_origin_not_blocked_by_guard(self):
        # 原请求非 https（生产路径不会出现，build 阶段已强制 https）→ 不触发降级防护
        handler = disc._HttpsOnlyRedirectHandler()
        try:
            handler.redirect_request(
                self._req("http://a.example.com/x"), None, 302, "Found",
                {}, "http://a.example.com/y",
            )
        except DiscoveryError:
            self.fail("原请求非 https 时不应触发降级防护")
        except Exception:  # pragma: no cover - urllib 内部细节非本测试关注点
            pass


# ---------------------------------------------------------------------------
# _default_fetch_discovery：异常白名单（问题 3）+ 最终 URL 校验（问题 4）
# ---------------------------------------------------------------------------


class TestDefaultFetchDiscovery(unittest.TestCase):
    """直接测网络层 ``_default_fetch_discovery``，用 fake opener 替换 ``_build_opener``（离线）。

    覆盖：各网络/协议异常一律包装成 ``DiscoveryError``（含问题 3 新增的
    ``http.client.HTTPException`` 与 ``ValueError``）；``decode(errors="replace")``
    让非法编码落到「不是合法 JSON」；最终 URL 必须仍是 https 且 host 一致（问题 4）。
    """

    URL = EXPECTED_URL

    def _call(self, resp=None, exc=None, timeout=5):
        self.fake = _FakeOpener(resp=resp, exc=exc)
        with mock.patch.object(disc, "_build_opener", return_value=self.fake):
            return disc._default_fetch_discovery(self.URL, timeout=timeout)

    def _ok_resp(self, payload=None, final_url=None):
        body = json.dumps(
            payload if payload is not None else {"issuer": ISSUER, "jwks_uri": JWKS_URI}
        ).encode("utf-8")
        return _FakeResponse(body=body, final_url=final_url or self.URL)

    # ---- 成功路径 ----

    def test_success_returns_dict_and_forwards_timeout(self):
        data = self._call(resp=self._ok_resp(), timeout=7)
        self.assertEqual(data["issuer"], ISSUER)
        self.assertEqual(len(self.fake.opened), 1)
        self.assertEqual(self.fake.opened[0][1], 7)  # timeout 透传给 opener.open

    # ---- 既有异常白名单（HTTPError / URLError / OSError 系）----

    def test_http_error_wrapped(self):
        exc = urllib.error.HTTPError(self.URL, 404, "Not Found", {}, None)
        with self.assertRaises(DiscoveryError) as ctx:
            self._call(exc=exc)
        self.assertIn("404", str(ctx.exception))

    def test_url_error_wrapped(self):
        with self.assertRaises(DiscoveryError) as ctx:
            self._call(exc=urllib.error.URLError("dns fail"))
        self.assertIn("网络错误", str(ctx.exception))

    def test_os_error_wrapped(self):
        with self.assertRaises(DiscoveryError) as ctx:
            self._call(exc=OSError("connection reset"))
        self.assertIn("超时/中断", str(ctx.exception))

    def test_connection_error_wrapped(self):
        with self.assertRaises(DiscoveryError):
            self._call(exc=ConnectionError("refused"))

    # ---- 问题 3 新增白名单：http.client.HTTPException / ValueError / UnicodeError ----

    def test_incomplete_read_wrapped(self):
        # IncompleteRead 是 HTTPException 子类，**不是 OSError 子类** → 旧白名单漏网
        with self.assertRaises(DiscoveryError) as ctx:
            self._call(exc=http.client.IncompleteRead(b"partial"))
        self.assertIn("IncompleteRead", str(ctx.exception))  # 消息含异常类型名

    def test_bad_status_line_wrapped(self):
        with self.assertRaises(DiscoveryError) as ctx:
            self._call(exc=http.client.BadStatusLine("garbage"))
        self.assertIn("BadStatusLine", str(ctx.exception))

    def test_invalid_url_wrapped(self):
        # InvalidURL（nonnumeric port）是 HTTPException 子类；问题 2 已在 build 阶段拦截，
        # 此处验证即便直达网络层也被兜住（双保险，不裸逃逸）
        with self.assertRaises(DiscoveryError) as ctx:
            self._call(exc=http.client.InvalidURL("nonnumeric port"))
        self.assertIn("InvalidURL", str(ctx.exception))

    def test_value_error_wrapped(self):
        with self.assertRaises(DiscoveryError) as ctx:
            self._call(exc=ValueError("bad value"))
        self.assertIn("ValueError", str(ctx.exception))

    # ---- O5：契约外异常兜底 + DiscoveryError 原样透传 ----

    def test_unexpected_runtime_error_wrapped(self):
        # O5：裸 RuntimeError 不在既有捕获矩阵内 → catch-all 兜底包装成 DiscoveryError，
        # 保留异常类型名，不让裸栈逃逸打断 DiscoveryError 接盘链。
        with self.assertRaises(DiscoveryError) as ctx:
            self._call(exc=RuntimeError("boom"))
        msg = str(ctx.exception)
        self.assertIn("RuntimeError", msg)  # 消息含异常类型名
        self.assertIn("boom", msg)          # 原因
        self.assertIn(self.URL, msg)        # url

    def test_discovery_error_passes_through_unwrapped(self):
        # O5：opener 内部抛的 DiscoveryError（如 _HttpsOnlyRedirectHandler 降级拦截）
        # 必须原样透传，不得被 catch-all 二次包装丢失原始语义。
        original = DiscoveryError("原始降级拦截语义")
        with self.assertRaises(DiscoveryError) as ctx:
            self._call(exc=original)
        self.assertIs(original, ctx.exception)  # 同一对象，未二次包装
        self.assertIn("原始降级拦截语义", str(ctx.exception))

    def test_non_utf8_body_falls_to_invalid_json(self):
        # 问题 3：errors="replace" 让非法 UTF-8（GBK/latin-1 错误页）不抛 UnicodeDecodeError，
        # 而是替换后落到「不是合法 JSON」分支（DiscoveryError，而非裸 UnicodeDecodeError 逃逸）
        body = b"<html>\xff\xfe gateway error</html>"
        with self.assertRaises(DiscoveryError) as ctx:
            self._call(resp=_FakeResponse(body=body, final_url=self.URL))
        self.assertIn("JSON", str(ctx.exception))

    # ---- JSON 结构校验 ----

    def test_invalid_json_wrapped(self):
        with self.assertRaises(DiscoveryError) as ctx:
            self._call(resp=_FakeResponse(body=b"<html>error</html>", final_url=self.URL))
        self.assertIn("JSON", str(ctx.exception))

    def test_non_dict_json_wrapped(self):
        with self.assertRaises(DiscoveryError) as ctx:
            self._call(resp=_FakeResponse(body=b'["not","dict"]', final_url=self.URL))
        self.assertIn("非 JSON 对象", str(ctx.exception))

    # ---- 问题 4：最终 URL 校验（防降级 / 防跨域重定向）----

    def test_final_url_non_https_rejected(self):
        # 双保险：即便 opener 返回的 geturl() 是 http（handler 本应已阻止），仍拒绝
        with self.assertRaises(DiscoveryError) as ctx:
            self._call(resp=self._ok_resp(final_url="http://idaas-unit-test.example.com/x"))
        self.assertIn("非 https", str(ctx.exception))

    def test_final_url_host_mismatch_rejected(self):
        # https→https 跨域重定向（host 改变）→ 拒绝，防 SSRF / 文档被换源
        with self.assertRaises(DiscoveryError) as ctx:
            self._call(resp=self._ok_resp(final_url="https://evil.example.com/x"))
        msg = str(ctx.exception)
        self.assertIn("host", msg)
        self.assertIn("evil.example.com", msg)

    def test_final_url_same_host_different_path_ok(self):
        # 同 host 的 https 重定向（仅路径变化）→ 接受
        data = self._call(resp=self._ok_resp(final_url=ORIGIN + "/redirected/path"))
        self.assertEqual(data["issuer"], ISSUER)


# ---------------------------------------------------------------------------
# W3：_normalize_origin 同源校验归一化
# ---------------------------------------------------------------------------


class TestNormalizeOrigin(DiscoveryTestCase):
    """W3：语义等价写法不被误杀，安全面不放宽。"""

    def test_explicit_443_port_same_origin(self):
        """显式 :443 与缺省端口归一为同一源。"""
        a = disc._normalize_origin("https://idaas-unit-test.example.com")
        b = disc._normalize_origin("https://idaas-unit-test.example.com:443")
        self.assertEqual(a, b)
        self.assertEqual(a, ("idaas-unit-test.example.com", 443))

    def test_trailing_dot_fqdn_same_origin(self):
        """末尾点 FQDN（DNS 语义等价）归一为同一源。"""
        a = disc._normalize_origin("https://idaas-unit-test.example.com")
        b = disc._normalize_origin("https://idaas-unit-test.example.com.")
        self.assertEqual(a, b)

    def test_punycode_same_origin(self):
        """IDNA punycode 与 Unicode 域名归一为同一源。"""
        # 例：münchen.de → xn--mnchen-3ya.de
        a = disc._normalize_origin("https://xn--mnchen-3ya.de")
        b = disc._normalize_origin("https://m\u00fcnchen.de")
        self.assertEqual(a, b)
        self.assertEqual(a[0], "xn--mnchen-3ya.de")

    def test_ipv6_same_origin(self):
        """IPv6 字面量归一：urlsplit().hostname 自动去方括号。"""
        a = disc._normalize_origin("https://[::1]:8443/path")
        self.assertIsNotNone(a)
        self.assertEqual(a, ("::1", 8443))

    def test_userinfo_stripped_same_origin(self):
        """归一后 userinfo 被 hostname 剥离，不影响同源判定。"""
        a = disc._normalize_origin("https://idaas-unit-test.example.com")
        b = disc._normalize_origin("https://user:pass@idaas-unit-test.example.com")
        self.assertEqual(a, b)

    def test_cross_host_rejected(self):
        """跨 host 仍拒绝。"""
        a = disc._normalize_origin("https://idaas-unit-test.example.com")
        b = disc._normalize_origin("https://evil.example.com")
        self.assertNotEqual(a, b)

    def test_http_rejected(self):
        """非 https 归一为 None。"""
        self.assertIsNone(disc._normalize_origin("http://idaas-unit-test.example.com"))

    def test_empty_and_invalid_return_none(self):
        """空 / 畸形 URL 归一为 None。"""
        self.assertIsNone(disc._normalize_origin(""))
        self.assertIsNone(disc._normalize_origin("not-a-url"))
        self.assertIsNone(disc._normalize_origin("https://[::1"))

    def test_different_port_is_different_origin(self):
        """非默认端口不同源。"""
        a = disc._normalize_origin("https://idaas-unit-test.example.com:443")
        b = disc._normalize_origin("https://idaas-unit-test.example.com:9999")
        self.assertNotEqual(a, b)


class TestGetIssuerJwksNormalizedOrigin(DiscoveryTestCase):
    """W3：get_issuer_jwks 同源校验用归一后的 (host, port) 比较。"""

    def test_explicit_443_issuer_accepted(self):
        """issuer 带显式 :443 与 ORIGIN（缺省端口）视为同源。"""
        issuer_443 = "https://idaas-unit-test.example.com:443/api/v2/iauths_system/oauth2"
        jwks_443 = "https://idaas-unit-test.example.com:443/api/v2/iauths_system/oauth2/jwks"
        fetch, _ = make_fetch_func(payload={"issuer": issuer_443, "jwks_uri": jwks_443})
        result = disc.get_issuer_jwks(ORIGIN, fetch_func=fetch)
        self.assertEqual(result, (issuer_443, jwks_443))

    def test_trailing_dot_fqdn_issuer_accepted(self):
        """issuer 用末尾点 FQDN 与 ORIGIN 视为同源。"""
        issuer_dot = "https://idaas-unit-test.example.com./api/v2/iauths_system/oauth2"
        jwks_dot = "https://idaas-unit-test.example.com./jwks"
        fetch, _ = make_fetch_func(payload={"issuer": issuer_dot, "jwks_uri": jwks_dot})
        result = disc.get_issuer_jwks(ORIGIN, fetch_func=fetch)
        self.assertEqual(result, (issuer_dot, jwks_dot))

    def test_punycode_issuer_accepted(self):
        """punycode issuer 与 Unicode origin 视为同源。"""
        origin_punycode = "https://xn--mnchen-3ya.de"
        issuer_unicode = "https://m\u00fcnchen.de/oauth2"
        jwks_unicode = "https://m\u00fcnchen.de/jwks"
        fetch, _ = make_fetch_func(payload={"issuer": issuer_unicode, "jwks_uri": jwks_unicode})
        result = disc.get_issuer_jwks(origin_punycode, fetch_func=fetch)
        self.assertEqual(result, (issuer_unicode, jwks_unicode))

    def test_cross_host_still_rejected_in_get_issuer_jwks(self):
        """跨 host 仍被 get_issuer_jwks 拒绝。"""
        fetch, _ = make_fetch_func(
            payload={"issuer": "https://evil.example.com/i", "jwks_uri": JWKS_URI}
        )
        with self.assertRaises(DiscoveryError) as ctx:
            disc.get_issuer_jwks(ORIGIN, fetch_func=fetch)
        self.assertIn("不同源", str(ctx.exception))


# ---------------------------------------------------------------------------
# W4：fetch_func arity 预判（Signature.bind）
# ---------------------------------------------------------------------------


class TestCallFetchFuncArity(DiscoveryTestCase):
    """W4：用 Signature.bind 做真实可绑定性预判。"""

    def test_keyword_only_timeout_raises_discovery_error(self):
        """def fetch(*, url, timeout=10) → 两种契约均不可绑定 → DiscoveryError。"""
        def fetch_kwonly(*, url, timeout=10):
            return {"issuer": ISSUER, "jwks_uri": JWKS_URI}

        with self.assertRaises(DiscoveryError) as ctx:
            disc._call_fetch_func(fetch_kwonly, "https://example.com/disc", 10)
        self.assertIn("不兼容", str(ctx.exception))

    def test_keyword_only_with_positional_url_falls_to_single_arg(self):
        """def fetch(url, *, timeout=10) → bind(url, timeout) 失败但 bind(url) 成功 → 单参调用。"""
        calls = []

        def fetch_kw_timeout(url, *, timeout=10):
            calls.append((url, timeout))
            return {"issuer": ISSUER, "jwks_uri": JWKS_URI}

        result = disc._call_fetch_func(fetch_kw_timeout, "https://example.com/disc", 5)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0], ("https://example.com/disc", 10))  # timeout 用默认值
        self.assertEqual(result["issuer"], ISSUER)

    def test_star_args_called_with_two_params(self):
        """def fetch(url, *args) → bind(url, timeout) 成功 → 双参调用且只调一次。"""
        calls = []

        def fetch_star(url, *args):
            calls.append((url, args))
            return {"issuer": ISSUER, "jwks_uri": JWKS_URI}

        result = disc._call_fetch_func(fetch_star, "https://example.com/disc", 10)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0], ("https://example.com/disc", (10,)))
        self.assertEqual(result["issuer"], ISSUER)

    def test_single_arg_func_called_without_timeout(self):
        """def fetch(url) → bind(url, timeout) 失败，bind(url) 成功 → 单参调用。"""
        calls = []

        def fetch_single(url):
            calls.append(url)
            return {"issuer": ISSUER, "jwks_uri": JWKS_URI}

        result = disc._call_fetch_func(fetch_single, "https://example.com/disc", 10)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0], "https://example.com/disc")

    def test_non_introspectable_fallback_to_two_args(self):
        """不可内省（signature 抛 TypeError/ValueError）→ 回落双参调用。"""
        calls = []
        # 模拟不可内省的 callable
        class FakeCallable:
            def __call__(self, url, timeout=10):
                calls.append((url, timeout))
                return {"issuer": ISSUER, "jwks_uri": JWKS_URI}

        obj = FakeCallable()
        with mock.patch("inspect.signature", side_effect=ValueError("no sig")):
            result = disc._call_fetch_func(obj, "https://example.com/disc", 5)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0], ("https://example.com/disc", 5))


# ---------------------------------------------------------------------------
# S1：_build_discovery_url 拒绝 userinfo@host
# ---------------------------------------------------------------------------


class TestBuildDiscoveryUrlUserinfo(DiscoveryTestCase):
    """S1：IDAAS_ORIGIN 含 user:password@ 形式应被拒绝。"""

    def test_userinfo_rejected(self):
        with self.assertRaises(DiscoveryError) as ctx:
            disc._build_discovery_url("https://admin:secret@idaas-unit-test.example.com")
        msg = str(ctx.exception)
        self.assertIn("user:password@", msg)
        self.assertIn("IDAAS_ORIGIN", msg)

    def test_username_only_rejected(self):
        with self.assertRaises(DiscoveryError) as ctx:
            disc._build_discovery_url("https://admin@idaas-unit-test.example.com")
        self.assertIn("user:password@", str(ctx.exception))

    def test_normal_origin_accepted(self):
        """正常 origin（无 userinfo）仍正常拼接。"""
        url = disc._build_discovery_url(ORIGIN)
        self.assertEqual(url, EXPECTED_URL)


# ---------------------------------------------------------------------------
# S10：缓存 key 归一化（语义等价 origin 共享缓存）
# ---------------------------------------------------------------------------


class TestDefaultCacheKeyNormalization(DiscoveryTestCase):
    """S10：语义等价写法共享同一缓存实例。"""

    def test_explicit_443_shares_cache_with_default_port(self):
        a = disc._get_default_cache("https://idaas-unit-test.example.com")
        b = disc._get_default_cache("https://idaas-unit-test.example.com:443")
        self.assertIs(a, b)

    def test_trailing_dot_shares_cache(self):
        a = disc._get_default_cache("https://idaas-unit-test.example.com")
        b = disc._get_default_cache("https://idaas-unit-test.example.com.")
        self.assertIs(a, b)

    def test_invalid_origin_falls_back_to_string_key(self):
        """归一失败（非法 origin）→ 退回原始字符串 key（不污染正常分桶）。"""
        cache = disc._get_default_cache("not-a-url")
        self.assertIn("not-a-url", disc._DEFAULT_CACHES)
        self.assertIs(cache, disc._DEFAULT_CACHES["not-a-url"])


if __name__ == "__main__":
    unittest.main()
