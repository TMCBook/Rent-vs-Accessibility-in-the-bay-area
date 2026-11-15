"""Failure examples (05): for each subgroup column, the largest groups, up to N concrete
mispredictions each (classification: wrong label, most confident first; regression: largest
absolute error). `note` is left blank for a human to fill in — never auto-generated."""
from __future__ import annotations

import pandas as pd

COLUMNS = ["id", "split", "subgroup_type", "subgroup", "true", "pred", "score", "abs_error", "note"]
# abs_error only means something for regression; classification tables leave it out.


def failure_examples(preds: pd.DataFrame, master: pd.DataFrame, cfg: dict, split: str) -> pd.DataFrame:
    t, fe = cfg["task"], cfg["failure_examples"]
    sg_cols, disp = t.get("subgroup_cols") or [], t.get("display_cols") or []
    keep = list(dict.fromkeys([t["id_col"], *sg_cols, *disp]))
    p = preds[(preds["split"] == split) & (preds["model"] == cfg["model"]["name"])]
    p = p.merge(master[keep], on=t["id_col"], how="left")
    if t["type"] == "classification":
        p = p[p["y_true"] != p["y_pred"]].copy()
        conf = (p["score"] - 0.5).abs() if p["score"].notna().any() else pd.Series(0, index=p.index)
        p["_rank"] = conf
        p["abs_error"] = pd.NA
    else:
        p = p.copy()
        p["abs_error"] = (p["y_true"] - p["y_pred"]).abs().round(4)
        p["_rank"] = p["abs_error"]
    rows = []
    for col in sg_cols:
        top = p[col].value_counts().head(fe["max_groups_per_subgroup"]).index
        for g in top:
            d = p[p[col] == g].sort_values("_rank", ascending=False).head(fe["per_group"])
            for _, r in d.iterrows():
                rows.append({"id": r[t["id_col"]], "split": split, "subgroup_type": col, "subgroup": g,
                             "true": r["y_true"], "pred": r["y_pred"], "score": r["score"],
                             "abs_error": r["abs_error"], "note": "",
                             **{c: r[c] for c in disp}})
    out = pd.DataFrame(rows) if rows else pd.DataFrame(columns=COLUMNS + disp)
    if t["type"] == "classification":
        out = out.drop(columns=["abs_error"])
    return out
