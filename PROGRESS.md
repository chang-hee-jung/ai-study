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
- [ ] 4주차 — 구조화된 출력 (JSON)
- [ ] 5주차 — 함수 호출 (Tool Use)
- [ ] 6주차 — 마일스톤 1: MeetingAssistant 요약+할일 자동 추출

## 3단계: RAG
- [ ] 7주차 — 임베딩 + chromadb
- [ ] 8주차 — 문서 인덱싱 + 청킹
- [ ] 9주차 — 마일스톤 2: 문서 QA 봇 (+ 프라이버시 결정)

## 4단계: 서비스화
- [ ] 10주차 — FastAPI
- [ ] 11주차 — 웹 UI
- [ ] 12주차 — 마일스톤 3: 사내 서버 배포
