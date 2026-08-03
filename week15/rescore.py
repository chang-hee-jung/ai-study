r"""15주차: 저장된 답변을 다시 채점한다 (모델 재실행 없이)

evaluate.py가 답변 원문을 json에 남기기 때문에, 채점 기준이 틀렸으면
모델을 다시 돌리지 않고 채점만 고쳐서 재계산할 수 있다.

고친 것:
  1) 공백 무시 매칭 - "5 분"과 "5분"을 같게 본다.
     qwen3.5는 숫자와 단위를 띄어 쓰는 습관이 있어 내용이 맞는데도 X로 잡혔다.
  2) 정답 문서 복수 허용 - 같은 사실이 여러 문서에 적힌 경우가 있다.
     예) 초 오프셋(:30/:54/:38)은 현장별-비교와 프레임-짝짓기 양쪽에 있다.

실행: .\venv\Scripts\python.exe week15\rescore.py
"""

import glob
import json
import os
import re

from evalset import EVALSET

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

# 같은 사실이 적힌 다른 문서들 (검색이 이쪽을 가져와도 정답으로 친다)
ALSO_OK = {
    "현장별 surface 초 오프셋은 각각 얼마인가?": ["wiki\\concepts\\프레임-짝짓기.md"],
    "31열 로그를 남기는 현장은 어디인가?": ["wiki\\entities\\운영기.md"],
    "요철은 몇 mm로 정규화하나?": ["wiki\\concepts\\높이-합성-공식.md"],
}


def squash(s):
    """공백을 전부 없앤다. '5 분' -> '5분'"""
    return re.sub(r"\s+", "", s)


def hit(text, group):
    t = squash(text)
    return any(squash(form) in t for form in group)


by_q = {c["q"]: c for c in EVALSET}

print(f"{'라벨':<18} {'검색 top-3':>11} {'답변':>8} {'최종':>8}   (괄호 = 재채점 전)")
print("-" * 70)

for path in sorted(glob.glob(os.path.join(RESULTS, "*.json"))):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    n = top_k_ok = ans_ok = both = 0
    changed = []

    for row in data["rows"]:
        case = by_q.get(row["q"])
        if case is None or case["doc"] is None:
            continue
        n += 1

        ok_docs = [case["doc"]] + ALSO_OK.get(row["q"], [])
        retrieved = any(d in row["sources"] for d in ok_docs)
        answered = all(hit(row["answer"], g) for g in case["must"])

        top_k_ok += retrieved
        ans_ok += answered
        both += retrieved and answered

        if answered != row["answered"] or retrieved != row["retrieved"]:
            changed.append((row["q"], row["retrieved"], retrieved, row["answered"], answered))

    old = data["both"]
    print(
        f"{data['label']:<18} {top_k_ok:>3}/{n} ({top_k_ok / n * 100:>3.0f}%) "
        f"{ans_ok:>3}/{n} {both:>4}/{n} ({both / n * 100:>3.0f}%)   ({old}/{n})"
    )
    for q, r0, r1, a0, a1 in changed:
        marks = []
        if r0 != r1:
            marks.append(f"검색 {'X->O' if r1 else 'O->X'}")
        if a0 != a1:
            marks.append(f"답변 {'X->O' if a1 else 'O->X'}")
        print(f"      {' / '.join(marks)}  {q[:44]}")
