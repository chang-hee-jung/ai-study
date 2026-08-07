# -*- coding: utf-8 -*-
"""헤르메스 설치 상태 전체 점검. 읽기만 한다."""
import json
import os
import subprocess
import sqlite3
from pathlib import Path

import yaml

H = Path(os.environ["LOCALAPPDATA"]) / "hermes"
HX = H / "hermes-agent" / "venv" / "Scripts" / "hermes.exe"
cfg = yaml.safe_load((H / "config.yaml").read_text(encoding="utf-8"))
ok, warn = [], []


def chk(cond, good, bad, hard=True):
    (ok if cond else (warn if not hard else warn)).append(good if cond else bad)
    print(f"  {'O' if cond else 'X'}  {good if cond else bad}")


print("=" * 66)
print("1) 기본 실행")
print("=" * 66)
chk(HX.exists(), f"실행파일 있음", "실행파일 없음")
p = os.environ.get("PATH", "") + ";" + (os.popen(
    'powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable(\'Path\',\'User\')"'
).read())
chk("hermes-agent" in p, "PATH 등록됨 (새 창에서 hermes 바로 실행)", "PATH 미등록")

print()
print("=" * 66)
print("2) 모델")
print("=" * 66)
mi = [k for k, v in enumerate(str(cfg).split()) if False]
model_blocks = [v for k, v in cfg.items() if k == "model"]
m = cfg.get("model", {})
chk(bool(m.get("default")), f"기본 모델: {m.get('default')} ({m.get('provider')})", "기본 모델 미설정")
provs = list((cfg.get("providers") or {}).keys())
chk("ollama" in provs, f"provider 등록: {', '.join(provs)}", "provider 없음")

env = (H / ".env").read_text(encoding="utf-8", errors="replace")
chk("OPENROUTER_API_KEY=sk-or" in env, "OpenRouter 키 설정됨", "OpenRouter 키 없음")

print()
print("=" * 66)
print("3) MoA")
print("=" * 66)
moa = cfg.get("moa", {})
pre = moa.get("presets", {})
chk("free-diverse" in pre, f"프리셋 등록: {', '.join(pre)}", "프리셋 없음")
if "free-diverse" in pre:
    fd = pre["free-diverse"]
    refs = fd.get("reference_models", [])
    vendors = {r["model"].split("/")[0] for r in refs}
    chk(len(vendors) >= 3, f"참조 {len(refs)}개 / 벤더 {len(vendors)}곳 — 다양성 확보",
        f"벤더 {len(vendors)}곳 — 다양성 부족")
    chk(fd.get("enabled"), "프리셋 활성화됨", "프리셋 비활성")
chk(moa.get("default_preset") == "free-diverse",
    f"기본 프리셋: {moa.get('default_preset')}", "기본 프리셋 미지정")
traces = list((H / "moa-traces").glob("*.jsonl")) if (H / "moa-traces").exists() else []
chk(len(traces) > 0, f"실행 기록 {len(traces)}건 — 실제 동작 확인됨", "실행 기록 없음")

print()
print("=" * 66)
print("4) 자기 학습")
print("=" * 66)
mem = list((H / "memories").glob("*")) if (H / "memories").exists() else []
chk(any(f.name == "MEMORY.md" for f in mem), f"메모리 파일 {len(mem)}개", "메모리 없음")
sk = cfg.get("skills", {})
mcfg = cfg.get("memory", {})
chk(mcfg.get("memory_enabled") is True, "메모리 기능 켜짐", "메모리 꺼짐")
chk(mcfg.get("nudge_interval", 99) <= 5,
    f"메모리 넛지 주기 {mcfg.get('nudge_interval')} (기본 10보다 낮춤)",
    f"메모리 넛지 {mcfg.get('nudge_interval')}")
try:
    r = subprocess.run([str(HX), "journey", "--json"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120)
    st = json.loads(r.stdout)["stats"]
    chk(st["learned_skills"] > 0,
        f"학습된 스킬 {st['learned_skills']}개 / 메모리 노드 {st['memory_nodes']}개",
        "학습 기록 없음")
except Exception as e:
    print(f"  ?  journey 조회 실패: {e}")

print()
print("=" * 66)
print("5) 백업")
print("=" * 66)
for f in ("config.yaml.bak", "config.yaml.premoa", "SOUL.md.orig"):
    chk((H / f).exists(), f"{f} 있음", f"{f} 없음", hard=False)

print()
print("=" * 66)
print("점검 요약")
print("=" * 66)
bad = [w for w in warn if w.startswith(("실행파일 없음", "PATH 미등록")) or "없음" in w or "부족" in w or "꺼짐" in w]
print(f"  통과 {len(ok)}  /  확인 필요 {len(bad)}")
for b in bad:
    print(f"    - {b}")
