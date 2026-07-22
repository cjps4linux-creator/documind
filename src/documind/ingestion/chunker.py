from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Chunk:
    text: str
    chunk_index: int
    char_start: int
    char_end: int


def chunk_text(text: str, chunk_size: int = 512, chunk_overlap: int = 64) -> list[Chunk]:
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size.")
    clean = re.sub(r"\s+", " ", text).strip()
    chunks: list[Chunk] = []
    start = 0
    index = 0
    while start < len(clean):
        end = start + chunk_size
        chunks.append(Chunk(text=clean[start:end], chunk_index=index, char_start=start, char_end=min(end, len(clean))))
        start = end - chunk_overlap
        index += 1
        if start >= len(clean):
            break
    return chunks
