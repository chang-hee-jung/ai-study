from ollama import chat

response = chat(
      model="qwen2.5:7b", 
      messages=[
          {"role": "user" , "content": "안녕, 넌 누구야?"}
      ],
  )
print(response.message.content)
print(response)