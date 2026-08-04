r"""16주차: 적설계 QA 봇 실사용 모드

15주차까지는 평가만 했다. 59문항은 내가(Claude가) 만든 문항이라
"뭘 개선할지도 내가 정하는" 상태였다. 이제 실제로 써보고 실패를 모은다.

달라진 점
  - 대화형 - 프로그램 한 번 띄우고 계속 물어본다 (모델·인덱스 재로딩 없음)
  - 답이 이상하면 그 자리에서 `x` 를 눌러 표시 -> failures.jsonl 에 쌓인다
  - 쌓인 실패가 다음 평가 문항이 된다

명령
  x        직전 답이 틀렸다고 표시 (사유를 물어봄)
  ?        직전 답의 근거 조각 전체를 보여줌
  q        종료

실행: cd F:\ai-study 후
      .\venv\Scripts\python.exe week16\chat_wiki.py
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "week15"))

os.environ.setdefault("ASK_HYBRID", "1")  # 15주차 채택본: 하이브리드 검색

import ask_wiki  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FAIL_LOG = os.path.join(HERE, "failures.jsonl")


def save_failure(question, answer, sources, reason):
    rec = {
        "q": question,
        "answer": answer,
        "sources": sources,
        "reason": reason,
        "model": ask_wiki.GEN_MODEL,
        "collection": ask_wiki.COLLECTION,
        "top_k": ask_wiki.TOP_K,
    }
    with open(FAIL_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def count_failures():
    if not os.path.exists(FAIL_LOG):
        return 0
    with open(FAIL_LOG, encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


print("적설계 위키 QA 봇")
print(f"  모델   {ask_wiki.GEN_MODEL}")
print(f"  인덱스 {ask_wiki.COLLECTION} / top_k {ask_wiki.TOP_K} / 하이브리드 {'ON' if ask_wiki.HYBRID else 'OFF'}")
print(f"  실패 기록 {count_failures()}건 ({FAIL_LOG})")
print("\n  x = 직전 답이 틀렸다고 표시 | ? = 근거 전체 보기 | q = 종료\n")

last = None

while True:
    try:
        line = input("질문> ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        break

    if not line:
        continue
    if line == "q":
        break

    if line == "x":
        if last is None:
            print("  (표시할 직전 답변이 없습니다)\n")
            continue
        reason = input("  뭐가 틀렸습니까? ").strip()
        save_failure(last["q"], last["answer"], last["sources"], reason)
        print(f"  기록했습니다. 누적 {count_failures()}건\n")
        continue

    if line == "?":
        if last is None:
            print("  (직전 답변이 없습니다)\n")
            continue
        for i, (chunk, meta, dist) in enumerate(last["evidence"], 1):
            print(f"\n  [근거 {i}] 거리 {dist:.3f}  {meta['source']}")
            for ln in chunk.split("\n"):
                print(f"      {ln}")
        print()
        continue

    t = time.time()
    text, chunks, metas, dists = ask_wiki.answer(line)
    elapsed = time.time() - t

    print(f"\n{text}\n")
    print(f"  근거: {', '.join(m['source'] for m in metas)}")
    print(f"  ({elapsed:.1f}초)\n")

    last = {
        "q": line,
        "answer": text,
        "sources": [m["source"] for m in metas],
        "evidence": list(zip(chunks, metas, dists)),
    }

print(f"\n종료. 실패 기록 누적 {count_failures()}건")
if count_failures():
    print(f"  {FAIL_LOG}")
