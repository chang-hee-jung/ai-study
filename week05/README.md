# 5주차 — Tool Use: 말하는 기계에서 일하는 기계로 (toolbot.py)

## 목표
- **함수 정의** (def, return, 독스트링, 타입 힌트) — 파이썬의 큰 산 하나
- 모델의 한계 체험: 모델은 지금 시각도, 내 디스크도 모른다
- Tool Use 흐름: 모델은 함수를 실행하지 않는다. **실행해달라고 요청**할 뿐
- 요청 실행 → 결과 회신 → 최종 답변의 2왕복 구조

## 핵심 그림
```
사용자: "F 드라이브 얼마 남았어?"
  → 모델: "check_disk(drive='F') 실행해줘" (tool_calls 요청)
  → 내 코드: 진짜 실행 → "F: 전체 931GB, 남음 198GB"
  → 모델: (결과 받고) "F 드라이브는 198GB 남아 있습니다"
```
실행 권한은 항상 내 코드에 있다. 모델은 부탁만 한다 — 이게 안전의 핵심이자
AgentOS가 하는 일의 전부다.

## 단계별 진행

### 1단계: 함수 만들기 (모델 없이)
week05/toolbot.py — 도구 두 개를 정의하고 직접 호출:
```python
from datetime import datetime
import shutil

def get_current_time() -> str:
    """현재 날짜와 시간을 알려준다."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def check_disk(drive: str) -> str:
    """지정한 드라이브의 전체 용량과 남은 용량을 GB 단위로 알려준다. drive는 'C', 'F' 같은 드라이브 문자."""
    total, used, free = shutil.disk_usage(f"{drive}:\\")
    return f"{drive} 드라이브: 전체 {total // 2**30}GB, 남음 {free // 2**30}GB"

print(get_current_time())
print(check_disk("C"))
```
- `def 이름(입력) -> 반환형:` — 나만의 명령어 만들기. 콜론 규칙으로 몸통은 들여쓰기
- `return` — 함수가 돌려주는 값
- `"""독스트링"""` — 함수 설명. **모델이 이걸 읽고 언제 이 함수를 쓸지 판단한다** (그냥 주석이 아님!)
- 타입 힌트(`drive: str`)도 모델에게 전달되는 정보

### 2단계: 모델의 한계 체험
같은 파일 아래에 (print 두 줄은 지우고):
```python
from ollama import chat
response = chat(model="qwen2.5:7b",
                messages=[{"role": "user", "content": "지금 몇 시야?"}])
print(response.message.content)
```
- 모델이 뭐라고 하는지 관찰. 시각을 아는가? 지어내는가?

### 3단계: 도구 쥐여주기 — 요청 관찰
chat 호출에 tools를 추가하고, 답 대신 tool_calls를 출력:
```python
response = chat(model="qwen2.5:7b",
                messages=[{"role": "user", "content": "지금 몇 시야?"}],
                tools=[get_current_time, check_disk])
print("답변:", response.message.content)
print("도구 요청:", response.message.tool_calls)
```
- 모델이 함수를 실행했는가? 아니면 "실행해달라"는 요청만 왔는가?
- "F 드라이브 얼마 남았어?"로 바꿔서도 실행 — 인자(drive='F')를 채워 오는가?

### 4단계: 요청 실행하고 결과 돌려주기 (2왕복 완성)
```python
messages = [{"role": "user", "content": "F 드라이브 얼마 남았어?"}]
available = {"get_current_time": get_current_time, "check_disk": check_disk}

response = chat(model="qwen2.5:7b", messages=messages,
                tools=[get_current_time, check_disk])

if response.message.tool_calls:
    messages.append(response.message)              # 모델의 요청도 이력에
    for call in response.message.tool_calls:
        fn = available[call.function.name]         # 이름으로 함수 찾기
        result = fn(**call.function.arguments)     # 진짜 실행!
        messages.append({"role": "tool", "name": call.function.name, "content": result})
    final = chat(model="qwen2.5:7b", messages=messages)
    print(final.message.content)
else:
    print(response.message.content)
```
- `available` dict: 함수 이름표 → 함수 실체. 모델이 준 이름으로 실체를 찾는다
- `fn(**call.function.arguments)` — `**`는 dict를 함수 인자로 펼쳐 넣는 문법
  ({"drive": "F"} → drive="F")
- role="tool" — user, assistant, system에 이은 네 번째 역할: 도구 실행 결과

### 5단계(보너스): 미니 에이전트
3주차 chatbot.py의 while 루프에 4단계를 합치면 — 도구를 쓰는 대화형 봇.
시간이 되면 도전.

## 체크포인트
- 모델이 함수를 "실행한다"가 왜 틀린 말인가?
- 독스트링이 왜 중요한가?
