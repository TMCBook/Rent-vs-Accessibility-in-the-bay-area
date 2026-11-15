"""Step `eval`: writes the model/subgroup/failure tables.

  03_model_vs_baseline.csv   model, role, metric, val, test   (test = LOCKED until final_eval)
  04_subgroup_performance.csv
  05_failure_examples.csv
Subgroup + failure analysis use the TEST split when available, else VAL (column `split` says which).
"""
from __future__ import annotations

import pandas as pd

from src.eval.error_analysis import failure_examples
from src.eval.metrics import compute
from src.eval.subgroup_eval import subgroup_table
from src.models.train import model_names
from src.utils import load_config, predictions_path, write_table


def model_vs_baseline(preds: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    task, main_model = cfg["task"]["type"], cfg["model"]["name"]
    rows = []
    for name in model_names(cfg):
        per_split = {}
        for sp in ["val", "test"]:
            d = preds[(preds["model"] == name) & (preds["split"] == sp)]
            per_split[sp] = compute(d, task) if len(d) else None
        for metric in per_split["val"]:
            rows.append({"model": name, "role": "model" if name == main_model else "baseline",
                         "metric": metric, "val": per_split["val"][metric],
                         "test": per_split["test"][metric] if per_split["test"] else "LOCKED",
                         "n_val": int(((preds["model"] == name) & (preds["split"] == "val")).sum()),
                         "n_test": int(((preds["model"] == name) & (preds["split"] == "test")).sum())})
    return pd.DataFrame(rows)


def main() -> None:
    cfg = load_config()
    preds = pd.read_parquet(predictions_path(cfg))
    write_table(model_vs_baseline(preds, cfg), cfg, "03_model_vs_baseline.csv")
    report_split = "test" if (preds["split"] == "test").any() else "val"
    master = pd.read_parquet(cfg["features"]["master_table"])
    write_table(subgroup_table(preds, master, cfg, report_split), cfg, "04_subgroup_performance.csv")
    write_table(failure_examples(preds, master, cfg, report_split), cfg, "05_failure_examples.csv")


if __name__ == "__main__":
    main()
