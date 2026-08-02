# 12주차+보너스: 지속 대화형 멀티스텝 에이전트 (week05 보너스 완성 — 챗봇 루프 + 에이전트 통합)
# 실행: .\venv\Scripts\python week12\agent.py
# 대화하듯 여러 목표를 이어서 맡긴다. 종료: /bye
#
# 챗봇과 에이전트의 경계선 = if를 while로:
#   챗봇:     도구 1번 쓰고 답한다
#   에이전트: 도구 결과를 보고 다음 도구를 스스로 결정, 완료까지 반복한다
# 이 파일은 그 반복을 "목표 하나"의 단위로 두고, 바깥에 대화 루프를 씌운 것이다.

import os
import json
import shutil

import chromadb
from ollama import chat, embed

MEMORY_FILE = "week12/memory.json"


def to_plain(entry):
    """ollama Message 객체든 dict든, JSON으로 저장 가능한 dict로 통일한다."""
    if isinstance(entry, dict):
        return entry
    d = {"role": entry.role, "content": entry.content or ""}
    if entry.tool_calls:
        d["tool_calls"] = [
            {"function": {"name": c.function.name, "arguments": dict(c.function.arguments)}}
            for c in entry.tool_calls
        ]
    return d


def load_memory() -> list:
    """지난 실행의 대화(system 프롬프트 제외)를 불러온다. 없으면 빈 대화로 시작."""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_memory(conversation: list):
    """system 프롬프트를 뺀 대화 부분만 저장한다 — 코드에서 프롬프트를 고쳐도 옛 메모리가 덮어쓰지 않도록."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump([to_plain(m) for m in conversation], f, ensure_ascii=False, indent=2)


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


def move_by_extension(folder: str, extensions: list, dest: str) -> str:
    """folder 바로 아래에서 extensions(예: ['exe','msi'])에 해당하는 파일을 전부 dest 폴더로 옮긴다.
    설치 파일처럼 확장자만으로 판단해도 되는 대량 정리에 쓴다. dest가 없으면 새로 만든다."""
    os.makedirs(dest, exist_ok=True)
    exts = {e.lower().lstrip(".") for e in extensions}
    moved, total_bytes = [], 0
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        if os.path.isfile(path) and name.rsplit(".", 1)[-1].lower() in exts:
            total_bytes += os.path.getsize(path)
            shutil.move(path, dest)
            moved.append(name)
    gb = total_bytes / (1024 ** 3)
    return f"{len(moved)}개 파일({gb:.2f}GB)을 {dest}로 이동 완료"


def search_rules(question: str) -> str:
    """사내 규정(근태, 휴가, 경비, 보안, 장비, 복지)에 대한 질문일 때 관련 규정 조각을 찾아준다."""
    client = chromadb.PersistentClient(path="week08/db")
    collection = client.get_collection("rules")
    q = embed(model="bge-m3", input=question)
    result = collection.query(query_embeddings=q.embeddings, n_results=2)
    chunks = result["documents"][0]
    return "\n---\n".join(chunks)


TOOLS = [list_files, make_folder, move_file, move_by_extension, search_rules]
AVAILABLE = {f.__name__: f for f in TOOLS}
DANGEROUS = {"move_file", "move_by_extension"}

MAX_ROUNDS = 8   # 폭주 방지: 목표 하나당 도구 라운드 상한

BASE_MODEL = "qwen2.5:7b"
ESCALATION_MODEL = "qwen2.5:14b"

SYSTEM = """너는 파일 정리와 사내 규정 안내를 수행하는 개인 비서 에이전트다. 반드시 한국어로만 답한다.
폴더와 파일 이름은 사용자가 말한 한국어 이름을 한 글자도 바꾸지 말고 그대로 사용한다.

규정(근태, 휴가, 경비, 보안, 장비, 복지) 관련 질문이면 search_rules 도구로 먼저 검색하고,
검색 결과에 있는 내용만으로 답한다. 검색 결과에 없는 내용은 절대 지어내지 않고
"규정에서 찾을 수 없습니다"라고 답한다.

도구를 호출하기 전, 매번 다음을 스스로 단계별로 따져본다:
1. 지금까지 도구 결과에서 실제로 확인된 사실이 무엇인가 (추측하지 않는다)
2. 이번에 쓸 도구의 인자가 사용자가 말한 한국어 이름과 글자 하나까지 일치하는가
3. 직전 라운드에서 에러가 있었다면, 같은 호출을 반복하는 것은 아닌가

목표를 받으면: 먼저 현재 상태를 도구로 확인하고, 위 점검을 거쳐 계획을 세우고, 도구를 차례로 사용해 완료한다.
도구에서 에러가 나면 같은 호출을 반복하지 말고, list_files로 현재 상태를 다시 확인한 뒤 계획을 수정한다.
도구 실행이 거부되면 그 파일은 건너뛰고 계속한다.
최종 보고 전에는 반드시 list_files로 실제 상태를 다시 확인해, 목표에 적힌 모든 항목이 실제로 처리됐는지 대조한 뒤 보고한다. 처리 못한 항목이 있으면 숨기지 말고 명시한다."""

past = load_memory()
history = [{"role": "system", "content": SYSTEM}] + past
if past:
    print(f"[메모리] 이전 대화 {len(past)}개 메시지를 불러왔다")

# ── 모델 에스컬레이션: 목표마다 7B로 시작, 애매하거나 실패하면 14B로 전환 ──
model = BASE_MODEL
escalated = False


def escalate(reason: str):
    global model, escalated
    if not escalated:
        print(f"\n[에스컬레이션] {reason} → {ESCALATION_MODEL}로 전환")
        model = ESCALATION_MODEL
        escalated = True


print("에이전트 비서 시작. 목표나 질문을 말해줘. 끝내려면 /bye")

# ── 대화 루프: 목표 하나마다 아래 에이전트 루프를 새로 돈다 ──────────
while True:
    user_input = input("\n나: ")
    if user_input.lower() == "/bye":
        print(f"[메모리] {MEMORY_FILE}에 저장됨 — 다음 실행 때 이어서 기억한다")
        break
    history.append({"role": "user", "content": user_input})

    # 새 목표는 항상 7B(손발)로 새로 시작 — 이전 목표의 에스컬레이션을 물려받지 않는다
    model = BASE_MODEL
    escalated = False
    last_error_key = None
    verify_used = False
    rounds = 0

    response = chat(model=model, messages=history, tools=TOOLS)

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
        print("\n(반복 상한 도달 — 이번 목표는 강제 종료)")

    history.append(response.message)  # 최종 답도 이력에 남겨야 다음 턴이 기억한다
    print(f"\n봇: {response.message.content}")

    save_memory(history[1:])  # system 프롬프트(history[0])는 저장하지 않는다

    # ── 검증 레이어: 모델의 말이 아니라 코드가 실제 상태로 판정한다 ──
    if last_folder:
        remaining = leftover_files(last_folder)
        if remaining:
            print(f"[검증 결과: 미완료] {last_folder}에 아직 남은 파일: {remaining}")
        else:
            print(f"[검증 결과: 완료] {last_folder}에 미정리 파일 없음")
