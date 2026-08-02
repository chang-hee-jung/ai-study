r"""14주차 2/2 - 숙제 1: ps SIZE > 파일 크기, 그 차액의 정체는?

가설: 차액 = KV 캐시 창고. 창고 크기는 num_ctx가 정한다.
예측: num_ctx를 2배로 하면 차액도 2배가 된다.

실행: F:\ai-study\venv\Scripts\python.exe week14\ctx_test.py
"""

import json
import urllib.request

from ollama import chat

MODEL = "qwen2.5:7b"
API = "http://127.0.0.1:11434"


def api(path):
    with urllib.request.urlopen(f"{API}{path}") as r:
        return json.load(r)


def file_size():
    """디스크에 있는 gguf 파일의 바이트 수 (변하지 않는 기준선)"""
    for m in api("/api/tags")["models"]:
        if m["name"] == MODEL:
            return m["size"]
    raise SystemExit(f"{MODEL} 모델이 없습니다")


def loaded():
    """지금 메모리에 올라가 있는 것 (없으면 None)"""
    for m in api("/api/ps")["models"]:
        if m["name"] == MODEL:
            return m
    return None


def unload():
    """keep_alive=0 = 답하자마자 내려가라. 다음 측정의 오염 방지."""
    chat(model=MODEL, messages=[{"role": "user", "content": "hi"}], keep_alive=0)


def load(num_ctx):
    """창고 크기를 지정해서 올린다"""
    chat(
        model=MODEL,
        messages=[{"role": "user", "content": "hi"}],
        options={"num_ctx": num_ctx},
    )


MB = 1024 * 1024
base = file_size()
print(f"파일 크기(기준선): {base:,} bytes = {base / MB:,.1f} MiB\n")
print(f"{'num_ctx':>8} {'ps.size':>15} {'차액(MiB)':>12} {'토큰당(KiB)':>12}")
print("-" * 51)

for num_ctx in (2048, 4096, 8192, 16384):
    unload()
    load(num_ctx)
    m = loaded()
    if m is None:
        print(f"{num_ctx:>8}   측정 실패 (모델이 안 올라감)")
        continue
    gap = m["size"] - base
    print(
        f"{num_ctx:>8} {m['size']:>15,} {gap / MB:>12,.1f} {gap / 1024 / num_ctx:>12,.2f}"
    )

unload()
print("\n맨 오른쪽 열(토큰당 비용)이 일정하면 -> 차액은 토큰 수에 비례한다 = 창고가 맞다.")
print("들쭉날쭉하면 -> 토큰과 무관한 다른 놈이 섞여 있다.")
