"""Step `tables`: assemble 06_hand_check_sample.csv and 07_key_findings.csv.

06 reads every docs/hand_checks/*.csv with columns:
    item_id, auto_value, checked_value, checker      (one row per hand-checked item)
07 derives every finding from the other tables — no hand-typed numbers (CLAUDE.md §7).
"""
from __future__ import annotations

import pandas as pd

from src.eval.metrics import HIGHER_IS_BETTER, PRIMARY
from src.utils import load_config, write_table

HAND_CHECK_COLS = ["item_id", "auto_value", "checked_value", "checker"]


def hand_check_table(cfg: dict) -> pd.DataFrame:
    rows = []
    for f in sorted(cfg["paths"]["hand_checks"].glob("*.csv")):
        d = pd.read_csv(f, dtype=str, keep_default_na=False)  # keep "N/A" as written
        missing = set(HAND_CHECK_COLS) - set(d.columns)
        if missing:
            raise SystemExit(f"{f.name}: missing columns {sorted(missing)}")
        a, c = d["auto_value"].fillna("").str.strip().str.lower(), d["checked_value"].fillna("").str.strip().str.lower()
        if (c == "").any():
            raise SystemExit(f"{f.name}: {int((c == '').sum())} rows have no checked_value yet "
                             f"(write N/A for a row the checker deliberately left unchecked)")
        skipped = c.isin(["n/a", "na"])           # checker chose not to judge this row
        a, c = a[~skipped], c[~skipped]
        an, cn = pd.to_numeric(a, errors="coerce"), pd.to_numeric(c, errors="coerce")
        # numbers agree within 1 cent / 0.01 (so "17.50" matches "17.5"); text must match exactly
        agree = ((an - cn).abs() <= 0.01).where(an.notna() & cn.notna(), a == c)
        rows.append({"check": f.stem, "sample_size": len(d), "n_checked": len(agree),
                     "n_not_checked": int(skipped.sum()),
                     "agreement_pct": round(100 * agree.mean(), 1),
                     "n_disagree": int((~agree).sum()),
                     "checkers": ";".join(sorted(d["checker"].dropna().unique())),
                     "source_file": f"docs/hand_checks/{f.name}"})
    return pd.DataFrame(rows, columns=["check", "sample_size", "n_checked", "n_not_checked", "agreement_pct", "n_disagree", "checkers",
                                       "source_file"])


def key_findings(cfg: dict, hand: pd.DataFrame) -> pd.DataFrame:
    tdir = cfg["paths"]["tables"]
    prim = PRIMARY[cfg["task"]["type"]]
    hib = HIGHER_IS_BETTER[prim]
    F = []

    def add(finding, number, source):
        F.append({"id": f"F{len(F) + 1}", "finding": finding, "number": number, "source": source})

    mvb_path = tdir / "03_model_vs_baseline.csv"
    if mvb_path.exists():
        mvb = pd.read_csv(mvb_path)
        p = mvb[mvb["metric"] == prim]
        col = "test" if (p["test"] != "LOCKED").all() else "val"
        vals = p.set_index("model")[col].astype(float)
        main = cfg["model"]["name"]
        add(f"{main} {prim} on {col} split", vals[main], "03_model_vs_baseline.csv")
        for b in cfg["baselines"]:
            add(f"baseline {b} {prim} on {col} split", vals[b], "03_model_vs_baseline.csv")
        best_b = vals[cfg["baselines"]].max() if hib else vals[cfg["baselines"]].min()
        add(f"{main} improvement over best baseline ({prim}, {col}; positive = better)",
            round((vals[main] - best_b) * (1 if hib else -1), 4), "03_model_vs_baseline.csv")

    sg_path = tdir / "04_subgroup_performance.csv"
    if sg_path.exists():
        sg = pd.read_csv(sg_path)
        sg = sg[~sg["small_n_caution"].astype(bool)] if len(sg) else sg
        if len(sg):
            worst = sg.sort_values("gap_vs_overall", ascending=hib).iloc[0]
            add(f"worst subgroup (n>={cfg['task'].get('small_n', 30)}): {worst['subgroup_type']}={worst['group']} "
                f"{prim} gap vs overall (n={worst['n']})", worst["gap_vs_overall"], "04_subgroup_performance.csv")

    ja_path = tdir / "02_join_audit.csv"
    if ja_path.exists():
        for _, r in pd.read_csv(ja_path).iterrows():
            add(f"join '{r['step']}' % left rows unmatched", r["pct_left_unmatched"], "02_join_audit.csv")

    for _, r in hand.iterrows():
        add(f"hand-check '{r['check']}' agreement % (n={r['n_checked']} checked)", r["agreement_pct"],
            "06_hand_check_sample.csv")
    return pd.DataFrame(F, columns=["id", "finding", "number", "source"])


def main() -> None:
    cfg = load_config()
    hand = hand_check_table(cfg)
    write_table(hand, cfg, "06_hand_check_sample.csv")
    write_table(key_findings(cfg, hand), cfg, "07_key_findings.csv")


if __name__ == "__main__":
    main()
