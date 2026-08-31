"""env 解析 / 占位符检测 / --check 指引 / 密钥文件优先级测试。"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import env as env_mod  # noqa: E402


class TestParseEnvFile(unittest.TestCase):
    def _write(self, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".env")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        return path

    def test_basic_parsing(self):
        path = self._write(
            "# 注释行\n"
            "REGION=cn-hangzhou\n"
            "KEY_WITH_SPACES = value with spaces  \n"
            "QUOTED=\"double quoted\"\n"
            "SINGLE='single quoted'\n"
            "\n"
            "EMPTY=\n"
        )
        parsed = env_mod.parse_env_file(path)
        self.assertEqual(parsed["REGION"], "cn-hangzhou")
        # 键值两端空白剥离
        self.assertEqual(parsed["KEY_WITH_SPACES"], "value with spaces")
        # 成对引号剥离
        self.assertEqual(parsed["QUOTED"], "double quoted")
        self.assertEqual(parsed["SINGLE"], "single quoted")
        # 空值保留（由 is_placeholder 判缺失）
        self.assertEqual(parsed["EMPTY"], "")
        os.unlink(path)

    def test_malformed_lines_skipped(self):
        path = self._write("no_equal_sign_line\n=VALUE_ONLY\nREGION=ok\n")
        parsed = env_mod.parse_env_file(path)
        self.assertEqual(parsed, {"REGION": "ok"})
        os.unlink(path)

    def test_missing_file_returns_empty(self):
        self.assertEqual(env_mod.parse_env_file("/nonexistent/.env"), {})

    def test_hash_inside_value_kept(self):
        path = self._write("AUDIENCE=agent-abc#not-a-comment\n")
        parsed = env_mod.parse_env_file(path)
        self.assertEqual(parsed["AUDIENCE"], "agent-abc#not-a-comment")
        os.unlink(path)


class TestPlaceholderDetection(unittest.TestCase):
    def test_empty_is_missing(self):
        self.assertTrue(env_mod.is_placeholder(""))
        self.assertTrue(env_mod.is_placeholder("   "))

    def test_template_placeholder_is_missing(self):
        self.assertTrue(env_mod.is_placeholder("<YOUR_USER_POOL_ID>"))
        self.assertTrue(env_mod.is_placeholder("<agentidentity.YOUR_REGION.aliyuncs.com>"))

    def test_real_value_ok(self):
        # 末位用非 hex 字符 z：验证「正常形态值不被误判为占位符」，
        # 同时避免仓库内出现 32 位连续 hex（触发敏感值扫描门禁）
        self.assertFalse(env_mod.is_placeholder("up_0000000000000000000000000000000z"))
        self.assertFalse(env_mod.is_placeholder("cn-hangzhou"))


class TestCheckEnv(unittest.TestCase):
    def test_full_config_passes(self):
        env = {key: "value-{}".format(i) for i, key in enumerate(env_mod.ENV_SCHEMA)}
        ok, missing = env_mod.check_env(env)
        self.assertTrue(ok)
        self.assertEqual(missing, [])

    def test_missing_required_reported_with_hint(self):
        env = {key: "v" for key in env_mod.ENV_SCHEMA if key != "USER_POOL_ID"}
        ok, missing = env_mod.check_env(env)
        self.assertFalse(ok)
        self.assertEqual(missing, ["USER_POOL_ID"])

    def test_placeholder_treated_as_missing(self):
        env = {key: "v" for key in env_mod.ENV_SCHEMA}
        env["SIGNIN_BASE_URL"] = "<https://signin.YOUR_REGION.aliyuncs.com>"
        ok, missing = env_mod.check_env(env)
        self.assertFalse(ok)
        self.assertIn("SIGNIN_BASE_URL", missing)

    def test_setup_keys_skipped_by_default(self):
        """SETUP_* 仅 setup --mode=script 需要：默认体检跳过。"""
        env = {key: "v" for key in env_mod.ENV_SCHEMA if key not in env_mod.SETUP_ONLY_KEYS}
        ok, _ = env_mod.check_env(env)
        self.assertTrue(ok)

    def test_setup_keys_checked_when_requested(self):
        env = {key: "v" for key in env_mod.ENV_SCHEMA if key not in env_mod.SETUP_ONLY_KEYS}
        ok, missing = env_mod.check_env(env, skip_setup_keys=False)
        self.assertFalse(ok)
        self.assertTrue(set(missing) <= env_mod.SETUP_ONLY_KEYS)

    def test_optional_key_empty_is_fine(self):
        env = {key: "v" for key in env_mod.ENV_SCHEMA}
        env["ALIYUN_SECURITY_TOKEN"] = ""
        ok, _ = env_mod.check_env(env)
        self.assertTrue(ok)


class TestRenderCheckReport(unittest.TestCase):
    def test_report_contains_where_to_fill_hints(self):
        report = env_mod.render_check_report({})  # 空 env：全部缺失
        self.assertIn("[MISSING]", report)
        self.assertIn("在哪取值", report)
        self.assertIn("USER_POOL_ID", report)
        self.assertIn("体检未通过", report)
        # 不回显任何值
        self.assertNotIn("value-", report)

    def test_report_masks_secrets(self):
        env = {key: "v" for key in env_mod.ENV_SCHEMA}
        env["ALIYUN_ACCESS_KEY_SECRET"] = "super-secret-value-123"
        report = env_mod.render_check_report(env)
        self.assertIn("体检通过", report)
        self.assertNotIn("super-secret-value-123", report)  # 密钥只显示 len
        self.assertIn("ALIYUN_ACCESS_KEY_SECRET (len=", report)


class TestEnvTemplateConsistency(unittest.TestCase):
    """env.template 与 ENV_SCHEMA 的一致性（模板是用户唯一的填写入口）。"""

    def setUp(self):
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "env.template"
        )
        self.parsed = env_mod.parse_env_file(template_path)

    def test_template_covers_all_schema_keys(self):
        missing = set(env_mod.ENV_SCHEMA) - set(self.parsed)
        self.assertEqual(missing, set(), "env.template 缺少键：{}".format(sorted(missing)))

    def test_template_values_all_placeholder_or_default(self):
        """模板值只允许占位符（<YOUR_）或空值或显式默认（不含任何真实值）。"""
        allowed_defaults = {
            "ALIYUN_SECURITY_TOKEN": "",
            "OAUTH_CLIENT_SECRET_FILE": "",
            "OAUTH_REDIRECT_URI": "http://127.0.0.1:8765/callback",
            "ORDER_SERVICE_SCOPES": "read,write.all",
            "SETUP_POOL_NAME": "idaas-obo-sample-pool",
            "SETUP_CLIENT_NAME": "idaas-obo-sample-cli",
            "SETUP_IDP_NAME": "idaas-obo-sample-idp",
            "SETUP_IDP_TYPE": "IDaaS",
            "SETUP_IDP_METADATA": "",
            "SETUP_OBO_VENDOR": "IDaaS",
            "SETUP_OBO_PROVIDER_CONFIG": "",
        }
        for key, value in self.parsed.items():
            if value == "" or "<YOUR_" in value or allowed_defaults.get(key) == value:
                continue
            self.fail("env.template 的 {}={} 不是占位符/默认值（疑似真实值）".format(key, value))

    def test_required_keys_are_placeholder_in_template(self):
        """必填键在模板中必须是 <YOUR_ 占位（保证用户不漏填）。"""
        for key, (required, _g, _h) in env_mod.ENV_SCHEMA.items():
            if required and key != "OAUTH_REDIRECT_URI":
                self.assertIn(
                    "<YOUR_",
                    self.parsed.get(key, ""),
                    "必填键 {} 在模板中应为 <YOUR_ 占位符".format(key),
                )


class TestGetSecret(unittest.TestCase):
    def test_file_takes_priority(self):
        with tempfile.TemporaryDirectory() as tmp:
            secret_file = os.path.join(tmp, "client_secret")
            with open(secret_file, "w", encoding="utf-8") as fh:
                fh.write("secret-from-file\n")
            env = {"OAUTH_CLIENT_SECRET": "secret-from-env", "OAUTH_CLIENT_SECRET_FILE": secret_file}
            self.assertEqual(
                env_mod.get_secret(env, "OAUTH_CLIENT_SECRET", "OAUTH_CLIENT_SECRET_FILE", "x"),
                "secret-from-file",
            )

    def test_env_value_when_no_file(self):
        env = {"OAUTH_CLIENT_SECRET": "secret-from-env", "OAUTH_CLIENT_SECRET_FILE": ""}
        self.assertEqual(
            env_mod.get_secret(env, "OAUTH_CLIENT_SECRET", "OAUTH_CLIENT_SECRET_FILE", "x"),
            "secret-from-env",
        )

    def test_missing_file_raises_with_hint(self):
        env = {"OAUTH_CLIENT_SECRET": "", "OAUTH_CLIENT_SECRET_FILE": "/nonexistent/secret"}
        with self.assertRaises(KeyError) as ctx:
            env_mod.get_secret(env, "OAUTH_CLIENT_SECRET", "OAUTH_CLIENT_SECRET_FILE", "x")
        self.assertIn("不存在", str(ctx.exception))

    def test_placeholder_raises_with_hint(self):
        env = {"OAUTH_CLIENT_SECRET": "<YOUR_OAUTH_CLIENT_SECRET>", "OAUTH_CLIENT_SECRET_FILE": ""}
        with self.assertRaises(KeyError) as ctx:
            env_mod.get_secret(env, "OAUTH_CLIENT_SECRET", "OAUTH_CLIENT_SECRET_FILE", "x")
        self.assertIn("在哪取值", str(ctx.exception))


class TestDeriveDefaults(unittest.TestCase):
    def test_region_fallback_from_control_endpoint(self):
        env = env_mod.derive_defaults({"CONTROL_ENDPOINT": "agentidentity.cn-hangzhou.aliyuncs.com"})
        self.assertEqual(env["REGION"], "cn-hangzhou")

    def test_region_fallback_from_data_endpoint(self):
        env = env_mod.derive_defaults({"DATA_ENDPOINT": "agentidentitydata.cn-beijing.aliyuncs.com"})
        self.assertEqual(env["REGION"], "cn-beijing")

    def test_defaults_filled(self):
        env = env_mod.derive_defaults({})
        self.assertEqual(env["ORDER_SERVICE_SCOPES"], "read,write.all")
        self.assertEqual(env["OAUTH_REDIRECT_URI"], "http://127.0.0.1:8765/callback")
        self.assertEqual(env["SETUP_POOL_NAME"], "idaas-obo-sample-pool")


if __name__ == "__main__":
    unittest.main()
