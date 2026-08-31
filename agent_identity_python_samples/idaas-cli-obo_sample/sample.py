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

纯 Python 标准库（3.9+），零第三方运行时依赖。
"""

import argparse
import json
import sys
import threading
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple

from lib import control_plane
from lib import env as env_mod
from lib import flow
from lib import tokens as tokens_mod
from lib.rpc import RpcError
from orders.server import make_server
from orders.verify import TokenVerifier

PROG = "sample.py"


# ---------------------------------------------------------------------------
# 子命令实现
# ---------------------------------------------------------------------------


def cmd_check(_args: argparse.Namespace) -> int:
    """全局 --check：env 逐项体检 + 令牌产物概览。"""
    config = env_mod.load_env()
    print(env_mod.render_check_report(config))
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
    return 0 if ok else 1


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
            "ORDER_SERVICE_ISSUER",
            "ORDER_SERVICE_JWKS_URI",
            "ALIYUN_ACCESS_KEY_ID",
            "ALIYUN_ACCESS_KEY_SECRET",
        ),
    )
    # 提前取密钥（缺了立即失败，别等浏览器登录完才发现）
    flow.client_secret_from_env(config)

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
            print("        （当前 scope 无 read.all → 只能看到本人订单；把你的 sub 配置到")
            print("          orders/mock_data.py 的 SUB_ALIAS / ORDERS_BY_SUB 即可看到数据）")

        # --- POST /orders：演示 write.all ---
        status, payload = _http_json(
            "{}/orders".format(orders_base),
            method="POST",
            bearer=at,
            body={"title": "demo 代下单：企业软件订阅 1 年", "amount": 1999.00},
        )
        _print_orders_payload("demo POST /orders (write.all)", status, payload)

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
        description="Agent Identity × IDaaS：入站联邦登录 + OBO 出站全链路演示（纯标准库）",
        epilog="先 cp env.template .env 并填值；python3 {} --check 体检后按步骤执行。".format(PROG),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="环境体检：逐项检查 .env 缺失项（含「在哪取值」指引）与 .tokens/ 令牌状态",
    )
    sub = parser.add_subparsers(dest="command", metavar="<子命令>")

    p_setup = sub.add_parser("setup", help="管控面资源准备（模式 A 控制台清单 / 模式 B 脚本一键）")
    p_setup.add_argument(
        "--mode",
        choices=["console", "script"],
        default="console",
        help="console=打印控制台点选清单；script=OpenAPI 一键创建并回写 .env（需 AK）",
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
    if args.check:
        return cmd_check(args)
    if not args.command:
        parser.print_help()
        return 0
    try:
        return args.func(args)
    except (
        flow.FlowError,
        control_plane.SetupError,
        tokens_mod.TokenExpiredError,
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
