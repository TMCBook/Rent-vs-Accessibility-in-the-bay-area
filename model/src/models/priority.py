"""Step `priority`: where to help first.

For every ZIP with December 2025 data, the trained main model gives P(rent growth during 2026 is in
the Bay Area's top third). The help-first score combines three things:

    priority = P(high rent growth) x (1 - access_score / 100) x renters

  * P(high rent growth): risk that renters get priced further out soon (the model's forecast)
  * 1 - access_score/100: how far the ZIP is from groceries, pharmacies, doctors, banks, transit
  * renters: how many people the help reaches (proxy: rental listings, config priority.renters_col)

With priority.affordable_only, only ZIPs at or below the median rent are ranked: that's where
low-wage renters can live today, and where losing ground hurts most.

Also writes a LIVE CHECK: Zillow has published September 2026 rents, so the 2026 forecast can be
compared with the first 9 months of actual growth. This is a partial year and is reported
separately from the held-out test set.

Writes outputs/tables/08_help_first_ranking.csv and 08b_forecast_live_check.csv.
"""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from src.utils import load_config, write_table


def main() -> None:
    cfg = load_config()
    pc = cfg["priority"]
    name = cfg["model"]["name"]
    pipe = joblib.load(cfg["paths"]["models"] / f"{name}.joblib")
    f = pd.read_parquet(cfg["paths"]["processed"] / "forecast_frame.parquet")
    X = f[pipe.named_steps["prep"].feature_names_in_]
    f["p_high_rent_growth"] = pipe.predict_proba(X)[:, list(pipe.classes_).index(1)]
    f["access_gap"] = 1 - f["access_score"] / 100
    f["renters"] = f[pc["renters_col"]].fillna(0)
    f["priority_score"] = f["p_high_rent_growth"] * f["access_gap"] * f["renters"]
    rent_median = f["rent"].median()
    f["at_or_below_median_rent"] = f["rent"] <= rent_median

    ranked = f[f["at_or_below_median_rent"]] if pc.get("affordable_only") else f
    ranked = ranked.sort_values("priority_score", ascending=False).reset_index(drop=True)
    ranked["rank"] = np.arange(1, len(ranked) + 1)
    cols = ["rank", "zipcode", "city", "county", "priority_score", "p_high_rent_growth", "access_score",
            "renters", "rent", "rent_g1", "jobs_median_hourly", "dist_grocery_mi", "dist_pharmacy_mi",
            "dist_primary_care_mi", "dist_transit_mi", "dist_food_bank_mi"]
    out = ranked[cols].copy()
    out["rent_dec_2025"] = out.pop("rent").round(0)
    out["rent_growth_2025_pct"] = (100 * out.pop("rent_g1")).round(1)
    for c in ["priority_score", "p_high_rent_growth"]:
        out[c] = out[c].round(3)
    print(f"ranked {len(out)} ZIPs (median Dec 2025 rent ${rent_median:,.0f}); top {pc['top_n']}:")
    print(out.head(pc["top_n"])[["rank", "zipcode", "city", "priority_score", "p_high_rent_growth",
                                  "access_score", "renters"]].to_string(index=False))
    write_table(out, cfg, "08_help_first_ranking.csv")

    # live check against Zillow's September 2026 rents (partial year)
    zr = pd.read_parquet(cfg["paths"]["interim"] / "zillow_research.parquet")
    sep = zr[(zr["year"] == 2026) & zr["is_partial_year"]][["zipcode", "rent"]].rename(columns={"rent": "rent_sep_2026"})
    lc = f.merge(sep, on="zipcode", how="inner", validate="one_to_one").dropna(subset=["rent_sep_2026", "rent"])
    lc["growth_dec25_sep26"] = lc["rent_sep_2026"] / lc["rent"] - 1
    lc["actual_top_third"] = (lc["growth_dec25_sep26"].rank(pct=True) > 2 / 3).astype(int)
    rows = [{"check": "2026 forecast vs actual Dec 2025 -> Sep 2026 growth (partial year)",
             "n_zips": len(lc), "auc": round(roc_auc_score(lc["actual_top_third"], lc["p_high_rent_growth"]), 4),
             "persistence_auc": round(roc_auc_score(lc["actual_top_third"], lc["rent_g1_rank"].fillna(.5)), 4),
             "top_quintile_hit_rate": round(lc[lc["p_high_rent_growth"] >= lc["p_high_rent_growth"].quantile(.8)]
                                            ["actual_top_third"].mean(), 4),
             "base_rate": round(lc["actual_top_third"].mean(), 4)}]
    write_table(pd.DataFrame(rows), cfg, "08b_forecast_live_check.csv")
    print(rows[0])


if __name__ == "__main__":
    main()
