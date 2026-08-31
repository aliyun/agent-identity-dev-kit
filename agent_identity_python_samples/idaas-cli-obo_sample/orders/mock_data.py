"""模拟订单数据：3 个示意身份（employee-alice / employee-bob / admin）差异化订单集。

数据规则（模拟一个真实企业内部订单系统的最小形态）：
- ``sub`` 是用户唯一标识：OBO AT 里的 sub 来自联邦登录的池用户；
- ``scope`` 含 ``read.all`` → 返回全部订单（管理员视角）；
  否则只返回 ``sub`` 本人名下订单（普通员工视角）；
- ``scope`` 含 ``write.all`` → 允许 POST 创建新订单。

如何体验差异化数据：
- 读者登录后拿到的真实 sub 与下方示意 sub 不同，属于「未知用户」→ 本人订单为空，
  这是预期行为；把登录后打印的 sub 填进 ``SUB_ALIAS``（或直接改 ``ORDERS_BY_SUB``）
  即可看到「本人订单」效果；
- 也可用两个不同 IDaaS 账号分别跑 demo，对比同一接口返回不同数据。
"""

from typing import Any, Dict, List

# 示意身份 → 订单列表（读者按自己实际的 sub 配置映射）
ORDERS_BY_SUB: Dict[str, List[Dict[str, Any]]] = {
    "employee-alice": [
        {
            "order_id": "ORD-1001",
            "owner_sub": "employee-alice",
            "title": "采购订单：办公显示器 x2",
            "amount": 2398.00,
            "status": "PAID",
        },
        {
            "order_id": "ORD-1002",
            "owner_sub": "employee-alice",
            "title": "差旅报销：杭州-北京往返",
            "amount": 1860.50,
            "status": "PENDING",
        },
    ],
    "employee-bob": [
        {
            "order_id": "ORD-2001",
            "owner_sub": "employee-bob",
            "title": "采购订单：机械键盘 x1",
            "amount": 699.00,
            "status": "PAID",
        },
    ],
    "admin": [
        {
            "order_id": "ORD-9001",
            "owner_sub": "admin",
            "title": "年度企业授权续费（管理单）",
            "amount": 128000.00,
            "status": "PAID",
        },
    ],
}

# sub 别名表：真实 sub → 示意身份（可选，方便读者把自己的 sub 映射到演示数据）
# 填法示例：{"user_xxxxxxxx…": "employee-alice"}
SUB_ALIAS: Dict[str, str] = {}


def resolve_sub(sub: str) -> str:
    """真实 sub → 示意身份（配了别名则映射，否则原样返回）。"""
    return SUB_ALIAS.get(sub, sub)


def orders_for_sub(sub: str) -> List[Dict[str, Any]]:
    """某用户名下的订单（未配置的 sub 返回空列表）。"""
    return ORDERS_BY_SUB.get(resolve_sub(sub), [])


def all_orders() -> List[Dict[str, Any]]:
    """全部订单（read.all 权限视角），按 order_id 稳定排序。"""
    merged: List[Dict[str, Any]] = []
    for orders in ORDERS_BY_SUB.values():
        merged.extend(orders)
    merged.sort(key=lambda o: str(o.get("order_id", "")))
    return merged


# ---------------------------------------------------------------------------
# POST /orders 创建订单（write.all）
# ---------------------------------------------------------------------------

_next_order_seq = [3000]


def create_order(sub: str, title: str, amount: Any) -> Dict[str, Any]:
    """以 sub 身份受理一笔新订单（内存态，重启即失——演示用）。"""
    _next_order_seq[0] += 1
    order = {
        "order_id": "ORD-{}".format(_next_order_seq[0]),
        "owner_sub": resolve_sub(sub),
        "title": title,
        "amount": amount,
        "status": "ACCEPTED",
    }
    ORDERS_BY_SUB.setdefault(resolve_sub(sub), []).append(order)
    return order
