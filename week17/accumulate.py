# 17주차: Hermes는 정말 "스스로 학습"하는가
#
# 실행: .\venv\Scripts\python week17\accumulate.py
#
# 지금까지의 비교(compare.py)는 매번 새 세션으로 단발 과제를 5번 반복했다.
# 그건 "한 번 시켰을 때 잘 하나"를 잰 것이고, 홍보 문구가 말하는 장점
# (스킬 자동 생성, 세션 초월 메모리)은 전부 "여러 번 시켰을 때 나아지나"
# 쪽이라 아예 측정이 안 됐다.
#
# 여기서는 축을 바꾼다.
#   - --continue 로 같은 세션을 이어간다
#   - 비슷한 일을 6번 반복시킨다
#   - 매 회차 skills/ 와 memories/ 를 스냅샷해서 새로 생기는지 본다
#
# 확인할 것
#   1. skills/ 에 에이전트가 만든 스킬이 생기는가
#   2. memories/ 에 사실이 뽑히는가
#   3. 회차가 갈수록 빨라지거나 도구 호출이 줄어드는가

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from make_testbed import BENCH, build, score

HERMES = (Path(os.environ["LOCALAPPDATA"]) / "hermes" / "hermes-agent"
          / "venv" / "Scripts" / "hermes.exe")
HOME = Path(os.environ["LOCALAPPDATA"]) / "hermes"
ROUNDS = 6
PER_TASK_TIMEOUT = 420

RULE = ("문서/사진/기타 폴더를 만들고 파일을 종류에 맞게 옮겨줘. "
        "문서는 txt/pdf/py, 사진은 jpg/png, 나머지는 기타로.")


def snapshot():
    """스킬과 메모리 파일 집합을 찍는다."""
    sk = {str(p.relative_to(HOME)) for p in (HOME / "skills").rglob("*") if p.is_file()}
    mem = {str(p.relative_to(HOME)) for p in (HOME / "memories").rglob("*") if p.is_file()} \
        if (HOME / "memories").exists() else set()
    return sk, mem


def run(task: str, first: bool):
    cmd = [str(HERMES), "chat"]
    if not first:
        cmd.append("--continue")      # 같은 세션을 이어간다 (기억이 쌓이는 조건)
    cmd += ["-q", task]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=PER_TASK_TIMEOUT)
        out = (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return time.time() - t0, 0, "시간초과", ""
    sec = time.time() - t0
    calls = 0
    for line in out.splitlines():
        if "tool call" in line:
            for tok in line.replace("(", " ").replace(",", " ").split():
                if tok.isdigit():
                    calls = int(tok)
    sid = ""
    m = re.search(r"Session:\s+(\S+)", out)
    if m:
        sid = m.group(1)
    return sec, calls, "", out, sid


if __name__ == "__main__":
    BENCH.mkdir(parents=True, exist_ok=True)
    base_sk, base_mem = snapshot()
    print(f"시작 시점 — 스킬 파일 {len(base_sk)}개 / 메모리 {len(base_mem)}개\n")

    rows = []
    for i in range(1, ROUNDS + 1):
        name = f"acc{i}"
        d = build(name)
        task = (f"{d.as_posix()} 폴더를 정리해줘. {RULE}" if i == 1
                else f"{d.as_posix()} 폴더도 아까와 같은 방식으로 정리해줘.")

        res = run(task, first=(i == 1))
        sec, calls, err, out = res[0], res[1], res[2], res[3]
        sid = res[4] if len(res) > 4 else ""
        s = score(d)
        sk, mem = snapshot()
        new_sk, new_mem = sk - base_sk, mem - base_mem

        rows.append((i, sec, calls, s["맞게 옮김"], len(new_sk), len(new_mem)))
        print(f"[{i}/{ROUNDS}] {sec:6.1f}초  도구 {calls:2}회  "
              f"정리 {s['맞게 옮김']}/{s['총']}  "
              f"새 스킬 {len(new_sk)}  새 메모리 {len(new_mem)}  {err}")
        for p in sorted(new_sk)[-3:]:
            print(f"        + {p}")
        for p in sorted(new_mem)[-3:]:
            print(f"        + {p}")
        (BENCH / f"acc_{i}.log").write_text(out, encoding="utf-8")

    print("\n" + "=" * 66)
    print(f"  {'회차':>4}{'시간':>9}{'도구':>6}{'점수':>7}{'새스킬':>8}{'새메모리':>9}")
    print("=" * 66)
    for i, sec, calls, sc, nsk, nmem in rows:
        print(f"  {i:>4}{sec:>8.1f}초{calls:>6}{sc:>5}/7{nsk:>8}{nmem:>9}")

    print("\n=== curator 상태 ===")
    try:
        r = subprocess.run([str(HERMES), "curator", "status"], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=180)
        print((r.stdout or r.stderr or "")[:1200])
    except Exception as e:
        print("  실패:", e)
