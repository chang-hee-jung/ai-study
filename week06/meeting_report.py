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
      {"role": "system", "content": """너는 회의 내용을 정리하는 도구다.
입력은 발화자 표시가 없는 음성 전사 텍스트다.
반드시 한국어로만 답한다.
날짜, 금액, 수량 같은 숫자는 원문 그대로 보존한다.
할 일의 담당자가 대화에서 확인되지 않으면 지어내지 말고 "미정"이라고 쓴다."""},
      {"role": "user", "content": prompt},
  ],  format={
          "type": "object",
          "properties": {
              "summary": {"type": "string"},
   		"decisions": {                              # ← 이 세 줄 추가
                  "type": "array",
                  "items": {"type": "string"}
              },
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
             "required": ["summary", "decisions", "todos"]   # ← decisions 추가
      },
  )
data = json.loads(response.message.content)
report = f"""# 회의 요약

  ## 한 줄 요약
  {data["summary"]}

  ## 결정사항
  """
for d in data["decisions"]:
      report = report + f"- {d}\n"

report = report + "\n## 할 일\n"
for todo in data["todos"]:
      report = report + f"- [ ] {todo['task']} (담당: {todo['owner']})\n"

outname = filename.replace(".txt", "_요약.md")
with open(outname, "w", encoding="utf-8") as f:
      f.write(report)

print(report)
print("보고서 저장:", outname)