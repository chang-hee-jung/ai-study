# 13주차(보너스): 모델 크기 비교 — 같은 질문을 7B와 14B에게, 품질과 속도를 나란히
# 사용법: .\venv\Scripts\python week13\compare.py "질문"

import sys
from ollama import chat

if len(sys.argv) < 2:
    print('사용법: python week13\\compare.py "질문"')
    sys.exit(1)

question = sys.argv[1]
MODELS = ["qwen2.5:7b", "qwen2.5:14b"]

for model in MODELS:
    response = chat(model=model, messages=[{"role": "user", "content": question}])
    tokens = response.eval_count
    seconds = response.eval_duration / 1_000_000_000   # 나노초 → 초
    print(f"\n{'=' * 20} {model} {'=' * 20}")
    print(response.message.content)
    print(f"--- 출력 {tokens}토큰 / {seconds:.1f}초 = {tokens / seconds:.1f} 토큰/초")
