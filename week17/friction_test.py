# -*- coding: utf-8 -*-
"""스킬까지 뽑아내는 세션.

메모리는 1차 마찰 실험에서 나왔다. 스킬은 기준이 더 높다 —
리뷰 프롬프트가 요구하는 것:
  · class-level 이름 (세션 한 번짜리 이름은 거부)
  · 기존 스킬 패치를 우선하는데, 70개가 전부 번들이라 손댈 수 없음
    → 새로 만드는 길밖에 없다

그래서 교정을 "이 폴더에서"가 아니라 "앞으로 모든 이런 작업에서"로
일반화해서 준다. 그리고 매 턴 bg-review가 완주하도록 turn.py로 돌린다.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

HOME = Path(os.environ["LOCALAPPDATA"]) / "hermes"
TURN = Path(__file__).with_name("turn.py")
PY = HOME / "hermes-agent" / "venv" / "Scripts" / "python.exe"
WORK = r"F:\ai-study"

TURNS = [
    "week17/bench/G1 폴더를 정리해줘.",

    # 스타일 교정 — 프롬프트가 'FIRST-CLASS skill signal'로 명시한 항목
    "설명이 너무 장황하다. 과정 나열하지 말고 결과만 한 줄로 말해라. "
    "앞으로 나와 하는 모든 작업에서 이 방식을 지켜라.",

    # 작업 방식 교정 — class-level로 일반화
    "그리고 순서가 틀렸다. 파일 정리 작업은 항상 이 순서로 해라: "
    "①ls로 현재 상태 확인 ②폴더 생성 ③파일 이동 ④ls로 결과 재확인. "
    "확인 없이 옮기지 마라. 이건 모든 파일 정리 작업에 적용되는 규칙이다.",

    "week17/bench/G2 폴더를 정리해줘.",

    # 도메인 규칙 — 12주차 사고에서 나온 그것
    "한글 폴더명을 영어로 바꾸지 마라. '문서'를 documents로, '사진'을 photos로 "
    "옮기면 안 된다. 사용자가 쓴 글자를 한 글자도 바꾸지 않는다. "
    "이건 앞으로 모든 작업에 예외 없이 적용된다.",

    "week17/bench/G3 폴더를 정리해줘. 지금까지 지적한 것 전부 지켜라.",

    # 명시적 학습 요청 — 프롬프트가 "explicit 'remember this'"를 first-class로 침
    "지금까지 내가 지적한 규칙들을 앞으로 같은 종류의 작업에서 계속 쓸 수 있게 "
    "정리해둬라. 다음에 비슷한 일을 시킬 때 이걸 다시 물어보지 않아도 되게 해라.",
]


def skills_now():
    return {str(p) for p in (HOME / "skills").rglob("*") if p.is_file()}


def mem_now():
    d = HOME / "memories"
    return {str(p) for p in d.rglob("*") if p.is_file()} if d.exists() else set()


if __name__ == "__main__":
    sys.path.insert(0, os.path.join(WORK, "week17"))
    from make_testbed import build
    for n in ("G1", "G2", "G3"):
        build(n)

    base_sk, base_mem = skills_now(), mem_now()
    print(f"시작 — 스킬 {len(base_sk)} / 메모리 {len(base_mem)}\n")

    sid = "-"
    for i, t in enumerate(TURNS, 1):
        r = subprocess.run([str(PY), str(TURN), sid, t], capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=600, cwd=WORK)
        out = (r.stdout or "") + (r.stderr or "")
        m = re.search(r"Session:\s+(\S+)", out)
        if m:
            sid = m.group(1)
        bg = "완주" if "bg-review 완주" in out else ("미완" if "bg-review" in out else "-")
        sk, mem = skills_now(), mem_now()
        print(f"[{i}/{len(TURNS)}] bg:{bg:4}  스킬+{len(sk-base_sk)}  메모리+{len(mem-base_mem)}"
              f"  | {t[:34]}...")
        for p in sorted(sk - base_sk)[-3:]:
            print(f"          + {os.path.relpath(p, HOME)}")

    print(f"\n세션: {sid}")
