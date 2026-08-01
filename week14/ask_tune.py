r"""14주차 2/2 - 실전: ask.py 튜닝 (bge-m3를 내리면 14B가 빨라지는가)

[문제]
  ask.py는 모델 두 개를 쓴다.
    1) bge-m3   : 질문 -> 벡터 (딱 한 번 쓰고 끝)
    2) qwen2.5:14b : 근거 -> 답변
  그런데 bge-m3는 KEEP_ALIVE 기본 5분이라 생성 내내 VRAM 0.62GB를 깔고 앉는다.
  14B는 혼자서도 8GB 카드에 안 들어가는 놈이라, 그 0.62GB가 GPU 몫을 깎는다.

[핵심 전제]
  ollama는 "모델을 올리는 순간"의 여유 VRAM을 보고 GPU 레이어 수를 정한다.
  한 번 정해지면 안 바뀐다. -> 반드시 14B를 올리기 "전에" 내려야 한다.

[조건]
  A (현행) : 검색 후 bge-m3를 그대로 둔 채 14B 로드
  B (튜닝) : 검색 후 bge-m3를 keep_alive=0으로 내리고 14B 로드

[예측 - 실행 전에 작성]
  B가 14B의 size_vram이 더 크고, eval 속도(tok/s)가 더 빠르다.
  (몇 %? ______ 적고 시작할 것)

실행: cd F:\ai-study 후
      .\venv\Scripts\python.exe week14\ask_tune.py
"""

import json
import os
import time
import urllib.request

import chromadb
from ollama import chat, embed

API = "http://127.0.0.1:11434"
GB = 1024**3

EMB_MODEL = "bge-m3"
GEN_MODEL = "qwen2.5:14b"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "week08", "db")

QUESTIONS = [
    "출장 숙박비 한도가 얼마야?",
    "재택근무는 어떻게 신청해?",
    "연차는 몇 일이고 이월되나?",
    "비밀번호는 얼마마다 바꿔야 해?",
]

SYSTEM = """너는 사내 규정 안내 봇이다.
반드시 한국어로만 답한다.
제공된 근거에 있는 내용만으로 답하고, 근거에 없는 내용은 절대 지어내지 않는다.
근거에 질문의 답이 없으면 "규정에서 찾을 수 없습니다"라고만 답한다.
답할 때 어느 근거를 참고했는지 (근거 1) 형식으로 표시한다."""


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
    """태그만 채운다. 모델명은 자르지 않는다 (자르면 7b와 14b가 뭉개진다)"""
    return name if ":" in name else f"{name}:latest"


def vram_of(model):
    """지금 그 모델이 VRAM에 얼마나 올라가 있나 (없으면 0)"""
    for m in get("/api/ps")["models"]:
        if norm(m["name"]) == norm(model):
            return m["size_vram"]
    return 0


def unload_all():
    for m in get("/api/ps")["models"]:
        name = m["name"]
        try:
            post("/api/generate", {"model": name, "keep_alive": 0})
        except Exception:
            post("/api/embed", {"model": name, "input": "x", "keep_alive": 0})
    time.sleep(1)


collection = chromadb.PersistentClient(path=DB).get_collection("rules")


def build_prompt(question):
    """ask.py의 1~2단계 그대로: 검색 -> 근거 조립. bge-m3가 여기서 올라간다."""
    q = embed(model=EMB_MODEL, input=question)
    result = collection.query(query_embeddings=q.embeddings, n_results=3)
    chunks = result["documents"][0]
    context = ""
    for i, chunk in enumerate(chunks):
        context += f"[근거 {i + 1}]\n{chunk}\n\n"
    return f"""아래 근거만 사용해서 질문에 답해줘.

{context}
질문: {question}"""


def one_run(question, drop_embedder):
    """조건 하나를 한 번 측정. 매번 완전 청소로 시작해 로드 시점을 통제한다."""
    unload_all()

    prompt = build_prompt(question)  # bge-m3 올라감

    if drop_embedder:
        post("/api/embed", {"model": EMB_MODEL, "input": "x", "keep_alive": 0})
        time.sleep(0.5)

    emb_vram = vram_of(EMB_MODEL)

    t = time.time()
    r = chat(
        model=GEN_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )
    wall = time.time() - t

    return {
        "emb_vram": emb_vram,
        "gen_vram": vram_of(GEN_MODEL),
        "tok_s": r.eval_count / (r.eval_duration / 1e9),
        "eval_count": r.eval_count,
        "load_s": r.load_duration / 1e9,
        "wall": wall,
    }


print(f"질문 {len(QUESTIONS)}개 x 조건 2개. 매번 전체 언로드로 시작합니다.\n")
print(f"{'질문':<28} {'조건':<12} {'emb VRAM':>9} {'14B VRAM':>9} {'tok/s':>7} {'총(초)':>7}")
print("-" * 80)

totals = {"A": [], "B": []}

for q in QUESTIONS:
    for cond, drop in (("A 현행", False), ("B 튜닝", True)):
        m = one_run(q, drop)
        totals[cond[0]].append(m)
        print(
            f"{q[:26]:<28} {cond:<12} "
            f"{m['emb_vram'] / GB:>8.2f}G {m['gen_vram'] / GB:>8.2f}G "
            f"{m['tok_s']:>7.2f} {m['wall']:>7.1f}"
        )
    print()

unload_all()


def avg(rows, key):
    return sum(r[key] for r in rows) / len(rows)


a, b = totals["A"], totals["B"]
print("=" * 80)
print(f"{'':<14} {'14B VRAM':>10} {'tok/s':>9} {'총 시간(초)':>12}")
print(f"{'A 현행':<14} {avg(a, 'gen_vram') / GB:>9.2f}G {avg(a, 'tok_s'):>9.2f} {avg(a, 'wall'):>12.1f}")
print(f"{'B 튜닝':<14} {avg(b, 'gen_vram') / GB:>9.2f}G {avg(b, 'tok_s'):>9.2f} {avg(b, 'wall'):>12.1f}")

d_vram = (avg(b, "gen_vram") - avg(a, "gen_vram")) / GB
d_speed = (avg(b, "tok_s") / avg(a, "tok_s") - 1) * 100
d_wall = (avg(b, "wall") / avg(a, "wall") - 1) * 100
print(f"{'차이':<14} {d_vram:>+9.2f}G {d_speed:>+8.1f}% {d_wall:>+11.1f}%")
print("\ntok/s가 올랐으면 -> 되찾은 VRAM만큼 레이어가 더 GPU로 갔다는 뜻.")
print("안 올랐으면 -> 0.62GB로는 레이어 하나도 더 못 올렸거나, 병목이 딴 데 있다.")
