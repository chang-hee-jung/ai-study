# 17주차 2단계: 같은 과제를 두 에이전트에게 시키고 비교한다
#
# 실행: .\venv\Scripts\python week17\compare.py
#       .\venv\Scripts\python week17\compare.py mine     (한쪽만)
#
# 핵심은 "누가 이기냐"가 아니라 "어디서 갈리냐"다.
# 채점은 모델의 보고가 아니라 실제 디스크 상태로 한다 — 12주차에 배운 것.

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from make_testbed import BENCH, build, score

GOAL = ("{path} 폴더를 정리해줘. 그 폴더 안에 문서, 사진, 기타 폴더를 만들고 "
        "파일을 종류에 맞게 옮겨줘. 문서는 txt/pdf/py, 사진은 jpg/png, 나머지는 기타로.")

PY = sys.executable
MEMORY = Path("week12/memory.json")


def find_hermes():
    """hermes 실행 파일을 찾는다. PATH에 없으면 기본 설치 위치를 뒤진다."""
    p = shutil.which("hermes")
    if p:
        return p
    guess = (Path(os.environ.get("LOCALAPPDATA", "")) / "hermes" / "hermes-agent"
             / "venv" / "Scripts" / "hermes.exe")
    return str(guess) if guess.exists() else None


def run_mine():
    """내 agent.py. 대화형이라 stdin으로 목표와 /bye를 밀어넣는다."""
    d = build("mine")
    if MEMORY.exists():
        MEMORY.unlink()          # 이전 실행의 기억이 남으면 공정하지 않다

    env = dict(os.environ, AGENT_AUTO_APPROVE="1", PYTHONIOENCODING="utf-8")
    stdin = GOAL.format(path=d.as_posix()) + "\n/bye\n"

    t0 = time.time()
    r = subprocess.run([PY, "week12/agent.py"], input=stdin, env=env,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=900)
    sec = time.time() - t0
    out = r.stdout or ""
    return {
        "이름": "내 agent.py",
        "초": sec,
        "라운드": out.count("── 라운드"),
        # agent.py는 `도구명{인자} → 결과` 형태로 찍는다. 소괄호가 아니라 중괄호다
        "도구호출": sum(out.count(t + "{") for t in
                     ("list_files", "make_folder", "move_file", "move_by_extension")),
        "점수": score(d),
        "출력": out,
        "에러": (r.stderr or "")[-800:],
    }


def run_hermes():
    """Hermes. -q 는 한 번 묻고 끝내는 모드."""
    exe = find_hermes()
    if not exe:
        return {"이름": "Hermes", "초": 0, "라운드": 0, "도구호출": 0,
                "점수": None, "출력": "", "에러": "hermes 실행 파일을 찾지 못했다"}

    d = build("hermes")
    t0 = time.time()
    r = subprocess.run([exe, "chat", "-q", GOAL.format(path=d.as_posix())],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=900,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    sec = time.time() - t0
    out = (r.stdout or "") + (r.stderr or "")

    # "Messages: 6 (1 user, 4 tool calls)" 같은 줄에서 도구 호출 수를 뽑는다
    calls = 0
    for line in out.splitlines():
        if "tool call" in line:
            for tok in line.replace("(", " ").replace(",", " ").split():
                if tok.isdigit():
                    calls = int(tok)
    return {"이름": "Hermes", "초": sec, "라운드": None, "도구호출": calls,
            "점수": score(d), "출력": out, "에러": ""}


def report(r):
    print(f"\n{'='*66}\n{r['이름']}\n{'='*66}")
    s = r["점수"]
    if s is None:
        print(f"  실행 실패: {r['에러']}")
        return
    print(f"  걸린 시간   {r['초']:.1f}초")
    if r["라운드"] is not None:
        print(f"  라운드      {r['라운드']}")
    print(f"  도구 호출   {r['도구호출']}")
    print(f"  정리 결과   {s['맞게 옮김']}/{s['총']}")
    if s["안 옮김"]:
        print(f"  안 옮긴 것  {s['안 옮김']}")
    if s["틀림"]:
        print(f"  잘못된 것  {s['틀림']}")
    if r["에러"].strip():
        print(f"  stderr 꼬리: {r['에러'].strip()[-300:]}")


def main():
    BENCH.mkdir(parents=True, exist_ok=True)
    args = [a for a in sys.argv[1:] if not a.startswith("-n")]
    trials = 1
    for a in sys.argv[1:]:
        if a.startswith("-n"):
            trials = int(a[2:] or 3)
    which = args or ["mine", "hermes"]

    # 한 번 돌린 결과로 결론 내지 않는다. 같은 과제·같은 모델인데도
    # 회차마다 결과가 뒤집히는 것을 15주차 judge에서 이미 겪었다.
    runs = {"내 agent.py": [], "Hermes": []}
    for t in range(1, trials + 1):
        print(f"\n{'#'*66}\n# {t}회차\n{'#'*66}")
        if "mine" in which:
            r = run_mine(); report(r); runs["내 agent.py"].append(r)
            (BENCH / f"mine_{t}.log").write_text(r["출력"], encoding="utf-8")
        if "hermes" in which:
            r = run_hermes(); report(r); runs["Hermes"].append(r)
            (BENCH / f"hermes_{t}.log").write_text(r["출력"], encoding="utf-8")

    print(f"\n{'='*66}\n{trials}회 종합\n{'='*66}")
    print(f"  {'':14}{'회차별 점수':>22}{'평균초':>9}{'평균도구':>9}")
    for name, rs in runs.items():
        if not rs:
            continue
        scores = [f"{r['점수']['맞게 옮김']}/{r['점수']['총']}" if r["점수"] else "X" for r in rs]
        avg_s = sum(r["초"] for r in rs) / len(rs)
        avg_t = sum(r["도구호출"] for r in rs) / len(rs)
        full = sum(1 for r in rs if r["점수"] and r["점수"]["맞게 옮김"] == r["점수"]["총"])
        print(f"  {name:14}{' '.join(scores):>22}{avg_s:>8.1f}초{avg_t:>9.1f}")
        print(f"  {'':14}완주 {full}/{len(rs)}회")
    print("\n  전문은 week17/bench/*_N.log")


if __name__ == "__main__":
    main()
