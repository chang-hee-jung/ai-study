# 2주차 — 문서 요약 CLI (summarize.py)

## 목표
- 파일 읽기 (open, encoding)
- 변수와 f-string으로 프롬프트 조립
- 명령 인자 받기 (sys.argv)
- 프롬프트 설계 실험 (시스템 프롬프트)

## 최종 결과물
```powershell
.\venv\Scripts\python week02\summarize.py week02\sample.txt
```
→ 파일 내용을 읽어서 요약을 출력하는 도구

## 단계별 진행 (한 번에 하나씩)

### 1단계: 파일 읽기
`week02\summarize.py` — 먼저 모델 없이, 파일을 읽어서 그대로 출력만:
```python
with open("week02/sample.txt", encoding="utf-8") as f:
    text = f.read()

print(text)
```
- `open(...)` = 파일 열기, `encoding="utf-8"` = 한글 깨짐 방지
- `with ... as f:` = 다 쓰면 자동으로 닫아주는 안전장치
- `f.read()` = 내용 전체를 문자열로 → `text` 변수에 저장

### 2단계: 읽은 내용을 모델에게 요약시키기
1단계의 `print(text)`를 지우고, 1주차 hello.py의 chat 호출을 붙인다.
프롬프트에 파일 내용을 넣는 법 (f-string):
```python
prompt = f"다음 글을 세 줄로 요약해줘:\n\n{text}"
```
- 문자열 앞의 `f` = 중괄호 `{}` 안에 변수를 끼워 넣을 수 있게 해줌
- `\n` = 줄바꿈 문자

### 3단계: 파일명을 인자로 받기
지금은 sample.txt가 코드에 박혀 있다(하드코딩). 실행할 때 받도록:
```python
import sys
filename = sys.argv[1]
```
- `sys.argv` = 실행 명령에서 프로그램 이름 뒤에 붙인 것들의 목록
- `sys.argv[1]` = 첫 번째 인자 (= 파일명)
- open()의 파일명 자리에 `filename` 변수를 넣으면 완성

### 4단계 (실험): 프롬프트 설계
같은 파일로 프롬프트만 바꿔가며 결과 비교:
- "세 줄로 요약해줘" vs "결정사항과 할 일만 뽑아줘" vs "보고서 형식으로 요약해줘"
- 시스템 프롬프트 추가해보기:
```python
messages=[
    {"role": "system", "content": "너는 회사 회의록을 정리하는 비서다. 항상 존댓말로, 개조식으로 답한다."},
    {"role": "user", "content": prompt}
]
```

## 체크포인트 (2주차 끝날 때 답할 수 있어야 함)
- 프롬프트(user)와 시스템 프롬프트(system)의 차이는?
- 하드코딩이 왜 나쁜가?
