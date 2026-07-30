# ai-study

AI 서비스 개발 공부 기록 저장소.

- 커리큘럼: [CURRICULUM.md](CURRICULUM.md)
- 진행 상태: [PROGRESS.md](PROGRESS.md)
- 주차별 코드와 메모: `week01/`, `week02/`, ...

새 Claude 세션에서 이어가기: "CURRICULUM.md랑 PROGRESS.md 읽고 공부 이어가자"

## 다른 PC에서 세팅하기 (집 PC 등)

repo에는 코드만 있고 venv·모델·벡터DB는 없다 (전부 재생성 가능). 순서:

1. 설치: [Python](https://python.org) (3.11+, "Add to PATH" 체크), [Git](https://git-scm.com), [Ollama](https://ollama.com)
2. 코드 받기:
   ```
   git clone https://github.com/chang-hee-jung/ai-study.git
   cd ai-study
   ```
3. 가상환경 + 패키지:
   ```
   python -m venv venv
   .\venv\Scripts\pip install -r requirements.txt
   ```
4. 모델 받기 (하드웨어에 맞게 — VRAM 8GB 미만이면 7b와 bge-m3만이라도):
   ```
   ollama pull qwen2.5:7b
   ollama pull qwen2.5:14b
   ollama pull qwen3:14b
   ollama pull bge-m3
   ```
5. 벡터 인덱스 재생성 (문서 QA용):
   ```
   .\venv\Scripts\python week08\build_index.py
   ```
6. 확인: `.\venv\Scripts\python week01\hello.py` — 답이 나오면 이사 완료

이후 공부 기록은 양쪽에서 `git pull` / `git push`로 동기화.
