r"""15주차 1단계: 적설계 위키를 인덱스로 굽는다

week08/build_index.py의 확장판. 달라진 점 3가지:
  1) 파일 하나 -> 폴더 전체(.md 재귀 탐색)
  2) frontmatter(--- 블록) 제거 - 본문이 아니라 메타데이터라 검색 노이즈가 된다
  3) 조각마다 출처(파일 경로)를 metadata로 저장 - 답변에 출처를 달고,
     나중에 평가할 때 "정답 문서를 가져왔나"를 판정하려면 이게 있어야 한다

청킹은 week08과 같은 문단 단위를 유지한다. 기준점(baseline)을 먼저 만들고
개선은 점수를 본 뒤에 한다.

실행: cd F:\ai-study 후
      .\venv\Scripts\python.exe week15\build_wiki_index.py
"""

import os
import re
import sys

import chromadb
from ollama import embed

WIKI = r"F:\SnowViewer3D_wiki"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "week15", "db")

MIN_LEN = 20  # 이보다 짧은 조각(제목 줄 등)은 버린다

# v2 = 링크 노이즈 처리. 기준선(v1)과 비교하려고 별도 컬렉션으로 굽는다.
#   .\venv\Scripts\python.exe week15\build_wiki_index.py v2
VARIANT = sys.argv[1] if len(sys.argv) > 1 else "v1"
V2 = VARIANT in ("v2", "v3")  # v3도 링크 처리는 그대로 쓴다
V3 = VARIANT == "v3"  # 헤딩 단위로 묶기
COLLECTION = {"v1": "snow_wiki", "v2": "snow_wiki_v2", "v3": "snow_wiki_v3"}[VARIANT]

# v3: 같은 헤딩(## / ###) 아래 문단들을 한 조각으로 묶는다.
# Q5가 안 풀린 원인 - 요약문("우선순위대로 정해진다")과 실제 목록(1.surface 2.ir 3.data)이
# 빈 줄로 갈려 다른 조각이 됐고, 질문과 가장 비슷한 건 요약문 쪽이었다.
# 절이 길면 이 크기에서 끊되, 끊긴 조각에도 헤딩을 다시 붙인다.
MAX_CHUNK = 900
HEADING = re.compile(r"^(#{1,6})\s+(.+)$")

# 위키 링크를 걷어낸 뒤 남는 실제 내용이 이보다 적으면 "링크 목록 조각"으로 보고 버린다.
# (예: "- 비교: [[현장별-비교]], [[지리산-현장]]" -> 남는 건 "- 비교: ," 뿐)
MIN_CONTENT = 30

LINK = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def strip_frontmatter(text):
    """맨 앞의 --- ... --- 블록을 걷어낸다"""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4 :].lstrip()
    return text


def title_of(text, fallback):
    """첫 번째 # 제목을 문서 이름으로 쓴다. 없으면 파일명."""
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else fallback


dropped = []  # v2에서 버린 링크 목록 조각 (몇 개나 걸러졌는지 보려고)


def collect():
    """위키의 .md를 전부 읽어 문단 단위로 쪼갠다"""
    chunks, metas = [], []
    files = 0

    for dirpath, _, filenames in os.walk(WIKI):
        for name in sorted(filenames):
            if not name.endswith(".md"):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, WIKI)

            with open(path, encoding="utf-8") as f:
                text = strip_frontmatter(f.read())

            title = title_of(text, name[:-3])
            files += 1

            heading = ""  # 지금 어느 절 아래인가 (v3에서 조각을 묶는 기준)
            buf = []  # v3: 같은 절의 문단들을 모아두는 곳

            def flush():
                """모아둔 문단들을 한 조각으로 확정한다 (v3 전용)"""
                if not buf:
                    return
                head = f"[{title}" + (f" > {heading}]" if heading else "]")
                chunks.append(head + "\n" + "\n\n".join(buf))
                metas.append({"source": rel, "title": title, "heading": heading})
                buf.clear()

            for para in text.split("\n\n"):
                para = para.strip()
                if not para:
                    continue

                m = HEADING.match(para.split("\n")[0])
                if V3 and m and len(para.split("\n")) == 1:
                    # 헤딩 줄을 만나면 앞 절을 닫고 새 절을 연다
                    flush()
                    heading = m.group(2).strip()
                    continue

                if len(para) < MIN_LEN:
                    continue

                if V2:
                    # 링크를 걷어내고 남는 내용이 거의 없으면 = 링크 목록 문단. 버린다.
                    if len(LINK.sub("", para).strip(" \n\t-:,·")) < MIN_CONTENT:
                        dropped.append((rel, para[:40].replace("\n", " ")))
                        continue
                    # 남기는 조각은 [[링크]]를 평문으로 바꾼다.
                    # 그대로 두면 모델이 답변에 위키 문법을 그대로 흉내낸다 (실측됨)
                    para = LINK.sub(r"\1", para)

                if V3:
                    # 절이 너무 길어지면 여기서 끊는다 (끊긴 뒤에도 헤딩은 다시 붙는다)
                    if sum(len(p) for p in buf) + len(para) > MAX_CHUNK and buf:
                        flush()
                    buf.append(para)
                    continue

                # v1/v2: 문단 하나가 곧 조각
                chunks.append(f"[{title}]\n{para}")
                metas.append({"source": rel, "title": title})

            flush()

    return chunks, metas, files


chunks, metas, files = collect()

if not chunks:
    raise SystemExit(f"{WIKI} 에서 읽은 조각이 없습니다. 경로를 확인하세요.")

lengths = [len(c) for c in chunks]
print(f"위키 경로 : {WIKI}")
print(f"버전      : {VARIANT} " + {
    "v1": "(기준선: 문단 단위)",
    "v2": "(링크 목록 제거 + [[링크]] 평문화)",
    "v3": "(v2 + 헤딩 단위로 묶기)",
}[VARIANT])
print(f"문서 수   : {files}개")
print(f"조각 수   : {len(chunks)}개" + (f"  (링크 목록 {len(dropped)}개 버림)" if V2 else ""))
print(f"조각 길이 : 평균 {sum(lengths) // len(lengths)}자 / 최소 {min(lengths)} / 최대 {max(lengths)}")

client = chromadb.PersistentClient(path=DB)
try:
    client.delete_collection(COLLECTION)
except Exception:
    pass
collection = client.create_collection(COLLECTION)

# 조각이 많으면 한 번에 임베딩하지 않고 나눠서 (메모리·타임아웃 회피)
BATCH = 64
for i in range(0, len(chunks), BATCH):
    part = chunks[i : i + BATCH]
    response = embed(model="bge-m3", input=part)
    collection.add(
        ids=[str(i + j) for j in range(len(part))],
        documents=part,
        embeddings=response.embeddings,
        metadatas=metas[i : i + BATCH],
    )
    print(f"  임베딩 {min(i + BATCH, len(chunks))}/{len(chunks)}")

print(f"\n저장 완료: {DB} (collection={COLLECTION}, {collection.count()}조각)")

# 문서별 조각 수 - 어떤 문서가 잘게 쪼개졌는지 확인용
counts = {}
for m in metas:
    counts[m["source"]] = counts.get(m["source"], 0) + 1
print("\n문서별 조각 수 (상위 10)")
for src, n in sorted(counts.items(), key=lambda x: -x[1])[:10]:
    print(f"  {n:>3}  {src}")
