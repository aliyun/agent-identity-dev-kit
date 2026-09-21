"""control_plane 单测（零网络）：

- Create*/Get* 响应嵌套防御解析：预发实测 CreateUserPool 返回
  ``{"RequestId": ..., "UserPool": {...}}`` 嵌套形态，旧代码只解析顶层 → 误报
  「成功但缺少 UserPoolId」；
- ``_call`` 保留异常链（``from exc``）：``__cause__`` 丢失会让
  ``_entity_not_exists`` 永远 False → cleanup 把「资源不存在（EntityNotExists）」
  报成「请手动清理」而非 [SKIP]；
- cleanup 防误删三路径：清单存在（按清单逆序删、逐项回写）、清单缺失（拒绝
  删除并给指引、不触碰网络）、``--from-env`` 逃生通道（按 .env 构造清单 +
  --yes 双确认）。
- 凭据链改造后的委托关系：``_call`` 不再内联组装 AK/SK，而是按
  「显式 creds 参数 > ``credentials.resolve_creds`` 实时解析」取凭据；模块级全局
  ``_ACTIVE_CREDS`` 已移除，改由 ``_CredsResolver``（TTL 缓存 + 可注入时钟）在
  setup（``_run_setup_script_inner``）与 cleanup（``_run_deletes``）两条路径显式传参，
  TTL 过期自动重解析（让 SDK/标准库到期刷新生效），失败不残留状态；
  ``run_setup_script`` 入口先用 ``resolve_creds_detailed`` 解析身份（fail-fast + 回显），
  ``_require_setup`` 不再硬校验 AK/SK（交给凭据链），endpoint 放宽为
  「REGION 或 CONTROL/DATA_ENDPOINT 至少其一」；setup 先回写核心产出（含只返回
  一次的 client_secret）再按 ``IDAAS_ORIGIN`` 走 ``discovery.apply_discovery`` 单独回写
  issuer/jwks_uri（仅值变化才回写，失败降级为警告不阻断 setup）。

所有外部交互（RPC 调用 / stdin 确认 / 清单文件 / 凭据解析 / discovery 拉取）
均被 mock 或指向临时目录——**全程离线**：``credentials.resolve_creds`` 一律打桩，
绝不让用例落到真实 SDK / ``~/.aliyun/config.json`` / 网络。
"""

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

SAMPLE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SAMPLE_DIR not in sys.path:
    sys.path.insert(0, SAMPLE_DIR)

from lib import control_plane as cp  # noqa: E402
from lib import tokens as tokens_mod  # noqa: E402
from lib.credentials import CredentialError  # noqa: E402
from lib.rpc import RpcError  # noqa: E402

# 单测固定凭据三元组（非真实凭据）：所有需要凭据的用例都用它打桩 resolve_creds
FAKE_CREDS = ("ak-unit-test", "sk-unit-test", None)

# discovery 回写用例的假值（与 test_discovery.py 同口径，非真实域名）
FAKE_IDAAS_ORIGIN = "https://idaas-unit-test.example.com"
FAKE_ISSUER = "https://idaas-unit-test.example.com/api/v2/iauths_system/oauth2"
FAKE_JWKS_URI = "https://idaas-unit-test.example.com/api/v2/iauths_system/oauth2/jwks"


def fake_config() -> dict:
    """能通过 ``_require_setup`` 的最小配置（值全部为测试占位，非真实凭据）。

    凭据链改造后 AK/SK 不再是必填项（由 ``credentials.resolve_creds`` 三级降级
    负责），故此处不再硬编码 AK/SK；需要凭据的用例自行打桩 ``resolve_creds``
    （见 ``CleanupTestCase.setUp`` 与 ``TestCallCredentialDelegation``）。
    """
    return {
        "CONTROL_ENDPOINT": "agentidentity.cn-test.aliyuncs.com",
        "DATA_ENDPOINT": "agentidentitydata.cn-test.aliyuncs.com",
        "OAUTH_REDIRECT_URI": "http://127.0.0.1:8765/callback",
        "SETUP_POOL_NAME": "env-pool",
        "SETUP_CLIENT_NAME": "env-cli",
        "SETUP_IDP_NAME": "env-idp",
        "WI_NAME": "env-wi",
        "OBO_PROVIDER_NAME": "env-provider",
    }


def setup_full_success_call(cfg, action, params=None, style="query", logger=None, creds=None):
    """``run_setup_script`` 六步全新建的假 ``_call``（Get* 报不存在 → Create* 成功）。"""
    responses = {
        "ListUserPools": {"UserPools": []},
        "CreateUserPool": {"RequestId": "r1", "UserPool": {"UserPoolId": "up_test0020"}},
        "SetSpecificIdentityProvider": {"RequestId": "r2"},
        "GetSpecificIdentityProvider": {
            "RequestId": "r3",
            "IdentityProvider": {"SSOStatus": "Enabled"},
        },
        "GetUserPoolClient": rpc_setup_error("EntityNotExists.ClientNotFound"),
        "CreateUserPoolClient": {
            "RequestId": "r4",
            "UserPoolClient": {"ClientId": "client_test20", "ClientSecret": "sec-unit"},
        },
        "GetIdentityProvider": rpc_setup_error("EntityNotExists.IdP"),
        "CreateIdentityProvider": {"RequestId": "r5"},
        "GetWorkloadIdentity": rpc_setup_error("EntityNotExists.WorkloadIdentity"),
        "CreateWorkloadIdentity": {"RequestId": "r6"},
        "GetOAuth2CredentialProvider": rpc_setup_error("EntityNotExists.Provider"),
        "CreateOAuth2CredentialProvider": {"RequestId": "r7"},
    }
    outcome = responses[action]
    if isinstance(outcome, Exception):
        raise outcome
    return outcome


def rpc_setup_error(code: str, status: int = 404) -> cp.SetupError:
    """构造带 RpcError ``__cause__`` 的 SetupError（模拟 _call 的 from exc 包装）。"""
    cause = RpcError(status, code, "message for " + code, "req-unit-test")
    try:
        raise cp.SetupError("X 调用失败：{}".format(cause)) from cause
    except cp.SetupError as wrapped:
        return wrapped


def noop_logger(_msg: str) -> None:
    pass


# ---------------------------------------------------------------------------
# 缺陷 #1：_first 防御式取键（顶层 + 嵌套对象）
# ---------------------------------------------------------------------------


class TestFirstDefensive(unittest.TestCase):
    def test_top_level_key(self):
        self.assertEqual(cp._first({"UserPoolId": "up_a"}, "UserPoolId"), "up_a")

    def test_nested_entity_shape(self):
        # 预发实测形态：{"RequestId": ..., "UserPool": {"UserPoolId": ...}}
        resp = {"RequestId": "r1", "UserPool": {"UserPoolId": "up_b", "UserPoolName": "p"}}
        self.assertEqual(
            cp._first(resp, "UserPoolId", "PoolId", nested=("UserPool", "Pool")), "up_b"
        )

    def test_nested_candidate_outer_keys(self):
        resp = {"Pool": {"PoolId": "up_c"}}
        self.assertEqual(
            cp._first(resp, "UserPoolId", "PoolId", nested=("UserPool", "Pool")), "up_c"
        )

    def test_top_level_preferred_over_nested(self):
        resp = {"UserPoolId": "up_top", "UserPool": {"UserPoolId": "up_inner"}}
        self.assertEqual(cp._first(resp, "UserPoolId", nested=("UserPool",)), "up_top")

    def test_blank_top_level_falls_through_to_nested(self):
        resp = {"UserPoolId": "", "Pool": {"PoolId": "up_d"}}
        self.assertEqual(cp._first(resp, "UserPoolId", "PoolId", nested=("Pool",)), "up_d")

    def test_empty_nested_object_and_missing_return_default(self):
        self.assertEqual(
            cp._first({"RequestId": "r", "UserPool": {}}, "UserPoolId", nested=("UserPool",), default=""),
            "",
        )
        self.assertIsNone(cp._first({}, "X", default=None))

    def test_non_dict_nested_value_ignored(self):
        resp = {"UserPool": "not-a-dict"}
        self.assertEqual(cp._first(resp, "UserPoolId", nested=("UserPool",), default="d"), "d")


class TestCreateResponseParsing(unittest.TestCase):
    """Create* 响应取值：嵌套形态不再误报缺字段，顶层形态保持兼容。"""

    def setUp(self):
        self.config = fake_config()

    def test_create_user_pool_nested_shape(self):
        responses = {
            "ListUserPools": {"UserPools": []},
            "CreateUserPool": {
                "RequestId": "r1",
                "UserPool": {"UserPoolId": "up_test0001", "UserPoolName": "env-pool"},
            },
        }

        def fake_call(cfg, action, params=None, style="query", logger=None, creds=None):
            return responses[action]

        with mock.patch.object(cp, "_call", side_effect=fake_call):
            pool_id, pool_name, created = cp._ensure_pool(self.config, noop_logger)
        self.assertEqual(pool_id, "up_test0001")
        self.assertEqual(pool_name, "env-pool")
        self.assertTrue(created)

    def test_create_user_pool_top_level_shape_compat(self):
        responses = {
            "ListUserPools": {"UserPools": []},
            "CreateUserPool": {"RequestId": "r1", "UserPoolId": "up_test0002"},
        }

        def fake_call(cfg, action, params=None, style="query", logger=None, creds=None):
            return responses[action]

        with mock.patch.object(cp, "_call", side_effect=fake_call):
            pool_id, _pool_name, created = cp._ensure_pool(self.config, noop_logger)
        self.assertEqual(pool_id, "up_test0002")
        self.assertTrue(created)

    def test_reused_pool_reports_not_created(self):
        responses = {
            "ListUserPools": {"UserPools": [{"UserPoolName": "env-pool", "UserPoolId": "up_test0003"}]},
        }

        def fake_call(cfg, action, params=None, style="query", logger=None, creds=None):
            return responses[action]

        with mock.patch.object(cp, "_call", side_effect=fake_call):
            pool_id, _pool_name, created = cp._ensure_pool(self.config, noop_logger)
        self.assertEqual(pool_id, "up_test0003")
        self.assertFalse(created)

    def test_create_user_pool_client_nested_shape(self):
        def fake_call(cfg, action, params=None, style="query", logger=None, creds=None):
            if action == "GetUserPoolClient":
                raise rpc_setup_error("EntityNotExists.ClientNotFound")
            if action == "CreateUserPoolClient":
                return {
                    "RequestId": "r2",
                    "UserPoolClient": {"ClientId": "client_test01", "ClientSecret": "sec-unit"},
                }
            raise AssertionError("unexpected action: " + action)

        with mock.patch.object(cp, "_call", side_effect=fake_call):
            client_id, secret, created = cp._ensure_client(
                self.config, "env-pool", "http://127.0.0.1:8765/callback", noop_logger
            )
        self.assertEqual(client_id, "client_test01")
        self.assertEqual(secret, "sec-unit")
        self.assertTrue(created)

    def test_create_client_secret_nested_shape(self):
        # 响应缺 Secret 顶层键 → CreateClientSecret 返回嵌套 {"Secret": {"ClientSecret": ...}}
        def fake_call(cfg, action, params=None, style="query", logger=None, creds=None):
            if action == "GetUserPoolClient":
                raise rpc_setup_error("EntityNotExists.ClientNotFound")
            if action == "CreateUserPoolClient":
                return {"RequestId": "r3", "UserPoolClient": {"ClientId": "client_test02"}}
            if action == "CreateClientSecret":
                return {"RequestId": "r4", "Secret": {"ClientSecret": "sec-nested"}}
            raise AssertionError("unexpected action: " + action)

        with mock.patch.object(cp, "_call", side_effect=fake_call):
            client_id, secret, _created = cp._ensure_client(
                self.config, "env-pool", "http://127.0.0.1:8765/callback", noop_logger
            )
        self.assertEqual(secret, "sec-nested")

    def test_get_workload_identity_nested_shape(self):
        responses = {
            "GetWorkloadIdentity": {
                "RequestId": "r5",
                "WorkloadIdentity": {"WorkloadIdentityName": "env-wi", "SessionBindingEnabled": True},
            },
        }

        def fake_call(cfg, action, params=None, style="query", logger=None, creds=None):
            return responses[action]

        with mock.patch.object(cp, "_call", side_effect=fake_call):
            wi_name, created = cp._ensure_workload_identity(self.config, "env-idp", noop_logger)
        self.assertEqual(wi_name, "env-wi")
        self.assertFalse(created)

    def test_get_oauth2_provider_nested_shape(self):
        responses = {
            "GetOAuth2CredentialProvider": {
                "RequestId": "r6",
                "OAuth2CredentialProvider": {"OAuth2CredentialProviderName": "env-provider"},
            },
        }

        def fake_call(cfg, action, params=None, style="query", logger=None, creds=None):
            return responses[action]

        with mock.patch.object(cp, "_call", side_effect=fake_call):
            provider_name, created = cp._ensure_oauth2_provider(self.config, noop_logger)
        self.assertEqual(provider_name, "env-provider")
        self.assertFalse(created)


# ---------------------------------------------------------------------------
# 缺陷 #2：_call 异常链保留 → _entity_not_exists / _already_exists 正确判定
# ---------------------------------------------------------------------------


class TestCallErrorChain(unittest.TestCase):
    """旧实现 ``raise ... from None`` 丢弃 __cause__ → EntityNotExists 永远判不出。"""

    def _call_and_catch(self, rpc_error: RpcError) -> cp.SetupError:
        config = {
            "CONTROL_ENDPOINT": "agentidentity.cn-test.aliyuncs.com",
        }
        # 凭据由 resolve_creds 提供（此处打桩，保持离线）；本类只关心异常链保留
        with mock.patch.object(cp.credentials, "resolve_creds", return_value=FAKE_CREDS):
            with mock.patch.object(cp.rpc, "rpc_call", side_effect=rpc_error):
                with self.assertRaises(cp.SetupError) as ctx:
                    cp._call(config, "GetWorkloadIdentity", {})
        return ctx.exception

    def test_entity_not_exists_detected_via_cause(self):
        exc = self._call_and_catch(RpcError(404, "EntityNotExists.WorkloadIdentity", "not found", "req-1"))
        self.assertIsInstance(exc.__cause__, RpcError)
        self.assertTrue(cp._entity_not_exists(exc))

    def test_not_found_code_detected(self):
        exc = self._call_and_catch(RpcError(404, "NotFound.UserPool", "gone", "req-2"))
        self.assertTrue(cp._entity_not_exists(exc))

    def test_other_error_not_entity_not_exists(self):
        exc = self._call_and_catch(RpcError(400, "InvalidParameter.X", "bad param", "req-3"))
        self.assertFalse(cp._entity_not_exists(exc))

    def test_already_exists_detected(self):
        exc = self._call_and_catch(RpcError(409, "EntityAlreadyExists.Provider", "duplicate", "req-4"))
        self.assertTrue(cp._already_exists(exc))


class TestDeleteQuietStatus(unittest.TestCase):
    """EntityNotExists 错误码路径应判定为 [SKIP]，而非「请手动清理」。"""

    def test_skip_on_entity_not_exists(self):
        with mock.patch.object(cp, "_call", side_effect=rpc_setup_error("EntityNotExists.UserPool")):
            status = cp._delete_quiet(
                fake_config(), "DeleteUserPool", {"UserPoolName": "p"}, "用户池 p", noop_logger
            )
        self.assertEqual(status, "skipped")

    def test_deleted_on_success(self):
        with mock.patch.object(cp, "_call", return_value={"RequestId": "r-ok"}):
            status = cp._delete_quiet(
                fake_config(), "DeleteUserPool", {"UserPoolName": "p"}, "用户池 p", noop_logger
            )
        self.assertEqual(status, "deleted")

    def test_failed_on_other_error(self):
        with mock.patch.object(cp, "_call", side_effect=rpc_setup_error("InvalidParameter.Protected")):
            status = cp._delete_quiet(
                fake_config(), "DeleteUserPool", {"UserPoolName": "p"}, "用户池 p", noop_logger
            )
        self.assertEqual(status, "failed")

    def test_failed_on_credential_error_not_propagated(self):
        """D3：CredentialError（凭据过期/不可得）不得中断尽力而为的逆序清理。

        ``_call`` 会直穿抛 ``credentials.CredentialError``（非 SetupError 子类）；
        旧 ``_delete_quiet`` 只捕 SetupError → 中途 STS 过期会让剩余条目全部不再尝试、
        且清单回写整段被跳过。现记为 failed（条目留清单供下次续删），不上抛。
        """
        with mock.patch.object(cp, "_call", side_effect=CredentialError("STS 已过期")):
            status = cp._delete_quiet(
                fake_config(), "DeleteUserPool", {"UserPoolName": "p"}, "用户池 p", noop_logger
            )
        self.assertEqual(status, "failed")


# ---------------------------------------------------------------------------
# 缺陷 #4：cleanup 防误删（清单机制三路径 + setup 写清单）
# ---------------------------------------------------------------------------


class CleanupTestCase(unittest.TestCase):
    """基类：清单文件指向临时目录，.env 读取替换为内存 fake 配置。

    额外防御（凭据链改造后必需）：
    - ``credentials.resolve_creds`` 与 ``resolve_creds_detailed`` 一律打桩——fake_config
      不再带显式 AK/SK，若不打桩，任何走到真实 ``_call`` / ``run_cleanup`` / ``run_setup_script``
      的路径会落到 SDK / ``~/.aliyun/config.json``（可能触发真实网络刷新），破坏离线保证；
    - ``_CredsResolver`` 每次由被测函数新建（无模块级全局），天然用例间隔离。
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        # tokens 模块的 TOKENS_DIR 被 patch 后：清单 load/save/remove 全走临时目录
        patcher = mock.patch.object(tokens_mod, "TOKENS_DIR", self._tmp.name)
        patcher.start()
        self.addCleanup(patcher.stop)
        # run_cleanup 内部的 env_mod.load_env() → fake 配置（含 _require_setup 必需键）
        patcher_env = mock.patch.object(cp.env_mod, "load_env", return_value=fake_config())
        patcher_env.start()
        self.addCleanup(patcher_env.stop)
        # 凭据解析打桩（离线）：resolve_creds 供 _CredsResolver.get()，
        # resolve_creds_detailed 供 run_setup_script / run_cleanup 入口的身份解析与回显
        patcher_creds = mock.patch.object(
            cp.credentials, "resolve_creds", return_value=FAKE_CREDS
        )
        self.resolve_creds_mock = patcher_creds.start()
        self.addCleanup(patcher_creds.stop)
        fake_resolved = cp.credentials.ResolvedCreds(
            FAKE_CREDS[0], FAKE_CREDS[1], FAKE_CREDS[2],
            cp.credentials.LEVEL_EXPLICIT, ".env 显式 ALIYUN_ACCESS_KEY_*（单测桩）",
        )
        patcher_detailed = mock.patch.object(
            cp.credentials, "resolve_creds_detailed", return_value=fake_resolved
        )
        self.resolve_detailed_mock = patcher_detailed.start()
        self.addCleanup(patcher_detailed.stop)
        # 防御：默认封死 input（用例显式 mock 才会有交互）
        patcher_input = mock.patch("builtins.input", side_effect=AssertionError("unexpected interactive input"))
        patcher_input.start()
        self.addCleanup(patcher_input.stop)

    def manifest_file(self) -> str:
        return os.path.join(self._tmp.name, cp.MANIFEST_NAME)

    def write_manifest(self, resources) -> None:
        tokens_mod.save_json(cp.MANIFEST_NAME, {"version": 1, "resources": resources})

    def read_manifest_resources(self):
        return tokens_mod.load_json(cp.MANIFEST_NAME).get("resources")


class TestRunDeletesCredentialFailure(CleanupTestCase):
    """W1：resolver 抛 CredentialError 时 _run_deletes 不抛出且 remaining 保全全部条目。

    凭据不可解时不得对 N 个条目各发一次注定失败的请求，也不得让异常逃逸
    打断 run_cleanup 的清单回写。
    """

    def test_resolver_failure_preserves_all_entries(self):
        entries = [
            {"type": "user_pool", "name": "pool-w1"},
            {"type": "pool_client", "name": "cli-w1", "pool_name": "pool-w1"},
            {"type": "identity_provider", "name": "idp-w1"},
        ]
        # 构造一个始终抛 CredentialError 的 resolver（通过 resolve_func 注入）
        def _always_fail(config):
            raise CredentialError("凭据链三级降级全部失败")

        resolver = cp._CredsResolver(fake_config(), resolve_func=_always_fail)
        with mock.patch.object(cp, "_call") as fake_call:
            remaining = cp._run_deletes(fake_config(), entries, resolver=resolver)
        # 不抛出、不发请求、remaining 保全全部条目
        fake_call.assert_not_called()
        self.assertEqual(len(remaining), 3)
        remaining_keys = {(e["type"], e["name"]) for e in remaining}
        self.assertEqual(remaining_keys, {
            ("user_pool", "pool-w1"),
            ("pool_client", "cli-w1"),
            ("identity_provider", "idp-w1"),
        })


class TestCleanupByManifest(CleanupTestCase):
    def test_deletes_in_reverse_order_then_removes_manifest(self):
        self.write_manifest([
            {"type": "user_pool", "name": "pool-a", "created_at": "2026-01-01T00:00:00Z"},
            {"type": "pool_client", "name": "cli-a", "pool_name": "pool-a", "created_at": "2026-01-01T00:00:01Z"},
        ])
        calls = []

        def fake_call(cfg, action, params=None, style="query", logger=None, creds=None):
            calls.append((action, params))
            return {"RequestId": "r-" + action}

        with mock.patch.object(cp, "_call", side_effect=fake_call):
            cp.run_cleanup(assume_yes=True)

        # 逆序：先删客户端（依赖方），再删池
        self.assertEqual([c[0] for c in calls], ["DeleteUserPoolClient", "DeleteUserPool"])
        self.assertEqual(calls[0][1], {"UserPoolName": "pool-a", "ClientName": "cli-a"})
        self.assertEqual(calls[1][1], {"UserPoolName": "pool-a"})
        # 全部删除成功 → 清单文件删除
        self.assertFalse(os.path.exists(self.manifest_file()))

    def test_interactive_cancel_keeps_manifest_and_network_untouched(self):
        self.write_manifest([{"type": "user_pool", "name": "pool-a"}])
        with mock.patch("builtins.input", return_value="no"):
            with mock.patch.object(cp, "_call") as fake_call:
                cp.run_cleanup(assume_yes=False)
        fake_call.assert_not_called()  # 取消确认 → 不发任何删除请求
        self.assertEqual(self.read_manifest_resources(), [{"type": "user_pool", "name": "pool-a"}])

    def test_interactive_yes_proceeds(self):
        self.write_manifest([{"type": "user_pool", "name": "pool-a"}])
        calls = []
        with mock.patch("builtins.input", return_value="yes"):
            with mock.patch.object(
                cp, "_call", side_effect=lambda cfg, action, params=None, **kw: calls.append(action) or {"RequestId": "r"}
            ):
                cp.run_cleanup(assume_yes=False)
        self.assertEqual(calls, ["DeleteUserPool"])
        self.assertFalse(os.path.exists(self.manifest_file()))

    def test_failed_delete_keeps_entry_in_manifest(self):
        self.write_manifest([
            {"type": "user_pool", "name": "pool-a"},
            {"type": "pool_client", "name": "cli-a", "pool_name": "pool-a"},
        ])

        def fake_call(cfg, action, params=None, style="query", logger=None, creds=None):
            if action == "DeleteUserPool":
                raise rpc_setup_error("InvalidParameter.Protected")
            return {"RequestId": "r"}

        with mock.patch.object(cp, "_call", side_effect=fake_call):
            cp.run_cleanup(assume_yes=True)
        # 客户端删除成功被移除；池删除失败保留在清单（重跑续删）
        self.assertEqual(self.read_manifest_resources(), [{"type": "user_pool", "name": "pool-a"}])

    def test_skip_removes_entry_from_manifest(self):
        self.write_manifest([{"type": "user_pool", "name": "pool-a"}])
        with mock.patch.object(cp, "_call", side_effect=rpc_setup_error("EntityNotExists.UserPool")):
            cp.run_cleanup(assume_yes=True)
        # 资源已不存在（[SKIP]）→ 条目移除 → 清单清空后删除文件
        self.assertFalse(os.path.exists(self.manifest_file()))

    def test_unknown_manifest_type_kept_and_not_deleted(self):
        self.write_manifest([
            {"type": "mystery", "name": "x"},
            {"type": "user_pool", "name": "pool-a"},
        ])
        calls = []

        def fake_call(cfg, action, params=None, style="query", logger=None, creds=None):
            calls.append(action)
            return {"RequestId": "r"}

        with mock.patch.object(cp, "_call", side_effect=fake_call):
            cp.run_cleanup(assume_yes=True)
        self.assertEqual(calls, ["DeleteUserPool"])  # 未知类型不删
        self.assertEqual(self.read_manifest_resources(), [{"type": "mystery", "name": "x"}])


class TestCleanupNoManifest(CleanupTestCase):
    def test_refuses_without_manifest_and_offers_guidance(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            with mock.patch.object(cp, "_call") as fake_call:
                cp.run_cleanup(assume_yes=True)  # 即使 --yes 也拒绝（无清单）
        fake_call.assert_not_called()  # 不触碰网络
        out = buf.getvalue()
        self.assertIn("未发现本样例创建的资源记录", out)
        self.assertIn("拒绝删除", out)
        self.assertIn("docs/control-plane-console.md", out)
        self.assertIn("--from-env", out)

    def test_from_env_without_yes_refuses_without_network(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            with mock.patch.object(cp, "_call") as fake_call:
                cp.run_cleanup(assume_yes=False, from_env=True)
        fake_call.assert_not_called()  # 双确认门槛：--from-env 必须叠加 --yes
        self.assertIn("双确认", buf.getvalue())

    def test_from_env_with_yes_deletes_by_env_values(self):
        calls = []

        def fake_call(cfg, action, params=None, style="query", logger=None, creds=None):
            calls.append((action, params))
            return {"RequestId": "r"}

        with mock.patch.object(cp, "_call", side_effect=fake_call):
            cp.run_cleanup(assume_yes=True, from_env=True)
        # 逆序全量删除（旧 cleanup 的范围）
        self.assertEqual([c[0] for c in calls], [
            "DeleteOAuth2CredentialProvider",
            "DeleteWorkloadIdentity",
            "DeleteIdentityProvider",
            "DeleteUserPoolClient",
            "DeleteUserPool",
        ])
        self.assertEqual(calls[0][1], {"OAuth2CredentialProviderName": "env-provider"})
        self.assertEqual(calls[3][1], {"UserPoolName": "env-pool", "ClientName": "env-cli"})
        # from-env 为内存清单：不落盘
        self.assertFalse(os.path.exists(self.manifest_file()))

    def test_manifest_takes_priority_over_from_env(self):
        # 清单存在时 --from-env 被忽略：按清单删（范围更小、更安全）
        self.write_manifest([{"type": "user_pool", "name": "pool-manifest"}])
        calls = []

        def fake_call(cfg, action, params=None, style="query", logger=None, creds=None):
            calls.append(action)
            return {"RequestId": "r"}

        with mock.patch.object(cp, "_call", side_effect=fake_call):
            cp.run_cleanup(assume_yes=True, from_env=True)
        self.assertEqual(calls, ["DeleteUserPool"])


class TestSetupIncrementalManifest(CleanupTestCase):
    """Major-2：setup 中途失败时已建资源已增量落盘（不产生「受保护孤儿」）。

    旧实现只在六步全部成功后统一 _merge_manifest：中途失败 → 已建资源进不了
    清单；重跑后幂等复用（created=False）清单永远为空 → 资源只能 --from-env
    或手动清理。
    """

    def test_failure_midway_manifest_contains_created_steps(self):
        # 前两步创建成功（池 + 客户端），第 4 步（第 3 个创建型步骤
        # _ensure_identity_provider）抛非 EntityNotExists 错误中断
        def fake_call(cfg, action, params=None, style="query", logger=None, creds=None):
            if action == "ListUserPools":
                return {"UserPools": []}
            if action == "CreateUserPool":
                return {
                    "RequestId": "r1",
                    "UserPool": {"UserPoolId": "up_test0010", "UserPoolName": "env-pool"},
                }
            if action == "SetSpecificIdentityProvider":
                return {"RequestId": "r2"}
            if action == "GetSpecificIdentityProvider":
                return {"RequestId": "r3", "IdentityProvider": {"SSOStatus": "Enabled"}}
            if action == "GetUserPoolClient":
                raise rpc_setup_error("EntityNotExists.ClientNotFound")
            if action == "CreateUserPoolClient":
                return {
                    "RequestId": "r4",
                    "UserPoolClient": {"ClientId": "client_test10", "ClientSecret": "sec-unit"},
                }
            if action == "GetIdentityProvider":
                # 失败注入点：确定性错误（非 EntityNotExists，不会被当作不存在跳过）
                raise rpc_setup_error("InternalError.RPC", status=500)
            raise AssertionError("unexpected action: " + action)

        config = fake_config()
        with mock.patch.object(cp, "_call", side_effect=fake_call):
            with self.assertRaises(cp.SetupError):
                cp.run_setup_script(config=config)

        # 关键断言：清单已含前两步创建的资源（每步 created=True 后立即增量落盘）
        resources = self.read_manifest_resources()
        self.assertEqual(
            [(r["type"], r["name"]) for r in resources],
            [("user_pool", "env-pool"), ("pool_client", "env-cli")],
        )

    def test_full_success_manifest_contains_all_created(self):
        def fake_call(cfg, action, params=None, style="query", logger=None, creds=None):
            responses = {
                "ListUserPools": {"UserPools": []},
                "CreateUserPool": {"RequestId": "r1", "UserPool": {"UserPoolId": "up_test0011"}},
                "SetSpecificIdentityProvider": {"RequestId": "r2"},
                "GetSpecificIdentityProvider": {"RequestId": "r3", "IdentityProvider": {"SSOStatus": "Enabled"}},
                "GetUserPoolClient": rpc_setup_error("EntityNotExists.ClientNotFound"),
                "CreateUserPoolClient": {
                    "RequestId": "r4",
                    "UserPoolClient": {"ClientId": "client_test11", "ClientSecret": "sec-unit"},
                },
                "GetIdentityProvider": rpc_setup_error("EntityNotExists.IdP"),
                "CreateIdentityProvider": {"RequestId": "r5"},
                "GetWorkloadIdentity": rpc_setup_error("EntityNotExists.WorkloadIdentity"),
                "CreateWorkloadIdentity": {"RequestId": "r6"},
                "GetOAuth2CredentialProvider": rpc_setup_error("EntityNotExists.Provider"),
                "CreateOAuth2CredentialProvider": {"RequestId": "r7"},
            }
            outcome = responses[action]
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        config = fake_config()
        config["SETUP_OBO_PROVIDER_CONFIG"] = '{"clientId": "app_test01", "clientSecret": "sec-unit"}'
        with mock.patch.object(cp, "_call", side_effect=fake_call):
            with mock.patch.object(cp, "writeback_env", return_value="/tmp/env-fake"):
                cp.run_setup_script(config=config)

        # 全部 6 步新建 → 清单含 5 类资源（按创建顺序）
        self.assertEqual(
            [r["type"] for r in self.read_manifest_resources()],
            [
                "user_pool",
                "pool_client",
                "identity_provider",
                "workload_identity",
                "oauth2_provider",
            ],
        )


class TestCleanupEofSafety(CleanupTestCase):
    """Minor-8：非交互环境（stdin 关闭/重定向）下 cleanup 失败安全——拒绝删除。"""

    def test_eof_on_confirm_refuses_deletion(self):
        self.write_manifest([{"type": "user_pool", "name": "pool-a"}])
        with mock.patch("builtins.input", side_effect=EOFError):
            with mock.patch.object(cp, "_call") as fake_call:
                cp.run_cleanup(assume_yes=False)
        fake_call.assert_not_called()  # EOF → answer="no" → 不发任何删除请求
        self.assertEqual(self.read_manifest_resources(), [{"type": "user_pool", "name": "pool-a"}])


class TestCleanupKeepPool(CleanupTestCase):
    """S-H：--keep-pool 跳过清单中的用户池不删，并保留在清单中。"""

    def test_keep_pool_skips_pool_and_keeps_it_in_manifest(self):
        self.write_manifest([
            {"type": "user_pool", "name": "pool-a"},
            {"type": "pool_client", "name": "cli-a", "pool_name": "pool-a"},
        ])
        calls = []

        def fake_call(cfg, action, params=None, style="query", logger=None, creds=None):
            calls.append(action)
            return {"RequestId": "r"}

        with mock.patch.object(cp, "_call", side_effect=fake_call):
            cp.run_cleanup(assume_yes=True, keep_pool=True)
        # 只删客户端，不删池
        self.assertEqual(calls, ["DeleteUserPoolClient"])
        # 池条目保留在清单（下次不带 --keep-pool 重跑仍可删）
        self.assertEqual(self.read_manifest_resources(), [{"type": "user_pool", "name": "pool-a"}])

    def test_keep_pool_only_pool_in_manifest_deletes_nothing(self):
        self.write_manifest([{"type": "user_pool", "name": "pool-a"}])
        with mock.patch.object(cp, "_call") as fake_call:
            cp.run_cleanup(assume_yes=True, keep_pool=True)
        fake_call.assert_not_called()  # 清单内只有池 → 无可删条目，不触碰网络
        self.assertEqual(self.read_manifest_resources(), [{"type": "user_pool", "name": "pool-a"}])


class TestManifestMerge(CleanupTestCase):
    def test_merge_appends_dedupes_and_stamps_created_at(self):
        cp._merge_manifest([{"type": "user_pool", "name": "pool-a"}])
        resources = self.read_manifest_resources()
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]["type"], "user_pool")
        self.assertIn("created_at", resources[0])
        # 同 (type, name) 不重复
        cp._merge_manifest([{"type": "user_pool", "name": "pool-a"}])
        self.assertEqual(len(self.read_manifest_resources()), 1)
        # 新条目追加
        cp._merge_manifest([{"type": "pool_client", "name": "cli-a", "pool_name": "pool-a"}])
        self.assertEqual(
            [r["name"] for r in self.read_manifest_resources()], ["pool-a", "cli-a"]
        )

    def test_merge_preserves_existing_entries(self):
        self.write_manifest([{"type": "user_pool", "name": "old-pool", "created_at": "2025-01-01T00:00:00Z"}])
        cp._merge_manifest([{"type": "workload_identity", "name": "wi-new"}])
        resources = self.read_manifest_resources()
        self.assertEqual(len(resources), 2)
        self.assertEqual(
            resources[0], {"type": "user_pool", "name": "old-pool", "created_at": "2025-01-01T00:00:00Z"}
        )

    def test_manifest_entries_from_env_filters_placeholders(self):
        config = fake_config()
        config["WI_NAME"] = "<YOUR_WI_NAME>"
        config["OBO_PROVIDER_NAME"] = ""
        entries = cp._manifest_entries_from_env(cp.env_mod.derive_defaults(config))
        # 占位符/空值被过滤；条目按创建顺序排列（cleanup 逆序处理 → 池最后删）
        self.assertEqual(
            [(e["type"], e["name"]) for e in entries],
            [
                ("user_pool", "env-pool"),
                ("pool_client", "env-cli"),
                ("identity_provider", "env-idp"),
            ],
        )
        self.assertEqual(entries[1]["pool_name"], "env-pool")

    def test_manifest_entries_from_env_full_order(self):
        entries = cp._manifest_entries_from_env(cp.env_mod.derive_defaults(fake_config()))
        # 创建顺序：pool → client → idp → wi → provider；逆序删除即 provider 最先、池最后
        self.assertEqual([e["type"] for e in entries], [
            "user_pool",
            "pool_client",
            "identity_provider",
            "workload_identity",
            "oauth2_provider",
        ])


# ---------------------------------------------------------------------------
# 凭据链改造：_require_setup 放宽 / _call 委托 / _ACTIVE_CREDS 生命周期
# ---------------------------------------------------------------------------


class TestRequireSetupRelaxed(unittest.TestCase):
    """``_require_setup``：不再硬校验 AK/SK（交给凭据链），endpoint 放宽。"""

    def test_passes_with_region_only(self):
        """只有 REGION（endpoint 由 derive_defaults 派生）即可通过。"""
        config = {
            "REGION": "cn-test",
            "OAUTH_REDIRECT_URI": "http://127.0.0.1:8765/callback",
        }
        cp._require_setup(config)  # 不抛即通过

    def test_passes_with_explicit_endpoints_without_region(self):
        config = {
            "CONTROL_ENDPOINT": "agentidentity.cn-test.aliyuncs.com",
            "DATA_ENDPOINT": "agentidentitydata.cn-test.aliyuncs.com",
            "OAUTH_REDIRECT_URI": "http://127.0.0.1:8765/callback",
        }
        cp._require_setup(config)

    def test_ak_sk_not_required(self):
        """关键回归：AK/SK 占位/缺失也不得报缺配置（由 resolve_creds 三级链负责）。"""
        for ak, sk in (
            ("", ""),
            ("<YOUR_ALIYUN_ACCESS_KEY_ID>", "<YOUR_ALIYUN_ACCESS_KEY_SECRET>"),
        ):
            config = fake_config()
            config["REGION"] = "cn-test"
            config["ALIYUN_ACCESS_KEY_ID"] = ak
            config["ALIYUN_ACCESS_KEY_SECRET"] = sk
            cp._require_setup(config)
        # 完全不出现这两个键也一样通过（fake_config 已不带 AK/SK）
        cp._require_setup(dict(fake_config(), REGION="cn-test"))

    def test_fails_without_region_and_endpoints(self):
        config = {"OAUTH_REDIRECT_URI": "http://127.0.0.1:8765/callback"}
        with self.assertRaises(cp.SetupError) as ctx:
            cp._require_setup(config)
        msg = str(ctx.exception)
        self.assertIn("REGION", msg)
        self.assertIn("CONTROL_ENDPOINT", msg)
        self.assertIn(cp.env_mod.ENV_FILE, msg)  # 指引用户去哪个文件补

    def test_fails_without_redirect_uri(self):
        config = {"REGION": "cn-test", "OAUTH_REDIRECT_URI": "<YOUR_OAUTH_REDIRECT_URI>"}
        with self.assertRaises(cp.SetupError) as ctx:
            cp._require_setup(config)
        self.assertIn("OAUTH_REDIRECT_URI", str(ctx.exception))

    def test_custom_context_in_message(self):
        with self.assertRaises(cp.SetupError) as ctx:
            cp._require_setup({}, context="cleanup --from-env")
        self.assertIn("cleanup --from-env", str(ctx.exception))


class TestCallCredentialDelegation(unittest.TestCase):
    """``_call`` 凭据来源两级优先：显式 creds 参数 > ``credentials.resolve_creds`` 实时解析。

    D2：模块级全局 ``_ACTIVE_CREDS`` 已移除，``_call`` 不再读取任何全局缓存；
    缓存职责上移到 ``_CredsResolver``（见 ``TestCredsResolver``），由调用方逐层显式传入 ``creds=``。
    """

    def setUp(self):
        self.config = {"CONTROL_ENDPOINT": "agentidentity.cn-test.aliyuncs.com"}

    def test_delegates_to_resolve_creds_and_forwards_triple(self):
        with mock.patch.object(cp.credentials, "resolve_creds", return_value=FAKE_CREDS) as m_resolve:
            with mock.patch.object(cp.rpc, "rpc_call", return_value={"RequestId": "r"}) as m_rpc:
                cp._call(self.config, "GetWorkloadIdentity", {})
        m_resolve.assert_called_once_with(self.config)
        self.assertEqual(m_rpc.call_args.kwargs["creds"], FAKE_CREDS)

    def test_explicit_creds_param_wins(self):
        explicit = ("ak-explicit", "sk-explicit", "token-explicit")
        with mock.patch.object(cp.credentials, "resolve_creds", return_value=FAKE_CREDS) as m_resolve:
            with mock.patch.object(cp.rpc, "rpc_call", return_value={}) as m_rpc:
                cp._call(self.config, "GetWorkloadIdentity", {}, creds=explicit)
        m_resolve.assert_not_called()
        self.assertEqual(m_rpc.call_args.kwargs["creds"], explicit)

    def test_no_module_level_active_creds_global(self):
        """D2 核心回归：模块级 ``_ACTIVE_CREDS`` 全局已彻底移除（不再存在可被污染的共享态）。"""
        self.assertFalse(hasattr(cp, "_ACTIVE_CREDS"))

    def test_credential_error_propagates_unwrapped(self):
        """凭据不可得 → CredentialError 原样上抛（不包成 SetupError，也不发请求），
        供 sample.py 顶层统一错误出口透传三途径指引。"""
        with mock.patch.object(
            cp.credentials, "resolve_creds", side_effect=CredentialError("三级链全败")
        ):
            with mock.patch.object(cp.rpc, "rpc_call") as m_rpc:
                with self.assertRaises(CredentialError):
                    cp._call(self.config, "GetWorkloadIdentity", {})
        m_rpc.assert_not_called()


class TestCredsResolver(unittest.TestCase):
    """D2：``_CredsResolver`` TTL 缓存替代模块级全局 ``_ACTIVE_CREDS``。

    旧全局缓存的是「解析结果快照」，会让 setup 长跑（最长 SSO_POLL_TIMEOUT=600s）
    期间 SDK 的 OAuth 自动刷新与标准库 sts_expiration 复检全被短路；本解析器
    TTL 内复用、过期重解析，且失败不残留状态。时钟 / 解析函数均可注入（离线）。
    """

    def _make(self, triples, ttl=300.0):
        state = {"n": 0, "t": 1000.0}

        def resolve_func(_config):
            idx = min(state["n"], len(triples) - 1)
            state["n"] += 1
            return triples[idx]

        resolver = cp._CredsResolver(
            {"CONTROL_ENDPOINT": "x"}, ttl=ttl,
            clock=lambda: state["t"], resolve_func=resolve_func,
        )
        return resolver, state

    def test_ttl_within_reuses_cache(self):
        """TTL 内多次 get() 只解析一次（setup ~10 次 _call 不重复进解析逻辑）。"""
        resolver, state = self._make([FAKE_CREDS])
        self.assertEqual(resolver.get(), FAKE_CREDS)
        state["t"] += 100.0  # TTL 内
        self.assertEqual(resolver.get(), FAKE_CREDS)
        self.assertEqual(resolver.get(), FAKE_CREDS)
        self.assertEqual(state["n"], 1)

    def test_ttl_expired_reresolves(self):
        """TTL 过期 → 重解析，拾取刷新后的凭据（如 STS 续期）。"""
        t1 = ("ak-old", "sk-old", "sts-old")
        t2 = ("ak-new", "sk-new", "sts-new")
        resolver, state = self._make([t1, t2], ttl=300.0)
        self.assertEqual(resolver.get(), t1)
        state["t"] += 301.0  # 超过 TTL
        self.assertEqual(resolver.get(), t2)
        self.assertEqual(state["n"], 2)

    def test_failure_leaves_no_cache_and_retries(self):
        """解析失败不写缓存；修好后下次 get() 重解析成功（不被 None 缓存卡死）。"""
        attempts = {"n": 0}

        def flaky(_config):
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise CredentialError("三级链全败")
            return FAKE_CREDS

        resolver = cp._CredsResolver(
            {"CONTROL_ENDPOINT": "x"}, ttl=300.0,
            clock=lambda: 0.0, resolve_func=flaky,
        )
        with self.assertRaises(CredentialError):
            resolver.get()
        self.assertIsNone(resolver._cached)  # 失败不残留缓存
        self.assertIsNone(resolver._cached_at)
        self.assertEqual(resolver.get(), FAKE_CREDS)  # 下次重试成功
        self.assertEqual(attempts["n"], 2)

    def test_resolver_creds_helper(self):
        """``_resolver_creds``：有 resolver → get()；None → None（由 _call 实时解析兜底）。"""
        resolver, _state = self._make([FAKE_CREDS])
        self.assertEqual(cp._resolver_creds(resolver), FAKE_CREDS)
        self.assertIsNone(cp._resolver_creds(None))

    def test_default_resolve_func_is_credentials_resolve_creds(self):
        """未注入 resolve_func 时默认委托 ``credentials.resolve_creds``（与 _call 同源）。"""
        resolver = cp._CredsResolver({"CONTROL_ENDPOINT": "x"}, clock=lambda: 0.0)
        self.assertIs(resolver._resolve, cp.credentials.resolve_creds)


class TestSetupResolverWiring(CleanupTestCase):
    """D2/D11：``run_setup_script`` 外壳——先 ``_require_setup``，再用 ``resolve_creds_detailed``
    解析身份（fail-fast + 回显），构造 ``_CredsResolver`` 显式传给 ``_run_setup_script_inner``。"""

    def test_resolver_passed_to_inner(self):
        seen = {}

        def fake_inner(config, with_scim=False, resolver=None):
            seen["resolver"] = resolver
            return {"USER_POOL_ID": "up_lifecycle"}

        with mock.patch.object(cp, "_run_setup_script_inner", side_effect=fake_inner):
            updates = cp.run_setup_script(config=fake_config())
        self.assertIsInstance(seen["resolver"], cp._CredsResolver)
        self.assertEqual(updates, {"USER_POOL_ID": "up_lifecycle"})
        self.resolve_detailed_mock.assert_called_once()  # 入口解析身份一次

    def test_inner_failure_leaves_no_global_residue(self):
        """inner 失败也不残留任何模块级凭据状态（旧 ``_ACTIVE_CREDS`` 已移除）。"""
        def boom(config, with_scim=False, resolver=None):
            self.assertIsInstance(resolver, cp._CredsResolver)
            raise cp.SetupError("mid-way failure")

        with mock.patch.object(cp, "_run_setup_script_inner", side_effect=boom):
            with self.assertRaises(cp.SetupError):
                cp.run_setup_script(config=fake_config())
        self.assertFalse(hasattr(cp, "_ACTIVE_CREDS"))

    def test_resolve_failure_skips_inner_and_any_creation(self):
        """D11 fail-fast：身份解析失败（半填/三级全败）→ 不进 inner、不发任何创建请求。"""
        self.resolve_detailed_mock.side_effect = CredentialError("三级链全败")
        with mock.patch.object(cp, "_run_setup_script_inner") as m_inner:
            with mock.patch.object(cp, "_call") as m_call:
                with self.assertRaises(CredentialError):
                    cp.run_setup_script(config=fake_config())
        m_inner.assert_not_called()
        m_call.assert_not_called()  # 任何创建操作之前就 fail-fast

    def test_require_setup_runs_before_creds_resolution(self):
        """缺配置时先报缺项，不得先去解析凭据（避免无谓 SDK 开销与误导性错误）。"""
        config = fake_config()
        config.pop("CONTROL_ENDPOINT")
        config.pop("DATA_ENDPOINT")
        with self.assertRaises(cp.SetupError):
            cp.run_setup_script(config=config)
        self.resolve_detailed_mock.assert_not_called()


class TestSetupDiscoveryWriteback(CleanupTestCase):
    """setup 末尾：配了 ``IDAAS_ORIGIN`` 则走 discovery 自动回写 issuer/jwks_uri。"""

    def _run_setup(self, config, apply_mock):
        # 快照每次 writeback_env 的入参副本：run_setup_script 会在第二次回写后
        # ``updates.update(disco_updates)`` 原地突变同一 dict，若直接读
        # m_wb.call_args_list[0] （别名引用）会看到被污染的最终态。
        snapshots = []

        def fake_writeback(upd):
            snapshots.append(dict(upd))
            return "/tmp/env-fake"

        with mock.patch.object(cp, "_call", side_effect=setup_full_success_call):
            with mock.patch.object(cp.discovery, "apply_discovery", apply_mock):
                with mock.patch.object(cp, "writeback_env", side_effect=fake_writeback) as m_wb:
                    updates = cp.run_setup_script(config=config)
        m_wb.snapshots = snapshots
        return updates, m_wb

    def _config_with_origin(self):
        config = fake_config()
        config["IDAAS_ORIGIN"] = FAKE_IDAAS_ORIGIN
        config["SETUP_OBO_PROVIDER_CONFIG"] = '{"clientId": "app_test20", "clientSecret": "sec-unit"}'
        return config

    def test_discovery_result_written_back(self):
        discovered = self._config_with_origin()
        discovered["ORDER_SERVICE_ISSUER"] = FAKE_ISSUER
        discovered["ORDER_SERVICE_JWKS_URI"] = FAKE_JWKS_URI
        apply_mock = mock.Mock(return_value=discovered)
        updates, m_wb = self._run_setup(self._config_with_origin(), apply_mock)
        apply_mock.assert_called_once()
        self.assertEqual(apply_mock.call_args[0][0]["IDAAS_ORIGIN"], FAKE_IDAAS_ORIGIN)
        # 返回的 updates 合并了核心产出 + discovery 两段
        self.assertEqual(updates["ORDER_SERVICE_ISSUER"], FAKE_ISSUER)
        self.assertEqual(updates["ORDER_SERVICE_JWKS_URI"], FAKE_JWKS_URI)
        # D1：两段回写——第一次核心产出（不含 issuer/jwks，先落盘只返回一次的
        # client_secret 等），第二次单独回写 discovery 拉到的 issuer/jwks
        self.assertEqual(m_wb.call_count, 2)
        core = m_wb.snapshots[0]
        disco = m_wb.snapshots[1]
        self.assertNotIn("ORDER_SERVICE_ISSUER", core)
        self.assertNotIn("ORDER_SERVICE_JWKS_URI", core)
        self.assertEqual(core["USER_POOL_ID"], "up_test0020")
        self.assertEqual(core["OAUTH_CLIENT_SECRET"], "sec-unit")
        self.assertEqual(disco, {
            "ORDER_SERVICE_ISSUER": FAKE_ISSUER,
            "ORDER_SERVICE_JWKS_URI": FAKE_JWKS_URI,
        })

    def test_discovery_failure_does_not_break_setup(self):
        apply_mock = mock.Mock(side_effect=cp.discovery.DiscoveryError("HTTP 503"))
        updates, m_wb = self._run_setup(self._config_with_origin(), apply_mock)
        self.assertNotIn("ORDER_SERVICE_ISSUER", updates)
        self.assertNotIn("ORDER_SERVICE_JWKS_URI", updates)
        # 五项核心产出照常回写
        self.assertEqual(updates["USER_POOL_ID"], "up_test0020")
        self.assertEqual(updates["OAUTH_CLIENT_ID"], "client_test20")
        m_wb.assert_called_once()

    def test_discovery_empty_result_not_written(self):
        """discovery 拉到了但 issuer/jwks 仍为空 → 不写空值进 .env。"""
        apply_mock = mock.Mock(return_value=self._config_with_origin())
        updates, _m_wb = self._run_setup(self._config_with_origin(), apply_mock)
        self.assertNotIn("ORDER_SERVICE_ISSUER", updates)
        self.assertNotIn("ORDER_SERVICE_JWKS_URI", updates)

    def test_no_idaas_origin_skips_discovery(self):
        """未配 IDAAS_ORIGIN（离线/air-gapped 场景）→ 不调 discovery，不报错。"""
        config = fake_config()
        config["SETUP_OBO_PROVIDER_CONFIG"] = '{"clientId": "app_test21", "clientSecret": "sec-unit"}'
        apply_mock = mock.Mock()
        updates, _m_wb = self._run_setup(config, apply_mock)
        apply_mock.assert_not_called()
        self.assertNotIn("ORDER_SERVICE_ISSUER", updates)

    def test_explicit_issuer_not_overwritten_by_discovery(self):
        """D7：显式值优先且未变化 → 不进 updates、不触发第二次回写（不抹掉行内注释）。"""
        config = self._config_with_origin()
        config["ORDER_SERVICE_ISSUER"] = "https://explicit-issuer.example.com"
        config["ORDER_SERVICE_JWKS_URI"] = "https://explicit-issuer.example.com/jwks"
        apply_mock = mock.Mock(return_value=dict(config))  # apply_discovery 不改显式值
        updates, m_wb = self._run_setup(config, apply_mock)
        # 值相对 discovery 前未变化 → 不回写这两键（旧实现会重写、抹掉行内注释）
        self.assertNotIn("ORDER_SERVICE_ISSUER", updates)
        self.assertNotIn("ORDER_SERVICE_JWKS_URI", updates)
        m_wb.assert_called_once()  # 只回写核心产出，未触发第二次 disco 回写


class TestRunSetupConsole(unittest.TestCase):
    """G3：``run_setup_console`` 在打印静态清单前先做**纯离线**配置校验。

    旧实现只 ``print(CONSOLE_CHECKLIST)``，``.env`` 写了非法 ``ENVIRONMENT``（如
    ``staging``）时既不报错也不告警、退出码 0，用户会拿着错误配置去控制台点一圈。
    修复后先调 ``env.derive_defaults(env.load_env())``（纯字典运算，无网络 / 无写盘），
    非法值抛 ``EnvError``（继承 ``RpcError``，被 ``sample.py`` 统一出口捕获 → 非 0）；
    校验通过则静态清单输出逐字不变。全程离线：``load_env`` 打桩，``derive_defaults``
    走真实实现（不 mock）。
    """

    def _capture(self, env_dict):
        buf = io.StringIO()
        with mock.patch.object(cp.env_mod, "load_env", return_value=dict(env_dict)), \
                redirect_stdout(buf):
            cp.run_setup_console()
        return buf.getvalue()

    def test_valid_environment_prints_checklist_unchanged(self):
        """合法 ENVIRONMENT（production）→ 静态清单逐字不变（校验不改正文）。"""
        out = self._capture({"ENVIRONMENT": "production"})
        # 校验通过后输出以完整静态清单开头（逐字不变）
        self.assertTrue(out.startswith(cp.CONSOLE_CHECKLIST))
        # 清单后的两行提示也照常输出
        self.assertIn("python3 sample.py setup --mode=script", out)

    def test_default_environment_prints_checklist(self):
        """缺省 ENVIRONMENT（键不存在）→ derive_defaults 默认 production → 清单照常。"""
        out = self._capture({})
        self.assertTrue(out.startswith(cp.CONSOLE_CHECKLIST))

    def test_invalid_environment_raises_env_error(self):
        """非法 ENVIRONMENT（staging）→ 抛 EnvError，且在打印清单之前 fail-fast。"""
        buf = io.StringIO()
        with mock.patch.object(cp.env_mod, "load_env", return_value={"ENVIRONMENT": "staging"}):
            with redirect_stdout(buf):
                with self.assertRaises(cp.env_mod.EnvError) as ctx:
                    cp.run_setup_console()
        self.assertIn("ENVIRONMENT", str(ctx.exception))
        # EnvError 继承 RpcError → 被 sample.py 统一错误出口捕获（非 0 退出）
        self.assertTrue(issubclass(cp.env_mod.EnvError, RpcError))
        # 校验失败发生在打印清单之前 → 不泄露半截清单
        self.assertNotIn("管控面资源准备清单", buf.getvalue())


# ---------------------------------------------------------------------------
# D-Minor4：身份回显文本锁定（setup 与 cleanup 两路径）
# ---------------------------------------------------------------------------


class TestIdentityEchoSetup(CleanupTestCase):
    """setup 身份回显必含三要素：来源、掩码 AK、含 STS。"""

    def test_setup_echo_contains_source_mask_ak_sts(self):
        fake_resolved = cp.credentials.ResolvedCreds(
            "LTAIFAKEFAKEFAKEFAKE", "sk-fake", "STS.FAKEFAKE",
            cp.credentials.LEVEL_STDLIB,
            "~/.aliyun/config.json(profile=default, mode=StsToken)",
        )
        with mock.patch.object(cp.credentials, "resolve_creds_detailed", return_value=fake_resolved), \
                mock.patch.object(cp, "_run_setup_script_inner", return_value={}), \
                redirect_stdout(io.StringIO()) as buf:
            cp.run_setup_script(config=fake_config())
        out = buf.getvalue()
        # 三要素：来源、掩码 AK、含 STS
        self.assertIn("~/.aliyun/config.json", out)  # 来源
        self.assertIn("LTAI", out)                   # 掩码前 4 字符
        self.assertIn("含 STS=是", out)              # 含 STS
        self.assertNotIn("LTAIFAKEFAKEFAKEFAKE", out)  # 不泄漏完整 AK


class TestIdentityEchoCleanup(CleanupTestCase):
    """cleanup 身份回显必含三要素：来源、掩码 AK、含 STS；且回显早于确认提示。"""

    def test_cleanup_echo_contains_source_mask_ak_sts(self):
        self.write_manifest([{"type": "user_pool", "name": "pool-echo"}])
        fake_resolved = cp.credentials.ResolvedCreds(
            "LTAIFAKEFAKEFAKEFAKE", "sk-fake", None,
            cp.credentials.LEVEL_EXPLICIT,
            ".env 显式 ALIYUN_ACCESS_KEY_*",
        )
        with mock.patch.object(cp.credentials, "resolve_creds_detailed", return_value=fake_resolved), \
                mock.patch.object(cp, "_call", return_value={"RequestId": "r"}), \
                redirect_stdout(io.StringIO()) as buf:
            cp.run_cleanup(assume_yes=True)
        out = buf.getvalue()
        self.assertIn(".env 显式 ALIYUN_ACCESS_KEY_*", out)  # 来源
        self.assertIn("LTAI", out)                           # 掩码
        self.assertIn("含 STS=否", out)                      # 含 STS

    def test_cleanup_echo_before_confirmation_prompt(self):
        """时序：回显早于确认提示（input 之前已打印回显）。"""
        self.write_manifest([{"type": "user_pool", "name": "pool-time"}])
        fake_resolved = cp.credentials.ResolvedCreds(
            "LTAIFAKEFAKEFAKEFAKE", "sk-fake", "STS.FAKEFAKE",
            cp.credentials.LEVEL_STDLIB, "~/.aliyun/config.json(profile=default)",
        )
        printed_before_input = []

        def fake_input(prompt=""):
            # input 被调用时，捕获当前已打印的内容
            printed_before_input.append(buf.getvalue())
            return "no"  # 取消删除

        buf = io.StringIO()
        with mock.patch.object(cp.credentials, "resolve_creds_detailed", return_value=fake_resolved), \
                mock.patch("builtins.input", side_effect=fake_input), \
                redirect_stdout(buf):
            cp.run_cleanup(assume_yes=False)
        # 回显在 input 之前已打印
        self.assertTrue(len(printed_before_input) > 0)
        echo_text = printed_before_input[0]
        self.assertIn("LTAI", echo_text)
        self.assertIn("含 STS=是", echo_text)
        self.assertIn("来源", echo_text)

    def test_from_env_echo_contains_three_elements(self):
        """--from-env 路径的身份回显也必含三要素。"""
        fake_resolved = cp.credentials.ResolvedCreds(
            "LTAIFAKEFAKEFAKEFAKE", "sk-fake", "STS.FAKEFAKE",
            cp.credentials.LEVEL_SDK, "CLIProfileCredentialsProvider",
        )
        with mock.patch.object(cp.credentials, "resolve_creds_detailed", return_value=fake_resolved), \
                mock.patch.object(cp, "_call", return_value={"RequestId": "r"}), \
                redirect_stdout(io.StringIO()) as buf:
            cp.run_cleanup(assume_yes=True, from_env=True)
        out = buf.getvalue()
        self.assertIn("CLIProfileCredentialsProvider", out)  # 来源
        self.assertIn("LTAI", out)                           # 掩码
        self.assertIn("含 STS=是", out)                      # 含 STS


if __name__ == "__main__":
    unittest.main()
