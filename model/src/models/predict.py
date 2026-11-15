"""Step `predict`: predictions for every model on VAL, and on TEST only when final_eval is on.

Writes data/processed/predictions.parquet (long format):
  <id_col>, split, model, y_true, y_pred, score, pos_label
  (score = P(pos_label) for binary classification, else NaN)
"""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd

from src.models.train import load_frame, model_names
from src.utils import load_config, predictions_path


def positive_label(pipe, cfg):
    classes = list(pipe.classes_)
    if len(classes) != 2:
        return None
    pl = cfg["task"].get("positive_label")
    return pl if pl is not None else classes[1]


def main() -> None:
    cfg = load_config()
    t = cfg["task"]
    df = load_frame(cfg)
    splits = ["val", "test"] if cfg.get("final_eval") else ["val"]
    print(f"predicting splits: {splits}" + ("" if cfg.get("final_eval") else "  (test LOCKED until final)"))
    parts = []
    for name in model_names(cfg):
        pipe = joblib.load(cfg["paths"]["models"] / f"{name}.joblib")
        for sp in splits:
            d = df[df["split"] == sp]
            X = d[pipe.named_steps["prep"].feature_names_in_]
            out = pd.DataFrame({t["id_col"]: d[t["id_col"]].to_numpy(), "split": sp, "model": name,
                                "y_true": d[t["target_col"]].to_numpy(), "y_pred": pipe.predict(X)})
            if t["type"] == "classification" and (pl := positive_label(pipe, cfg)) is not None:
                col = list(pipe.classes_).index(pl)
                out["score"] = pipe.predict_proba(X)[:, col]
                out["pos_label"] = str(pl)
            else:
                out["score"] = np.nan
                out["pos_label"] = None
            parts.append(out)
    pd.concat(parts, ignore_index=True).to_parquet(predictions_path(cfg), index=False)


if __name__ == "__main__":
    main()
