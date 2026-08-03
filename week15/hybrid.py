r"""15주차: 하이브리드 검색 (벡터 + BM25 키워드)

[왜]
59문항으로 넓히니 검색 실패 7건이 나왔고, 전부 같은 성격이었다 — **어휘 충돌**.
질문에 쓰인 흔한 단어와 겉모양이 같은 엉뚱한 문서가 1등을 한다.

  "**파일명**과 클래스명이 어긋난 사례" -> 파일명-시각-규약.md (정답은 SnowAccumulator.md)
  "3D 화면을 **좌우**로 이동"          -> 메시-생성.md(X축 좌우 반전) (정답은 외부-의존성.md)
  "**적설값이 0**이면 IR 질감"          -> 지리산-적설값-결측.md (정답은 높이-합성-공식.md)

정답 문서에는 `클래스명`, `우클릭 드래그`, `질감`, `csv.gz` 같은 **드문 단어**가 박혀 있다.
벡터는 주제 유사도를 보느라 그걸 놓치고, 키워드 검색은 정확히 그걸 잡는다.

[방식]
- BM25를 외부 패키지 없이 직접 구현. 조각이 143개뿐이라 매번 만들어도 부담 없다
- 한국어라 형태소 분석기가 없으므로 **띄어쓰기 토큰 + 글자 2-gram**을 함께 쓴다
  ("클래스명"이 통째로 안 잘려도 "클래", "래스", "스명"으로 걸린다)
- 두 검색을 점수로 섞지 않고 **순위로 합친다(RRF)**. 점수 정규화가 필요 없고,
  한쪽이 이상한 값을 내도 덜 흔들린다.  score = Σ 1/(k + 순위),  k=60

사용: ask_wiki.py에서 $env:ASK_HYBRID = "1"
"""

import math
import re

K1 = 1.5
B = 0.75
RRF_K = 60

WORD = re.compile(r"[a-zA-Z0-9_.]+")
HANGUL = re.compile(r"[가-힣]+")


def tokenize(text):
    """띄어쓰기 토큰 + 한글 2-gram. 형태소 분석기 없이 한국어를 다루는 최소한의 방법."""
    t = text.lower()
    tokens = WORD.findall(t)
    for run in HANGUL.findall(t):
        tokens.append(run)
        for i in range(len(run) - 1):
            tokens.append(run[i : i + 2])
    return tokens


class BM25:
    def __init__(self, docs):
        self.docs = [tokenize(d) for d in docs]
        self.n = len(self.docs)
        self.len = [len(d) for d in self.docs]
        self.avglen = sum(self.len) / max(self.n, 1)

        self.tf = []
        df = {}
        for toks in self.docs:
            counts = {}
            for w in toks:
                counts[w] = counts.get(w, 0) + 1
            self.tf.append(counts)
            for w in counts:
                df[w] = df.get(w, 0) + 1

        self.idf = {
            w: math.log(1 + (self.n - c + 0.5) / (c + 0.5)) for w, c in df.items()
        }

    def scores(self, query):
        q = tokenize(query)
        out = [0.0] * self.n
        for w in q:
            idf = self.idf.get(w)
            if idf is None:
                continue
            for i, counts in enumerate(self.tf):
                f = counts.get(w)
                if not f:
                    continue
                denom = f + K1 * (1 - B + B * self.len[i] / self.avglen)
                out[i] += idf * f * (K1 + 1) / denom
        return out

    def top(self, query, k):
        s = self.scores(query)
        order = sorted(range(self.n), key=lambda i: -s[i])
        return [i for i in order[:k] if s[i] > 0]


def rrf(rankings, k=RRF_K):
    """여러 검색 결과를 순위로 합친다. rankings = [[idx...], [idx...]]"""
    score = {}
    for ranked in rankings:
        for rank, idx in enumerate(ranked, start=1):
            score[idx] = score.get(idx, 0.0) + 1.0 / (k + rank)
    return sorted(score, key=lambda i: -score[i])
