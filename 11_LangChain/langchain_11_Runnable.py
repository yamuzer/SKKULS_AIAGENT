import os, csv, math
from collections import defaultdict
from dotenv import load_dotenv
from pathlib import Path
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "../.env"
CSV_PATH = BASE_DIR / "data" / "support_documents_24.csv"

CHROMA_PATH = BASE_DIR / "chroma_langchain_data"
MARKER_PATH = CHROMA_PATH / 'created.marker'

COLLECTION_NAME = "support_documents"

CHUNK_SIZE = 40
CHUNK_OVERLAP = 10

load_dotenv(dotenv_path=ENV_PATH)
api_key = os.getenv(
    "GEMINI_API_KEY"
)

if not api_key:
    raise ValueError('GEMINI_API_KEY를 읽을 수 없습니다.')

if not CHROMA_PATH.exists():
    raise FileNotFoundError('\nChromaDB를 찾을 수 없습니다.')

EMBEDDING_MODEL = (
    'gemini-embedding-2'
)

OUTPUT_DIMENSION = 768

embeddings = GoogleGenerativeAIEmbeddings(
    model=EMBEDDING_MODEL,
    api_key=api_key,
    output_dimensionality=OUTPUT_DIMENSION
)

try:
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH,
        create_collection_if_not_exists=False
    )
except Exception as error:
    raise RuntimeError(
        'Chroma collection을 열 수 없습니다.'
    )

stored_data = vector_store.get(
    limit=5,
    include=[
        'documents',
        'metadatas'
    ]
)

stored_ids = stored_data.get('ids', [])

if not stored_ids:
    raise RuntimeError(
        'chorma collection을 열었지만 저장된 document가 없습니다.'
        )


retriever = vector_store.as_retriever(
    search_type='similarity',
    search_kwargs={
        'k':3
    }
)

def print_title(title: str) -> None:
    print('\n' + '=' * 80)
    print(title)
    print('='*80)
    print()

def format_documents(
        documents: list[Document]
) -> str:

    context_blocks = []

    for index, document in enumerate(documents, start=1):
        metadata = document.metadata

        parent_doc_id = metadata.get(
            'parent_doc_id',
            metadata.get('doc_id', 'UNKNOWN')
        )

        title = metadata.get('title', '제목 없음')
        category_ko = metadata.get('category_ko', '분류 없음')

        block = (
            f"[문서 {index}]\n"
            f"[문서 ID: {parent_doc_id}]\n"
            f"[제목: {title}]\n"
            f"[카테고리: {category_ko}]\n"
            f"[내용: {document.page_content}]\n"
        )

        context_blocks.append(block)


    return '\n\n'.join(context_blocks)

format_runnable = RunnableLambda(format_documents)

question_passthrougth = RunnablePassthrough()

model = ChatGoogleGenerativeAI(
    model='gemini-3.7-flash',
    api_key=api_key
)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            (
                '당신은 고객지원 지식 문서를 기반으로 답변하는 AI 도우미입니다.\n\n'
                '반드시 제공된 Context만 근거로 답변하세요.\n'
                'Context에서 답을 찾을 수 없다면 "제공된 문서만으로 확인 할 수 없습니다."라고 답하세요.\n'
                '추측하거나 없는 정책을 만들지 마세요.\n'
                '답변은 한국어로 간결하게 작성하세요.\n\n'
                '[Context]\n'
                '{context}'
            )
        ),
        (
            'human',
            '{question}'
        )
    ]
)

'''
같은 question 

경로 A:
question -> retriever -> List[Document] -> RunnableLambda(format_documents) -> context

경로 B:
question -> RunnablePassThrough -> 같은 question
'''

rag_input_chain = {
    'context': (retriever | format_runnable),
    'question': question_passthrougth
}

rag_chain = (rag_input_chain | prompt | model | StrOutputParser())


sample_question = '환불은 언제 반영되나요?'

passed_question = question_passthrougth.invoke(sample_question)

print_title('RunnablePassThrough')
print(f'입력: {sample_question}')
print(passed_question)

context_chain = retriever | format_runnable

context_only = context_chain.invoke(sample_question)




print_title('RunnableLambda')
print(context_only)


question = '환불 승인은 완료됐는데 카드에 아직 돈이 들어오지 않았습니다. 왜 그런가요?'

answer = rag_chain.invoke(question)
print_title('RAG Chain Invoke')
print(f'질문: {question}')
print(f'답변: \n{answer}')    