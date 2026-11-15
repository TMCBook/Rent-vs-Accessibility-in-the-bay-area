"""Zillow Research indexes (ZORI rent, ZHVI home value) -> one long ZIP x year table.

Source: Albert's saved Bay Area rows of Zillow's public ZORI / ZHVI files
(../housing_costs/data/zillow_research/, see ../housing_costs/docs/albert_housing_costs.md).
These are external data committed to the repo, not a shared-drive folder, so they are read
from the repo rather than data/raw.

Output: data/interim/zillow_research.parquet, one row per (zipcode, year):
  year 2015..2025 = December value; year 2026 = September 2026 (latest month, partial year,
  flagged with is_partial_year=True). Rows where both rent and value are missing are dropped.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.utils import ROOT

NAME = "zillow_research"
SRC = ROOT.parent / "housing_costs" / "data" / "zillow_research"   # repo root / housing_costs


def _long(path: Path, value_name: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"RegionName": str})
    date_cols = [c for c in df.columns if c[:2] == "20"]
    out = df.melt(id_vars=["RegionName", "City", "CountyName"], value_vars=date_cols,
                  var_name="month", value_name=value_name)
    out["month"] = pd.to_datetime(out["month"])
    out["year"] = out["month"].dt.year.astype("int64")
    return out.rename(columns={"RegionName": "zipcode", "City": "zillow_city", "CountyName": "county"})


def clean(raw_dir: Path, interim_dir: Path) -> Path:
    rent = _long(SRC / "zori_bay_area.csv", "rent")
    value = _long(SRC / "zhvi_bay_area.csv", "value")
    print(f"[{NAME}] ZORI zips={rent.zipcode.nunique()} rows={len(rent)}; "
          f"ZHVI zips={value.zipcode.nunique()} rows={len(value)}")
    keys = ["zipcode", "year", "month"]
    df = rent.merge(value, on=keys, how="outer", suffixes=("", "_v"), validate="one_to_one")
    for c in ["zillow_city", "county"]:
        df[c] = df[c].fillna(df.pop(f"{c}_v"))
    n0 = len(df)
    df = df[df["rent"].notna() | df["value"].notna()].copy()
    print(f"[{NAME}] drop rows with neither rent nor value: {n0} -> {len(df)}")
    df["zipcode"] = df["zipcode"].str.zfill(5)
    df["county"] = df["county"].str.replace(" County", "", regex=False)
    df["is_partial_year"] = df["month"].dt.month != 12
    df = df.sort_values(keys).reset_index(drop=True)
    out = interim_dir / f"{NAME}.parquet"
    df.to_parquet(out, index=False)
    return out
