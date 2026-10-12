"""RAG leve: chunking por seção + TF-IDF (1-2 gramas) + similaridade do cosseno. Retorna fonte e trecho."""
import re
from dataclasses import dataclass
from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from . import config

STOP_PT = ["de", "da", "do", "das", "dos", "a", "o", "as", "os", "e", "em", "um", "uma", "para", "por", "com", "que", "na", "no",
           "nas", "nos", "se", "ao", "ou", "como", "mais", "mas", "é", "ser", "pode", "podem", "deve", "devem", "quando", "sua", "seu"]


@dataclass
class Chunk:
    source: str
    title: str
    section: str
    text: str


def _load_chunks() -> list[Chunk]:
    chunks = []
    for f in sorted(config.KB_DIR.glob("*.md")):
        title, section, buf = f.stem, "", []
        def flush():
            body = " ".join(buf).strip()
            if body:
                chunks.append(Chunk(f.name, title, section, body))
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
            elif line.startswith("## "):
                flush(); buf.clear(); section = line[3:].strip()
            elif line.strip():
                buf.append(line.strip())
        flush()
    return chunks


class Retriever:
    def __init__(self):
        self.chunks = _load_chunks()
        if not self.chunks:
            raise RuntimeError(f"Base de conhecimento vazia em {config.KB_DIR}")
        self.vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, strip_accents="unicode", lowercase=True,
                                   stop_words=[s for s in STOP_PT])
        self.mat = self.vec.fit_transform([f"{c.title}. {c.section}. {c.text}" for c in self.chunks])

    def search(self, query: str, k: int = 3, min_score: float | None = None) -> list[dict]:
        min_score = config.RAG_MIN_SCORE if min_score is None else min_score
        q = self.vec.transform([query])
        sims = linear_kernel(q, self.mat).ravel()
        order = sims.argsort()[::-1][:k]
        return [dict(source=self.chunks[i].source, title=self.chunks[i].title, section=self.chunks[i].section,
                     text=self.chunks[i].text, score=round(float(sims[i]), 3)) for i in order if sims[i] >= min_score]


@lru_cache(maxsize=1)
def get_retriever() -> Retriever:
    return Retriever()
