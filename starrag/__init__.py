# -*- coding: utf-8 -*-
"""StarRAG: RAG over Star Catalogs (Gaia DR3 + Legacy CSV)."""

from .cards import build_star_card, create_star_cards
from .cli import main
from .config import StarragConfig, load_config, save_config, init_config
from .embeddings import build_faiss_index, load_index
from .ingest import (
    build_stars_table_from_gaia,
    detect_format,
    load_csv_to_sqlite,
    load_gaia_folder_to_sqlite,
)
from .output import print_result_details, print_results_table, sort_results_for_display
from .query import query_hybrid, sanity_check

__all__ = [
    # Cards
    "build_star_card",
    "create_star_cards",
    # CLI
    "main",
    # Config
    "StarragConfig",
    "load_config",
    "save_config",
    "init_config",
    # Embeddings
    "build_faiss_index",
    "load_index",
    # Ingest
    "detect_format",
    "load_csv_to_sqlite",
    "load_gaia_folder_to_sqlite",
    "build_stars_table_from_gaia",
    # Output
    "print_results_table",
    "print_result_details",
    "sort_results_for_display",
    # Query
    "query_hybrid",
    "sanity_check",
]
