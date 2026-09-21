"""D6：sample.py --check 的「纯离线体检」默认口径 与 --creds-live 真实解析口径。

背景（评审 Major）：旧 cmd_check 直接调 credentials.resolve_creds(config)，当 .env
未显式填 AK/SK（本次推荐的默认姿势）时会落到 SDK 级 get_credential()——可能触发
OAuth 续期 / AssumeRole / ECS 元数据探测等**网络副作用**，并可能回写全局
~/.aliyun/config.json。而 docs 把 --check 定为「通用排查第一步」，离线/内网 CI 中
会挂起并污染共享文件。修复后：默认离线只报告各级「能力」，--creds-live 才真实解析。

全程离线：patch credentials 的**公开离线探测 API**（``probe_explicit`` /
``probe_sdk_installed`` / ``probe_stdlib``）与 env/tokens 的读写，绝不调用
resolve_creds / resolve_creds_detailed / _creds_from_sdk / get_credential()、绝不联网、
绝不读真实 ~/.aliyun/config.json。

解耦护栏（修复 F）：sample.py 只准调 credentials 的**公开** API，不得引用其私有符号
（_creds_from_explicit / _creds_from_aliyun_config / _LAST_STDLIB_SOURCE /
CredentialClient 等）—— 见 ``TestNoPrivateCredentialsCoupling``，用 ``ast`` 静态扫描
源码（不用易碎的正则）。

安全红线：所有 AK 均为假数据；断言校验 stdout 只出现掩码（≤4 字符 + len=），
绝不出现完整或前 8 位 AK。
"""

import argparse
import ast
import inspect
import io
import json
import os
import socket
import sys
import tempfile
import unittest
import urllib.request
from contextlib import redirect_stdout
from unittest import mock

SAMPLE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SAMPLE_DIR not in sys.path:
    sys.path.insert(0, SAMPLE_DIR)

import sample  # noqa: E402
from lib import credentials  # noqa: E402

# 合成假 AK（G2，非真实凭据）：保留可识别的阿里云 ``LTAI`` 形态前缀以便掩码断言
# 有意义（sample._mask_ak 取 ak[:4] → "LTAI"），后半段一律用重复的 ``FAKE`` 块。
# 选此形态的理由：① 20 字符、``len=20`` 与掩码输出 ``LTAI…(len=20)`` 断言保持成立；
# ② ``FAKE_AK[:8]`` = "LTAIFAKE" 不会出现在掩码输出里，支撑「前 8 位不泄露」断言；
# ③ 全大写重复块使 Shannon 熵≈ 2.5（< 3.0），低于 gitleaks/trufflehog 的阿里云 AK
# 熵阈，不会被误判为真实凭据泄露（扫描器豁免审查可据此认定）。
FAKE_AK = "LTAIFAKEFAKEFAKEFAKE"
FAKE_SK = "sk-fake-unit-test"
FAKE_CONFIG = {"ALIYUN_ACCESS_KEY_ID": FAKE_AK, "ALIYUN_ACCESS_KEY_SECRET": FAKE_SK}

# probe_* 公开 API 返回的 level/source 取值（与 resolve_creds_detailed 同级一致）
EXPLICIT_SOURCE = ".env 显式 ALIYUN_ACCESS_KEY_*"
STDLIB_SOURCE = "~/.aliyun/config.json(profile=default, mode=StsToken)"


def _resolved(level, source, ak=FAKE_AK, sk=FAKE_SK, token=None):
    """构造 ``ResolvedCreds``（``probe_explicit`` / ``probe_stdlib`` 的返回形态）。"""
    return credentials.ResolvedCreds(ak, sk, token, level, source)


class CountingCredentialClient:
    """假 SDK 客户端类：一旦被**构造**即计数（离线口径下计数必须恒为 0）。

    构造真实 ``CredentialClient()`` 会 eager 建整条 provider 链并可能探 ECS 元数据，
    因此本文件绝不引入真 SDK 类。
    """

    constructs = 0

    def __init__(self):
        type(self).constructs += 1

    def get_credential(self):
        raise AssertionError("离线口径绝不得调用 get_credential()")


def _args(creds_live=False):
    return argparse.Namespace(check=True, creds_live=creds_live)


class CmdCheckBase(unittest.TestCase):
    """隔离 cmd_check 的 env/report/tokens 段，只聚焦凭据链段的行为。"""

    def setUp(self):
        patchers = [
            mock.patch.object(sample.env_mod, "load_env", return_value=dict(FAKE_CONFIG)),
            mock.patch.object(sample.env_mod, "derive_defaults", side_effect=lambda c: dict(c)),
            mock.patch.object(sample.env_mod, "render_check_report", return_value="[env report]"),
            mock.patch.object(sample.env_mod, "check_env", return_value=(True, [])),
            mock.patch.object(sample.tokens_mod, "tokens_status", return_value={}),
        ]
        for patcher in patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def _run(self, args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            sample.cmd_check(args)
        return buf.getvalue()

    def _run_rc(self, args):
        """返回 (退出码, stdout)：供 O1 退出码语义用例使用（_run 只看正文）。"""
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = sample.cmd_check(args)
        return rc, buf.getvalue()


class TestCheckOffline(CmdCheckBase):
    """默认 --check：纯离线，绝不触发真实凭据解析 / 网络 / 写盘。

    patch 点一律为 credentials 的**公开离线探测 API**（``probe_explicit`` /
    ``probe_sdk_installed`` / ``probe_stdlib``）—— sample.py 已不再引用任何私有符号。
    """

    def test_explicit_hit_masks_ak(self):
        with mock.patch.object(credentials, "probe_explicit",
                               return_value=_resolved(
                                   credentials.LEVEL_EXPLICIT, EXPLICIT_SOURCE)), \
                mock.patch.object(credentials, "probe_sdk_installed", return_value=True), \
                mock.patch.object(credentials, "probe_stdlib",
                                  side_effect=credentials.CredentialError("no config")):
            out = self._run(_args(creds_live=False))
        self.assertIn("离线体检", out)
        self.assertIn("[1] .env 显式", out)
        # 掩码收窄：只出现前 4 字符 + len=，绝不出现完整或前 8 位 AK
        self.assertIn("LTAI…(len=20)", out)
        self.assertNotIn(FAKE_AK, out)
        self.assertNotIn(FAKE_AK[:8], out)

    def test_offline_never_calls_live_resolution(self):
        """D6 核心保证：离线口径绝不调用 resolve_creds / resolve_creds_detailed / SDK。"""
        with mock.patch.object(credentials, "probe_explicit", return_value=None), \
                mock.patch.object(credentials, "probe_sdk_installed", return_value=False), \
                mock.patch.object(credentials, "probe_stdlib",
                                  side_effect=credentials.CredentialError("no config")), \
                mock.patch.object(credentials, "resolve_creds") as m_rc, \
                mock.patch.object(credentials, "resolve_creds_detailed") as m_rcd, \
                mock.patch.object(credentials, "_creds_from_sdk") as m_sdk, \
                mock.patch.object(credentials, "_get_sdk_client") as m_client:
            self._run(_args(creds_live=False))
        m_rc.assert_not_called()
        m_rcd.assert_not_called()
        m_sdk.assert_not_called()
        m_client.assert_not_called()  # 离线口径连 SDK 客户端都不该构造

    def test_sdk_not_installed_reported(self):
        with mock.patch.object(credentials, "probe_explicit", return_value=None), \
                mock.patch.object(credentials, "probe_sdk_installed", return_value=False), \
                mock.patch.object(credentials, "probe_stdlib",
                                  side_effect=credentials.CredentialError("no config")):
            out = self._run(_args(creds_live=False))
        self.assertIn("[2] alibabacloud_credentials SDK：未安装", out)

    def test_sdk_installed_reported_without_calling(self):
        with mock.patch.object(credentials, "probe_explicit", return_value=None), \
                mock.patch.object(credentials, "probe_sdk_installed",
                                  return_value=True) as m_probe, \
                mock.patch.object(credentials, "probe_stdlib",
                                  side_effect=credentials.CredentialError("no config")):
            out = self._run(_args(creds_live=False))
        self.assertIn("[2] alibabacloud_credentials SDK：已安装", out)
        self.assertIn("不调用 get_credential()", out)
        # 安装态只能通过公开探测 API 拿（不得直接读 credentials.CredentialClient）
        m_probe.assert_called_once_with()

    def test_stdlib_level_readable(self):
        with mock.patch.object(credentials, "probe_explicit", return_value=None), \
                mock.patch.object(credentials, "probe_sdk_installed", return_value=False), \
                mock.patch.object(credentials, "probe_stdlib",
                                  return_value=_resolved(
                                      credentials.LEVEL_STDLIB, STDLIB_SOURCE,
                                      token="sts-fake")):
            out = self._run(_args(creds_live=False))
        self.assertIn("[3] 标准库 ~/.aliyun/config.json（只读）：可解析", out)
        self.assertIn("profile=default", out)
        self.assertNotIn(FAKE_AK, out)  # 掩码

    def test_half_fill_prints_full_guidance(self):
        """半填时透传 credentials 的多行指引（不止首行）。"""
        err = credentials.CredentialError(
            ".env 显式凭据半填：ALIYUN_ACCESS_KEY_ID 已填写。\n"
            "下一步（二选一）：\n"
            "  A) 补齐 ALIYUN_ACCESS_KEY_SECRET；\n"
            "  B) 或两项都清空以走 CLI 凭据链。"
        )
        with mock.patch.object(credentials, "probe_explicit", side_effect=err), \
                mock.patch.object(credentials, "probe_sdk_installed", return_value=False), \
                mock.patch.object(credentials, "probe_stdlib",
                                  side_effect=credentials.CredentialError("no config")):
            out = self._run(_args(creds_live=False))
        self.assertIn("半填", out)
        # 完整多行指引透传：末行的 A)/B) 修复路径必须出现
        self.assertIn("A) 补齐 ALIYUN_ACCESS_KEY_SECRET", out)
        self.assertIn("B) 或两项都清空", out)

    def test_offline_end_to_end_sandboxed_no_network_no_write(self):
        """不 patch probe_*：走**真实**公开 API，端到端验证离线口径无网络 / 无写盘。

        沙箱：CLI 配置指向临时假文件、HOME 指向临时目录、SDK 客户端类用计数替身
        （构造即计数）、socket/DNS/urlopen 全部打桩。绝不读真实 ~/.aliyun/config.json，
        绝不打印真实凭据（AK 全为假数据且 sample 侧本身掩码）。
        """
        tmp = tempfile.TemporaryDirectory(prefix="sample-check-offline-")
        self.addCleanup(tmp.cleanup)
        cfg_path = os.path.join(tmp.name, "config.json")
        profile = {
            "name": "default", "mode": "StsToken", "access_key_id": "STS.fake0001",
            "access_key_secret": FAKE_SK, "sts_token": "sts-fake",
            "sts_expiration": "2099-01-01T00:00:00Z",
        }
        with open(cfg_path, "w", encoding="utf-8") as fh:
            json.dump({"current": "default", "profiles": [profile]}, fh)
        with open(cfg_path, "rb") as fh:
            before_bytes = fh.read()
        before_listing = sorted(os.listdir(tmp.name))
        CountingCredentialClient.constructs = 0
        with mock.patch.dict(os.environ, {
                "ALIBABA_CLOUD_CLI_CONFIG_FILE": cfg_path, "HOME": tmp.name}), \
                mock.patch.object(credentials, "CredentialClient",
                                  CountingCredentialClient), \
                mock.patch.object(socket, "socket") as m_sock, \
                mock.patch.object(socket, "create_connection") as m_conn, \
                mock.patch.object(socket, "getaddrinfo") as m_dns, \
                mock.patch.object(urllib.request, "urlopen") as m_url:
            out = self._run(_args(creds_live=False))
        # 三级能力均如实报告（走的是真实 probe_* 实现）
        self.assertIn("[1] .env 显式 ALIYUN_ACCESS_KEY_*：命中", out)
        self.assertIn("[2] alibabacloud_credentials SDK：已安装", out)
        self.assertIn("[3] 标准库 ~/.aliyun/config.json（只读）：可解析", out)
        self.assertIn("profile=default, mode=StsToken", out)
        self.assertIn("STS.…(len=12)", out)  # 掩码
        self.assertNotIn("STS.fake0001", out)
        # 无副作用：未构造 SDK 客户端、未发网络、未写盘
        self.assertEqual(CountingCredentialClient.constructs, 0)
        m_sock.assert_not_called()
        m_conn.assert_not_called()
        m_dns.assert_not_called()
        m_url.assert_not_called()
        with open(cfg_path, "rb") as fh:
            self.assertEqual(fh.read(), before_bytes)
        self.assertEqual(sorted(os.listdir(tmp.name)), before_listing)


class TestCheckLive(CmdCheckBase):
    """--creds-live：真实 resolve_creds_detailed()，精确报告命中级别 + 来源。"""

    def _resolved(self, level, source, ak=FAKE_AK, token=None):
        return credentials.ResolvedCreds(ak, FAKE_SK, token, level, source)

    def test_live_explicit_level_label(self):
        with mock.patch.object(
            credentials, "resolve_creds_detailed",
            return_value=self._resolved(
                credentials.LEVEL_EXPLICIT, ".env 显式 ALIYUN_ACCESS_KEY_*"),
        ):
            out = self._run(_args(creds_live=True))
        self.assertIn("--creds-live", out)
        self.assertIn(".env 显式 AK/SK（最高优先）", out)
        self.assertIn("LTAI…(len=20)", out)
        self.assertNotIn(FAKE_AK, out)
        self.assertNotIn(FAKE_AK[:8], out)

    def test_live_sdk_level_label(self):
        with mock.patch.object(
            credentials, "resolve_creds_detailed",
            return_value=self._resolved(
                credentials.LEVEL_SDK, "CLIProfileCredentialsProvider", ak="STS.fake", token="t"),
        ):
            out = self._run(_args(creds_live=True))
        self.assertIn("SDK 凭据链（provider=CLIProfileCredentialsProvider）", out)
        self.assertIn("含 STS=是", out)
        self.assertIn("STS.…", out)  # 掩码前 4 字符

    def test_live_stdlib_level_label(self):
        with mock.patch.object(
            credentials, "resolve_creds_detailed",
            return_value=self._resolved(
                credentials.LEVEL_STDLIB, "~/.aliyun/config.json(profile=default, mode=AK)"),
        ):
            out = self._run(_args(creds_live=True))
        self.assertIn("标准库降级读 ~/.aliyun/config.json", out)

    def test_live_failure_prints_full_guidance(self):
        err = credentials.CredentialError(
            "凭据链三级降级全部失败。\n"
            "下一步（任选其一即可）：\n"
            "  A) pip install alibabacloud-credentials；\n"
            "  B) aliyun configure --mode AK；\n"
            "  C) .env 显式填 AK/SK。"
        )
        with mock.patch.object(credentials, "resolve_creds_detailed", side_effect=err):
            out = self._run(_args(creds_live=True))
        self.assertIn("[未配置]", out)
        # 完整多行指引逐行透传（旧实现只取首行、丢弃 A/B/C）
        self.assertIn("A) pip install alibabacloud-credentials", out)
        self.assertIn("B) aliyun configure --mode AK", out)
        self.assertIn("C) .env 显式填 AK/SK", out)


class TestCheckExitCode(CmdCheckBase):
    """O1：``--check`` 退出码并入「确定性配置错误」（半填 / 标准库 STS 过期）。

    ``CmdCheckBase.setUp`` 已把 ``check_env`` 打桩为 ``(True, [])``，故退出码只取
    决于离线凭据链体检的 hard_failure。全程离线（只 patch 公开 ``probe_*`` API）。
    C1 契约：错误分类改按 ``CredentialError.reason`` 结构化字段判定（不再用跨模块
    中文文案子串匹配），且 Level 1 命中时 Level 3 不可达、其陈旧状态不计入退出码。
    """

    def test_half_fill_returns_nonzero(self):
        """显式 AK/SK 半填 → 确定性配置错误 → 退出码非 0。"""
        err = credentials.CredentialError(".env 显式凭据半填：ALIYUN_ACCESS_KEY_ID 已填写。")
        with mock.patch.object(credentials, "probe_explicit", side_effect=err), \
                mock.patch.object(credentials, "probe_sdk_installed", return_value=False), \
                mock.patch.object(credentials, "probe_stdlib",
                                  side_effect=credentials.CredentialError("未找到 aliyun CLI 配置文件")):
            rc, out = self._run_rc(_args(creds_live=False))
        self.assertEqual(1, rc)
        self.assertIn("半填", out)  # 报告正文仍逐字体现

    def test_both_empty_returns_zero(self):
        """两级都留空（推荐的走凭据链姿势）→ 退出码 0，绝不能变红。"""
        with mock.patch.object(credentials, "probe_explicit", return_value=None), \
                mock.patch.object(credentials, "probe_sdk_installed", return_value=False), \
                mock.patch.object(credentials, "probe_stdlib",
                                  side_effect=credentials.CredentialError("未找到 aliyun CLI 配置文件")):
            rc, _out = self._run_rc(_args(creds_live=False))
        self.assertEqual(0, rc)

    def test_both_filled_returns_zero(self):
        """显式命中 + 标准库可解析（两项都填）→ 退出码 0。"""
        with mock.patch.object(credentials, "probe_explicit",
                               return_value=_resolved(credentials.LEVEL_EXPLICIT, EXPLICIT_SOURCE)), \
                mock.patch.object(credentials, "probe_sdk_installed", return_value=True), \
                mock.patch.object(credentials, "probe_stdlib",
                                  return_value=_resolved(credentials.LEVEL_STDLIB, STDLIB_SOURCE)):
            rc, _out = self._run_rc(_args(creds_live=False))
        self.assertEqual(0, rc)

    def test_stdlib_sts_expired_returns_nonzero(self):
        """标准库 profile 的 STS 凭据已过期 → 确定性配置错误 → 退出码非 0。"""
        expired = credentials.CredentialError(
            "~/.aliyun/config.json 中 profile mode=StsToken 的 STS 凭据已过期"
            "（sts_expiration=2020-01-01T00:00:00Z）。标准库降级路径不做 refresh。",
            reason=credentials.REASON_STS_EXPIRED)
        with mock.patch.object(credentials, "probe_explicit", return_value=None), \
                mock.patch.object(credentials, "probe_sdk_installed", return_value=False), \
                mock.patch.object(credentials, "probe_stdlib", side_effect=expired):
            rc, out = self._run_rc(_args(creds_live=False))
        self.assertEqual(1, rc)
        self.assertIn("不可用", out)

    def test_sdk_installed_only_returns_zero(self):
        """SDK 已装但两级留空（离线口径不调用）→ 安装态不影响退出码 → 0。"""
        with mock.patch.object(credentials, "probe_explicit", return_value=None), \
                mock.patch.object(credentials, "probe_sdk_installed", return_value=True), \
                mock.patch.object(credentials, "probe_stdlib",
                                  side_effect=credentials.CredentialError("未找到 aliyun CLI 配置文件")):
            rc, out = self._run_rc(_args(creds_live=False))
        self.assertEqual(0, rc)
        self.assertIn("已安装", out)

    def test_explicit_hit_with_stale_expired_profile_returns_zero(self):
        """C1：Level 1 命中时 Level 3 不可达，其陈旧 STS 过期不计入退出码。"""
        stale_expired = credentials.CredentialError(
            "~/.aliyun/config.json 中 profile mode=StsToken 的 STS 凭据已过期",
            reason=credentials.REASON_STS_EXPIRED,
        )
        with mock.patch.object(credentials, "probe_explicit",
                               return_value=_resolved(
                                   credentials.LEVEL_EXPLICIT, EXPLICIT_SOURCE)), \
                mock.patch.object(credentials, "probe_sdk_installed", return_value=True), \
                mock.patch.object(credentials, "probe_stdlib", side_effect=stale_expired):
            rc, out = self._run_rc(_args(creds_live=False))
        # Level 1 命中，三级链短路语义：Level 3 不可达，不计入退出码
        self.assertEqual(0, rc)
        self.assertIn("Level 1 已命中", out)
        self.assertIn("不计入退出码", out)

    def test_creds_live_half_fill_returns_nonzero(self):
        """W5：半填缺陷在 --creds-live 模式下仍必须计入退出码（与离线一致）。"""
        err = credentials.CredentialError(
            ".env 显式凭据半填：ALIYUN_ACCESS_KEY_ID 已填写。",
            reason=credentials.REASON_HALF_FILLED,
        )
        with mock.patch.object(credentials, "resolve_creds_detailed", side_effect=err):
            rc, out = self._run_rc(_args(creds_live=True))
        self.assertEqual(1, rc)
        self.assertIn("半填", out)


class TestArgparseDescription(unittest.TestCase):
    """O6：--help 首屏 description 与模块 docstring 口径一致（标准库可独立运行 + SDK 为可选增强）。

    D-Major1：setup 子命令 help 不得含「需 AK」（与凭据链改造矛盾，是用户第一入口）。
    """

    def test_description_states_stdlib_and_optional_sdk(self):
        desc = sample.build_parser().description or ""
        # 简洁一行说清：纯标准库可独立运行 + SDK 为可选增强
        self.assertIn("标准库", desc)
        self.assertIn("独立运行", desc)
        self.assertIn("SDK", desc)
        self.assertIn("可选增强", desc)
        # 不再用与 docstring 有张力的短式「（纯标准库）」
        self.assertNotIn("（纯标准库）", desc)

    def test_help_output_contains_description(self):
        help_text = sample.build_parser().format_help()
        self.assertIn("标准库", help_text)
        self.assertIn("可选增强", help_text)

    def test_setup_subparser_help_no_ak_requirement(self):
        """D-Major1：setup --mode 的 help 不得含「需 AK」（凭据链改造后不需显式 AK）。"""
        parser = sample.build_parser()
        # 遍历 subparser 找到 setup
        setup_action = None
        for action in parser._subparsers._actions:
            if hasattr(action, "choices") and "setup" in (action.choices or {}):
                setup_action = action
                break
        self.assertIsNotNone(setup_action, "setup 子命令未找到")
        setup_parser = setup_action.choices["setup"]
        setup_help = setup_parser.format_help()
        self.assertNotIn("需 AK", setup_help)
        self.assertNotIn("需AK", setup_help)
        # 正向断言：包含凭据链相关表述
        self.assertIn("凭据链", setup_help)


class TestNoChineseSubstringErrorClassification(unittest.TestCase):
    """C1 护栏：_check_creds_offline 源码不得用中文字面量对 str(exc) 做 ``in`` 比较。

    跨模块中文文案子串匹配是 fail-open 缺陷（文案一改判定就静默失效），
    改用 CredentialError.reason 结构化字段。本测试用 ast 扫描源码确保不回退。
    """

    def test_no_chinese_substring_error_classification(self):
        """ast 扫描 _check_creds_offline：不存在对 str(exc) 的中文字面量 in 比较。"""
        source = inspect.getsource(sample._check_creds_offline)
        tree = ast.parse(source)
        # 收集所有 Compare 节点里的 Str/Constant 字面量（包含中文的）
        chinese_literals_in_compare = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            # 检查 comparators 和 left 是否含中文字符串字面量
            operands = [node.left] + list(node.comparators)
            for operand in operands:
                if isinstance(operand, ast.Constant) and isinstance(operand.value, str):
                    if any('\u4e00' <= ch <= '\u9fff' for ch in operand.value):
                        chinese_literals_in_compare.append(operand.value)
        self.assertEqual(
            [], chinese_literals_in_compare,
            "_check_creds_offline 不得用中文字面量做错误分类（改用 exc.reason）："
            "{}".format(chinese_literals_in_compare),
        )


class TestNoPrivateCredentialsCoupling(unittest.TestCase):
    """解耦护栏（修复 F）：sample.py 不得引用 credentials 的私有符号。

    这是交付给客户的**教学样例**：耦合被调模块的私有实现细节属于质量缺陷 ——
    私有符号重构会静默打断 sample.py，读者还会误以为那些是推荐用法。

    用 ``ast`` 静态扫描（而非易碎的正则）：既查属性访问，也查源码文本
    （后者额外覆盖注释 / docstring 里对私有符号的命名引用）。
    """

    #: 已从 sample.py 解耦掉的 credentials 私有/实现细节符号名。
    BANNED_NAMES = (
        "_creds_from_explicit",
        "_creds_from_sdk",
        "_creds_from_aliyun_config",
        "_get_sdk_client",
        "_resolve_chain",
        "_LAST_STDLIB_SOURCE",
        "_LAST_SDK_SOURCE",
        "_LAST_SDK_FAILURE",
        "CredentialClient",
    )

    #: 离线体检必须走的公开探测 API（防止上面两条断言靠「删代码」空过）。
    REQUIRED_PUBLIC = ("probe_explicit", "probe_sdk_installed", "probe_stdlib")

    @staticmethod
    def _credentials_attrs(source):
        """收集源码里所有 ``credentials.<attr>`` 的属性名（ast，不依赖文本形式）。"""
        return {
            node.attr
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "credentials"
        }

    def test_no_private_attribute_access_on_credentials(self):
        """sample.py 里所有 ``credentials.X`` 的 X 都必须是公开名字（无 ``_`` 前缀）。"""
        private = sorted(
            attr for attr in self._credentials_attrs(inspect.getsource(sample))
            if attr.startswith("_")
        )
        self.assertEqual(
            [], private,
            "sample.py 不得访问 credentials 的私有属性：{}".format(private),
        )

    def test_banned_private_names_absent_from_source_text(self):
        """源码文本（含注释 / docstring）不得再出现已解耦的私有符号名。"""
        source = inspect.getsource(sample)
        hits = sorted(name for name in self.BANNED_NAMES if name in source)
        self.assertEqual(
            [], hits,
            "sample.py 仍引用 credentials 私有/实现细节符号：{}（请改用 probe_* 公开 API）".format(hits),
        )

    def test_offline_check_calls_public_probe_trio(self):
        """正向锁定：``_check_creds_offline`` 必须调齐 probe_* 三件套。"""
        attrs = self._credentials_attrs(inspect.getsource(sample._check_creds_offline))
        for name in self.REQUIRED_PUBLIC:
            self.assertIn(
                name, attrs,
                "_check_creds_offline 未调用公开探测 API {}（实际调用：{}）".format(
                    name, sorted(attrs)),
            )

    def test_credentials_exposes_probe_trio_as_public(self):
        """探测 API 必须是 credentials 的公开可调用对象（不是测试里凭空 patch 的名字）。"""
        for name in self.REQUIRED_PUBLIC:
            self.assertTrue(
                callable(getattr(credentials, name, None)),
                "credentials.{} 缺失或不可调用".format(name),
            )


if __name__ == "__main__":
    unittest.main()
