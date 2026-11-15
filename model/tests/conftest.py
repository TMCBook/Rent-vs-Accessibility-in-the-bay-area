"""Synthetic fixture for pipeline smoke tests. SYNTHETIC DATA ONLY — lives in a pytest tmp dir,
never in outputs/, never reported."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import yaml

from src.utils import ROOT


def synthetic_master(n: int = 600, task: str = "classification", seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    city = rng.choice(["A", "B", "C", "D"], size=n)
    kind = rng.choice(["clinic", "grocery", "school"], size=n)
    x1, x2 = rng.normal(size=n), rng.normal(size=n)
    lin = 1.5 * x1 - x2 + (city == "A") * 0.8 + rng.normal(scale=0.7, size=n)
    target = (lin > 0).astype(int) if task == "classification" else lin
    return pd.DataFrame({"id": [f"r{i}" for i in range(n)], "place_id": [f"p{i // 3}" for i in range(n)],
                         "x1": x1, "x2": x2, "city": city, "kind": kind, "target": target})


@pytest.fixture
def synth_cfg(tmp_path, monkeypatch):
    def make(task: str = "classification", group_col: str | None = None):
        base = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
        base["paths"] = {k: str(tmp_path / k) for k in base["paths"]}
        base["features"]["master_table"] = str(tmp_path / "processed" / "master.parquet")
        # synthetic data has none of the project's columns: reset project-specific settings
        base["task"].update({"type": task, "categorical_cols": ["city"], "subgroup_cols": ["city", "kind"],
                             "display_cols": ["x1"], "exclude_cols": [], "positive_label": None})
        base["split"].update({"group_col": group_col, "time_col": None})
        base["model"] = {"name": "hist_gb", "params": {}}
        base["baselines"] = ["dummy", "linear"]
        base["final_eval"] = True
        (tmp_path / "processed").mkdir(parents=True, exist_ok=True)
        synthetic_master(task=task).to_parquet(base["features"]["master_table"], index=False)
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text(yaml.safe_dump(base), encoding="utf-8")
        monkeypatch.setenv("DATATHON_CONFIG", str(cfg_path))
        monkeypatch.delenv("DATATHON_FINAL_EVAL", raising=False)
        return tmp_path
    return make


def run_pipeline() -> None:
    from src.eval import evaluate, make_tables
    from src.models import predict, split, train
    from src.viz import figures
    for mod in (split, train, predict, evaluate, make_tables, figures):
        mod.main()
