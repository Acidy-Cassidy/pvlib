# -*- coding: utf-8 -*-
"""Configuration management for StarRAG."""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

CONFIG_FILENAME = "starrag.json"


def _get_config_search_paths() -> list:
    """Get config search paths (evaluated at runtime, not import time)."""
    return [
        Path.cwd() / CONFIG_FILENAME,
        Path.home() / ".config" / "starrag" / CONFIG_FILENAME,
        Path.home() / f".{CONFIG_FILENAME}",
    ]


@dataclass
class StarragConfig:
    """Configuration for StarRAG CLI."""

    # Output paths (derived from 'name' if not set)
    name: str = "stars"
    db: Optional[str] = None
    index: Optional[str] = None
    meta: Optional[str] = None

    # Model settings
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
    device: str = "auto"
    batch_size: int = 1024

    # Ingestion settings
    chunksize: int = 200_000

    # Query defaults
    k: int = 10

    def __post_init__(self):
        """Derive db/index/meta from name if not explicitly set."""
        if self.db is None:
            self.db = f"{self.name}.db"
        if self.index is None:
            self.index = f"{self.name}.faiss"
        if self.meta is None:
            self.meta = f"{self.name}_meta.json"

    def get_paths(self) -> tuple:
        """Return (db, index, meta) paths."""
        return self.db, self.index, self.meta

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "StarragConfig":
        """Create config from dictionary."""
        # Only pass known fields
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)


def find_config_file() -> Optional[Path]:
    """Find the first existing config file in search paths."""
    for path in _get_config_search_paths():
        if path.exists():
            return path
    return None


def load_config(config_path: Optional[str] = None) -> StarragConfig:
    """
    Load configuration from file.

    Search order:
    1. Explicit path if provided
    2. ./starrag.json
    3. ~/.config/starrag/starrag.json
    4. ~/.starrag.json
    5. Default values
    """
    if config_path:
        path = Path(config_path)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return StarragConfig.from_dict(data)
        else:
            raise FileNotFoundError(f"Config file not found: {config_path}")

    found = find_config_file()
    if found:
        with open(found, "r", encoding="utf-8") as f:
            data = json.load(f)
        return StarragConfig.from_dict(data)

    return StarragConfig()


def save_config(config: StarragConfig, path: Optional[str] = None) -> Path:
    """
    Save configuration to file.

    If path not specified, saves to ./starrag.json
    """
    save_path = Path(path) if path else Path.cwd() / CONFIG_FILENAME
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, indent=2)

    return save_path


def init_config(name: str = "stars", force: bool = False) -> Path:
    """
    Initialize a new config file in the current directory.

    Returns the path to the created config file.
    """
    config_path = Path.cwd() / CONFIG_FILENAME

    if config_path.exists() and not force:
        raise FileExistsError(f"Config file already exists: {config_path}")

    config = StarragConfig(name=name)
    return save_config(config, str(config_path))
