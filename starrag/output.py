# -*- coding: utf-8 -*-
"""Result formatting and printing functions for StarRAG."""

import re
from typing import Any, Dict, List, Optional


def _re_find(pattern: str, text: str, flags: int = 0) -> Optional[str]:
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None


def _to_float(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def _to_int(s: Optional[str]) -> Optional[int]:
    if not s:
        return None
    try:
        return int(float(s))
    except Exception:
        return None


def shorten_id(s: Any, keep_start: int = 7, keep_end: int = 5) -> str:
    if s is None:
        return "-"
    st = str(s).strip()
    if not st or st == "None":
        return "-"
    if len(st) <= keep_start + keep_end + 3:
        return st
    return f"{st[:keep_start]}...{st[-keep_end:]}"


def summarize_card(card: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    out["type"] = _re_find(r"\btype:\s*([^\|]+)", card)

    out["ra"] = _to_float(_re_find(r"ra:\s*([0-9\.\-]+)\s*deg", card))
    out["dec"] = _to_float(_re_find(r"dec:\s*([0-9\.\-]+)\s*deg", card))

    out["dist_pc"] = _to_float(_re_find(r"dist:\s*([0-9\.\-]+)\s*pc", card))
    out["plx_mas"] = _to_float(_re_find(r"parallax:\s*([0-9\.\-]+)\s*mas", card))

    out["Kmag"] = _to_float(_re_find(r"\bK\s*([0-9\.\-]+)", card))
    out["Gmag"] = _to_float(_re_find(r"\bG\s*([0-9\.\-]+)", card))
    out["Vmag"] = _to_float(_re_find(r"\bV\s*([0-9\.\-]+)", card))

    out["Teff_K"] = _to_int(_re_find(r"Teff\s*([0-9\.\-]+)\s*K", card))
    out["R_Rsun"] = _to_float(_re_find(r"\bR\s*([0-9\.\-]+)\s*Rsun", card))

    out["MH"] = _to_float(_re_find(r"\[M/H\]\s*([0-9\.\-]+)", card))

    out["class"] = _re_find(r"\bclass\s*([A-Za-z0-9\-\_]+)", card)

    out["GAIA"] = _re_find(r"\bGAIA\s*([0-9]+)", card)
    out["HIP"] = _re_find(r"\bHIP\s*([0-9]+)", card)
    out["TWOMASS"] = _re_find(r"\b2MASS\s*([0-9A-Za-z\+\-]+)", card)

    return out


def _fmt_num(x: Any, nd: int = 3) -> str:
    if x is None:
        return "-"
    try:
        xf = float(x)
        s = f"{xf:.{nd}f}"
        s = s.rstrip("0").rstrip(".")
        return s if s else "0"
    except Exception:
        return str(x)


def _fmt_int(x: Any) -> str:
    if x is None:
        return "-"
    try:
        return str(int(x))
    except Exception:
        return str(x)


def sort_results_for_display(results: List[Dict[str, Any]], sort_key: str) -> List[Dict[str, Any]]:
    key = (sort_key or "").strip().lower()
    if key not in {"score", "gmag", "kmag", "dist", "teff", "r", "mh"}:
        return results

    def get_val(r: Dict[str, Any]) -> float:
        card = r.get("card", "") or ""
        s = summarize_card(card)
        if key == "score":
            v = r.get("score", None)
            return float(v) if v is not None else float("-inf")
        if key == "gmag":
            v = s.get("Gmag", None)
            return float(v) if v is not None else float("inf")
        if key == "kmag":
            v = s.get("Kmag", None)
            return float(v) if v is not None else float("inf")
        if key == "dist":
            v = s.get("dist_pc", None)
            return float(v) if v is not None else float("inf")
        if key == "teff":
            v = s.get("Teff_K", None)
            return float(v) if v is not None else float("inf")
        if key == "r":
            v = s.get("R_Rsun", None)
            return float(v) if v is not None else float("inf")
        if key == "mh":
            v = s.get("MH", None)
            return float(v) if v is not None else float("inf")
        return float("inf")

    reverse = True if key == "score" else False
    return sorted(results, key=get_val, reverse=reverse)


def print_results_table(results: List[Dict[str, Any]],
                        max_rows: int = 50,
                        wide: bool = False,
                        gaia_short: bool = True) -> None:
    rows: List[Dict[str, Any]] = []
    for r in results[:max_rows]:
        s = summarize_card(r.get("card", "") or "")
        gaia_val = s.get("GAIA") or "-"
        hip_val = s.get("HIP") or "-"
        if not wide and gaia_short:
            gaia_val = shorten_id(gaia_val)

        rows.append({
            "rowid": str(r.get("ID", "-")),
            "orig_ID": str(r.get("orig_ID", "-")) if r.get("orig_ID") is not None else "-",
            "score": _fmt_num(r.get("score"), 4) if r.get("score") is not None else "-",
            "G": _fmt_num(s.get("Gmag"), 3),
            "K": _fmt_num(s.get("Kmag"), 3),
            "Teff": _fmt_int(s.get("Teff_K")),
            "MH": _fmt_num(s.get("MH"), 2),
            "R": _fmt_num(s.get("R_Rsun"), 1),
            "class": s.get("class") or "-",
            "dist_pc": _fmt_num(s.get("dist_pc"), 1),
            "ra": _fmt_num(s.get("ra"), 3),
            "dec": _fmt_num(s.get("dec"), 3),
            "GAIA": gaia_val,
            "HIP": hip_val,
        })

    headers = ["rowid", "orig_ID", "score", "G", "K", "Teff", "MH", "R", "class", "dist_pc", "ra", "dec", "GAIA", "HIP"]
    right_align = {"score", "G", "K", "Teff", "MH", "R", "dist_pc", "ra", "dec"}

    widths = {h: len(h) for h in headers}
    for row in rows:
        for h in headers:
            widths[h] = max(widths[h], len(str(row.get(h, ""))))

    def sep(ch: str = "-") -> str:
        return "  ".join(ch * widths[h] for h in headers)

    def fmt_cell(h: str, v: str) -> str:
        if h in right_align:
            return v.rjust(widths[h])
        return v.ljust(widths[h])

    print(sep("-"))
    print("  ".join(fmt_cell(h, h) if h not in right_align else h.rjust(widths[h]) for h in headers))
    print(sep("="))
    for row in rows:
        print("  ".join(fmt_cell(h, str(row.get(h, ""))) for h in headers))
    print(sep("-"))
    if len(results) > max_rows:
        print(f"(showing first {max_rows} of {len(results)})")


def print_result_details(r: Dict[str, Any], wide: bool = False) -> None:
    card = r.get("card", "") or ""
    s = summarize_card(card)

    gaia = s.get("GAIA") or "-"
    hip = s.get("HIP") or "-"
    twomass = s.get("TWOMASS") or "-"
    if not wide:
        gaia = shorten_id(gaia)

    print("")
    print(f"rowid:   {r.get('ID')}   orig_ID: {r.get('orig_ID')}   score: {_fmt_num(r.get('score'), 4)}")
    print(f"type:    {s.get('type') or '-'}   class: {s.get('class') or '-'}")
    print(f"coords:  ra { _fmt_num(s.get('ra'), 6) } deg   dec { _fmt_num(s.get('dec'), 6) } deg")
    print(f"dist:    { _fmt_num(s.get('dist_pc'), 3) } pc   plx { _fmt_num(s.get('plx_mas'), 3) } mas")
    print(f"mags:    G { _fmt_num(s.get('Gmag'), 3) }   K { _fmt_num(s.get('Kmag'), 3) }   V { _fmt_num(s.get('Vmag'), 3) }")
    print(f"params:  Teff { _fmt_int(s.get('Teff_K')) } K   [M/H] { _fmt_num(s.get('MH'), 3) }   R { _fmt_num(s.get('R_Rsun'), 3) } Rsun")
    print(f"ids:     GAIA {gaia}   HIP {hip}   2MASS {twomass}")
