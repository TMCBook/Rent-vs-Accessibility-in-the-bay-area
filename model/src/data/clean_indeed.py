"""Indeed job postings -> one row per deduplicated Bay Area posting with normalized hourly pay.

Raw: data/raw/indeed/indeed_job_listings.csv (shared drive "Indeed Jobs").
Steps (each logged):
  1. keep postings whose location parses as "<City>, CA [ZIP]"
  2. keep postings in a Bay Area city or ZIP (cities/ZIPs from the essentials table)
  3. dedupe on job_title + company_name + location (README: reposts are common)
  4. parse salary_formatted to hourly pay: hourly as-is; yearly / 2080; monthly * 12 / 2080;
     weekly / 40; daily / 8. Ranges use the midpoint. Spanish units ("por hora", "al año") too.
     Values outside $10-$500/hr are set to null (parse errors / equity-style ranges).
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.utils import ROOT

NAME = "indeed"
COLS = ["jobid", "job_title", "company_name", "location", "salary_formatted", "date_posted_parsed"]
NUM = re.compile(r"\$?([\d,]+(?:\.\d+)?)\s*([kK])?")
UNITS = [("hour", ("hour", "hora")), ("year", ("year", "año", "ano")), ("month", ("month", "mes")),
         ("week", ("week", "semana")), ("day", ("day", "día", "dia"))]
TO_HOURLY = {"hour": 1, "year": 1 / 2080, "month": 12 / 2080, "week": 1 / 40, "day": 1 / 8}


def parse_pay(s) -> tuple[float, str | None]:
    if not isinstance(s, str):
        return np.nan, None
    vals = [float(a.replace(",", "")) * (1000 if k else 1) for a, k in NUM.findall(s)
            if any(ch.isdigit() for ch in a)]
    if not vals:
        return np.nan, None
    v = sum(vals[:2]) / len(vals[:2])
    t = s.lower()
    for unit, words in UNITS:
        if any(w in t for w in words):
            return v * TO_HOURLY[unit], unit
    return np.nan, None


def clean(raw_dir: Path, interim_dir: Path) -> Path:
    df = pd.read_csv(Path(raw_dir) / "indeed" / "indeed_job_listings.csv", usecols=COLS,
                     dtype=str, on_bad_lines="skip", engine="python")
    print(f"[{NAME}] raw postings: {len(df)}")
    loc = df["location"].fillna("").str.extract(
        r"(?:^|,\s*)([A-Za-z][A-Za-z .'\-]+),\s*CA(?:\s+(\d{5}))?\s*$")
    df["city"], df["zipcode"] = loc[0].str.strip(), loc[1]
    n0 = len(df)
    df = df[df["city"].notna()]
    print(f"[{NAME}] location parses as '<City>, CA': {n0} -> {len(df)}")

    ess = pd.read_parquet(Path(interim_dir) / "essentials.parquet", columns=["zipcode", "city"])
    n0 = len(df)
    df = df[df["city"].isin(set(ess["city"])) | df["zipcode"].isin(set(ess["zipcode"]))]
    print(f"[{NAME}] Bay Area city or ZIP: {n0} -> {len(df)}")

    n0 = len(df)
    df = df.drop_duplicates(["job_title", "company_name", "location"])
    print(f"[{NAME}] dedupe title+company+location: {n0} -> {len(df)}")

    parsed = df["salary_formatted"].map(parse_pay)
    df["hourly_pay"] = [p for p, _ in parsed]
    df["pay_unit"] = [u for _, u in parsed]
    bad = ~df["hourly_pay"].between(10, 500)
    df.loc[bad, ["hourly_pay"]] = np.nan
    df["has_pay"] = df["salary_formatted"].notna()
    df["date_posted"] = pd.to_datetime(df["date_posted_parsed"], errors="coerce", utc=True)
    print(f"[{NAME}] with pay posted: {df['has_pay'].mean():.1%}; parsed hourly: "
          f"{df['hourly_pay'].notna().mean():.1%}")
    df = df[["jobid", "city", "zipcode", "job_title", "has_pay", "hourly_pay", "pay_unit", "date_posted"]]
    out = Path(interim_dir) / f"{NAME}.parquet"
    df.reset_index(drop=True).to_parquet(out, index=False)
    return out
