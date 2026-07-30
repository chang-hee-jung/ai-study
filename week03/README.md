# 3주차 — 기억하는 챗봇 (chatbot.py)

## 목표
- 반복 루프 (while, input, break)
- 목록에 쌓기 (list, append)
- **stateless 개념**: API는 기억이 없다 — 대화 이력을 매번 전부 다시 보낸다
- 스트리밍 출력 (한 글자씩 실시간 표시)

## 최종 결과물
```powershell
.\venv\Scripts\python week03\chatbot.py
```
→ `ollama run`처럼 대화가 이어지는 챗봇. 단, 내가 만든 것

## 단계별 진행

### 1단계: 대화 루프 (모델 없이)
계속 입력을 받다가 /bye 치면 끝나는 뼈대:
```python
while True:
    user_input = input("나: ")
    if user_input == "/bye":
        break
    print("(입력받음:", user_input, ")")
```
- `while True:` = 무한 반복 (콜론 규칙: 안쪽은 들여쓰기)
- `input("나: ")` = 사용자가 엔터 칠 때까지 기다렸다가 그 내용을 돌려줌
- `break` = 반복 탈출

### 2단계: 모델 연결 (기억 없음 버전)
print 자리에 chat 호출을 넣는다. 매번 그 한 마디만 보내는 버전.
실험: "내 이름은 창희야" → 다음 턴에 "내 이름 뭐게?" — 기억하는가?

### 3단계: 대화 이력 쌓기 (기억 만들기)
```python
history = []                                        # 루프 밖에서 빈 목록
history.append({"role": "user", "content": user_input})     # 내 말 추가
response = chat(model="qwen2.5:7b", messages=history)       # 지금까지 전부 보냄
history.append({"role": "assistant", "content": response.message.content})  # 답도 추가
```
- 핵심: messages에 이번 한 마디가 아니라 **history 전체**를 보낸다
- 같은 실험 반복: 이름을 기억하는가?

### 4단계: 스트리밍
```python
stream = chat(model="qwen2.5:7b", messages=history, stream=True)
answer = ""
for part in stream:
    print(part.message.content, end="", flush=True)
    answer = answer + part.message.content
print()
history.append({"role": "assistant", "content": answer})
```
- `stream=True` = 답을 다 만들 때까지 기다리지 않고 조각조각 받음
- `end=""` = print가 줄바꿈 안 하게, `flush=True` = 즉시 화면에

## 체크포인트
- "API는 stateless다"란 무슨 뜻인가?
- 대화가 길어지면 왜 토큰(비용)이 눈덩이처럼 커지는가?
