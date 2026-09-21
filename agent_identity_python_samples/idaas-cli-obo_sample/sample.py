#!/usr/bin/env python3
"""idaas-cli-obo sample：Agent Identity × IDaaS 入站登录 + OBO 出站 全链路演示 CLI。

叙事主线（一个命令一个步骤，全部可独立重跑）：
  管控面（一次性）  setup --mode=console | setup --mode=script
  数据面第 1 步     login          浏览器联邦登录 → loopback 回调 → 池 ID Token
  数据面第 2 步     exchange-wat   池 ID Token → WAT（身份从「人」升维为「工作负载」）
  数据面第 3 步     obo            WAT → 订单服务 AT/RT（on-behalf-of 出站）
  数据面第 4 步     serve-orders   本地模拟订单企业服务（验签 + 差异化数据）
  一键串联          demo
  清理              cleanup

纯 Python 标准库（3.9+）即可独立运行；可选 alibabacloud-credentials（3.10+）启用 CLI 凭据链自动刷新。
"""

import argparse
import json
import sys
import threading
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple

from lib import control_plane
from lib import credentials
from lib import discovery
from lib import env as env_mod
from lib import flow
from lib import tokens as tokens_mod
from lib.rpc import RpcError
from orders.server import make_server
from orders.verify import TokenVerifier

# 兼容保留：install_atexit_guard() 现为 no-op 兜底（atexit 时机对已启动线程改不动
# daemon 属性、且 CPython 先 join 非 daemon 线程再跑 atexit，语义上不可能生效）。
# 真正生效的 SDK 线程防护在 credentials 模块内部：构造 SDK 客户端前后同步快照
# threading.enumerate() 差集并标 daemon=True（详见该模块 docstring）。此处调用仅为兼容旧行为。
credentials.install_atexit_guard()

PROG = "sample.py"


# ---------------------------------------------------------------------------
# 子命令实现
# ---------------------------------------------------------------------------


def _mask_ak(ak: str) -> str:
    """AK 掩码回显：最多前 4 字符（``LTAI``/``STS.`` 形态前缀）+ 长度。

    安全红线（D6）：绝不打印 8 位或完整 AK——--check 输出会进 CI 日志、
    常被整段贴进 issue。与 ``env.render_check_report`` / ``control_plane._mask_ak``
    掩码策略保持一致（旧实现打 ``creds[0][:8]`` 与之自相矛盾，已收窄）。
    """
    if not ak:
        return "<空>"
    return "{}…(len={})".format(ak[:4], len(ak))


def _level_label(level: str, source: str) -> str:
    """命中级别 → 人读标签（D6：改用 ``resolved.level``/``source``，不再靠 ``STS.`` 前缀猜）。"""
    if level == credentials.LEVEL_EXPLICIT:
        return ".env 显式 AK/SK（最高优先）"
    if level == credentials.LEVEL_SDK:
        return "SDK 凭据链（provider={}）".format(source or "-")
    if level == credentials.LEVEL_STDLIB:
        return "标准库降级读 ~/.aliyun/config.json"
    return "未知级别（{}）".format(level)


def _print_indented(text: str) -> None:
    """逐行缩进透传多行文本（D6：不再只取首行）。

    credentials.py 精心构造了含 A/B/C 三条修复路径的多行指引，旧实现
    ``str(exc).split("\\n")[0]`` 会把最有诊断价值的那行全部丢弃。
    """
    for line in str(text).splitlines() or [""]:
        print("        {}".format(line))


def _check_creds_offline(config: Dict[str, str]) -> bool:
    """离线口径凭据链体检（D6）：不触发任何网络调用 / 刷新 / 写盘。

    逐级探测「能力」而非「最终生效值」——SDK 级的真实命中需要调
    ``get_credential()``（可能触发 OAuth 续期 / AssumeRole / ECS 元数据探测等
    网络副作用，并可能回写全局 ``~/.aliyun/config.json``），离线口径绝不调用它，
    只报告 SDK 是否已安装。要精确定位「实际生效哪一级」用 ``--creds-live``。

    只调 credentials.py 的**公开离线探测 API**（``probe_explicit`` /
    ``probe_sdk_installed`` / ``probe_stdlib``）：三者均只读、无网络无刷新无写盘，
    且 ``level``/``source`` 与 ``resolve_creds_detailed`` 在同级上完全一致。
    不引用被调模块的私有符号（``_`` 前缀）—— 那是实现细节，重构会静默打断
    本文件，读者也会误以为是推荐用法。

    返回：是否存在**确定性配置错误**（供 ``cmd_check`` 并入退出码，见 O1/C1）。
    仅两类计入硬失败——① 显式 AK/SK 半填（``probe_explicit`` 抛 ``CredentialError``）；
    ② 标准库 profile 的 STS 凭据已过期（``probe_stdlib`` 抛 ``CredentialError`` 且
    ``exc.reason == credentials.REASON_STS_EXPIRED``）**且**第 3 级可达 —— 三级链
    是短路语义，Level 1 命中或半填时 Level 3 可证明不可达，其陈旧状态不影响
    生效凭据，不计入退出码。错误分类一律按 ``CredentialError.reason`` 结构化
    字段判定，严禁用跨模块中文文案子串匹配（文案一改判定就静默 fail-open）。
    以下**不**计入：两级都留空（这是推荐的走凭据链姿势，
    绝不能让 ``--check`` 变红）、SDK 已安装但未调用（离线口径的正常状态）、
    ``~/.aliyun/config.json`` 缺席（合法的无标准库配置姿势）。报告正文逐字不变，
    返回值只影响退出码。
    """
    print("[check] 凭据链状态（离线体检：不触发网络 / 刷新 / 写盘）：")
    hard_failure = False
    # 第 1 级：显式 .env AK/SK（只读判定；命中即最终生效级，无需网络）
    explicit = None  # C1：初始化提到 try 之前，except 路径也保证已绑定
    halffill = False
    try:
        explicit = credentials.probe_explicit(config)
    except credentials.CredentialError as exc:
        explicit = None
        halffill = True
        hard_failure = True  # O1：半填是确定性配置错误 → 计入退出码
        print("  [1] .env 显式 ALIYUN_ACCESS_KEY_*：半填（拒绝静默降级）")
        _print_indented(exc)
    if not halffill:
        if explicit is not None:
            print("  [1] .env 显式 ALIYUN_ACCESS_KEY_*：命中（最高优先，实际生效）")
            print("      AK={}，含 STS={}".format(
                _mask_ak(explicit.access_key_id),
                "是" if explicit.security_token else "否"))
        else:
            print("  [1] .env 显式 ALIYUN_ACCESS_KEY_*：未填（两项均空/占位）→ 交凭据链降级")
    # 第 2 级：SDK（只探测安装态，绝不调用 get_credential()）
    if credentials.probe_sdk_installed():
        print("  [2] alibabacloud_credentials SDK：已安装（离线口径不调用 get_credential()，")
        print("      实际是否命中请用 --creds-live 确认）")
    else:
        print("  [2] alibabacloud_credentials SDK：未安装（pip install alibabacloud-credentials")
        print("      可启用 CLI 凭据链自动刷新）")
    # 第 3 级：标准库只读解析 ~/.aliyun/config.json（含 STS 过期判定，无副作用）
    # C1 可达性门控：三级链是短路语义 —— Level 1 命中（explicit 非空）或半填
    # （解析已在 Level 1 抛错中断）时，真实解析根本走不到 Level 3，其状态
    # （含陈旧的 STS 过期）不影响生效凭据，不得计入退出码（假阳性）。
    stdlib_reachable = explicit is None and not halffill
    try:
        stdlib = credentials.probe_stdlib()
    except credentials.CredentialError as exc:
        print("  [3] 标准库 ~/.aliyun/config.json（只读）：不可用")
        _print_indented(exc)
        # O1/C1：按结构化 reason 分类（不再用中文文案子串匹配）——仅「STS 凭据
        # 已过期」且本级可达时计入退出码；「未找到配置文件」（缺席）是合法的
        # 无标准库姿势，不算失败。
        if not stdlib_reachable:
            print("      （Level 1 已命中，本级不参与生效，不计入退出码）")
        elif exc.reason == credentials.REASON_STS_EXPIRED:
            hard_failure = True
    else:
        print("  [3] 标准库 ~/.aliyun/config.json（只读）：可解析")
        print("      AK={}，含 STS={}，来源={}".format(
            _mask_ak(stdlib.access_key_id),
            "是" if stdlib.security_token else "否",
            stdlib.source))
    print("  提示：离线体检只报告各级「能力」，不判定最终生效级（SDK 级需真实调用）。")
    print("       运行 python3 sample.py --check --creds-live 获取精确命中级别与来源。")
    return hard_failure


def _check_creds_live(config: Dict[str, str]) -> bool:
    """--creds-live：执行完整 ``resolve_creds_detailed()``（允许真实网络 / 刷新）。

    精确报告命中级别 + 人读来源；失败逐行透传完整指引。AK 回显收窄到最多
    4 字符 + 长度（D6）。

    返回：是否存在确定性配置错误（W5）。显式凭据半填（``exc.reason ==
    REASON_HALF_FILLED``）是与解析模式无关的确定性配置错误，离线与 live 两模式
    必须一致计入退出码（旧实现在 live 模式下吞掉半填，门禁被开关削弱）；
    其余 live 解析失败（网络抖动、SDK 刷新失败、STS 过期等运行时/环境态）
    保留既有语义不计入门禁。
    """
    print("[check] 凭据链状态（--creds-live：真实解析，可能触发网络 / 刷新）：")
    try:
        resolved = credentials.resolve_creds_detailed(config)
    except credentials.CredentialError as exc:
        print("  [未配置] 凭据链未解析成功：")
        _print_indented(exc)
        return exc.reason == credentials.REASON_HALF_FILLED
    print("  [OK] 命中：{}".format(_level_label(resolved.level, resolved.source)))
    print("      AK={}，含 STS={}，来源={}".format(
        _mask_ak(resolved.access_key_id),
        "是" if resolved.security_token else "否",
        resolved.source,
    ))
    return False


def cmd_check(args: argparse.Namespace) -> int:
    """全局 --check：env 逐项体检（派生前快照）+ 凭据链状态 + 令牌产物概览。

    默认离线口径（不触发网络）；叠加 ``--creds-live`` 才做真实凭据解析。

    退出码语义（O1/C1/W5）：返回 0 当且仅当「必填项齐全」**且**「凭据链体检无
    确定性配置错误」；任一不满足返回 1，便于 CI 门禁据退出码拦截。确定性配置
    错误仅指：显式 AK/SK 半填（离线与 ``--creds-live`` 两模式**一致**计入）、
    标准库 profile 的 STS 凭据已过期且该级**可达**（Level 1 命中时 Level 3 的
    陈旧过期状态不计入，详见 ``_check_creds_offline``）。两级都留空（推荐姿势）、
    SDK 已装未调用均返回 0。``--creds-live`` 的其余真实解析失败（网络抖动、
    SDK 刷新失败等运行时/环境态）不计入退出码。
    """
    # D6：传入派生前快照 raw_env，报告才能区分「用户配的」与「程序派生猜的」。
    raw = env_mod.load_env()
    config = env_mod.derive_defaults(raw)
    print(env_mod.render_check_report(config, raw_env=raw))
    print()
    creds_hard_failure = False
    if getattr(args, "creds_live", False):
        creds_hard_failure = _check_creds_live(config)
    else:
        creds_hard_failure = _check_creds_offline(config)
    status = tokens_mod.tokens_status()
    print()
    print("[check] 令牌产物（.tokens/，0600）：")
    for name in ("id_token", "wat", "order_at"):
        item = status.get(name, {})
        if not item.get("exists"):
            print("  [ABSENT] {}（尚未生成）".format(name))
        elif item.get("expired"):
            print("  [EXPIRED] {} → {}".format(name, item.get("hint", "请重跑对应步骤")))
        else:
            print("  [VALID] {}".format(name))
    print("  order_rt: {}".format("存在" if status.get("order_rt_exists") else "不存在"))
    ok, _missing = env_mod.check_env(config)
    return 0 if (ok and not creds_hard_failure) else 1


def cmd_setup(args: argparse.Namespace) -> int:
    if args.mode == "console":
        control_plane.run_setup_console()
        return 0
    control_plane.run_setup_script(with_scim=args.with_scim)
    return 0


def cmd_login(args: argparse.Namespace) -> int:
    flow.run_login(port=args.port, timeout=args.timeout)
    return 0


def cmd_exchange_wat(_args: argparse.Namespace) -> int:
    flow.run_exchange_wat()
    return 0


def cmd_obo(_args: argparse.Namespace) -> int:
    flow.run_obo()
    return 0


def cmd_serve_orders(args: argparse.Namespace) -> int:
    from orders.server import serve_foreground

    serve_foreground(port=args.port)
    return 0


def cmd_cleanup(args: argparse.Namespace) -> int:
    control_plane.run_cleanup(assume_yes=args.yes, from_env=args.from_env, keep_pool=args.keep_pool)
    return 0


# ---------------------------------------------------------------------------
# demo：一键串联
# ---------------------------------------------------------------------------


def _http_json(
    url: str, method: str = "GET", bearer: Optional[str] = None,
    body: Optional[Dict[str, Any]] = None, timeout: int = 20,
) -> Tuple[int, Any]:
    """demo 内部 HTTP 调用（本地订单服务）。"""
    data = None
    headers = {"Accept": "application/json"}
    if bearer:
        headers["Authorization"] = "Bearer {}".format(bearer)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return resp.status, payload
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw)
        except ValueError:
            return exc.code, raw


def _print_orders_payload(prefix: str, status: int, payload: Any) -> None:
    print("[{}] HTTP {} →".format(prefix, status))
    if isinstance(payload, dict):
        print("        scope_view={} sub={} 订单数={}".format(
            payload.get("scope_view", "-"), payload.get("sub", "-"), payload.get("count", "-")
        ))
        orders = payload.get("orders") or []
        for order in orders[:5]:
            print("          - {} | {} | {} | {}".format(
                order.get("order_id"), order.get("owner_sub"),
                order.get("title"), order.get("status"),
            ))
        if len(orders) > 5:
            print("          …（其余 {} 笔略）".format(len(orders) - 5))
        if payload.get("error"):
            print("        error={} error_description={}".format(
                payload.get("error"), payload.get("error_description")
            ))
    else:
        print("        {}".format(str(payload)[:300]))


def run_demo(login_port: Optional[int] = None) -> int:
    """demo：起订单服务 → login → exchange-wat → obo（WAT 窗口内自动衔接）→ 调 /orders。

    login_port：显式指定 login loopback 回调端口（None 时从 OAUTH_REDIRECT_URI
    提取，通常为 8765；被占用时可指定如 8766）。
    """
    config = env_mod.derive_defaults(env_mod.load_env())
    flow.require_config(
        config,
        (
            "USER_POOL_ID",
            "OAUTH_CLIENT_ID",
            "SIGNIN_BASE_URL",
            "DATA_ENDPOINT",
            "WI_NAME",
            "OBO_PROVIDER_NAME",
            "ORDER_SERVICE_AUDIENCE",
        ),
    )
    # 提前取密钥（缺了立即失败，别等浏览器登录完才发现）
    flow.client_secret_from_env(config)

    # discovery 懒触发：仅 demo 需要 issuer/jwks，拉取回填空位
    config = discovery.apply_discovery(config)
    flow.require_config(config, ("ORDER_SERVICE_ISSUER", "ORDER_SERVICE_JWKS_URI"))

    # --- 后台起订单服务（临时端口，结束自动停）---
    verifier = TokenVerifier(
        issuer=config["ORDER_SERVICE_ISSUER"],
        audience=config["ORDER_SERVICE_AUDIENCE"],
        jwks_uri=config["ORDER_SERVICE_JWKS_URI"],
    )
    server = make_server(port=0, verifier=verifier)
    orders_port = server.server_address[1]
    orders_base = "http://127.0.0.1:{}".format(orders_port)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print("[demo] 模拟订单服务已在后台启动：{}（GET /health | GET /orders | POST /orders）".format(orders_base))

    # login 回调端口：--port 显式指定优先；缺省从 OAUTH_REDIRECT_URI 提取（默认 8765）
    if login_port:
        resolved_login_port = login_port
    else:
        redirect_uri = config.get("OAUTH_REDIRECT_URI", "")
        try:
            resolved_login_port = int(redirect_uri.rstrip("/").split(":")[-1].split("/")[0])
        except (ValueError, IndexError):
            resolved_login_port = 8765

    try:
        # --- 第 1 步：浏览器登录（无痕窗口提示由 run_login 打印）---
        print("[demo] 第 1 步：login（浏览器联邦登录，loopback 端口 {}）".format(resolved_login_port))
        flow.run_login(port=resolved_login_port, timeout=300, config=config)

        # --- 第 2→3 步：WAT 窗口内自动衔接，不等待用户输入 ---
        print("[demo] 第 2 步：exchange-wat（WAT 有效期仅约 5 分钟，立即进入第 3 步）")
        flow.run_exchange_wat(config)
        print("[demo] 第 3 步：obo（on-behalf-of 换取订单服务令牌）")
        obo_result = flow.run_obo(config)

        # --- 第 4 步：消费令牌调订单服务，演示差异化数据 ---
        at = obo_result.get("order_at") or tokens_mod.load_order_at()
        print("[demo] 第 4 步：用订单服务 AT 调用本地模拟服务")
        status, payload = _http_json("{}/orders".format(orders_base), bearer=at)
        _print_orders_payload("demo GET /orders", status, payload)
        if isinstance(payload, dict) and payload.get("scope_view") == "own":
            print("        （当前 scope 无 read:all → 只能看到本人订单；把你的 sub 配置到")
            print("          orders/mock_data.py 的 SUB_ALIAS / ORDERS_BY_SUB 即可看到数据）")

        # --- POST /orders：演示 write:all ---
        status, payload = _http_json(
            "{}/orders".format(orders_base),
            method="POST",
            bearer=at,
            body={"title": "demo 代下单：企业软件订阅 1 年", "amount": 1999.00},
        )
        _print_orders_payload("demo POST /orders (write:all)", status, payload)

        # --- 收尾指引 ---
        print()
        print("[demo] 全链路完成：入站联邦登录 → WAT 身份升维 → OBO 出站 → 订单服务按身份返回差异化数据。")
        print("[demo] 换一个用户（或无痕窗口换账号）重跑 demo，可见 /orders 返回不同数据。")
        return 0
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)
        print("[demo] 模拟订单服务已停止。")


def cmd_demo(args: argparse.Namespace) -> int:
    return run_demo(login_port=args.port)


# ---------------------------------------------------------------------------
# argparse 装配
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Agent Identity × IDaaS：入站联邦登录 + OBO 出站全链路演示"
        "（纯 Python 标准库即可独立运行；alibabacloud-credentials SDK 为可选增强）",
        epilog="先 cp env.template .env 并填值；python3 {} --check 体检后按步骤执行。".format(PROG),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="环境体检：逐项检查 .env 缺失项（含「在哪取值」指引）与 .tokens/ 令牌状态（纯离线，不触发网络）",
    )
    parser.add_argument(
        "--creds-live",
        action="store_true",
        dest="creds_live",
        help="配合 --check：执行真实凭据解析（可能触发 SDK 网络刷新 / 回写 ~/.aliyun/config.json），"
        "精确报告命中级别与来源；默认 --check 为纯离线体检，不触发网络",
    )
    sub = parser.add_subparsers(dest="command", metavar="<子命令>")

    p_setup = sub.add_parser("setup", help="管控面资源准备（模式 A 控制台清单 / 模式 B 脚本一键）")
    p_setup.add_argument(
        "--mode",
        choices=["console", "script"],
        default="console",
        help="console=打印控制台点选清单；script=OpenAPI 一键创建并回写 .env"
        "（凭据经三级凭据链解析，无需显式 AK；IDaaS 身份源绑定等控制台专属步骤仍需手工完成）",
    )
    p_setup.add_argument(
        "--with-scim",
        action="store_true",
        help="（script 模式）请求开启 SCIM provisioning：本 sample 未实现自动化，仅打印指引",
    )
    p_setup.set_defaults(func=cmd_setup)

    p_login = sub.add_parser("login", help="数据面第 1 步：浏览器联邦登录 → loopback 回调 → 池 ID Token")
    p_login.add_argument("--port", type=int, default=8765, help="loopback 回调端口（默认 8765，被占用时可换）")
    p_login.add_argument("--timeout", type=int, default=300, help="等待浏览器回调超时秒数（默认 300）")
    p_login.set_defaults(func=cmd_login)

    p_wat = sub.add_parser("exchange-wat", help="数据面第 2 步：池 ID Token → WAT（身份升维，有效期约 5 分钟）")
    p_wat.set_defaults(func=cmd_exchange_wat)

    p_obo = sub.add_parser("obo", help="数据面第 3 步：WAT → 订单服务 AT/RT（on-behalf-of 出站）")
    p_obo.set_defaults(func=cmd_obo)

    p_serve = sub.add_parser("serve-orders", help="数据面第 4 步：本地模拟订单企业服务（前台运行）")
    p_serve.add_argument("--port", type=int, default=9090, help="订单服务端口（默认 9090）")
    p_serve.set_defaults(func=cmd_serve_orders)

    p_demo = sub.add_parser("demo", help="一键串联：起订单服务 → login → exchange-wat → obo → 调 /orders")
    p_demo.add_argument(
        "--port",
        type=int,
        default=None,
        help="login loopback 回调端口（默认从 OAUTH_REDIRECT_URI 提取，通常为 8765；"
        "被占用时指定如 8766，白名单无需同步改）",
    )
    p_demo.set_defaults(func=cmd_demo)

    p_cleanup = sub.add_parser(
        "cleanup",
        help="逆序删除 setup 记录在资源清单（.tokens/created_resources.json）内的管控面资源"
        "（幂等，不存在即 [SKIP]；清单缺失时拒绝删除并给指引）",
    )
    p_cleanup.add_argument("--yes", action="store_true", help="跳过删除确认（脚本化用）")
    p_cleanup.add_argument(
        "--keep-pool",
        action="store_true",
        dest="keep_pool",
        help="保留清单中的用户池不删（演示反复迭代时避免重复等待 SSO 编排；池会保留在清单中，"
        "下次 cleanup 仍可删）",
    )
    p_cleanup.add_argument(
        "--from-env",
        action="store_true",
        dest="from_env",
        help="清单缺失时的逃生通道：按 .env 当前值删除（危险，不校验资源归属；须叠加 --yes 双确认）",
    )
    p_cleanup.set_defaults(func=cmd_cleanup)

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # --check 快路径与子命令均纳入 try 白名单（D6）：.env 写了非法 ENVIRONMENT 时
    # derive_defaults 会抛 env.EnvError（继承 RpcError），旧实现 --check 位于 try 之外
    # 会裸栈；其余子命令已覆盖，此处对齐。
    if not args.check and not args.command:
        parser.print_help()
        return 0
    try:
        if args.check:
            return cmd_check(args)
        return args.func(args)
    except (
        flow.FlowError,
        control_plane.SetupError,
        tokens_mod.TokenExpiredError,
        credentials.CredentialError,
        discovery.DiscoveryError,
        RpcError,
    ) as exc:
        print()
        print("[error] {}".format(exc), file=sys.stderr)
        print("[error] 上述信息已包含下一步指引；也可运行 python3 {} --check 复查配置。".format(PROG), file=sys.stderr)
        return 1
    except EOFError:
        # 非交互环境（stdin 已关闭/重定向）下的确认类操作：统一按失败安全方向拒绝
        print(
            "[error] 当前环境非交互（stdin 已关闭），需要确认的操作已按失败安全方向拒绝。\n"
            "[error] 脚本化场景请用对应参数显式确认（如 cleanup --yes）。",
            file=sys.stderr,
        )
        return 1
    except KeyboardInterrupt:
        print("\n[info] 已中断（未完成的步骤可直接重跑，命令均幂等）。", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
