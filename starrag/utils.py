# -*- coding: utf-8 -*-
"""General utility functions for StarRAG."""

import math
import os
import re
from typing import Any, Dict, Optional

import mynumpy as np


def _is_nan(x: Any) -> bool:
    try:
        return x is None or (isinstance(x, float) and math.isnan(x))
    except Exception:
        return False


def fmt(x: Any, nd: int = 3) -> str:
    if _is_nan(x) or x == "":
        return ""
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    if isinstance(x, (float, np.floating)):
        s = f"{float(x):.{nd}f}"
        s = s.rstrip("0").rstrip(".")
        return s
    return str(x)


def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _safe_int(x: Any) -> Optional[int]:
    if _is_nan(x) or x == "":
        return None
    try:
        return int(float(x))
    except Exception:
        return None


def _row_lower_map(row: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in row.items():
        if k is None:
            continue
        out[str(k).strip().lower()] = v
    return out


def get_field(row: Dict[str, Any], row_lc: Dict[str, Any], key: str) -> Any:
    if key in row:
        return row.get(key)
    return row_lc.get(key.strip().lower())


def _remove_if_exists(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def _norm_colname(c: Any) -> str:
    """Normalize CSV column names to stable SQLite column names."""
    return str(c).strip().strip('"').strip("'").strip().lower()


def _pick_id_col(cols: set) -> Optional[str]:
    """
    Auto-detect the Gaia ID/join key across common export variants.
    Assumes cols are normalized (lowercase).
    """
    candidates = [
        "source_id",
        "sourceid",
        "gaia_source_id",
        "gaia_sourceid",
        "designation",
        "id",
    ]
    for want in candidates:
        if want in cols:
            return want
    return None
