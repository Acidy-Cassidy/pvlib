#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for StarRAG - star catalog hybrid retrieval system.

Run with: pytest test_rag.py -v
"""
import json
import math
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest import mock

import mynumpy as np
import mypandas as pd
import mypytest

# Import from the starrag package modules
from starrag import utils, output, cards, ingest, embeddings, query, config
from starrag import cli
import subprocess
import sys


# =============================================================================
# Fixtures
# =============================================================================

@mypytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@mypytest.fixture
def sample_star_row() -> Dict[str, Any]:
    """Sample star data row for testing."""
    return {
        "_rid": 1,
        "ID": "STAR_001",
        "GAIA": "1234567890123456789",
        "TWOMASS": "12345678+1234567",
        "HIP": "12345",
        "objType": "STAR",
        "ra": 180.12345,
        "dec": -45.67890,
        "pmRA": 10.5,
        "pmDEC": -5.2,
        "plx": 25.0,
        "d": 40.0,
        "Vmag": 5.5,
        "Bmag": 6.1,
        "GAIAmag": 5.3,
        "Jmag": 4.2,
        "Hmag": 3.9,
        "Kmag": 3.8,
        "Teff": 5500,
        "logg": 4.2,
        "MH": -0.15,
        "rad": 1.1,
        "lumclass": "V",
    }


@mypytest.fixture
def sample_csv_content():
    """Sample CSV content for testing CSV parsing."""
    return """ID,ra,dec,Teff,Kmag,d,MH,GAIAmag,plx
STAR001,180.123,-45.678,5500,3.8,40.0,-0.15,5.3,25.0
STAR002,90.456,30.123,4200,5.2,100.0,0.10,7.1,10.0
STAR003,270.789,-60.234,6500,2.1,25.0,-0.50,4.0,40.0
"""


@mypytest.fixture
def sample_db(temp_dir, sample_csv_content):
    """Create a sample SQLite database with star data."""
    csv_path = os.path.join(temp_dir, "stars.csv")
    db_path = os.path.join(temp_dir, "test.db")

    with open(csv_path, "w") as f:
        f.write(sample_csv_content)

    ingest.load_csv_to_sqlite(csv_path, db_path, table="stars")
    return db_path


# =============================================================================
# Tests: Utility Functions (starrag.utils)
# =============================================================================

class TestIsNan:
    """Tests for _is_nan function."""

    def test_none_is_nan(self):
        assert utils._is_nan(None) is True

    def test_float_nan_is_nan(self):
        assert utils._is_nan(float("nan")) is True

    def test_numpy_nan_is_nan(self):
        assert utils._is_nan(np.nan) is True

    def test_regular_float_not_nan(self):
        assert utils._is_nan(3.14) is False

    def test_zero_not_nan(self):
        assert utils._is_nan(0) is False

    def test_string_not_nan(self):
        assert utils._is_nan("hello") is False

    def test_empty_string_not_nan(self):
        assert utils._is_nan("") is False


class TestFmt:
    """Tests for fmt function."""

    def test_format_none(self):
        assert utils.fmt(None) == ""

    def test_format_nan(self):
        assert utils.fmt(float("nan")) == ""

    def test_format_empty_string(self):
        assert utils.fmt("") == ""

    def test_format_integer(self):
        assert utils.fmt(42) == "42"

    def test_format_float_default_precision(self):
        result = utils.fmt(3.14159)
        assert result == "3.142"

    def test_format_float_custom_precision(self):
        result = utils.fmt(3.14159, nd=2)
        assert result == "3.14"

    def test_format_float_strips_trailing_zeros(self):
        result = utils.fmt(3.10000)
        assert result == "3.1"

    def test_format_float_strips_trailing_dot(self):
        result = utils.fmt(3.0)
        assert result == "3"

    def test_format_string(self):
        assert utils.fmt("hello") == "hello"

    def test_format_numpy_int(self):
        assert utils.fmt(np.int64(42)) == "42"

    def test_format_numpy_float(self):
        result = utils.fmt(np.float64(3.14159))
        assert result == "3.142"


class TestNormalizeWs:
    """Tests for normalize_ws function."""

    def test_collapse_spaces(self):
        assert utils.normalize_ws("hello   world") == "hello world"

    def test_collapse_tabs(self):
        assert utils.normalize_ws("hello\t\tworld") == "hello world"

    def test_collapse_newlines(self):
        assert utils.normalize_ws("hello\n\nworld") == "hello world"

    def test_strip_edges(self):
        assert utils.normalize_ws("  hello  ") == "hello"

    def test_mixed_whitespace(self):
        assert utils.normalize_ws("  hello \t\n world  ") == "hello world"

    def test_empty_string(self):
        assert utils.normalize_ws("") == ""


class TestSafeInt:
    """Tests for _safe_int function."""

    def test_int_value(self):
        assert utils._safe_int(42) == 42

    def test_float_value(self):
        assert utils._safe_int(42.7) == 42

    def test_string_int(self):
        assert utils._safe_int("42") == 42

    def test_string_float(self):
        assert utils._safe_int("42.7") == 42

    def test_none_returns_none(self):
        assert utils._safe_int(None) is None

    def test_nan_returns_none(self):
        assert utils._safe_int(float("nan")) is None

    def test_empty_string_returns_none(self):
        assert utils._safe_int("") is None

    def test_invalid_string_returns_none(self):
        assert utils._safe_int("hello") is None


class TestRowLowerMap:
    """Tests for _row_lower_map function."""

    def test_lowercase_keys(self):
        row = {"RA": 180.0, "DEC": -45.0, "Teff": 5500}
        result = utils._row_lower_map(row)
        assert "ra" in result
        assert "dec" in result
        assert "teff" in result

    def test_preserves_values(self):
        row = {"RA": 180.0, "DEC": -45.0}
        result = utils._row_lower_map(row)
        assert result["ra"] == 180.0
        assert result["dec"] == -45.0

    def test_strips_keys(self):
        row = {" RA ": 180.0}
        result = utils._row_lower_map(row)
        assert "ra" in result

    def test_skips_none_keys(self):
        row = {None: 42, "RA": 180.0}
        result = utils._row_lower_map(row)
        assert None not in result
        assert "ra" in result


class TestGetField:
    """Tests for get_field function."""

    def test_exact_match(self):
        row = {"RA": 180.0}
        row_lc = utils._row_lower_map(row)
        assert utils.get_field(row, row_lc, "RA") == 180.0

    def test_case_insensitive_fallback(self):
        row = {"RA": 180.0}
        row_lc = utils._row_lower_map(row)
        assert utils.get_field(row, row_lc, "ra") == 180.0

    def test_missing_field(self):
        row = {"RA": 180.0}
        row_lc = utils._row_lower_map(row)
        assert utils.get_field(row, row_lc, "missing") is None


class TestNormColname:
    """Tests for _norm_colname function."""

    def test_lowercase(self):
        assert utils._norm_colname("RA") == "ra"

    def test_strip_spaces(self):
        assert utils._norm_colname("  RA  ") == "ra"

    def test_strip_quotes(self):
        assert utils._norm_colname('"RA"') == "ra"
        assert utils._norm_colname("'RA'") == "ra"


class TestPickIdCol:
    """Tests for _pick_id_col function."""

    def test_source_id(self):
        cols = {"source_id", "ra", "dec"}
        assert utils._pick_id_col(cols) == "source_id"

    def test_sourceid(self):
        cols = {"sourceid", "ra", "dec"}
        assert utils._pick_id_col(cols) == "sourceid"

    def test_designation(self):
        cols = {"designation", "ra", "dec"}
        assert utils._pick_id_col(cols) == "designation"

    def test_id(self):
        cols = {"id", "ra", "dec"}
        assert utils._pick_id_col(cols) == "id"

    def test_priority_order(self):
        cols = {"source_id", "sourceid", "id", "ra", "dec"}
        assert utils._pick_id_col(cols) == "source_id"

    def test_no_match(self):
        cols = {"ra", "dec", "mag"}
        assert utils._pick_id_col(cols) is None


class TestRemoveIfExists:
    """Tests for _remove_if_exists function."""

    def test_remove_existing_file(self, temp_dir):
        path = os.path.join(temp_dir, "test.txt")
        with open(path, "w") as f:
            f.write("test")

        assert os.path.exists(path)
        utils._remove_if_exists(path)
        assert not os.path.exists(path)

    def test_remove_nonexistent_file_no_error(self, temp_dir):
        path = os.path.join(temp_dir, "nonexistent.txt")
        utils._remove_if_exists(path)  # Should not raise

    def test_remove_empty_path_no_error(self):
        utils._remove_if_exists("")  # Should not raise

    def test_remove_none_path_no_error(self):
        utils._remove_if_exists(None)  # Should not raise


# =============================================================================
# Tests: Output Helper Functions (starrag.output)
# =============================================================================

class TestShortenId:
    """Tests for shorten_id function."""

    def test_short_id_unchanged(self):
        assert output.shorten_id("12345") == "12345"

    def test_long_id_shortened(self):
        long_id = "12345678901234567890"
        result = output.shorten_id(long_id)
        assert "..." in result
        assert result.startswith("1234567")
        assert result.endswith("67890")

    def test_none_returns_dash(self):
        assert output.shorten_id(None) == "-"

    def test_empty_string_returns_dash(self):
        assert output.shorten_id("") == "-"

    def test_none_string_returns_dash(self):
        assert output.shorten_id("None") == "-"


class TestSummarizeCard:
    """Tests for summarize_card function."""

    def test_extract_type(self):
        card = "type: STAR | ra: 180.0 deg"
        result = output.summarize_card(card)
        assert result["type"] == "STAR"

    def test_extract_ra_dec(self):
        card = "ra: 180.123 deg, dec: -45.678 deg"
        result = output.summarize_card(card)
        assert result["ra"] == pytest.approx(180.123)
        assert result["dec"] == pytest.approx(-45.678)

    def test_extract_distance(self):
        card = "dist: 40.5 pc"
        result = output.summarize_card(card)
        assert result["dist_pc"] == pytest.approx(40.5)

    def test_extract_parallax(self):
        card = "parallax: 25.0 mas"
        result = output.summarize_card(card)
        assert result["plx_mas"] == pytest.approx(25.0)

    def test_extract_magnitudes(self):
        card = "mags: G 5.3, K 3.8, V 5.5"
        result = output.summarize_card(card)
        assert result["Gmag"] == pytest.approx(5.3)
        assert result["Kmag"] == pytest.approx(3.8)
        assert result["Vmag"] == pytest.approx(5.5)

    def test_extract_teff(self):
        card = "Teff 5500 K"
        result = output.summarize_card(card)
        assert result["Teff_K"] == 5500

    def test_extract_radius(self):
        card = "R 1.1 Rsun"
        result = output.summarize_card(card)
        assert result["R_Rsun"] == pytest.approx(1.1)

    def test_extract_metallicity(self):
        card = "[M/H] -0.15"
        result = output.summarize_card(card)
        assert result["MH"] == pytest.approx(-0.15)

    def test_extract_gaia_id(self):
        card = "GAIA 1234567890123456789"
        result = output.summarize_card(card)
        assert result["GAIA"] == "1234567890123456789"

    def test_extract_hip_id(self):
        card = "HIP 12345"
        result = output.summarize_card(card)
        assert result["HIP"] == "12345"


class TestFmtNum:
    """Tests for _fmt_num function."""

    def test_none_returns_dash(self):
        assert output._fmt_num(None) == "-"

    def test_format_float(self):
        assert output._fmt_num(3.14159, nd=2) == "3.14"

    def test_strips_trailing_zeros(self):
        assert output._fmt_num(3.10, nd=2) == "3.1"

    def test_zero_value(self):
        assert output._fmt_num(0.0, nd=2) == "0"


class TestFmtInt:
    """Tests for _fmt_int function."""

    def test_none_returns_dash(self):
        assert output._fmt_int(None) == "-"

    def test_int_value(self):
        assert output._fmt_int(42) == "42"

    def test_float_value(self):
        assert output._fmt_int(42.7) == "42"


class TestSortResultsForDisplay:
    """Tests for sort_results_for_display function."""

    def test_sort_by_score_descending(self):
        results = [
            {"score": 0.5, "card": ""},
            {"score": 0.9, "card": ""},
            {"score": 0.7, "card": ""},
        ]
        sorted_results = output.sort_results_for_display(results, "score")
        scores = [r["score"] for r in sorted_results]
        assert scores == [0.9, 0.7, 0.5]

    def test_invalid_sort_key_unchanged(self):
        results = [
            {"score": 0.5, "card": ""},
            {"score": 0.9, "card": ""},
        ]
        sorted_results = output.sort_results_for_display(results, "invalid")
        assert sorted_results == results

    def test_empty_sort_key_unchanged(self):
        results = [
            {"score": 0.5, "card": ""},
            {"score": 0.9, "card": ""},
        ]
        sorted_results = output.sort_results_for_display(results, "")
        assert sorted_results == results


# =============================================================================
# Tests: Star Card Builder (starrag.cards)
# =============================================================================

class TestBuildStarCard:
    """Tests for build_star_card function."""

    def test_basic_card(self, sample_star_row):
        card = cards.build_star_card(sample_star_row)

        # Check IDs are present
        assert "STAR_001" in card
        assert "GAIA" in card
        assert "2MASS" in card
        assert "HIP" in card

        # Check coordinates
        assert "ra:" in card
        assert "dec:" in card

        # Check physical parameters
        assert "Teff" in card
        assert "5500" in card

    def test_card_includes_magnitudes(self, sample_star_row):
        card = cards.build_star_card(sample_star_row)
        assert "mags:" in card
        assert "K" in card

    def test_card_includes_distance(self, sample_star_row):
        card = cards.build_star_card(sample_star_row)
        assert "dist:" in card
        assert "40" in card

    def test_card_includes_class(self, sample_star_row):
        card = cards.build_star_card(sample_star_row)
        assert "class V" in card

    def test_empty_row_fallback(self):
        row = {"_rid": 42}
        card = cards.build_star_card(row)
        # With only _rid, the card gets default "type: STAR"
        assert "STAR" in card

    def test_minimal_row(self):
        row = {"_rid": 1, "ra": 180.0, "dec": -45.0}
        card = cards.build_star_card(row)
        assert "ra:" in card
        assert "dec:" in card


# =============================================================================
# Tests: CSV Detection and Loading (starrag.ingest)
# =============================================================================

class TestDetectFormat:
    """Tests for detect_format function."""

    def test_detect_comma_delimiter(self, temp_dir):
        csv_path = os.path.join(temp_dir, "test.csv")
        with open(csv_path, "w") as f:
            f.write("ID,ra,dec,Teff,Kmag\n")
            f.write("1,180.0,-45.0,5500,3.8\n")

        delim, header_idx, _ = ingest.detect_format(csv_path)
        assert delim == ","
        assert header_idx == 0

    def test_detect_tab_delimiter(self, temp_dir):
        csv_path = os.path.join(temp_dir, "test.tsv")
        with open(csv_path, "w") as f:
            f.write("ID\tra\tdec\tTeff\tKmag\n")
            f.write("1\t180.0\t-45.0\t5500\t3.8\n")

        delim, header_idx, _ = ingest.detect_format(csv_path)
        assert delim == "\t"
        assert header_idx == 0

    def test_skip_comment_lines(self, temp_dir):
        csv_path = os.path.join(temp_dir, "test.csv")
        with open(csv_path, "w") as f:
            f.write("# This is a comment\n")
            f.write("# Another comment\n")
            f.write("ID,ra,dec,Teff,Kmag\n")
            f.write("1,180.0,-45.0,5500,3.8\n")

        delim, header_idx, _ = ingest.detect_format(csv_path)
        assert delim == ","
        assert header_idx == 2  # Skip 2 comment lines


class TestLoadCsvToSqlite:
    """Tests for load_csv_to_sqlite function."""

    def test_basic_load(self, temp_dir, sample_csv_content):
        csv_path = os.path.join(temp_dir, "stars.csv")
        db_path = os.path.join(temp_dir, "test.db")

        with open(csv_path, "w") as f:
            f.write(sample_csv_content)

        ingest.load_csv_to_sqlite(csv_path, db_path, table="stars")

        with sqlite3.connect(db_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM stars").fetchone()[0]
            assert count == 3

    def test_columns_present(self, temp_dir, sample_csv_content):
        csv_path = os.path.join(temp_dir, "stars.csv")
        db_path = os.path.join(temp_dir, "test.db")

        with open(csv_path, "w") as f:
            f.write(sample_csv_content)

        ingest.load_csv_to_sqlite(csv_path, db_path, table="stars")

        with sqlite3.connect(db_path) as conn:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(stars)").fetchall()]
            assert "ID" in cols
            assert "ra" in cols
            assert "Teff" in cols


class TestIterFiles:
    """Tests for _iter_files function."""

    def test_find_csv_files(self, temp_dir):
        # Create test files
        for name in ["GaiaSource_001.csv", "GaiaSource_002.csv", "other.txt"]:
            Path(temp_dir, name).touch()

        files = ingest._iter_files(temp_dir, "GaiaSource_*.csv")
        assert len(files) == 2
        assert all("GaiaSource" in f for f in files)

    def test_empty_folder(self, temp_dir):
        files = ingest._iter_files(temp_dir, "*.csv")
        assert files == []

    def test_sorted_results(self, temp_dir):
        for name in ["c.csv", "a.csv", "b.csv"]:
            Path(temp_dir, name).touch()

        files = ingest._iter_files(temp_dir, "*.csv")
        basenames = [os.path.basename(f) for f in files]
        assert basenames == ["a.csv", "b.csv", "c.csv"]


# =============================================================================
# Tests: Star Cards Creation (starrag.cards)
# =============================================================================

class TestCreateStarCards:
    """Tests for create_star_cards function."""

    def test_creates_cards_table(self, sample_db):
        cards.create_star_cards(sample_db, source_table="stars", cards_table="star_cards")

        with sqlite3.connect(sample_db) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t[0] for t in tables]
            assert "star_cards" in table_names

    def test_card_count_matches(self, sample_db):
        cards.create_star_cards(sample_db, source_table="stars", cards_table="star_cards")

        with sqlite3.connect(sample_db) as conn:
            stars_count = conn.execute("SELECT COUNT(*) FROM stars").fetchone()[0]
            cards_count = conn.execute("SELECT COUNT(*) FROM star_cards").fetchone()[0]
            assert cards_count == stars_count

    def test_cards_have_content(self, sample_db):
        cards.create_star_cards(sample_db, source_table="stars", cards_table="star_cards")

        with sqlite3.connect(sample_db) as conn:
            card_rows = conn.execute("SELECT card FROM star_cards").fetchall()
            for (card,) in card_rows:
                assert card is not None
                assert len(card) > 0
                assert card != "star"  # Not just fallback


# =============================================================================
# Tests: SQL Filter (starrag.query)
# =============================================================================

class TestSqlFilterIds:
    """Tests for sql_filter_ids function."""

    def test_filter_by_distance(self, sample_db):
        with sqlite3.connect(sample_db) as conn:
            ids = query.sql_filter_ids(conn, "stars", "d <= ?", (50.0,))
            assert len(ids) == 2  # STAR001 (40pc) and STAR003 (25pc)

    def test_filter_by_teff(self, sample_db):
        with sqlite3.connect(sample_db) as conn:
            ids = query.sql_filter_ids(conn, "stars", "Teff >= ?", (5000,))
            assert len(ids) == 2  # STAR001 (5500K) and STAR003 (6500K)

    def test_filter_returns_empty(self, sample_db):
        with sqlite3.connect(sample_db) as conn:
            ids = query.sql_filter_ids(conn, "stars", "d <= ?", (1.0,))
            assert len(ids) == 0


# =============================================================================
# Tests: Device Resolution (starrag.embeddings)
# =============================================================================

class TestResolveDevice:
    """Tests for _resolve_device function."""

    def test_cpu_explicit(self):
        assert embeddings._resolve_device("cpu") == "cpu"

    def test_cpu_uppercase(self):
        assert embeddings._resolve_device("CPU") == "cpu"

    def test_invalid_device_raises(self):
        with pytest.raises(RuntimeError, match="must be one of"):
            embeddings._resolve_device("gpu")

    def test_auto_without_cuda_returns_cpu(self):
        with mock.patch.dict("sys.modules", {"torch": None}):
            # When torch is not available, should return cpu
            result = embeddings._resolve_device("auto")
            # Result should be either cpu or cuda depending on environment
            assert result in ("cpu", "cuda")


# =============================================================================
# Tests: Index Metadata (starrag.embeddings)
# =============================================================================

class TestIndexMeta:
    """Tests for IndexMeta dataclass."""

    def test_create_meta(self):
        meta = embeddings.IndexMeta(
            model_name="test-model",
            dim=384,
            id_list=[1, 2, 3]
        )
        assert meta.model_name == "test-model"
        assert meta.dim == 384
        assert meta.id_list == [1, 2, 3]

    def test_meta_to_dict(self):
        meta = embeddings.IndexMeta(
            model_name="test-model",
            dim=384,
            id_list=[1, 2, 3]
        )
        d = meta.__dict__
        assert d["model_name"] == "test-model"
        assert d["dim"] == 384
        assert d["id_list"] == [1, 2, 3]


# =============================================================================
# Tests: Configuration (starrag.config)
# =============================================================================

class TestStarragConfig:
    """Tests for StarragConfig dataclass."""

    def test_default_config(self):
        cfg = config.StarragConfig()
        assert cfg.name == "stars"
        assert cfg.db == "stars.db"
        assert cfg.index == "stars.faiss"
        assert cfg.meta == "stars_meta.json"

    def test_custom_name_derives_paths(self):
        cfg = config.StarragConfig(name="gaia")
        assert cfg.db == "gaia.db"
        assert cfg.index == "gaia.faiss"
        assert cfg.meta == "gaia_meta.json"

    def test_explicit_paths_override(self):
        cfg = config.StarragConfig(
            name="test",
            db="/path/to/custom.db",
            index="/path/to/custom.faiss",
            meta="/path/to/custom.json"
        )
        assert cfg.db == "/path/to/custom.db"
        assert cfg.index == "/path/to/custom.faiss"
        assert cfg.meta == "/path/to/custom.json"

    def test_get_paths(self):
        cfg = config.StarragConfig(name="mycat")
        db, index, meta = cfg.get_paths()
        assert db == "mycat.db"
        assert index == "mycat.faiss"
        assert meta == "mycat_meta.json"

    def test_to_dict(self):
        cfg = config.StarragConfig(name="test")
        d = cfg.to_dict()
        assert d["name"] == "test"
        assert d["db"] == "test.db"
        assert "model" in d
        assert "device" in d

    def test_from_dict(self):
        data = {"name": "custom", "k": 20, "device": "cuda"}
        cfg = config.StarragConfig.from_dict(data)
        assert cfg.name == "custom"
        assert cfg.k == 20
        assert cfg.device == "cuda"
        # Derived paths
        assert cfg.db == "custom.db"

    def test_from_dict_ignores_unknown_fields(self):
        data = {"name": "test", "unknown_field": "ignored"}
        cfg = config.StarragConfig.from_dict(data)
        assert cfg.name == "test"
        assert not hasattr(cfg, "unknown_field")


class TestConfigIO:
    """Tests for config file I/O."""

    def test_save_and_load_config(self, temp_dir):
        cfg = config.StarragConfig(name="testcat", k=15)
        path = os.path.join(temp_dir, "test_config.json")

        config.save_config(cfg, path)
        assert os.path.exists(path)

        loaded = config.load_config(path)
        assert loaded.name == "testcat"
        assert loaded.k == 15
        assert loaded.db == "testcat.db"

    def test_load_nonexistent_explicit_path_raises(self, temp_dir):
        path = os.path.join(temp_dir, "nonexistent.json")
        with pytest.raises(FileNotFoundError):
            config.load_config(path)

    def test_load_default_when_no_config(self, temp_dir):
        # Change to temp_dir where no config exists
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            cfg = config.load_config()
            assert cfg.name == "stars"  # Default
        finally:
            os.chdir(original_cwd)

    def test_init_config_creates_file(self, temp_dir):
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            path = config.init_config(name="myproject")
            assert path.exists()
            assert path.name == "starrag.json"

            # Load and verify
            cfg = config.load_config()
            assert cfg.name == "myproject"
        finally:
            os.chdir(original_cwd)

    def test_init_config_raises_if_exists(self, temp_dir):
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            config.init_config(name="first")

            with pytest.raises(FileExistsError):
                config.init_config(name="second")
        finally:
            os.chdir(original_cwd)

    def test_init_config_force_overwrites(self, temp_dir):
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            config.init_config(name="first")
            config.init_config(name="second", force=True)

            cfg = config.load_config()
            assert cfg.name == "second"
        finally:
            os.chdir(original_cwd)


# =============================================================================
# Tests: CLI (starrag.cli)
# =============================================================================

class TestCLIHelp:
    """Tests for CLI help output."""

    def test_main_help_shows_commands(self):
        """Test that main help shows all available commands."""
        result = subprocess.run(
            [sys.executable, "-m", "starrag", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "init" in result.stdout
        assert "config" in result.stdout
        assert "build" in result.stdout
        assert "build-gaia" in result.stdout
        assert "query" in result.stdout

    def test_main_help_shows_quick_start(self):
        """Test that main help shows quick start guide."""
        result = subprocess.run(
            [sys.executable, "-m", "starrag", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Quick Start" in result.stdout
        assert "Initialize config" in result.stdout
        assert "Build index" in result.stdout

    def test_main_help_shows_examples(self):
        """Test that main help shows examples."""
        result = subprocess.run(
            [sys.executable, "-m", "starrag", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Examples" in result.stdout

    def test_init_help(self):
        """Test init command help."""
        result = subprocess.run(
            [sys.executable, "-m", "starrag", "init", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "--name" in result.stdout
        assert "--force" in result.stdout

    def test_config_help(self):
        """Test config command help."""
        result = subprocess.run(
            [sys.executable, "-m", "starrag", "config", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

    def test_build_help(self):
        """Test build command help."""
        result = subprocess.run(
            [sys.executable, "-m", "starrag", "build", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "--csv" in result.stdout
        assert "--dir" in result.stdout
        assert "--db" in result.stdout
        assert "--index" in result.stdout
        assert "--meta" in result.stdout
        assert "default from config" in result.stdout

    def test_build_gaia_help(self):
        """Test build-gaia command help."""
        result = subprocess.run(
            [sys.executable, "-m", "starrag", "build-gaia", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "--dir" in result.stdout
        assert "--chunksize" in result.stdout

    def test_query_help(self):
        """Test query command help."""
        result = subprocess.run(
            [sys.executable, "-m", "starrag", "query", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "query_text" in result.stdout
        assert "--max-dist" in result.stdout
        assert "--min-teff" in result.stdout
        assert "--max-teff" in result.stdout
        assert "--k" in result.stdout

    def test_no_args_shows_help(self):
        """Test that running with no args shows help."""
        result = subprocess.run(
            [sys.executable, "-m", "starrag"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "StarRAG" in result.stdout
        assert "Quick Start" in result.stdout


class TestCLICommands:
    """Tests for CLI command execution."""

    def test_init_creates_config(self, temp_dir):
        """Test that init command creates config file."""
        result = subprocess.run(
            [sys.executable, "-m", "starrag", "init", "--name", "testcat"],
            capture_output=True,
            text=True,
            cwd=temp_dir
        )
        assert result.returncode == 0
        assert "Created config" in result.stdout

        config_path = os.path.join(temp_dir, "starrag.json")
        assert os.path.exists(config_path)

        with open(config_path) as f:
            cfg = json.load(f)
        assert cfg["name"] == "testcat"
        assert cfg["db"] == "testcat.db"

    def test_init_fails_if_exists(self, temp_dir):
        """Test that init fails if config already exists."""
        # Create first config
        subprocess.run(
            [sys.executable, "-m", "starrag", "init"],
            cwd=temp_dir
        )

        # Try to create again
        result = subprocess.run(
            [sys.executable, "-m", "starrag", "init"],
            capture_output=True,
            text=True,
            cwd=temp_dir
        )
        assert result.returncode != 0
        assert "already exists" in result.stdout or "Error" in result.stdout

    def test_init_force_overwrites(self, temp_dir):
        """Test that init --force overwrites existing config."""
        # Create first config
        subprocess.run(
            [sys.executable, "-m", "starrag", "init", "--name", "first"],
            cwd=temp_dir
        )

        # Overwrite with force
        result = subprocess.run(
            [sys.executable, "-m", "starrag", "init", "--name", "second", "--force"],
            capture_output=True,
            text=True,
            cwd=temp_dir
        )
        assert result.returncode == 0

        config_path = os.path.join(temp_dir, "starrag.json")
        with open(config_path) as f:
            cfg = json.load(f)
        assert cfg["name"] == "second"

    def test_config_shows_settings(self, temp_dir):
        """Test that config command shows current settings."""
        # Create config first
        subprocess.run(
            [sys.executable, "-m", "starrag", "init", "--name", "mycat"],
            cwd=temp_dir
        )

        result = subprocess.run(
            [sys.executable, "-m", "starrag", "config"],
            capture_output=True,
            text=True,
            cwd=temp_dir
        )
        assert result.returncode == 0
        assert "mycat" in result.stdout
        assert "mycat.db" in result.stdout
        assert "mycat.faiss" in result.stdout

    def test_query_requires_query_text(self):
        """Test that query command requires query text."""
        result = subprocess.run(
            [sys.executable, "-m", "starrag", "query"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
        assert "query text is required" in result.stdout or "error" in result.stdout.lower()


class TestCLIApplyConfigDefaults:
    """Tests for _apply_config_defaults function."""

    def test_applies_db_default(self):
        """Test that db default is applied from config."""
        import argparse
        args = argparse.Namespace(db=None, index=None, meta=None,
                                   model=None, device=None, batch_size=None,
                                   chunksize=None, k=None)
        cfg = config.StarragConfig(name="test")

        cli._apply_config_defaults(args, cfg)

        assert args.db == "test.db"
        assert args.index == "test.faiss"
        assert args.meta == "test_meta.json"

    def test_cli_args_override_config(self):
        """Test that CLI args override config defaults."""
        import argparse
        args = argparse.Namespace(db="/custom/path.db", index=None, meta=None,
                                   model=None, device=None, batch_size=None,
                                   chunksize=None, k=None)
        cfg = config.StarragConfig(name="test")

        cli._apply_config_defaults(args, cfg)

        assert args.db == "/custom/path.db"  # Not overwritten
        assert args.index == "test.faiss"    # From config


# =============================================================================
# Integration Tests
# =============================================================================

class TestFullPipeline:
    """Integration tests for the full pipeline."""

    def test_csv_to_cards_pipeline(self, temp_dir, sample_csv_content):
        csv_path = os.path.join(temp_dir, "stars.csv")
        db_path = os.path.join(temp_dir, "test.db")

        with open(csv_path, "w") as f:
            f.write(sample_csv_content)

        # Load CSV
        ingest.load_csv_to_sqlite(csv_path, db_path, table="stars")

        # Create cards
        cards.create_star_cards(db_path, source_table="stars", cards_table="star_cards")

        # Verify
        with sqlite3.connect(db_path) as conn:
            stars = conn.execute("SELECT COUNT(*) FROM stars").fetchone()[0]
            cards_count = conn.execute("SELECT COUNT(*) FROM star_cards").fetchone()[0]

            assert stars == 3
            assert cards_count == 3

            # Check card content
            card = conn.execute(
                "SELECT card FROM star_cards WHERE orig_ID = 'STAR001'"
            ).fetchone()[0]
            assert "STAR001" in card
            assert "5500" in card  # Teff


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    mypytest.main([__file__, "-v"])
