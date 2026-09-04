import json

from collections import Counter
from pathlib import Path


# ============================================================
# 1. 기본 경로
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent


DATA_DIR = (
    BASE_DIR
    / "data"
)


DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


DOCUMENT_PATH = (
    DATA_DIR
    / "documents.json"
)


GRAPH_PATH = (
    DATA_DIR
    / "knowledge_graph.json"
)


# ============================================================
# 2. 부서 데이터
# ============================================================

departments = [

    {
        "name": "AI개발팀",
        "location": "판교",
        "description": (
            "머신러닝, 컴퓨터 비전, "
            "생성형 AI 서비스를 개발한다."
        ),
    },

    {
        "name": "데이터분석팀",
        "location": "서울",
        "description": (
            "고객, 매출, 서비스 데이터를 분석하고 "
            "예측 모델을 개발한다."
        ),
    },

    {
        "name": "플랫폼개발팀",
        "location": "서울",
        "description": (
            "데이터 플랫폼과 사내 API 시스템을 "
            "개발하고 운영한다."
        ),
    },

    {
        "name": "서비스기획팀",
        "location": "부산",
        "description": (
            "AI 서비스 기획과 사용자 요구사항 "
            "분석을 담당한다."
        ),
    },

    {
        "name": "품질관리팀",
        "location": "대전",
        "description": (
            "제조 품질 데이터 분석과 "
            "불량 원인 분석을 담당한다."
        ),
    },

    {
        "name": "클라우드운영팀",
        "location": "인천",
        "description": (
            "클라우드 인프라와 서비스 운영 "
            "환경을 관리한다."
        ),
    },

]


# ============================================================
# 3. 프로젝트 데이터
# ============================================================

projects = [

    {
        "name": "VisionGuard",
        "department": "AI개발팀",
        "description": (
            "제조 공정의 제품 이미지를 분석하여 "
            "표면 결함과 불량 여부를 탐지하는 "
            "컴퓨터 비전 프로젝트이다."
        ),
        "technologies": [
            "PyTorch",
            "OpenCV",
            "Python",
        ],
    },

    {
        "name": "SmartFactory",
        "department": "품질관리팀",
        "description": (
            "생산 설비와 품질 데이터를 분석하여 "
            "공정 이상을 조기에 발견하는 "
            "스마트 제조 프로젝트이다."
        ),
        "technologies": [
            "Python",
            "Pandas",
            "PostgreSQL",
        ],
    },

    {
        "name": "CustomerInsight",
        "department": "데이터분석팀",
        "description": (
            "고객 구매 행동과 서비스 이용 기록을 "
            "분석하여 고객 특성과 관심 상품을 "
            "파악하는 프로젝트이다."
        ),
        "technologies": [
            "Python",
            "Pandas",
            "ChromaDB",
        ],
    },

    {
        "name": "SalesForecast",
        "department": "데이터분석팀",
        "description": (
            "과거 판매 기록과 계절 정보를 이용해 "
            "상품별 미래 판매량을 예측하는 "
            "프로젝트이다."
        ),
        "technologies": [
            "Python",
            "Pandas",
            "scikit-learn",
        ],
    },

    {
        "name": "DocuMind",
        "department": "AI개발팀",
        "description": (
            "사내 문서를 검색하고 관련 근거를 찾아 "
            "사용자의 질문에 답하는 "
            "문서 지식 검색 프로젝트이다."
        ),
        "technologies": [
            "LangChain",
            "ChromaDB",
            "Python",
        ],
    },

    {
        "name": "ChatSupport",
        "department": "서비스기획팀",
        "description": (
            "고객 문의 내용을 분석하고 관련 정보를 "
            "찾아 상담 답변 작성을 지원하는 "
            "AI 상담 프로젝트이다."
        ),
        "technologies": [
            "LangChain",
            "LangGraph",
            "ChromaDB",
        ],
    },

    {
        "name": "DataHub",
        "department": "플랫폼개발팀",
        "description": (
            "여러 업무 시스템의 데이터를 수집하여 "
            "통합 API와 데이터 서비스를 제공하는 "
            "플랫폼 프로젝트이다."
        ),
        "technologies": [
            "FastAPI",
            "PostgreSQL",
            "Docker",
        ],
    },

    {
        "name": "QualityAI",
        "department": "품질관리팀",
        "description": (
            "생산 품질 데이터를 분석하여 "
            "불량 발생 패턴과 주요 원인을 "
            "찾는 품질 분석 프로젝트이다."
        ),
        "technologies": [
            "PyTorch",
            "Pandas",
            "Python",
        ],
    },

    {
        "name": "CloudMonitor",
        "department": "클라우드운영팀",
        "description": (
            "서버와 애플리케이션 상태를 수집하여 "
            "장애 징후와 자원 사용 이상을 "
            "탐지하는 운영 프로젝트이다."
        ),
        "technologies": [
            "Docker",
            "FastAPI",
            "PostgreSQL",
        ],
    },

    {
        "name": "ProjectFlow",
        "department": "서비스기획팀",
        "description": (
            "업무 진행 상태와 승인 절차를 관리하고 "
            "반복 작업을 자동화하기 위한 "
            "업무 흐름 관리 프로젝트이다."
        ),
        "technologies": [
            "LangGraph",
            "FastAPI",
            "Python",
        ],
    },

]


# ============================================================
# 4. 직원 데이터
# ============================================================
#
# primary_skill은 Knowledge Graph에서
#
# Person -- USES --> Technology
#
# 관계를 만들 때 사용한다.
#
# ============================================================

employees = [

    {
        "name": "김철수",
        "department": "AI개발팀",
        "projects": [
            "VisionGuard",
            "DocuMind",
        ],
        "primary_skill": "PyTorch",
        "role": "컴퓨터 비전 모델 개발",
    },

    {
        "name": "이영희",
        "department": "데이터분석팀",
        "projects": [
            "CustomerInsight",
            "SalesForecast",
        ],
        "primary_skill": "Pandas",
        "role": "고객 및 매출 데이터 분석",
    },

    {
        "name": "박민수",
        "department": "품질관리팀",
        "projects": [
            "QualityAI",
            "SmartFactory",
        ],
        "primary_skill": "Python",
        "role": "생산 품질 데이터 분석",
    },

    {
        "name": "최지은",
        "department": "데이터분석팀",
        "projects": [
            "CustomerInsight",
        ],
        "primary_skill": "ChromaDB",
        "role": "고객 정보 검색 및 분석",
    },

    {
        "name": "정현우",
        "department": "플랫폼개발팀",
        "projects": [
            "DataHub",
        ],
        "primary_skill": "FastAPI",
        "role": "데이터 API 개발",
    },

    {
        "name": "한서연",
        "department": "AI개발팀",
        "projects": [
            "DocuMind",
            "ChatSupport",
        ],
        "primary_skill": "LangChain",
        "role": "RAG 기반 질의응답 개발",
    },

    {
        "name": "윤도현",
        "department": "플랫폼개발팀",
        "projects": [
            "DataHub",
            "CloudMonitor",
        ],
        "primary_skill": "Docker",
        "role": "데이터 플랫폼 배포 및 운영",
    },

    {
        "name": "오유진",
        "department": "서비스기획팀",
        "projects": [
            "ChatSupport",
            "ProjectFlow",
        ],
        "primary_skill": "LangGraph",
        "role": "AI 업무 흐름 설계",
    },

    {
        "name": "강민재",
        "department": "품질관리팀",
        "projects": [
            "VisionGuard",
            "QualityAI",
        ],
        "primary_skill": "OpenCV",
        "role": "이미지 품질 검사",
    },

    {
        "name": "신하늘",
        "department": "클라우드운영팀",
        "projects": [
            "CloudMonitor",
        ],
        "primary_skill": "FastAPI",
        "role": "서비스 상태 모니터링",
    },

    {
        "name": "장우석",
        "department": "클라우드운영팀",
        "projects": [
            "CloudMonitor",
            "DataHub",
        ],
        "primary_skill": "PostgreSQL",
        "role": "운영 데이터베이스 관리",
    },

    {
        "name": "임수빈",
        "department": "서비스기획팀",
        "projects": [
            "ProjectFlow",
            "ChatSupport",
        ],
        "primary_skill": "LangGraph",
        "role": "서비스 프로세스 자동화",
    },

    {
        "name": "서지훈",
        "department": "AI개발팀",
        "projects": [
            "VisionGuard",
        ],
        "primary_skill": "NumPy",
        "role": "영상 데이터 전처리",
    },

    {
        "name": "배하린",
        "department": "데이터분석팀",
        "projects": [
            "SalesForecast",
        ],
        "primary_skill": "scikit-learn",
        "role": "판매량 예측 모델 개발",
    },

    {
        "name": "문태경",
        "department": "품질관리팀",
        "projects": [
            "SmartFactory",
        ],
        "primary_skill": "PostgreSQL",
        "role": "생산 데이터 관리",
    },

]


# ============================================================
# 5. 기술 Entity
# ============================================================

technologies = [

    "Python",
    "Pandas",
    "PyTorch",
    "FastAPI",
    "LangChain",
    "LangGraph",
    "ChromaDB",
    "PostgreSQL",
    "Docker",
    "OpenCV",
    "scikit-learn",
    "NumPy",

]


# ============================================================
# 6. 지역 Entity
# ============================================================

locations = [

    "서울",
    "판교",
    "부산",
    "대전",
    "인천",

]


# ============================================================
# 7. Document 저장 리스트
# ============================================================

documents = []


# ============================================================
# 8. Document 추가 함수
# ============================================================

def add_document(
    category: str,
    title: str,
    text: str,
) -> str:

    # --------------------------------------------------------
    # 현재 문서 수를 이용하여
    # DOC-001 형태의 ID 생성
    # --------------------------------------------------------

    document_number = (
        len(documents)
        + 1
    )


    doc_id = (
        f"DOC-"
        f"{document_number:03d}"
    )


    documents.append(

        {
            "doc_id":
                doc_id,

            "category":
                category,

            "title":
                title,

            "text":
                text,
        }
    )


    return doc_id


# ============================================================
# 9. Graph Node 저장
# ============================================================

nodes = {}


# ============================================================
# 10. Node 추가 함수
# ============================================================

def add_node(
    node_id: str,
    node_type: str,
):

    if node_id not in nodes:

        nodes[
            node_id
        ] = {

            "id":
                node_id,

            "type":
                node_type,

            "source_documents":
                [],
        }


# ============================================================
# 11. Relation 저장
# ============================================================

relations = []


# ============================================================
# 12. Relation 추가 함수
# ============================================================

def add_relation(
    source: str,
    relation: str,
    target: str,
    source_document: str,
):

    relation_number = (
        len(relations)
        + 1
    )


    edge_id = (
        f"REL-"
        f"{relation_number:03d}"
    )


    relations.append(

        {
            "edge_id":
                edge_id,

            "source":
                source,

            "relation":
                relation,

            "target":
                target,

            "source_document":
                source_document,
        }
    )


    # --------------------------------------------------------
    # 해당 문서를 Node의 provenance에도 저장
    # --------------------------------------------------------

    for node_id in [
        source,
        target,
    ]:

        if (
            source_document
            not in nodes[
                node_id
            ][
                "source_documents"
            ]
        ):

            nodes[
                node_id
            ][
                "source_documents"
            ].append(
                source_document
            )


# ============================================================
# 13. 기본 Entity Node 생성
# ============================================================

for employee in employees:

    add_node(
        employee["name"],
        "Person",
    )


for department in departments:

    add_node(
        department["name"],
        "Department",
    )


for project in projects:

    add_node(
        project["name"],
        "Project",
    )


for technology in technologies:

    add_node(
        technology,
        "Technology",
    )


for location in locations:

    add_node(
        location,
        "Location",
    )


# ============================================================
# 14. 직원 Profile Document
# ============================================================
#
# 15개 생성
#
# 여기서:
#
# Person -- WORKS_IN --> Department
#
# Person -- PARTICIPATES_IN --> Project
#
# 관계를 만든다.
#
# ============================================================

for employee in employees:

    project_text = (
        ", ".join(
            employee[
                "projects"
            ]
        )
    )


    text = (

        f"{employee['name']}은(는) "
        f"{employee['department']} 소속으로 "

        f"{project_text} 프로젝트에 "
        f"참여하고 있다. "

        f"주요 담당 업무는 "
        f"{employee['role']}이다."
    )


    doc_id = add_document(

        category="employee_profile",

        title=(
            f"{employee['name']} "
            f"직원 정보"
        ),

        text=text,
    )


    # --------------------------------------------------------
    # 직원 → 부서
    # --------------------------------------------------------

    add_relation(

        employee["name"],

        "WORKS_IN",

        employee["department"],

        doc_id,
    )


    # --------------------------------------------------------
    # 직원 → 프로젝트
    # --------------------------------------------------------

    for project_name in (
        employee["projects"]
    ):

        add_relation(

            employee["name"],

            "PARTICIPATES_IN",

            project_name,

            doc_id,
        )


# ============================================================
# 15. 직원 기술 Document
# ============================================================
#
# 15개
#
# Person -- USES --> Technology
#
# ============================================================

for employee in employees:

    text = (

        f"{employee['name']}은(는) "
        f"{employee['role']} 업무에서 "

        f"{employee['primary_skill']} 기술을 "
        f"주요 도구로 사용한다."
    )


    doc_id = add_document(

        category="employee_skill",

        title=(
            f"{employee['name']} "
            f"주요 기술"
        ),

        text=text,
    )


    add_relation(

        employee["name"],

        "USES",

        employee[
            "primary_skill"
        ],

        doc_id,
    )


# ============================================================
# 16. 프로젝트 설명 Document
# ============================================================
#
# 10개
#
# Project -- BELONGS_TO --> Department
#
# ============================================================

for project in projects:

    text = (

        f"{project['name']}는 "
        f"{project['description']} "

        f"이 프로젝트는 "
        f"{project['department']}에서 "
        f"주관한다."
    )


    doc_id = add_document(

        category="project",

        title=(
            f"{project['name']} "
            f"프로젝트 소개"
        ),

        text=text,
    )


    add_relation(

        project["name"],

        "BELONGS_TO",

        project[
            "department"
        ],

        doc_id,
    )


# ============================================================
# 17. 프로젝트 기술 Document
# ============================================================
#
# 10개
#
# 각 프로젝트 기술 3개
#
# Project -- USES --> Technology
#
# 총 Relation 30개
#
# ============================================================

for project in projects:

    technology_text = (
        ", ".join(
            project[
                "technologies"
            ]
        )
    )


    text = (

        f"{project['name']} 프로젝트에서는 "

        f"{technology_text}를 "
        f"주요 기술로 사용한다. "

        f"각 기술은 프로젝트의 "
        f"데이터 처리, 모델 개발 또는 "
        f"서비스 구현에 활용된다."
    )


    doc_id = add_document(

        category="project_technology",

        title=(
            f"{project['name']} "
            f"사용 기술"
        ),

        text=text,
    )


    for technology in (
        project["technologies"]
    ):

        add_relation(

            project["name"],

            "USES",

            technology,

            doc_id,
        )


# ============================================================
# 18. 부서 Document
# ============================================================
#
# 6개
#
# Department -- LOCATED_IN --> Location
#
# ============================================================

for department in departments:

    text = (

        f"{department['name']}은(는) "
        f"{department['location']}에서 근무한다. "

        f"주요 업무는 "
        f"{department['description']}"
    )


    doc_id = add_document(

        category="department",

        title=(
            f"{department['name']} "
            f"부서 정보"
        ),

        text=text,
    )


    add_relation(

        department["name"],

        "LOCATED_IN",

        department[
            "location"
        ],

        doc_id,
    )


# ============================================================
# 여기까지 Document 수
#
# 직원 Profile        15
# 직원 Skill          15
# 프로젝트 설명       10
# 프로젝트 기술       10
# 부서                 6
#
# 합계                56
# ============================================================


# ============================================================
# 19. Vector Search 연습용 추가 Document
# ============================================================
#
# 14개
#
# 이 문서들은 Knowledge Graph Relation을
# 직접 만들지 않는다.
#
# 이유:
#
# Vector Search를 했을 때
# 관련 문서뿐 아니라 비슷한 내용을 가진
# 다른 문서도 검색되도록 하기 위함이다.
#
# 즉 검색 난이도를 조금 높이는 데이터이다.
#
# ============================================================

supplemental_documents = [

    {
        "title": "이미지 품질 검사 업무",
        "text": (
            "제조 현장에서는 제품 이미지를 이용해 "
            "스크래치, 균열, 오염과 같은 외관 불량을 "
            "자동으로 확인하는 기술이 활용된다. "
            "OpenCV와 딥러닝 모델을 함께 사용할 수 있다."
        ),
    },

    {
        "title": "생산 데이터 품질 분석",
        "text": (
            "생산 품질 분석에서는 공정별 측정값과 "
            "불량 기록을 비교해 이상 패턴과 "
            "불량 발생 원인을 조사한다."
        ),
    },

    {
        "title": "고객 행동 데이터 분석",
        "text": (
            "고객의 구매 이력과 서비스 이용 기록을 "
            "분석하면 고객 관심 분야와 구매 패턴을 "
            "파악하는 데 도움이 된다."
        ),
    },

    {
        "title": "문서 검색 자동화",
        "text": (
            "많은 사내 문서에서 필요한 내용을 찾기 위해 "
            "문서를 벡터로 변환하고 의미적으로 가까운 "
            "자료를 검색하는 방식을 사용할 수 있다."
        ),
    },

    {
        "title": "서버 장애 감시",
        "text": (
            "운영 시스템에서는 CPU, 메모리, API 응답 시간과 "
            "오류 로그를 지속적으로 확인하여 "
            "장애 가능성을 조기에 발견한다."
        ),
    },

    {
        "title": "API 서비스 개발",
        "text": (
            "데이터와 AI 모델을 다른 시스템에서 "
            "사용할 수 있도록 REST API 형태로 "
            "서비스를 제공할 수 있다."
        ),
    },

    {
        "title": "판매 예측 업무",
        "text": (
            "과거 판매량과 계절성, 프로모션 정보를 분석하면 "
            "앞으로 필요한 상품 수량과 예상 매출을 "
            "추정하는 데 활용할 수 있다."
        ),
    },

    {
        "title": "업무 프로세스 자동화",
        "text": (
            "승인, 검토, 알림처럼 반복되는 업무 단계를 "
            "워크플로우 형태로 구성하면 "
            "업무 처리 과정을 자동화할 수 있다."
        ),
    },

    {
        "title": "데이터 플랫폼 운영",
        "text": (
            "여러 시스템의 데이터를 하나의 플랫폼에서 "
            "수집하고 관리하면 분석 시스템과 "
            "서비스에서 데이터를 재사용하기 쉽다."
        ),
    },

    {
        "title": "RAG 시스템 개요",
        "text": (
            "RAG 시스템은 사용자의 질문과 관련된 "
            "외부 자료를 먼저 검색한 뒤 "
            "검색 결과를 LLM에 전달하여 답변을 생성한다."
        ),
    },

    {
        "title": "VectorDB 활용",
        "text": (
            "VectorDB는 텍스트의 의미를 나타내는 "
            "Embedding Vector를 저장하고 "
            "질문과 유사한 문서를 검색하는 데 사용한다."
        ),
    },

    {
        "title": "Knowledge Graph 활용",
        "text": (
            "Knowledge Graph는 사람, 프로젝트, 기술과 같은 "
            "Entity 사이의 관계를 Graph 형태로 표현하여 "
            "연결된 정보를 탐색하는 데 활용한다."
        ),
    },

    {
        "title": "클라우드 서비스 운영",
        "text": (
            "컨테이너 기반 서비스를 안정적으로 운영하려면 "
            "배포 환경과 데이터베이스 상태, "
            "서비스 로그를 함께 관리해야 한다."
        ),
    },

    {
        "title": "AI 프로젝트 기술 선택",
        "text": (
            "AI 프로젝트에서는 데이터 종류와 서비스 목적에 따라 "
            "Python, PyTorch, Pandas, FastAPI 등의 "
            "기술을 조합하여 사용할 수 있다."
        ),
    },

]


for item in supplemental_documents:

    add_document(

        category="supplement",

        title=item[
            "title"
        ],

        text=item[
            "text"
        ],
    )


# ============================================================
# 20. Node Dictionary → List
# ============================================================

node_list = list(
    nodes.values()
)


# ============================================================
# 21. Knowledge Graph 최종 구조
# ============================================================

knowledge_graph = {

    "nodes":
        node_list,

    "relations":
        relations,
}


# ============================================================
# 22. 데이터 검증
# ============================================================

print("=" * 70)
print("데이터 검증")
print("=" * 70)


print(
    "Document 수:",
    len(documents)
)


print(
    "Node 수:",
    len(node_list)
)


print(
    "Relation 수:",
    len(relations)
)


# ============================================================
# 목표 수 확인
# ============================================================

assert len(documents) == 70, (
    "Document 수가 70개가 아닙니다."
)


assert len(node_list) == 48, (
    "Node 수가 48개가 아닙니다."
)


assert len(relations) == 100, (
    "Relation 수가 100개가 아닙니다."
)


# ============================================================
# 23. Document ID 중복 검사
# ============================================================

document_ids = [

    document[
        "doc_id"
    ]

    for document
    in documents
]


assert (
    len(document_ids)
    ==
    len(set(document_ids))
), (
    "Document ID가 중복되었습니다."
)


# ============================================================
# 24. Relation ID 중복 검사
# ============================================================

relation_ids = [

    relation[
        "edge_id"
    ]

    for relation
    in relations
]


assert (
    len(relation_ids)
    ==
    len(set(relation_ids))
), (
    "Relation ID가 중복되었습니다."
)


# ============================================================
# 25. Relation의 Node 존재 검사
# ============================================================

node_ids = set(
    nodes.keys()
)


for relation in relations:

    assert (
        relation[
            "source"
        ]
        in node_ids
    )


    assert (
        relation[
            "target"
        ]
        in node_ids
    )


# ============================================================
# 26. source_document 존재 검사
# ============================================================

document_id_set = set(
    document_ids
)


for relation in relations:

    assert (
        relation[
            "source_document"
        ]
        in document_id_set
    )


# ============================================================
# 27. JSON 저장
# ============================================================

with open(
    DOCUMENT_PATH,
    "w",
    encoding="utf-8",
) as file:

    json.dump(

        documents,

        file,

        ensure_ascii=False,

        indent=4,
    )


with open(
    GRAPH_PATH,
    "w",
    encoding="utf-8",
) as file:

    json.dump(

        knowledge_graph,

        file,

        ensure_ascii=False,

        indent=4,
    )


# ============================================================
# 28. Document Category 확인
# ============================================================

category_counter = Counter(

    document[
        "category"
    ]

    for document
    in documents
)


# ============================================================
# 29. Relation 종류 확인
# ============================================================

relation_counter = Counter(

    relation[
        "relation"
    ]

    for relation
    in relations
)


# ============================================================
# 30. 결과 출력
# ============================================================

print("\n")
print("=" * 70)
print("Document Category")
print("=" * 70)


for (
    category,
    count,
) in category_counter.items():

    print(
        f"{category:20s}",
        count
    )


print("\n")
print("=" * 70)
print("Relation Type")
print("=" * 70)


for (
    relation,
    count,
) in relation_counter.items():

    print(
        f"{relation:20s}",
        count
    )


print("\n")
print("=" * 70)
print("파일 생성 완료")
print("=" * 70)


print(
    "documents.json:"
)


print(
    DOCUMENT_PATH
)


print()


print(
    "knowledge_graph.json:"
)


print(
    GRAPH_PATH
)