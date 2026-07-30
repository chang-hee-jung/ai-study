# 13주차 2차전: 같은 체급 세대 비교 — qwen2.5:14b(구) vs qwen3:14b(신)
# 사용법: .\venv\Scripts\python week13\compare2.py "질문"
#
# qwen3의 특징 = "생각 모드": 답하기 전에 속으로 추론한다.
# ollama가 그 추론을 message.thinking에 따로 담아준다 (답변과 분리됨)

import sys
from ollama import chat

if len(sys.argv) < 2:
    print('사용법: python week13\\compare2.py "질문"')
    sys.exit(1)

question = sys.argv[1]
MODELS = ["qwen2.5:14b", "qwen3:14b"]

for model in MODELS:
    response = chat(model=model, messages=[{"role": "user", "content": question}])
    tokens = response.eval_count
    seconds = response.eval_duration / 1_000_000_000
    print(f"\n{'=' * 20} {model} {'=' * 20}")

    # qwen3의 속마음(생각 과정)이 있으면 앞부분만 구경
    thinking = response.message.thinking
    if thinking:
        print(f"[생각 중... 총 {len(thinking)}자] {thinking[:150]}...")
        print("-" * 50)

    print(response.message.content)
    print(f"--- 출력 {tokens}토큰 / {seconds:.1f}초 = {tokens / seconds:.1f} 토큰/초")
