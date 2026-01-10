# -*- coding: utf-8 -*-
"""Hybrid retrieval and sanity check for StarRAG."""

import json
import os
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

import mynumpy as np

from .embeddings import load_index
from .output import print_results_table

# Optional dep
try:
    import faiss  # type: ignore
except Exception:
    faiss = None


def sql_filter_ids(conn: sqlite3.Connection,
                   table: str,
                   where_sql: str,
                   params: Tuple[Any, ...]) -> List[int]:
    q = f"SELECT rowid FROM {table} WHERE {where_sql};"
    rows = conn.execute(q, params).fetchall()
    out: List[int] = []
    for r in rows:
        if r and r[0] is not None:
            try:
                out.append(int(r[0]))
            except Exception:
                pass
    return out


def query_hybrid(db_path: str, index_path: str, meta_path: str,
                 q: str,
                 k: int = 10,
                 where_sql: Optional[str] = None,
                 params: Optional[Tuple[Any, ...]] = None,
                 source_table: str = "stars",
                 cards_table: str = "star_cards",
                 device: str = "auto") -> List[Dict[str, Any]]:
    index, meta, model = load_index(index_path, meta_path, device=device)

    with sqlite3.connect(db_path) as conn:
        candidates: Optional[set] = None
        if where_sql:
            ids = sql_filter_ids(conn, source_table, where_sql, params or tuple())
            candidates = set(ids)

        qv = model.encode([q], normalize_embeddings=True)
        qv = np.asarray(qv, dtype=np.float32)

        if candidates is None:
            D, I = index.search(qv, k)
            results: List[Dict[str, Any]] = []
            for score, idx in zip(D[0].tolist(), I[0].tolist()):
                if idx < 0:
                    continue
                sid = int(meta["id_list"][idx])
                row = conn.execute(
                    f'SELECT orig_ID, card FROM {cards_table} WHERE ID=?;',
                    (sid,)
                ).fetchone()
                orig_id = row[0] if row else None
                card = row[1] if row else ""
                results.append({"ID": sid, "orig_ID": orig_id, "score": float(score), "card": card})
            return results

        probe = max(k * 40, 500)
        D, I = index.search(qv, probe)

        filtered: List[Tuple[float, int]] = []
        for score, idx in zip(D[0].tolist(), I[0].tolist()):
            if idx < 0:
                continue
            sid = int(meta["id_list"][idx])
            if sid in candidates:
                filtered.append((float(score), sid))
            if len(filtered) >= k:
                break

        out: List[Dict[str, Any]] = []
        for sc, sid in filtered[:k]:
            row = conn.execute(
                f'SELECT orig_ID, card FROM {cards_table} WHERE ID=?;',
                (sid,)
            ).fetchone()
            out.append({"ID": sid, "orig_ID": row[0] if row else None, "score": sc, "card": row[1] if row else ""})
        return out


def sanity_check(db_path: str, index_path: str, meta_path: str,
                 cards_table: str = "star_cards",
                 source_table: str = "stars",
                 sample_n: int = 3) -> None:
    print("\n[SANITY] Checking DB + cards + index...")

    with sqlite3.connect(db_path) as conn:
        stars_n = conn.execute(f"SELECT COUNT(*) FROM {source_table};").fetchone()[0]
        cards_n = conn.execute(f"SELECT COUNT(*) FROM {cards_table};").fetchone()[0]
        empty_n = conn.execute(
            f"SELECT COUNT(*) FROM {cards_table} WHERE card IS NULL OR trim(card)='';"
        ).fetchone()[0]

        print(f"[SANITY] stars rows:      {stars_n}")
        print(f"[SANITY] star_cards rows: {cards_n}")
        print(f"[SANITY] empty cards:     {empty_n}")

        if cards_n == 0:
            raise RuntimeError("Sanity check failed: star_cards is empty.")
        if empty_n > 0:
            print("[SANITY] WARNING: some cards are empty.")

        rowish = conn.execute(
            f"SELECT COUNT(*) FROM {cards_table} WHERE card LIKE 'row %';"
        ).fetchone()[0]
        print(f"[SANITY] 'row N' cards:    {rowish}")

        if rowish > int(0.8 * cards_n):
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({source_table});").fetchall()]
            raise RuntimeError(
                "Sanity check failed: most cards are 'row N' (no star fields present).\n"
                f"stars table columns (first 40): {cols[:40]}\n"
                "This means ingestion did not load expected columns."
            )

        print("[SANITY] Sample cards (compact):")
        rows = conn.execute(
            f"SELECT ID, orig_ID, card FROM {cards_table} "
            f"WHERE card IS NOT NULL AND trim(card)<>'' LIMIT ?;",
            (int(sample_n),)
        ).fetchall()
        fake_results = [{"ID": rid, "orig_ID": oid, "score": None, "card": card} for (rid, oid, card) in rows]
        print_results_table(fake_results, max_rows=sample_n, wide=False, gaia_short=True)

    if faiss is None:
        raise RuntimeError("Sanity check failed: faiss not installed.")
    if not os.path.exists(index_path):
        raise RuntimeError("Sanity check failed: FAISS index file missing.")
    if not os.path.exists(meta_path):
        raise RuntimeError("Sanity check failed: meta json missing.")

    idx = faiss.read_index(index_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    ntotal = int(getattr(idx, "ntotal", 0))
    id_list_n = len(meta.get("id_list", []))
    print(f"[SANITY] FAISS ntotal:     {ntotal}")
    print(f"[SANITY] meta id_list len: {id_list_n}")

    if ntotal != id_list_n:
        raise RuntimeError("Sanity check failed: FAISS ntotal != meta id_list length.")
    if ntotal == 0:
        raise RuntimeError("Sanity check failed: FAISS index is empty.")

    print("[SANITY] OK.\n")
