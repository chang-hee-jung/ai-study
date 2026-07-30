from ollama import chat

import sys

filename = sys.argv[1]

with open(filename, encoding="utf-8") as f:
      text = f.read()

prompt = f"다음 회의록에서 결정사항과 할 일만 뽑아줘:\n\n{text}"

response = chat(
      model="qwen2.5:7b",
        messages=[
      {"role": "system", "content": """너는 회사 회의록을 정리하는 비서다.
  반드시 한국어로만 답한다.
  날짜, 금액, 인원수 같은 숫자는 빠뜨리지 말고 원문 그대로 보존한다.
  확정되지 않은 사항을 확정된 것처럼 쓰지 않는다."""},
      {"role": "user", "content": prompt},
  ],
  )
print(response.message.content)