# 8주차 3단계: 구축된 인덱스에서 검색
# 실행: .\venv\Scripts\python week08\search.py "질문을 여기에"

import sys
from ollama import embed
import chromadb

if len(sys.argv) < 2:
    print('사용법: python week08\\search.py "질문"')
    sys.exit(1)

question = sys.argv[1]

# 저장해둔 인덱스를 불러온다 (임베딩·저장은 이미 끝났으므로 빠름)
client = chromadb.PersistentClient(path="week08/db")
collection = client.get_collection("rules")

# 질문을 같은 모델로 임베딩해서 가장 가까운 조각 3개 검색
q = embed(model="bge-m3", input=question)
result = collection.query(query_embeddings=q.embeddings, n_results=3)

print("질문:", question)
for doc, dist in zip(result["documents"][0], result["distances"][0]):
    print(f"\n[거리 {dist:.3f}]")
    print(doc)
