#!/usr/bin/env python3
"""
embed.py

Reads data/metadata.json (the chunk ledger produced by chunk.py) and writes
data/embeddings.npy — one L2-normalized embedding vector per chunk, in the
same row order as metadata.json. Row i of embeddings.npy corresponds EXACTLY
to metadata.json[i]. Never reorder, filter, or sort chunks between loading
metadata and writing embeddings — if the two files fall out of row-alignment,
every retrieval result will silently point at the wrong chunk.

Embedding model: sentence-transformers/all-MiniLM-L6-v2 (local, CPU-friendly,
384-dim). No API key required. The model itself is downloaded from Hugging
Face on first run and cached locally after that.

Retrieval note: because vectors are L2-normalized here, similarity at query
time is just a plain dot product (embeddings @ query_vec) — no separate norm
step needed later.

Usage:
    python embedder.py                  # full re-embed of every chunk
    python embedder.py --incremental    # only re-embed new/changed chunks,
                                      # reuse cached vectors for the rest
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 32

METADATA_PATH = Path("../data/metadata.json")
EMBEDDINGS_PATH = Path("../data/embeddings.npy")
CACHE_PATH = Path("../data/embeddings_cache.json")  # id -> {"hash": ..., "index": ...}


def load_metadata() -> list[dict]:
    if not METADATA_PATH.exists():
        raise SystemExit(
            f"{METADATA_PATH} not found. Run chunk.py first to generate it."
        )
    chunks = json.loads(METADATA_PATH.read_text())
    if not chunks:
        raise SystemExit(f"{METADATA_PATH} is empty — nothing to embed.")
    return chunks


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text())
    return {}


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1  # avoid divide-by-zero on a degenerate all-zero vector
    return vectors / norms


def load_model():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise SystemExit(
            "sentence-transformers is not installed. Run:\n"
            "    pip install sentence-transformers"
        )
    return SentenceTransformer(MODEL_NAME)


def embed_texts(model, texts: list[str]) -> np.ndarray:
    vectors = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return l2_normalize(vectors.astype(np.float32))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--incremental", action="store_true",
        help="reuse cached vectors for chunks whose text hasn't changed since "
             "the last run; only embed chunks that are new or edited",
    )
    args = parser.parse_args()

    chunks = load_metadata()
    model = load_model()
    dim = model.get_sentence_embedding_dimension()

    cache = load_cache() if args.incremental else {}
    old_embeddings = None
    if args.incremental and cache and EMBEDDINGS_PATH.exists():
        old_embeddings = np.load(EMBEDDINGS_PATH)

    final_vectors = np.zeros((len(chunks), dim), dtype=np.float32)
    to_embed_texts: list[str] = []
    to_embed_positions: list[int] = []
    new_cache: dict = {}
    cached_count = 0

    for i, chunk in enumerate(chunks):
        cid = chunk["id"]
        h = text_hash(chunk["text"])
        cached_entry = cache.get(cid)
        can_reuse = (
            args.incremental
            and cached_entry is not None
            and cached_entry.get("hash") == h
            and old_embeddings is not None
            and cached_entry.get("index", -1) < old_embeddings.shape[0]
        )
        if can_reuse:
            final_vectors[i] = old_embeddings[cached_entry["index"]]
            cached_count += 1
        else:
            to_embed_texts.append(chunk["text"])
            to_embed_positions.append(i)
        new_cache[cid] = {"hash": h, "index": i}

    if to_embed_texts:
        fresh_vectors = embed_texts(model, to_embed_texts)
        for pos, vec in zip(to_embed_positions, fresh_vectors):
            final_vectors[pos] = vec

    if final_vectors.shape[0] != len(chunks):
        raise SystemExit(
            f"embedding count mismatch: {final_vectors.shape[0]} vectors for "
            f"{len(chunks)} chunks. Refusing to write a misaligned file."
        )

    EMBEDDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.save(EMBEDDINGS_PATH, final_vectors)
    CACHE_PATH.write_text(json.dumps(new_cache, indent=2))

    print(f"model: {MODEL_NAME}")
    print(f"dimension: {dim}")
    print(f"batch size: {BATCH_SIZE}")
    print(f"total chunks: {len(chunks)}")
    if args.incremental:
        print(f"  reused from cache: {cached_count}")
        print(f"  freshly embedded:  {len(to_embed_texts)}")
    else:
        print(f"  freshly embedded:  {len(to_embed_texts)} (full re-embed)")
    print(f"wrote {EMBEDDINGS_PATH}  shape={final_vectors.shape}")


if __name__ == "__main__":
    main()