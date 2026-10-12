"""Tiny dependency-free retrieval (TF-IDF style) over markdown files.

It is intentionally simple so the project runs anywhere. For a bigger
knowledge base you can swap this module for a vector DB (Qdrant, pgvector).
"""
import math
import re
from collections import Counter
from pathlib import Path

from .config import settings

_WORD = re.compile(r"[\w']+", re.UNICODE)
_STOP = {"the", "a", "an", "is", "are", "to", "of", "and", "or", "in", "on", "for",
         "i", "my", "me", "you", "it", "bir", "ve", "bu", "da", "de", "mi", "ne"}


def _tokens(text: str) -> list[str]:
    return [t for t in _WORD.findall(text.lower()) if t not in _STOP and len(t) > 2]


class KnowledgeBase:
    def __init__(self, directory: str):
        self.chunks: list[dict] = []
        self._load(Path(directory))
        n = max(len(self.chunks), 1)
        df: Counter = Counter()
        for c in self.chunks:
            df.update(set(c["tokens"]))
        self.idf = {t: math.log(1 + n / d) for t, d in df.items()}

    def _load(self, directory: Path) -> None:
        if not directory.exists():
            return
        for path in sorted(directory.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            for block in re.split(r"\n(?=#{1,3} )", text):
                block = block.strip()
                if len(block) > 20:
                    self.chunks.append(
                        {"source": path.name, "text": block, "tokens": _tokens(block)}
                    )

    def search(self, query: str, k: int = 2) -> list[dict]:
        q = Counter(_tokens(query))
        scored = []
        for c in self.chunks:
            tf = Counter(c["tokens"])
            score = sum(self.idf.get(t, 0) * min(tf[t], 3) * w for t, w in q.items() if t in tf)
            if score > 0:
                scored.append((score, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:k]]


_kb: "KnowledgeBase | None" = None


def get_kb() -> KnowledgeBase:
    global _kb
    if _kb is None:
        _kb = KnowledgeBase(settings.kb_dir)
    return _kb
