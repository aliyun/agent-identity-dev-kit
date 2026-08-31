"""``.tokens/`` 令牌落盘与读取：目录 0600、文件 0600、原子写（tmp + os.replace）。

读取时做过期检测并给出「重跑哪一步」指引：
- id_token / order_at：解码 JWT payload 的 exp（不验签，仅本地判断）；
- wat：JWE 本地不可解码，按侧车文件 wat.meta 记录的 acquired_at + TTL(240s) 判断
  （服务端实测有效期约 5 分钟，保守取 240s）。
"""

import base64
import json
import os
import sys
import time
from typing import Any, Dict

from . import env as env_mod

TOKENS_DIR = os.path.join(env_mod.SAMPLE_DIR, ".tokens")

# WAT 本地缓存 TTL（秒）：服务端实测约 5 分钟，留余量取 240s
WAT_TTL_SECONDS = 240

# 各令牌过期后的「重跑哪一步」指引
RERUN_HINT = {
    "id_token": "请重跑数据面第 1 步：python3 sample.py login（用无痕窗口走联邦登录入口）",
    "wat": "请重跑数据面第 2 步：python3 sample.py exchange-wat（WAT 有效期仅约 5 分钟，"
    "拿到后立即执行 obo；demo 命令会自动衔接）",
    "order_at": "请重跑数据面第 3 步：python3 sample.py obo（必要时先 exchange-wat 刷新 WAT）",
}


class TokenExpiredError(Exception):
    """令牌已过期/缺失，message 内自带重跑指引。"""


def _ensure_dir() -> None:
    os.makedirs(TOKENS_DIR, mode=0o700, exist_ok=True)
    # makedirs 的 mode 不保证已存在目录的权限，显式收紧（chmod 偶发静默失败时重试一次）
    for _ in range(2):
        try:
            os.chmod(TOKENS_DIR, 0o700)
            break
        except OSError:
            time.sleep(0.05)
    else:
        # 两次重试仍失败：不再静默吞掉，打告警引导手动修复（令牌文件仍会写入，
        # 但目录权限可能宽于 0700，属于需要用户知晓的安全降级）。
        print(
            "[tokens] 警告：无法将 {} 权限收紧到 0700（chmod 两次失败）。"
            "请手动执行：chmod 700 {}".format(TOKENS_DIR, TOKENS_DIR),
            file=sys.stderr,
        )


def _atomic_write(name: str, content: str) -> str:
    """0600 + 原子写：os.open 以 0600 **创建即带权限**（避免先 open 再 chmod 之间的窗口期），
    flush + fsync 落盘后 os.replace（避免半份文件被读到）。
    """
    _ensure_dir()
    path = os.path.join(TOKENS_DIR, name)
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(content)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    return path


def _read_file(name: str) -> str:
    path = os.path.join(TOKENS_DIR, name)
    if not os.path.isfile(path):
        return ""
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read().strip()


def mask(token: str) -> str:
    """令牌脱敏打印：前 8 字符 + … + 总长度。"""
    if not token:
        return "<empty>"
    return "{}…(len={})".format(token[:8], len(token))


def decode_jwt_payload(token: str) -> Dict[str, Any]:
    """解码 JWT payload（仅本地教学/过期判断用，不做签名校验）。

    payload 不是 JSON 对象（如纯数字/数组）时抛 ValueError——下游统一以
    ``claims.get(...)`` 消费，非 dict 会转成裸 AttributeError。
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("不是合法 JWT（段数 != 3）；若为 JWE（5 段）则本地不可解码")
    payload_b64 = parts[1]
    payload_b64 += "=" * (-len(payload_b64) % 4)
    payload = json.loads(base64.urlsafe_b64decode(payload_b64))
    if not isinstance(payload, dict):
        raise ValueError("JWT payload 不是 JSON 对象（解析结果类型：{}）".format(type(payload).__name__))
    return payload


def save_token(name: str, value: str) -> str:
    """落盘令牌（单值文件）。返回文件路径。"""
    return _atomic_write(name, value)


def save_json(name: str, data: Dict[str, Any]) -> str:
    """落盘 JSON 侧车文件（如 wat.meta）。"""
    return _atomic_write(name, json.dumps(data, ensure_ascii=False, indent=2))


def load_json(name: str) -> Dict[str, Any]:
    raw = _read_file(name)
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except ValueError:
        return {}


def save_wat(wat: str) -> str:
    """落盘 WAT 并写侧车 wat.meta（acquired_at + TTL）。"""
    path = save_token("wat", wat)
    save_json(
        "wat.meta",
        {
            "acquired_at": int(time.time()),
            "ttl": WAT_TTL_SECONDS,
            "note": "WAT 为 JWE 本地不可解码；服务端实测有效期约 5 分钟，"
            "此处按 TTL 秒数保守缓存，过期请重跑 exchange-wat",
        },
    )
    return path


def load_id_token() -> str:
    """读取 id_token，缺失/过期抛 TokenExpiredError（含重跑指引）。"""
    token = _read_file("id_token")
    if not token:
        raise TokenExpiredError(
            "未找到 .tokens/id_token（尚未登录）。{}".format(RERUN_HINT["id_token"])
        )
    try:
        claims = decode_jwt_payload(token)
    except (ValueError, json.JSONDecodeError):
        raise TokenExpiredError(
            ".tokens/id_token 内容不是合法 JWT，可能已损坏。{}".format(RERUN_HINT["id_token"])
        )
    exp = claims.get("exp")
    if isinstance(exp, (int, float)) and exp <= time.time():
        raise TokenExpiredError(
            "池 ID Token 已过期（exp={}）。{}".format(
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(exp)), RERUN_HINT["id_token"]
            )
        )
    return token


def load_wat() -> str:
    """读取 WAT，缺失/超 TTL 抛 TokenExpiredError（含重跑指引）。"""
    wat = _read_file("wat")
    if not wat:
        raise TokenExpiredError("未找到 .tokens/wat（尚未兑换）。{}".format(RERUN_HINT["wat"]))
    meta = load_json("wat.meta")
    acquired_at = meta.get("acquired_at")
    ttl = meta.get("ttl", WAT_TTL_SECONDS)
    if not isinstance(acquired_at, (int, float)):
        # 无侧车（异常落盘）：按文件修改时间兜底
        try:
            acquired_at = os.path.getmtime(os.path.join(TOKENS_DIR, "wat"))
        except OSError:
            acquired_at = time.time()
    if time.time() - acquired_at > ttl:
        raise TokenExpiredError(
            "WAT 已超过本地缓存 TTL（{}s，服务端有效期约 5 分钟）。{}".format(ttl, RERUN_HINT["wat"])
        )
    return wat


def load_order_at() -> str:
    """读取订单服务 AT，缺失/过期抛 TokenExpiredError（含重跑指引）。"""
    token = _read_file("order_at")
    if not token:
        raise TokenExpiredError(
            "未找到 .tokens/order_at（尚未执行 OBO）。{}".format(RERUN_HINT["order_at"])
        )
    try:
        claims = decode_jwt_payload(token)
        exp = claims.get("exp")
        if isinstance(exp, (int, float)) and exp <= time.time():
            raise TokenExpiredError(
                "订单服务 AT 已过期（exp={}）。{}".format(
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(exp)),
                    RERUN_HINT["order_at"],
                )
            )
    except (ValueError, json.JSONDecodeError):
        # 非 JWT 形态（不透明令牌）不做本地过期判断，交由服务端 401 兜底
        pass
    return token


def load_order_rt() -> str:
    """读取订单服务 RT（可能为空；OBO RT 刷新仅作提示，sample 不实现刷新）。"""
    return _read_file("order_rt")


def tokens_status() -> Dict[str, Any]:
    """--check 用：概览 .tokens/ 下各令牌状态（不返回令牌本体）。"""
    status: Dict[str, Any] = {}
    checks = {
        "id_token": load_id_token,
        "wat": load_wat,
        "order_at": load_order_at,
    }
    for name, loader in checks.items():
        exists = os.path.isfile(os.path.join(TOKENS_DIR, name))
        item: Dict[str, Any] = {"exists": exists}
        if exists:
            try:
                loader()
                item["expired"] = False
            except TokenExpiredError as exc:
                item["expired"] = True
                item["hint"] = str(exc)
        status[name] = item
    status["order_rt_exists"] = os.path.isfile(os.path.join(TOKENS_DIR, "order_rt"))
    return status
