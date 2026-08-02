# 9주차: 문서 QA 봇 (마일스톤 2) — 검색(RAG) + 생성의 합체
# 사용법: .\venv\Scripts\python week09\ask.py "질문"

import os
import sys
from ollama import chat, embed
import chromadb

if len(sys.argv) < 2:
    print('사용법: python week09\\ask.py "질문"')
    sys.exit(1)

question = sys.argv[1]

# ── 1) 검색: 8주차에 구축한 인덱스에서 관련 조각 3개 ──────────────
client = chromadb.PersistentClient(path="week08/db")
collection = client.get_collection("rules")

q = embed(model="bge-m3", input=question)
result = collection.query(query_embeddings=q.embeddings, n_results=3)

chunks = result["documents"][0]
distances = result["distances"][0]
if distances[0] > 1.2:
      print("답변: 규정에서 관련 내용을 찾을 수 없습니다")
      sys.exit(0)


# ── 2) 검색된 조각들을 "근거"로 프롬프트에 조립 ──────────────────
context = ""
for i, chunk in enumerate(chunks):
    context = context + f"[근거 {i+1}]\n{chunk}\n\n"

prompt = f"""아래 근거만 사용해서 질문에 답해줘.

{context}
질문: {question}"""

# ── 3) 생성: 근거를 보고 답하게 한다 ────────────────────────────
# 14주차: GPU에 올릴 레이어 수를 손으로 지정할 수 있다 (미설정이면 ollama 자동 판정).
#   14B는 8GB 카드에 다 안 들어가서 일부가 CPU로 간다. 자동 판정은 보수적이라
#   48개 중 31개만 올렸는데, 38개까지 올리면 27.7% 빨라진다 (week14/gpu_confirm.py).
#   단 최적값은 PC마다 다르다 — 화면이 VRAM을 쓰는 무iGPU PC에서 38을 쓰면
#   VRAM이 넘쳐 공유 메모리로 새고 오히려 절반 속도가 된다. 그래서 기본은 자동.
#   설정법:  $env:ASK_NUM_GPU = "38"     (영구:  setx ASK_NUM_GPU 38)
options = {}
if os.environ.get("ASK_NUM_GPU"):
    options["num_gpu"] = int(os.environ["ASK_NUM_GPU"])

response = chat(
    model="qwen2.5:14b",
    options=options,
    messages=[
        {"role": "system", "content": """너는 사내 규정 안내 봇이다.
반드시 한국어로만 답한다.
제공된 근거에 있는 내용만으로 답하고, 근거에 없는 내용은 절대 지어내지 않는다.
근거에 질문의 답이 없으면 "규정에서 찾을 수 없습니다"라고만 답한다.
답할 때 어느 근거를 참고했는지 (근거 1) 형식으로 표시한다."""},
        {"role": "user", "content": prompt},
    ],
)

print("답변:", response.message.content)
print()
print("--- 참고한 검색 결과 (거리가 작을수록 관련 높음) ---")
for i, (chunk, dist) in enumerate(zip(chunks, distances)):
    print(f"[근거 {i+1}] 거리 {dist:.3f} : {chunk[:40]}...")
