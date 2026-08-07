# -*- coding: utf-8 -*-
"""MoA가 실제로 도는지 A/B로 확인한다.

같은 질문을 두 번 던진다.
  A: 그냥 -q            → 메인 모델(gpt-4.1) 혼자
  B: MoA 마커를 실어서   → 참조 3개 + 취합

MoA가 진짜 돌면 (1) 느리고 (2) 답이 더 넓고 (3) 참조 모델 특유의
관점이 섞인다. 시간 차이가 가장 객관적인 지표다.
"""
import pathlib
import subprocess
import sys
import time

import yaml

HOME = pathlib.Path.home() / "AppData" / "Local" / "hermes"
sys.path.insert(0, str(HOME / "hermes-agent"))
HERMES = HOME / "hermes-agent" / "venv" / "Scripts" / "hermes.exe"

from hermes_cli.moa_config import encode_moa_turn

cfg = yaml.safe_load((HOME / "config.yaml").read_text(encoding="utf-8"))
Q = ("파이썬 딕셔너리 두 개를 병합할 때 키가 겹치면 값을 리스트로 모으는 "
     "방법을 알려줘. 짧게.")


def run(payload, label):
    t0 = time.time()
    r = subprocess.run([str(HERMES), "chat", "--provider", "copilot",
                        "-m", "gpt-4.1", "-q", payload],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=600, cwd=r"F:\ai-study")
    sec = time.time() - t0
    out = (r.stdout or "") + (r.stderr or "")
    body = []
    keep = False
    for ln in out.splitlines():
        s = ln.replace("\x1b", "")
        if "─ ⚕ Hermes" in s:
            keep = True
            continue
        if keep and s.strip().startswith("╰"):
            keep = False
        if keep:
            body.append(s.strip("│ "))
    text = "\n".join(x for x in body if x.strip())
    print(f"\n{'='*62}\n{label}  —  {sec:.1f}초 / 응답 {len(text)}자\n{'='*62}")
    print(text[:700])
    return sec, len(text)


a = run(Q, "A: 단일 모델 (gpt-4.1)")
b = run(encode_moa_turn(Q, cfg["moa"], preset="free-diverse"),
        "B: MoA (참조 3 + 취합 1)")

print(f"\n{'='*62}")
print(f"  A 단일   {a[0]:6.1f}초   {a[1]:5}자")
print(f"  B MoA    {b[0]:6.1f}초   {b[1]:5}자")
print(f"  → 시간 {b[0]/max(a[0],0.1):.1f}배, 분량 {b[1]/max(a[1],1):.1f}배")
print("  MoA가 실제로 돌면 참조 모델 3개를 기다리므로 뚜렷하게 느려야 한다.")
