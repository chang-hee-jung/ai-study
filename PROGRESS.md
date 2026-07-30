# 진행 상태

> 주차 완료 시 체크. 새 세션에서 Claude가 이 파일을 읽고 이어간다.

## 1단계: 파이썬 근육 + 첫 API 호출
- [x] **1주차 완료 (2026-07-30)** — 환경 세팅 + hello.py
  - [x] venv 생성, 교재 결정(Ollama 로컬), qwen2.5:7b·llama3.1:8b 설치
  - [x] 과제 1: 터미널 대화 체험 + 두 모델 한국어 비교 (환각 현상 관찰)
  - [x] 과제 2: hello.py 작성·실행 성공 — IndentationError→404→SyntaxError 자력 해결
  - [x] 과제 3: response 해부 (eval_count, 토큰 비용 계산 퀴즈 통과)
  - [x] 배운 것: week01/NOTES.md (Claude 정리 — 사용자는 회고 작성보다 실습 선호)
- [x] **2주차 완료 (2026-07-30)** — 문서 요약 CLI (summarize.py)
  - [x] 1단계: 파일 읽기 (open, with, encoding)
  - [x] 2단계: f-string으로 프롬프트 조립 + 모델 요약
  - [x] 3단계: sys.argv로 파일명 인자 받기 (argv[0] 자기요약 사건 포함)
  - [x] 4단계: system 프롬프트로 중국어 섞임·숫자 유실·왜곡 해결, 프롬프트 교체로 할일 추출 변신
  - [x] 배운 것: week02/NOTES.md

## 2단계: LLM 앱 핵심 패턴
- [x] **3주차 완료 (2026-07-30)** — 멀티턴 챗봇 + 스트리밍 (chatbot.py)
  - [x] 1단계: while/input/break 대화 루프 (+대소문자 구분 발견)
  - [x] 2단계: 기억 없음 버전으로 stateless 체험 (이름 잊어버림)
  - [x] 3단계: history.append로 기억 구현 (이름 기억 성공) + 토큰 눈덩이 개념
  - [x] 4단계: stream=True 스트리밍 출력
  - [x] 배운 것: week03/NOTES.md
- [x] **4주차 완료 (2026-07-31)** — 구조화된 출력 (extract.py)
  - [x] 1단계: 프롬프트로 JSON 부탁 (f-string 중괄호 이스케이프)
  - [x] 2단계: json.loads로 dict 변환, 키 접근·체이닝
  - [x] 3단계: format=JSON 스키마로 출력 강제 (부탁→강제)
  - [x] 4단계: for 반복으로 할일 체크리스트 출력
  - [x] 배운 것: week04/NOTES.md
- [x] **5주차 완료 (2026-07-31)** — Tool Use (toolbot.py)
  - [x] 1단계: def/return/독스트링 — 함수 정의 첫 경험 (get_current_time, check_disk)
  - [x] 2단계: 도구 없는 모델의 한계 체험 ("시계를 확인할 수 없습니다")
  - [x] 3단계: tools 전달 → tool_calls 요청 관찰 (모델은 실행하지 않는다)
  - [x] 4단계: 요청 실행 + role="tool" 회신 → 실제 디스크 용량으로 답변 성공
  - [ ] 5단계(보너스): 챗봇 루프 통합 = 미니 에이전트 (선택)
  - [x] 배운 것: week05/NOTES.md
- [x] **6주차 완료 (2026-07-31)** — 마일스톤 1: 회의 전사 자동 보고서 (meeting_report.py)
  - [x] extract.py 재조립 + 전사 텍스트 대응
  - [x] 스키마에 decisions 직접 추가 (스스로 설계)
  - [x] "비서" 담당자 환각 → 프롬프트 규칙("미정")으로 해결
  - [x] open("w")로 md 보고서 파일 생성 — 숫자·날짜 보존 확인
  - [x] 배운 것: week06/NOTES.md / 실전: 다음 실제 회의 때 투입

## 3단계: RAG
- [x] **7주차 완료 (2026-08-01)** — 임베딩 + chromadb
  - [x] bge-m3로 문장→1024차원 벡터 확인
  - [x] chromadb collection에 문장 5개 저장, 의미 검색 성공 ("회사 카드"→"법인카드")
  - [x] 랭킹의 한계 관찰 (오답이 근소하게 이기는 사례) → top-k 넉넉히 + 모델 판별 원칙
  - [x] 거리 = 신뢰도 신호 발견
  - [x] 배운 것: week07/NOTES.md
- [x] **8주차 완료 (2026-08-01)** — 문서 인덱싱 + 청킹
  - [x] 문단 청킹 (split, 짧은 조각 필터) — 15조각 → 10조각
  - [x] PersistentClient로 인덱스 구축/검색 분리 (build_index.py / search.py)
  - [x] 검색 3전 3승: "비번"→"비밀번호" 준말 매칭까지 확인
  - [x] 배운 것: week08/NOTES.md
- [x] **9주차 완료 (2026-08-01)** — 마일스톤 2: 문서 QA 봇 (ask.py)
  - [x] 검색+생성 합체: 근거 조립 → "근거만으로 답하라" → 출처 표시
  - [x] 함정 질문 방어 확인 (RAG 헌법 + 직접 짠 거리 문지기 이중 방어)
  - [x] 추론 실패 → 프롬프트 지시로 해결 (RAG 품질 = 검색 × 추론력)
  - [x] 배운 것: week09/NOTES.md / 회사 실문서 투입은 4단계에서 결정

## 4단계: 에이전트화 (2026-08-01 개편 — 개인용·작업위임 목표로 확정)
- [x] **10주차 완료 (2026-08-02)** — 도구 쓰는 챗봇 (assistant.py)
  - [x] 루프+이력+도구 합체, 4종 시험 통과 (도구/인자/잡담 판단/이력 재활용)
  - [x] 도구 결과의 이력 재활용 확인 ("아까 얼마랬지?" 재실행 없이 답)
  - [x] list_files 도구 직접 추가 — 맥락으로 경로 추론까지 확인
  - [x] 배운 것: week10/NOTES.md
- [x] **11주차 완료 (2026-08-02)** — 내 비서: 6개 도구 (assistant2.py)
  - [x] search_rules 도구 = Agentic RAG (검색 여부를 에이전트가 판단)
  - [x] read_file로 회의록 요약이 대화 한 마디로
  - [x] 위험 도구(move_file) y/n 승인제 + 거부를 모델에 전달 → 우아한 포기 확인
  - [x] 배운 것: week11/NOTES.md
- [x] **12주차 완료 (2026-08-03)** — 마일스톤 3: 멀티스텝 에이전트 (agent.py)
  - [x] if→while: 도구 연쇄 루프 + MAX_ROUNDS + try/except
  - [x] 1차: 상한 미완성 → "보고≠실제, 검증 필수" / 2차: 중국어 인자 대참사 →
        도구 방어 설계 + 프롬프트 보강 / 3차: 3라운드 자연 종료 완주
  - [x] 배운 것: week12/NOTES.md
- (보류) 서비스화 트랙: FastAPI→웹UI→사내배포 — 실수요 생기면

---

# 🎓 12주 커리큘럼 완주 (2026-07-30 ~ 2026-08-03)
결과물: hello.py → summarize.py → chatbot.py → extract.py → toolbot.py →
meeting_report.py(M1) → 임베딩/인덱스 → ask.py(M2) → assistant.py → assistant2.py → agent.py(M3)
다음 후보: 도구 확장(서버 점검 비서 등), 큰 모델 비교, 서비스화 트랙 부활
