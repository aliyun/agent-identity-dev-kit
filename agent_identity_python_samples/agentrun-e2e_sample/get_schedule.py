"""日程查询工具（演示 STS 临时凭据注入）。

STS 凭据由 agent-identity-python-sdk 自动注入（@requires_sts_token），
代码内不出现任何长期 AK。

结构说明：装饰器作用于内部实现 _get_schedule，外层 wrapper 提供干净的
工具签名（隐藏被注入的 sts_credential 参数）。
"""
from agent_identity_python_sdk.core import requires_sts_token
from agent_identity_python_sdk.model.stscredential import STSCredential


@requires_sts_token(inject_param_name="sts_credential")
def _get_schedule(date: str, sts_credential: STSCredential) -> str:
    if not sts_credential:
        raise Exception("Sts credential is required")

    return (
        f"Schedule for {date}:\n"
        "1. 9:00 AM Opening meeting\n"
        "2. 10:00 AM Check-in\n"
        "3. 11:00 AM Check-out"
    )


def get_schedule(date: str) -> str:
    """Mock tool to get schedule information.

    Args:
        date: The date to get schedule for.
    """
    return _get_schedule(date=date)
