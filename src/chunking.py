from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        raw_sentences = re.split(r"(?<=[.!?])\s+|(?<=\.)\n", text)
        sentences = [s.strip() for s in raw_sentences if s.strip()]
        if not sentences:
            return []
        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[i : i + self.max_sentences_per_chunk]
            chunks.append(" ".join(group).strip())
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            return [current_text[i : i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        sep = remaining_separators[0]
        next_separators = remaining_separators[1:]

        if sep == "":
            return [current_text[i : i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        if sep not in current_text:
            return self._split(current_text, next_separators)

        splits = current_text.split(sep)
        chunks: list[str] = []
        current: list[str] = []
        current_len = 0

        for piece in splits:
            if len(piece) > self.chunk_size:
                if current:
                    chunks.append(sep.join(current))
                    current = []
                    current_len = 0
                sub_chunks = self._split(piece, next_separators)
                chunks.extend(sub_chunks)
            else:
                piece_len = len(piece)
                added_len = piece_len + (len(sep) if current else 0)
                if current_len + added_len <= self.chunk_size:
                    current.append(piece)
                    current_len += added_len
                else:
                    if current:
                        chunks.append(sep.join(current))
                    current = [piece]
                    current_len = piece_len

        if current:
            chunks.append(sep.join(current))

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    norm_a = math.sqrt(sum(x * x for x in vec_a))
    norm_b = math.sqrt(sum(x * x for x in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed_chunker = FixedSizeChunker(
            chunk_size=chunk_size,
            overlap=min(50, chunk_size // 2 if chunk_size < 100 else 50),
        )
        sentence_chunker = SentenceChunker()
        recursive_chunker = RecursiveChunker(chunk_size=chunk_size)

        strategies = {
            "fixed_size": fixed_chunker.chunk(text),
            "by_sentences": sentence_chunker.chunk(text),
            "recursive": recursive_chunker.chunk(text),
        }

        results: dict = {}
        for name, chunks in strategies.items():
            count = len(chunks)
            avg_length = sum(len(c) for c in chunks) / count if count > 0 else 0.0
            results[name] = {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks,
            }
        return results


class MarkdownHeadingChunker:
    """
    Split markdown text by structural headings (e.g. #, ##, ###).

    Each section (heading + associated body) becomes an independent semantic chunk.
    If any section exceeds max_chunk_size, it is further split using RecursiveChunker.
    """

    def __init__(self, max_chunk_size: int = 1500) -> None:
        self.max_chunk_size = max_chunk_size
        self._fallback = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        pattern = r"(?m)^(#+\s+.+)$"
        splits = re.split(pattern, text)

        sections: list[str] = []
        if splits[0].strip():
            sections.append(splits[0].strip())

        i = 1
        while i < len(splits):
            heading = splits[i].strip()
            content = splits[i + 1].strip() if i + 1 < len(splits) else ""
            section_text = f"{heading}\n\n{content}".strip() if content else heading
            if section_text:
                sections.append(section_text)
            i += 2

        if not sections:
            return self._fallback.chunk(text)

        chunks: list[str] = []
        for sec in sections:
            if len(sec) > self.max_chunk_size:
                chunks.extend(self._fallback.chunk(sec))
            else:
                chunks.append(sec)

        return chunks


HeadingChunker = MarkdownHeadingChunker
