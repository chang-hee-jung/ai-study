# 진행 상태

> 주차 완료 시 체크. 새 세션에서 Claude가 이 파일을 읽고 이어간다.

## 1단계: 파이썬 근육 + 첫 API 호출
- [ ] 1주차 — 환경 세팅 + hello.py
  - [x] venv 생성, anthropic·google-genai 설치 (2026-07-30)
  - [x] 교재 결정: Gemini 검토 후 **Ollama 로컬 모델로 최종 결정** (2026-07-30)
  - [x] Ollama v0.32.5 설치 + qwen2.5:7b 다운로드 + pip install ollama (2026-07-30)
  - [ ] 과제 1: `ollama run qwen2.5:7b`로 터미널 대화 체험
  - [ ] 과제 2: hello.py 작성 및 실행 성공
  - [ ] 과제 3(확장): response 전체 출력, eval_count 찾기
- [ ] 2주차 — 문서 요약 CLI (summarize.py)

## 2단계: LLM 앱 핵심 패턴
- [ ] 3주차 — 멀티턴 챗봇 + 스트리밍
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
- [ ] 12주차 — 마일스톤 3: .172 서버 사내 배포
