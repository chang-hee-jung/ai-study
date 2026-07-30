# 1주차 배운 것 (Claude 정리)

- Ollama 설치, qwen2.5:7b / llama3.1:8b 두 모델 받아서 한국어·영어 비교 → 한국어는 Qwen 우세, 둘 다 사실관계는 틀림(김치찌개에 냉면/식초) = **환각(hallucination)**. 모델은 맞는 말이 아니라 그럴듯한 말을 만든다
- 파이썬은 **들여쓰기가 문법**이다. 첫 칸부터 시작, 괄호 안쪽만 들여쓴다 (IndentationError)
- .py 파일은 프로그램이 아니라 텍스트. **python이 실행해주는 것** (`.\venv\Scripts\python 파일`)
- **에러(traceback)는 맨 마지막 줄이 진짜 원인.** 파일명·줄번호·에러종류 세 가지를 먼저 본다
- 함수 인자는 쉼표로 구분한다 (SyntaxError: forgot a comma?)
- 메시지에는 role이 붙는다: 내가 보내면 `user`, 모델 답은 `assistant`. 대화 = 이 둘을 번갈아 쌓기
- 토큰 = 과금 단위. prompt_eval_count(입력) / eval_count(출력)를 각각 다른 단가로 계산. 입력은 싸고 출력은 비쌈. 호출당 푼돈이라도 서비스는 곱셈이라 커진다
- RTX 4060 기준 추론 속도 약 48토큰/초 (eval_duration으로 계산)
- venv는 절대경로가 박혀 있어 폴더 이동 시 재생성 필요
