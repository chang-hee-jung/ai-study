# -*- coding: utf-8 -*-
"""OpenRouter 무료 모델 중 실제로 응답하는 것을 골라낸다.

무료 목록에 있어도 "This model is unavailable for free" 로 막히는 게 많다.
MoA에 넣기 전에 실물로 확인한다. Hermes가 최소 64K 컨텍스트를 요구하므로
그 조건도 같이 건다.
"""
import json
import os
import concurrent.futures as cf

import requests

KEY = os.environ["OR_KEY"]
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

models = requests.get("https://openrouter.ai/api/v1/models", timeout=30).json()["data"]
cands = [m for m in models
         if m["id"].endswith(":free") and (m.get("context_length") or 0) >= 64000]
print(f"무료 + 64K 이상: {len(cands)}개\n")


def probe(m):
    mid = m["id"]
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=H,
                          json={"model": mid,
                                "messages": [{"role": "user", "content": "Reply with only: OK"}],
                                "max_tokens": 12}, timeout=60)
        d = r.json()
        if "error" in d:
            return mid, False, str(d["error"].get("message", ""))[:44], m
        txt = d["choices"][0]["message"]["content"]
        return mid, True, repr(txt[:16]), m
    except Exception as e:
        return mid, False, f"{type(e).__name__}", m


with cf.ThreadPoolExecutor(max_workers=6) as ex:
    results = list(ex.map(probe, cands))

ok = []
for mid, good, note, m in sorted(results, key=lambda x: (not x[1], x[0])):
    print(f"  {'O' if good else 'X'}  {mid:48} {note}")
    if good:
        ok.append((mid, m.get("context_length"), mid.split("/")[0]))

print(f"\n=== 실제로 되는 것 {len(ok)}개 ===")
byvendor = {}
for mid, ctx, vendor in ok:
    byvendor.setdefault(vendor, []).append((mid, ctx))
for v, lst in sorted(byvendor.items()):
    print(f"  [{v}]")
    for mid, ctx in lst:
        print(f"      {mid:50} ctx={ctx:,}")
print(f"\n벤더 수: {len(byvendor)}  → MoA 다양성 확보 가능 여부의 핵심")
