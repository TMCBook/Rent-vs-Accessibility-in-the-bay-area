"""Essential-services access per ZIP, rebuilt from raw data with Anna's method (Person 3).

Port of ../essential_services/notebooks/03_anna_essential_services.ipynb (cells 4-31); method in
../essential_services/docs/anna_essential_services.md. Same category lists, filters and formulas.

Raw inputs (data/raw/, shared drive):
  places/google_maps.csv                       Google Maps Places
  zillow/*.csv                                 Zillow Housing listings (3 parts)

Steps (each logged):
  1. Places: drop permanently closed; map exact categories to 7 service buckets.
  2. Homes: Zillow listings with coordinates and ZIP, deduped on zpid, 9 Bay Area counties only.
  3. Drop places more than 3 miles from any home (outside the Bay Area).
  4. For every home: haversine distance to the nearest place in each bucket, and count within 1 mile.
  5. Per ZIP: median home's values; n_homes; city/county = most common; low_data = n_homes < 20.
  6. access_score: average percentile rank (closer = higher) of grocery, pharmacy, primary care,
     bank, transit distances, x 100. bank_to_checkcash_ratio = banks / (check-cashing + 1).
  7. median_rent / n_rentals from FOR_RENT listings with price $300-$30,000.

After building, the result is compared with Anna's saved table
(../essential_services/outputs/tables/anna_essentials_by_zip.csv) and the per-column differences
are written to outputs/tables/10_essentials_rebuild_check.csv.

Output: data/interim/essentials.parquet, one row per zipcode.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree

from src.utils import ROOT, load_config, write_table

NAME = "essentials"
ANNA_TABLE = ROOT.parent / "essential_services" / "outputs" / "tables" / "anna_essentials_by_zip.csv"
KEEP = ["zipcode", "city", "county", "n_homes", "low_data", "access_score",
        "dist_grocery_mi", "dist_pharmacy_mi", "dist_primary_care_mi", "dist_transit_mi",
        "dist_food_bank_mi", "dist_bank_mi", "dist_check_cashing_mi",
        "count_grocery_1mi", "count_pharmacy_1mi", "count_primary_care_1mi", "count_transit_1mi",
        "count_food_bank_1mi", "bank_to_checkcash_ratio", "median_rent", "n_rentals"]

BUCKETS = {
    "grocery": ["Grocery store", "Supermarket", "Asian grocery store", "Indian grocery store",
                "Produce market"],
    "food_bank": ["Food bank"],
    "pharmacy": ["Pharmacy"],
    "primary_care": ["Doctor", "Medical clinic", "Internist", "Pediatrician", "Family practice physician",
                     "Clinic", "Community health center", "Urgent care center", "Women's health clinic",
                     "Medical Center", "Hospital"],
    "bank": ["Bank", "Credit union"],
    "check_cashing": ["Money transfer service", "Check cashing service", "Pawn shop"],
    "transit": ["Bus stop", "Transit station", "Transport hub"],
}
BAY_AREA = ["Alameda County", "Contra Costa County", "Marin County", "Napa County",
            "San Francisco County", "San Mateo County", "Santa Clara County",
            "Solano County", "Sonoma County"]
ACCESS_PARTS = ["dist_grocery_mi", "dist_pharmacy_mi", "dist_primary_care_mi", "dist_bank_mi", "dist_transit_mi"]
EARTH_MI = 3958.8


def _zillow(raw_dir: Path, cols: list[str]) -> pd.DataFrame:
    files = sorted((raw_dir / "zillow").glob("*.csv"))
    if not files:
        raise SystemExit(f"[{NAME}] no Zillow CSVs in {raw_dir / 'zillow'}")
    parts = []
    for f in files:
        have = [c for c in cols if c in pd.read_csv(f, nrows=0).columns]
        for chunk in pd.read_csv(f, usecols=have, dtype={"zipcode": str}, chunksize=20_000):
            parts.append(chunk)
    return pd.concat(parts, ignore_index=True)


def build(raw_dir: Path) -> pd.DataFrame:
    # 1. places
    df = pd.read_csv(raw_dir / "places" / "google_maps.csv",
                     usecols=["place_id", "category", "lat", "lon", "permanently_closed"])
    n0 = len(df)
    df = df[~(df["permanently_closed"].astype(str).str.lower() == "true")]
    print(f"[{NAME}] places: drop permanently closed {n0} -> {len(df)}")
    cat_to_bucket = {cat: b for b, cats in BUCKETS.items() for cat in cats}
    df["bucket"] = df["category"].map(cat_to_bucket)

    # 2. homes
    homes = _zillow(raw_dir, ["zpid", "zipcode", "city", "county", "latitude", "longitude"])
    n0 = len(homes)
    homes = homes.dropna(subset=["latitude", "longitude", "zipcode"]).drop_duplicates("zpid")
    homes["zipcode"] = homes["zipcode"].str.extract(r"(\d{5})")[0]
    homes = homes.dropna(subset=["zipcode"])
    homes = homes[homes["county"].isin(BAY_AREA)].reset_index(drop=True)
    print(f"[{NAME}] homes: with coordinates + ZIP, deduped, Bay Area only {n0} -> {len(homes)} "
          f"in {homes['zipcode'].nunique()} ZIPs")

    # 3. places near homes
    places = df[df["bucket"].notna()].dropna(subset=["lat", "lon"]).copy()
    home_rad = np.radians(homes[["latitude", "longitude"]].to_numpy())
    d, _ = BallTree(home_rad, metric="haversine").query(np.radians(places[["lat", "lon"]].to_numpy()), k=1)
    n0 = len(places)
    places = places[d[:, 0] * EARTH_MI <= 3]
    print(f"[{NAME}] places in a service bucket within 3 miles of a home: {n0} -> {len(places)}")

    # 4. distances and counts per home
    for b in BUCKETS:
        tree = BallTree(np.radians(places.loc[places["bucket"] == b, ["lat", "lon"]].to_numpy()),
                        metric="haversine")
        homes[f"dist_{b}_mi"] = tree.query(home_rad, k=1)[0][:, 0] * EARTH_MI
        homes[f"count_{b}_1mi"] = tree.query_radius(home_rad, r=1 / EARTH_MI, count_only=True)

    # 5. per ZIP
    metric_cols = [c for c in homes.columns if c.startswith(("dist_", "count_"))]
    g = homes.groupby("zipcode")
    by_zip = g[metric_cols].median()
    by_zip["n_homes"] = g.size()
    mode = lambda s: s.mode().iat[0] if s.notna().any() else None  # noqa: E731
    by_zip["city"] = g["city"].agg(mode)
    by_zip["county"] = g["county"].agg(mode)
    by_zip["low_data"] = by_zip["n_homes"] < 20

    # 6. scores
    ranks = pd.concat([1 - by_zip[c].rank(pct=True) for c in ACCESS_PARTS], axis=1)
    by_zip["access_score"] = (ranks.mean(axis=1) * 100).round(1)
    by_zip["bank_to_checkcash_ratio"] = by_zip["count_bank_1mi"] / (by_zip["count_check_cashing_1mi"] + 1)

    # 7. rent
    rent = _zillow(raw_dir, ["zipcode", "county", "homeStatus", "price"])
    rent = rent[(rent["homeStatus"] == "FOR_RENT") & rent["county"].isin(BAY_AREA)]
    rent = rent[rent["price"].between(300, 30000)]
    rent["zipcode"] = rent["zipcode"].str.extract(r"(\d{5})")[0]
    by_zip["median_rent"] = rent.groupby("zipcode")["price"].median()
    by_zip["n_rentals"] = rent.groupby("zipcode").size()
    return by_zip.reset_index()


def compare_with_saved(new: pd.DataFrame) -> pd.DataFrame:
    """Per-column agreement between the rebuilt table and Anna's saved CSV."""
    old = pd.read_csv(ANNA_TABLE, dtype={"zipcode": str})
    m = new.merge(old, on="zipcode", how="outer", suffixes=("_new", "_saved"), indicator=True)
    rows = [{"column": "zipcode (rows)", "n_compared": int((m["_merge"] == "both").sum()),
             "n_only_rebuilt": int((m["_merge"] == "left_only").sum()),
             "n_only_saved": int((m["_merge"] == "right_only").sum())}]
    both = m[m["_merge"] == "both"]
    for c in KEEP[1:]:
        a, b = both[f"{c}_new"], both[f"{c}_saved"]
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b) and not pd.api.types.is_bool_dtype(a):
            diff = (a.astype(float) - b.astype(float)).abs()
            same = (diff <= 1e-6) | (a.isna() & b.isna())
            rows.append({"column": c, "n_compared": len(both), "n_equal": int(same.sum()),
                         "max_abs_diff": round(float(diff.max()), 6) if diff.notna().any() else 0.0})
        else:
            same = (a.astype(str) == b.astype(str))
            rows.append({"column": c, "n_compared": len(both), "n_equal": int(same.sum()), "max_abs_diff": None})
    return pd.DataFrame(rows)


def clean(raw_dir: Path, interim_dir: Path) -> Path:
    by_zip = build(Path(raw_dir))
    check = compare_with_saved(by_zip)
    write_table(check, load_config(), "10_essentials_rebuild_check.csv")
    bad = check[(check["column"] != "zipcode (rows)") & (check["n_equal"] < check["n_compared"])]
    print(f"[{NAME}] rebuilt {len(by_zip)} ZIPs; columns differing from Anna's saved table: "
          f"{list(bad['column']) or 'none'}")

    df = by_zip[KEEP].copy()
    df["zipcode"] = df["zipcode"].str.zfill(5)
    df["county"] = df["county"].str.replace(" County", "", regex=False)
    df["low_data"] = df["low_data"].astype(bool)
    df["n_homes"] = df["n_homes"].astype("int64")
    df["n_rentals"] = df["n_rentals"].fillna(0).astype(float)
    for c in [c for c in KEEP if c.startswith("count_")]:
        df[c] = df[c].astype(float)
    out = Path(interim_dir) / f"{NAME}.parquet"
    df.to_parquet(out, index=False)
    return out
