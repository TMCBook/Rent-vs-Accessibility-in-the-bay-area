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
    pd.DataFrame({"item_id": s["id"], "zipcode": s["zipcode"], "year_t": s["year"],
                  "rent_dec_t": s["rent"].round(0), "next_growth_pct": (100 * s["next_rent_growth"]).round(2),
                  "auto_value": s["target"].astype(str), "checked_value": "", "checker": ""}
                 ).to_csv(out_dir / "rent_growth_label.csv", index=False)
    print("wrote docs/hand_checks_todo/indeed_pay_parse.csv (40) and rent_growth_label.csv (30)")


if __name__ == "__main__":
    main()
