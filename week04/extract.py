import json

from ollama import chat

import sys

filename = sys.argv[1]

with open(filename, encoding="utf-8") as f:
      text = f.read()

prompt = f"""다음 회의록에서 정보를 뽑아 JSON으로만 답해줘.
  다른 말은 하지 말고 JSON만. 형식:
  {{"summary": "한 줄 요약", "todos": [{{"task": "할 일", "owner": "담당자"}}]}}

회의록:
  {text}"""

response = chat(
      model="qwen2.5:7b",
        messages=[
      {"role": "system", "content": """너는 회사 회의록을 정리하는 비서다.
  반드시 한국어로만 답한다.
  날짜, 금액, 인원수 같은 숫자는 빠뜨리지 말고 원문 그대로 보존한다.
  확정되지 않은 사항을 확정된 것처럼 쓰지 않는다."""},
      {"role": "user", "content": prompt},
  ],  format={
          "type": "object",
          "properties": {
              "summary": {"type": "string"},
              "todos": {
                  "type": "array",
                  "items": {
                      "type": "object",
                      "properties": {
                          "task": {"type": "string"},
                          "owner": {"type": "string"}
                      },
                      "required": ["task", "owner"]
                  }
              }
          },
          "required": ["summary", "todos"]
      },
  )
data = json.loads(response.message.content)
data = json.loads(response.message.content)
print("요약:", data["summary"])
print()
print("할 일 목록:")
for todo in data["todos"]:
      print(f"  [ ] {todo['task']} (담당: {todo['owner']})")