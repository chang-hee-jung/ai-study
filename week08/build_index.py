# 8주차 2단계: 문서를 청킹해서 벡터 DB에 저장 (인덱스 구축)
# 실행: .\venv\Scripts\python week08\build_index.py

from ollama import embed
import chromadb

with open("week08/rules.txt", encoding="utf-8") as f:
    text = f.read()

# 문단 단위 청킹 + 너무 짧은 조각(제목 줄)은 버린다
chunks = text.split("\n\n")
chunks = [c.strip() for c in chunks if len(c.strip()) > 20]

print("인덱싱할 조각 수:", len(chunks))

# PersistentClient: 지난주의 Client()와 달리 디스크에 저장된다.
# 한 번 구축해두면 다음에 검색만 할 수 있다 (9주차 QA봇이 이걸 재사용)
client = chromadb.PersistentClient(path="week08/db")

# 재실행 대비: 같은 이름이 이미 있으면 지우고 새로 만든다
try:
    client.delete_collection("rules")
except Exception:
    pass
collection = client.create_collection("rules")

# 조각 전부를 한 번에 임베딩해서 저장
response = embed(model="bge-m3", input=chunks)
collection.add(
    ids=[str(i) for i in range(len(chunks))],
    documents=chunks,
    embeddings=response.embeddings,
)

print("저장 완료: week08/db 폴더")
