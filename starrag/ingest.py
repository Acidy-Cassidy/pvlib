# -*- coding: utf-8 -*-
"""CSV ingestion and SQLite loading for StarRAG."""

import csv
import sqlite3
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

import mypandas as pd

from .utils import _norm_colname, _pick_id_col

WANTED_COLS = {
    "id", "objid", "objtype",
    "ra", "dec",
    "teff", "logg", "mh",
    "kmag", "jmag", "hmag", "gaiamag",
    "plx", "d",
}

DELIMS = [",", "\t", "|", ";"]


def _read_head_lines(path: str, n: int = 200) -> List[str]:
    lines: List[str] = []
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        for _ in range(n):
            try:
                lines.append(next(f))
            except StopIteration:
                break
    return lines


def _parse_cols(line: str, delim: str) -> List[str]:
    try:
        row = next(csv.reader([line], delimiter=delim))
        return [c.strip().strip('"').strip() for c in row]
    except Exception:
        return []


def _score_header_candidate(line: str, delim: str) -> Tuple[int, int]:
    cols = _parse_cols(line, delim)
    cols_lc = [c.lower() for c in cols if c]
    hits = len(set(cols_lc).intersection(WANTED_COLS))
    ncols = len(cols_lc)
    return hits, ncols


def detect_format(csv_path: str) -> Tuple[str, int, List[str]]:
    head_lines = _read_head_lines(csv_path, n=200)

    best_delim = ","
    best_idx = 0
    best_hits = -1
    best_ncols = -1

    for i, line in enumerate(head_lines):
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            continue

        for d in DELIMS:
            hits, ncols = _score_header_candidate(line, d)
            if hits > best_hits or (hits == best_hits and ncols > best_ncols):
                best_hits, best_ncols = hits, ncols
                best_delim, best_idx = d, i

    return best_delim, best_idx, head_lines


def load_csv_to_sqlite(csv_path: str, db_path: str, table: str = "stars") -> None:
    delim, header_idx, head_lines = detect_format(csv_path)
    skiprows = header_idx

    try:
        df = pd.read_csv(
            csv_path,
            sep=delim,
            skiprows=skiprows,
            header=0,
            encoding="utf-8",
            engine="python",
            on_bad_lines="skip",
        )
    except Exception:
        df = pd.read_csv(
            csv_path,
            sep=delim,
            skiprows=skiprows,
            header=0,
            encoding="utf-8",
            engine="c",
            low_memory=False,
        )

    df.columns = [str(c).strip() for c in df.columns]
    cols_lc = set([c.lower() for c in df.columns])

    hits = len(cols_lc.intersection(WANTED_COLS))
    if hits < 3:
        header_preview = head_lines[header_idx].rstrip("\n") if header_idx < len(head_lines) else ""
        raise RuntimeError(
            "CSV parse sanity failed: not enough known columns detected.\n"
            f"Detected delimiter={repr(delim)} header_line_index={header_idx}\n"
            f"Header line preview: {header_preview[:200]}\n"
            f"Parsed columns (first 30): {df.columns[:30].tolist()}\n"
            "This means the file has a different delimiter/header layout than expected."
        )

    with sqlite3.connect(db_path) as conn:
        df.to_sql(table, conn, if_exists="replace", index=False)

        idx_cols = ["ID", "objID", "ra", "dec", "d", "Teff", "Kmag", "GAIAmag", "plx", "MH"]
        for col in idx_cols:
            if col in df.columns:
                conn.execute(f'CREATE INDEX IF NOT EXISTS idx_{table}_{col} ON {table}("{col}");')
        conn.commit()


# -----------------------------
# Gaia folder ingest
# -----------------------------

def _iter_files(folder: str, pattern: str) -> List[str]:
    p = Path(folder)
    return sorted([str(x) for x in p.glob(pattern) if x.is_file()])


def _score_gaia_header(line: str, delim: str) -> int:
    cols = [_norm_colname(c) for c in line.split(delim)]
    wanted = {"source_id", "sourceid", "ra", "dec", "parallax", "pmra", "pmdec", "phot_g_mean_mag", "teff_gspphot"}
    return len(set(cols) & wanted)


def _detect_csv_layout(path: str) -> Tuple[str, int]:
    """
    Returns (delimiter, skiprows) for Gaia chunk CSVs.

    Robust against:
      - UTF-8 BOM
      - Excel "sep=," preamble line
      - ECSV metadata lines like "# %ECSV 1.0" (and any "# ..." YAML comment block)
      - leading whitespace before '#'
      - header line not being the first line
      - delimiter could be ',', ';', '\t', or '|'
    """
    delims = [",", ";", "\t", "|"]

    lines: List[str] = []
    with open(path, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
        for _ in range(800):
            try:
                lines.append(next(f))
            except StopIteration:
                break

    if not lines:
        return ",", 0

    hinted_delim: Optional[str] = None
    candidates: List[Tuple[int, int, str]] = []  # (score, idx, delim)

    for i, raw in enumerate(lines):
        line_stripped = raw.strip()
        if not line_stripped:
            continue

        # Excel delimiter hint (not a comment)
        if line_stripped.lower().startswith("sep=") and len(line_stripped) >= 5:
            hinted = line_stripped[4]
            if hinted in delims:
                hinted_delim = hinted
            continue

        # Skip comment/metadata lines (ECSV uses these heavily)
        if raw.lstrip().startswith("#"):
            continue

        # Evaluate this line as a possible header for each delimiter
        for d in delims:
            score = _score_gaia_header(line_stripped, d)
            ncols = len(line_stripped.split(d))
            candidates.append((score * 1000 + ncols, i, d))

    if not candidates:
        return (hinted_delim or ","), 0

    candidates.sort(reverse=True)
    best_score, best_idx, best_delim = candidates[0]

    if hinted_delim is not None:
        hinted_candidates = [c for c in candidates if c[2] == hinted_delim]
        if hinted_candidates:
            hinted_best = hinted_candidates[0]
            if (best_score - hinted_best[0]) < 1000:
                best_score, best_idx, best_delim = hinted_best

    return best_delim, best_idx


def _read_csv_chunks(path: str, chunksize: int) -> Iterator[pd.DataFrame]:
    """
    Chunked CSV reader with:
      - auto delimiter detection
      - skips preamble/header offset
      - ignores comment lines (ECSV metadata) via comment="#"
    This is a true generator (no list(it) materialization).
    """
    delim, skiprows = _detect_csv_layout(path)

    try:
        it = pd.read_csv(
            path,
            sep=delim,
            skiprows=skiprows,
            header=0,
            encoding="utf-8-sig",
            engine="c",
            low_memory=False,
            chunksize=chunksize,
            on_bad_lines="skip",
            comment="#",
        )
    except TypeError:
        it = pd.read_csv(
            path,
            sep=delim,
            skiprows=skiprows,
            header=0,
            encoding="utf-8-sig",
            engine="python",
            chunksize=chunksize,
            on_bad_lines="skip",
        )

    for chunk in it:
        yield chunk


def load_gaia_folder_to_sqlite(folder: str, db_path: str, chunksize: int = 200_000,
                              limit_files: int = 0) -> None:
    gaia_files = _iter_files(folder, "GaiaSource_*.csv")
    ap_files = _iter_files(folder, "AstrophysicalParameters_*.csv")

    if limit_files and limit_files > 0:
        gaia_files = gaia_files[:limit_files]
        ap_files = ap_files[:limit_files]

    if not gaia_files:
        raise RuntimeError(f"No GaiaSource_*.csv files found in {folder}")
    if not ap_files:
        raise RuntimeError(f"No AstrophysicalParameters_*.csv files found in {folder}")

    with sqlite3.connect(db_path) as conn:
        conn.execute("DROP TABLE IF EXISTS gaia_source_raw;")
        conn.execute("DROP TABLE IF EXISTS gaia_astro_raw;")
        conn.commit()

        print(f"[GAIA] Loading {len(gaia_files)} GaiaSource files into gaia_source_raw ...")
        first = True
        for fp in gaia_files:
            print(f"  - {fp}")
            for chunk in _read_csv_chunks(fp, chunksize=chunksize):
                chunk.columns = [_norm_colname(c) for c in chunk.columns]
                chunk.to_sql("gaia_source_raw", conn, if_exists="replace" if first else "append", index=False)
                first = False

        print(f"[GAIA] Loading {len(ap_files)} AstrophysicalParameters files into gaia_astro_raw ...")
        first = True
        for fp in ap_files:
            print(f"  - {fp}")
            for chunk in _read_csv_chunks(fp, chunksize=chunksize):
                chunk.columns = [_norm_colname(c) for c in chunk.columns]
                chunk.to_sql("gaia_astro_raw", conn, if_exists="replace" if first else "append", index=False)
                first = False

        print("[GAIA] Creating indexes ...")

        def cols_of(table: str) -> set:
            rows = conn.execute(f"PRAGMA table_info({table});").fetchall()
            return set([_norm_colname(r[1]) for r in rows])

        src_cols = cols_of("gaia_source_raw")
        ap_cols = cols_of("gaia_astro_raw")

        src_id = _pick_id_col(src_cols)
        ap_id = _pick_id_col(ap_cols)

        if src_id:
            try:
                conn.execute(f'CREATE INDEX IF NOT EXISTS idx_gaia_source_raw_{src_id} ON gaia_source_raw("{src_id}");')
            except Exception:
                pass
        if ap_id:
            try:
                conn.execute(f'CREATE INDEX IF NOT EXISTS idx_gaia_astro_raw_{ap_id} ON gaia_astro_raw("{ap_id}");')
            except Exception:
                pass

        conn.commit()


def build_stars_table_from_gaia(db_path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("DROP TABLE IF EXISTS stars;")
        conn.commit()

        def cols_of(table: str) -> set:
            rows = conn.execute(f"PRAGMA table_info({table});").fetchall()
            return set([_norm_colname(r[1]) for r in rows])

        src_cols = cols_of("gaia_source_raw")
        ap_cols = cols_of("gaia_astro_raw")

        src_id = _pick_id_col(src_cols)
        ap_id = _pick_id_col(ap_cols)

        if not src_id:
            raise RuntimeError(
                "gaia_source_raw missing an ID/join column.\n"
                "Expected one of: source_id, sourceid, gaia_source_id, designation, id\n"
                f"Have (first 80): {sorted(list(src_cols))[:80]}"
            )
        if not ap_id:
            raise RuntimeError(
                "gaia_astro_raw missing an ID/join column.\n"
                "Expected one of: source_id, sourceid, gaia_source_id, designation, id\n"
                f"Have (first 80): {sorted(list(ap_cols))[:80]}"
            )

        ra_col = "ra" if "ra" in src_cols else None
        dec_col = "dec" if "dec" in src_cols else None
        plx_col = "parallax" if "parallax" in src_cols else None
        pmra_col = "pmra" if "pmra" in src_cols else None
        pmdec_col = "pmdec" if "pmdec" in src_cols else None
        gmag_col = "phot_g_mean_mag" if "phot_g_mean_mag" in src_cols else None

        teff_col = "teff_gspphot" if "teff_gspphot" in ap_cols else ("teff" if "teff" in ap_cols else None)
        logg_col = "logg_gspphot" if "logg_gspphot" in ap_cols else ("logg" if "logg" in ap_cols else None)
        mh_col = "mh_gspphot" if "mh_gspphot" in ap_cols else ("mh" if "mh" in ap_cols else None)
        rad_col = "radius_gspphot" if "radius_gspphot" in ap_cols else ("radius" if "radius" in ap_cols else None)

        sel = []
        sel.append(f's."{src_id}" AS "GAIA"')
        sel.append(f's."{src_id}" AS "ID"')

        sel.append(f's."{ra_col}" AS "ra"' if ra_col else 'NULL AS "ra"')
        sel.append(f's."{dec_col}" AS "dec"' if dec_col else 'NULL AS "dec"')
        sel.append(f's."{pmra_col}" AS "pmRA"' if pmra_col else 'NULL AS "pmRA"')
        sel.append(f's."{pmdec_col}" AS "pmDEC"' if pmdec_col else 'NULL AS "pmDEC"')

        if plx_col:
            sel.append(f's."{plx_col}" AS "plx"')
            sel.append(f'CASE WHEN s."{plx_col}" > 0 THEN 1000.0 / s."{plx_col}" ELSE NULL END AS "d"')
        else:
            sel.append('NULL AS "plx"')
            sel.append('NULL AS "d"')

        sel.append(f's."{gmag_col}" AS "GAIAmag"' if gmag_col else 'NULL AS "GAIAmag"')
        sel.append(f'a."{teff_col}" AS "Teff"' if teff_col else 'NULL AS "Teff"')
        sel.append(f'a."{logg_col}" AS "logg"' if logg_col else 'NULL AS "logg"')
        sel.append(f'a."{mh_col}" AS "MH"' if mh_col else 'NULL AS "MH"')
        sel.append(f'a."{rad_col}" AS "rad"' if rad_col else 'NULL AS "rad"')

        q = f"""
        CREATE TABLE stars AS
        SELECT
          {", ".join(sel)}
        FROM gaia_source_raw s
        LEFT JOIN gaia_astro_raw a
          ON a."{ap_id}" = s."{src_id}";
        """
        print(f"[GAIA] Building normalized stars table (join on {src_id}) ...")
        conn.execute(q)
        conn.commit()

        print("[GAIA] Creating stars indexes ...")
        for col in ["ID", "GAIA", "ra", "dec", "d", "Teff", "MH", "GAIAmag", "plx"]:
            try:
                conn.execute(f'CREATE INDEX IF NOT EXISTS idx_stars_{col} ON stars("{col}");')
            except Exception:
                pass
        conn.commit()
