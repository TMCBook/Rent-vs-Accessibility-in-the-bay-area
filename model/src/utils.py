"""Shared helpers: config loading, paths, seeding, table writing."""
from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_config(path: str | os.PathLike | None = None) -> dict[str, Any]:
    """Load config.yaml (or $DATATHON_CONFIG). Env overrides: DATATHON_RAW_DIR, DATATHON_FINAL_EVAL."""
    path = Path(path or os.environ.get("DATATHON_CONFIG", ROOT / "config.yaml"))
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    base = path.resolve().parent
    cfg["paths"] = {k: _abs(base, v) for k, v in cfg["paths"].items()}
    if os.environ.get("DATATHON_RAW_DIR"):
        cfg["paths"]["raw"] = Path(os.environ["DATATHON_RAW_DIR"])
    cfg["features"]["master_table"] = _abs(base, cfg["features"]["master_table"])
    if os.environ.get("DATATHON_FINAL_EVAL") == "1":
        cfg["final_eval"] = True
    for p in ("interim", "processed", "tables", "figures", "models"):
        cfg["paths"][p].mkdir(parents=True, exist_ok=True)
    return cfg


def _abs(base: Path, p: str | Path) -> Path:
    p = Path(p)
    return p if p.is_absolute() else base / p


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def write_table(df: pd.DataFrame, cfg: dict, name: str) -> Path:
    out = cfg["paths"]["tables"] / name
    df.to_csv(out, index=False)
    print(f"wrote {name} ({len(df)} rows)")
    return out


def split_path(cfg: dict) -> Path:
    return cfg["paths"]["processed"] / "split_ids.parquet"


def predictions_path(cfg: dict) -> Path:
    return cfg["paths"]["processed"] / "predictions.parquet"
