"""Task-appropriate metrics. PRIMARY metric is what subgroup gaps and headline findings use."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn import metrics as M

PRIMARY = {"classification": "macro_f1", "regression": "rmse"}
HIGHER_IS_BETTER = {"macro_f1": True, "accuracy": True, "precision_macro": True, "recall_macro": True,
                    "auc": True, "rmse": False, "mae": False, "r2": True}


def compute(d: pd.DataFrame, task: str) -> dict[str, float]:
    """d has y_true, y_pred, score, pos_label (score/pos_label set only for binary classification)."""
    yt, yp = d["y_true"], d["y_pred"]
    if task == "classification":
        out = {
            "macro_f1": M.f1_score(yt, yp, average="macro", zero_division=0),
            "accuracy": M.accuracy_score(yt, yp),
            "precision_macro": M.precision_score(yt, yp, average="macro", zero_division=0),
            "recall_macro": M.recall_score(yt, yp, average="macro", zero_division=0),
            "auc": np.nan,
        }
        if len(d) and d["score"].notna().all():
            is_pos = yt.astype(str) == d["pos_label"].astype(str)
            if is_pos.nunique() == 2:
                out["auc"] = M.roc_auc_score(is_pos, d["score"])
    else:
        out = {"rmse": float(np.sqrt(M.mean_squared_error(yt, yp))),
               "mae": M.mean_absolute_error(yt, yp),
               "r2": M.r2_score(yt, yp) if len(d) > 1 else np.nan}
    return {k: round(float(v), 4) for k, v in out.items()}
