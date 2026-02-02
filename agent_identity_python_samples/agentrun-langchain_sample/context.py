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
