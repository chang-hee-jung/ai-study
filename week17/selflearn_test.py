# -*- coding: utf-8 -*-
"""지적 없이도 스스로 배우는가.

앞선 실험은 전부 사람이 교정을 넣어 ①② 신호로 발동시킨 것이었다.
리뷰 프롬프트에는 사람 개입 없이도 걸리는 신호가 둘 더 있다.

  ③ 사소하지 않은 기법·수정·우회로·디버깅 경로가 나옴
  ④ 불러 쓴 스킬이 틀렸거나 빠짐

이번엔 아무 지적도 하지 않는다. 대신 진짜 어려운 문제를 준다.
일부러 망가뜨린 스크립트를 고치게 하면 디버깅 경로가 생긴다.
"""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HOME = Path(os.environ["LOCALAPPDATA"]) / "hermes"
TURN = Path(__file__).with_name("turn.py")
PY = HOME / "hermes-agent" / "venv" / "Scripts" / "python.exe"
WORK = Path(r"F:\ai-study\week17\bench\debug")

# 일부러 심어둔 버그 3종. 눈에 잘 안 띄고 원인이 서로 다르다.
BROKEN = '''# 매출 집계 스크립트
import csv
from collections import defaultdict

def load(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows

def total_by_region(rows):
    out = defaultdict(int)
    for r in rows:
        out[r["region"]] += r["amount"]      # 버그1: 문자열을 더한다
    return out

def top_region(totals):
    return max(totals)                        # 버그2: 값이 아니라 키로 최대

def report(path):
    rows = load(path)
    t = total_by_region(rows)
    print(f"지역 수: {len(t)}")
    print(f"최대 매출 지역: {top_region(t)}")
    for k in sorted(t, key=lambda x: t[x]):   # 버그3: 오름차순(내림차순이어야)
        print(f"  {k}: {t[k]:,}원")

if __name__ == "__main__":
    report("sales.csv")
'''

CSV = """region,amount
서울,150000
부산,90000
서울,120000
대구,45000
부산,60000
"""

TASKS = [
    "sales_report.py 를 실행하면 에러가 난다. 원인을 찾아서 고쳐줘. "
    "고친 뒤 실제로 실행해서 결과가 맞는지 확인해라.",
    "결과가 정확한지 손으로 계산해서 검증해줘.",
    "혹시 더 남은 문제가 있는지 코드를 다시 훑어봐줘.",
]


def snap():
    sk = {str(p) for p in (HOME / "skills").rglob("*") if p.is_file()}
    mem = {str(p) for p in (HOME / "memories").rglob("*") if p.is_file()} \
        if (HOME / "memories").exists() else set()
    return sk, mem


if __name__ == "__main__":
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / "sales_report.py").write_text(BROKEN, encoding="utf-8")
    (WORK / "sales.csv").write_text(CSV, encoding="utf-8")
    print(f"작업 폴더: {WORK}")
    print("버그 3종을 심어뒀다. 지적은 한 마디도 하지 않는다.\n")

    base_sk, base_mem = snap()
    print(f"시작 — 스킬 {len(base_sk)} / 메모리 {len(base_mem)}\n")

    sid = "-"
    for i, t in enumerate(TASKS, 1):
        full = f"{WORK.as_posix()} 폴더의 {t}"
        r = subprocess.run([str(PY), str(TURN), sid, full], capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=700, cwd=str(WORK))
        out = (r.stdout or "") + (r.stderr or "")
        m = re.search(r"Session:\s+(\S+)", out)
        if m:
            sid = m.group(1)
        bg = "완주" if "bg-review 완주" in out else "-"
        sk, mem = snap()
        print(f"[{i}/{len(TASKS)}] bg:{bg:4} 스킬+{len(sk-base_sk)} 메모리+{len(mem-base_mem)}"
              f"  | {t[:32]}...")
        for p in sorted(sk - base_sk)[-3:]:
            print(f"        + {os.path.relpath(p, HOME)}")
        (WORK / f"turn_{i}.log").write_text(out, encoding="utf-8")

    print(f"\n세션: {sid}")
    print("\n=== 고쳐진 코드 ===")
    print((WORK / "sales_report.py").read_text(encoding="utf-8")[:900])
