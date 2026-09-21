"""env 解析 / 占位符检测 / --check 指引 / 密钥文件优先级 / 派生规则测试。

派生规则（``derive_defaults``）覆盖两个方向，且必须**纯离线**（仅字典运算，
无网络/文件 IO 副作用——discovery 拉取由 ``lib/discovery.py`` 独立承担）：
- 反向兜底：CONTROL/DATA_ENDPOINT → REGION；ORDER_SERVICE_ISSUER → IDAAS_ORIGIN；
- 正向派生：REGION → CONTROL/DATA_ENDPOINT；ENVIRONMENT+REGION → SIGNIN_BASE_URL。
两方向都遵守「显式值永远优先」（仅当目标键为占位/空才填），保证向后兼容。

ENVIRONMENT 专项约束（本文件重点锁定）：
- 归一化：``strip().lower()``；缺失/占位 → ``production``；
- 白名单：非 ``production``/``pre-release`` → 抛 ``EnvError``（继承 ``RpcError``，
  已在 sample.py 的统一错误出口白名单内）；
- ``POOL_JWKS_BASE`` 镜像门控：只有用户**显式声明** ENVIRONMENT=production 才镜像为
  SIGNIN_BASE_URL。存量 .env（无 ENVIRONMENT 键）必须保持旧行为：POOL_JWKS_BASE
  留空 → ``control_plane._pool_wellknown_host()`` 走 DATA_ENDPOINT。

``render_check_report`` 需区分「.env 实填值」与「派生值」（传入派生前快照
``raw_env`` 时，派生键标注 ``（已派生）``），且不传 ``raw_env`` 时行为向后兼容。
"""

import contextlib
import io
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import env as env_mod  # noqa: E402
from lib.rpc import RpcError  # noqa: E402


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


class TestLoadEnv(unittest.TestCase):
    """``load_env``：.env + 进程环境变量叠加（环境变量优先，且两侧都 strip）。"""

    def _write(self, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".env")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        self.addCleanup(os.unlink, path)
        return path

    def _set_environ(self, key: str, value: str) -> None:
        old = os.environ.get(key)
        os.environ[key] = value
        if old is None:
            self.addCleanup(os.environ.pop, key, None)
        else:
            self.addCleanup(os.environ.__setitem__, key, old)

    def test_os_environ_overrides_env_file(self):
        path = self._write("REGION=cn-hangzhou\n")
        self._set_environ("REGION", "ap-southeast-1")
        self.assertEqual(env_mod.load_env(path)["REGION"], "ap-southeast-1")

    def test_os_environ_values_are_stripped(self):
        """进程环境变量也 strip：与 parse_env_file 语义对齐。

        不 strip 的后果：CI 注入 ``ENVIRONMENT=" pre-release "`` 时，归一化前的
        字串相等判断全部落空 → 静默按 production 派生出正式登录域。
        """
        path = self._write("REGION=cn-hangzhou\nSIGNIN_BASE_URL=\n")
        self._set_environ("SIGNIN_BASE_URL", "  https://signin.cn-hangzhou.aliyuncs.com  ")
        self._set_environ("REGION", "\tap-southeast-1\n")
        env = env_mod.load_env(path)
        self.assertEqual(env["SIGNIN_BASE_URL"], "https://signin.cn-hangzhou.aliyuncs.com")
        self.assertEqual(env["REGION"], "ap-southeast-1")

    def test_whitespace_only_os_environ_does_not_clobber_env_file(self):
        """strip 后为空 → 视为未注入，保留 .env 里的值（而不是覆盖成空白占位）。"""
        path = self._write("SIGNIN_BASE_URL=https://signin.cn-hangzhou.aliyuncs.com\n")
        self._set_environ("SIGNIN_BASE_URL", "   ")
        self.assertEqual(
            env_mod.load_env(path)["SIGNIN_BASE_URL"],
            "https://signin.cn-hangzhou.aliyuncs.com",
        )

    def test_only_schema_keys_picked_from_os_environ(self):
        """环境变量只叠加 ENV_SCHEMA 内的键（避免无关变量污染配置）。"""
        path = self._write("REGION=cn-hangzhou\n")
        self._set_environ("NOT_IN_SCHEMA_AT_ALL", "x")
        self.assertNotIn("NOT_IN_SCHEMA_AT_ALL", env_mod.load_env(path))


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
        # 用仍为必填的 USER_POOL_ID 验证「占位符等同缺失」：
        # SIGNIN_BASE_URL 等已降级为可选（由 REGION+ENVIRONMENT 派生），不再触发 missing
        env = {key: "v" for key in env_mod.ENV_SCHEMA}
        env["USER_POOL_ID"] = "<YOUR_USER_POOL_ID>"
        ok, missing = env_mod.check_env(env)
        self.assertFalse(ok)
        self.assertIn("USER_POOL_ID", missing)

    def test_derivable_keys_placeholder_not_reported_missing(self):
        """配置精简后可派生/可 discovery 的键降级为可选：留空或占位都不算缺失。"""
        env = {key: "v" for key in env_mod.ENV_SCHEMA}
        for key in (
            "SIGNIN_BASE_URL",
            "CONTROL_ENDPOINT",
            "DATA_ENDPOINT",
            "POOL_JWKS_BASE",
            "ORDER_SERVICE_ISSUER",
            "ORDER_SERVICE_JWKS_URI",
        ):
            env[key] = "<YOUR_{}>".format(key)
        ok, missing = env_mod.check_env(env)
        self.assertTrue(ok)
        self.assertEqual(missing, [])

    def test_credential_keys_optional(self):
        """AK/SK 降级为可选（留空走凭据链）：不得再计入缺失。"""
        env = {key: "v" for key in env_mod.ENV_SCHEMA}
        env["ALIYUN_ACCESS_KEY_ID"] = ""
        env["ALIYUN_ACCESS_KEY_SECRET"] = ""
        env["ALIYUN_SECURITY_TOKEN"] = ""
        ok, missing = env_mod.check_env(env)
        self.assertTrue(ok)
        self.assertEqual(missing, [])

    def test_required_key_set_is_simplified(self):
        """必填名单锁定：客户手填只剩 REGION/ORDER_SERVICE_AUDIENCE/IDAAS_ORIGIN
        三项，其余必填项均为 setup 产出（管控面资源 ID）。"""
        required = {key for key, (req, _g, _h) in env_mod.ENV_SCHEMA.items() if req}
        self.assertEqual(
            required,
            {
                "REGION",
                "USER_POOL_ID",
                "OAUTH_CLIENT_ID",
                "OAUTH_CLIENT_SECRET",
                "OAUTH_REDIRECT_URI",
                "WI_NAME",
                "OBO_PROVIDER_NAME",
                "ORDER_SERVICE_AUDIENCE",
                "IDAAS_ORIGIN",
            },
        )
        # 凭据链与派生/discovery 兜底的键一律非必填
        for key in (
            "ALIYUN_ACCESS_KEY_ID",
            "ALIYUN_ACCESS_KEY_SECRET",
            "CONTROL_ENDPOINT",
            "DATA_ENDPOINT",
            "SIGNIN_BASE_URL",
            "ORDER_SERVICE_ISSUER",
            "ORDER_SERVICE_JWKS_URI",
            "ENVIRONMENT",
        ):
            self.assertFalse(env_mod.ENV_SCHEMA[key][0], "{} 应为可选".format(key))

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
    #: 一份能通过体检的「用户实填」配置（不含任何可派生端点）。
    _RAW_BASE = {
        "REGION": "ap-southeast-1",
        "USER_POOL_ID": "up_demo0001",
        "OAUTH_CLIENT_ID": "client_demo01",
        "OAUTH_CLIENT_SECRET": "sec-demo-01",
        "OAUTH_REDIRECT_URI": "http://127.0.0.1:8765/callback",
        "WI_NAME": "demo-wi",
        "OBO_PROVIDER_NAME": "demo-provider",
        "ORDER_SERVICE_AUDIENCE": "test-aud",
        "IDAAS_ORIGIN": "https://idaas-demo.example.com",
    }

    def _raw(self, **overrides):
        raw = dict(self._RAW_BASE)
        raw.update(overrides)
        return raw

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

    def test_skip_setup_keys_positional_arg_still_works(self):
        """签名向后兼容：``skip_setup_keys`` 仍可位置传参（raw_env 只追加在末位）。"""
        env = {key: "v" for key in env_mod.ENV_SCHEMA}
        self.assertIn("SETUP_POOL_NAME", env_mod.render_check_report(env, False))
        self.assertNotIn("SETUP_POOL_NAME", env_mod.render_check_report(env))

    # ---- raw_env 未传：行为与历史一致（向后兼容）----

    def test_without_raw_env_no_derived_mark(self):
        """不传 raw_env → 不加「（已派生）」标记，[OK] 行格式与历史完全一致。"""
        raw = self._raw(ENVIRONMENT="production")
        with contextlib.redirect_stderr(io.StringIO()):
            config = env_mod.derive_defaults(raw)
        report = env_mod.render_check_report(config)
        self.assertNotIn("（已派生）", report)
        lines = report.splitlines()
        self.assertIn(
            "  [OK] CONTROL_ENDPOINT = agentidentity.ap-southeast-1.aliyuncs.com", lines
        )
        self.assertIn(
            "  [OK] POOL_JWKS_BASE = https://signin-ap-southeast-1.aliyunagentid.com", lines
        )
        # 尾部 ENVIRONMENT 生效值行仍在（无快照时不臆断来源）
        self.assertIn("[check] ENVIRONMENT 生效值：production", lines)
        self.assertIn("体检通过", report)

    # ---- raw_env 传入：区分实填值与派生值 ----

    def test_with_raw_env_derived_keys_marked(self):
        raw = self._raw(ENVIRONMENT="production")
        with contextlib.redirect_stderr(io.StringIO()):
            config = env_mod.derive_defaults(raw)
        lines = env_mod.render_check_report(config, raw_env=raw).splitlines()
        # .env 里根本没写的键 → 标记已派生
        self.assertIn(
            "  [OK] CONTROL_ENDPOINT = agentidentity.ap-southeast-1.aliyuncs.com（已派生）", lines
        )
        self.assertIn(
            "  [OK] DATA_ENDPOINT = agentidentitydata.ap-southeast-1.aliyuncs.com（已派生）", lines
        )
        self.assertIn(
            "  [OK] SIGNIN_BASE_URL = https://signin-ap-southeast-1.aliyunagentid.com（已派生）",
            lines,
        )
        self.assertIn(
            "  [OK] POOL_JWKS_BASE = https://signin-ap-southeast-1.aliyunagentid.com（已派生）",
            lines,
        )
        # 用户实填的键 → 不带标记
        self.assertIn("  [OK] REGION = ap-southeast-1", lines)
        self.assertIn("  [OK] ENVIRONMENT = production", lines)
        self.assertIn("  [OK] USER_POOL_ID = up_demo0001", lines)
        self.assertIn("  [OK] IDAAS_ORIGIN = https://idaas-demo.example.com", lines)
        # 尾部回显生效值 + 来源
        self.assertIn(
            "[check] ENVIRONMENT 生效值：production（来源：.env/环境变量显式填写）", lines
        )

    def test_with_raw_env_legacy_shape_marks_environment_as_derived(self):
        """存量 .env（无 ENVIRONMENT 键）：ENVIRONMENT 本身是默认值 → 标记已派生，
        且 POOL_JWKS_BASE 未被镜像（仍为可选未填），来源行说明是默认 production。

        与 Critical-1 联动：用户看到「已派生/默认」就知道这不是自己配的值。
        """
        raw = self._raw()  # 无 ENVIRONMENT
        config = env_mod.derive_defaults(raw)
        report = env_mod.render_check_report(config, raw_env=raw)
        lines = report.splitlines()
        self.assertIn("  [OK] ENVIRONMENT = production（已派生）", lines)
        self.assertIn("  [OPTIONAL-EMPTY] POOL_JWKS_BASE（可选，未填）", lines)
        self.assertIn(
            "[check] ENVIRONMENT 生效值：production（来源：未在 .env/环境变量声明，"
            "默认 production）",
            lines,
        )
        self.assertIn("体检通过", report)

    def test_with_raw_env_pre_release_source_line(self):
        raw = self._raw(ENVIRONMENT="Pre-Release")  # 归一化后 pre-release
        config = env_mod.derive_defaults(raw)
        lines = env_mod.render_check_report(config, raw_env=raw).splitlines()
        self.assertIn(
            "[check] ENVIRONMENT 生效值：pre-release（来源：.env/环境变量显式填写）", lines
        )
        self.assertIn("  [OK] ENVIRONMENT = pre-release", lines)
        self.assertIn(
            "  [OK] SIGNIN_BASE_URL = https://signin.ap-southeast-1.aliyuncs.com（已派生）", lines
        )
        self.assertIn("  [OPTIONAL-EMPTY] POOL_JWKS_BASE（可选，未填）", lines)

    def test_with_raw_env_secrets_still_masked(self):
        """传 raw_env 不得放宽掩码策略：含 SECRET/ACCESS_KEY/TOKEN 的键仍只显示长度。"""
        raw = self._raw(
            ALIYUN_ACCESS_KEY_ID="akid-demo-0001",
            ALIYUN_ACCESS_KEY_SECRET="super-secret-value-123",
            ALIYUN_SECURITY_TOKEN="sts-token-demo",
        )
        config = env_mod.derive_defaults(raw)
        report = env_mod.render_check_report(config, raw_env=raw)
        for secret in ("super-secret-value-123", "akid-demo-0001", "sts-token-demo", "sec-demo-01"):
            self.assertNotIn(secret, report)
        self.assertIn(
            "  [OK] ALIYUN_ACCESS_KEY_SECRET (len={})".format(len("super-secret-value-123")),
            report.splitlines(),
        )
        self.assertIn(
            "  [OK] OAUTH_CLIENT_SECRET (len={})".format(len(self._RAW_BASE["OAUTH_CLIENT_SECRET"])),
            report.splitlines(),
        )

    def test_placeholder_in_raw_env_counts_as_derived(self):
        """raw 里是模板占位符（<YOUR_…）也算「未填」：派生后应标记已派生。"""
        raw = self._raw(CONTROL_ENDPOINT="<agentidentity.YOUR_REGION.aliyuncs.com>")
        config = env_mod.derive_defaults(raw)
        self.assertIn(
            "  [OK] CONTROL_ENDPOINT = agentidentity.ap-southeast-1.aliyuncs.com（已派生）",
            env_mod.render_check_report(config, raw_env=raw).splitlines(),
        )

    def test_explicit_value_not_marked_even_if_equal_to_derivation(self):
        """用户实填的值即使与派生结果相同，也不得标记为已派生。"""
        raw = self._raw(CONTROL_ENDPOINT="agentidentity.ap-southeast-1.aliyuncs.com")
        config = env_mod.derive_defaults(raw)
        self.assertIn(
            "  [OK] CONTROL_ENDPOINT = agentidentity.ap-southeast-1.aliyuncs.com",
            env_mod.render_check_report(config, raw_env=raw).splitlines(),
        )


class TestEnvTemplateConsistency(unittest.TestCase):
    """env.template 与 ENV_SCHEMA 的一致性（模板是用户唯一的填写入口）。"""

    def setUp(self):
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "env.template"
        )
        self.parsed = env_mod.parse_env_file(template_path)
        with open(template_path, "r", encoding="utf-8") as fh:
            self.raw = fh.read()

    def _comment_above(self, key: str) -> str:
        """取模板中 ``KEY=`` 行上方连续的注释块（验证注释文案已同步）。"""
        lines = self.raw.splitlines()
        idx = next(i for i, line in enumerate(lines) if line.startswith(key + "="))
        block = []
        for line in reversed(lines[:idx]):
            if not line.startswith("#"):
                break
            block.append(line)
        return "\n".join(reversed(block))

    def test_template_covers_all_schema_keys(self):
        missing = set(env_mod.ENV_SCHEMA) - set(self.parsed)
        self.assertEqual(missing, set(), "env.template 缺少键：{}".format(sorted(missing)))

    def test_template_has_no_unknown_keys(self):
        """反向一致：模板不得出现 schema 外的键（避免用户填了不生效的项）。"""
        extra = set(self.parsed) - set(env_mod.ENV_SCHEMA)
        self.assertEqual(extra, set(), "env.template 出现 schema 未定义的键：{}".format(sorted(extra)))

    def test_new_keys_present_in_template(self):
        """本次新增的两键必须在模板里（用户唯一的填写入口）。"""
        self.assertIn("IDAAS_ORIGIN", self.parsed)
        self.assertIn("ENVIRONMENT", self.parsed)
        self.assertEqual(self.parsed["ENVIRONMENT"], "production")  # 默认值直写模板

    def test_environment_comment_documents_whitelist_and_legacy_escape(self):
        """ENVIRONMENT 注释必须写明：合法取值只有两个（归一化、非法值报错），
        以及删除本行/留空可保持存量向后兼容行为。"""
        comment = self._comment_above("ENVIRONMENT")
        self.assertIn("production", comment)
        self.assertIn("pre-release", comment)
        self.assertIn("归一化", comment)
        self.assertIn("报错", comment)
        self.assertIn("删除本行", comment)  # 存量用户的逃生通道

    def test_pool_jwks_comment_documents_gating(self):
        """POOL_JWKS_BASE 注释必须说明留空时的两种情形（镜像 / 走 DATA_ENDPOINT）。"""
        comment = self._comment_above("POOL_JWKS_BASE")
        self.assertIn("ENVIRONMENT=production", comment)  # 镜像条件
        self.assertIn("SIGNIN_BASE_URL", comment)
        self.assertIn("DATA_ENDPOINT", comment)          # 旧行为（未声明/pre-release）
        self.assertIn("pre-release", comment)

    def test_template_values_all_placeholder_or_default(self):
        """模板值只允许占位符（<YOUR_）或空值或显式默认（不含任何真实值）。"""
        allowed_defaults = {
            "ENVIRONMENT": "production",
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

    def test_idaas_origin_required_and_placeholder(self):
        """IDAAS_ORIGIN 升为必填：模板必须留 <YOUR_ 占位提醒用户填写。"""
        self.assertTrue(env_mod.ENV_SCHEMA["IDAAS_ORIGIN"][0])
        self.assertIn("<YOUR_", self.parsed["IDAAS_ORIGIN"])

    def test_derivable_and_credential_keys_left_empty_in_template(self):
        """可派生 / 可 discovery / 走凭据链的键在模板中应留空（而非占位符）：
        用户不填即可享受自动派生，不会被 <YOUR_ 占位误导为必填。"""
        for key in (
            "ALIYUN_ACCESS_KEY_ID",
            "ALIYUN_ACCESS_KEY_SECRET",
            "ALIYUN_SECURITY_TOKEN",
            "CONTROL_ENDPOINT",
            "DATA_ENDPOINT",
            "SIGNIN_BASE_URL",
            "POOL_JWKS_BASE",
            "ORDER_SERVICE_ISSUER",
            "ORDER_SERVICE_JWKS_URI",
        ):
            self.assertFalse(env_mod.ENV_SCHEMA[key][0], "{} 应为可选".format(key))
            self.assertEqual(
                self.parsed.get(key, ""),
                "",
                "{} 应在模板中留空（自动派生/凭据链兜底）".format(key),
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

    # ---- ENVIRONMENT 默认值与归一化写回 ----

    def test_environment_defaults_to_production(self):
        self.assertEqual(env_mod.derive_defaults({})["ENVIRONMENT"], "production")

    def test_environment_placeholder_defaults_to_production(self):
        env = env_mod.derive_defaults({"ENVIRONMENT": "<YOUR_ENVIRONMENT>"})
        self.assertEqual(env["ENVIRONMENT"], "production")

    def test_environment_explicit_value_preserved(self):
        env = env_mod.derive_defaults({"ENVIRONMENT": "pre-release"})
        self.assertEqual(env["ENVIRONMENT"], "pre-release")

    def test_environment_normalized_value_written_back(self):
        """归一化后的值必须写回 merged，下游一律用归一化值（不再拿到原字串）。"""
        env = env_mod.derive_defaults({"ENVIRONMENT": " Pre-Release "})
        self.assertEqual(env["ENVIRONMENT"], "pre-release")

    # ---- 正向派生：REGION → CONTROL/DATA_ENDPOINT ----

    def test_endpoints_derived_from_region_production(self):
        with contextlib.redirect_stderr(io.StringIO()):  # 吃掉 POOL_JWKS_BASE 镜像提示
            env = env_mod.derive_defaults({"REGION": "ap-southeast-1", "ENVIRONMENT": "production"})
        self.assertEqual(env["CONTROL_ENDPOINT"], "agentidentity.ap-southeast-1.aliyuncs.com")
        self.assertEqual(env["DATA_ENDPOINT"], "agentidentitydata.ap-southeast-1.aliyuncs.com")

    def test_endpoints_derived_from_region_pre_release(self):
        """endpoint 形态与环境无关（只随 REGION 变）；环境只影响 signin/pool_jwks。"""
        env = env_mod.derive_defaults({"REGION": "cn-hangzhou", "ENVIRONMENT": "pre-release"})
        self.assertEqual(env["CONTROL_ENDPOINT"], "agentidentity.cn-hangzhou.aliyuncs.com")
        self.assertEqual(env["DATA_ENDPOINT"], "agentidentitydata.cn-hangzhou.aliyuncs.com")

    def test_endpoint_placeholders_are_derived(self):
        env = env_mod.derive_defaults({
            "REGION": "cn-hangzhou",
            "CONTROL_ENDPOINT": "<agentidentity.YOUR_REGION.aliyuncs.com>",
            "DATA_ENDPOINT": "",
        })
        self.assertEqual(env["CONTROL_ENDPOINT"], "agentidentity.cn-hangzhou.aliyuncs.com")
        self.assertEqual(env["DATA_ENDPOINT"], "agentidentitydata.cn-hangzhou.aliyuncs.com")

    def test_explicit_endpoint_not_overwritten_by_region(self):
        """显式值永远优先：已填 CONTROL_ENDPOINT 不被 REGION 派生覆盖。"""
        env = env_mod.derive_defaults({
            "REGION": "cn-hangzhou",
            "CONTROL_ENDPOINT": "agentidentity.custom-vpc.aliyuncs.com",
        })
        self.assertEqual(env["CONTROL_ENDPOINT"], "agentidentity.custom-vpc.aliyuncs.com")
        # 未显式填的另一项仍按 REGION 派生
        self.assertEqual(env["DATA_ENDPOINT"], "agentidentitydata.cn-hangzhou.aliyuncs.com")

    def test_region_fallback_then_forward_derivation(self):
        """反向兜底 + 正向派生联动：只给 CONTROL_ENDPOINT → 推出 REGION → 再补 DATA_ENDPOINT。"""
        env = env_mod.derive_defaults({"CONTROL_ENDPOINT": "agentidentity.cn-beijing.aliyuncs.com"})
        self.assertEqual(env["REGION"], "cn-beijing")
        self.assertEqual(env["DATA_ENDPOINT"], "agentidentitydata.cn-beijing.aliyuncs.com")

    def test_no_region_no_endpoint_derivation(self):
        """REGION 不可得时不臆造 endpoint（留给 check_env 报 MISSING）。"""
        env = env_mod.derive_defaults({})
        self.assertTrue(env_mod.is_placeholder(env.get("CONTROL_ENDPOINT", "")))
        self.assertTrue(env_mod.is_placeholder(env.get("DATA_ENDPOINT", "")))
        self.assertTrue(env_mod.is_placeholder(env.get("SIGNIN_BASE_URL", "")))

    # ---- 正向派生：ENVIRONMENT + REGION → SIGNIN_BASE_URL / POOL_JWKS_BASE ----

    def test_signin_derived_production_shape(self):
        env = env_mod.derive_defaults({"REGION": "ap-southeast-1"})  # ENVIRONMENT 默认 production
        self.assertEqual(env["SIGNIN_BASE_URL"], "https://signin-ap-southeast-1.aliyunagentid.com")

    def test_signin_derived_pre_release_shape(self):
        env = env_mod.derive_defaults({"REGION": "cn-hangzhou", "ENVIRONMENT": "pre-release"})
        self.assertEqual(env["SIGNIN_BASE_URL"], "https://signin.cn-hangzhou.aliyuncs.com")

    def test_pool_jwks_base_mirrors_signin_in_production(self):
        """**显式声明** ENVIRONMENT=production（如新加坡正式环境）：池 discovery/JWKS 走登录域。"""
        with contextlib.redirect_stderr(io.StringIO()):
            env = env_mod.derive_defaults({"REGION": "ap-southeast-1", "ENVIRONMENT": "production"})
        self.assertEqual(env["POOL_JWKS_BASE"], env["SIGNIN_BASE_URL"])
        self.assertEqual(env["POOL_JWKS_BASE"], "https://signin-ap-southeast-1.aliyunagentid.com")

    def test_pool_jwks_base_stays_empty_when_environment_absent(self):
        """**向后兼容护栏（Critical-1）**：存量 .env 形态（无 ENVIRONMENT 键、
        SIGNIN_BASE_URL 显式、POOL_JWKS_BASE 留空）在用户零操作下：
        - ENVIRONMENT 默认化后仍为 production（SIGNIN 派生形态不变）；
        - POOL_JWKS_BASE 必须保持留空 → control_plane._pool_wellknown_host()
          继续走 DATA_ENDPOINT（改造前行为），而不是静默翻转成登录域。"""
        env = env_mod.derive_defaults({
            "REGION": "cn-hangzhou",
            "SIGNIN_BASE_URL": "https://signin.cn-hangzhou.aliyuncs.com",
            "POOL_JWKS_BASE": "",
        })
        self.assertEqual(env["ENVIRONMENT"], "production")
        self.assertEqual(env["SIGNIN_BASE_URL"], "https://signin.cn-hangzhou.aliyuncs.com")
        self.assertTrue(env_mod.is_placeholder(env.get("POOL_JWKS_BASE", "")))

    def test_pool_jwks_base_stays_empty_when_environment_absent_and_signin_derived(self):
        """同上，但 SIGNIN_BASE_URL 也未填（仍按 REGION 派生成 production 形态）。"""
        env = env_mod.derive_defaults({"REGION": "cn-hangzhou"})
        self.assertEqual(env["SIGNIN_BASE_URL"], "https://signin-cn-hangzhou.aliyunagentid.com")
        self.assertTrue(env_mod.is_placeholder(env.get("POOL_JWKS_BASE", "")))

    def test_pool_jwks_base_placeholder_environment_treated_as_absent(self):
        """ENVIRONMENT 为模板占位符 = 未声明 → 不镜像（与键缺失同语义）。"""
        env = env_mod.derive_defaults({
            "REGION": "cn-hangzhou",
            "ENVIRONMENT": "<YOUR_ENVIRONMENT>",
        })
        self.assertEqual(env["ENVIRONMENT"], "production")
        self.assertTrue(env_mod.is_placeholder(env.get("POOL_JWKS_BASE", "")))

    def test_pool_jwks_base_mirrors_explicit_signin_when_production_declared(self):
        """显式声明 production 时，镜像的是「生效的」SIGNIN_BASE_URL（包括用户实填值）。"""
        with contextlib.redirect_stderr(io.StringIO()):
            env = env_mod.derive_defaults({
                "REGION": "ap-southeast-1",
                "ENVIRONMENT": "PRODUCTION",  # 归一化后 production
                "SIGNIN_BASE_URL": "https://signin.custom.example.com",
            })
        self.assertEqual(env["SIGNIN_BASE_URL"], "https://signin.custom.example.com")
        self.assertEqual(env["POOL_JWKS_BASE"], "https://signin.custom.example.com")

    def test_mirror_emits_warning_on_stderr(self):
        """镜像真正发生时必须输出一行提示（否则派生对用户不可见）。"""
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            env_mod.derive_defaults({"REGION": "ap-southeast-1", "ENVIRONMENT": "production"})
        msg = buf.getvalue()
        self.assertIn("POOL_JWKS_BASE", msg)
        self.assertIn("https://signin-ap-southeast-1.aliyunagentid.com", msg)
        self.assertIn("DATA_ENDPOINT", msg)  # 告知旧行为回退路径
        self.assertIn("ENVIRONMENT", msg)

    def test_no_warning_when_mirror_not_triggered(self):
        """存量形态（未声明 ENVIRONMENT）不镜像 → 也不得喷提示日志。"""
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            env_mod.derive_defaults({"REGION": "cn-hangzhou"})
        self.assertEqual(buf.getvalue(), "")

    def test_no_warning_when_pool_jwks_base_explicit(self):
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            env_mod.derive_defaults({
                "REGION": "ap-southeast-1",
                "ENVIRONMENT": "production",
                "POOL_JWKS_BASE": "https://jwks.custom.example.com",
            })
        self.assertEqual(buf.getvalue(), "")

    def test_pool_jwks_base_left_empty_in_pre_release(self):
        """pre-release：POOL_JWKS_BASE 不设值（走 DATA_ENDPOINT 的预发行为）。"""
        env = env_mod.derive_defaults({"REGION": "cn-hangzhou", "ENVIRONMENT": "pre-release"})
        self.assertTrue(env_mod.is_placeholder(env.get("POOL_JWKS_BASE", "")))

    def test_explicit_signin_not_overwritten(self):
        env = env_mod.derive_defaults({
            "REGION": "ap-southeast-1",
            "SIGNIN_BASE_URL": "https://signin.custom.example.com",
        })
        self.assertEqual(env["SIGNIN_BASE_URL"], "https://signin.custom.example.com")
        # 未显式声明 ENVIRONMENT（存量形态）→ 不镜像 POOL_JWKS_BASE（继续走 DATA_ENDPOINT）
        self.assertTrue(env_mod.is_placeholder(env.get("POOL_JWKS_BASE", "")))

    def test_explicit_pool_jwks_base_not_overwritten(self):
        env = env_mod.derive_defaults({
            "REGION": "ap-southeast-1",
            "POOL_JWKS_BASE": "https://jwks.custom.example.com",
        })
        self.assertEqual(env["POOL_JWKS_BASE"], "https://jwks.custom.example.com")

    def test_signin_placeholder_is_derived(self):
        env = env_mod.derive_defaults({
            "REGION": "cn-hangzhou",
            "SIGNIN_BASE_URL": "<https://signin.YOUR_REGION.aliyuncs.com>",
        })
        self.assertEqual(env["SIGNIN_BASE_URL"], "https://signin-cn-hangzhou.aliyunagentid.com")

    # ---- 反向兜底：ORDER_SERVICE_ISSUER → IDAAS_ORIGIN ----

    def test_idaas_origin_reverse_fallback_from_issuer(self):
        env = env_mod.derive_defaults({
            "ORDER_SERVICE_ISSUER": "https://idaas-demo.example.com/api/v2/iauths_system/oauth2",
        })
        self.assertEqual(env["IDAAS_ORIGIN"], "https://idaas-demo.example.com")

    def test_idaas_origin_explicit_not_overwritten(self):
        env = env_mod.derive_defaults({
            "IDAAS_ORIGIN": "https://explicit.example.com",
            "ORDER_SERVICE_ISSUER": "https://other.example.com/oauth2",
        })
        self.assertEqual(env["IDAAS_ORIGIN"], "https://explicit.example.com")

    def test_idaas_origin_placeholder_gets_reverse_fallback(self):
        env = env_mod.derive_defaults({
            "IDAAS_ORIGIN": "<YOUR_IDAAS_ORIGIN>",
            "ORDER_SERVICE_ISSUER": "https://idaas-demo.example.com/oauth2",
        })
        self.assertEqual(env["IDAAS_ORIGIN"], "https://idaas-demo.example.com")

    def test_idaas_origin_stays_empty_without_issuer(self):
        """两者都空：不臆造 origin（留给 check_env 报 MISSING / apply_discovery 宽容跳过）。"""
        env = env_mod.derive_defaults({})
        self.assertTrue(env_mod.is_placeholder(env.get("IDAAS_ORIGIN", "")))

    def test_idaas_origin_placeholder_issuer_ignored(self):
        env = env_mod.derive_defaults({"ORDER_SERVICE_ISSUER": "<YOUR_ORDER_SERVICE_ISSUER>"})
        self.assertTrue(env_mod.is_placeholder(env.get("IDAAS_ORIGIN", "")))

    def test_malformed_issuer_does_not_break_derive(self):
        """畸形 issuer（urlsplit 抛 ValueError）不得让整个入口链路裸栈崩溃。"""
        env = env_mod.derive_defaults({"ORDER_SERVICE_ISSUER": "https://[::1/x"})
        self.assertTrue(env_mod.is_placeholder(env.get("IDAAS_ORIGIN", "")))

    # ---- 纯离线与无副作用 ----

    def test_derive_defaults_does_not_mutate_input(self):
        original = {"REGION": "ap-southeast-1"}
        snapshot = dict(original)
        env_mod.derive_defaults(original)
        self.assertEqual(original, snapshot)

    # ---- W2：幂等契约 f(f(x)) == f(x) ----

    def test_derive_defaults_is_idempotent(self):
        """W2：重复派生结果不变，POOL_JWKS_BASE 不翻转。

        四种入参形态：
        1. 无 ENVIRONMENT 键的存量形态
        2. 显式 production
        3. 显式 pre-release
        4. Pre-Release 带空格
        """
        cases = [
            ({"REGION": "cn-hangzhou"}, "无 ENVIRONMENT 键的存量形态"),
            ({"REGION": "cn-hangzhou", "ENVIRONMENT": "production"}, "显式 production"),
            ({"REGION": "cn-hangzhou", "ENVIRONMENT": "pre-release"}, "显式 pre-release"),
            ({"REGION": "cn-hangzhou", "ENVIRONMENT": " Pre-Release "}, "Pre-Release 带空格"),
        ]
        for raw, label in cases:
            with self.subTest(label=label):
                first = env_mod.derive_defaults(dict(raw))
                second = env_mod.derive_defaults(dict(first))
                # f(f(x)) == f(x)
                for key in first:
                    if key.startswith("_"):
                        continue  # 内部标记键不参与比对
                    self.assertEqual(
                        first.get(key), second.get(key),
                        "幂等破坏：{} 形态下 key={} 第一次={!r} 第二次={!r}".format(
                            label, key, first.get(key), second.get(key)
                        ),
                    )
                # POOL_JWKS_BASE 不翻转：存量形态（无显式 ENVIRONMENT）二次派生仍为空
                if "ENVIRONMENT" not in raw or env_mod.is_placeholder(raw.get("ENVIRONMENT", "")):
                    self.assertTrue(
                        env_mod.is_placeholder(second.get("POOL_JWKS_BASE", "")),
                        "幂等破坏：{} 形态下 POOL_JWKS_BASE 翻转为 {!r}".format(
                            label, second.get("POOL_JWKS_BASE")
                        ),
                    )

    def test_derive_defaults_does_not_read_env_file(self):
        """纯离线：仓库 .env 里明明有 REGION，但 ``derive_defaults({})`` 不得读到它
        （只允许字典运算，无文件 IO/网络）。"""
        env = env_mod.derive_defaults({})
        self.assertTrue(env_mod.is_placeholder(env.get("REGION", "")))
        self.assertTrue(env_mod.is_placeholder(env.get("CONTROL_ENDPOINT", "")))

    def test_derive_defaults_does_not_fill_issuer_or_jwks(self):
        """discovery 是网络副作用，绝不进 derive_defaults：issuer/jwks 保持空位，
        由 ``lib/discovery.py:apply_discovery`` 在 demo/serve-orders 入口懒触发回填。"""
        env = env_mod.derive_defaults({"REGION": "ap-southeast-1", "IDAAS_ORIGIN": "https://idaas-demo.example.com"})
        self.assertTrue(env_mod.is_placeholder(env.get("ORDER_SERVICE_ISSUER", "")))
        self.assertTrue(env_mod.is_placeholder(env.get("ORDER_SERVICE_JWKS_URI", "")))

    def test_minimal_three_key_config_derives_endpoints(self):
        """极简配置（客户手填 3 项 + 模板自带的 ENVIRONMENT=production）：
        其余端点全部自动派生，体检应直接通过。"""
        with contextlib.redirect_stderr(io.StringIO()):
            env = env_mod.derive_defaults({
                "REGION": "ap-southeast-1",
                "ENVIRONMENT": "production",  # env.template 直写的默认行
                "ORDER_SERVICE_AUDIENCE": "test-aud",
                "IDAAS_ORIGIN": "https://idaas-demo.example.com",
                # 以下为 setup 产出（模式 B 回写或模式 A 抄录）
                "USER_POOL_ID": "up_demo0001",
                "OAUTH_CLIENT_ID": "client_demo01",
                "OAUTH_CLIENT_SECRET": "sec-demo-01",
                "WI_NAME": "demo-wi",
                "OBO_PROVIDER_NAME": "demo-provider",
            })
        self.assertEqual(env["CONTROL_ENDPOINT"], "agentidentity.ap-southeast-1.aliyuncs.com")
        self.assertEqual(env["SIGNIN_BASE_URL"], "https://signin-ap-southeast-1.aliyunagentid.com")
        self.assertEqual(env["POOL_JWKS_BASE"], "https://signin-ap-southeast-1.aliyunagentid.com")
        ok, missing = env_mod.check_env(env)
        self.assertTrue(ok, "极简配置派生后应体检通过，但缺：{}".format(missing))

    def test_minimal_config_without_template_environment_line(self):
        """同上但用户删了 ENVIRONMENT 行（存量/极简形态）：仅 POOL_JWKS_BASE 不镜像，
        其余派生与体检结果不变（POOL_JWKS_BASE 本就是可选键）。"""
        env = env_mod.derive_defaults({
            "REGION": "ap-southeast-1",
            "ORDER_SERVICE_AUDIENCE": "test-aud",
            "IDAAS_ORIGIN": "https://idaas-demo.example.com",
            "USER_POOL_ID": "up_demo0001",
            "OAUTH_CLIENT_ID": "client_demo01",
            "OAUTH_CLIENT_SECRET": "sec-demo-01",
            "WI_NAME": "demo-wi",
            "OBO_PROVIDER_NAME": "demo-provider",
        })
        self.assertEqual(env["CONTROL_ENDPOINT"], "agentidentity.ap-southeast-1.aliyuncs.com")
        self.assertEqual(env["SIGNIN_BASE_URL"], "https://signin-ap-southeast-1.aliyunagentid.com")
        self.assertTrue(env_mod.is_placeholder(env.get("POOL_JWKS_BASE", "")))
        ok, missing = env_mod.check_env(env)
        self.assertTrue(ok, "应体检通过，但缺：{}".format(missing))


class TestEnvironmentValidation(unittest.TestCase):
    """ENVIRONMENT 归一化（strip+lower）与白名单校验（非法值报错，不静默降级）。"""

    def test_valid_environment_whitelist(self):
        self.assertEqual(env_mod._VALID_ENVIRONMENTS, ("production", "pre-release"))
        self.assertEqual(env_mod.DEFAULT_ENVIRONMENT, "production")

    def test_pre_release_spellings_all_normalized(self):
        """四种写法均得到 pre-release 形态：SIGNIN=登录域 aliyuncs.com、POOL_JWKS_BASE 留空。

        不归一化的后果：这些写法会静默走 else 分支派生出正式登录域
        （https://signin-<region>.aliyunagentid.com），PKCE 授权码与 client_secret
        被发往错误环境，报错却是 invalid_client / redirect_uri 不匹配。
        """
        for raw in ("pre-release", "Pre-Release", "PRE-RELEASE", " pre-release ", "\tpre-release\n"):
            env = env_mod.derive_defaults({"REGION": "cn-hangzhou", "ENVIRONMENT": raw})
            self.assertEqual(env["ENVIRONMENT"], "pre-release", "原值 {!r}".format(raw))
            self.assertEqual(
                env["SIGNIN_BASE_URL"], "https://signin.cn-hangzhou.aliyuncs.com", "原值 {!r}".format(raw)
            )
            self.assertTrue(
                env_mod.is_placeholder(env.get("POOL_JWKS_BASE", "")), "原值 {!r}".format(raw)
            )

    def test_production_spellings_all_normalized(self):
        for raw in ("production", "Production", "PRODUCTION", " production "):
            with contextlib.redirect_stderr(io.StringIO()):
                env = env_mod.derive_defaults({"REGION": "ap-southeast-1", "ENVIRONMENT": raw})
            self.assertEqual(env["ENVIRONMENT"], "production", "原值 {!r}".format(raw))
            self.assertEqual(
                env["SIGNIN_BASE_URL"],
                "https://signin-ap-southeast-1.aliyunagentid.com",
                "原值 {!r}".format(raw),
            )
            self.assertEqual(env["POOL_JWKS_BASE"], env["SIGNIN_BASE_URL"], "原值 {!r}".format(raw))

    def test_invalid_values_raise_env_error(self):
        for bad in ("staging", "pre_release", "prerelease", "prod", "production-", "PRE_RELEASE"):
            with self.assertRaises(env_mod.EnvError, msg="ENVIRONMENT={!r} 应报错".format(bad)) as ctx:
                env_mod.derive_defaults({"REGION": "cn-hangzhou", "ENVIRONMENT": bad})
            message = str(ctx.exception)
            self.assertIn(bad, message)          # 回显非法值原文
            self.assertIn("production", message)  # 合法取值列表
            self.assertIn("pre-release", message)
            self.assertIn(".env", message)        # 「修正 .env 后重跑」指引

    def test_invalid_value_error_before_any_derivation(self):
        """校验在派生之前：不得先抛一半派生结果再报错。"""
        with self.assertRaises(env_mod.EnvError):
            env_mod.derive_defaults({"REGION": "cn-hangzhou", "ENVIRONMENT": "staging"})

    def test_env_error_inherits_rpc_error_for_cli_whitelist(self):
        """EnvError 必须继承 sample.py 已捕获的类型（RpcError），否则用户看到裸栈。

        只继承、不修改 sample.py：其 ``main()`` 的 except 白名单已含 ``RpcError``。
        """
        self.assertTrue(issubclass(env_mod.EnvError, RpcError))
        err = env_mod.EnvError("配置错了")
        self.assertIsInstance(err, RpcError)
        self.assertIsInstance(err, Exception)
        # 重写 __str__：只回显 message，不带 RpcError 的「HTTP 0」误导前缀
        self.assertEqual(str(err), "配置错了")
        self.assertEqual(err.code, "InvalidConfiguration")
        self.assertFalse(err.retryable)

    def test_empty_or_placeholder_environment_not_an_error(self):
        """缺失/空/纯空白/模板占位 → 默认 production（不报错），但不算「显式声明」。"""
        for raw in ("", "   ", "<YOUR_ENVIRONMENT>"):
            env = env_mod.derive_defaults({"REGION": "cn-hangzhou", "ENVIRONMENT": raw})
            self.assertEqual(env["ENVIRONMENT"], "production", "原值 {!r}".format(raw))
            self.assertTrue(env_mod.is_placeholder(env.get("POOL_JWKS_BASE", "")))

    def test_none_environment_value_tolerated(self):
        """值为 None（如脚本拼装配置时漏值）不得 AttributeError。"""
        env = env_mod.derive_defaults({"REGION": "cn-hangzhou", "ENVIRONMENT": None})
        self.assertEqual(env["ENVIRONMENT"], "production")
        self.assertEqual(env["SIGNIN_BASE_URL"], "https://signin-cn-hangzhou.aliyunagentid.com")


class TestExtractOrigin(unittest.TestCase):
    """``_extract_origin``：IDAAS_ORIGIN 反向兜底的 URL 解析辅助函数。"""

    def test_https_url_with_path(self):
        self.assertEqual(
            env_mod._extract_origin("https://idaas-demo.example.com/api/v2/oauth2"),
            "https://idaas-demo.example.com",
        )

    def test_keeps_port(self):
        self.assertEqual(
            env_mod._extract_origin("https://idaas-demo.example.com:8443/oauth2"),
            "https://idaas-demo.example.com:8443",
        )

    def test_strips_query_and_fragment(self):
        self.assertEqual(
            env_mod._extract_origin("https://idaas-demo.example.com/oauth2?a=1#frag"),
            "https://idaas-demo.example.com",
        )

    def test_trailing_whitespace_tolerated(self):
        self.assertEqual(
            env_mod._extract_origin("  https://idaas-demo.example.com/x  "),
            "https://idaas-demo.example.com",
        )

    def test_no_scheme_returns_empty(self):
        self.assertEqual(env_mod._extract_origin("idaas-demo.example.com/oauth2"), "")

    def test_urn_style_issuer_returns_empty(self):
        """非 http(s) 形态 issuer（如 urn:）无 netloc → 空串（不回填）。"""
        self.assertEqual(env_mod._extract_origin("urn:example:issuer"), "")

    def test_empty_and_placeholder_return_empty(self):
        self.assertEqual(env_mod._extract_origin(""), "")
        self.assertEqual(env_mod._extract_origin("<YOUR_ORDER_SERVICE_ISSUER>"), "")

    def test_malformed_ipv6_url_returns_empty_not_raise(self):
        """``urlsplit`` 对残缺的 IPv6 方括号抛 ``ValueError``（Python 3.9-3.12），
        必须吞掉并返回空串（docstring 承诺「解析失败返回空串」）。

        不捕获的后果：``derive_defaults`` 是 --check/login/exchange-wat/obo/demo/
        setup/cleanup/serve-orders **每个入口的第一道调用**，用户写错的 issuer
        会让所有子命令裸栈崩溃。"""
        self.assertEqual(env_mod._extract_origin("https://[::1/x"), "")
        self.assertEqual(env_mod._extract_origin("http://["), "")
        self.assertEqual(env_mod._extract_origin("  https://[::1/x  "), "")

    def test_valid_ipv6_url_still_parsed(self):
        """合法的 IPv6 主机名不能被 except ValueError 误伤。"""
        self.assertEqual(
            env_mod._extract_origin("https://[::1]:8443/oauth2"),
            "https://[::1]:8443",
        )


if __name__ == "__main__":
    unittest.main()
