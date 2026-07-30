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
- [ ] 7주차 — 임베딩 + chromadb
- [ ] 8주차 — 문서 인덱싱 + 청킹
- [ ] 9주차 — 마일스톤 2: 문서 QA 봇 (+ 프라이버시 결정)

## 4단계: 서비스화
- [ ] 10주차 — FastAPI
- [ ] 11주차 — 웹 UI
- [ ] 12주차 — 마일스톤 3: 사내 서버 배포
