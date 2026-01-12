import asyncio
from contextvars import ContextVar
from queue import Queue
from typing import Optional
from agentscope.message import Msg

class AgentContext:
    queue_context: ContextVar[Optional[Queue]] = ContextVar("queue", default=None)

    @staticmethod
    async def on_auth_url(url: str, tool_name: str):
        queue = AgentContext.queue_context.get()

        async def _put_to_queue():
            await queue.put((
                Msg(
                    name="Friday",
                    role="assistant",

                    content=[{'type': 'text', 'text': f'Please click the link to authorize {tool_name}: {str(url)} \n\n'}]
                ),
                False
            ))

        asyncio.create_task(_put_to_queue())
