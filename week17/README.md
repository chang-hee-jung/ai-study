# 17주차 — 남이 만든 에이전트 (Hermes Agent)

12주차에 `agent.py`를 직접 만들었다. 이번 주는 **같은 것을 남이 만든 것**과 붙여본다.

목적은 프레임워크 사용법 익히기가 아니다. **내 코드에 없는 것을 찾아내는 것**이다.
구경만 하면 "좋네" 하고 끝난다. 하나를 훔쳐와서 내 agent.py에 심어야 실력이 된다.

## 상대는 누구인가

**Hermes Agent** — Nous Research가 만든 오픈소스 에이전트 프레임워크(MIT).

중요한 건 이거다. **모델이 안 들어있다.** 껍데기(하네스)만 주고 모델은 내가 꽂는다.
그래서 Ollama를 그대로 붙일 수 있다. 우리가 14~16주차에 쓰던 그 Ollama다.

이게 왜 중요하냐면, 지금까지 "에이전트를 만든다"고 할 때 우리가 실제로 만든 건
**모델이 아니라 하네스**였기 때문이다. `agent.py` 237줄 중 모델을 부르는 줄은
`chat(...)` 몇 줄뿐이고, 나머지는 전부 하네스다. 도구 루프, 승인 게이트, 검증,
메모리 — 그게 하네스다.

그러니 이번 비교는 **하네스 대 하네스**다. 공정한 시합이다.

## 순서

### 1단계 — 붙이기 전에 모델부터 검증한다

`tool_check.py`를 먼저 돌린다. Hermes는 도구 호출 위에 서 있는 물건이라,
모델이 도구 호출을 제대로 못 하면 아무리 좋은 하네스를 얹어도 안 돈다.

우리 모델 중 누가 도구 호출을 잘하는지 먼저 재둔다. 붙이고 나서 안 되면
하네스 문제인지 모델 문제인지 구분이 안 된다.

```
.\venv\Scripts\python week17\tool_check.py
```

### 2단계 — 설치하고 Ollama에 연결

설치는 직접 한다(아래 "설치" 항목). 그다음 같은 과제를 둘에게 시킨다.

12주차 testbed와 같은 상황을 만들어 놓고 "이 폴더 정리해줘"를 양쪽에 시킨다.
어느 쪽이 잘하냐보다 **어디서 갈리는지**를 본다.

### 3단계 — 해부

`~/.hermes/` 안을 열어본다. 여기가 이번 주의 핵심이다.

```
~/.hermes/
├── config.yaml      설정 (내 agent.py는 상수가 코드에 박혀 있다)
├── SOUL.md          에이전트 정체성 (내 SYSTEM 프롬프트에 해당)
├── memories/        지속 기억 (내 memory.json에 해당)
├── skills/          스스로 만든 스킬 (내 agent.py에는 없는 개념)
└── sessions/        대화 세션
```

각 폴더를 열어보고 **내 agent.py의 어느 부분에 해당하는지** 대조한다.
대응되는 게 없는 폴더가 곧 내가 놓친 것이다.

### 4단계 — 하나 훔쳐서 심는다

3단계에서 찾은 것 중 하나를 골라 `agent.py`에 넣는다.

내가 미리 찍어둔 후보는 **메모리 압축**이다. 지금 `save_memory()`는 대화 전체를
통째로 쌓는다. 오래 쓰면 memory.json이 계속 커지고, 결국 컨텍스트 창을 넘겨서
터진다. Hermes는 요약 + 검색으로 이걸 푼다.

다만 3단계에서 더 나은 후보를 찾으면 그걸로 바꿔도 된다.

## 설치

공식 설치 명령은 이렇다.

```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

**이 명령이 뭘 하는지 알고 실행해야 한다.** 인터넷에서 스크립트를 받아 그 자리에서
실행한다는 뜻이다. 내용을 먼저 보고 싶으면 이렇게 받아서 읽어본 뒤 실행한다.

```powershell
irm https://hermes-agent.nousresearch.com/install.ps1 -OutFile install.ps1
notepad install.ps1
```

설치 후 Ollama 연결은 `~/.hermes/config.yaml`에 이렇게 넣는다.

```yaml
providers:
  ollama:
    type: openai-compatible
    base_url: http://localhost:11434/v1
    api_key: ollama

model:
  provider: ollama
  default: qwen3:8b
```

`hermes setup --portal`은 Nous Portal 가입을 요구한다. **우리는 Ollama로 갈 거라
안 해도 된다.** 웹검색 같은 내장 도구를 쓰려면 그때 가서 정하면 된다.

## 주의

이 저장소는 **공개**다. `~/.hermes/` 안에는 대화 기록과 API 키가 쌓인다.
**그 폴더의 내용을 이 저장소에 복사해 넣지 말 것.** 관찰한 구조만 글로 적는다.

## 산출물

- `tool_check.py` — 모델별 도구 호출 능력 측정
- `NOTES.md` — 비교 결과와 배운 것 (실습 후 정리)
- `agent_v2.py` — 4단계에서 이식한 개선판
