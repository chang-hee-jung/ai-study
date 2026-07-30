# 4주차 — 구조화된 출력: 말이 아니라 데이터 받기 (extract.py)

## 목표
- JSON 개념 (기계가 읽는 데이터 형식)
- `json.loads()` — 문자열을 파이썬 dict로
- 프롬프트로 JSON을 "부탁"하기 vs `format`으로 "강제"하기
- 뽑은 데이터를 코드로 다루기 (dict 접근, for 반복)

## 왜 필요한가 (체크포인트 미리보기)
2주차 할일 추출 결과는 사람 눈에는 좋았지만 자유 텍스트였다.
"할일 목록을 회사 메신저로 보내는 프로그램"을 만든다면? 텍스트에서 뭐가 할일이고
누가 담당인지 코드로 잘라내야 하는데, 모델이 매번 형식을 바꾸면 코드가 깨진다.
(심지어 "决定事项："처럼 언어도 바뀜) → 답을 처음부터 **데이터 구조**로 받으면 해결

## 최종 결과물
```powershell
.\venv\Scripts\python week04\extract.py week02\sample.txt
```
→ 회의록에서 {요약, 결정사항[], 할일[{내용, 담당}]}를 JSON으로 뽑아
할일을 체크리스트로 출력

## 단계별 진행

### 1단계: JSON을 "부탁"해보기 (그리고 배신당하기)
week02/summarize.py를 복사해 week04/extract.py로. 프롬프트만 교체:
```python
prompt = f"""다음 회의록에서 정보를 뽑아 JSON으로만 답해줘.
다른 말은 하지 말고 JSON만. 형식:
{{"summary": "한 줄 요약", "todos": [{{"task": "할 일", "owner": "담당자"}}]}}

회의록:
{text}"""
```
- f-string 안에서 중괄호를 문자로 쓰려면 `{{` `}}` 두 번 (f-string의 {}와 구분)
- 여러 번 실행해보기: 매번 깔끔한 JSON이 나오는가? 앞뒤에 딴소리나 ```json 같은 게 붙지 않는가?

### 2단계: 문자열 → 데이터 (json.loads)
```python
import json
data = json.loads(response.message.content)
print(data["summary"])
```
- `json.loads()` = JSON 문자열을 파이썬 dict(사전)로 변환
- dict는 `data["키"]`로 값을 꺼낸다
- 1단계에서 모델이 딴소리를 붙였다면 여기서 죽는다 → 그게 "부탁"의 한계

### 3단계: 강제하기 (format 파라미터)
chat()에 format을 주면 모델 출력 자체를 JSON 구조로 강제한다:
```python
response = chat(
    model="qwen2.5:7b",
    messages=[...],
    format={
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "todos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string"},
                        "owner": {"type": "string"}
                    },
                    "required": ["task", "owner"]
                }
            }
        },
        "required": ["summary", "todos"]
    },
)
```
- 이걸 JSON 스키마라고 부른다: "출력은 이 모양이어야 한다"는 설계도
- 프롬프트(부탁)와 달리 어기는 게 불가능 — 2주차 중국어 사태의 정식 해법

### 4단계: 데이터로 일하기
```python
print("요약:", data["summary"])
print("할 일:")
for todo in data["todos"]:
    print(f"  [ ] {todo['task']} (담당: {todo['owner']})")
```
- for로 목록을 돌며 체크리스트 출력 — 모델 출력이 "말"이 아니라 "데이터"가 된 순간

## 체크포인트
- 왜 자유 텍스트가 아니라 JSON으로 받아야 하는가?
- "부탁"(프롬프트)과 "강제"(format/스키마)의 차이는?
