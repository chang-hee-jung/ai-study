# 11주차: 내 비서 만들기 — 도구 확장 + 위험 도구 확인 장치
# 실행: .\venv\Scripts\python week11\assistant2.py
# 사전 조건: week08/db 인덱스가 있어야 함 (없으면 build_index.py 먼저)

import os
import shutil
from datetime import datetime

import chromadb
from ollama import chat, embed


# ── 기본 도구 (10주차에서 가져옴) ────────────────────────────────
def get_current_time() -> str:
    """현재 날짜와 시간을 알려준다."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def check_disk(drive: str) -> str:
    """지정한 드라이브의 전체 용량과 남은 용량을 GB 단위로 알려준다. drive는 'C', 'F' 같은 드라이브 문자."""
    total, used, free = shutil.disk_usage(f"{drive}:\\")
    return f"{drive} 드라이브: 전체 {total // 2**30}GB, 남음 {free // 2**30}GB"


def list_files(folder: str) -> str:
    """지정한 폴더 안의 파일과 폴더 목록을 알려준다. folder는 'F:/ai-study' 같은 경로."""
    return str(os.listdir(folder))


# ── 새 도구 1: 규정 검색 (week08 인덱스를 도구로 = Agentic RAG) ──
def search_rules(question: str) -> str:
    """사내 규정(근태, 휴가, 경비, 보안, 장비, 복지)에 대한 질문일 때 관련 규정 조각을 찾아준다."""
    client = chromadb.PersistentClient(path="week08/db")
    collection = client.get_collection("rules")
    q = embed(model="bge-m3", input=question)
    result = collection.query(query_embeddings=q.embeddings, n_results=2)
    chunks = result["documents"][0]
    return "\n---\n".join(chunks)


# ── 새 도구 2: 파일 읽기 (회의록 등 아무 텍스트나 읽어서 비서가 요약 가능) ──
def read_file(path: str) -> str:
    """텍스트 파일의 내용을 읽어준다. path는 'week06/sample_transcript.txt' 같은 경로."""
    with open(path, encoding="utf-8") as f:
        content = f.read()
    return content[:3000]  # 너무 긴 파일은 앞부분만 (토큰 보호)


# ── 새 도구 3: 파일 이동 — 위험! 실행 전 사용자 확인을 거친다 ──
def move_file(src: str, dst: str) -> str:
    """파일을 src 경로에서 dst 경로로 이동한다."""
    shutil.move(src, dst)
    return f"{src} → {dst} 이동 완료"


TOOLS = [get_current_time, check_disk, list_files, search_rules, read_file, move_file]
AVAILABLE = {f.__name__: f for f in TOOLS}   # 함수의 __name__으로 전화번호부 자동 생성

# 이 목록에 있는 도구는 실행 전 반드시 사용자에게 물어본다
DANGEROUS = {"move_file"}

SYSTEM = """너는 내 PC에서 돌아가는 개인 비서다. 반드시 한국어로만 답한다.
사내 규정 질문이면 search_rules 도구를 사용하고, 그 결과에 있는 내용만으로 답한다.
파일 내용이 필요하면 read_file로 읽는다. 도구가 거부되면 억지로 다시 시도하지 않는다."""

history = [{"role": "system", "content": SYSTEM}]

while True:
    user_input = input("나: ")
    if user_input.lower() == "/bye":
        break
    history.append({"role": "user", "content": user_input})

    response = chat(model="qwen2.5:7b", messages=history, tools=TOOLS)

    if response.message.tool_calls:
        history.append(response.message)
        for call in response.message.tool_calls:
            name = call.function.name
            args = call.function.arguments

            # ── 확인 장치: 위험한 도구는 실행 전에 사용자 승인 ──
            if name in DANGEROUS:
                ok = input(f"  ⚠ {name}{dict(args)} 실행할까요? (y/n): ")
                if ok.lower() != "y":
                    result = "사용자가 실행을 거부했습니다."
                    print(f"  (도구 거부: {name})")
                    history.append({"role": "tool", "name": name, "content": result})
                    continue

            fn = AVAILABLE[name]
            result = fn(**args)
            print(f"  (도구 실행: {name})")
            history.append({"role": "tool", "name": name, "content": result})
        response = chat(model="qwen2.5:7b", messages=history, tools=TOOLS)

    answer = response.message.content
    print("봇:", answer)
    history.append({"role": "assistant", "content": answer})
