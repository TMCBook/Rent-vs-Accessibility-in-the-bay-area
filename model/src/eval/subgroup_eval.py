"""Subgroup / fairness table (04): per subgroup column and group, n, model metrics, baseline
primary metric, and gap vs overall. Groups with n < task.small_n get small_n_caution=True."""
from __future__ import annotations

import pandas as pd

from src.eval.metrics import HIGHER_IS_BETTER, PRIMARY, compute

COLUMNS = ["split", "subgroup_type", "group", "n", "small_n_caution", "primary_metric", "model_value",
           "baseline_value", "overall_model_value", "gap_vs_overall", "worse_than_overall"]


def subgroup_table(preds: pd.DataFrame, master: pd.DataFrame, cfg: dict, split: str) -> pd.DataFrame:
    t = cfg["task"]
    task, prim = t["type"], PRIMARY[t["type"]]
    main_model = cfg["model"]["name"]
    base = next((b for b in cfg["baselines"] if b != "dummy"), cfg["baselines"][0])
    sg_cols = t.get("subgroup_cols") or []
    p = preds[preds["split"] == split].merge(master[[t["id_col"], *sg_cols]], on=t["id_col"], how="left")
    pm, pb = p[p["model"] == main_model], p[p["model"] == base]
    overall = compute(pm, task)[prim]
    rows = []
    for col in sg_cols:
        for g, dm in pm.groupby(col, dropna=False):
            db = pb[pb[col].eq(g) if pd.notna(g) else pb[col].isna()]
            m, b = compute(dm, task), compute(db, task)
            gap = round(m[prim] - overall, 4)
            rows.append({"split": split, "subgroup_type": col, "group": "MISSING" if pd.isna(g) else g,
                         "n": len(dm), "small_n_caution": len(dm) < t.get("small_n", 30),
                         "primary_metric": prim, "model_value": m[prim], "baseline_value": b[prim],
                         "overall_model_value": overall, "gap_vs_overall": gap,
                         "worse_than_overall": gap < 0 if HIGHER_IS_BETTER[prim] else gap > 0,
                         **{f"model_{k}": v for k, v in m.items() if k != prim}})
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=COLUMNS)
