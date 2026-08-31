"""阿里云 RPC API 纯标准库客户端（RPC 风格 / V1 签名 / HMAC-SHA1）。

签名逻辑以预发实测通过的实现为蓝本（镜像 alibabacloud_tea_openapi client.py 的
RPC 分支与 alibabacloud_openapi_util get_rpcsignature），零第三方依赖：

- ``style='query'``：业务参数放 query（如 GetWorkloadAccessTokenForJWT）；
- ``style='formData'``：业务参数以 query 编码展开并入签名集合，body 以
  ``application/x-www-form-urlencoded`` 发送，签名放 query——
  GetResourceOAuth2Token 必须用这种风格（实测 query/JSON body 均报 MissingParameter）。

重试策略（RpcError.retryable / should_retry）：
- 网络错误 / HTTP 5xx / Throttling*：默认 3 次指数退避；
- ``wait_window=True``（预发滚动发布场景）：MissingParameter.* 额外重试 30×5s，
  等待新旧实例窗口切换；
- SignatureDoesNotMatch / 凭证类（InvalidAccessKeyId 等）/ InvalidParameter /
  Forbidden.*：不重试（重试也不会成功，且掩盖真实原因）。
"""

import base64
import hashlib
import hmac
import json
import random
import ssl
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, quote_plus, urlencode

DEFAULT_USER_AGENT = "agentidentity-idaas-cli-obo-sample/1.0"

# ---------------------------------------------------------------------------
# SSL 上下文：默认上下文（不关闭证书校验）；系统无 CA 时尝试 certifi（可选依赖）兜底。
# ---------------------------------------------------------------------------

_SSL_CONTEXT: Optional["ssl.SSLContext"] = None
_SSL_LOCK = threading.Lock()


def ssl_context() -> "ssl.SSLContext":
    """返回进程级共享 SSL 上下文（verify 开启）。"""
    global _SSL_CONTEXT
    with _SSL_LOCK:
        if _SSL_CONTEXT is None:
            ctx = ssl.create_default_context()
            stats = ctx.cert_store_stats()
            if stats.get("x509", 0) == 0:
                try:  # pragma: no cover - 依赖环境是否有 certifi
                    import certifi  # type: ignore

                    ctx = ssl.create_default_context(cafile=certifi.where())
                except Exception:
                    # 保持默认上下文（校验仍开启）；连接失败时错误信息会引导安装 certifi
                    pass
            _SSL_CONTEXT = ctx
        return _SSL_CONTEXT


# ---------------------------------------------------------------------------
# 基础工具（镜像 tea_openapi utils.py / form.py）
# ---------------------------------------------------------------------------


def percent_encode(value: str, safe: str = "~") -> str:
    """RPC V1 签名专用百分号编码：UTF-8 + 仅 ``~`` 不编码（``/`` 等保留字也会被编码）。"""
    return quote(str(value), safe=safe, encoding="utf-8")


def get_timestamp(now: Optional[float] = None) -> str:
    """RPC meta 参数 Timestamp：UTC 时间，格式 %Y-%m-%dT%H:%M:%SZ。

    timezone-aware 写法（datetime.fromtimestamp + tz=timezone.utc，3.9+ 兼容），
    避免 datetime.utcnow()/utcfromtimestamp() 在 Python 3.12+ 的 DeprecationWarning。
    """
    if now is None:
        now = time.time()
    return datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_NONCE_SEQ = [0]
_NONCE_LOCK = threading.Lock()


def get_nonce() -> str:
    """RPC meta 参数 SignatureNonce：md5(进程-线程-毫秒-序号-随机数)。"""
    with _NONCE_LOCK:
        seq = _NONCE_SEQ[0]
        _NONCE_SEQ[0] += 1
    thread_id = threading.get_ident()
    current_time = int(time.time() * 1000)
    rand_num = random.getrandbits(64)
    msg = "{}-{}-{}-{}-{}".format(current_time, thread_id, current_time, seq, rand_num)
    return hashlib.md5(msg.encode("utf-8")).hexdigest()


def _object_handler(key: str, value: Any, out: Dict[str, str]) -> None:
    """展开嵌套参数：dict → k.sub 递归；list → k.N（N 从 1 起）；标量 → str()。"""
    if value is None:
        return
    if isinstance(value, dict):
        for k, v in value.items():
            _object_handler("{}.{}".format(key, k), v, out)
    elif isinstance(value, (list, tuple)):
        for index, val in enumerate(value):
            _object_handler("{}.{}".format(key, index + 1), val, out)
    else:
        if key.startswith("."):
            key = key[1:]
        out[key] = str(value)


def utils_query(filter_dict: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """dict → 扁平化参数集（用于 formData body 的展开与签名集合）。"""
    out: Dict[str, str] = {}
    if filter_dict:
        _object_handler("", filter_dict, out)
    return out


def to_form_string(val: Dict[str, str]) -> str:
    """form body 序列化：按 key 排序后 urlencode（镜像 DaraForm.to_form_string）。"""
    if not val:
        return ""
    return urlencode({k: val[k] for k in sorted(val)})


# ---------------------------------------------------------------------------
# RPC V1 签名（镜像 openapi_util client.get_rpcsignature）
# ---------------------------------------------------------------------------


def canonical_query_string(signed_params: Dict[str, Any]) -> str:
    """规范化查询串：按 key 排序，k=v 以 & 连接（首字符无 &），percent_encode 编码。"""
    cqs = ""
    for k in sorted(signed_params.keys()):
        value = signed_params[k]
        if value is None:
            continue
        cqs += "&{}={}".format(percent_encode(k), percent_encode(value))
    return cqs[1:]


def string_to_sign(method: str, signed_params: Dict[str, Any]) -> str:
    """待签名串：METHOD & %2F & quote_plus(canonical_query_string, safe='~')。"""
    return "{}&%2F&{}".format(
        method, quote_plus(canonical_query_string(signed_params), safe="~", encoding="utf-8")
    )


def get_rpc_signature(signed_params: Dict[str, Any], method: str, secret: str) -> str:
    """HMAC-SHA1(secret + '&', string_to_sign) → base64。"""
    digest_maker = hmac.new(
        (secret + "&").encode("utf-8"),
        string_to_sign(method, signed_params).encode("utf-8"),
        digestmod=hashlib.sha1,
    )
    return str(base64.b64encode(digest_maker.digest()), encoding="utf-8")


# ---------------------------------------------------------------------------
# 请求构造（独立函数便于离线测试固定向量）
# ---------------------------------------------------------------------------


def build_signed_request(
    endpoint: str,
    action: str,
    version: str,
    params: Optional[Dict[str, Any]],
    style: str = "query",
    creds: Tuple[str, str, Optional[str]] = ("<AK>", "<SK>", None),
    method: str = "POST",
    timestamp: Optional[str] = None,
    nonce: Optional[str] = None,
) -> Dict[str, Any]:
    """构造已签名请求（不发网络）。返回 dict(url, body, headers, signed_params)。

    creds = (access_key_id, access_key_secret, security_token or None)。
    SecurityToken 同时进入签名集合与最终 query（STS 双凭证要求）。
    """
    if style not in ("query", "formData"):
        raise ValueError("style 只支持 'query' 或 'formData'，收到：{!r}".format(style))
    ak, sk, security_token = creds
    params = dict(params or {})

    query: Dict[str, Any] = {
        "Action": action,
        "Format": "json",
        "Version": version,
        "Timestamp": timestamp or get_timestamp(),
        "SignatureNonce": nonce or get_nonce(),
    }
    headers = {
        "host": endpoint,
        "x-acs-version": version,
        "x-acs-action": action,
        "user-agent": DEFAULT_USER_AGENT,
    }

    body_str: Optional[str] = None
    if style == "query":
        # 业务参数直接放 query
        query.update(params)
    else:
        # formData 风格：body 展开（dict→k.sub / list→k.N）后 urlencode 发送；
        # 展开结果并入签名集合；签名本身仍放 query（不放 body）。
        flat = utils_query(params)
        body_str = to_form_string(flat)
        headers["content-type"] = "application/x-www-form-urlencoded"

    if security_token:
        query["SecurityToken"] = security_token
    query["SignatureMethod"] = "HMAC-SHA1"
    query["SignatureVersion"] = "1.0"
    query["AccessKeyId"] = ak

    signed_params: Dict[str, Any] = dict(query)
    if style == "formData":
        signed_params.update(utils_query(params))

    query["Signature"] = get_rpc_signature(signed_params, method, sk)

    url = "https://{}?{}".format(endpoint, urlencode(query))
    return {
        "url": url,
        "body": body_str.encode("utf-8") if body_str is not None else None,
        "headers": headers,
        "signed_params": signed_params,
        "method": method,
    }


# ---------------------------------------------------------------------------
# 错误与重试
# ---------------------------------------------------------------------------


class RpcError(Exception):
    """阿里云 RPC 错误：status / code / message / request_id / retryable。"""

    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        request_id: str = "",
        retryable: bool = False,
    ):
        super().__init__(
            "HTTP {} code={} message={} request_id={}".format(status, code, message, request_id)
        )
        self.status = status
        self.code = code
        self.message = message
        self.request_id = request_id
        self.retryable = retryable

    def __str__(self) -> str:
        return (
            "[RpcError] HTTP {} | code={} | message={} | RequestId={}"
            .format(self.status, self.code, self.message, self.request_id or "-")
        )


# 网络层/服务端抖动类错误：可重试
_RETRYABLE_CODE_PREFIXES = ("Throttling",)
# 凭证/签名/参数/权限类错误：重试无意义
_NON_RETRYABLE_CODE_PREFIXES = (
    "SignatureDoesNotMatch",
    "IncompleteSignature",
    "InvalidAccessKeyId",
    "InvalidSecurityToken",
    "InvalidParameter",
    "Forbidden",
    "AuthFailure",
    "EntityAlreadyExists",
    "EntityNotExists",
    "MissingParameter",
)


def classify_error(status: int, code: str) -> Tuple[bool, str]:
    """判定错误可否重试。返回 (retryable, reason)。"""
    if status >= 500:
        return True, "HTTP 5xx（服务端错误）"
    if status == 0 or status == -1:
        return True, "网络错误"
    for prefix in _NON_RETRYABLE_CODE_PREFIXES:
        if code.startswith(prefix):
            return False, "确定性业务错误（{}*），重试无意义".format(prefix)
    for prefix in _RETRYABLE_CODE_PREFIXES:
        if code.startswith(prefix):
            return True, "限流（{}*），退避后可重试".format(prefix)
    if status in (408, 429):
        return True, "HTTP {}（超时/限流）".format(status)
    return False, "HTTP {} 业务错误".format(status)


# ---------------------------------------------------------------------------
# rpc_call
# ---------------------------------------------------------------------------


def _parse_error_payload(status: int, raw: str) -> RpcError:
    """从错误响应体解析 RpcError（兼容 JSON 与非 JSON 体）。"""
    code, message, request_id = "", "", ""
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            code = str(data.get("Code") or data.get("code") or "")
            message = str(data.get("Message") or data.get("message") or "")[:300]
            request_id = str(data.get("RequestId") or data.get("requestId") or "")
    except (ValueError, TypeError):
        message = (raw or "")[:300]
    retryable, _reason = classify_error(status, code)
    return RpcError(status, code, message, request_id, retryable)


def rpc_call(
    endpoint: str,
    action: str,
    version: str,
    params: Optional[Dict[str, Any]] = None,
    style: str = "query",
    creds: Tuple[str, str, Optional[str]] = ("<AK>", "<SK>", None),
    timeout: int = 30,
    max_retries: int = 3,
    wait_window: bool = False,
    logger=None,
) -> Dict[str, Any]:
    """执行一次 RPC 调用，成功返回响应 dict（含 RequestId），失败抛 RpcError。

    wait_window=True 时：MissingParameter.* 视为预发滚动发布窗口抖动，
    追加重试（最多 30 次、每次间隔 5s）；窗口等待**不消耗**普通退避预算
    （attempt 归零），窗口结束后遇 Throttling/5xx 仍有完整的 3 次重试。
    """
    window_attempts = 30 if wait_window else 0
    attempt = 0
    backoff = 1.0
    while True:
        attempt += 1
        try:
            return _do_call(endpoint, action, version, params, style, creds, timeout)
        except RpcError as exc:
            # wait_window：MissingParameter.* 交给窗口重试计数（且不被默认 3 次上限拦截）
            if wait_window and exc.code.startswith("MissingParameter"):
                if window_attempts > 0:
                    window_attempts -= 1
                    # 窗口等待不计入 attempt：否则 N 次窗口抖动后，后续普通可重试
                    # 错误（Throttling/5xx）会被 attempt <= max_retries 提前放弃。
                    attempt = 0
                    if logger:
                        logger(
                            "[rpc] {} 报 {}（疑似滚动发布窗口）→ 5s 后重试"
                            "（剩余 {} 次）".format(action, exc.code, window_attempts)
                        )
                    time.sleep(5)
                    continue
            retryable, reason = classify_error(exc.status, exc.code)
            if retryable and attempt <= max_retries:
                if logger:
                    logger(
                        "[rpc] {} 第 {} 次失败（{}）→ {:.0f}s 后重试".format(
                            action, attempt, reason, backoff
                        )
                    )
                time.sleep(backoff)
                backoff = min(backoff * 2, 8.0)
                continue
            raise


def _do_call(
    endpoint: str,
    action: str,
    version: str,
    params: Optional[Dict[str, Any]],
    style: str,
    creds: Tuple[str, str, Optional[str]],
    timeout: int,
) -> Dict[str, Any]:
    req_info = build_signed_request(endpoint, action, version, params, style, creds)
    request = urllib.request.Request(
        req_info["url"], data=req_info["body"], headers=req_info["headers"],
        method=req_info["method"],
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=ssl_context()) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = ""
        try:
            raw = exc.read().decode("utf-8", errors="replace")
        except Exception:  # pragma: no cover - 读错误体失败
            pass
        error = _parse_error_payload(exc.code, raw)
        raise error from None
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        err = RpcError(0, "NetworkError", "无法连接 {}：{}".format(endpoint, reason), "", True)
        raise err from None
    except (TimeoutError, ConnectionError, OSError) as exc:
        err = RpcError(0, "NetworkError", "连接超时/中断：{}".format(exc), "", True)
        raise err from None
    except json.JSONDecodeError as exc:
        err = RpcError(-1, "BadResponse", "响应不是合法 JSON：{}".format(exc), "", True)
        raise err from None


def err_code(resp: Optional[Dict[str, Any]]) -> str:
    """从响应 dict 提取错误码（无错返回空串）。"""
    if not isinstance(resp, dict):
        return ""
    return str(resp.get("Code") or resp.get("code") or "")
