"""credentials 三级降级凭据链单测（全程离线，零网络）。

覆盖 ``lib/credentials.py`` 的核心契约：

- **第 1 级（显式）**：``config`` 的 ``ALIYUN_ACCESS_KEY_ID/SECRET`` **两项均**非占位
  即胜出，绝不触发 SDK / config.json（向后兼容 / CI 注入语义）；两项均占位则降级；
  **恰好一项非占位则抛 ``CredentialError``**（拒绝静默降级到可能是另一个阿里云
  账号的凭据链 —— 管控面会真实创建/删除资源）。
- **第 2 级（SDK）**：懒加载单例只构造一次；只用一次 ``get_credential()`` 取全三字段
  （不碰 3 个 deprecated getter，避免 3x provider 成本）；SDK 未装（ImportError）/
  构造失败 / 调用异常 / 返回空值 → 一律降级第 3 级，且四条失败态各自写入精确原因。
- **SDK 失败负缓存**：``get_credential()`` 异常/空值后进 TTL 30s 窗口，窗口内直接
  跳过 SDK 级（省下无凭据机器上固定 ~2.0s 的 ECS 元数据探测）且 stderr 只打一次；
  过期后重试；成功结果永不缓存。
- **第 3 级（标准库降级）**：纯 stdlib 解析 ``~/.aliyun/config.json`` 的
  AK / StsToken / OAuth 三 mode；STS 过期抛带指引的 ``CredentialError``（不做 refresh）；
  不支持的 mode / 文件缺失 / 结构非法均抛带指引错误。
- **全失败**：三级全落空抛统一 ``CredentialError``，message 含三途径下一步指引、
  第 [2] 级如实填写精确失败原因、且无双句号。
- **可观测 API**：``resolve_creds_detailed`` 返回带 ``level``/``source`` 的 namedtuple，
  而 ``resolve_creds`` 签名与行为向后兼容（前三字段逐位相等）。
- **离线探测公开 API**：``probe_explicit`` / ``probe_sdk_installed`` / ``probe_stdlib``
  与私有实现及 ``resolve_creds_detailed`` 在同级上等价（含 ``level``/``source``），
  且带无副作用护栏：不构造 SDK 客户端、不调 ``get_credential()``、不写盘、不发网络。
- **线程防护**：``_get_sdk_client`` 只对构造前后的 ``threading.enumerate()`` **差集**
  标 daemon；``ensure_daemon_threads()`` 无参时不再无差别遍历全部线程。

离线保证
--------
- SDK 一律用假 ``CredentialClient`` 类替换（``mock.patch.object``），不构造真实客户端；
- ``~/.aliyun/config.json`` 一律指向 ``tempfile`` 临时文件（通过
  ``ALIBABA_CLOUD_CLI_CONFIG_FILE`` 环境变量覆盖），基类默认把它指向**不存在**的路径，
  这样任何「意外降级」都会立刻失败而不是读到开发者本机真实凭据；
- 进程内状态（单例 ``_CRED_CLIENT``、SDK 负缓存时间戳、来源/失败记录）每个用例
  前后统一走 ``credentials._reset_caches()`` 复位，避免用例间串味；
- 负缓存 TTL 用可注入时钟 ``credentials._TIME_SOURCE`` 控制，绝不真 sleep。
"""

import builtins
import io
import json
import os
import socket
import sys
import tempfile
import threading
import unittest
import urllib.request
from contextlib import redirect_stderr
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import credentials as creds_mod  # noqa: E402
from lib.credentials import CredentialError  # noqa: E402


# ---------------------------------------------------------------------------
# 测试替身与工具
# ---------------------------------------------------------------------------

# 未来/过去时间戳（STS 过期判定用；避免依赖 datetime.now 的相对计算）
FUTURE_TS = "2099-01-01T00:00:00Z"
PAST_TS = "2000-01-01T00:00:00Z"


class FakeCredModel:
    """假 ``CredentialModel``：SDK ``get_credential()`` 的返回对象。

    ``provider_name=None`` 时**故意不提供该属性**，以覆盖旧版 SDK（v1.0.4）无此
    字段、``resolve_creds_detailed`` 必须回退人读描述的防御分支。
    """

    def __init__(self, access_key_id="", access_key_secret="", security_token=None,
                 provider_name=None):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.security_token = security_token
        if provider_name is not None:
            self.provider_name = provider_name


class FakeThread:
    """假线程对象：``daemon`` 可自由读写。

    真 ``threading.Thread`` 对已启动线程的 ``daemon`` setter 恒抛 ``RuntimeError``，
    无法在单测里构造「未启动但已在 enumerate() 差集里」的线程对象（真实语义下那是
    ``threading._limbo`` 短窗口）。用本替身可直接验证差集收敛逻辑。
    """

    def __init__(self, name, daemon=False):
        self.name = name
        self.daemon = daemon


class FakeClock:
    """可手动推进的假时钟（替掉 ``credentials._TIME_SOURCE``，避免真 sleep）。"""

    def __init__(self, start=1000.0):
        self.value = start

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


def make_fake_client_cls(model=None, exc=None, construct_exc=None):
    """构造假 ``CredentialClient`` 类 + 计数器 state（用于断言单例/调用次数）。

    - ``model``：``get_credential()`` 返回的假 CredentialModel；
    - ``exc``：``get_credential()`` 抛出的异常（模拟 SDK 内部失败 → 应降级）；
    - ``construct_exc``：``__init__`` 抛出的异常（模拟 SDK 构造失败 → 不缓存 None）；
    - deprecated getter（``get_access_key_id`` 等）一旦被调用即计数——
      ``resolve_creds`` 正确实现下该计数必须恒为 0。
    """
    state = {"constructs": 0, "get_credential_calls": 0, "deprecated_calls": 0}

    class FakeCredentialClient:
        def __init__(self):
            state["constructs"] += 1
            if construct_exc is not None:
                raise construct_exc

        def get_credential(self):
            state["get_credential_calls"] += 1
            if exc is not None:
                raise exc
            return model

        # ---- 3 个 deprecated getter：resolve_creds 绝不应调用 ----
        def get_access_key_id(self):
            state["deprecated_calls"] += 1
            return getattr(model, "access_key_id", "")

        def get_access_key_secret(self):
            state["deprecated_calls"] += 1
            return getattr(model, "access_key_secret", "")

        def get_security_token(self):
            state["deprecated_calls"] += 1
            return getattr(model, "security_token", None)

        def get_type(self):
            state["deprecated_calls"] += 1
            return "sts"

    return FakeCredentialClient, state


class CredentialsTestCase(unittest.TestCase):
    """基类：进程内状态复位 + 默认「SDK 未安装」+ config.json 指向不存在路径（离线兜底）。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        # 进程内状态复位（SDK 单例 + 负缓存时间戳 + 来源/失败记录），前后各一次
        creds_mod._reset_caches()
        self.addCleanup(creds_mod._reset_caches)
        # 默认：SDK 未安装（ImportError 语义）——需要 SDK 的用例自行再 patch 覆盖
        patcher_sdk = mock.patch.object(creds_mod, "CredentialClient", None)
        patcher_sdk.start()
        self.addCleanup(patcher_sdk.stop)
        # 默认：aliyun CLI 配置文件不存在（避免任何用例误读开发者本机真实凭据）
        self.missing_config_path = os.path.join(self._tmp.name, "no-such-config.json")
        patcher_env = mock.patch.dict(
            os.environ, {creds_mod._ALIYUN_CONFIG_PATH_ENV: self.missing_config_path}
        )
        patcher_env.start()
        self.addCleanup(patcher_env.stop)

    @staticmethod
    def _reset_singleton():
        """兼容入口：旧用例/外部引用保留，实际复位全部进程内状态。"""
        creds_mod._reset_caches()

    # ---- 工具 ----
    def write_aliyun_config(self, profiles, current="default"):
        """写一份假 ``~/.aliyun/config.json`` 到临时目录，返回路径。"""
        path = os.path.join(self._tmp.name, "config.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"current": current, "profiles": profiles}, fh)
        # 指过去：第 3 级降级路径读它（不碰真实 HOME）
        os.environ[creds_mod._ALIYUN_CONFIG_PATH_ENV] = path
        return path

    def ak_profile(self, name="default", ak="LTAfake0001", sk="sk-fake-0001"):
        return {"name": name, "mode": "AK", "access_key_id": ak, "access_key_secret": sk}

    def sts_profile(
        self,
        name="default",
        mode="StsToken",
        ak="STS.fake0001",
        sk="sk-fake-sts",
        token="sts-token-fake",
        expiration=FUTURE_TS,
    ):
        """StsToken / OAuth mode 的假 profile（含 sts_expiration）。"""
        return {
            "name": name,
            "mode": mode,
            "access_key_id": ak,
            "access_key_secret": sk,
            "sts_token": token,
            "sts_expiration": expiration,
        }


# ---------------------------------------------------------------------------
# 第 1 级：显式 AK/SK 永远最高优先
# ---------------------------------------------------------------------------


class TestExplicitLevel(CredentialsTestCase):
    def test_explicit_ak_wins_and_never_touches_lower_levels(self):
        config = {
            "ALIYUN_ACCESS_KEY_ID": "LTAfake0001",
            "ALIYUN_ACCESS_KEY_SECRET": "sk-fake-0001",
        }
        with mock.patch.object(creds_mod, "_get_sdk_client") as m_sdk:
            with mock.patch.object(creds_mod, "_creds_from_aliyun_config") as m_cfg:
                got = creds_mod.resolve_creds(config)
        self.assertEqual(got, ("LTAfake0001", "sk-fake-0001", None))
        m_sdk.assert_not_called()  # 命中第 1 级：SDK 客户端连构造都不该发生
        m_cfg.assert_not_called()

    def test_explicit_with_security_token_returns_triple(self):
        config = {
            "ALIYUN_ACCESS_KEY_ID": "STS.fake0001",
            "ALIYUN_ACCESS_KEY_SECRET": "sk-fake-sts",
            "ALIYUN_SECURITY_TOKEN": "token-fake-01",
        }
        self.assertEqual(
            creds_mod.resolve_creds(config), ("STS.fake0001", "sk-fake-sts", "token-fake-01")
        )

    def test_explicit_placeholder_token_dropped(self):
        config = {
            "ALIYUN_ACCESS_KEY_ID": "LTAfake0002",
            "ALIYUN_ACCESS_KEY_SECRET": "sk-fake-0002",
            "ALIYUN_SECURITY_TOKEN": "<YOUR_ALIYUN_SECURITY_TOKEN>",
        }
        self.assertEqual(
            creds_mod.resolve_creds(config), ("LTAfake0002", "sk-fake-0002", None)
        )

    def test_explicit_placeholder_ak_falls_through_to_sdk(self):
        config = {
            "ALIYUN_ACCESS_KEY_ID": "<YOUR_ALIYUN_ACCESS_KEY_ID>",
            "ALIYUN_ACCESS_KEY_SECRET": "<YOUR_ALIYUN_ACCESS_KEY_SECRET>",
        }
        with mock.patch.object(
            creds_mod, "_creds_from_sdk", return_value=("sdk-ak", "sdk-sk", "sdk-token")
        ) as m_sdk:
            got = creds_mod.resolve_creds(config)
        self.assertEqual(got, ("sdk-ak", "sdk-sk", "sdk-token"))
        m_sdk.assert_called_once_with()

    def test_explicit_half_filled_raises(self):
        """只填 AK 不填 SK（常见手误）→ 必须抛错，绝不静默降级。

        P0 场景：若沿用旧的 ``or`` 短路，半填与两项都没填结果完全一致，会静默
        落到 SDK/标准库凭据链 —— 而那可能是**另一个阿里云账号**的身份。本 sample
        的管控面会真实创建/删除企业身份资源，用错账号不可接受。
        """
        config = {"ALIYUN_ACCESS_KEY_ID": "LTAfake0003", "ALIYUN_ACCESS_KEY_SECRET": ""}
        with mock.patch.object(creds_mod, "_creds_from_sdk") as m_sdk:
            with mock.patch.object(creds_mod, "_creds_from_aliyun_config") as m_cfg:
                with self.assertRaises(CredentialError) as ctx:
                    creds_mod.resolve_creds(config)
        msg = str(ctx.exception)
        # 消息必须指明是哪一项缺失（本例：SK）
        self.assertIn("ALIYUN_ACCESS_KEY_SECRET", msg)
        self.assertIn("ALIYUN_ACCESS_KEY_ID", msg)
        self.assertIn("半填", msg)
        # 两条出路：补齐另一项 / 两项都清空以走 aliyun CLI 凭据链
        self.assertIn("补齐", msg)
        self.assertIn("都清空", msg)
        self.assertIn("aliyun CLI 凭据链", msg)
        # 设计意图必须写进消息（供用户理解为何不自动降级）
        self.assertIn("拒绝静默降级", msg)
        # 降级链路根本不得被触发（否则就是用错账号跑了管控面）
        m_sdk.assert_not_called()
        m_cfg.assert_not_called()

    def test_explicit_half_filled_missing_ak_raises(self):
        """镜像场景：只填 SK 不填 AK → 消息指明缺失项为 AK Id。"""
        config = {"ALIYUN_ACCESS_KEY_ID": "", "ALIYUN_ACCESS_KEY_SECRET": "sk-fake-0004"}
        with self.assertRaises(CredentialError) as ctx:
            creds_mod.resolve_creds(config)
        msg = str(ctx.exception)
        self.assertIn("ALIYUN_ACCESS_KEY_ID 缺失", msg)
        self.assertIn("ALIYUN_ACCESS_KEY_SECRET 已填写", msg)

    def test_explicit_half_filled_placeholder_counts_as_missing(self):
        """占位值等同未填：AK 真值 + SK 仍为 <YOUR_...> 模板占位 → 报错。"""
        config = {
            "ALIYUN_ACCESS_KEY_ID": "LTAfake0005",
            "ALIYUN_ACCESS_KEY_SECRET": "<YOUR_ALIYUN_ACCESS_KEY_SECRET>",
        }
        with self.assertRaises(CredentialError) as ctx:
            creds_mod.resolve_creds(config)
        self.assertIn("ALIYUN_ACCESS_KEY_SECRET", str(ctx.exception))

    def test_explicit_both_empty_falls_through_to_chain(self):
        """正向：两项都为空 → 返回 None 走降级（新推荐姿势，必须保留）。"""
        config = {"ALIYUN_ACCESS_KEY_ID": "", "ALIYUN_ACCESS_KEY_SECRET": ""}
        self.assertIsNone(creds_mod._creds_from_explicit(config))
        with mock.patch.object(
            creds_mod, "_creds_from_sdk", return_value=("sdk-ak", "sdk-sk", None)
        ) as m_sdk:
            got = creds_mod.resolve_creds(config)
        self.assertEqual(got, ("sdk-ak", "sdk-sk", None))
        m_sdk.assert_called_once_with()

    def test_explicit_both_placeholder_falls_through_to_chain(self):
        """正向：两项都是模板占位 → 同样走降级，不报错。"""
        config = {
            "ALIYUN_ACCESS_KEY_ID": "<YOUR_ALIYUN_ACCESS_KEY_ID>",
            "ALIYUN_ACCESS_KEY_SECRET": "<YOUR_ALIYUN_ACCESS_KEY_SECRET>",
        }
        self.assertIsNone(creds_mod._creds_from_explicit(config))
        with mock.patch.object(
            creds_mod, "_creds_from_sdk", return_value=("sdk-ak", "sdk-sk", None)
        ):
            self.assertEqual(
                creds_mod.resolve_creds(config), ("sdk-ak", "sdk-sk", None)
            )

    def test_creds_from_explicit_returns_none_for_empty_config(self):
        self.assertIsNone(creds_mod._creds_from_explicit({}))
        self.assertIsNone(creds_mod._creds_from_explicit({"ALIYUN_ACCESS_KEY_ID": "   "}))

    def test_explicit_detailed_level_and_source(self):
        """显式级命中：level="explicit"，source 指向 .env 变量名。"""
        config = {
            "ALIYUN_ACCESS_KEY_ID": "LTAfake0006",
            "ALIYUN_ACCESS_KEY_SECRET": "sk-fake-0006",
        }
        resolved = creds_mod.resolve_creds_detailed(config)
        self.assertEqual(resolved.level, creds_mod.LEVEL_EXPLICIT)
        self.assertEqual(resolved.level, "explicit")
        self.assertEqual(resolved.source, ".env 显式 ALIYUN_ACCESS_KEY_*")
        self.assertEqual(resolved.triple, ("LTAfake0006", "sk-fake-0006", None))


# ---------------------------------------------------------------------------
# 第 2 级：SDK 主路径（懒加载单例 + 一次 get_credential）
# ---------------------------------------------------------------------------


class TestSdkLevel(CredentialsTestCase):
    def test_sdk_triple_and_single_get_credential_call(self):
        fake_cls, state = make_fake_client_cls(
            model=FakeCredModel("sdk-ak", "sdk-sk", "sdk-token")
        )
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            got = creds_mod.resolve_creds({})
        self.assertEqual(got, ("sdk-ak", "sdk-sk", "sdk-token"))
        self.assertEqual(state["get_credential_calls"], 1)  # 一次取全三字段
        self.assertEqual(state["deprecated_calls"], 0)  # 绝不用 3 个 deprecated getter

    def test_sdk_without_token_returns_none_third_element(self):
        fake_cls, _state = make_fake_client_cls(model=FakeCredModel("sdk-ak", "sdk-sk", None))
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            self.assertEqual(creds_mod.resolve_creds({}), ("sdk-ak", "sdk-sk", None))

    def test_sdk_client_is_singleton_across_resolve_calls(self):
        """多次 resolve_creds：CredentialClient 只构造一次（避免 setup ~10 次 _call 重复实例化）。"""
        fake_cls, state = make_fake_client_cls(model=FakeCredModel("sdk-ak", "sdk-sk", None))
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            for _ in range(3):
                creds_mod.resolve_creds({})
        self.assertEqual(state["constructs"], 1)
        self.assertEqual(state["get_credential_calls"], 3)

    def test_get_sdk_client_returns_same_instance(self):
        fake_cls, state = make_fake_client_cls(model=FakeCredModel("a", "b"))
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            first = creds_mod._get_sdk_client()
            second = creds_mod._get_sdk_client()
        self.assertIs(first, second)
        self.assertEqual(state["constructs"], 1)

    def test_sdk_import_error_returns_none_client(self):
        """SDK 未安装（模块级 CredentialClient=None）→ _get_sdk_client() 恒 None。"""
        self.assertIsNone(creds_mod.CredentialClient)  # 基类默认即「未安装」
        self.assertIsNone(creds_mod._get_sdk_client())

    def test_sdk_import_error_falls_back_to_stdlib_config(self):
        self.write_aliyun_config([self.ak_profile(ak="LTAfallback1", sk="sk-fallback-1")])
        real_sdk_level = creds_mod._creds_from_sdk
        sdk_results = []

        def spy_sdk_level():
            outcome = real_sdk_level()
            sdk_results.append(outcome)
            return outcome

        with mock.patch.object(creds_mod, "_creds_from_sdk", side_effect=spy_sdk_level):
            got = creds_mod.resolve_creds({})
        self.assertEqual(got, ("LTAfallback1", "sk-fallback-1", None))
        self.assertEqual(sdk_results, [None])  # SDK 未装 → 第 2 级返回 None，不抛异常

    def test_sdk_exception_falls_back_to_stdlib_config(self):
        self.write_aliyun_config([self.ak_profile(ak="LTAfallback2", sk="sk-fallback-2")])
        fake_cls, state = make_fake_client_cls(exc=RuntimeError("boom: no provider"))
        buf = io.StringIO()
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            with redirect_stderr(buf):
                got = creds_mod.resolve_creds({})
        self.assertEqual(got, ("LTAfallback2", "sk-fallback-2", None))
        self.assertEqual(state["get_credential_calls"], 1)
        self.assertIn("降级到标准库路径", buf.getvalue())  # 降级留痕（便于排查）

    def test_sdk_empty_ak_falls_back_to_stdlib_config(self):
        self.write_aliyun_config([self.ak_profile(ak="LTAfallback3", sk="sk-fallback-3")])
        fake_cls, _state = make_fake_client_cls(model=FakeCredModel("", "", None))
        buf = io.StringIO()
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            with redirect_stderr(buf):
                got = creds_mod.resolve_creds({})
        self.assertEqual(got, ("LTAfallback3", "sk-fallback-3", None))
        self.assertIn("SDK 返回空 AK/SK", buf.getvalue())

    def test_sdk_construct_failure_not_cached(self):
        """构造失败不缓存 None：修好配置后下次调用应重新尝试构造。"""
        fake_cls, state = make_fake_client_cls(construct_exc=ValueError("bad sdk config"))
        buf = io.StringIO()
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            with redirect_stderr(buf):
                self.assertIsNone(creds_mod._get_sdk_client())
                self.assertIsNone(creds_mod._get_sdk_client())
        self.assertEqual(state["constructs"], 2)  # 未缓存 → 两次都重新构造
        self.assertIn("初始化失败", buf.getvalue())

    def test_explicit_wins_over_sdk(self):
        """第 1 级命中时，SDK 客户端连构造都不该发生。"""
        fake_cls, state = make_fake_client_cls(model=FakeCredModel("sdk-ak", "sdk-sk", None))
        config = {
            "ALIYUN_ACCESS_KEY_ID": "LTAfake0009",
            "ALIYUN_ACCESS_KEY_SECRET": "sk-fake-0009",
        }
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            got = creds_mod.resolve_creds(config)
        self.assertEqual(got, ("LTAfake0009", "sk-fake-0009", None))
        self.assertEqual(state["constructs"], 0)


# ---------------------------------------------------------------------------
# 第 3 级：标准库降级解析 ~/.aliyun/config.json
# ---------------------------------------------------------------------------


class TestStdlibConfigLevel(CredentialsTestCase):
    def test_ak_mode_returns_pair_without_token(self):
        path = self.write_aliyun_config([self.ak_profile(ak="LTAak0001", sk="sk-ak-0001")])
        self.assertEqual(
            creds_mod._creds_from_aliyun_config(path), ("LTAak0001", "sk-ak-0001", None)
        )

    def test_sts_mode_valid_returns_triple(self):
        path = self.write_aliyun_config(
            [self.sts_profile(ak="STS.sts0001", sk="sk-sts-0001", token="token-sts-0001")]
        )
        self.assertEqual(
            creds_mod._creds_from_aliyun_config(path),
            ("STS.sts0001", "sk-sts-0001", "token-sts-0001"),
        )

    def test_sts_mode_expired_raises_with_guidance(self):
        path = self.write_aliyun_config([self.sts_profile(expiration=PAST_TS)])
        with self.assertRaises(CredentialError) as ctx:
            creds_mod._creds_from_aliyun_config(path)
        msg = str(ctx.exception)
        self.assertIn("已过期", msg)
        self.assertIn("pip install alibabacloud-credentials", msg)  # 指引 1：装 SDK
        self.assertIn("aliyun configure", msg)  # 指引 2：重新登录刷新

    def test_oauth_mode_valid_returns_cached_triple(self):
        profile = self.sts_profile(
            mode="OAuth", ak="STS.oauth001", sk="sk-oauth-001", token="token-oauth-001"
        )
        profile["oauth_refresh_token"] = "refresh-fake-001"  # 降级路径不使用（不做 refresh）
        path = self.write_aliyun_config([profile])
        got = creds_mod._creds_from_aliyun_config(path)
        self.assertEqual(got, ("STS.oauth001", "sk-oauth-001", "token-oauth-001"))
        # OAuth mode 缓存的是 STS 临时凭据（access_key_id 带 STS. 前缀），第三元素必非空
        self.assertTrue(got[0].startswith("STS."))
        self.assertIsNotNone(got[2])

    def test_oauth_mode_expired_raises_with_guidance(self):
        path = self.write_aliyun_config([self.sts_profile(mode="OAuth", expiration=PAST_TS)])
        with self.assertRaises(CredentialError) as ctx:
            creds_mod._creds_from_aliyun_config(path)
        msg = str(ctx.exception)
        self.assertIn("OAuth", msg)
        self.assertIn("不做 refresh", msg)
        self.assertIn("pip install", msg)

    def test_unsupported_mode_raises_with_guidance(self):
        path = self.write_aliyun_config(
            [{"name": "default", "mode": "RamRoleArn", "access_key_id": "x", "access_key_secret": "y"}]
        )
        with self.assertRaises(CredentialError) as ctx:
            creds_mod._creds_from_aliyun_config(path)
        msg = str(ctx.exception)
        self.assertIn("RamRoleArn", msg)
        self.assertIn("不在标准库降级路径支持范围", msg)
        self.assertIn("pip install alibabacloud-credentials", msg)

    def test_missing_file_raises_with_three_way_guidance(self):
        with self.assertRaises(CredentialError) as ctx:
            creds_mod._creds_from_aliyun_config(self.missing_config_path)
        msg = str(ctx.exception)
        self.assertIn("未找到 aliyun CLI 配置文件", msg)
        self.assertIn("aliyun configure", msg)
        self.assertIn("alibabacloud-credentials", msg)
        self.assertIn("ALIYUN_ACCESS_KEY_ID", msg)

    def test_env_var_overrides_default_path(self):
        """ALIBABA_CLOUD_CLI_CONFIG_FILE 覆盖 ~/.aliyun/config.json（与 SDK 对齐）。"""
        self.write_aliyun_config([self.ak_profile(ak="LTAenvvar1", sk="sk-envvar-1")])
        self.assertEqual(creds_mod._aliyun_config_path(), os.environ[creds_mod._ALIYUN_CONFIG_PATH_ENV])
        # 不传 config_path → 走环境变量指向的临时文件（不读真实 HOME）
        self.assertEqual(
            creds_mod._creds_from_aliyun_config(), ("LTAenvvar1", "sk-envvar-1", None)
        )

    def test_invalid_json_raises(self):
        path = os.path.join(self._tmp.name, "broken.json")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("{not-json")
        with self.assertRaises(CredentialError) as ctx:
            creds_mod._creds_from_aliyun_config(path)
        self.assertIn("失败", str(ctx.exception))

    def test_top_level_not_object_raises(self):
        path = os.path.join(self._tmp.name, "list.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(["unexpected"], fh)
        with self.assertRaises(CredentialError) as ctx:
            creds_mod._creds_from_aliyun_config(path)
        self.assertIn("顶层结构非 JSON 对象", str(ctx.exception))

    def test_missing_current_raises(self):
        path = os.path.join(self._tmp.name, "no-current.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"profiles": [self.ak_profile()]}, fh)
        with self.assertRaises(CredentialError) as ctx:
            creds_mod._creds_from_aliyun_config(path)
        self.assertIn("current", str(ctx.exception))

    def test_current_profile_not_found_raises(self):
        path = self.write_aliyun_config([self.ak_profile(name="other")], current="default")
        with self.assertRaises(CredentialError) as ctx:
            creds_mod._creds_from_aliyun_config(path)
        self.assertIn("未找到 current", str(ctx.exception))

    def test_current_selects_matching_profile(self):
        path = self.write_aliyun_config(
            [
                self.ak_profile(name="first", ak="LTAfirst01", sk="sk-first-01"),
                self.ak_profile(name="second", ak="LTAsecond1", sk="sk-second-1"),
            ],
            current="second",
        )
        self.assertEqual(
            creds_mod._creds_from_aliyun_config(path), ("LTAsecond1", "sk-second-1", None)
        )

    def test_ak_mode_with_empty_values_raises(self):
        path = self.write_aliyun_config([self.ak_profile(ak="", sk="")])
        with self.assertRaises(CredentialError) as ctx:
            creds_mod._creds_from_aliyun_config(path)
        self.assertIn("为空", str(ctx.exception))

    def test_sts_mode_missing_token_raises(self):
        profile = self.sts_profile()
        profile["sts_token"] = ""
        path = self.write_aliyun_config([profile])
        with self.assertRaises(CredentialError) as ctx:
            creds_mod._creds_from_aliyun_config(path)
        self.assertIn("三件套", str(ctx.exception))

    def test_full_chain_reaches_stdlib_level(self):
        """resolve_creds 端到端：显式占位 + SDK 未装 → 命中第 3 级。"""
        self.write_aliyun_config([self.ak_profile(ak="LTAchain01", sk="sk-chain-01")])
        config = {
            "ALIYUN_ACCESS_KEY_ID": "<YOUR_ALIYUN_ACCESS_KEY_ID>",
            "ALIYUN_ACCESS_KEY_SECRET": "",
        }
        self.assertEqual(creds_mod.resolve_creds(config), ("LTAchain01", "sk-chain-01", None))


class TestStsExpirationParsing(unittest.TestCase):
    """``sts_expiration`` 解析与过期判定（时间格式差异不得误伤用户）。"""

    def test_parse_zulu_suffix(self):
        dt = creds_mod._parse_sts_expiration("2026-09-14T12:00:00Z")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.year, 2026)
        self.assertIsNotNone(dt.tzinfo)  # 必须 timezone-aware

    def test_parse_offset_suffix(self):
        dt = creds_mod._parse_sts_expiration("2026-09-14T20:00:00+08:00")
        self.assertEqual(dt.hour, 12)  # 归一到 UTC

    def test_parse_naive_treated_as_utc(self):
        dt = creds_mod._parse_sts_expiration("2026-09-14T12:00:00")
        self.assertEqual(dt.utcoffset().total_seconds(), 0)

    def test_parse_garbage_returns_none(self):
        self.assertIsNone(creds_mod._parse_sts_expiration("not-a-date"))
        self.assertIsNone(creds_mod._parse_sts_expiration(""))
        self.assertIsNone(creds_mod._parse_sts_expiration(None))

    def test_unparsable_expiration_is_lenient(self):
        """无法解析 → 视为未过期（宽容，让真实错误在 RPC 401 时暴露）。"""
        self.assertFalse(creds_mod._is_sts_expired("garbage"))
        self.assertFalse(creds_mod._is_sts_expired(None))

    def test_expired_and_future(self):
        self.assertTrue(creds_mod._is_sts_expired(PAST_TS))
        self.assertFalse(creds_mod._is_sts_expired(FUTURE_TS))


# ---------------------------------------------------------------------------
# 三级全败：统一 CredentialError + 三途径指引
# ---------------------------------------------------------------------------


class TestAllLevelsFail(CredentialsTestCase):
    def test_all_three_levels_fail_raises_unified_error(self):
        config = {
            "ALIYUN_ACCESS_KEY_ID": "<YOUR_ALIYUN_ACCESS_KEY_ID>",
            "ALIYUN_ACCESS_KEY_SECRET": "<YOUR_ALIYUN_ACCESS_KEY_SECRET>",
        }
        with self.assertRaises(CredentialError) as ctx:
            creds_mod.resolve_creds(config)
        msg = str(ctx.exception)
        self.assertIn("三级降级全部失败", msg)
        self.assertIn("[1]", msg)
        self.assertIn("[2]", msg)
        self.assertIn("[3]", msg)
        # 三途径下一步指引
        self.assertIn("pip install alibabacloud-credentials", msg)
        self.assertIn("aliyun configure", msg)
        self.assertIn("ALIYUN_ACCESS_KEY_ID", msg)
        # SDK 未安装场景：第 2 级原因标注 ImportError
        self.assertIn("未安装（ImportError）", msg)

    def test_failure_reason_marks_sdk_exception_when_installed(self):
        fake_cls, _state = make_fake_client_cls(exc=RuntimeError("boom"))
        buf = io.StringIO()
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            with redirect_stderr(buf):
                with self.assertRaises(CredentialError) as ctx:
                    creds_mod.resolve_creds({})
        self.assertIn("get_credential() 异常", str(ctx.exception))

    # ---- 聚合错误消息分级精确化（四种失败态不得混为一谈） ----

    def test_failure_reason_carries_sdk_exception_detail(self):
        """第 [2] 级必须带上 get_credential() 的**具体异常文本**，不只是「见 stderr」。"""
        fake_cls, _state = make_fake_client_cls(exc=RuntimeError("ecs metadata timeout"))
        buf = io.StringIO()
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            with redirect_stderr(buf):
                with self.assertRaises(CredentialError) as ctx:
                    creds_mod.resolve_creds({})
        self.assertIn("ecs metadata timeout", str(ctx.exception))

    def test_failure_reason_distinguishes_construct_failure(self):
        """构造失败（配置非法）必须与「未安装」/「get_credential 异常」区分开。"""
        fake_cls, _state = make_fake_client_cls(construct_exc=ValueError("bad sdk config"))
        buf = io.StringIO()
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            with redirect_stderr(buf):
                with self.assertRaises(CredentialError) as ctx:
                    creds_mod.resolve_creds({})
        msg = str(ctx.exception)
        self.assertIn("构造失败（配置非法）", msg)
        self.assertIn("bad sdk config", msg)
        # 不得退化成另外两种笼统措辞
        self.assertNotIn("未安装（ImportError）", msg)
        self.assertNotIn("get_credential() 异常", msg)

    def test_failure_reason_distinguishes_empty_ak_sk(self):
        """SDK 返回空 AK/SK 是独立失败态，不得归为「get_credential() 异常」。"""
        fake_cls, _state = make_fake_client_cls(model=FakeCredModel("", "", None))
        buf = io.StringIO()
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            with redirect_stderr(buf):
                with self.assertRaises(CredentialError) as ctx:
                    creds_mod.resolve_creds({})
        msg = str(ctx.exception)
        self.assertIn("返回空 AK/SK", msg)
        self.assertNotIn("get_credential() 异常", msg)
        self.assertNotIn("未安装（ImportError）", msg)

    def test_no_double_period_in_aggregated_message(self):
        """第 [3] 级消息自带句尾「。」，模板不得再补一个（实测曾输出「。。」）。"""
        with self.assertRaises(CredentialError) as ctx:
            creds_mod.resolve_creds({})
        msg = str(ctx.exception)
        self.assertNotIn("。。", msg)
        self.assertNotIn("..", msg)
        # 确实命中了自带句号的多行降级指引（即双句号的诱发场景）
        self.assertIn("（最高优先）。", msg)

    def test_one_period_helper_normalizes_trailing_punctuation(self):
        """_one_period 归一化：句尾句号/尾空白被剔除，交由模板补唯一一个。

        前导空白与内部换行必须**原样保留**（多行降级指引的缩进不能丢）。
        """
        self.assertEqual(creds_mod._one_period("abc。"), "abc")
        self.assertEqual(creds_mod._one_period("abc."), "abc")
        self.assertEqual(creds_mod._one_period("abc。。"), "abc")
        self.assertEqual(creds_mod._one_period("abc.。."), "abc")
        self.assertEqual(creds_mod._one_period("abc"), "abc")
        self.assertEqual(creds_mod._one_period("abc。  \n"), "abc")
        # 退化输入：全是句号不得被吃空（至少保留一个句号）
        self.assertEqual(creds_mod._one_period("..."), ".")
        self.assertEqual(creds_mod._one_period("。。。"), "。")
        self.assertEqual(creds_mod._one_period(""), "")
        self.assertEqual(creds_mod._one_period("   "), "")
        # 多行文本：只动句尾，不动换行与缩进
        self.assertEqual(
            creds_mod._one_period("首行\n  1) 次行（最高优先）。"),
            "首行\n  1) 次行（最高优先）",
        )

    def test_error_type_is_credential_error_for_callers(self):
        """调用方（flow/control_plane）依赖 CredentialError 类型做统一错误出口。"""
        with self.assertRaises(CredentialError):
            creds_mod.resolve_creds({})
        self.assertTrue(issubclass(CredentialError, Exception))


# ---------------------------------------------------------------------------
# 可观测 API：resolve_creds_detailed 返回命中级别与来源（sample.py --check 依赖）
# ---------------------------------------------------------------------------


class TestResolveCredsDetailed(CredentialsTestCase):
    """``resolve_creds_detailed`` 契约（下游 ``sample.py --check`` 照此对接）。

    改造前 ``sample.py`` 只能用 ``creds[0].startswith("STS.")`` 猜级别，区分不出
    SDK 与标准库路径；本组用例锁定新的可观测字段。
    """

    def test_namedtuple_field_order_and_names(self):
        """字段名与顺序是对外契约，不得随意调整。"""
        self.assertEqual(
            creds_mod.ResolvedCreds._fields,
            ("access_key_id", "access_key_secret", "security_token", "level", "source"),
        )

    def test_level_constants_are_stable_strings(self):
        """level 取值域（下游可能直接字符串比较）。"""
        self.assertEqual(creds_mod.LEVEL_EXPLICIT, "explicit")
        self.assertEqual(creds_mod.LEVEL_SDK, "sdk")
        self.assertEqual(creds_mod.LEVEL_STDLIB, "stdlib")

    def test_sdk_level_source_uses_provider_name(self):
        """SDK 级优先用 CredentialModel.provider_name 作来源。"""
        fake_cls, _state = make_fake_client_cls(
            model=FakeCredModel(
                "sdk-ak", "sdk-sk", "sdk-token",
                provider_name="CliProfileCredentialsProvider",
            )
        )
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            resolved = creds_mod.resolve_creds_detailed({})
        self.assertEqual(resolved.level, "sdk")
        self.assertEqual(resolved.source, "CliProfileCredentialsProvider")
        self.assertEqual(resolved.access_key_id, "sdk-ak")
        self.assertEqual(resolved.access_key_secret, "sdk-sk")
        self.assertEqual(resolved.security_token, "sdk-token")

    def test_sdk_level_source_falls_back_when_provider_name_absent(self):
        """旧版 SDK 无 provider_name 字段 → 防御式 getattr 回退人读描述。"""
        fake_cls, _state = make_fake_client_cls(
            model=FakeCredModel("sdk-ak", "sdk-sk", None)  # 故意不带 provider_name
        )
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            resolved = creds_mod.resolve_creds_detailed({})
        self.assertEqual(resolved.level, "sdk")
        self.assertEqual(resolved.source, "alibabacloud_credentials 默认链")

    def test_stdlib_level_source_includes_profile_and_mode(self):
        """标准库级来源带上 profile 名与 mode（便于用户定位到底读了哪个 profile）。"""
        self.write_aliyun_config(
            [self.ak_profile(name="prod", ak="LTAstd0001", sk="sk-std-0001")], current="prod"
        )
        resolved = creds_mod.resolve_creds_detailed({})
        self.assertEqual(resolved.level, "stdlib")
        self.assertEqual(resolved.source, "~/.aliyun/config.json(profile=prod, mode=AK)")
        self.assertEqual(resolved.triple, ("LTAstd0001", "sk-std-0001", None))

    def test_stdlib_level_source_for_oauth_mode(self):
        self.write_aliyun_config(
            [self.sts_profile(mode="OAuth", ak="STS.det0001", sk="sk-det", token="tk-det")]
        )
        resolved = creds_mod.resolve_creds_detailed({})
        self.assertEqual(resolved.level, "stdlib")
        self.assertIn("mode=OAuth", resolved.source)
        self.assertEqual(resolved.security_token, "tk-det")

    def test_backward_compat_resolve_creds_equals_first_three_fields(self):
        """向后兼容硬约束：resolve_creds 与 detailed 的前三字段逐位相等。"""
        self.write_aliyun_config([self.ak_profile(ak="LTAcompat1", sk="sk-compat-1")])
        plain = creds_mod.resolve_creds({})
        creds_mod._reset_caches()
        detailed = creds_mod.resolve_creds_detailed({})
        self.assertEqual(plain, tuple(detailed)[:3])
        self.assertEqual(plain, detailed.triple)
        self.assertEqual(len(plain), 3)  # 签名不得变长（下游按三元组解包）

    def test_resolve_creds_returns_plain_tuple_not_namedtuple(self):
        """resolve_creds 必须返回裸 tuple（不得泄漏 ResolvedCreds 类型给旧调用方）。"""
        config = {
            "ALIYUN_ACCESS_KEY_ID": "LTAplain01",
            "ALIYUN_ACCESS_KEY_SECRET": "sk-plain-01",
        }
        got = creds_mod.resolve_creds(config)
        self.assertIs(type(got), tuple)
        ak, sk, token = got  # 三元组解包必须照旧可用
        self.assertEqual((ak, sk, token), ("LTAplain01", "sk-plain-01", None))

    def test_detailed_raises_same_errors_as_plain(self):
        """两个入口异常语义一致：三级全败均抛 CredentialError。"""
        with self.assertRaises(CredentialError):
            creds_mod.resolve_creds_detailed({})
        creds_mod._reset_caches()
        with self.assertRaises(CredentialError):
            creds_mod.resolve_creds({})

    def test_detailed_half_filled_raises_before_touching_chain(self):
        """detailed 入口同样拒绝半填静默降级。"""
        config = {"ALIYUN_ACCESS_KEY_ID": "LTAhalf001", "ALIYUN_ACCESS_KEY_SECRET": ""}
        with mock.patch.object(creds_mod, "_creds_from_sdk") as m_sdk:
            with self.assertRaises(CredentialError):
                creds_mod.resolve_creds_detailed(config)
        m_sdk.assert_not_called()


# ---------------------------------------------------------------------------
# 离线探测公开 API（probe_* 三件套）：sample.py --check 的唯一对接面
# ---------------------------------------------------------------------------


class TestOfflineProbeApi(CredentialsTestCase):
    """``probe_explicit`` / ``probe_sdk_installed`` / ``probe_stdlib`` 契约。

    三件套是给**离线体检**（``sample.py --check`` 默认口径）用的公开只读探测 API，
    取代 sample.py 直接调用私有 helper（``_creds_from_explicit`` /
    ``_creds_from_aliyun_config`` / 模块级 ``_LAST_STDLIB_SOURCE`` /
    ``CredentialClient``）的不良耦合。本组用例锁定四件事：

    (a) 与私有实现 / ``resolve_creds_detailed`` 在同级上**等价**（含 level/source）；
    (b) ``probe_sdk_installed()`` 的 True/False 两分支；
    (c) ``probe_explicit`` 的异常语义（半填抛 ``CredentialError``、两项均缺返回 ``None``）；
    (d) **无副作用护栏**：不构造 SDK 客户端、不调 ``get_credential()``、不写盘、不发网络。
    """

    # ---- 工具 ----
    @staticmethod
    def _read_bytes(path):
        with open(path, "rb") as fh:
            return fh.read()

    # ---- (a) 等价性：第 1 级 ----
    def test_probe_explicit_equals_detailed_on_explicit_level(self):
        """命中显式级：probe_explicit 与 resolve_creds_detailed 返回**全字段相等**。"""
        config = {
            "ALIYUN_ACCESS_KEY_ID": "LTAprobe01",
            "ALIYUN_ACCESS_KEY_SECRET": "sk-probe-01",
        }
        probed = creds_mod.probe_explicit(config)
        detailed = creds_mod.resolve_creds_detailed(config)
        self.assertIsInstance(probed, creds_mod.ResolvedCreds)
        self.assertEqual(probed, detailed)  # namedtuple 逐位相等（含 level/source）
        self.assertEqual(probed.level, creds_mod.LEVEL_EXPLICIT)
        self.assertEqual(probed.level, "explicit")
        self.assertEqual(probed.source, ".env 显式 ALIYUN_ACCESS_KEY_*")
        # 与私有实现同口径（薄委托，不得有第二份判定逻辑）
        self.assertEqual(probed.triple, creds_mod._creds_from_explicit(config))

    def test_probe_explicit_carries_security_token(self):
        config = {
            "ALIYUN_ACCESS_KEY_ID": "STS.probe02",
            "ALIYUN_ACCESS_KEY_SECRET": "sk-probe-sts",
            "ALIYUN_SECURITY_TOKEN": "token-probe-01",
        }
        probed = creds_mod.probe_explicit(config)
        self.assertEqual(probed.triple, ("STS.probe02", "sk-probe-sts", "token-probe-01"))
        self.assertEqual(probed.security_token, "token-probe-01")

    def test_probe_explicit_drops_placeholder_token(self):
        """占位 STS token 必须被丢弃（与真实解析路径一致）。"""
        config = {
            "ALIYUN_ACCESS_KEY_ID": "LTAprobe03",
            "ALIYUN_ACCESS_KEY_SECRET": "sk-probe-03",
            "ALIYUN_SECURITY_TOKEN": "<YOUR_ALIYUN_SECURITY_TOKEN>",
        }
        probed = creds_mod.probe_explicit(config)
        self.assertIsNone(probed.security_token)
        self.assertEqual(probed.triple, creds_mod._creds_from_explicit(config))

    def test_probe_explicit_never_touches_lower_levels(self):
        """护栏：探测第 1 级不得推进降级链（不碰 SDK、不读 config.json）。"""
        config = {
            "ALIYUN_ACCESS_KEY_ID": "LTAprobe04",
            "ALIYUN_ACCESS_KEY_SECRET": "sk-probe-04",
        }
        fake_cls, state = make_fake_client_cls(model=FakeCredModel("sdk-ak", "sdk-sk", None))
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls), \
                mock.patch.object(creds_mod, "_creds_from_sdk") as m_sdk, \
                mock.patch.object(creds_mod, "_creds_from_aliyun_config") as m_cfg:
            probed = creds_mod.probe_explicit(config)
        self.assertEqual(probed.level, creds_mod.LEVEL_EXPLICIT)
        m_sdk.assert_not_called()
        m_cfg.assert_not_called()
        self.assertEqual(state["constructs"], 0)

    # ---- (c) 异常语义：半填 / 两项均缺 ----
    def test_probe_explicit_returns_none_when_both_missing(self):
        """两项均缺/占位/纯空白 → ``None``（本级不可用，交凭据链降级）。"""
        cases = [
            {},
            {"ALIYUN_ACCESS_KEY_ID": "", "ALIYUN_ACCESS_KEY_SECRET": ""},
            {"ALIYUN_ACCESS_KEY_ID": "   "},
            {
                "ALIYUN_ACCESS_KEY_ID": "<YOUR_ALIYUN_ACCESS_KEY_ID>",
                "ALIYUN_ACCESS_KEY_SECRET": "<YOUR_ALIYUN_ACCESS_KEY_SECRET>",
            },
        ]
        for config in cases:
            self.assertIsNone(creds_mod.probe_explicit(config))
            # 与私有实现逐项同口径
            self.assertIsNone(creds_mod._creds_from_explicit(config))

    def test_probe_explicit_half_fill_raises_same_message_as_resolve(self):
        """硬约束：半填必须抛 ``CredentialError``，且 message 与真实解析路径逐字相同。

        ``--check`` 靠这个异常把配置错误暴露给用户；若 probe 静默返回 ``None``，
        半填（可能是另一个阿里云账号）就会被体检当成「未填」放过去。
        """
        config = {"ALIYUN_ACCESS_KEY_ID": "LTAprobe05", "ALIYUN_ACCESS_KEY_SECRET": ""}
        with mock.patch.object(creds_mod, "_get_sdk_client") as m_client, \
                mock.patch.object(creds_mod, "_creds_from_aliyun_config") as m_cfg:
            with self.assertRaises(CredentialError) as ctx_probe:
                creds_mod.probe_explicit(config)
            with self.assertRaises(CredentialError) as ctx_private:
                creds_mod._creds_from_explicit(config)
        with self.assertRaises(CredentialError) as ctx_resolve:
            creds_mod.resolve_creds(config)
        with self.assertRaises(CredentialError) as ctx_detailed:
            creds_mod.resolve_creds_detailed(config)
        msg = str(ctx_probe.exception)
        self.assertEqual(msg, str(ctx_private.exception))
        self.assertEqual(msg, str(ctx_resolve.exception))
        self.assertEqual(msg, str(ctx_detailed.exception))
        self.assertIn("半填", msg)
        self.assertIn("ALIYUN_ACCESS_KEY_SECRET", msg)
        self.assertIn("拒绝静默降级", msg)
        # 抛错前绝不得触碰降级链
        m_client.assert_not_called()
        m_cfg.assert_not_called()

    def test_probe_explicit_half_fill_missing_ak_raises(self):
        """镜像场景：只填 SK 不填 AK → 消息指明缺失项为 AK Id。"""
        config = {"ALIYUN_ACCESS_KEY_ID": "", "ALIYUN_ACCESS_KEY_SECRET": "sk-probe-06"}
        with self.assertRaises(CredentialError) as ctx:
            creds_mod.probe_explicit(config)
        msg = str(ctx.exception)
        self.assertIn("ALIYUN_ACCESS_KEY_ID 缺失", msg)
        self.assertIn("ALIYUN_ACCESS_KEY_SECRET 已填写", msg)

    def test_probe_explicit_half_fill_placeholder_counts_as_missing(self):
        config = {
            "ALIYUN_ACCESS_KEY_ID": "LTAprobe07",
            "ALIYUN_ACCESS_KEY_SECRET": "<YOUR_ALIYUN_ACCESS_KEY_SECRET>",
        }
        with self.assertRaises(CredentialError) as ctx:
            creds_mod.probe_explicit(config)
        self.assertIn("ALIYUN_ACCESS_KEY_SECRET", str(ctx.exception))

    # ---- (b) SDK 安装态两分支 + 护栏 ----
    def test_probe_sdk_installed_false_when_import_failed(self):
        """基类已 patch ``CredentialClient=None``（等价于 ImportError 场景）。"""
        self.assertIsNone(creds_mod.CredentialClient)
        self.assertIs(creds_mod.probe_sdk_installed(), False)  # 必须返回真 bool

    def test_probe_sdk_installed_true_when_client_class_present(self):
        fake_cls, _state = make_fake_client_cls(model=FakeCredModel("sdk-ak", "sdk-sk", None))
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            self.assertIs(creds_mod.probe_sdk_installed(), True)

    def test_probe_sdk_installed_never_constructs_client(self):
        """护栏：构造 ``CredentialClient()`` 会 eager 建整条 provider 链并可能探 ECS 元数据。"""
        fake_cls, state = make_fake_client_cls(model=FakeCredModel("sdk-ak", "sdk-sk", None))
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls), \
                mock.patch.object(creds_mod, "_get_sdk_client") as m_get, \
                mock.patch.object(creds_mod, "_creds_from_sdk") as m_sdk:
            self.assertIs(creds_mod.probe_sdk_installed(), True)
        self.assertEqual(state["constructs"], 0)  # 绝不构造客户端
        self.assertEqual(state["get_credential_calls"], 0)  # 绝不调 get_credential()
        self.assertEqual(state["deprecated_calls"], 0)
        m_get.assert_not_called()
        m_sdk.assert_not_called()
        self.assertIsNone(creds_mod._CRED_CLIENT)  # 单例未被建立

    def test_probe_sdk_installed_does_not_touch_failure_cache(self):
        """护栏：只读安装态，不得写入 SDK 失败记录 / 负缓存时间戳。"""
        fake_cls, _state = make_fake_client_cls(model=FakeCredModel("sdk-ak", "sdk-sk", None))
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            creds_mod.probe_sdk_installed()
        self.assertIsNone(creds_mod._LAST_SDK_FAILURE)
        self.assertIsNone(creds_mod._SDK_FAILED_AT)
        self.assertIs(creds_mod._sdk_negative_cache_active(), False)

    # ---- (a) 等价性：第 3 级 ----
    def test_probe_stdlib_equals_detailed_on_stdlib_level(self):
        """命中标准库级：probe_stdlib 与 resolve_creds_detailed 返回**全字段相等**。"""
        self.write_aliyun_config(
            [self.ak_profile(name="prod", ak="LTAprobe08", sk="sk-probe-08")], current="prod"
        )
        probed = creds_mod.probe_stdlib()
        detailed = creds_mod.resolve_creds_detailed({})
        self.assertIsInstance(probed, creds_mod.ResolvedCreds)
        self.assertEqual(probed, detailed)
        self.assertEqual(probed.level, creds_mod.LEVEL_STDLIB)
        self.assertEqual(probed.level, "stdlib")
        self.assertEqual(probed.source, "~/.aliyun/config.json(profile=prod, mode=AK)")
        self.assertEqual(probed.triple, ("LTAprobe08", "sk-probe-08", None))

    def test_probe_stdlib_source_matches_private_last_stdlib_source(self):
        """``source`` 自带 profile/mode —— 调用方无需再读模块级私有变量。"""
        path = self.write_aliyun_config(
            [self.sts_profile(ak="STS.probe09", sk="sk-probe-sts", token="tk-probe")]
        )
        probed = creds_mod.probe_stdlib()
        self.assertEqual(probed.triple, creds_mod._creds_from_aliyun_config(path))
        self.assertEqual(probed.source, creds_mod._LAST_STDLIB_SOURCE)
        self.assertIn("profile=default", probed.source)
        self.assertIn("mode=StsToken", probed.source)

    def test_probe_stdlib_source_not_polluted_by_previous_resolution(self):
        """护栏：上一次解析留下的来源不得泄漏到本次 probe 结果（先清后取）。"""
        self.write_aliyun_config(
            [self.ak_profile(name="first", ak="LTAprobe13", sk="sk-probe-13")],
            current="first",
        )
        previous = creds_mod.resolve_creds_detailed({})
        self.assertIn("profile=first", previous.source)  # 先把来源写成 first
        # 换一份配置（profile 名不同）再 probe：source 必须反映本次 profile
        self.write_aliyun_config(
            [self.ak_profile(name="second", ak="LTAprobe14", sk="sk-probe-14")],
            current="second",
        )
        probed = creds_mod.probe_stdlib()
        self.assertIn("profile=second", probed.source)
        self.assertNotIn("profile=first", probed.source)
        self.assertEqual(probed.triple, ("LTAprobe14", "sk-probe-14", None))

    def test_probe_stdlib_source_falls_back_when_delegate_does_not_set_it(self):
        """委托方（如被 mock 的私有 helper）未写来源时，回退通用描述而非残留值。"""
        creds_mod._LAST_STDLIB_SOURCE = "~/.aliyun/config.json(profile=stale, mode=AK)"
        with mock.patch.object(
            creds_mod, "_creds_from_aliyun_config",
            return_value=("LTAprobe15", "sk-probe-15", None),
        ):
            probed = creds_mod.probe_stdlib()
        self.assertEqual(probed.source, "~/.aliyun/config.json")
        self.assertEqual(probed.level, creds_mod.LEVEL_STDLIB)
        self.assertEqual(probed.triple, ("LTAprobe15", "sk-probe-15", None))

    def test_probe_stdlib_oauth_mode_source(self):
        self.write_aliyun_config(
            [self.sts_profile(mode="OAuth", ak="STS.probe10", sk="sk-probe-oauth",
                              token="tk-probe-oauth")]
        )
        probed = creds_mod.probe_stdlib()
        self.assertIn("mode=OAuth", probed.source)
        self.assertEqual(probed.security_token, "tk-probe-oauth")

    def test_probe_stdlib_never_touches_sdk(self):
        """护栏：探测第 3 级不得回跳去构造 SDK 客户端。"""
        self.write_aliyun_config([self.ak_profile(ak="LTAprobe11", sk="sk-probe-11")])
        fake_cls, state = make_fake_client_cls(model=FakeCredModel("sdk-ak", "sdk-sk", None))
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls), \
                mock.patch.object(creds_mod, "_creds_from_sdk") as m_sdk:
            probed = creds_mod.probe_stdlib()
        self.assertEqual(probed.level, creds_mod.LEVEL_STDLIB)
        m_sdk.assert_not_called()
        self.assertEqual(state["constructs"], 0)
        self.assertEqual(state["get_credential_calls"], 0)

    def test_probe_stdlib_expired_raises_same_message_as_private(self):
        """STS 过期：抛错且 message 与私有实现逐字相同（含两条刷新指引）。"""
        self.write_aliyun_config([self.sts_profile(mode="OAuth", expiration=PAST_TS)])
        with self.assertRaises(CredentialError) as ctx_probe:
            creds_mod.probe_stdlib()
        with self.assertRaises(CredentialError) as ctx_private:
            creds_mod._creds_from_aliyun_config()
        msg = str(ctx_probe.exception)
        self.assertEqual(msg, str(ctx_private.exception))
        self.assertIn("已过期", msg)
        self.assertIn("不做 refresh", msg)
        self.assertIn("pip install alibabacloud-credentials", msg)

    def test_probe_stdlib_missing_file_raises_same_message_as_private(self):
        """基类默认把 CLI 配置指向**不存在**路径（绝不读真实 HOME）。"""
        with self.assertRaises(CredentialError) as ctx_probe:
            creds_mod.probe_stdlib()
        with self.assertRaises(CredentialError) as ctx_private:
            creds_mod._creds_from_aliyun_config()
        msg = str(ctx_probe.exception)
        self.assertEqual(msg, str(ctx_private.exception))
        self.assertIn("未找到 aliyun CLI 配置文件", msg)

    def test_probe_stdlib_unsupported_mode_raises(self):
        self.write_aliyun_config(
            [{"name": "default", "mode": "RamRoleArn", "access_key_id": "x",
              "access_key_secret": "y"}]
        )
        with self.assertRaises(CredentialError) as ctx:
            creds_mod.probe_stdlib()
        self.assertIn("不在标准库降级路径支持范围", str(ctx.exception))

    # ---- (d) 无副作用护栏：不写盘 / 不发网络 ----
    def test_probe_stdlib_is_read_only_no_write_no_network(self):
        """护栏：``probe_stdlib()`` 只读 —— 不写盘、不发网络、不做 refresh。"""
        path = self.write_aliyun_config(
            [self.sts_profile(ak="STS.probe12", sk="sk-probe-sts", token="tk-probe")]
        )
        before_bytes = self._read_bytes(path)
        before_mtime = os.path.getmtime(path)
        before_listing = sorted(os.listdir(self._tmp.name))
        real_open = builtins.open
        opened_modes = []

        def spy_open(file, mode="r", *args, **kwargs):
            opened_modes.append(str(mode))
            return real_open(file, mode, *args, **kwargs)

        with mock.patch.object(socket, "socket") as m_sock, \
                mock.patch.object(socket, "create_connection") as m_conn, \
                mock.patch.object(socket, "getaddrinfo") as m_dns, \
                mock.patch.object(urllib.request, "urlopen") as m_url, \
                mock.patch("builtins.open", side_effect=spy_open):
            probed = creds_mod.probe_stdlib()
        self.assertEqual(probed.triple, ("STS.probe12", "sk-probe-sts", "tk-probe"))
        # 只读：所有 open 调用的 mode 不得含任何写标记
        self.assertTrue(opened_modes, "probe_stdlib 应至少读一次配置文件")
        for mode in opened_modes:
            for write_flag in ("w", "a", "x", "+"):
                self.assertNotIn(write_flag, mode, "probe_stdlib 以写模式打开了文件：{}".format(mode))
        # 未写盘：内容 / mtime / 目录清单均不变
        self.assertEqual(self._read_bytes(path), before_bytes)
        self.assertEqual(os.path.getmtime(path), before_mtime)
        self.assertEqual(sorted(os.listdir(self._tmp.name)), before_listing)
        # 未发网络：socket / DNS / urlopen 全部未被调用
        m_sock.assert_not_called()
        m_conn.assert_not_called()
        m_dns.assert_not_called()
        m_url.assert_not_called()

    # ---- 公开性与文档契约 ----
    def test_probe_api_is_public_and_documented(self):
        """三件套必须是公开名字（无下划线前缀）且带 docstring —— 它们是对外契约。"""
        for name in ("probe_explicit", "probe_sdk_installed", "probe_stdlib"):
            func = getattr(creds_mod, name, None)
            self.assertTrue(callable(func), "{} 不存在或不可调用".format(name))
            self.assertFalse(name.startswith("_"))
            self.assertTrue((func.__doc__ or "").strip(), "{} 缺少 docstring".format(name))

    def test_module_docstring_documents_probe_trio_split(self):
        """模块 docstring 必须写清 probe_*（离线体检）与 resolve_*（真实解析）的分工。"""
        doc = creds_mod.__doc__ or ""
        for token in (
            "probe_explicit", "probe_sdk_installed", "probe_stdlib",
            "resolve_creds_detailed", "离线体检", "get_credential",
        ):
            self.assertIn(token, doc)


# ---------------------------------------------------------------------------
# SDK 失败负缓存：无凭据机器上不再每次解析都付 ~2.0s ECS 元数据探测
# ---------------------------------------------------------------------------


class TestSdkFailureNegativeCache(CredentialsTestCase):
    """负缓存只记「SDK 路径已尝试且失败」这一事实，TTL 30s。

    成功结果**绝不缓存**（否则破坏 SDK 的 STS 到期自动刷新语义）。
    时钟用可注入的 ``_TIME_SOURCE`` 替身，全程不真 sleep。
    """

    def test_repeated_failure_calls_sdk_only_once_within_ttl(self):
        """TTL 窗口内连续三次解析：SDK 只被探一次（省下 2×~2.0s）。"""
        self.write_aliyun_config([self.ak_profile(ak="LTAnc00001", sk="sk-nc-0001")])
        fake_cls, state = make_fake_client_cls(exc=RuntimeError("ecs metadata timeout"))
        clock = FakeClock()
        buf = io.StringIO()
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            with mock.patch.object(creds_mod, "_TIME_SOURCE", clock):
                with redirect_stderr(buf):
                    for _ in range(3):
                        got = creds_mod.resolve_creds({})
        self.assertEqual(got, ("LTAnc00001", "sk-nc-0001", None))
        self.assertEqual(state["get_credential_calls"], 1)  # 后两次直接跳过 SDK 级
        # stderr 降级日志在同一 TTL 窗口内只打一次
        self.assertEqual(buf.getvalue().count("降级到标准库路径"), 1)

    def test_empty_ak_sk_also_enters_negative_cache(self):
        """返回空 AK/SK 同样已付完整链路成本，必须进负缓存。"""
        self.write_aliyun_config([self.ak_profile(ak="LTAnc00002", sk="sk-nc-0002")])
        fake_cls, state = make_fake_client_cls(model=FakeCredModel("", "", None))
        clock = FakeClock()
        buf = io.StringIO()
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            with mock.patch.object(creds_mod, "_TIME_SOURCE", clock):
                with redirect_stderr(buf):
                    for _ in range(3):
                        creds_mod.resolve_creds({})
        self.assertEqual(state["get_credential_calls"], 1)
        self.assertEqual(buf.getvalue().count("SDK 返回空 AK/SK"), 1)

    def test_cache_expires_after_ttl_and_retries_sdk(self):
        """TTL 过期 → 重新尝试 SDK（给用户修复凭据后自动恢复的机会）。"""
        self.write_aliyun_config([self.ak_profile(ak="LTAnc00003", sk="sk-nc-0003")])
        fake_cls, state = make_fake_client_cls(exc=RuntimeError("boom"))
        clock = FakeClock()
        buf = io.StringIO()
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            with mock.patch.object(creds_mod, "_TIME_SOURCE", clock):
                with redirect_stderr(buf):
                    creds_mod.resolve_creds({})
                    self.assertEqual(state["get_credential_calls"], 1)
                    clock.advance(creds_mod.SDK_FAILURE_NEGATIVE_TTL + 1.0)
                    creds_mod.resolve_creds({})
        self.assertEqual(state["get_credential_calls"], 2)  # 过期后重试
        self.assertEqual(buf.getvalue().count("降级到标准库路径"), 2)

    def test_cache_still_active_just_before_ttl(self):
        """边界：TTL 未到时仍命中负缓存（严格小于比较）。"""
        self.write_aliyun_config([self.ak_profile(ak="LTAnc00004", sk="sk-nc-0004")])
        fake_cls, state = make_fake_client_cls(exc=RuntimeError("boom"))
        clock = FakeClock()
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            with mock.patch.object(creds_mod, "_TIME_SOURCE", clock):
                with redirect_stderr(io.StringIO()):
                    creds_mod.resolve_creds({})
                    clock.advance(creds_mod.SDK_FAILURE_NEGATIVE_TTL - 0.5)
                    creds_mod.resolve_creds({})
        self.assertEqual(state["get_credential_calls"], 1)

    def test_success_is_never_cached(self):
        """成功结果不得缓存：否则 SDK 的 STS 到期自动刷新语义被破坏。"""
        fake_cls, state = make_fake_client_cls(model=FakeCredModel("sdk-ak", "sdk-sk", None))
        clock = FakeClock()
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            with mock.patch.object(creds_mod, "_TIME_SOURCE", clock):
                for _ in range(3):
                    creds_mod.resolve_creds({})
        self.assertEqual(state["get_credential_calls"], 3)  # 每次都真取（SDK 内部自己缓存）
        self.assertIsNone(creds_mod._SDK_FAILED_AT)  # 成功不进负缓存

    def test_sdk_not_installed_does_not_enter_negative_cache(self):
        """SDK 未安装是零成本判定，无需也不应占用负缓存窗口。"""
        clock = FakeClock()
        with mock.patch.object(creds_mod, "_TIME_SOURCE", clock):
            self.assertIsNone(creds_mod._creds_from_sdk())
        self.assertIsNone(creds_mod._SDK_FAILED_AT)
        self.assertEqual(creds_mod._LAST_SDK_FAILURE, "未安装（ImportError）")

    def test_construct_failure_does_not_enter_negative_cache(self):
        """构造失败保留「修好配置后下次重试」语义（不得被负缓存掩住）。"""
        fake_cls, state = make_fake_client_cls(construct_exc=ValueError("bad sdk config"))
        clock = FakeClock()
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            with mock.patch.object(creds_mod, "_TIME_SOURCE", clock):
                with redirect_stderr(io.StringIO()):
                    self.assertIsNone(creds_mod._creds_from_sdk())
                    self.assertIsNone(creds_mod._creds_from_sdk())
        self.assertEqual(state["constructs"], 2)
        self.assertIsNone(creds_mod._SDK_FAILED_AT)
        self.assertIn("构造失败（配置非法）", creds_mod._LAST_SDK_FAILURE)

    def test_reset_caches_clears_all_process_state(self):
        """``_reset_caches()`` 必须把单例/负缓存/来源/失败记录一次清干净。"""
        fake_cls, _state = make_fake_client_cls(exc=RuntimeError("boom"))
        clock = FakeClock()
        with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
            with mock.patch.object(creds_mod, "_TIME_SOURCE", clock):
                with redirect_stderr(io.StringIO()):
                    creds_mod._creds_from_sdk()
        self.assertIsNotNone(creds_mod._SDK_FAILED_AT)
        self.assertIsNotNone(creds_mod._LAST_SDK_FAILURE)
        creds_mod._reset_caches()
        self.assertIsNone(creds_mod._CRED_CLIENT)
        self.assertIsNone(creds_mod._SDK_FAILED_AT)
        self.assertIsNone(creds_mod._LAST_SDK_FAILURE)
        self.assertIsNone(creds_mod._LAST_SDK_SOURCE)
        self.assertIsNone(creds_mod._LAST_STDLIB_SOURCE)
        self.assertFalse(creds_mod._sdk_negative_cache_active())

    def test_ttl_default_is_30_seconds(self):
        """TTL 默认值锁定 30s（评审约定，改动需同步下游文档）。"""
        self.assertEqual(creds_mod.SDK_FAILURE_NEGATIVE_TTL, 30.0)


# ---------------------------------------------------------------------------
# 线程防护：只对可归因于 SDK 构造的差集线程标 daemon=True
# ---------------------------------------------------------------------------


class TestDaemonThreadGuard(unittest.TestCase):
    """``ensure_daemon_threads`` / ``install_atexit_guard`` 已收敛为兼容入口。

    旧实现无差别遍历 ``threading.enumerate()`` 是**结构性无效的假兜底**：
    (a) ``Thread.daemon`` setter 对已启动线程抛 ``RuntimeError``，而 enumerate()
    返回的全是已启动线程 → 恒走 except；(b) CPython ``Py_FinalizeEx`` 先
    ``wait_for_thread_shutdown()`` 再跑 atexit → 真挂住时钩子轮不到执行。
    真正生效的防护已移到 ``_get_sdk_client()`` 内同步执行（见下方另一组用例）。
    """

    def test_ensure_daemon_threads_survives_running_thread(self):
        """无参调用不得抛异常（兼容旧调用点：``sample.py`` 经 atexit 注册）。"""
        stop = threading.Event()
        worker = threading.Thread(target=stop.wait, name="fake-sdk-worker", daemon=False)
        worker.start()
        try:
            creds_mod.ensure_daemon_threads()  # 不抛异常即为通过
        finally:
            stop.set()
            worker.join(timeout=5)

    def test_no_arg_call_does_not_touch_any_thread(self):
        """行为变更：无参调用不再无差别遍历全部线程（避免误伤宿主业务线程）。"""
        stop = threading.Event()
        worker = threading.Thread(target=stop.wait, name="host-business-thread", daemon=False)
        worker.start()
        try:
            self.assertEqual(creds_mod.ensure_daemon_threads(), [])
            self.assertFalse(worker.daemon)  # 宿主线程必须原封不动
        finally:
            stop.set()
            worker.join(timeout=5)

    def test_main_thread_untouched(self):
        before = threading.current_thread().daemon
        creds_mod.ensure_daemon_threads()
        self.assertEqual(threading.current_thread().daemon, before)

    def test_explicit_candidates_get_marked(self):
        """显式传入候选集合时仍能把未启动线程标 daemon（保留公开 API 能力）。"""
        candidate = FakeThread("sdk-provider-thread", daemon=False)
        marked = creds_mod.ensure_daemon_threads([candidate])
        self.assertEqual(marked, ["sdk-provider-thread"])
        self.assertTrue(candidate.daemon)

    def test_install_atexit_guard_registers_hook(self):
        with mock.patch.object(creds_mod.atexit, "register") as m_register:
            creds_mod.install_atexit_guard()
        m_register.assert_called_once_with(creds_mod.ensure_daemon_threads)


class TestDaemonizeNewThreadsScope(unittest.TestCase):
    """``_daemonize_new_threads`` 的作用域收敛：只碰差集，不碰存量线程。"""

    def test_only_diff_threads_are_marked(self):
        """存量线程（回写 config.json 的、宿主业务的）必须原封不动。"""
        pre_existing = FakeThread("aliyun-config-writeback", daemon=False)
        host_business = FakeThread("host-business", daemon=False)
        sdk_new = FakeThread("sdk-new-provider", daemon=False)
        # 模拟 _get_sdk_client 的差集：构造后多出 sdk_new
        marked = creds_mod._daemonize_new_threads({sdk_new})
        self.assertEqual(marked, ["sdk-new-provider"])
        self.assertTrue(sdk_new.daemon)
        self.assertFalse(pre_existing.daemon)
        self.assertFalse(host_business.daemon)

    def test_already_daemon_candidates_are_skipped(self):
        th = FakeThread("sdk-already-daemon", daemon=True)
        self.assertEqual(creds_mod._daemonize_new_threads([th]), [])
        self.assertTrue(th.daemon)

    def test_main_thread_and_current_thread_never_marked(self):
        """双保险：即使调用方误传全量集合，也至少不碰主线程/当前线程。"""
        current = threading.current_thread()
        fake_main = FakeThread("MainThread", daemon=False)
        marked = creds_mod._daemonize_new_threads([current, fake_main])
        self.assertEqual(marked, [])
        self.assertFalse(fake_main.daemon)

    def test_started_thread_runtime_error_is_swallowed(self):
        """已启动线程改 daemon 抛 RuntimeError → 必须被静默吞掉，不冒到调用方。"""
        stop = threading.Event()
        worker = threading.Thread(target=stop.wait, name="started-worker", daemon=False)
        worker.start()
        try:
            marked = creds_mod._daemonize_new_threads([worker])
        finally:
            stop.set()
            worker.join(timeout=5)
        self.assertEqual(marked, [])
        self.assertFalse(worker.daemon)

    def test_empty_diff_is_noop(self):
        self.assertEqual(creds_mod._daemonize_new_threads(set()), [])


class TestSdkClientThreadSnapshot(CredentialsTestCase):
    """``_get_sdk_client`` 必须在构造前后各快照一次，且只对差集下手。"""

    def test_snapshots_before_and_after_construction(self):
        """构造前后共两次快照（不依赖 atexit，主线程仍在运行时同步执行）。"""
        fake_cls, _state = make_fake_client_cls(model=FakeCredModel("a", "b"))
        with mock.patch.object(
            creds_mod, "_snapshot_threads", side_effect=lambda: set()
        ) as m_snap:
            with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
                creds_mod._get_sdk_client()
        self.assertEqual(m_snap.call_count, 2)  # 前一次 + 后一次

    def test_only_newly_appeared_threads_are_daemonized(self):
        """差集内的线程被标 daemon；构造前已存在的线程绝不被碰。"""
        pre_existing = FakeThread("aliyun-config-writeback", daemon=False)
        sdk_thread = FakeThread("sdk-eager-provider", daemon=False)
        snapshots = [{pre_existing}, {pre_existing, sdk_thread}]
        fake_cls, _state = make_fake_client_cls(model=FakeCredModel("a", "b"))

        # 递进式快照：每调一次返回下一个集合（模拟构造前/后的 enumerate()）
        calls = {"n": 0}

        def next_snapshot():
            idx = min(calls["n"], len(snapshots) - 1)
            calls["n"] += 1
            return set(snapshots[idx])

        with mock.patch.object(creds_mod, "_snapshot_threads", side_effect=next_snapshot):
            with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
                creds_mod._get_sdk_client()
        self.assertEqual(calls["n"], 2)
        self.assertTrue(sdk_thread.daemon)      # 可归因于 SDK 构造 → 标 daemon
        self.assertFalse(pre_existing.daemon)   # 存量线程 → 原封不动

    def test_singleton_reuse_does_not_resnapshot(self):
        """单例复用路径不重复快照/不重复标 daemon（零额外开销）。"""
        fake_cls, state = make_fake_client_cls(model=FakeCredModel("a", "b"))
        with mock.patch.object(
            creds_mod, "_snapshot_threads", side_effect=lambda: set()
        ) as m_snap:
            with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
                creds_mod._get_sdk_client()
                creds_mod._get_sdk_client()
                creds_mod._get_sdk_client()
        self.assertEqual(m_snap.call_count, 2)  # 只在首次构造时快照两次
        self.assertEqual(state["constructs"], 1)

    def test_construct_failure_still_daemonizes_diff(self):
        """构造抛异常也要处理差集（provider 链 eager 构造中途失败可能已起线程）。"""
        sdk_thread = FakeThread("sdk-half-built", daemon=False)
        calls = {"n": 0}
        snapshots = [set(), {sdk_thread}]

        def next_snapshot():
            idx = min(calls["n"], len(snapshots) - 1)
            calls["n"] += 1
            return set(snapshots[idx])

        fake_cls, _state = make_fake_client_cls(construct_exc=ValueError("bad sdk config"))
        with mock.patch.object(creds_mod, "_snapshot_threads", side_effect=next_snapshot):
            with mock.patch.object(creds_mod, "CredentialClient", fake_cls):
                with redirect_stderr(io.StringIO()):
                    self.assertIsNone(creds_mod._get_sdk_client())
        self.assertTrue(sdk_thread.daemon)

    def test_sdk_uninstalled_skips_snapshot_entirely(self):
        """SDK 未安装时不应产生任何快照开销。"""
        with mock.patch.object(creds_mod, "_snapshot_threads") as m_snap:
            self.assertIsNone(creds_mod._get_sdk_client())
        m_snap.assert_not_called()


# ---------------------------------------------------------------------------
# 消费点委托：flow.creds_from_env 是薄封装（消除两处重复组装）
# ---------------------------------------------------------------------------


class TestConsumerDelegation(unittest.TestCase):
    """凭据消费点（``lib/flow.py``）已收敛到 ``credentials.resolve_creds`` 单一入口。

    改造前 ``flow.creds_from_env`` 与 ``control_plane._call`` 各有一份内联三元组
    组装（~50 LOC 重复）；改造后两者均委托本模块。
    """

    def test_flow_creds_from_env_delegates_to_resolve_creds(self):
        from lib import flow as flow_mod

        config = {
            "ALIYUN_ACCESS_KEY_ID": "LTAfake1001",
            "ALIYUN_ACCESS_KEY_SECRET": "sk-fake-1001",
        }
        with mock.patch.object(
            creds_mod, "resolve_creds", return_value=("ak-x", "sk-x", "token-x")
        ) as m_resolve:
            got = flow_mod.creds_from_env(config)
        self.assertEqual(got, ("ak-x", "sk-x", "token-x"))
        m_resolve.assert_called_once_with(config)

    def test_credential_error_propagates_unwrapped_through_flow(self):
        """CredentialError 不得被包成 FlowError：sample.py 顶层靠它透传三途径指引。"""
        from lib import flow as flow_mod

        with mock.patch.object(
            creds_mod, "resolve_creds", side_effect=CredentialError("三级链全败")
        ):
            with self.assertRaises(CredentialError):
                flow_mod.creds_from_env({})

    def test_data_plane_require_lists_dropped_ak_sk(self):
        """run_exchange_wat / run_obo 的 require_config 名单不再含 AK/SK（交给凭据链）。"""
        import inspect

        from lib import flow as flow_mod

        for func in (flow_mod.run_exchange_wat, flow_mod.run_obo):
            src = inspect.getsource(func)
            self.assertNotIn(
                "ALIYUN_ACCESS_KEY_ID", src, "{} 不应再硬要求 AK".format(func.__name__)
            )
            self.assertNotIn(
                "ALIYUN_ACCESS_KEY_SECRET", src, "{} 不应再硬要求 SK".format(func.__name__)
            )
            # 仍保留业务必填项（不得因改造而误删）
            self.assertIn("DATA_ENDPOINT", src)
            self.assertIn("creds_from_env", src)

    def test_run_obo_keeps_business_required_keys(self):
        import inspect

        from lib import flow as flow_mod

        src = inspect.getsource(flow_mod.run_obo)
        self.assertIn("OBO_PROVIDER_NAME", src)
        self.assertIn("ORDER_SERVICE_AUDIENCE", src)


# ---------------------------------------------------------------------------
# requirements.txt 版本钉定（SDK 是可选依赖，上界必须锁住未验证的大版本）
# ---------------------------------------------------------------------------


class TestRequirementsPin(unittest.TestCase):
    """``alibabacloud-credentials`` 钉 ``>=1.0.4,<1.1``（已实测 1.0.4 / 1.0.10）。"""

    @staticmethod
    def _read_requirements():
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "requirements.txt"
        )
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()

    def test_credentials_pinned_with_upper_bound(self):
        text = self._read_requirements()
        spec_lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        self.assertIn("alibabacloud-credentials>=1.0.4,<1.1", spec_lines)

    def test_optional_dependency_note_preserved(self):
        """「推荐可选依赖 + 缺失时自动降级标准库」的说明必须保留。"""
        text = self._read_requirements()
        self.assertIn("可选依赖", text)
        self.assertIn("降级", text)
        self.assertIn("~/.aliyun/config.json", text)

    def test_credentials_spec_has_both_bounds(self):
        """版本规格必须同时带下界与上界（单边 >= 会让未验证的大版本静默滑进来）。"""
        text = self._read_requirements()
        spec = next(
            (
                line.strip()
                for line in text.splitlines()
                if line.strip().startswith("alibabacloud-credentials")
            ),
            None,
        )
        self.assertIsNotNone(spec, "requirements.txt 缺少 alibabacloud-credentials 条目")
        self.assertIn(">=", spec)
        self.assertIn("<", spec)
        self.assertEqual(
            spec, "alibabacloud-credentials>=1.0.4,<1.1",
            "上界变动需同步跑退出时延测试并更新模块 docstring 的已验证版本清单",
        )


if __name__ == "__main__":
    unittest.main()
