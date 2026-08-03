r"""15주차 3단계: 점수판 - 지금 QA 봇이 몇 점인가

두 가지를 나눠서 잰다. 섞어서 재면 어디를 고쳐야 할지 알 수 없다.

  검색 정확도 : 정답이 적힌 문서를 가져왔는가 (top-1 / top-k)
  답변 정확도 : 가져온 근거로 실제로 맞게 답했는가 (must 표기 포함 여부)

이 둘을 나누면 실패가 세 종류로 갈린다.
  검색 X          -> 청킹·임베딩·top-k 문제
  검색 O + 답변 X -> 프롬프트·모델·근거 조립 문제   <- 지금 의심되는 쪽
  둘 다 O         -> 통과

결과는 week15/results/ 에 저장한다. 16주차 개선 뒤 같은 스크립트로 재서 비교한다.

실행: cd F:\ai-study 후
      .\venv\Scripts\python.exe week15\evaluate.py [라벨]
      예) .\venv\Scripts\python.exe week15\evaluate.py baseline
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ask_wiki import TOP_K, answer  # noqa: E402
from evalset import EVALSET  # noqa: E402

LABEL = sys.argv[1] if len(sys.argv) > 1 else "baseline"
OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def hit(text, group):
    """같은 뜻의 표기 묶음 중 하나라도 들어 있으면 통과"""
    return any(form in text for form in group)


rows = []
t0 = time.time()

print(f"평가 시작 - {len(EVALSET)}문항, top_k={TOP_K}, 라벨={LABEL}\n")

for i, case in enumerate(EVALSET, 1):
    text, chunks, metas, dists = answer(case["q"])
    sources = [m["source"] for m in metas]

    if case["doc"] is None:
        # 함정 문항: 검색은 채점 대상이 아니다. 모른다고 답해야 정답.
        retrieved, rank = None, None
    else:
        retrieved = case["doc"] in sources
        rank = sources.index(case["doc"]) + 1 if retrieved else None

    answered = all(hit(text, group) for group in case["must"])

    rows.append({
        "q": case["q"],
        "doc": case["doc"],
        "retrieved": retrieved,
        "rank": rank,
        "answered": answered,
        "dist1": round(dists[0], 3),
        "sources": sources,
        "answer": text,
    })

    mark_r = "-" if retrieved is None else ("O" if retrieved else "X")
    mark_a = "O" if answered else "X"
    print(f"{i:>2}. 검색 {mark_r}{f'({rank}위)' if rank else '     '}  답변 {mark_a}   {case['q'][:34]}")

elapsed = time.time() - t0

# ── 집계 ────────────────────────────────────────────────────────────
real = [r for r in rows if r["doc"] is not None]
traps = [r for r in rows if r["doc"] is None]

top1 = sum(1 for r in real if r["rank"] == 1)
topk = sum(1 for r in real if r["retrieved"])
ans_ok = sum(1 for r in real if r["answered"])
both = sum(1 for r in real if r["retrieved"] and r["answered"])
trap_ok = sum(1 for r in traps if r["answered"])

# 검색은 됐는데 답변이 틀린 것 = 생성 단계 문제
found_but_wrong = [r for r in real if r["retrieved"] and not r["answered"]]
not_found = [r for r in real if not r["retrieved"]]

n = len(real)
print("\n" + "=" * 62)
print(f"점수판  ({LABEL})")
print("=" * 62)
print(f"  검색 정확도 top-1   : {top1}/{n}  ({top1 / n * 100:.0f}%)")
print(f"  검색 정확도 top-{TOP_K}   : {topk}/{n}  ({topk / n * 100:.0f}%)")
print(f"  답변 정확도         : {ans_ok}/{n}  ({ans_ok / n * 100:.0f}%)")
print(f"  최종(둘 다 통과)    : {both}/{n}  ({both / n * 100:.0f}%)")
print(f"  함정 문항           : {trap_ok}/{len(traps)}")
print(f"\n  실패 분해")
print(f"    검색부터 실패      : {len(not_found)}건")
print(f"    검색 O / 답변 X    : {len(found_but_wrong)}건   <- 생성 단계 문제")
print(f"\n  소요 {elapsed / 60:.1f}분")

if found_but_wrong:
    print("\n  [검색은 됐는데 답변이 틀린 문항]")
    for r in found_but_wrong:
        print(f"    - {r['q']}  (정답문서 {r['rank']}위)")

if not_found:
    print("\n  [정답 문서를 못 가져온 문항]")
    for r in not_found:
        print(f"    - {r['q']}")
        print(f"        가져온 것: {r['sources']}")

os.makedirs(OUTDIR, exist_ok=True)
path = os.path.join(OUTDIR, f"{LABEL}.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump({
        "label": LABEL,
        "top_k": TOP_K,
        "n": n,
        "top1": top1,
        "topk": topk,
        "answered": ans_ok,
        "both": both,
        "trap_ok": trap_ok,
        "rows": rows,
    }, f, ensure_ascii=False, indent=2)
print(f"\n저장: {path}")
