"""Step `data`: run every registered cleaner (config.yaml `datasets`), validate, summarize.

Writes data/interim/<name>.parquet and outputs/tables/01_dataset_summary.csv.
"""
from __future__ import annotations

import importlib

import pandas as pd

from src.data.schemas import SCHEMAS
from src.data.validate import validate
from src.utils import load_config, write_table


def summarize(name: str, df: pd.DataFrame) -> dict:
    dates = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    miss = df.isna().mean()
    row = {
        "dataset": name,
        "rows": len(df),
        "cols": df.shape[1],
        "date_col": dates[0] if dates else "",
        "date_min": df[dates[0]].min() if dates else "",
        "date_max": df[dates[0]].max() if dates else "",
        "pct_missing_cells": round(100 * float(miss.mean()), 2) if len(df.columns) else 0.0,
        "most_missing_col": miss.idxmax() if len(df.columns) else "",
        "most_missing_pct": round(100 * float(miss.max()), 2) if len(df.columns) else 0.0,
    }
    return row


def main() -> None:
    cfg = load_config()
    raw, interim = cfg["paths"]["raw"], cfg["paths"]["interim"]
    names = cfg.get("datasets") or []
    if not names:
        print("No datasets registered in config.yaml `datasets` yet — nothing to clean.")
    rows, failures = [], []
    for name in names:
        mod = importlib.import_module(f"src.data.clean_{name}")
        out = mod.clean(raw, interim)
        df = pd.read_parquet(out)
        if name not in SCHEMAS:
            failures.append(f"{name}: no SCHEMA in src/data/schemas.py")
        else:
            failures += [f"{name}: {p}" for p in validate(df, SCHEMAS[name])]
        rows.append(summarize(name, df))
    write_table(pd.DataFrame(rows, columns=list(summarize("x", pd.DataFrame()).keys())), cfg,
                "01_dataset_summary.csv")
    if failures:
        raise SystemExit("Data contract violations:\n  " + "\n  ".join(failures))


if __name__ == "__main__":
    main()
