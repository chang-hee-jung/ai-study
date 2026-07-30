# 6주차 — 마일스톤 1: 회의 전사 → 자동 보고서 (meeting_report.py)

## 목표
- 지금까지 만든 부품(파일읽기·JSON 스키마·프롬프트)을 **재조립**해서 실전 도구 완성
- 파일 **쓰기** (open의 "w" 모드) — 처음으로 결과를 파일로 남긴다
- STT(음성인식) 텍스트의 특징 이해: 구어체, 문장부호 없음, 오인식 — 그걸 LLM이 정리

## 배경
MeetingAssistant(meeting_listen.py)가 회의 소리를 `[HH:MM:SS] 문장` 형식으로 전사해
transcripts/에 쌓는다. 이번 주에 만드는 도구는 그 전사 파일을 받아
**요약 + 결정사항 + 할일 보고서(md 파일)**를 자동 생성한다.
실제 회의 전사가 아직 없으므로 샘플(sample_transcript.txt)로 개발하고,
다음 실제 회의 때 그대로 투입한다.

## 프라이버시 메모
회의 내용은 회사 기밀일 수 있다 → 로컬 모델(Ollama)이라 PC 밖으로 안 나감.
1주차에 로컬을 선택한 보상이 여기서 나온다.
단, **실제 회의 전사 파일은 절대 이 공개 repo에 커밋하지 않는다** (.gitignore 처리).

## 최종 결과물
```powershell
.\venv\Scripts\python week06\meeting_report.py week06\sample_transcript.txt
```
→ `week06\sample_transcript_요약.md` 파일이 생성됨

## 단계별 진행

### 1단계: 뼈대 재조립 (새로운 것 없음)
week04/extract.py를 복사해서 week06/meeting_report.py로.
샘플 전사를 읽어 그대로 요약이 도는지 확인만.
관찰: 전사 텍스트는 회의록과 달리 지저분하다(누가 말했는지 없음, 문장부호 없음)

### 2단계: 스키마 확장 (스스로 설계)
기존 스키마는 summary, todos뿐. **decisions(결정사항 목록)를 직접 추가**해보기.
힌트: todos와 달리 결정사항은 문자열 배열이면 충분 —
`"decisions": {"type": "array", "items": {"type": "string"}}`
- system 프롬프트도 전사 텍스트에 맞게 손보기 (예: "발화자 정보가 없는 음성 전사임을
  감안하라", "언급되지 않은 담당자는 '미정'으로 표기하라")

### 3단계: 보고서를 파일로 쓰기
```python
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
print("보고서 저장:", outname)
```
- `open(경로, "w", ...)` — "w"는 쓰기 모드 (없으면 만들고, 있으면 덮어씀!)
- `f.write(문자열)` — 파일에 쓰기
- `filename.replace(a, b)` — 문자열 치환으로 출력 파일명 자동 생성

### 4단계: 실전 배치 준비
- 생성된 _요약.md를 열어 품질 확인 (팔십만 원, 오천 부, 요일들이 살아있는가?)
- MeetingAssistant의 진짜 transcripts 경로로도 실행해보기 (빈 파일이라 에러날 것 —
  빈 파일 처리를 어떻게 할지 생각해보기)
- 다음 실제 회의 후: `python week06\meeting_report.py C:\Users\s-n\MeetingAssistant\transcripts\meeting_XXX.txt`

## 체크포인트
- "w" 모드의 위험(덮어쓰기)은 언제 사고가 되나?
- 전사 텍스트가 회의록보다 어려운 이유는?
