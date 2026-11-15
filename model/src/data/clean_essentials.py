"""Essential-services access per ZIP, from Anna's table (Person 3).

Source: ../essential_services/outputs/tables/anna_essentials_by_zip.csv, produced from the raw
Google Maps Places + Zillow listing files by notebooks/03_anna_essential_services.ipynb
(method: ../essential_services/docs/anna_essential_services.md).

⚠️ Reproducibility gap: this reads Anna's committed output, not data/raw. To close it, port the
notebook's distance step into this cleaner so `run.py data` rebuilds it from raw Places.

Output: data/interim/essentials.parquet, one row per zipcode (293 rows).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.utils import ROOT

NAME = "essentials"
SRC = ROOT.parent / "essential_services" / "outputs" / "tables" / "anna_essentials_by_zip.csv"
KEEP = ["zipcode", "city", "county", "n_homes", "low_data", "access_score",
        "dist_grocery_mi", "dist_pharmacy_mi", "dist_primary_care_mi", "dist_transit_mi",
        "dist_food_bank_mi", "dist_bank_mi", "dist_check_cashing_mi",
        "count_grocery_1mi", "count_pharmacy_1mi", "count_primary_care_1mi", "count_transit_1mi",
        "count_food_bank_1mi", "bank_to_checkcash_ratio", "median_rent", "n_rentals"]


def clean(raw_dir: Path, interim_dir: Path) -> Path:
    df = pd.read_csv(SRC, dtype={"zipcode": str})
    print(f"[{NAME}] read {len(df)} zips ({int(df['low_data'].sum())} flagged low_data)")
    df = df[KEEP].copy()
    df["zipcode"] = df["zipcode"].str.zfill(5)
    df["county"] = df["county"].str.replace(" County", "", regex=False)
    df["low_data"] = df["low_data"].astype(bool)
    df["n_rentals"] = df["n_rentals"].fillna(0)
    out = interim_dir / f"{NAME}.parquet"
    df.to_parquet(out, index=False)
    return out
