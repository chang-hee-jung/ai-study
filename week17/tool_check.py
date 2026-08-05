# 17주차 1단계: 모델별 도구 호출 능력 측정
#
# 실행: .\venv\Scripts\python week17\tool_check.py
#       .\venv\Scripts\python week17\tool_check.py qwen3:8b llama3.1:8b   (일부만)
#
# 왜 먼저 재는가.
# 에이전트 프레임워크는 도구 호출 위에 서 있다. 모델이 도구를 제대로 못 부르면
# 아무리 좋은 하네스를 얹어도 안 돈다. 붙이고 나서 안 되면 하네스 문제인지
# 모델 문제인지 구분이 안 되므로, 붙이기 전에 모델 쪽을 먼저 확정해둔다.
#
# 채점은 4가지를 본다.
#   1. 도구를 부르는가
#   2. 맞는 도구를 고르는가
#   3. 인자를 정확히 넘기는가 (한글 이름을 안 바꾸는가 - 12주차 대참사의 그 항목)
#   4. 도구가 필요없는 질문에 억지로 부르지 않는가

import sys
import time

from ollama import chat

# ── 시험용 도구 (실제로 실행하지 않는다. 호출 형태만 본다) ──────────────


def list_files(folder: str) -> str:
    """지정한 폴더 안의 파일과 폴더 목록을 알려준다. folder는 'week17' 같은 경로."""
    return "(측정용이라 실행하지 않음)"


def make_folder(path: str) -> str:
    """새 폴더를 만든다. path는 'week17/자료' 같은 경로."""
    return "(측정용이라 실행하지 않음)"


def get_weather(city: str) -> str:
    """도시의 현재 날씨를 알려준다."""
    return "(측정용이라 실행하지 않음)"


TOOLS = [list_files, make_folder, get_weather]

# (설명, 질문, 기대 도구, 기대 인자)  기대 도구가 None이면 "도구를 쓰면 안 됨"
CASES = [
    ("기본 호출",
     "week17 폴더에 뭐가 들어있는지 알려줘",
     "list_files", {"folder": "week17"}),

    ("한글 인자 보존",
     "week17 안에 '실습자료' 라는 폴더를 만들어줘",
     "make_folder", {"path": "week17/실습자료"}),

    ("도구 선택",
     "서울 날씨 어때?",
     "get_weather", {"city": "서울"}),

    ("과잉 호출 억제",
     "파이썬에서 리스트와 튜플의 차이가 뭐야?",
     None, None),
]

DEFAULT_MODELS = ["qwen3:8b", "qwen2.5:7b", "llama3.1:8b",
                  "qwen3:14b", "gemma4:e4b-it-qat"]


def norm(v):
    """인자 비교용: 경로 구분자와 따옴표 차이는 같은 것으로 본다."""
    return str(v).replace("\\", "/").strip().strip("'\"")


def judge(resp, want_tool, want_args):
    """한 문항을 채점해 (기호, 설명)을 돌려준다."""
    calls = resp.message.tool_calls

    if want_tool is None:                       # 도구를 쓰면 안 되는 문항
        if not calls:
            return "O", "도구 안 씀"
        return "X", f"불필요하게 {calls[0].function.name} 호출"

    if not calls:
        return "X", "도구를 안 부름"

    got = calls[0].function.name
    if got != want_tool:
        return "X", f"{got} 호출 (기대: {want_tool})"

    args = dict(calls[0].function.arguments)
    for k, want in want_args.items():
        if k not in args:
            return "-", f"인자 {k} 누락"
        if norm(args[k]) != norm(want):
            return "-", f"{k}={args[k]!r} (기대: {want!r})"
    return "O", "정확"


def run(model):
    print(f"\n{'='*62}\n{model}\n{'='*62}")
    score, total_sec = 0, 0.0

    for label, question, want_tool, want_args in CASES:
        t0 = time.time()
        try:
            resp = chat(model=model, messages=[{"role": "user", "content": question}],
                        tools=TOOLS, think=False)
        except Exception as e:
            msg = str(e)
            # 도구를 지원하지 않는 모델은 여기서 걸린다. 그것도 결과다.
            if "does not support tools" in msg or "tools" in msg.lower():
                print(f"  [{label}] 도구 미지원 — {msg[:70]}")
                continue
            # think 인자를 모르는 구버전 모델은 빼고 재시도
            try:
                resp = chat(model=model, messages=[{"role": "user", "content": question}],
                            tools=TOOLS)
            except Exception as e2:
                print(f"  [{label}] 실패 — {str(e2)[:70]}")
                continue

        sec = time.time() - t0
        total_sec += sec
        mark, why = judge(resp, want_tool, want_args)
        if mark == "O":
            score += 1
        print(f"  [{mark}] {label:12} {sec:5.1f}초  {why}")

    print(f"  → {score}/{len(CASES)}   총 {total_sec:.1f}초")
    return model, score, total_sec


if __name__ == "__main__":
    models = sys.argv[1:] or DEFAULT_MODELS
    print("도구 호출 능력 측정 — O 정확 / - 도구는 맞고 인자가 틀림 / X 틀림")
    print("(첫 호출은 모델을 VRAM에 올리는 시간이 포함되어 느리다)")

    results = [run(m) for m in models]

    print(f"\n{'='*62}\n요약\n{'='*62}")
    print(f"  {'모델':22}{'점수':>6}{'시간':>10}")
    for m, s, t in sorted(results, key=lambda r: (-r[1], r[2])):
        print(f"  {m:22}{s:>4}/{len(CASES)}{t:>8.1f}초")
    print("\n에이전트에 쓸 모델은 점수부터 보고 고른다. 속도는 그다음이다.")
