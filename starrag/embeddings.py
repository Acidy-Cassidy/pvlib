# -*- coding: utf-8 -*-
"""Embeddings and FAISS index building/loading for StarRAG."""

import json
import sqlite3
import time
from dataclasses import dataclass
from typing import List

import mynumpy as np
from mytqdm import tqdm

# Optional heavy deps (only needed for embedding/index steps)
try:
    import faiss  # type: ignore
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:
    faiss = None
    SentenceTransformer = None


@dataclass
class IndexMeta:
    model_name: str
    dim: int
    id_list: List[int]


def _resolve_device(user_device: str) -> str:
    """Returns "cuda" or "cpu" based on user choice and availability."""
    dev = (user_device or "auto").strip().lower()
    if dev not in {"auto", "cpu", "cuda"}:
        raise RuntimeError("--device must be one of: auto, cpu, cuda")

    if dev == "cpu":
        return "cpu"

    # auto/cuda: try to use torch if available
    try:
        import torch  # type: ignore
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass

    if dev == "cuda":
        print("[EMB] WARNING: --device cuda requested but CUDA is not available. Falling back to CPU.")
    return "cpu"


def build_faiss_index(
    db_path: str,
    index_path: str,
    meta_path: str,
    cards_table: str = "star_cards",
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    batch_size: int = 1024,
    device: str = "auto",
    embed_where: str = "",
    heartbeat_every_rows: int = 0,
    heartbeat_every_sec: float = 120.0,
) -> None:
    """
    TRUE STREAMING embedding + FAISS build:
    - does not load all cards into RAM
    - encodes batches and adds to FAISS incrementally
    - writes meta id_list at the end

    GPU:
    - if CUDA is available and --device cuda/auto, SentenceTransformer will run on GPU.

    Optional filter:
    - embed_where: SQL WHERE clause applied to star_cards selection.
      Example: "card LIKE '%Teff%'"
      Example: "ID IN (SELECT rowid FROM stars WHERE Teff IS NOT NULL OR MH IS NOT NULL)"  (advanced)

    Heartbeat:
    - prints a progress line periodically so you can confirm it's alive even if tqdm stops repainting.
    """
    if faiss is None or SentenceTransformer is None:
        raise RuntimeError("Missing deps. Install: pip install faiss-cpu sentence-transformers tqdm")

    resolved = _resolve_device(device)
    model = SentenceTransformer(model_name, device=resolved)
    print(f"[EMB] model={model_name} device={resolved} batch_size={batch_size}")

    # Heartbeat tunables (safe defaults)
    if heartbeat_every_rows <= 0:
        heartbeat_every_rows = max(batch_size * 50, 50_000)  # about every ~50 batches, at least 50k rows

    where_sql = ""
    if embed_where and embed_where.strip():
        where_sql = " WHERE " + embed_where.strip()

    with sqlite3.connect(db_path) as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM {cards_table}{where_sql};").fetchone()[0]
        if not total:
            raise RuntimeError("No rows selected for embedding. Check your --embed-where filter (or ingestion).")

        rowish = conn.execute(
            f"SELECT COUNT(*) FROM {cards_table}{where_sql} AND card LIKE 'row %';"
            if where_sql else
            f"SELECT COUNT(*) FROM {cards_table} WHERE card LIKE 'row %';"
        ).fetchone()[0]
        if rowish > int(0.8 * total):
            raise RuntimeError(
                "Cards look wrong: most cards are 'row N'.\n"
                "That means ingestion did not load expected columns.\n"
                "Fix the input ingestion first."
            )

        print(f"[EMB] Streaming encode {total} cards (batch_size={batch_size}) ...")

        cur = conn.cursor()
        cur.execute(f"SELECT ID, card FROM {cards_table}{where_sql} ORDER BY ID;")

        id_list: List[int] = []

        # Pull first batch to initialize dim + index
        first_rows = cur.fetchmany(batch_size)
        if not first_rows:
            raise RuntimeError("star_cards selection is empty after COUNT(*) said otherwise (unexpected).")

        first_ids: List[int] = []
        first_texts: List[str] = []
        for sid, card in first_rows:
            if sid is None:
                continue
            try:
                sid_i = int(sid)
            except Exception:
                continue
            first_ids.append(sid_i)
            first_texts.append("" if card is None else str(card))

        if not first_ids:
            raise RuntimeError("First batch had no valid IDs.")

        X0 = model.encode(
            first_texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        X0 = np.asarray(X0, dtype=np.float32)
        dim = int(X0.shape[1])

        index = faiss.IndexFlatIP(dim)
        index.add(X0)
        id_list.extend(first_ids)

        done = len(first_rows)

        pbar = tqdm(total=total, desc="Batches", unit="rows")
        pbar.update(done)

        # Heartbeat state
        last_hb_done = done
        last_hb_time = time.time()

        while True:
            rows = cur.fetchmany(batch_size)
            if not rows:
                break

            ids_batch: List[int] = []
            texts_batch: List[str] = []
            for sid, card in rows:
                if sid is None:
                    continue
                try:
                    sid_i = int(sid)
                except Exception:
                    continue
                ids_batch.append(sid_i)
                texts_batch.append("" if card is None else str(card))

            if ids_batch:
                X = model.encode(
                    texts_batch,
                    batch_size=batch_size,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )
                X = np.asarray(X, dtype=np.float32)
                index.add(X)
                id_list.extend(ids_batch)

            done += len(rows)
            pbar.update(len(rows))

            # Heartbeat: every N rows OR every M seconds
            now = time.time()
            if (done - last_hb_done) >= heartbeat_every_rows or (now - last_hb_time) >= heartbeat_every_sec:
                pct = (done / total * 100.0) if total else 0.0
                rate = pbar.format_dict.get("rate", None)
                rate_s = f"{rate:.2f} rows/s" if isinstance(rate, (int, float)) and rate else "?"
                print(f"[EMB] heartbeat: {done}/{total} ({pct:.2f}%)  rate={rate_s} rows/s")
                last_hb_done = done
                last_hb_time = now

        pbar.close()

    faiss.write_index(index, index_path)
    meta = IndexMeta(model_name=model_name, dim=dim, id_list=id_list)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta.__dict__, f, indent=2)

    print(f"[EMB] Done. dim={dim} ntotal={int(getattr(index, 'ntotal', 0))} meta_ids={len(id_list)}")


def load_index(index_path: str, meta_path: str, device: str = "auto"):
    if faiss is None or SentenceTransformer is None:
        raise RuntimeError("Missing deps. Install: pip install faiss-cpu sentence-transformers")

    index = faiss.read_index(index_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    resolved = _resolve_device(device)
    model = SentenceTransformer(meta["model_name"], device=resolved)
    return index, meta, model
