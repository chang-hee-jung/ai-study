r"""16주차: 검색 전용 벤치 (생성 없이 검색만 잰다)

[왜 따로 만드나]
evaluate.py는 59문항에 10분이 걸리는데 대부분이 답변 생성 시간이다.
검색만 재면 1분이면 끝난다. 반복이 10배 빨라진다.

[왜 통과/실패가 아니라 순위인가]
남은 실패가 3건뿐이라 통과/실패로는 개선인지 운인지 구분이 안 된다.
정답 문서가 몇 위로 나오는지를 보면 5위->2위 같은 변화도 잡힌다.
같은 3건으로도 판정이 된다.

지표
  Recall@k  정답 문서가 상위 k개 안에 있는 문항 비율
  MRR       1/순위의 평균. 1위면 1.0, 2위면 0.5, 못 찾으면 0
            순위가 오르면 올라가므로 통과/실패보다 해상도가 높다

실행: cd F:\ai-study 후
      .\venv\Scripts\python.exe week16\retrieval_bench.py [라벨]
"""

import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "week15"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ask_wiki  # noqa: E402
from evalset import EVALSET  # noqa: E402

# rescore.py와 같은 목록 (같은 사실이 적힌 다른 문서)
ALSO_OK = {
    "현장별 surface 초 오프셋은 각각 얼마인가?": ["wiki\\concepts\\프레임-짝짓기.md"],
    "31열 로그를 남기는 현장은 어디인가?": ["wiki\\entities\\운영기.md"],
    "요철은 몇 mm로 정규화하나?": ["wiki\\concepts\\높이-합성-공식.md"],
    "SftpCollector는 지금 실제로 쓰이나?": ["wiki\\synthesis\\미사용-코드.md"],
}

DEPTH = 10  # 몇 위까지 보고 순위를 매길지
LABEL = sys.argv[1] if len(sys.argv) > 1 else "base"
OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "retrieval")

cases = [c for c in EVALSET if c["doc"]]

print(f"검색 벤치 - {len(cases)}문항, 상위 {DEPTH}위까지, 라벨={LABEL}")
print(f"  인덱스 {ask_wiki.COLLECTION} / 하이브리드 {'ON' if ask_wiki.HYBRID else 'OFF'}"
      f" / 리랭커 {'ON' if getattr(ask_wiki, 'RERANK', False) else 'OFF'}\n")

rows = []
t0 = time.time()

for i, c in enumerate(cases, 1):
    ok_docs = [c["doc"]] + ALSO_OK.get(c["q"], [])
    _, metas, dists = ask_wiki.search(c["q"], DEPTH)
    sources = [m["source"] for m in metas]

    rank = None
    for j, s in enumerate(sources, 1):
        if s in ok_docs:
            rank = j
            break

    rows.append({"q": c["q"], "doc": c["doc"], "rank": rank, "sources": sources})
    mark = f"{rank}위" if rank else " -- "
    print(f"{i:>2}. {mark}  {c['q'][:44]}")

elapsed = time.time() - t0
n = len(rows)


def recall_at(k):
    return sum(1 for r in rows if r["rank"] and r["rank"] <= k) / n


mrr = sum(1 / r["rank"] for r in rows if r["rank"]) / n

print("\n" + "=" * 60)
print(f"검색 점수판  ({LABEL})")
print("=" * 60)
for k in (1, 3, 5, 10):
    print(f"  Recall@{k:<2}  {recall_at(k) * 100:5.1f}%  ({sum(1 for r in rows if r['rank'] and r['rank'] <= k)}/{n})")
print(f"  MRR       {mrr:.4f}")
print(f"\n  소요 {elapsed:.1f}초 ({elapsed / n:.2f}초/문항)")

missed = [r for r in rows if not r["rank"]]
deep = [r for r in rows if r["rank"] and r["rank"] > 3]
if missed:
    print(f"\n  [상위 {DEPTH}위 안에도 없음] {len(missed)}건")
    for r in missed:
        print(f"    - {r['q']}")
if deep:
    print(f"\n  [4위 이하로 밀림] {len(deep)}건")
    for r in deep:
        print(f"    - {r['rank']}위  {r['q']}")

os.makedirs(OUTDIR, exist_ok=True)
path = os.path.join(OUTDIR, f"{LABEL}.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump({
        "label": LABEL, "n": n, "depth": DEPTH,
        "collection": ask_wiki.COLLECTION,
        "hybrid": ask_wiki.HYBRID,
        "rerank": getattr(ask_wiki, "RERANK", False),
        "recall": {str(k): recall_at(k) for k in (1, 3, 5, 10)},
        "mrr": mrr, "elapsed": elapsed, "rows": rows,
    }, f, ensure_ascii=False, indent=2)
print(f"\n저장: {path}")
