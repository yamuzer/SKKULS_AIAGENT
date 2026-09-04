# SmartHRD AI Agent — 프로젝트 진행 현황 보고서 (Progress Log)

- **최종 업데이트:** 2026-09-04
- **현재 상태:** Phase 0 완료 / Phase 1 진행 준비
- **기준 문서:** `docs/SmartHRD_AI_Agent_PRD_v1.3.md`

---

## 1. 전체 마일스톤 현황

| Phase | 단계명 | 상태 | 완료일 | 핵심 산출물 및 주요 성과 |
| :---: | :--- | :---: | :---: | :--- |
| **Phase 0** | **Repository & Data Audit** | **완료** | 2026-09-04 | 원천 데이터 전수 프로파일링, 3대 감사/설계 문서 작성, NCS 마스터 추출 |
| **Phase 1** | Structured Data Foundation | 대기 (진행 예정) | - | PostgreSQL DDL/인덱스 구축, CSV 적재 파이프라인, 핵심 분석 함수 |
| **Phase 2** | Document Ingestion & Retrieval | 대기 | - | 공통 Document Schema 구현, 비정형 15종 문서 청킹 및 ChromaDB 적재 |
| **Phase 3** | LangChain RAG + LLM | 대기 | - | 규정 검색 체인, 조문/페이지 출처 인용 시스템 |
| **Phase 4** | LangChain Structured Analysis | 대기 | - | 정형 훈련시장 분석 쿼리 도구 및 수치 그라운딩 프롬프트 |
| **Phase 5** | LangGraph Integration | 대기 | - | Router, Market Node, RAG Node, Synthesis Node 통합 워크플로우 (혼합 질문 E2E) |
| **Phase 6** | Streamlit Productization | 대기 | - | 사용자 인터페이스(시장 분석 카드, AI 의견 탭, 규정 출처 뷰어) 구현 |
| **Phase 7** | Evaluation & Optimization | 대기 | - | 40개 평가 데이터셋 벤치마크, 라우팅/수치 정확도 측정 및 최적화 |

---

## 2. 상세 작업 내역 (Phase 0)

### 2.1 저장소 및 데이터 전수 프로파일링
- **정형 훈련과정 데이터 (`2101-2604_국민내일배움카드_훈련과정_목록_정제본.csv`):**
  - 원본 628,384행, 23개 컬럼 (321.87 MB)
  - `index` 컬럼 제거 후 순수 업무 중복 8,847건 검출 및 제거 $\rightarrow$ **최종 619,537건** 확정
  - 복합 기본키 `(trpr_id, trpr_degr)` 결측 0건, 중복 0건 (고유 과정 139,138개, 회차 619,537건)
  - `ncsCd` 컬럼의 `.0` 부동소수점 및 선행 0 탈락 현상 확인 $\rightarrow$ 8자리 `zfill(8)` 공식 정규화 규칙 확정 (비정상/미매칭 임의 변경 금지)
  - 취업률 성과 지표의 90% 결측치 확인 $\rightarrow$ 임의 0% 치환 금지 및 모수/커버리지 병기 정책 확정
  - 주말/주중 구분(`wkendSe`)의 미확인 코드 `9.0`(136,789건) 확인 $\rightarrow$ 공식 명세 미확인 코드로 원본 보존 ('기타/미지정' 확정 금지)
- **노동시장 구인분류표 (`산업별직종별_구인분류표.xlsx`):**
  - 2026년 7월 단월 데이터 및 상위 분류 셀 병합 구조 확인 $\rightarrow$ PRD 지침에 따라 **MVP 분석 제외, V2 확장 자산으로 보존**
- **비정형 문서 15종 (`data/unstructured/`):**
  - `직업능력심사평가원_FAQ.json` (58건): 1문 1답 단위 청킹 적합
  - `법령 위반사항_20251125.csv` (52건): **CP949 인코딩** 파싱 규칙 수립
  - 법령/시행령/규칙/고시 PDF 8종: 국가법령 조문(`제N조`) 중심 구조화 청킹 전략 수립
  - `고용24 API 목록 PDF`: 텍스트 스트림 대신 벡터 곡선(1,933개) 형태 확인 $\rightarrow$ 이미 `DATA_DICTIONARY.md`에 전수 반영 완료

### 2.2 NCS 마스터 데이터 추출 완료
- **원천 파일:** `data/structured/NCS정보망DB(대분류별,2022년3월).xlsx` (24개 시트, 190.8MB)
- **추출 스크립트:** [`pipeline/extract_ncs_master.py`](file:///c:/Users/SD2-21/Desktop/maeng/workspace/SKKULS_AIAGENT/15_MIniProject/pipeline/extract_ncs_master.py)
- **생성된 마스터:** [`data/structured/ncs_codes_master.csv`](file:///c:/Users/SD2-21/Desktop/maeng/workspace/SKKULS_AIAGENT/15_MIniProject/data/structured/ncs_codes_master.csv)
  - 8자리 세분류 코드 총 **1,083개** 추출 완료
  - 8개 계층 컬럼: `major_cd`, `major_nm`, `mid_cd`, `mid_nm`, `minor_cd`, `minor_nm`, `detail_cd`, `detail_nm`
- **매칭률 검증 결과:** 정제본 훈련과정 데이터(619,537건)와 대조 시 **96.31% (596,177건) 정상 매칭** 확인 (미매칭 3.69%는 Soft FK 및 Left Join 처리)

### 2.3 NCS 매칭률 공식 검증 완료 (SPEC v1.1 3.5절 충족)
- **검증 스크립트:** [`pipeline/validate_ncs_matching.py`](file:///c:/Users/SD2-21/Desktop/maeng/workspace/SKKULS_AIAGENT/15_MIniProject/pipeline/validate_ncs_matching.py)
- **공식 보고서:** [`docs/NCS_MATCHING_REPORT.md`](file:///c:/Users/SD2-21/Desktop/maeng/workspace/SKKULS_AIAGENT/15_MIniProject/docs/NCS_MATCHING_REPORT.md)
- **실측 매칭 지표 (정제본 619,537건 기준):**
  - 전체 회차: 619,537건
  - 유효 NCS 회차: 619,029건 (결측 508건)
  - 고유 코드 수: 584개
  - 정상 매칭 회차 수: **596,177건 (96.31%)**
  - 미매칭 회차 수: 22,852건 (3.69%)
  - 정상 매칭 고유 코드 수: **528개 (90.41%)**
  - 미매칭 고유 코드 수: 56개 (9.59%)
  - 선행 0 복원 미적용 시 50.91%로 급락하는 현상 실측 및 표준 8자리 복원 근거 확립

### 2.4 작성 완료된 설계 및 감사 문서
1. [`docs/DATA_AUDIT.md`](file:///c:/Users/SD2-21/Desktop/maeng/workspace/SKKULS_AIAGENT/15_MIniProject/docs/DATA_AUDIT.md): 데이터 전수 감사 보고서
2. [`docs/DATABASE_DESIGN.md`](file:///c:/Users/SD2-21/Desktop/maeng/workspace/SKKULS_AIAGENT/15_MIniProject/docs/DATABASE_DESIGN.md): PostgreSQL DDL, 인덱스, 지표 SQL, ETL 설계서
3. [`docs/IMPLEMENTATION_PLAN.md`](file:///c:/Users/SD2-21/Desktop/maeng/workspace/SKKULS_AIAGENT/15_MIniProject/docs/IMPLEMENTATION_PLAN.md): 단계별 구현 계획 및 게이트 체크리스트
4. [`docs/PHASE1_VALIDATION_SPEC_v1.1.md`](file:///c:/Users/SD2-21/Desktop/maeng/workspace/SKKULS_AIAGENT/15_MIniProject/docs/PHASE1_VALIDATION_SPEC_v1.1.md): 데이터 품질 규칙 및 SQL 테스트셋 명세서
5. [`docs/NCS_MATCHING_REPORT.md`](file:///c:/Users/SD2-21/Desktop/maeng/workspace/SKKULS_AIAGENT/15_MIniProject/docs/NCS_MATCHING_REPORT.md): NCS 매칭률 9대 지표 실측 검증 보고서

---

## 3. 다음 작업 (Phase 1 착수 예정 항목)

1. **DB 환경 설정:** PostgreSQL 연결 모듈 (`database/connection.py`) 구축
2. **테이블 생성:** `database/schema.sql` 기반 `training_courses` 및 `ncs_codes` 테이블 생성
3. **훈련과정 적재 파이프라인:** CSV 정제 및 Bulk Insert 파이프라인 (`pipeline/load_training_courses.py`) 작성 및 실행 (619,537건)
4. **분석 쿼리 함수 구현:** `database/queries.py` (T01~T10 표준 분석 함수 및 Coverage 병기 로직)
5. **정량 데이터 검증:** `tests/test_phase1_validation.py`를 통한 DQ 검증 및 Reference Reconciliation 확인
