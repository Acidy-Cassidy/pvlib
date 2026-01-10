# -*- coding: utf-8 -*-
"""Star card builder for StarRAG."""

import sqlite3
from typing import Any, Dict, List

import mypandas as pd

from .utils import _row_lower_map, _safe_int, fmt, get_field, normalize_ws


def build_star_card(row: Dict[str, Any]) -> str:
    parts: List[str] = []
    row_lc = _row_lower_map(row)

    rid = _safe_int(get_field(row, row_lc, "_rid"))

    orig_id = fmt(get_field(row, row_lc, "ID"))
    gaia = fmt(get_field(row, row_lc, "GAIA"))
    twomass = fmt(get_field(row, row_lc, "TWOMASS"))
    hip = fmt(get_field(row, row_lc, "HIP"))
    objtype = fmt(get_field(row, row_lc, "objType")) or "STAR"

    title_bits = [b for b in [f"ID {orig_id}", f"GAIA {gaia}", f"2MASS {twomass}", f"HIP {hip}"]
                  if b and not b.endswith(" ")]
    if title_bits:
        parts.append(" | ".join(title_bits))

    if objtype:
        parts.append(f"type: {objtype}")

    ra = fmt(get_field(row, row_lc, "ra"), 6)
    dec = fmt(get_field(row, row_lc, "dec"), 6)
    if ra and dec:
        parts.append(f"ra: {ra} deg, dec: {dec} deg")

    pmra = fmt(get_field(row, row_lc, "pmRA"))
    pmdec = fmt(get_field(row, row_lc, "pmDEC"))
    plx = fmt(get_field(row, row_lc, "plx"))
    dist = fmt(get_field(row, row_lc, "d"))
    kin_bits = []
    if pmra or pmdec:
        kin_bits.append(f"pm: ({pmra},{pmdec}) mas/yr".replace("(,", "(").replace(",)", ")"))
    if plx:
        kin_bits.append(f"parallax: {plx} mas")
    if dist:
        kin_bits.append(f"dist: {dist} pc")
    if kin_bits:
        parts.append("; ".join(kin_bits))

    mags = []
    for label, key in [
        ("V", "Vmag"), ("B", "Bmag"), ("G", "GAIAmag"),
        ("g", "gmag"), ("r", "rmag"), ("i", "imag"), ("z", "zmag"),
        ("J", "Jmag"), ("H", "Hmag"), ("K", "Kmag"),
        ("W1", "w1mag"), ("W2", "w2mag"),
    ]:
        v = fmt(get_field(row, row_lc, key))
        if v:
            mags.append(f"{label} {v}")
    if mags:
        parts.append("mags: " + ", ".join(mags))

    teff = fmt(get_field(row, row_lc, "Teff"))
    logg = fmt(get_field(row, row_lc, "logg"))
    mh = fmt(get_field(row, row_lc, "MH"))
    rad = fmt(get_field(row, row_lc, "rad"))

    phys_bits = []
    if teff:
        phys_bits.append(f"Teff {teff} K")
    if logg:
        phys_bits.append(f"logg {logg}")
    if mh:
        phys_bits.append(f"[M/H] {mh}")
    if rad:
        phys_bits.append(f"R {rad} Rsun")
    if phys_bits:
        parts.append("params: " + ", ".join(phys_bits))

    lumclass = fmt(get_field(row, row_lc, "lumclass"))
    if lumclass:
        parts.append(f"class {lumclass}")

    out = normalize_ws(" | ".join(parts))
    if not out:
        out = f"row {rid}" if rid is not None else "star"
    return out


def create_star_cards(db_path: str, source_table: str = "stars", cards_table: str = "star_cards") -> None:
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(f'SELECT rowid as _rid, * FROM {source_table};', conn)

        cards: List[Dict[str, Any]] = []
        for _, r in df.iterrows():
            row = r.to_dict()
            rid = _safe_int(row.get("_rid"))
            if rid is None:
                continue

            card = build_star_card(row)

            cards.append({
                "ID": rid,
                "orig_ID": row.get("ID"),
                "objID": row.get("objID"),
                "card": card
            })

        cdf = pd.DataFrame(cards, columns=["ID", "orig_ID", "objID", "card"])
        cdf.to_sql(cards_table, conn, if_exists="replace", index=False)

        conn.execute(f'CREATE INDEX IF NOT EXISTS idx_{cards_table}_ID ON {cards_table}("ID");')
        conn.execute(f'CREATE INDEX IF NOT EXISTS idx_{cards_table}_objID ON {cards_table}("objID");')
        conn.execute(f'CREATE INDEX IF NOT EXISTS idx_{cards_table}_orig_ID ON {cards_table}("orig_ID");')
        conn.commit()
