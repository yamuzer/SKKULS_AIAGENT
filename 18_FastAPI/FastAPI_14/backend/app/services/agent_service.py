from collections.abc import AsyncIterator
from typing import Any


class AgentService:

    def __init__(
            self,
            agent:Any
    ):
        self.agent = agent



    async def invoke(
            self,
            message: str
    ) -> tuple[str, list[str]]:

        return await self.agent.invoke(
            message
        )



    async def stream(
            self, 
            message: str
    ) -> AsyncIterator[str]:
        async for chunk in self.agent.stream(message):
            yield chunk