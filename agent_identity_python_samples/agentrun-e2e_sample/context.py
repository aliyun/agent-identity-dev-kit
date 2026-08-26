"""Agent 上下文：承载 OAuth2 授权链接的回传通道。

本地工具触发用户授权时，SDK 通过 on_auth_url 把授权链接
放进队列，由服务层取出并返回给终端用户。

"""
import asyncio
from contextvars import ContextVar
from queue import Queue
from typing import Optional


class AgentContext:
    queue_context: ContextVar[Optional[Queue]] = ContextVar("queue", default=None)

    @staticmethod
    def on_auth_url(url: str, tool_name: str):
        queue = AgentContext.queue_context.get()

        async def _put_to_queue():
            await queue.put(f'Please click the link to authorize {tool_name}: {str(url)} \n\n')

        asyncio.create_task(_put_to_queue())
