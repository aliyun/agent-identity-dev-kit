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

所有外部交互（RPC 调用 / stdin 确认 / 清单文件）均被 mock 或指向临时目录。
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
from lib.rpc import RpcError  # noqa: E402


def fake_config() -> dict:
    """能通过 _require_setup 的最小配置（值全部为测试占位，非真实凭据）。"""
    return {
        "ALIYUN_ACCESS_KEY_ID": "ak-unit-test",
        "ALIYUN_ACCESS_KEY_SECRET": "sk-unit-test",
        "CONTROL_ENDPOINT": "agentidentity.cn-test.aliyuncs.com",
        "DATA_ENDPOINT": "agentidentitydata.cn-test.aliyuncs.com",
        "OAUTH_REDIRECT_URI": "http://127.0.0.1:8765/callback",
        "SETUP_POOL_NAME": "env-pool",
        "SETUP_CLIENT_NAME": "env-cli",
        "SETUP_IDP_NAME": "env-idp",
        "WI_NAME": "env-wi",
        "OBO_PROVIDER_NAME": "env-provider",
    }


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

        def fake_call(cfg, action, params=None, style="query", logger=None):
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

        def fake_call(cfg, action, params=None, style="query", logger=None):
            return responses[action]

        with mock.patch.object(cp, "_call", side_effect=fake_call):
            pool_id, _pool_name, created = cp._ensure_pool(self.config, noop_logger)
        self.assertEqual(pool_id, "up_test0002")
        self.assertTrue(created)

    def test_reused_pool_reports_not_created(self):
        responses = {
            "ListUserPools": {"UserPools": [{"UserPoolName": "env-pool", "UserPoolId": "up_test0003"}]},
        }

        def fake_call(cfg, action, params=None, style="query", logger=None):
            return responses[action]

        with mock.patch.object(cp, "_call", side_effect=fake_call):
            pool_id, _pool_name, created = cp._ensure_pool(self.config, noop_logger)
        self.assertEqual(pool_id, "up_test0003")
        self.assertFalse(created)

    def test_create_user_pool_client_nested_shape(self):
        def fake_call(cfg, action, params=None, style="query", logger=None):
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
        def fake_call(cfg, action, params=None, style="query", logger=None):
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

        def fake_call(cfg, action, params=None, style="query", logger=None):
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

        def fake_call(cfg, action, params=None, style="query", logger=None):
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
            "ALIYUN_ACCESS_KEY_ID": "ak-unit-test",
            "ALIYUN_ACCESS_KEY_SECRET": "sk-unit-test",
        }
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


# ---------------------------------------------------------------------------
# 缺陷 #4：cleanup 防误删（清单机制三路径 + setup 写清单）
# ---------------------------------------------------------------------------


class CleanupTestCase(unittest.TestCase):
    """基类：清单文件指向临时目录，.env 读取替换为内存 fake 配置。"""

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


class TestCleanupByManifest(CleanupTestCase):
    def test_deletes_in_reverse_order_then_removes_manifest(self):
        self.write_manifest([
            {"type": "user_pool", "name": "pool-a", "created_at": "2026-01-01T00:00:00Z"},
            {"type": "pool_client", "name": "cli-a", "pool_name": "pool-a", "created_at": "2026-01-01T00:00:01Z"},
        ])
        calls = []

        def fake_call(cfg, action, params=None, style="query", logger=None):
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

        def fake_call(cfg, action, params=None, style="query", logger=None):
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

        def fake_call(cfg, action, params=None, style="query", logger=None):
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

        def fake_call(cfg, action, params=None, style="query", logger=None):
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

        def fake_call(cfg, action, params=None, style="query", logger=None):
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
        def fake_call(cfg, action, params=None, style="query", logger=None):
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
        def fake_call(cfg, action, params=None, style="query", logger=None):
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

        def fake_call(cfg, action, params=None, style="query", logger=None):
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


if __name__ == "__main__":
    unittest.main()
