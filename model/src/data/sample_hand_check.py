"""Draw hand-check samples for a teammate to verify (CLAUDE.md §5: hand-check a sample).

Writes docs/hand_checks_todo/<name>.csv with `auto_value` filled and `checked_value` BLANK.
A person fills `checked_value` + `checker`, then moves the file to docs/hand_checks/ so
`run.py tables` counts it. Nothing here fills in a check automatically.

  python -m src.data.sample_hand_check
"""
from __future__ import annotations

import pandas as pd

from src.utils import ROOT, load_config


def main() -> None:
    cfg = load_config()
    out_dir = ROOT / "docs" / "hand_checks_todo"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Indeed pay parsing: does salary_formatted -> hourly_pay read correctly?
    jobs = pd.read_parquet(cfg["paths"]["interim"] / "indeed.parquet")
    raw = pd.read_csv(cfg["paths"]["raw"] / "indeed" / "indeed_job_listings.csv",
                      usecols=["jobid", "salary_formatted"], dtype=str, on_bad_lines="skip", engine="python")
    s = jobs[jobs["has_pay"]].sample(40, random_state=cfg["seed"]).merge(raw.drop_duplicates("jobid"), on="jobid")
    pd.DataFrame({"item_id": s["jobid"],
                  "salary_formatted": s["salary_formatted"],
                  "auto_value": s["hourly_pay"].round(2).astype("string").fillna("unparsed"),
                  "checked_value": "", "checker": ""}).to_csv(out_dir / "indeed_pay_parse.csv", index=False)

    # 2. Target label: is the 'high rent-growth' label right, read off Zillow's own numbers?
    m = pd.read_parquet(cfg["features"]["master_table"])
    m = m[~m["year"].isin(cfg["split"]["test_values"])]          # never sample test labels
    s = m.sample(30, random_state=cfg["seed"])
    # Inputs a person needs: both December rents (straight from Zillow's file) and that year's
    # top-third cutoff, i.e. the smallest growth among ZIPs ranked in the top third. The checker
    # computes growth = rent_dec_next / rent_dec_t - 1 and compares it with the cutoff.
    zr = pd.read_parquet(cfg["paths"]["interim"] / "zillow_research.parquet")
    dec = zr[~zr["is_partial_year"]].pivot(index="zipcode", columns="year", values="rent")
    cut = {}
    for y in sorted(s["year"].unique()):
        g = (dec[y + 1] / dec[y] - 1).dropna()
        cut[y] = g[g.rank(pct=True) > 2 / 3].min()
    pd.DataFrame({"item_id": s["id"], "zipcode": s["zipcode"], "year_t": s["year"],
                  "rent_dec_t": [round(dec.at[z, y], 2) for z, y in zip(s["zipcode"], s["year"])],
                  "rent_dec_next": [round(dec.at[z, y + 1], 2) for z, y in zip(s["zipcode"], s["year"])],
                  "top_third_cutoff_pct": [round(100 * cut[y], 2) for y in s["year"]],
                  "auto_value": s["target"].astype(str), "checked_value": "", "checker": ""}
                 ).to_csv(out_dir / "rent_growth_label.csv", index=False)
    print("wrote docs/hand_checks_todo/indeed_pay_parse.csv (40) and rent_growth_label.csv (30)")


if __name__ == "__main__":
    main()
