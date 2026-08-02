# 12주차: 멀티스텝 에이전트 (마일스톤 3 — 피날레)
# 사용법: .\venv\Scripts\python week12\agent.py "목표를 여기에"
#
# 챗봇과 에이전트의 경계선 = if를 while로:
#   챗봇:     도구 1번 쓰고 답한다
#   에이전트: 도구 결과를 보고 다음 도구를 스스로 결정, 완료까지 반복한다

import os
import sys
import shutil

import chromadb
from ollama import chat, embed

if len(sys.argv) < 2:
    print('사용법: python week12\\agent.py "목표"')
    sys.exit(1)

goal = sys.argv[1]


# ── 도구들 ──────────────────────────────────────────────────────
last_folder = None  # 검증용: 모델이 마지막으로 조회한 폴더를 코드가 기억해둔다


def list_files(folder: str) -> str:
    """지정한 폴더 안의 파일과 폴더 목록을 알려준다. folder는 'week12/testbed' 같은 경로."""
    global last_folder
    last_folder = folder
    return str(os.listdir(folder))


def leftover_files(folder: str) -> list:
    """폴더 바로 아래 남아있는 파일(하위 폴더 제외) 목록 — 정리가 덜 끝났다는 코드 차원의 증거."""
    return [e for e in os.listdir(folder) if os.path.isfile(os.path.join(folder, e))]


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


def search_rules(question: str) -> str:
    """사내 규정(근태, 휴가, 경비, 보안, 장비, 복지)에 대한 질문일 때 관련 규정 조각을 찾아준다."""
    client = chromadb.PersistentClient(path="week08/db")
    collection = client.get_collection("rules")
    q = embed(model="bge-m3", input=question)
    result = collection.query(query_embeddings=q.embeddings, n_results=2)
    chunks = result["documents"][0]
    return "\n---\n".join(chunks)


TOOLS = [list_files, make_folder, move_file, search_rules]
AVAILABLE = {f.__name__: f for f in TOOLS}
DANGEROUS = {"move_file"}

MAX_ROUNDS = 8   # 폭주 방지: 도구 라운드 상한

SYSTEM = """너는 파일 정리와 사내 규정 안내를 수행하는 에이전트다. 반드시 한국어로만 답한다.
폴더와 파일 이름은 목표에 적힌 한국어 이름을 한 글자도 바꾸지 말고 그대로 사용한다.

규정(근태, 휴가, 경비, 보안, 장비, 복지) 관련 질문이면 search_rules 도구로 먼저 검색하고,
검색 결과에 있는 내용만으로 답한다. 검색 결과에 없는 내용은 절대 지어내지 않고
"규정에서 찾을 수 없습니다"라고 답한다.

도구를 호출하기 전, 매번 다음을 스스로 단계별로 따져본다:
1. 지금까지 도구 결과에서 실제로 확인된 사실이 무엇인가 (추측하지 않는다)
2. 이번에 쓸 도구의 인자가 목표 문장의 한국어 이름과 글자 하나까지 일치하는가
3. 직전 라운드에서 에러가 있었다면, 같은 호출을 반복하는 것은 아닌가

목표를 받으면: 먼저 현재 상태를 도구로 확인하고, 위 점검을 거쳐 계획을 세우고, 도구를 차례로 사용해 완료한다.
도구에서 에러가 나면 같은 호출을 반복하지 말고, list_files로 현재 상태를 다시 확인한 뒤 계획을 수정한다.
도구 실행이 거부되면 그 파일은 건너뛰고 계속한다.
최종 보고 전에는 반드시 list_files로 실제 상태를 다시 확인해, 목표에 적힌 모든 항목이 실제로 처리됐는지 대조한 뒤 보고한다. 처리 못한 항목이 있으면 숨기지 말고 명시한다."""

history = [
    {"role": "system", "content": SYSTEM},
    {"role": "user", "content": goal},
]

# ── 모델 에스컬레이션: 7B로 시작, 애매하거나 실패하면 14B로 전환 ──
model = "qwen2.5:7b"
ESCALATION_MODEL = "qwen2.5:14b"
escalated = False
last_error_key = None  # (도구명, 인자) — 같은 실패가 반복되는지 코드로 감시


def escalate(reason: str):
    global model, escalated
    if not escalated:
        print(f"\n[에스컬레이션] {reason} → {ESCALATION_MODEL}로 전환")
        model = ESCALATION_MODEL
        escalated = True


response = chat(model=model, messages=history, tools=TOOLS)

rounds = 0
verify_used = False  # 검증 재요청은 한 번만 — 계속 우기면 무한루프가 되므로
# ── 에이전트 루프: 도구 요청이 없어질 때까지 반복 ────────────────
while rounds < MAX_ROUNDS:
    if response.message.tool_calls:
        rounds = rounds + 1
        print(f"\n── 라운드 {rounds} (모델: {model}) ──")
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

            # 같은 도구를 같은 인자로 불렀는데 또 에러 → 7B가 헤매는 중, 전환
            error_key = (name, tuple(sorted(args.items()))) if result.startswith("에러 발생") else None
            if error_key is not None and error_key == last_error_key:
                escalate("같은 에러 반복")
            last_error_key = error_key

        response = chat(model=model, messages=history, tools=TOOLS)
        continue

    # 모델이 도구 호출을 멈췄다 = "끝났다"는 주장. 말로만 믿지 않고 코드로 재확인한다
    if not verify_used and last_folder:
        remaining = leftover_files(last_folder)
        if remaining:
            print(f"\n[검증] 모델은 끝났다고 했지만 {last_folder}에 미정리 파일 발견: {remaining} — 이어서 진행시킨다")
            escalate("검증 실패(미완료를 완료로 보고)")
            history.append({
                "role": "user",
                "content": f"검증 결과 {last_folder}에 아직 처리 안 된 파일이 남아있다: {remaining}. 계속 정리하라.",
            })
            response = chat(model=model, messages=history, tools=TOOLS)
            verify_used = True
            continue

    break

if rounds >= MAX_ROUNDS:
    print("\n(반복 상한 도달 — 강제 종료)")

print("\n=== 최종 보고 (모델) ===")
print(response.message.content)

# ── 검증 레이어: 모델의 말이 아니라 코드가 실제 상태로 판정한다 ──
if last_folder:
    remaining = leftover_files(last_folder)
    if remaining:
        print(f"\n[검증 결과: 미완료] {last_folder}에 아직 남은 파일: {remaining}")
    else:
        print(f"\n[검증 결과: 완료] {last_folder}에 미정리 파일 없음")
