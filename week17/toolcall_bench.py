# 17주차: 왜 도구를 안 부르고 글로 쓰는가
#
# 실행: .\venv\Scripts\python week17\toolcall_bench.py
#
# 5회 비교 실습에서 2회가 "라운드 0"으로 끝났다. 모델이 도구 호출을
# 마크다운 코드블록으로 출력한 것이다. 의도도 인자도 맞는데 형식만 틀렸다.
#
# 1단계 tool_check.py에서 같은 모델이 4/4였다는 점이 단서다.
# 그때와 지금의 차이는 셋뿐이다.
#   - 시스템 프롬프트 유무
#   - 도구 개수 (3개 vs 5개)
#   - 과제의 복잡도 (단문 질문 vs 다단계 정리)
#
# 대화 이력은 아니다. compare.py가 매 회차 memory.json을 지우고 시작한다.
#
# 여기서는 시스템 프롬프트를 세 갈래로 갈라 어느 쪽이 범인인지 센다.

import re
import sys
import time
from pathlib import Path

from ollama import chat

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "week12"))

AGENT = (Path(__file__).resolve().parent.parent / "week12" / "agent.py").read_text(encoding="utf-8")
FULL = AGENT.split('SYSTEM = """')[1].split('"""')[0]

# 도구 호출 규칙 블록을 통째로 들어낸 판본 (대조군)
NO_STEPS = re.sub(r"도구를 호출할 때 지키는 것:.*?바로 도구를 호출한다\.\n\n", "", FULL, flags=re.S)
if NO_STEPS == FULL:   # 예전 문구도 받아준다
    NO_STEPS = re.sub(r"도구를 호출하기 전,.*?는 것은 아닌가\n\n", "", FULL, flags=re.S)

GOAL = ("week17/bench/probe 폴더를 정리해줘. 그 폴더 안에 문서, 사진, 기타 폴더를 만들고 "
        "파일을 종류에 맞게 옮겨줘. 문서는 txt/pdf/py, 사진은 jpg/png, 나머지는 기타로.")

CONDS = [
    ("프롬프트 없음", None),
    ("전체 프롬프트", FULL),
    ("단계별 지시 뺀 판", NO_STEPS),
]
MODELS = ["gemma4:e4b-it-qat", "qwen3.5:9b"]
N = 5

# 실제로 실행하지는 않는다. 도구 호출이 나오는지만 본다.
def list_files(folder: str) -> str:
    """지정한 폴더 안의 파일과 폴더 목록을 알려준다."""
    return "(측정용)"


def make_folder(path: str) -> str:
    """새 폴더를 만든다."""
    return "(측정용)"


def move_file(src: str, dst: str) -> str:
    """파일을 src에서 이미 존재하는 폴더 dst 안으로 옮긴다."""
    return "(측정용)"


def move_by_extension(folder: str, extensions: list, dest: str) -> str:
    """folder 아래에서 extensions에 해당하는 파일을 dest로 옮긴다."""
    return "(측정용)"


def search_rules(question: str) -> str:
    """사내 규정 질문일 때 관련 규정 조각을 찾아준다."""
    return "(측정용)"


TOOLS = [list_files, make_folder, move_file, move_by_extension, search_rules]
JSONISH = re.compile(r"```|\"tool[_ ]?name\"|\"toolName\"|\"arguments\"|\"parameters\"", re.I)


def trial(model, system):
    msgs = ([{"role": "system", "content": system}] if system else []) + \
           [{"role": "user", "content": GOAL}]
    t0 = time.time()
    try:
        r = chat(model=model, messages=msgs, tools=TOOLS)
    except Exception as e:
        return "오류", 0.0, str(e)[:60]
    sec = time.time() - t0
    if r.message.tool_calls:
        return "도구", sec, r.message.tool_calls[0].function.name
    body = (r.message.content or "").strip()
    kind = "글(JSON모양)" if JSONISH.search(body) else "글(서술)"
    return kind, sec, body[:50].replace("\n", " ")


if __name__ == "__main__":
    print(f"조건 {len(CONDS)}개 x 모델 {len(MODELS)}개 x {N}회\n")
    print("전체 프롬프트 길이:", len(FULL.encode()), "바이트")
    print("단계별 지시 뺀 판:", len(NO_STEPS.encode()), "바이트\n")

    rows = []
    for model in MODELS:
        for label, system in CONDS:
            got = []
            for i in range(N):
                kind, sec, detail = trial(model, system)
                got.append(kind)
                print(f"  {model:18} {label:16} {i+1}/{N}  {kind:12} {sec:5.1f}초  {detail[:40]}")
            ok = got.count("도구")
            rows.append((model, label, ok, got))
            print(f"  → {model} / {label}: 도구 호출 {ok}/{N}\n")

    print("=" * 68)
    print(f"  {'모델':20}{'조건':18}{'도구호출':>8}")
    print("=" * 68)
    for model, label, ok, got in rows:
        bar = "".join("O" if g == "도구" else "X" for g in got)
        print(f"  {model:20}{label:18}{ok:>4}/{N}   {bar}")
    print("\n  O = 진짜 tool_call / X = 본문에 글로 씀")
