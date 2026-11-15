"""Step `train`: fit the main model and every baseline on the TRAIN split only.
Saves outputs/models/<name>.joblib and <name>.json (features, seed, versions, n_train)."""
from __future__ import annotations

import json
import subprocess
from importlib.metadata import version

import joblib
import pandas as pd
from pandas.api import types as pdt

from src.utils import ROOT, load_config, set_seed, split_path


def feature_columns(df: pd.DataFrame, cfg: dict) -> tuple[list[str], list[str]]:
    t, s = cfg["task"], cfg["split"]
    cat = list(t.get("categorical_cols") or [])
    blocked = {t["id_col"], t["target_col"], *(t.get("exclude_cols") or [])}
    if s.get("group_col"):
        blocked.add(s["group_col"])
    if t.get("feature_cols"):
        num = [c for c in t["feature_cols"] if c not in cat]
    else:
        num = [c for c in df.columns if c not in blocked and c not in cat
               and pdt.is_numeric_dtype(df[c]) and not pdt.is_bool_dtype(df[c])]
    leaked = blocked & set(num + cat)
    if leaked:
        raise SystemExit(f"Blocked columns used as features: {sorted(leaked)}")
    return num, cat


def model_names(cfg: dict) -> list[str]:
    return [cfg["model"]["name"], *cfg["baselines"]]


def load_frame(cfg: dict) -> pd.DataFrame:
    df = pd.read_parquet(cfg["features"]["master_table"])
    sp = pd.read_parquet(split_path(cfg))
    return df.merge(sp, on=cfg["task"]["id_col"], how="inner", validate="one_to_one")


def _git_hash() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True).stdout.strip() or "uncommitted"
    except OSError:
        return "unknown"


def main() -> None:
    from src.models.baseline import build_pipeline

    cfg = load_config()
    set_seed(cfg["seed"])
    df = load_frame(cfg)
    train = df[df["split"] == "train"]
    num, cat = feature_columns(df, cfg)
    if not num and not cat:
        raise SystemExit("No feature columns found; set task.feature_cols / categorical_cols in config.yaml")
    X, y = train[num + cat], train[cfg["task"]["target_col"]]
    for name in model_names(cfg):
        pipe = build_pipeline(name, cfg, num, cat).fit(X, y)
        joblib.dump(pipe, cfg["paths"]["models"] / f"{name}.joblib")
        meta = {"name": name, "role": "model" if name == cfg["model"]["name"] else "baseline",
                "task": cfg["task"]["type"], "numeric_features": num, "categorical_features": cat,
                "n_train": len(train), "seed": cfg["seed"], "git": _git_hash(),
                "versions": {p: version(p) for p in ["scikit-learn", "pandas", "numpy"]}}
        (cfg["paths"]["models"] / f"{name}.json").write_text(json.dumps(meta, indent=2))
        print(f"trained {name} on {len(train)} rows, {len(num) + len(cat)} features")


if __name__ == "__main__":
    main()
