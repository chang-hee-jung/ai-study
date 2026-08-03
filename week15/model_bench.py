r"""15주차: 모델 비교용 벤치 - VRAM 점유와 생성 속도를 같은 조건에서 잰다

13주차 모델 비교는 답변을 눈으로 보고 판단했다. 이제 숫자로 잰다.
출력 길이를 고정(num_predict)해서 측정 조건을 통일하고, 매번 언로드로 시작해
레이어 분할이 새로 결정되게 한다 (14주차에서 배운 오염 방지).

실행: cd F:\ai-study 후
      .\venv\Scripts\python.exe week15\model_bench.py qwen2.5:14b gemma4:e4b-it-qat
"""

import json
import os
import sys
import time
import urllib.request

from ollama import chat

API = "http://127.0.0.1:11434"
GB = 1024**3

NUM_PREDICT = 120
REPEATS = 2
PROMPT = "적설 데이터를 3D로 보여주는 프로그램의 구조를 세 문장으로 설명해줘."

MODELS = sys.argv[1:] or ["qwen2.5:14b", "gemma4:e4b-it-qat"]


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
            return m["size_vram"], m["size"]
    return 0, 0


def unload_all():
    for m in get("/api/ps")["models"]:
        try:
            post("/api/generate", {"model": m["name"], "keep_alive": 0})
        except Exception:
            post("/api/embed", {"model": m["name"], "input": "x", "keep_alive": 0})
    time.sleep(1)


def file_size(model):
    for m in get("/api/tags")["models"]:
        if norm(m["name"]) == norm(model):
            return m["size"]
    return 0


print(f"출력 {NUM_PREDICT}토큰 고정, 각 {REPEATS}회. ASK_NUM_GPU={os.environ.get('ASK_NUM_GPU', '(미설정)')}\n")
print(f"{'모델':<22} {'파일':>7} {'VRAM':>7} {'GPU밖':>7} {'로드(초)':>8} {'tok/s':>8}")
print("-" * 68)

for model in MODELS:
    options = {"num_predict": NUM_PREDICT}
    # num_gpu는 모델마다 최적값이 다르다. 다 올라가는 모델엔 손대지 않는다.
    if os.environ.get("ASK_NUM_GPU") and model.startswith("qwen2.5:14b"):
        options["num_gpu"] = int(os.environ["ASK_NUM_GPU"])

    speeds, load_s, vram, size = [], 0, 0, 0
    for _ in range(REPEATS):
        unload_all()
        r = chat(model=model, messages=[{"role": "user", "content": PROMPT}], options=options)
        if not r.eval_count or not r.eval_duration:
            print(f"  ({model}: 측정값 누락 - 이번 회차 건너뜀)")
            continue
        speeds.append(r.eval_count / (r.eval_duration / 1e9))
        load_s = r.load_duration / 1e9
        vram, size = vram_of(model)

    if not speeds:
        print(f"{model:<22}   측정 실패")
        continue

    fsize = file_size(model)
    outside = fsize - vram  # 파일 대비 VRAM에 안 올라간 몫
    avg = sum(speeds) / len(speeds)
    print(
        f"{model:<22} {fsize / GB:>6.2f}G {vram / GB:>6.2f}G {outside / GB:>6.2f}G "
        f"{load_s:>8.1f} {avg:>8.2f}"
    )

unload_all()
print("\nGPU밖 = 파일 크기 - VRAM 점유. 임베딩 테이블처럼 VRAM에 안 올리는 몫이 여기 잡힌다.")
