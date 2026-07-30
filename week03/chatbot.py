from ollama import chat

history = []                     # ← 루프 밖! 대화가 쌓일 빈 목록

while True:
      user_input = input("나: ")
      if user_input == "/bye":
          break
      history.append({"role": "user", "content": user_input})
      stream = chat(
          model="qwen2.5:7b",
          messages=history,
          stream=True,
      )
      answer = ""
      print("봇: ", end="", flush=True)
      for part in stream:
          print(part.message.content, end="", flush=True)
          answer = answer + part.message.content
      print()
      history.append({"role": "assistant", "content": answer})