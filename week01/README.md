# 1주차 — 환경 세팅과 첫 API 호출

## 목표
- venv, pip, 환경변수 개념 이해
- Gemini API로 첫 호출 성공
- 토큰과 비용 개념 이해

## 준비 (완료)
- [x] `C:\Users\s-n\ai-study` + venv (Python 3.14.3)
- [x] `pip install google-genai`

## 과제 1: API 키 발급
1. https://aistudio.google.com/apikey → API 키 만들기 (`AIza...`)
2. PowerShell: `setx GEMINI_API_KEY "키"`
3. 터미널 새로 열기 (setx는 새 터미널부터 적용)

## 과제 2: hello.py 작성 (빈칸 직접 채우기)

```python
from google import genai

# 클라이언트 생성 - GEMINI_API_KEY 환경변수를 자동으로 읽음
client = genai.Client()

# 모델에게 메시지 보내기
response = client.models.generate_content(
    model="___",       # 힌트: 무료 티어의 빠른 모델. "gemini-2.5-" 로 시작
    contents="___",    # 힌트: 모델에게 보낼 말
)

# 응답 출력
print(response.text)
```

실행:
```powershell
cd C:\Users\s-n\ai-study
.\venv\Scripts\python week01\hello.py
```

## 과제 3 (확장): 토큰 확인
- `print(response.usage_metadata)` 추가해서 입력/출력 토큰 수 확인
- 질문: 이 호출이 유료였다면 얼마였을까? (모델 단가 찾아서 직접 계산)

## 배운 것 메모
(주차 끝나면 NOTES.md에 기록)
