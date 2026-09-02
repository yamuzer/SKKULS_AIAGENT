from langchain.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, MessagesState, START, END

def reply_node(state: MessagesState):
    print('\n[reply_node 실행]')
    messages = state['messages']

    print(f'현재 메세지 개수: {len(messages)}')

    for message in messages:
        print(f"{type(message).__name__} : {message.content}" )

    last_message = messages[-1]
    print(['\n마지막 메세지:'])
    print(last_message.content)

    ai_message = AIMessage(
        content = (
            '반갑습니다. Langgraph Message State 실습을 시작해보겠습니다.'
        )
    )

    return {
        'message': [
            ai_message
        ]
    }


builder = StateGraph(MessagesState)

builder.add_node(
    'reply',
    reply_node
)

builder.add_edge(
    START,
    'reply'
)
builder.add_edge(
    'reply',
    END
)

graph = builder.compile()

initial_state = {
    'messages':[
        HumanMessage(
            content='안녕하세요.'
        ),
        AIMessage(
            content= "안녕하세요. 무엇을 도와드릴까요."
        ),
        HumanMessage(
            content="LangGraph 공부를 하고 있습니다."
        )
    ]
}

result = graph.invoke(initial_state)

print('\n최종 메세지')

for index, message in enumerate(result['messages'], start=1):
    print(f"{index}. {type(message).__name__}")
    print(message.content)
    print()
