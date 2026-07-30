from datetime import datetime
import shutil

def get_current_time() -> str:
      """현재 날짜와 시간을 알려준다."""
      return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def check_disk(drive: str) -> str:
      """지정한 드라이브의 전체 용량과 남은 용량을 GB 단위로 알려준다. drive는 'C', 'F' 같은 드라이브
  문자."""
      total, used, free = shutil.disk_usage(f"{drive}:\\")
      return f"{drive} 드라이브: 전체 {total // 2**30}GB, 남음 {free // 2**30}GB"

from ollama import chat

messages = [{"role": "user", "content": "F 드라이브 얼마 남았어?"}]
available = {"get_current_time": get_current_time, "check_disk": check_disk}

response = chat(model="qwen2.5:7b", messages=messages,
                  tools=[get_current_time, check_disk])

if response.message.tool_calls:
      messages.append(response.message)
      for call in response.message.tool_calls:
          fn = available[call.function.name]
          result = fn(**call.function.arguments)
          print("(도구 실행:", call.function.name, "→", result, ")")
          messages.append({"role": "tool", "name": call.function.name, "content": result})
      final = chat(model="qwen2.5:7b", messages=messages)
      print(final.message.content)
else:
      print(response.message.content)
