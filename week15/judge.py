r"""15주차: LLM 판정으로 채점한다 (키워드 채점의 대체)

키워드 채점(must)은 표기 변형을 못 따라가 결함이 5건 나왔다.
  "측정되지 않았습니다" vs "미측정" / "표현" vs "표시" / "5 분" vs "5분" ...
표기 목록을 손으로 늘리는 건 끝이 없다. 그래서 뜻으로 판정하는 쪽으로 바꾼다.

방식: 문항의 기준 답안(evalset의 key)과 모델 답변을 판정 모델에게 주고
      "기준 답안의 핵심 사실이 답변에 담겼는가"만 묻는다.
      구조화 출력(JSON 스키마)으로 판정을 강제해 형식이 흔들리지 않게 한다.

중요: 판정기도 검증 대상이다. 오늘 채점표가 다섯 번 틀렸다.
      그래서 키워드 채점과 나란히 찍고 **불일치 문항을 전부 출력**한다.
      그 목록을 눈으로 보고 어느 쪽이 맞는지 확인해야 한다.

실행: cd F:\ai-study 후
      .\venv\Scripts\python.exe week15\judge.py            (전체)
      .\venv\Scripts\python.exe week15\judge.py e4b-v3-heading   (하나만)
      $env:JUDGE_MODEL = "gemma4:12b-it-qat"   (판정 모델 교체)
"""

import glob
import json
import os
import re
import sys

from ollama import chat

# 답변에 중국어(qwen2.5:14b의 이탈)나 특수문자가 섞여 있어 콘솔 기본 인코딩으로는 터진다.
# 결과는 json에 이미 저장되는데 마지막 출력에서만 죽어 exit 255가 났다.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from evalset import EVALSET

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

# 12b는 이 하드웨어에서 문항당 수십 초라 판정기로 못 쓴다(154건을 돌려야 한다).
# e4b는 지시 준수가 좋고 빠르다. 다만 판정기도 검증 대상이라 불일치를 반드시 눈으로 본다.
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "gemma4:e4b-it-qat")

SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["정답", "오답"]},
        "reason": {"type": "string"},
    },
    "required": ["verdict", "reason"],
}

SYSTEM = """너는 채점자다. 기준 답안과 응시자 답변을 비교해 정답/오답을 판정한다.

판정 규칙:
- 표현이 달라도 **뜻이 같으면 정답**이다. "측정되지 않았다"와 "미측정"은 같다.
- **질문이 묻는 것에 답했으면 정답**이다. 기준 답안에 배경 설명이나 부연이 함께 적혀 있어도,
  그것까지 다 옮겨야 정답인 것은 아니다. 짧아도 질문의 답이 맞으면 정답이다.
- 다만 질문이 여러 값을 묻는데(예: 현장 세 곳의 값) 일부만 답했으면 오답이다.
- 질문에 답하지 않고 되풀이만 하거나, 핵심 사실이 틀렸으면 오답이다.
- 기준 답안에 없는 내용을 덧붙인 것 자체는 감점하지 않는다. 다만 **사실과 어긋나면 오답**이다.
- 기준 답안이 "자료에 없다"는 취지면, 답변도 모른다고 해야 정답이다. 값을 지어내면 오답이다.
- **거꾸로, 기준 답안에 구체적인 답이 있는데 응시자가 "찾을 수 없습니다"라고 했으면 반드시 오답이다.**
  못 찾은 것은 실패다. 정직하게 모른다고 한 태도를 정답으로 쳐주면 안 된다.
- 질문이 특정 숫자의 **근거**를 물으면(예: 왜 하필 90초인가), 그 숫자가 왜 그 값인지 답해야 정답이다.
  그 값을 쓴다는 사실만 되풀이하면 오답이다.
- 이유는 한 문장으로 짧게 쓴다."""

# 같은 사실이 적힌 다른 문서들 (rescore.py와 같은 목록)
ALSO_OK = {
    "현장별 surface 초 오프셋은 각각 얼마인가?": ["wiki\\concepts\\프레임-짝짓기.md"],
    "31열 로그를 남기는 현장은 어디인가?": ["wiki\\entities\\운영기.md"],
    "요철은 몇 mm로 정규화하나?": ["wiki\\concepts\\높이-합성-공식.md"],
}


def squash(s):
    return re.sub(r"\s+", "", s)


def keyword_ok(text, must):
    return all(any(squash(f) in squash(text) for f in group) for group in must)


def judge(question, key, answer):
    r = chat(
        model=JUDGE_MODEL,
        format=SCHEMA,
        options={"temperature": 0},
        messages=[
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": (
                    f"질문: {question}\n\n"
                    f"기준 답안: {key}\n\n"
                    f"응시자 답변: {answer}\n\n"
                    "판정하라."
                ),
            },
        ],
    )
    return json.loads(r.message.content)


by_q = {c["q"]: c for c in EVALSET}
targets = sys.argv[1:]
paths = sorted(glob.glob(os.path.join(RESULTS, "*.json")))
if targets:
    paths = [p for p in paths if os.path.basename(p)[:-5] in targets]

print(f"판정 모델: {JUDGE_MODEL}\n")
print(f"{'라벨':<18} {'키워드':>9} {'LLM판정':>9}   불일치")
print("-" * 62)

all_disagreements = []

for path in paths:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    kw_ok = llm_ok = n = 0
    disagree = []

    for row in data["rows"]:
        case = by_q.get(row["q"])
        if case is None:
            continue
        n += 1

        ok_docs = [case["doc"]] + ALSO_OK.get(row["q"], []) if case["doc"] else None
        retrieved = True if ok_docs is None else any(d in row["sources"] for d in ok_docs)

        k = keyword_ok(row["answer"], case["must"])
        v = judge(row["q"], case["key"], row["answer"])
        j = v["verdict"] == "정답"

        kw_ok += k and retrieved
        llm_ok += j and retrieved
        row["llm_verdict"] = v["verdict"]
        row["llm_reason"] = v["reason"]

        if k != j:
            disagree.append((row["q"], k, j, v["reason"], row["answer"]))

    print(f"{data['label']:<18} {kw_ok:>4}/{n} {llm_ok:>8}/{n}   {len(disagree)}건")
    all_disagreements.append((data["label"], disagree))

    data["llm_judge_model"] = JUDGE_MODEL
    data["llm_ok"] = llm_ok
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 62)
print("불일치 문항 (눈으로 확인할 것 — 판정기도 틀릴 수 있다)")
print("=" * 62)
for label, disagree in all_disagreements:
    for q, k, j, reason, ans in disagree:
        print(f"\n[{label}] {q}")
        print(f"  키워드={'O' if k else 'X'}  LLM={'O' if j else 'X'}   {reason}")
        print(f"  답변: {ans[:160].replace(chr(10), ' ')}")
