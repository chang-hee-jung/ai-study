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


def world_state(folder):
    """폴더 트리의 스냅샷. 이게 변하면 진도가 나간 것이다.

    "진도"를 모델의 말이 아니라 디스크로 판정하기 위한 것이다.
    모델이 아무리 열심히 설명해도 트리가 그대로면 진도는 0이다.
    """
    if not folder or not os.path.isdir(folder):
        return None
    return tuple((r, tuple(sorted(d)), tuple(sorted(f)))
                 for r, d, f in os.walk(folder))


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
    설치 파일처럼 확장자만으로 판단해도 되는 대량 정리에 쓴다.
    dest는 미리 make_folder로 만들어져 있어야 한다."""
    # 원래는 os.makedirs(dest, exist_ok=True) 였다. 그런데 17주차 실험에서
    # 모델이 경로에서 'bench'를 빠뜨려 'week17/mine/사진'을 넘겼는데,
    # 이 줄이 그 폴더를 새로 만들어버려 에러 없이 엉뚱한 곳으로 옮겼다.
    # move_file에는 12주차 사고 뒤 같은 방어를 넣었는데 이 도구는 빠져 있었다.
    if not os.path.isdir(dest):
        return (f"에러: {dest} 폴더가 존재하지 않는다. "
                f"list_files로 실제 폴더 이름을 확인하고 make_folder로 먼저 만들어라.")
    if not os.path.isdir(folder):
        return f"에러: {folder} 폴더가 존재하지 않는다. list_files로 확인하라."
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

# ── 폭주 방지 ─────────────────────────────────────────────────
# 원래는 MAX_ROUNDS = 8 하나로 잘랐다. 그런데 17주차 비교 실습에서
# 실수를 한 번도 안 한 에이전트가 8라운드에서 잘렸다.
#   1(조회) + 3(폴더 생성) + 4(이동) = 8   ← 파일 3개 남기고 강제 종료
# 라운드는 "얼마나 오래 걸리는가"이지 "잘못 가고 있는가"가 아니다.
# 상한이 건강한 진행을 벌한 것이다.
#
# Hermes의 tool_loop_guardrails를 보고 기준을 바꿨다. 라운드가 아니라
# 병적인 신호 세 가지를 센다. 진도가 나가면 카운터를 0으로 되돌린다.
#   exact_failure     같은 도구를 같은 인자로 불러서 또 실패
#   same_tool_failure 같은 도구가 인자를 바꿔가며 계속 실패
#   no_progress       도구를 불렀는데 폴더 상태가 그대로
WARN_AT = {"exact_failure": 2, "same_tool_failure": 3, "no_progress": 4}
STOP_AT = {"exact_failure": 5, "same_tool_failure": 8, "no_progress": 8}

# no_progress만 Hermes 기본값(경고 2 / 중단 5)보다 느슨하게 잡았다.
# 내 SYSTEM 프롬프트가 "최종 보고 전에 list_files로 다시 확인하라"고 시키기
# 때문이다. 목적지 폴더 3~4개를 훑는 동안은 폴더가 안 변하는 게 정상인데,
# 2에서 경고하면 올바르게 검증하는 에이전트에게 "조회만 반복하지 말라"고
# 잔소리하게 된다. 범용 기본값은 내 프롬프트 사정을 모른다.

# 진짜 무한루프에 대비한 최후의 벽. 정상 작업이 여기 닿을 일은 없다.
HARD_CEILING = 100

# 17주차 교체: qwen3:8b는 이 PC에서 정리되어 없어졌는데 코드가 따라가지 않아
# 조용히 404가 나고 있었다. week17/tool_check.py로 다시 재서 1등을 앉혔다.
# (도구 호출 4/4, VRAM도 제일 가벼움)
BASE_MODEL = "gemma4:e4b-it-qat"
ESCALATION_MODEL = "qwen3:14b"

# 파이프로 실행할 때는 승인 프롬프트에 답할 사람이 없다. 벤치마크처럼
# 무인으로 돌릴 때만 1로 켠다. 기본은 꺼져 있어야 안전하다.
AUTO_APPROVE = os.environ.get("AGENT_AUTO_APPROVE") == "1"

SYSTEM = """너는 파일 정리와 사내 규정 안내를 겸하는 개인 비서 에이전트다. 반드시 한국어로만 답한다.
폴더와 파일 이름은 사용자가 말한 한국어 이름을 한 글자도 바꾸지 말고 그대로 사용한다.

규정(근태, 휴가, 경비, 보안, 장비, 복지) 관련 질문이면 search_rules 도구로 먼저 검색하고,
검색 결과에 있는 내용만으로 답한다. 검색 결과에 없는 내용은 절대 지어내지 않고
"규정에서 찾을 수 없습니다"라고 답한다.

파일 정리나 사내 규정과 무관한 일반적인 질문·잡담도 편하게 받아준다. 이때는 도구를 억지로
쓰지 않고 네가 아는 대로 답하되, 최신 정보나 실시간 정보(오늘 날짜, 현재 시각, 최근 뉴스,
현직 인물 등)처럼 학습 시점 이후 바뀌었을 수 있는 내용은 "학습 데이터 기준이라 최신 정보가
아닐 수 있다"고 먼저 밝히고 답한다.

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

    # 새 목표는 항상 작은 모델로 새로 시작 — 이전 목표의 에스컬레이션을 물려받지 않는다
    model = BASE_MODEL
    escalated = False
    last_error_key = None
    verify_used = False
    rounds = 0
    counters = {"exact_failure": 0, "same_tool_failure": 0, "no_progress": 0}
    warned = set()
    stop_reason = None
    # 진도를 잴 기준 폴더. 목표 하나당 한 번만 정한다.
    # last_folder를 그대로 쓰면 list_files가 하위 폴더를 조회할 때마다 값이
    # 바뀌어, 라운드 전후로 '서로 다른 폴더'를 비교하게 된다. 그러면 언제나
    # "달라졌다"가 나와서 no_progress가 영원히 0이다 (실제로 그 버그가 있었다).
    watch_folder = None

    response = chat(model=model, messages=history, tools=TOOLS)

    # ── 에이전트 루프: 도구 요청이 없어질 때까지 반복 ────────────────
    while rounds < HARD_CEILING:
        if response.message.tool_calls:
            rounds = rounds + 1
            watch = watch_folder          # 이번 라운드 내내 같은 폴더를 본다
            before = world_state(watch)
            round_failed = []
            print(f"\n── 라운드 {rounds} (모델: {model}) ──")
            history.append(response.message)

            for call in response.message.tool_calls:
                name = call.function.name
                args = call.function.arguments

                if name in DANGEROUS and not AUTO_APPROVE:
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

                failed = result.startswith("에러 발생") or result.startswith("에러:")
                error_key = (name, tuple(sorted(args.items()))) if failed else None
                if failed:
                    round_failed.append(name)
                    # 같은 도구를 같은 인자로 불렀는데 또 실패 = 제자리걸음
                    if error_key == last_error_key:
                        counters["exact_failure"] += 1
                        escalate("같은 호출로 반복 실패")
                last_error_key = error_key

            # ── 병적인 신호를 센다 (라운드 수가 아니라) ──────────────
            counters["same_tool_failure"] = (
                counters["same_tool_failure"] + 1 if round_failed else 0)

            # 첫 조회 폴더를 감시 대상으로 고정한다. os.walk가 재귀라
            # 그 아래 어디가 바뀌어도 잡힌다.
            if watch_folder is None and last_folder:
                watch_folder = last_folder

            after = world_state(watch)
            if before is not None and after == before:
                # 도구를 불렀는데 폴더가 그대로다. 조회만 반복하는 경우도 여기 걸린다.
                counters["no_progress"] += 1
            elif after != before:
                # 진도가 나갔다. 카운터를 전부 되돌린다.
                # 이것이 라운드 상한과의 결정적 차이다 — 오래 걸려도 벌하지 않는다.
                counters = {k: 0 for k in counters}
                warned.clear()

            # 경고: 끊지 않고 모델에게 알려 방향을 바꿀 기회를 준다
            NUDGE = {
                "exact_failure": "같은 도구를 같은 인자로 반복 호출해 계속 실패하고 있다. 인자를 다시 확인하라.",
                "same_tool_failure": "도구 호출이 연달아 실패하고 있다. list_files로 현재 상태를 먼저 확인하라.",
                "no_progress": "도구를 불렀지만 폴더 상태가 전혀 변하지 않았다. 조회만 반복하지 말고 실제 작업을 하라.",
            }
            for k, v in counters.items():
                if WARN_AT[k] <= v < STOP_AT[k] and k not in warned:
                    warned.add(k)
                    print(f"  [경고] {k} {v}회 — 모델에게 알린다")
                    history.append({"role": "user", "content": f"[시스템 경고] {NUDGE[k]}"})
                    escalate(f"{k} {v}회")

            stop_reason = next((f"{k} {v}회" for k, v in counters.items()
                                if v >= STOP_AT[k]), None)
            if stop_reason:
                break

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

    if stop_reason:
        print(f"\n(중단: {stop_reason} — 병적인 반복으로 판단해 끊었다)")
    elif rounds >= HARD_CEILING:
        print(f"\n(중단: 라운드 {HARD_CEILING}회 — 최후의 벽에 닿았다)")

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
