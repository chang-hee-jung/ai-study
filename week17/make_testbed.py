# 17주차 2단계: 비교용 testbed 생성
#
# 실행: .\venv\Scripts\python week17\make_testbed.py
#
# 두 에이전트에게 똑같은 출발선을 준다. 한쪽이 이미 정리된 폴더를 받으면
# 비교가 안 되므로, 매번 지우고 같은 상태로 새로 만든다.

import shutil
from pathlib import Path

BENCH = Path("week17/bench")

# 12주차 testbed와 같은 구성. 확장자만 보면 어디로 갈지 알 수 있게 짰다.
FILES = {
    "보고서_1분기.txt": "1분기 실적 보고서입니다.\n",
    "메모.txt": "장보기: 우유, 계란\n",
    "매뉴얼.pdf": "%PDF-1.4 (내용은 없는 더미 파일)\n",
    "테스트스크립트.py": "print('hello')\n",
    "사진_야유회.jpg": "(jpg 더미)\n",
    "사진_워크샵.png": "(png 더미)\n",
    "백업자료.zip": "(zip 더미)\n",
}

# 채점 기준: 확장자 -> 들어가야 할 폴더
EXPECTED = {
    ".txt": "문서", ".pdf": "문서", ".py": "문서",
    ".jpg": "사진", ".png": "사진",
    ".zip": "기타",
}


def build(name: str) -> Path:
    """지정한 이름으로 깨끗한 testbed 하나를 만든다."""
    d = BENCH / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    for fname, body in FILES.items():
        (d / fname).write_text(body, encoding="utf-8")
    return d


def score(d: Path) -> dict:
    """정리 결과를 채점한다. 모델의 보고가 아니라 실제 디스크 상태로 판정한다."""
    placed, wrong, left = 0, [], []
    for fname in FILES:
        want = EXPECTED[Path(fname).suffix]
        if (d / want / fname).exists():
            placed += 1
        elif (d / fname).exists():
            left.append(fname)
        else:
            # 어딘가로 갔는데 제자리가 아니다 (또는 이름이 바뀌었다)
            found = [p for p in d.rglob(fname)]
            wrong.append(f"{fname} → {found[0].parent.name}" if found else f"{fname} 실종")
    return {"맞게 옮김": placed, "총": len(FILES), "안 옮김": left, "틀림": wrong}


if __name__ == "__main__":
    for name in ("mine", "hermes"):
        d = build(name)
        print(f"{d} 준비됨 — 파일 {len(FILES)}개")
    print("\n두 폴더가 동일한 상태다. 각각에게 같은 목표를 준다.")
