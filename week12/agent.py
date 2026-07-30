# 12주차: 멀티스텝 에이전트 (마일스톤 3 — 피날레)
# 사용법: .\venv\Scripts\python week12\agent.py "목표를 여기에"
#
# 챗봇과 에이전트의 경계선 = if를 while로:
#   챗봇:     도구 1번 쓰고 답한다
#   에이전트: 도구 결과를 보고 다음 도구를 스스로 결정, 완료까지 반복한다

import os
import sys
import shutil

from ollama import chat

if len(sys.argv) < 2:
    print('사용법: python week12\\agent.py "목표"')
    sys.exit(1)

goal = sys.argv[1]


# ── 도구들 ──────────────────────────────────────────────────────
def list_files(folder: str) -> str:
    """지정한 폴더 안의 파일과 폴더 목록을 알려준다. folder는 'week12/testbed' 같은 경로."""
    return str(os.listdir(folder))


def make_folder(path: str) -> str:
    """새 폴더를 만든다. 이미 있으면 그냥 넘어간다. path는 'week12/testbed/문서' 같은 경로."""
    os.makedirs(path, exist_ok=True)
    return f"{path} 폴더 준비됨"


def move_file(src: str, dst: str) -> str:
    """파일을 src 경로에서, 이미 존재하는 폴더 dst 안으로 이동한다."""
    # 방어 설계: 목적지 폴더가 없으면 이동 대신 개명 사고가 나므로 미리 차단
    if not os.path.isdir(dst):
        return f"에러: {dst} 폴더가 존재하지 않는다. list_files로 실제 폴더 이름을 확인하라."
    shutil.move(src, dst)
    return f"{src} → {dst} 이동 완료"


TOOLS = [list_files, make_folder, move_file]
AVAILABLE = {f.__name__: f for f in TOOLS}
DANGEROUS = {"move_file"}

MAX_ROUNDS = 8   # 폭주 방지: 도구 라운드 상한

SYSTEM = """너는 파일 정리를 수행하는 에이전트다. 반드시 한국어로만 답한다.
폴더와 파일 이름은 목표에 적힌 한국어 이름을 한 글자도 바꾸지 말고 그대로 사용한다.
목표를 받으면: 먼저 현재 상태를 도구로 확인하고, 계획을 세우고, 도구를 차례로 사용해 완료한다.
도구에서 에러가 나면 같은 호출을 반복하지 말고, list_files로 현재 상태를 다시 확인한 뒤 계획을 수정한다.
도구 실행이 거부되면 그 파일은 건너뛰고 계속한다.
모든 작업이 끝나면 무엇을 했는지 최종 보고를 한다."""

history = [
    {"role": "system", "content": SYSTEM},
    {"role": "user", "content": goal},
]

response = chat(model="qwen2.5:7b", messages=history, tools=TOOLS)

rounds = 0
# ── 에이전트 루프: 도구 요청이 없어질 때까지 반복 ────────────────
while response.message.tool_calls and rounds < MAX_ROUNDS:
    rounds = rounds + 1
    print(f"\n── 라운드 {rounds} ──")
    history.append(response.message)

    for call in response.message.tool_calls:
        name = call.function.name
        args = call.function.arguments

        if name in DANGEROUS:
            ok = input(f"  ⚠ {name}{dict(args)} 실행? (y/n): ")
            if ok.lower() != "y":
                print(f"  (거부: {name})")
                history.append({"role": "tool", "name": name, "content": "사용자가 거부했습니다. 이 파일은 건너뛴다."})
                continue

        fn = AVAILABLE[name]
        try:
            result = fn(**args)
        except Exception as e:
            result = f"에러 발생: {e}"
        print(f"  {name}{dict(args)} → {result}")
        history.append({"role": "tool", "name": name, "content": result})

    response = chat(model="qwen2.5:7b", messages=history, tools=TOOLS)

if rounds >= MAX_ROUNDS:
    print("\n(반복 상한 도달 — 강제 종료)")

print("\n=== 최종 보고 ===")
print(response.message.content)
