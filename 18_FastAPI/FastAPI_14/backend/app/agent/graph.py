from collections.abc import AsyncIterator

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.tools import TOOLS


SYSTEM_PROMPT = """
당신은 AI 교육을 돕는 LangGraph Agent입니다.

규칙:
1. 계산이 필요하면 계산 Tool을 사용하세요.
2. FastAPI, React, LangGraph 수업 정보가 필요하면 get_course_info Tool을 사용하세요.
3. Tool이 필요하지 않는 일반 질문은 직접 답하세요.
4. Tool 결과를 사용자가 이해하기 쉽게 정리하세요.
5. 답변은 한국어로 작성하세요.
""".strip()



class LangGraphAgent:

    def __init__(
            self,
            api_key: str,
            model_name: str
    ):

        self.model = ChatGoogleGenerativeAI(
            model=model_name,
            api_key=api_key,
            max_retries=2
        )

        self.model_with_tools = self.model.bind_tools(TOOLS)

        self.graph = self._build_graph()



    def _build_graph(self):

        async def agent_node(
                state: MessagesState
        ):
            messages = [
                SystemMessage(
                    content=SYSTEM_PROMPT
                ),
                *state['messages']
            ]

            response = await self.model_with_tools.ainvoke(messages)

            return {
                'messages': response
            }


        builder = StateGraph(MessagesState)

        builder.add_node(
            'agent',
            agent_node
        )

        builder.add_node(
            'tools',
            ToolNode(TOOLS)
        )


        builder.add_edge(
            START,
            'agent'
        )


        builder.add_conditional_edges(
            'agent',

            tools_condition,

            {
                'tools': 'tools',
                '__end__': END
            }
        )

        builder.add_edge(
            'tools',
            'agent'
        )

        return builder.compile()


    @staticmethod
    def _message_text(message) -> str:
        text = getattr(
            message,
            'text',
            None
        )

        if isinstance(text, str):
            return text

        content = getattr(
            message,
            'content',
            ''
        )

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts = []

            for block in content:
                if isinstance(block, dict) and block.get('type') == 'text':
                    parts.append(
                        block.get('text', '')
                    )

            return ''.join(parts)

        return str(content)


    async def invoke(
            self,
            message: str
    ) -> tuple[str, list[str]]:

        result = await self.graph.ainvoke(
            {
                'messages': [
                    HumanMessage(
                        content=message
                    )
                ]
            }
        )

        messages = result['messages']

        answer = self._message_text(messages[-1])

        used_tools = []

        for current_message in messages:
            if isinstance(current_message, ToolMessage):
                tool_name = current_message.name

                if tool_name and tool_name not in used_tools:
                    used_tools.append(tool_name)

        return (
            answer,
            used_tools
        )



    async def stream(
            self,
            message: str
    ) -> AsyncIterator[str]:

        async for message_chunk, metadata in self.graph.astream(
            {
                'messages':[
                    HumanMessage(
                        content=message
                    )
                ]
            },
            stream_mode='messages'
        ):
            if metadata.get('langgraph_node') != 'agent':
                continue

            text = self._message_text(message_chunk)

            if text:
                yield text
    

        