# -*- coding: utf-8 -*-
"""CLI commands for StarRAG."""

import argparse
import sys
from typing import Any, List

from .cards import create_star_cards
from .config import StarragConfig, load_config, save_config, init_config, find_config_file
from .embeddings import build_faiss_index
from .ingest import (
    build_stars_table_from_gaia,
    load_csv_to_sqlite,
    load_gaia_folder_to_sqlite,
)
from .output import print_result_details, print_results_table, sort_results_for_display
from .query import query_hybrid, sanity_check
from .utils import _remove_if_exists


def _apply_config_defaults(args: argparse.Namespace, config: StarragConfig) -> None:
    """Apply config defaults to args where not explicitly set."""
    if getattr(args, 'db', None) is None:
        args.db = config.db
    if getattr(args, 'index', None) is None:
        args.index = config.index
    if getattr(args, 'meta', None) is None:
        args.meta = config.meta
    if getattr(args, 'model', None) is None:
        args.model = config.model
    if getattr(args, 'device', None) is None:
        args.device = config.device
    if getattr(args, 'batch_size', None) is None:
        args.batch_size = config.batch_size
    if getattr(args, 'chunksize', None) is None:
        args.chunksize = config.chunksize
    if getattr(args, 'k', None) is None:
        args.k = config.k


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize a new config file."""
    try:
        path = init_config(name=args.name, force=args.force)
        print(f"Created config: {path}")
        print(f"  db:    {args.name}.db")
        print(f"  index: {args.name}.faiss")
        print(f"  meta:  {args.name}_meta.json")
        print("\nEdit starrag.json to customize settings.")
    except FileExistsError as e:
        print(f"Error: {e}")
        print("Use --force to overwrite.")
        sys.exit(1)


def cmd_build(args: argparse.Namespace) -> None:
    config = load_config(getattr(args, 'config', None))
    _apply_config_defaults(args, config)

    if not args.no_clean:
        print("[0/4] Cleaning old outputs (db/index/meta)...")
        _remove_if_exists(args.db)
        _remove_if_exists(args.index)
        _remove_if_exists(args.meta)

    if args.dir:
        print("[1/4] Loading Gaia folder -> SQLite raw tables...")
        load_gaia_folder_to_sqlite(
            folder=args.dir,
            db_path=args.db,
            chunksize=args.chunksize,
            limit_files=args.limit_files,
        )

        print("[2/4] Building normalized stars table (join)...")
        build_stars_table_from_gaia(args.db)
    else:
        if not args.csv:
            raise SystemExit("build requires either --csv <file> OR --dir <folder>")
        print("[1/4] Loading CSV -> SQLite (stars)...")
        load_csv_to_sqlite(args.csv, args.db, table="stars")

    print("[3/4] Building star cards...")
    create_star_cards(args.db, source_table="stars", cards_table="star_cards")

    print("[4/4] Building FAISS index...")
    build_faiss_index(
        db_path=args.db,
        index_path=args.index,
        meta_path=args.meta,
        cards_table="star_cards",
        model_name=args.model,
        batch_size=args.batch_size,
        device=args.device,
        embed_where=args.embed_where,
        heartbeat_every_rows=args.heartbeat_every_rows,
        heartbeat_every_sec=args.heartbeat_every_sec,
    )

    sanity_check(args.db, args.index, args.meta, cards_table="star_cards", source_table="stars")

    print("Done.")
    print(f"DB:    {args.db}")
    print(f"INDEX: {args.index}")
    print(f"META:  {args.meta}")


def cmd_build_gaia(args: argparse.Namespace) -> None:
    config = load_config(getattr(args, 'config', None))
    _apply_config_defaults(args, config)

    if not args.no_clean:
        print("[0/4] Cleaning old outputs (db/index/meta)...")
        _remove_if_exists(args.db)
        _remove_if_exists(args.index)
        _remove_if_exists(args.meta)

    print("[1/4] Loading Gaia folder -> SQLite raw tables...")
    load_gaia_folder_to_sqlite(
        folder=args.dir,
        db_path=args.db,
        chunksize=args.chunksize,
        limit_files=args.limit_files,
    )

    print("[2/4] Building normalized stars table (join)...")
    build_stars_table_from_gaia(args.db)

    print("[3/4] Building star cards...")
    create_star_cards(args.db, source_table="stars", cards_table="star_cards")

    print("[4/4] Building FAISS index...")
    build_faiss_index(
        db_path=args.db,
        index_path=args.index,
        meta_path=args.meta,
        cards_table="star_cards",
        model_name=args.model,
        batch_size=args.batch_size,
        device=args.device,
        embed_where=args.embed_where,
        heartbeat_every_rows=args.heartbeat_every_rows,
        heartbeat_every_sec=args.heartbeat_every_sec,
    )

    sanity_check(args.db, args.index, args.meta, cards_table="star_cards", source_table="stars")

    print("Done (Gaia ingest).")
    print(f"DB:    {args.db}")
    print(f"INDEX: {args.index}")
    print(f"META:  {args.meta}")


def cmd_query(args: argparse.Namespace) -> None:
    config = load_config(getattr(args, 'config', None))
    _apply_config_defaults(args, config)

    where = []
    params: List[Any] = []

    if args.max_dist is not None:
        where.append('d IS NOT NULL AND d <= ?')
        params.append(float(args.max_dist))

    if args.min_teff is not None:
        where.append('Teff IS NOT NULL AND Teff >= ?')
        params.append(float(args.min_teff))

    if args.max_teff is not None:
        where.append('Teff IS NOT NULL AND Teff <= ?')
        params.append(float(args.max_teff))

    if args.max_gmag is not None:
        where.append('GAIAmag IS NOT NULL AND GAIAmag <= ?')
        params.append(float(args.max_gmag))

    if args.max_mh is not None:
        where.append('MH IS NOT NULL AND MH <= ?')
        params.append(float(args.max_mh))
    if args.min_mh is not None:
        where.append('MH IS NOT NULL AND MH >= ?')
        params.append(float(args.min_mh))

    where_sql = " AND ".join(where) if where else None

    results = query_hybrid(
        db_path=args.db,
        index_path=args.index,
        meta_path=args.meta,
        q=args.q,
        k=args.k,
        where_sql=where_sql,
        params=tuple(params) if params else None,
        source_table="stars",
        cards_table="star_cards",
        device=args.device,
    )

    results = sort_results_for_display(results, args.sort)
    print_results_table(results, wide=args.wide, gaia_short=(not args.no_gaia_short))

    if args.details:
        for r in results:
            print_result_details(r, wide=args.wide)


def cmd_config_show(args: argparse.Namespace) -> None:
    """Show current configuration."""
    found = find_config_file()
    if found:
        print(f"Config file: {found}")
    else:
        print("Config file: (none found, using defaults)")

    config = load_config(getattr(args, 'config', None))
    print(f"\nCurrent settings:")
    print(f"  name:       {config.name}")
    print(f"  db:         {config.db}")
    print(f"  index:      {config.index}")
    print(f"  meta:       {config.meta}")
    print(f"  model:      {config.model}")
    print(f"  device:     {config.device}")
    print(f"  batch_size: {config.batch_size}")
    print(f"  chunksize:  {config.chunksize}")
    print(f"  k:          {config.k}")


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="starrag",
        description="StarRAG: Hybrid retrieval over star catalogs",
        epilog="""
Quick Start:
  1. Initialize config:  starrag init --name mycatalog
  2. Build index:        starrag build --csv stars.csv
  3. Query:              starrag query "cool red giant"

Examples:
  starrag init                          # Create starrag.json with defaults
  starrag init --name gaia              # Use 'gaia' as base name for files
  starrag build --csv mydata.csv        # Build from CSV file
  starrag build --dir ./gaia_chunks     # Build from Gaia folder
  starrag query "hot blue star"         # Semantic search
  starrag query "giant" --max-dist 100  # With distance filter
  starrag config                        # Show current settings
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--config", "-c", default=None, help="Path to config file (default: auto-detect)")

    sub = ap.add_subparsers(dest="cmd")

    # init command
    init_p = sub.add_parser("init", help="Initialize a new starrag.json config file")
    init_p.add_argument("--name", "-n", default="stars", help="Base name for output files (default: stars)")
    init_p.add_argument("--force", "-f", action="store_true", help="Overwrite existing config")
    init_p.set_defaults(func=cmd_init)

    # config command
    cfg_p = sub.add_parser("config", help="Show current configuration")
    cfg_p.set_defaults(func=cmd_config_show)

    # build command
    b = sub.add_parser("build", help="Build SQLite + star cards + FAISS index")
    b.add_argument("--csv", default=None, help="Single CSV input (legacy mode)")
    b.add_argument("--dir", default=None, help=r"Folder with GaiaSource_*.csv + AstrophysicalParameters_*.csv (Gaia mode)")
    b.add_argument("--db", default=None, help="SQLite database path (default from config)")
    b.add_argument("--index", default=None, help="FAISS index path (default from config)")
    b.add_argument("--meta", default=None, help="Metadata JSON path (default from config)")
    b.add_argument("--model", default=None, help="Embedding model (default from config)")
    b.add_argument("--batch-size", type=int, default=None, help="Embedding batch size (default from config)")
    b.add_argument("--device", default=None, help="Embedding device: auto|cpu|cuda")
    b.add_argument("--embed-where", default="", help="Optional SQL WHERE clause to filter star_cards for embedding")
    b.add_argument("--heartbeat-every-rows", type=int, default=0, help="Heartbeat print every N rows (0 = auto)")
    b.add_argument("--heartbeat-every-sec", type=float, default=120.0, help="Heartbeat print every N seconds")
    b.add_argument("--chunksize", type=int, default=None, help="CSV chunk size for Gaia ingestion")
    b.add_argument("--limit-files", type=int, default=0, help="For testing: ingest only first N files")
    b.add_argument("--no-clean", action="store_true", help="Do not delete old db/index/meta before building")
    b.set_defaults(func=cmd_build)

    # build-gaia command
    g = sub.add_parser("build-gaia", help="Build from Gaia folder (GaiaSource_*.csv + AstrophysicalParameters_*.csv)")
    g.add_argument("--dir", required=True, help="Folder containing GaiaSource_*.csv and AstrophysicalParameters_*.csv")
    g.add_argument("--db", default=None, help="SQLite database path (default from config)")
    g.add_argument("--index", default=None, help="FAISS index path (default from config)")
    g.add_argument("--meta", default=None, help="Metadata JSON path (default from config)")
    g.add_argument("--model", default=None, help="Embedding model (default from config)")
    g.add_argument("--batch-size", type=int, default=None, help="Embedding batch size (default from config)")
    g.add_argument("--device", default=None, help="Embedding device: auto|cpu|cuda")
    g.add_argument("--embed-where", default="", help="Optional SQL WHERE clause to filter star_cards for embedding")
    g.add_argument("--heartbeat-every-rows", type=int, default=0, help="Heartbeat print every N rows (0 = auto)")
    g.add_argument("--heartbeat-every-sec", type=float, default=120.0, help="Heartbeat print every N seconds")
    g.add_argument("--chunksize", type=int, default=None, help="CSV chunk size for ingestion")
    g.add_argument("--limit-files", type=int, default=0, help="For testing: only ingest first N files")
    g.add_argument("--no-clean", action="store_true", help="Do not delete old db/index/meta before building")
    g.set_defaults(func=cmd_build_gaia)

    # query command
    q = sub.add_parser("query", help="Hybrid query (semantic + SQL filters)")
    q.add_argument("query_text", nargs="?", default=None, help="Natural language query")
    q.add_argument("--q", default=None, help="Natural language query (alternative to positional)")
    q.add_argument("--db", default=None, help="SQLite database path (default from config)")
    q.add_argument("--index", default=None, help="FAISS index path (default from config)")
    q.add_argument("--meta", default=None, help="Metadata JSON path (default from config)")
    q.add_argument("--k", type=int, default=None, help="Number of results (default from config)")
    q.add_argument("--max-dist", type=float, default=None, help="Max distance in parsecs")
    q.add_argument("--min-teff", type=float, default=None, help="Min effective temperature (K)")
    q.add_argument("--max-teff", type=float, default=None, help="Max effective temperature (K)")
    q.add_argument("--max-gmag", type=float, default=None, help="Max Gaia G magnitude")
    q.add_argument("--max-mh", type=float, default=None, help="Max metallicity [M/H]")
    q.add_argument("--min-mh", type=float, default=None, help="Min metallicity [M/H]")
    q.add_argument("--details", action="store_true", help="Print multi-line details for each hit")
    q.add_argument("--sort", default="", help="Display sort: score|gmag|kmag|dist|teff|r|mh")
    q.add_argument("--wide", action="store_true", help="Show full long IDs")
    q.add_argument("--no-gaia-short", action="store_true", help="Do not shorten GAIA IDs")
    q.add_argument("--device", default=None, help="Query embedding device: auto|cpu|cuda")
    q.set_defaults(func=cmd_query)

    args = ap.parse_args()

    # Handle query with positional argument
    if args.cmd == "query":
        if args.query_text:
            args.q = args.query_text
        if not args.q:
            q.print_help()
            print("\nError: query text is required")
            sys.exit(1)

    if args.cmd is None:
        ap.print_help()
        sys.exit(0)

    args.func(args)
