'''
question -> filter + threshold retriever -> document 존재 여부 분기
'''
import os
from dotenv import load_dotenv
from pathlib import Path

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableLambda, RunnableBranch

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "../.env"
CSV_PATH = BASE_DIR / "data" / "support_documents_24.csv"

CHROMA_PATH = BASE_DIR / "chroma_langchain_data"
COLLECTION_NAME = "support_documents"

TOP_K = 4
SCORE_THRESHOLD = 0.70
FILTER_CATEGORY = 'refund'


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
    limit=3,
    include=[
        'metadatas'
    ]
)

stored_ids = stored_data.get('ids', [])

if not stored_ids:
    raise RuntimeError(
        'chorma collection을 열었지만 저장된 document가 없습니다.'
        )


def print_title(title: str) -> None:
    print('\n' + '=' * 80)
    print(title)
    print('='*80)
    print()


retriever = vector_store.as_retriever(
    search_type='similarity_score_threshold',
    search_kwargs={
        'k': TOP_K,
        'score_threshold': SCORE_THRESHOLD,
        'filter': {
            'category': FILTER_CATEGORY
        }
    }
)


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


def prepare_prompt_input(data: dict) -> dict:

    return {
        'question': data['question'],
        'context': format_documents(
            data['documents']
        )
    }


def make_success_result(
    data: dict
) -> dict:

    return {
        'answer': data['answer'],
        'documents': data['documents'],
        'llm_called': True
    }


def make_no_document_result(
    data: dict
) -> dict:

    return {
        'answer': '관련 근거 문서를 찾지 못했습니다.',
        'documents': [],
        'llm_called': False
    }


model = ChatGoogleGenerativeAI(
    model='gemini-3.7-flash',
    api_key=api_key
)


prompt = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            (
                "당신은 고객 지원 지식 문서를 기반으로 답변하는 AI 도우미입니다.\n\n"
                "반드시 제공된 Context만 근거로 답변하세요.\n"
                "추측하거나 없는 정책을 만들지 마세요.\n"
                "답변은 한국어로 간결하게 작성하세요.\n"
                "[Context]\n"
                "{context}"
            )
        ),
        (
            'human',
            '{question}'
        )
    ]
)

answer_chain = RunnableLambda(prepare_prompt_input) | prompt | model | StrOutputParser()

retrieval_chain = {
    'question': RunnablePassthrough(),
    'documents': retriever
}

success_branch = RunnablePassthrough.assign(answer=answer_chain) | RunnableLambda(make_success_result)

no_document_branch = RunnableLambda(make_no_document_result)

'''
len(documents) > 0

True: success branch

False: no_document_branch
'''

branch = RunnableBranch(
    (lambda data: len(data["documents"]) > 0, success_branch),
    no_document_branch
)

safe_rag_chain = (retrieval_chain | branch)


def print_result(
        question: str,
        result: dict
) -> None:

    print('\n질문:')
    print(question)
    print(f"\nLLM 호출 여부: {result['llm_called']}")
    print(f"\n검색 문서 수: {len(result['documents'])}")
    print("\n답변:")
    print(result['answer'])

    if result['documents']:
        print('\n검색 근거:')

        for document in result['documents']:
            metadata = document.metadata

            print(
                f"-{metadata.get('parent_doc_id', metadata.get('doc_id'))} / {metadata.get('title')}"
            )
relevant_question = (
    '환불 승인은 완료됐는데 카드에 아직 금액이 반영되지 않았습니다. 얼마나 걸릴 수 있나요?'
)
relevant_result = safe_rag_chain.invoke(relevant_question)
print_result(relevant_question, relevant_result)

irrelevant_question = '서울 내일 날씨와 강수 확률을 알려주세요.'
irrelevant_result = safe_rag_chain.invoke(irrelevant_question)

print_result(irrelevant_question, irrelevant_result)