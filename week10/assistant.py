# 10주차: 도구 쓰는 챗봇 — 3주차(루프+이력) + 5주차(도구)의 합체
# 실행: .\venv\Scripts\python week10\assistant.py

from datetime import datetime
import shutil

from ollama import chat


# ── 도구들 (5주차에서 가져옴) ────────────────────────────────────
def get_current_time() -> str:
    """현재 날짜와 시간을 알려준다."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def check_disk(drive: str) -> str:
    """지정한 드라이브의 전체 용량과 남은 용량을 GB 단위로 알려준다. drive는 'C', 'F' 같은 드라이브 문자."""
    total, used, free = shutil.disk_usage(f"{drive}:\\")
    return f"{drive} 드라이브: 전체 {total // 2**30}GB, 남음 {free // 2**30}GB"

def list_files(folder: str) -> str:
      """지정한 폴더 안의 파일과 폴더 목록을 알려준다. folder는 'F:/ai-study' 같은 경로."""
      import os
      return str(os.listdir(folder))


TOOLS = [get_current_time, check_disk, list_files]
AVAILABLE = {"get_current_time": get_current_time, "check_disk": check_disk, "list_files": list_files}

SYSTEM = """너는 내 PC에서 돌아가는 개인 비서다. 반드시 한국어로만 답한다.
도구가 필요한 질문이면 도구를 사용하고, 일반 대화면 그냥 답한다."""

# ── 대화 루프 (3주차 구조 + 도구 처리) ──────────────────────────
history = [{"role": "system", "content": SYSTEM}]

while True:
    user_input = input("나: ")
    if user_input.lower() == "/bye":
        break
    history.append({"role": "user", "content": user_input})

    response = chat(model="qwen2.5:7b", messages=history, tools=TOOLS)

    # 모델이 도구를 요청했으면: 실행 → 결과를 이력에 추가 → 한 번 더 물어봄
    if response.message.tool_calls:
        history.append(response.message)
        for call in response.message.tool_calls:
            fn = AVAILABLE[call.function.name]
            result = fn(**call.function.arguments)
            print(f"  (도구 실행: {call.function.name} → {result})")
            history.append({"role": "tool", "name": call.function.name, "content": result})
        response = chat(model="qwen2.5:7b", messages=history, tools=TOOLS)

    answer = response.message.content
    print("봇:", answer)
    history.append({"role": "assistant", "content": answer})
