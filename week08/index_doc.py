with open("week08/rules.txt", encoding="utf-8") as f:
      text = f.read()

chunks = text.split("\n\n")

print("조각 수:", len(chunks))
for i, chunk in enumerate(chunks):
      print(f"[{i}] ({len(chunk)}자) {chunk[:30]}...")