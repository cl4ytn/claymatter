#!/usr/bin/env python3
"""
chunk.py

Splits markdown source files in corpus/ into small, semantically coherent
chunks for the RAG retrieval store, and writes data/metadata.json.

Strategy: semi-manual / header-based. You author corpus/*.md with ## or ###
headers marking each idea boundary — the headers ARE the chunk boundaries,
decided by you as the writer. This script mechanically executes that split,
and only falls back to paragraph/sentence splitting if a section under a
header is too long, or merges a section forward if it's too short.

Each corpus file must start with a small YAML front-matter block naming its
category, so category is tagged at the content level rather than maintained
as a separate file-path mapping:

    ---
    category: projects
    ---
    ## ClayMatter
    ClayMatter is a ...

Usage:
    python chunk.py                                  # ../data/corpus/ -> ../data/metadata.json
    python chunk.py --min-words 30 --max-words 150
"""

import argparse
import json
import re
from pathlib import Path

import yaml

FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
HEADER_RE = re.compile(r"^#{2,3}\s+(.*)$", re.MULTILINE)


def parse_front_matter(text: str) -> tuple[dict, str]:
    m = FRONT_MATTER_RE.match(text)
    if not m:
        raise ValueError("missing front matter block (need '---\\ncategory: ...\\n---')")
    meta = yaml.safe_load(m.group(1)) or {}
    body = text[m.end():]
    return meta, body


def split_by_headers(body: str) -> list[tuple[str, str]]:
    """Return (header_text, section_body) pairs. Content before the first
    header, if any, is returned with header ''."""
    matches = list(HEADER_RE.finditer(body))
    if not matches:
        return [("", body.strip())]

    sections = []
    if matches[0].start() > 0:
        preamble = body[:matches[0].start()].strip()
        if preamble:
            sections.append(("", preamble))

    for i, m in enumerate(matches):
        header = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        section_body = body[start:end].strip()
        if section_body:
            sections.append((header, section_body))
    return sections


def split_long_section(text: str, max_words: int) -> list[str]:
    """Split on paragraph breaks first, then sentence boundaries, greedily
    packing up to max_words per chunk. No-op if already under the limit."""
    if len(text.split()) <= max_words:
        return [text]

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    for para in paragraphs:
        if len(para.split()) <= max_words:
            chunks.append(para)
            continue
        sentences = re.split(r"(?<=[.!?])\s+", para)
        current: list[str] = []
        current_words = 0
        for sent in sentences:
            n = len(sent.split())
            if current and current_words + n > max_words:
                chunks.append(" ".join(current))
                current, current_words = [], 0
            current.append(sent)
            current_words += n
        if current:
            chunks.append(" ".join(current))
    return chunks


def merge_short_sections(sections: list[tuple[str, str]], min_words: int) -> list[tuple[str, str]]:
    """Merge a section under min_words into the next one so no chunk is too
    small to carry context. Keeps the earlier section's header."""
    merged: list[tuple[str, str]] = []
    i = 0
    while i < len(sections):
        header, text = sections[i]
        if len(text.split()) < min_words and i + 1 < len(sections):
            next_header, next_text = sections[i + 1]
            merged.append((header, text + "\n\n" + next_text))
            i += 2
        else:
            merged.append((header, text))
            i += 1
    return merged


def chunk_file(path: Path, min_words: int, max_words: int) -> list[dict]:
    text = path.read_text()
    meta, body = parse_front_matter(text)
    if "category" not in meta:
        raise ValueError(f"{path}: front matter missing 'category'")
    category = meta["category"]

    sections = merge_short_sections(split_by_headers(body), min_words)

    chunks = []
    idx = 0
    for header, section_text in sections:
        for piece in split_long_section(section_text, max_words):
            piece = piece.strip()
            if not piece:
                continue
            chunks.append({
                "id": f"{path.stem}_{idx:03d}",
                "text": piece,
                "category": category,
                "source": str(path),
                "header": header,
                "word_count": len(piece.split()),
            })
            idx += 1
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", default="../data/corpus")
    parser.add_argument("--out", default="../data/metadata.json")
    parser.add_argument("--min-words", type=int, default=20,
                         help="sections shorter than this get merged into the next section")
    parser.add_argument("--max-words", type=int, default=150,
                         help="sections longer than this get split further")
    args = parser.parse_args()

    corpus_dir = Path(args.corpus_dir)
    md_files = sorted(corpus_dir.rglob("*.md"))
    if not md_files:
        raise SystemExit(f"no .md files found under {corpus_dir}")

    all_chunks: list[dict] = []
    for path in md_files:
        try:
            file_chunks = chunk_file(path, args.min_words, args.max_words)
        except ValueError as e:
            print(f"SKIPPED {path}: {e}")
            continue
        all_chunks.extend(file_chunks)
        print(f"{path} -> {len(file_chunks)} chunks")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(all_chunks, indent=2))

    word_counts = [c["word_count"] for c in all_chunks]
    print(f"\n{len(all_chunks)} total chunks written to {out_path}")
    if word_counts:
        print(f"word count: min={min(word_counts)} max={max(word_counts)} "
              f"avg={sum(word_counts)/len(word_counts):.0f}")


if __name__ == "__main__":
    main()