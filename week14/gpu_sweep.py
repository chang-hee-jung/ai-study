r"""14주차 2/2 - 실전 2: num_gpu 스윕 (노는 VRAM 2.2GB를 쓸 수 있는가)

[배경]
  ask_tune.py 결과: bge-m3를 내려 0.62GB를 비워줘도 14B는 5.78GB에서
  바이트 단위로 꿈쩍도 안 했다. 8GB 카드인데 2.2GB가 놀고 있다.
  -> ollama의 자동 레이어 판정이 보수적이라는 뜻.

[가설]
  num_gpu로 레이어 수를 직접 올리면 놀던 VRAM을 쓰고 그만큼 빨라진다.

[예측 - 실행 전에 작성]
  레이어를 올릴수록 tok/s가 오르다가, 어느 지점에서 VRAM이 터져
  로드 실패하거나 급격히 느려진다(스왑). 그 직전이 최적점.
  최적점 tok/s = ______ (적고 시작할 것. 기본값은 11.9)

[주의]
  과하게 밀어넣으면 로드 실패 / 화면 일시 멈춤 가능. 예외는 잡아둠.

실행: cd F:\ai-study 후
      .\venv\Scripts\python.exe week14\gpu_sweep.py
"""

import json
import time
import urllib.request

from ollama import chat

API = "http://127.0.0.1:11434"
GB = 1024**3

MODEL = "qwen2.5:14b"
LAYERS = 48  # qwen2.5:14b의 전체 레이어 수

# 자동(None)을 먼저 재서 기준선을 잡고, 위로 올려본다
SWEEP = [None, 30, 34, 38, 42, 46, 48]

PROMPT = "사내 규정에서 출장비 정산 절차를 세 문장으로 설명해줘."


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


def norm(name):
    return name if ":" in name else f"{name}:latest"


def vram_of(model):
    for m in get("/api/ps")["models"]:
        if norm(m["name"]) == norm(model):
            return m["size_vram"]
    return 0


def unload_all():
    for m in get("/api/ps")["models"]:
        try:
            post("/api/generate", {"model": m["name"], "keep_alive": 0})
        except Exception:
            post("/api/embed", {"model": m["name"], "input": "x", "keep_alive": 0})
    time.sleep(1)


print(f"{MODEL} num_gpu 스윕 (전체 {LAYERS}레이어, VRAM 8GB)\n")
print(f"{'num_gpu':>9} {'VRAM':>8} {'로드(초)':>9} {'tok/s':>8} {'생성토큰':>8}  결과")
print("-" * 62)

best = (None, 0.0)

for n in SWEEP:
    unload_all()
    options = {} if n is None else {"num_gpu": n}
    label = "자동" if n is None else str(n)

    try:
        t = time.time()
        r = chat(
            model=MODEL,
            messages=[{"role": "user", "content": PROMPT}],
            options=options,
        )
        wall = time.time() - t
        tok_s = r.eval_count / (r.eval_duration / 1e9)
        vram = vram_of(MODEL)
        print(
            f"{label:>9} {vram / GB:>7.2f}G {r.load_duration / 1e9:>9.1f} "
            f"{tok_s:>8.2f} {r.eval_count:>8}  ok"
        )
        if tok_s > best[1]:
            best = (label, tok_s)
    except Exception as e:
        msg = str(e).split("\n")[0][:28]
        print(f"{label:>9} {'-':>8} {'-':>9} {'-':>8} {'-':>8}  실패: {msg}")

unload_all()

print("-" * 62)
if best[0] is not None:
    print(f"최고: num_gpu={best[0]} 에서 {best[1]:.2f} tok/s")
print("\nVRAM 열이 num_gpu를 따라 오르면 -> 자동 판정이 보수적이었다는 뜻.")
print("안 오르면 -> num_gpu는 상한일 뿐 다른 제약이 진짜 범인이다.")
