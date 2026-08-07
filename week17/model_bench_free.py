# -*- coding: utf-8 -*-
"""OpenRouter 무료 모델 중 어느 것이 에이전트용으로 제일 나은가.

크기로 고르지 않고 실제로 잰다. 헤르메스가 요구하는 것은 두 가지다.
  1. 긴 시스템 프롬프트를 받고도 도구를 제대로 부르는가
  2. 도구가 필요 없을 때 억지로 부르지 않는가
여기에 속도와 한국어 품질을 함께 본다.
"""
import concurrent.futures as cf
import json
import os
import time

import requests

KEY = os.environ["OR_KEY"]
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
URL = "https://openrouter.ai/api/v1/chat/completions"

MODELS = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "google/gemma-4-26b-a4b-it:free",
    "poolside/laguna-s-2.1:free",
]

SYSTEM = open(r"F:\ai-study\week12\agent.py", encoding="utf-8").read() \
    .split('SYSTEM = """')[1].split('"""')[0]

TOOLS = [{"type": "function", "function": {"name": n, "description": d,
          "parameters": {"type": "object", "properties": p, "required": list(p)}}}
         for n, d, p in [
    ("list_files", "폴더 안의 파일과 폴더 목록을 알려준다", {"folder": {"type": "string"}}),
    ("make_folder", "새 폴더를 만든다", {"path": {"type": "string"}}),
    ("move_file", "파일을 옮긴다", {"src": {"type": "string"}, "dst": {"type": "string"}}),
]]

# (라벨, 질문, 기대도구|None, 기대인자|None)
CASES = [
    ("기본호출", "week17 폴더에 뭐가 들어있는지 알려줘", "list_files", {"folder": "week17"}),
    ("한글인자", "week17 안에 '실습자료' 라는 폴더를 만들어줘", "make_folder", {"path": "week17/실습자료"}),
    ("과잉억제", "파이썬에서 리스트와 튜플의 차이가 뭐야?", None, None),
    ("한국어", "적설량을 예측하는 모델을 만들려면 어떤 데이터가 필요한지 세 가지만 짧게", None, None),
]


def norm(v):
    return str(v).replace("\\", "/").strip().strip("'\"")


def one(model, case):
    label, q, want, wargs = case
    t0 = time.time()
    try:
        r = requests.post(URL, headers=H, timeout=180, json={
            "model": model,
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": q}],
            "tools": TOOLS, "tool_choice": "auto", "max_tokens": 400})
        d = r.json()
    except Exception as e:
        return label, "ERR", time.time() - t0, f"{type(e).__name__}", 0
    sec = time.time() - t0
    if "error" in d:
        return label, "ERR", sec, str(d["error"].get("message", ""))[:40], 0
    m = d["choices"][0]["message"]
    usage = d.get("usage", {}) or {}
    out_tok = usage.get("completion_tokens", 0)
    tc = m.get("tool_calls")
    if want is None:
        if tc:
            return label, "X", sec, f"불필요 호출 {tc[0]['function']['name']}", out_tok
        body = (m.get("content") or "").strip()
        return label, ("O" if len(body) > 20 else "-"), sec, body[:40].replace("\n", " "), out_tok
    if not tc:
        return label, "X", sec, "글로 씀: " + (m.get("content") or "")[:32].replace("\n", " "), out_tok
    f = tc[0]["function"]
    if f["name"] != want:
        return label, "-", sec, f"{f['name']} 호출(기대 {want})", out_tok
    try:
        args = json.loads(f["arguments"]) if isinstance(f["arguments"], str) else f["arguments"]
    except Exception:
        return label, "-", sec, "인자 파싱 실패", out_tok
    for k, v in wargs.items():
        if norm(args.get(k, "")) != norm(v):
            return label, "-", sec, f"{k}={args.get(k)!r}", out_tok
    return label, "O", sec, "정확", out_tok


def run(model):
    rows = [one(model, c) for c in CASES]
    score = sum(1 for r in rows if r[1] == "O")
    tot = sum(r[2] for r in rows)
    return model, score, tot, rows


print(f"시스템 프롬프트 {len(SYSTEM.encode())} 바이트 / 도구 3개 / 문항 {len(CASES)}개\n")
with cf.ThreadPoolExecutor(max_workers=3) as ex:
    results = list(ex.map(run, MODELS))

for model, score, tot, rows in results:
    print(f"── {model}")
    for label, mark, sec, note, tok in rows:
        print(f"     [{mark}] {label:8} {sec:6.1f}초 {tok:>4}tok  {note}")
    print(f"     → {score}/{len(CASES)}  총 {tot:.1f}초\n")

print("=" * 72)
print(f"  {'모델':52}{'점수':>6}{'시간':>9}")
print("=" * 72)
for model, score, tot, rows in sorted(results, key=lambda r: (-r[1], r[2])):
    bar = "".join(r[1] for r in rows)
    print(f"  {model:52}{score:>3}/{len(CASES)}{tot:>7.1f}초  {bar}")
