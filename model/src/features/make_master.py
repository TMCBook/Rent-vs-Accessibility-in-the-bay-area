"""Step `features`: call the configured builder, check the master-table contract, write it,
and write outputs/tables/02_join_audit.csv."""
from __future__ import annotations

import importlib

from src.features.joins import audit_rows, reset_audit
from src.utils import load_config, write_table


def check_master(df, cfg) -> list[str]:
    t = cfg["task"]
    probs = []
    for c in [t["id_col"], t["target_col"], *t["subgroup_cols"]]:
        if c not in df.columns:
            probs.append(f"master table missing required column {c!r}")
    if t["id_col"] in df.columns and df[t["id_col"]].duplicated().any():
        probs.append(f"id_col {t['id_col']!r} is not unique ({int(df[t['id_col']].duplicated().sum())} dups)")
    if t["target_col"] in df.columns and df[t["target_col"]].isna().any():
        probs.append(f"target {t['target_col']!r} has {int(df[t['target_col']].isna().sum())} nulls")
    return probs


def main() -> None:
    cfg = load_config()
    reset_audit()
    mod = importlib.import_module(f"src.features.{cfg['features']['builder']}")
    df = mod.build(cfg)
    probs = check_master(df, cfg)
    if probs:
        raise SystemExit("Master table contract violations:\n  " + "\n  ".join(probs))
    out = cfg["features"]["master_table"]
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"wrote master table {out.name}: {df.shape}")
    write_table(audit_rows(), cfg, "02_join_audit.csv")


if __name__ == "__main__":
    main()
