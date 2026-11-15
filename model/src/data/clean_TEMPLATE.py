"""TEMPLATE — copy to src/data/clean_<name>.py, add <name> to config.yaml `datasets`,
and add SCHEMAS["<name>"] in src/data/schemas.py.

Rules: never write to raw_dir; write exactly one parquet to interim_dir;
print row counts before/after each filter so decisions can be logged in docs/data_decisions.md.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

NAME = "TEMPLATE"


def clean(raw_dir: Path, interim_dir: Path) -> Path:
    df = pd.read_csv(raw_dir / NAME / "data.csv")  # ⚠️ adjust to real file name/format
    n0 = len(df)

    # --- cleaning steps: each one logged ---
    df = df.drop_duplicates()
    print(f"[{NAME}] drop_duplicates: {n0} -> {len(df)}")

    out = interim_dir / f"{NAME}.parquet"
    df.to_parquet(out, index=False)
    return out
