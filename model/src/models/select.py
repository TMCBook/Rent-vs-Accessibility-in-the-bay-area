"""Step `select`: model selection by rolling-origin (expanding window) cross-validation.

For each fold year y in the TRAIN+VAL years, fit on years < y and score year y. The test years
(config split.test_values) are dropped before anything else, so model choice never sees them.
Writes outputs/tables/09_model_selection_cv.csv (one row per candidate) — the evidence for the
model and params set in config.yaml.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, roc_auc_score

from src.models.baseline import build_pipeline
from src.models.train import feature_columns
from src.utils import load_config, write_table

SMALL_GB = {"max_depth": 2, "learning_rate": 0.03, "max_iter": 200, "min_samples_leaf": 30,
            "l2_regularization": 2.0}
CANDIDATES = [  # (label, model name, params, feature set)
    ("logistic C=0.1 (all features)", "logistic", {"C": 0.1, "class_weight": "balanced"}, "all"),
    ("logistic C=1 (all features)", "logistic", {"C": 1.0, "class_weight": "balanced"}, "all"),
    ("logistic C=0.03 (all features)", "logistic", {"C": 0.03, "class_weight": "balanced"}, "all"),
    ("logistic C=0.1 (rent history only)", "logistic", {"C": 0.1, "class_weight": "balanced"}, "history"),
    ("gradient boosting, small (all features)", "hist_gb", SMALL_GB, "all"),
    ("gradient boosting, depth 3 (all features)", "hist_gb",
     {"max_depth": 3, "learning_rate": 0.05, "max_iter": 300, "min_samples_leaf": 20}, "all"),
    ("random forest (all features)", "random_forest",
     {"n_estimators": 500, "min_samples_leaf": 10, "max_features": 0.5}, "all"),
    ("persistence rule", "persistence", {}, "persistence"),
]
FOLD_YEARS = [2019, 2020, 2021, 2022, 2023]


def main() -> None:
    warnings.filterwarnings("ignore", category=UserWarning)
    cfg = load_config()
    df = pd.read_parquet(cfg["features"]["master_table"])
    tcol = cfg["split"]["time_col"]
    df = df[~df[tcol].isin(cfg["split"]["test_values"])]          # test years never loaded
    num, cat = feature_columns(df, cfg)
    hist = [c for c in cfg["baseline_params"]["history_logistic"]["columns"] if c in num]
    y_col = cfg["task"]["target_col"]
    rows = []
    for label, name, params, fs in CANDIDATES:
        c = {**cfg, "model": {"name": name, "params": params}}
        cols, cats = {"all": (num, cat), "history": (hist, []), "persistence": (num, cat)}[fs]
        aucs, f1s = [], []
        for y in FOLD_YEARS:
            tr, va = df[df[tcol] < y], df[df[tcol] == y]
            pipe = build_pipeline(name, c, cols, cats).fit(tr[cols + cats], tr[y_col])
            score = pipe.predict_proba(va[cols + cats])[:, 1]
            aucs.append(roc_auc_score(va[y_col], score))
            f1s.append(f1_score(va[y_col], pipe.predict(va[cols + cats]), average="macro"))
        rows.append({"candidate": label, "model": name, "params": str(params), "features": fs,
                     "mean_auc": round(float(np.mean(aucs)), 4), "mean_macro_f1": round(float(np.mean(f1s)), 4),
                     **{f"auc_{y}": round(a, 4) for y, a in zip(FOLD_YEARS, aucs)},
                     "folds": f"train on years < y, score year y, y in {FOLD_YEARS}"})
        print(f"{label:45s} mean AUC {np.mean(aucs):.3f}  macro-F1 {np.mean(f1s):.3f}")
    out = pd.DataFrame(rows).sort_values("mean_auc", ascending=False)
    write_table(out, cfg, "09_model_selection_cv.csv")


if __name__ == "__main__":
    main()
