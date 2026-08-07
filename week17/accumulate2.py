# 17주차: 자기 학습을 제대로 재본다 (긴 세션)
#
# 실행: .\venv\Scripts\python week17\accumulate2.py
#
# 1차 시도(accumulate.py)는 user 턴 6회로 끝냈다. 그런데 config.yaml에
# 넛지 주기가 이렇게 박혀 있었다.
#
#   skills.creation_nudge_interval : 15   ← 스킬 생성 넛지는 15턴마다
#   memory.nudge_interval          : 10   ← 메모리 넛지는 10턴마다
#   memory.flush_min_turns         :  6
#
# 6턴으로는 둘 다 못 넘는다. "발동 안 함"이 아니라 "주기에 도달 못 함"이었다.
# 이번엔 24턴을 한 세션에서 돌린다.
#
# 그리고 과제도 바꾼다. 똑같은 일만 반복하면 스킬로 굳힐 절차가 없다.
# 비슷하지만 조금씩 다른 일을 시켜야 "이럴 땐 이렇게"가 만들어진다.

import os
import re
import subprocess
import time
from pathlib import Path

from make_testbed import BENCH, build, score

HOME = Path(os.environ["LOCALAPPDATA"]) / "hermes"
HERMES = HOME / "hermes-agent" / "venv" / "Scripts" / "hermes.exe"
TURNS = 24
PER_TURN_TIMEOUT = 300

BASE_RULE = "문서는 txt/pdf/py, 사진은 jpg/png, 나머지는 기타"


def tasks():
    """24턴. 정리 작업을 뼈대로 하되 규칙과 표현을 조금씩 바꾼다."""
    out = []
    for i in range(1, 9):
        d = f"week17/bench/L{i}"
        if i == 1:
            out.append((d, f"{d} 폴더를 정리해줘. 문서/사진/기타 폴더를 만들고 "
                           f"파일을 종류에 맞게 옮겨줘. {BASE_RULE}로."))
        elif i in (2, 4, 6, 8):
            out.append((d, f"{d} 폴더도 아까와 같은 방식으로 정리해줘."))
        else:
            out.append((d, f"{d} 폴더를 같은 규칙으로 정리해줘."))
        # 사이사이 확인 질문을 넣어 턴 수를 채우고 대화를 자연스럽게 만든다
        out.append((None, f"{d} 안에 각 폴더별로 파일이 몇 개씩 들어갔는지 알려줘."))
        out.append((None, "방금 한 정리 작업의 절차를 한 줄로 요약해줘."))
    return out[:TURNS]


def snap():
    sk = {str(p.relative_to(HOME)) for p in (HOME / "skills").rglob("*") if p.is_file()}
    mem = {str(p.relative_to(HOME)) for p in (HOME / "memories").rglob("*") if p.is_file()} \
        if (HOME / "memories").exists() else set()
    return sk, mem


# 모델을 환경변수로 갈아끼울 수 있게 한다. 가설 1(모델이 약해서)을 가르기 위해
# 나머지 조건은 그대로 두고 모델만 바꿔 돌린다.
PROVIDER = os.environ.get("HERMES_PROVIDER", "")
MODEL = os.environ.get("HERMES_MODEL", "")


def run(text, sid):
    cmd = [str(HERMES), "chat"]
    if PROVIDER:
        cmd += ["--provider", PROVIDER]
    if MODEL:
        cmd += ["-m", MODEL]
    if sid:
        cmd += ["--resume", sid]
    cmd += ["-q", text]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=PER_TURN_TIMEOUT)
        out = (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return time.time() - t0, "", "시간초과", ""
    m = re.search(r"Session:\s+(\S+)", out)
    return time.time() - t0, (m.group(1) if m else sid), "", out


if __name__ == "__main__":
    BENCH.mkdir(parents=True, exist_ok=True)
    base_sk, base_mem = snap()
    print(f"시작 — 스킬 {len(base_sk)}개 / 메모리 {len(base_mem)}개")
    print(f"넛지 주기: 스킬 15턴, 메모리 10턴 → {TURNS}턴 돌린다\n")

    sid = ""
    for n, (folder, text) in enumerate(tasks(), 1):
        if folder:
            build(Path(folder).name)
        sec, sid, err, out = run(text, sid)
        sk, mem = snap()
        nsk, nmem = sk - base_sk, mem - base_mem
        sc = ""
        if folder:
            s = score(BENCH / Path(folder).name)
            sc = f"정리 {s['맞게 옮김']}/{s['총']}"
        # 넛지가 실제로 떴는지 출력에서 찾아본다
        hint = ""
        for kw in ("skill", "Skill", "memory", "Memory", "MEMORY", "remember"):
            if kw in out:
                hint = "  ※출력에 skill/memory 언급"
                break
        print(f"[{n:2}/{TURNS}] {sec:6.1f}초  스킬+{len(nsk)}  메모리+{len(nmem)}  "
              f"{sc:12} {err}{hint}")
        for p in sorted(nsk)[-2:]:
            print(f"          + 스킬 {p}")
        for p in sorted(nmem)[-2:]:
            print(f"          + 메모리 {p}")
        (BENCH / f"L_{n:02}.log").write_text(out, encoding="utf-8")

    sk, mem = snap()
    print(f"\n{'='*60}")
    print(f"최종 — 새 스킬 {len(sk-base_sk)}개 / 새 메모리 {len(mem-base_mem)}개")
    print(f"세션: {sid}")
    print("=" * 60)
    for cmd in (["curator", "status"], ["memory", "show"]):
        try:
            r = subprocess.run([str(HERMES)] + cmd, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=180)
            print(f"\n--- hermes {' '.join(cmd)} ---")
            print((r.stdout or r.stderr or "")[:900])
        except Exception as e:
            print(f"  {cmd} 실패: {e}")
