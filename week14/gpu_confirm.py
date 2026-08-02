r"""14주차 2/2 - 실전 3: num_gpu 최적점 확인 측정

[배경]
  gpu_sweep.py에서 38레이어가 15.29 tok/s로 1등이었다. 하지만
  각 지점을 한 번씩만 쟀고, 생성 토큰이 84~121개로 들쭉날쭉했다.
  38 vs 42의 차이(4%)가 진짜인지 노이즈인지 모른다.

[개선]
  1) num_predict로 출력 길이를 120토큰에 고정 -> 측정 조건 통일
  2) 각 지점을 3회 반복 -> 편차를 눈으로 확인
  3) 46은 제외 (VRAM 초과 = 공유 메모리 스필, 이미 기각됨)

실행: cd F:\ai-study 후
      .\venv\Scripts\python.exe week14\gpu_confirm.py
"""

import json
import time
import urllib.request

from ollama import chat

API = "http://127.0.0.1:11434"
GB = 1024**3

MODEL = "qwen2.5:14b"
CANDIDATES = [None, 34, 38, 42]  # None = ollama 자동 판정 (기준선)
REPEATS = 3
NUM_PREDICT = 120  # 출력 길이 고정

PROMPT = "사내 규정에서 출장비 정산 절차를 설명해줘."


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


print(f"{MODEL} 최적점 확인 - 출력 {NUM_PREDICT}토큰 고정, 각 {REPEATS}회\n")
print(f"{'num_gpu':>9} {'VRAM':>8}   " + "  ".join(f"{i + 1}회" for i in range(REPEATS)) + "     평균     편차")
print("-" * 64)

results = {}

for n in CANDIDATES:
    label = "자동" if n is None else str(n)
    options = {"num_predict": NUM_PREDICT}
    if n is not None:
        options["num_gpu"] = n

    runs = []
    vram = 0
    for _ in range(REPEATS):
        unload_all()  # 매번 새로 올려야 레이어 분할이 다시 결정된다
        r = chat(
            model=MODEL,
            messages=[{"role": "user", "content": PROMPT}],
            options=options,
        )
        runs.append(r.eval_count / (r.eval_duration / 1e9))
        vram = vram_of(MODEL)

    avg = sum(runs) / len(runs)
    spread = max(runs) - min(runs)
    results[label] = avg
    cells = "  ".join(f"{v:5.2f}" for v in runs)
    print(f"{label:>9} {vram / GB:>7.2f}G   {cells}   {avg:6.2f}   {spread:5.2f}")

unload_all()

print("-" * 64)
base = results.get("자동")
best = max(results, key=results.get)
print(f"최적: num_gpu={best} ({results[best]:.2f} tok/s)")
if base:
    gain = (results[best] / base - 1) * 100
    print(f"자동 대비 {gain:+.1f}%")
print("\n편차 열이 후보 간 차이보다 크면 -> 그 둘은 사실상 동점. 안전한 쪽을 고른다.")
