"""Human failure notes for outputs/tables/05_failure_examples.csv.

The same ZIP-year appears in 05 once per subgroup it belongs to (county, access tier, rent tier).
This module turns 05 into a one-row-per-ZIP worksheet for a person to annotate, then copies the
finished notes back into every matching row of 05.

  python -m src.eval.failure_notes worksheet   # writes docs/failure_notes_worksheet.csv
  python -m src.eval.failure_notes apply       # copies the `note` column back into 05

Worksheet columns:
  last_yr_growth_pct / actual_growth_pct   rent growth during year t and t+1, in %
  cutoff_pct                               that year's top-third cutoff (label = 1 if actual >= cutoff)
  case                                     which pattern the row matches (by simple rules, see CASES)
  note_template                            a starting sentence with ___ blanks: a SUGGESTION ONLY
  note                                     what the person writes (copied into 05 by `apply`)

`note_template` is generated; `note` must be written by a person. `apply` refuses notes that still
contain ___ and copies only the `note` column, never the template.
"""
from __future__ import annotations

import sys

import pandas as pd

from src.utils import ROOT, load_config

WORKSHEET = ROOT / "docs" / "failure_notes_worksheet.csv"
CASES = {
    "false alarm: expected rebound":
        "Rent fell or was flat in 2024 (___%); model expected a rebound. Rose only ___%, below the ___% cutoff.",
    "false alarm: ordinary year":
        "Steady growth in 2024 (___%); model flagged a spike, but growth stayed at ___%, below the ___% cutoff.",
    "missed spike: momentum":
        "Already rising ___% in 2024; model expected cooling, but rent kept climbing (+___%).",
    "missed spike: sudden jump":
        "Little growth in 2024 (___%), then a sudden jump to ___% that past trends didn't signal.",
}
NEAR_MISS = " Near miss: ___% is just under the ___% cutoff."
CONFIDENT = " Model was very confident (score ___)."


def _cutoffs(cfg: dict) -> dict[int, float]:
    zr = pd.read_parquet(cfg["paths"]["interim"] / "zillow_research.parquet")
    dec = zr[~zr["is_partial_year"]].pivot(index="zipcode", columns="year", values="rent")
    out = {}
    for y in dec.columns:
        if y + 1 in dec.columns:
            g = (dec[y + 1] / dec[y] - 1).dropna()
            out[int(y)] = 100 * g[g.rank(pct=True) > 2 / 3].min()
    return out


def _case(r) -> str:
    if r["true"] == 0:
        return "false alarm: expected rebound" if r["last_yr_growth_pct"] <= 0.5 else "false alarm: ordinary year"
    return "missed spike: momentum" if r["last_yr_growth_pct"] >= 4 else "missed spike: sudden jump"


def worksheet() -> None:
    cfg = load_config()
    fe = pd.read_csv(cfg["paths"]["tables"] / "05_failure_examples.csv", dtype={"zipcode": str},
                     keep_default_na=False)
    if (fe["note"].str.strip() != "").any():
        print("note: 05 already has some notes; they are copied into the worksheet")
    groups = fe.groupby("id")["subgroup"].agg(lambda s: "; ".join(dict.fromkeys(s)))
    ws = fe.drop_duplicates("id").set_index("id")
    ws["listed_under"] = groups
    cut = _cutoffs(cfg)
    ws["last_yr_growth_pct"] = (100 * ws["rent_g1"].astype(float)).round(1)
    ws["actual_growth_pct"] = (100 * ws["next_rent_growth"].astype(float)).round(1)
    ws["cutoff_pct"] = ws["year"].astype(int).map(cut).round(2)
    ws["score"] = ws["score"].astype(float).round(2)
    ws["case"] = ws.apply(_case, axis=1)
    ws["note_template"] = ws["case"].map(CASES)
    near = (ws["true"] == 0) & (ws["actual_growth_pct"] >= ws["cutoff_pct"] - 0.6)
    ws.loc[near, "note_template"] += NEAR_MISS
    conf = (ws["score"] >= 0.85) | (ws["score"] <= 0.2)
    ws.loc[conf, "note_template"] += CONFIDENT
    cols = ["zipcode", "city", "listed_under", "true", "pred", "score", "last_yr_growth_pct",
            "actual_growth_pct", "cutoff_pct", "case", "note_template", "note"]
    out = ws.reset_index()[["id", *cols]].sort_values(["case", "city", "id"])
    out.to_csv(WORKSHEET, index=False)
    print(f"wrote {WORKSHEET.relative_to(ROOT)} ({len(out)} ZIPs): "
          + ", ".join(f"{k} {v}" for k, v in out["case"].value_counts().items()))


def apply() -> None:
    cfg = load_config()
    ws = pd.read_csv(WORKSHEET, dtype=str, keep_default_na=False)
    note = ws["note"].str.strip()
    missing = ws.loc[note == "", "id"].tolist()
    blanks = ws.loc[note.str.contains("___", regex=False), "id"].tolist()
    if missing or blanks:
        raise SystemExit("Notes not finished:\n"
                         + (f"  empty: {', '.join(missing)}\n" if missing else "")
                         + (f"  still has ___: {', '.join(blanks)}\n" if blanks else ""))
    path = cfg["paths"]["tables"] / "05_failure_examples.csv"
    fe = pd.read_csv(path, dtype=str, keep_default_na=False)
    by_id = dict(zip(ws["id"], note))
    unknown = sorted(set(fe["id"]) - set(by_id))
    if unknown:
        raise SystemExit(f"worksheet has no row for: {unknown} (rebuild it with `worksheet`)")
    fe["note"] = fe["id"].map(by_id)
    fe.to_csv(path, index=False)
    print(f"copied {len(by_id)} notes into {len(fe)} rows of 05_failure_examples.csv")


if __name__ == "__main__":
    {"worksheet": worksheet, "apply": apply}[(sys.argv[1:] or ["worksheet"])[0]]()
