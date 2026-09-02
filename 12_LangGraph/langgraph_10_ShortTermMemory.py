from langchain.messages import HumanMessage, AIMessage

from langgraph.graph import StateGraph, MessagesState, START, END

from langgraph.checkpoint.memory import InMemorySaver



def reply_node(state: MessagesState):

    print('\n[reply_node 실행]')

    messages = state['messages']

    print(f'현재 메세지 개수: {len(messages)}')

    print('\n현재 메세지:')

    for index, message in enumerate(messages):
        print(f"{index} {type(message).__name__} : {message.content}")


    last_message = messages[-1]
    print('\n마지막 메세지:')
    print(last_message.content)

    if '이름' in last_message.content:
        remembered_name = None

        for message in messages:
            if isinstance(message, HumanMessage) and '내 이름은' in message.content:
                text = message.content

                remembered_name = (
                    text.replace('내 이름은', '')
                    .replace('이야', '')
                    .replace('야', '')
                    .replace('.', '')
                    .strip()
                )

        if remembered_name:
            answer = f"이전에 이름을 {remembered_name}이라고 말했습니다."
        else:
            answer = "이전 대화에서 이름을 찾지 못했습니다."

    else:
        answer = "알겠습니다. 대화 내용을 기억해보겠습니다."


    return {
        'messages':[
            AIMessage(
                content=answer
            )
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

checkpointer = InMemorySaver()

graph = builder.compile(
    checkpointer=checkpointer
)

# thread 설정
config = {
    'configurable': {
        'thread_id': 'user-001'
    }
}


result = graph.invoke(
    {
        'messages':[
            HumanMessage(
                content='내 이름은 철수야.'
            )
        ]
    },
    config=config
)

print('\n첫 번째 메세지')
for index, message in enumerate(result['messages'], start=1):
    print(f"{type(message).__name__}")
    print(message.content)
    print()



result = graph.invoke(
    {
        'messages':[
            HumanMessage(
                content='내 이름은 뭐였지?'
            )
        ]
    },
    config=config
)

print('\n두 번째 실행 결과:')
for index, message in enumerate(result['messages'], start=1):
    print(f"{type(message).__name__}")
    print(message.content)
    print()