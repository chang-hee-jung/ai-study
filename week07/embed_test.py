from ollama import embed
import chromadb

sentences = [
      "우리 회사 연차는 1년에 15일입니다",
      "재택근무는 주 2회까지 가능합니다",
      "법인카드 한도는 월 50만 원입니다",
      "서버 정기 점검은 매주 일요일 새벽에 진행됩니다",
      "회의실 예약은 사내 포털에서 합니다",
  ]

client = chromadb.Client()
collection = client.create_collection("rules")

response = embed(model="bge-m3", input=sentences)
collection.add(
      ids=["0", "1", "2", "3", "4"],
      documents=sentences,
      embeddings=response.embeddings,
  )

question = "회사 카드로 얼마까지 결제 가능?"
q = embed(model="bge-m3", input=question)
result = collection.query(query_embeddings=q.embeddings, n_results=2)

print("질문:", question)
for doc, dist in zip(result["documents"][0], result["distances"][0]):
    print(f"  거리 {dist:.3f} : {doc}")