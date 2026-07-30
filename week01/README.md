# 1주차 — 환경 세팅과 첫 로컬 LLM 호출

## 목표
- venv, pip 개념 이해
- Ollama로 내 PC에서 모델 실행 + 파이썬으로 첫 호출
- 토큰 개념 이해

## 준비 (완료)
- [x] `C:\Users\s-n\ai-study` + venv (Python 3.14.3)
- [x] Ollama 설치 (v0.32.5), `pip install ollama`
- [x] 모델 다운로드: `qwen2.5:7b`

## 과제 1: 터미널에서 모델과 대화해보기

```powershell
ollama run qwen2.5:7b
```

- 아무 말이나 걸어보기. `/bye`로 종료
- 관찰: GPU(RTX 4060)로 도는지 작업관리자에서 확인해보기

## 과제 2: hello.py 작성 (빈칸 직접 채우기)

```python
from ollama import chat

# 내 PC의 Ollama 서버에 메시지 보내기
response = chat(
    model="___",       # 힌트: 우리가 받은 모델 이름 (태그까지)
    messages=[
        {"role": "___", "content": "___"}   # 힌트: 누가 보내는 메시지인가? user? assistant?
    ],
)

# 응답 출력
print(response.message.content)
```

실행:
```powershell
cd C:\Users\s-n\ai-study
.\venv\Scripts\python week01\hello.py
```

## 과제 3 (확장): 생각해볼 것
- `response`에는 content 말고 뭐가 더 들어있을까? `print(response)`로 전체를 출력해보고
  `eval_count`(출력 토큰 수)를 찾아보기
- 질문: 이걸 Gemini나 Claude API로 바꾸면 코드에서 뭐가 달라질까? (힌트: 거의 안 달라짐)

## 배운 것 메모
(주차 끝나면 NOTES.md에 기록)
