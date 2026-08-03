r"""15주차: 적설계 위키 QA 봇 (week09/ask.py의 적설계판)

week09/ask.py와 다른 점:
  - 인덱스가 week15/db (적설계 위키 317조각)
  - 조각마다 출처 파일이 붙어 있어 답변에 문서명을 표시한다
  - 거리 문지기 임계값을 상수로 뺐다 (자료가 바뀌면 다시 잡아야 하는 값)

사용법: cd F:\ai-study 후
        .\venv\Scripts\python.exe week15\ask_wiki.py "지리산 적설값이 왜 비어있어?"
"""

import os
import sys

import chromadb
from ollama import chat, embed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "week15", "db")
# v3(헤딩 단위 청킹)이 채택본. 20/21로 v1·v2(19/21)보다 높다.
# 비교용으로 갈아끼우려면:  $env:ASK_COLLECTION = "snow_wiki"
COLLECTION = os.environ.get("ASK_COLLECTION", "snow_wiki_v3")

TOP_K = int(os.environ.get("ASK_TOP_K", "3"))
MAX_DIST = 1.2  # 이보다 멀면 "관련 자료 없음". 자료가 바뀌면 재조정 대상

# gemma4:e4b-it-qat이 채택본. qwen2.5:14b와 동점인데 VRAM 40%, 5배 빠르고,
# 실패할 때도 한국어를 지키고 "모른다"고 답한다 (14B는 중국어 이탈 + 출처 조작).
# 비교용으로 갈아끼우려면:  $env:ASK_MODEL = "qwen2.5:14b"
GEN_MODEL = os.environ.get("ASK_MODEL", "gemma4:e4b-it-qat")

SYSTEM = """너는 적설계 시스템(SnowViewer3D) 기술 안내 봇이다.
반드시 한국어로만 답한다.
제공된 근거에 있는 내용만으로 답하고, 근거에 없는 내용은 절대 지어내지 않는다.
근거에 질문의 답이 없으면 "자료에서 찾을 수 없습니다"라고만 답한다.
답할 때 어느 근거를 참고했는지 (근거 1) 형식으로 표시한다.
숫자, 파일명, 코드 위치는 근거에 적힌 그대로 옮긴다."""


def search(question, top_k=TOP_K):
    collection = chromadb.PersistentClient(path=DB).get_collection(COLLECTION)
    q = embed(model="bge-m3", input=question)
    r = collection.query(query_embeddings=q.embeddings, n_results=top_k)
    return r["documents"][0], r["metadatas"][0], r["distances"][0]


def answer(question, top_k=TOP_K):
    chunks, metas, dists = search(question, top_k)

    if dists[0] > MAX_DIST:
        return "자료에서 찾을 수 없습니다", chunks, metas, dists

    context = ""
    for i, (chunk, meta) in enumerate(zip(chunks, metas)):
        context += f"[근거 {i + 1}] (출처: {meta['source']})\n{chunk}\n\n"

    options = {}
    if os.environ.get("ASK_NUM_GPU"):
        options["num_gpu"] = int(os.environ["ASK_NUM_GPU"])

    kwargs = {}
    # qwen3 계열은 생각 모드가 기본 ON이라 토큰을 다 써버리고 답이 비어 나온다.
    # 모델 비교를 공정하게 하려면 꺼야 한다:  $env:ASK_NO_THINK = "1"
    if os.environ.get("ASK_NO_THINK"):
        kwargs["think"] = False

    response = chat(
        model=GEN_MODEL,
        options=options,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"아래 근거만 사용해서 질문에 답해줘.\n\n{context}질문: {question}"},
        ],
        **kwargs,
    )
    return response.message.content, chunks, metas, dists


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('사용법: python week15\\ask_wiki.py "질문"')
        sys.exit(1)

    question = sys.argv[1]
    text, chunks, metas, dists = answer(question)

    print("답변:", text)
    print("\n--- 참고한 검색 결과 (거리가 작을수록 관련 높음) ---")
    for i, (chunk, meta, dist) in enumerate(zip(chunks, metas, dists)):
        head = chunk.replace("\n", " ")[:60]
        print(f"[근거 {i + 1}] 거리 {dist:.3f}  {meta['source']}")
        print(f"          {head}...")
