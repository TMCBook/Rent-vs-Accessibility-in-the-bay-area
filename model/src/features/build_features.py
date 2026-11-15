"""Master table for the rent-spike model: one row per ZIP x year t (December).

Question: will this ZIP's rent growth over the NEXT year (Dec t -> Dec t+1) be in the top third
of Bay Area ZIPs that year?  (target = 1 = "high rent-growth risk")

Leakage rules
  * Time-varying features use only values at or before Dec t (rent/value levels and past growth).
  * The target is ranked WITHIN the target year, so region-wide shocks (COVID 2020-21) don't
    define the label; the model has to rank ZIPs against each other.
  * Static context (essential-services access from 2026 Places data; job postings 2024-2026) is
    treated as slow-moving neighborhood structure and used for every year. This is a documented
    assumption (docs/data_decisions.md), not a time-respecting feature.
  * Rows for t = 2025 have no full-year target yet (Dec 2026 isn't published); they are written to
    data/processed/forecast_frame.parquet for the help-first ranking instead of the master table.

id = "<zipcode>_<t>". Subgroups: county, access_tier, rent_tier.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.joins import audited_merge
from src.utils import load_config

LOW_WAGE_HOURLY = 25.0  # postings paying under this hourly rate count as low-wage (≈ Bay Area median)


def _growth(s: pd.Series, k: int) -> pd.Series:
    return s / s.shift(k) - 1


def zip_year_panel(zr: pd.DataFrame) -> pd.DataFrame:
    """December-only panel with lagged growth features and the next-year target."""
    dec = zr[~zr["is_partial_year"]].sort_values(["zipcode", "year"]).copy()
    # make the year grid complete per ZIP so shift(k) means k years back
    grid = (dec.groupby("zipcode")["year"].agg(["min", "max"]).reset_index())
    grid = grid.assign(year=[list(range(a, 2026)) for a, b in zip(grid["min"], grid["max"])]) \
               .explode("year")[["zipcode", "year"]]
    grid["year"] = grid["year"].astype("int64")
    p = grid.merge(dec[["zipcode", "year", "rent", "value"]], on=["zipcode", "year"], how="left")
    meta = zr.drop_duplicates("zipcode")[["zipcode", "county"]]
    p = p.merge(meta, on="zipcode", how="left")
    g = p.groupby("zipcode", group_keys=False)
    p["rent_g1"] = g["rent"].apply(lambda s: _growth(s, 1))
    p["rent_g2"] = g["rent"].apply(lambda s: _growth(s, 1).shift(1))
    p["rent_g3yr"] = g["rent"].apply(lambda s: _growth(s, 3))
    p["value_g1"] = g["value"].apply(lambda s: _growth(s, 1))
    p["value_g2"] = g["value"].apply(lambda s: _growth(s, 1).shift(1))
    p["value_g3yr"] = g["value"].apply(lambda s: _growth(s, 3))
    p["rent_years_observed"] = g["rent"].apply(lambda s: s.notna().cumsum())
    # next-year growth (target source) — never used as a feature
    p["next_rent_growth"] = g["rent"].apply(lambda s: s.shift(-1) / s - 1)

    by_year = p.groupby("year")
    p["rent_g1_rank"] = by_year["rent_g1"].rank(pct=True)
    p["rent_g1_vs_region"] = p["rent_g1"] - by_year["rent_g1"].transform("median")
    p["value_g1_vs_region"] = p["value_g1"] - by_year["value_g1"].transform("median")
    p["rent_rank_in_year"] = by_year["rent"].rank(pct=True)
    p["rent_vs_county"] = p["rent"] / p.groupby(["year", "county"])["rent"].transform("median")
    p["value_vs_county"] = p["value"] / p.groupby(["year", "county"])["value"].transform("median")
    p["price_to_rent"] = p["value"] / (12 * p["rent"])
    p["log_rent"] = np.log(p["rent"])
    p["log_value"] = np.log(p["value"])
    # target: top third of next-year growth among ZIPs with a next-year value, ranked within year
    p["next_growth_rank"] = p.groupby("year")["next_rent_growth"].rank(pct=True)
    p["target"] = np.where(p["next_rent_growth"].isna(), np.nan, (p["next_growth_rank"] > 2 / 3).astype(float))
    return p


def job_features(jobs: pd.DataFrame, ess: pd.DataFrame) -> pd.DataFrame:
    """City-level posting features, attached to ZIPs through the ZIP's city."""
    hourly = jobs[jobs["pay_unit"] == "hour"]
    city = jobs.groupby("city").agg(jobs_n=("jobid", "size"), jobs_pay_share=("has_pay", "mean"))
    city["jobs_median_hourly"] = hourly.groupby("city")["hourly_pay"].median()
    city["jobs_low_wage_share"] = hourly.groupby("city")["hourly_pay"].apply(
        lambda s: (s < LOW_WAGE_HOURLY).mean())
    city["jobs_hourly_n"] = hourly.groupby("city").size()
    city = city.reset_index()
    # thin cities: fall back to nothing (NaN) for wage features; HistGB/imputer handles NaN
    thin = city["jobs_hourly_n"].fillna(0) < 20
    city.loc[thin, ["jobs_median_hourly", "jobs_low_wage_share"]] = np.nan
    city["log_jobs_n"] = np.log1p(city["jobs_n"])
    zips = ess[["zipcode", "city"]]
    out = audited_merge(zips, city, on="city", step="essentials(zip) <- indeed(city)", how="left",
                        validate="many_to_one")
    out["log_jobs_n"] = out["log_jobs_n"].fillna(0)
    return out.drop(columns=["city", "jobs_hourly_n", "jobs_n"])


def build_all(cfg: dict) -> pd.DataFrame:
    interim = cfg["paths"]["interim"]
    zr = pd.read_parquet(interim / "zillow_research.parquet")
    ess = pd.read_parquet(interim / "essentials.parquet")
    jobs = pd.read_parquet(interim / "indeed.parquet")

    panel = zip_year_panel(zr)
    ess_cols = ["zipcode", "city", "low_data", "access_score", "n_homes", "n_rentals",
                "dist_grocery_mi", "dist_pharmacy_mi", "dist_primary_care_mi", "dist_transit_mi",
                "dist_food_bank_mi", "count_transit_1mi", "count_grocery_1mi", "bank_to_checkcash_ratio"]
    df = audited_merge(panel, ess[ess_cols], on="zipcode", step="zillow_research(zip-year) <- essentials(zip)",
                       how="left", validate="many_to_one")
    df = audited_merge(df, job_features(jobs, ess), on="zipcode",
                       step="panel(zip-year) <- job features(zip via city)", how="left", validate="many_to_one")
    df["log_n_homes"] = np.log1p(df["n_homes"])

    # subgroups (fixed cut points so they mean the same thing every year)
    df["access_tier"] = pd.cut(df["access_score"], [-0.1, 100 / 3, 200 / 3, 100.1],
                               labels=["low access", "mid access", "high access"]).astype("string")
    df["rent_tier"] = pd.cut(df["rent_rank_in_year"], [0, 1 / 3, 2 / 3, 1.0],
                             labels=["cheapest third", "middle third", "priciest third"]).astype("string")
    df["id"] = df["zipcode"] + "_" + df["year"].astype(str)
    # usable rows: current rent and last-year growth known, ZIP not low_data
    usable = df["rent"].notna() & df["rent_g1"].notna() & ~df["low_data"].fillna(True).astype(bool)
    return df[usable].copy()


def build(cfg: dict) -> pd.DataFrame:
    df = build_all(cfg)
    forecast = df[df["year"] == 2025].copy()
    forecast.to_parquet(cfg["paths"]["processed"] / "forecast_frame.parquet", index=False)
    print(f"forecast frame (t=2025, predicting 2026): {len(forecast)} zips")
    master = df[df["target"].notna()].copy()
    master["target"] = master["target"].astype("int64")
    print("master rows by year:", master.groupby("year").size().to_dict())
    print("positive rate:", round(master["target"].mean(), 3))
    return master
