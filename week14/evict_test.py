r"""14주차 2/2 - 숙제 2: 7B 실종 사건 (자연 만료냐, 강제 축출이냐)

[설계 - 학생]
  두 가설은 연료가 다르다. 만료=시간, 축출=공간 압박.
  지금까지 관찰에선 둘이 동시에 있어서 못 갈랐다.
  -> 7B에 keep_alive=30m을 걸어 "시간" 연료를 물리적으로 끊는다.
     그 상태에서 다른 모델을 투입해 "공간 압박"만 남긴다.

[판결표 - 실행 전에 작성]
  본실험: 14B 투입 (4.7 + 9.0 = 13.7GB > VRAM 8GB, 압박 있음)
     7B 사라짐 -> 축출        7B 남음 -> 만료
  대조군: bge-m3 투입 (4.7 + 1.2 = 5.9GB < VRAM 8GB, 압박 없음)
     7B 사라짐 -> 항상 밀어낸다    7B 남음 -> 자리 부족할 때만 밀어낸다

실행: F:\ai-study\venv\Scripts\python.exe F:\ai-study\week14\evict_test.py
"""

import json
import time
import urllib.request

from ollama import chat

API = "http://127.0.0.1:11434"
GB = 1024**3

SMALL = "qwen2.5:7b"  # 피해자
BIG = "qwen2.5:14b"  # 본실험 투입 모델 (압박 O)
EMB = "bge-m3"  # 대조군 투입 모델 (압박 X)

KEEP = "30m"  # 만료 가능성 제거용


def get(path):
    with urllib.request.urlopen(f"{API}{path}") as r:
        return json.load(r)


def post(path, payload):
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def ps():
    return get("/api/ps")["models"]


def show(label):
    """현재 메모리 상태를 찍고, 올라가 있는 모델 이름 집합을 돌려준다"""
    models = ps()
    print(f"\n  [{label}]")
    if not models:
        print("    (비어 있음)")
        return set()
    total = 0
    for m in models:
        total += m["size_vram"]
        until = m["expires_at"][11:19]  # 시:분:초만
        print(
            f"    {m['name']:<16} vram={m['size_vram'] / GB:5.2f}GB  until={until}"
        )
    print(f"    {'합계':<15} vram={total / GB:5.2f}GB")
    return {m["name"] for m in models}


def norm(name):
    """'bge-m3' -> 'bge-m3:latest'. 태그만 채우고 모델명은 절대 자르지 않는다.
    (자르면 qwen2.5:7b와 qwen2.5:14b가 같은 모델로 뭉개진다 - 실제로 겪은 버그)"""
    return name if ":" in name else f"{name}:latest"


def alive(names, model):
    return any(norm(n) == norm(model) for n in names)


def unload_all():
    """모든 모델 즉시 내리기 (keep_alive=0). 다음 측정의 오염 방지."""
    for m in ps():
        name = m["name"]
        try:
            post("/api/generate", {"model": name, "keep_alive": 0})
        except Exception:
            post("/api/embed", {"model": name, "input": "x", "keep_alive": 0})
    time.sleep(1)


def load_chat(model, keep_alive):
    t = time.time()
    chat(
        model=model,
        messages=[{"role": "user", "content": "hi"}],
        keep_alive=keep_alive,
    )
    return time.time() - t


def load_embed(model, keep_alive):
    t = time.time()
    post("/api/embed", {"model": model, "input": "hi", "keep_alive": keep_alive})
    return time.time() - t


def run(title, invader, loader, pressure):
    print(f"\n{'=' * 62}\n{title}\n{'=' * 62}")

    unload_all()
    show("0. 청소 후")

    sec = load_chat(SMALL, KEEP)
    names = show(f"1. {SMALL} 투입 (keep_alive={KEEP}, {sec:.1f}s)")
    if not alive(names, SMALL):
        print("    !! 피해자가 안 올라감 - 실험 중단")
        return None

    print(f"\n  -> {invader} 투입 중... (합계 {pressure})")
    sec = loader(invader, "5m")
    names = show(f"2. {invader} 투입 후 (로드 {sec:.1f}s)")

    survived = alive(names, SMALL)
    print(f"\n  경과 시간 {sec:.1f}s << 300s(기본 만료) 이고, keep_alive는 {KEEP}.")
    print(f"  => {SMALL} 생존 여부: {'남아 있음' if survived else '사라짐'}")
    return survived


# --- 본실험 -------------------------------------------------------------
survived_pressure = run(
    "본실험: 압박 있음 (4.7 + 9.0 = 13.7GB > VRAM 8GB)",
    BIG,
    load_chat,
    "13.7GB > 8GB",
)

# --- 대조군 -------------------------------------------------------------
survived_control = run(
    "대조군: 압박 없음 (4.7 + 1.2 = 5.9GB < VRAM 8GB)",
    EMB,
    load_embed,
    "5.9GB < 8GB",
)

unload_all()

# --- 판결 (실행 전에 정해둔 표대로) --------------------------------------
print(f"\n{'=' * 62}\n판결\n{'=' * 62}")

if survived_pressure is None or survived_control is None:
    print("  실험 미완 - 판결 보류")
else:
    if survived_pressure:
        print("  본실험: 7B 남음   -> 범인은 [자연 만료]. 14B는 무관한 구경꾼이었다.")
    else:
        print("  본실험: 7B 사라짐 -> 범인은 [강제 축출]. 만료는 무죄.")

    if survived_control:
        print("  대조군: 7B 남음   -> 축출은 [자리가 부족할 때만] 일어난다.")
    else:
        print("  대조군: 7B 사라짐 -> 축출은 [압박과 무관하게 항상] 일어난다.")
