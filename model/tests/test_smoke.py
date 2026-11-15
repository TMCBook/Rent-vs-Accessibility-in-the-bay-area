"""End-to-end smoke test on synthetic data: every fixed-name table is produced and well-formed."""
from __future__ import annotations

import pandas as pd
import pytest

from tests.conftest import run_pipeline


@pytest.mark.parametrize("task", ["classification", "regression"])
def test_pipeline_end_to_end(synth_cfg, task):
    tmp = synth_cfg(task=task, group_col="place_id")
    run_pipeline()
    T = tmp / "tables"
    mvb = pd.read_csv(T / "03_model_vs_baseline.csv")
    assert set(mvb["role"]) == {"model", "baseline"}
    assert (mvb["test"].astype(str) != "LOCKED").all()
    sg = pd.read_csv(T / "04_subgroup_performance.csv")
    assert len(sg) >= 3 and {"n", "gap_vs_overall", "baseline_value"} <= set(sg.columns)
    fe = pd.read_csv(T / "05_failure_examples.csv")
    assert len(fe) > 0 and "note" in fe.columns and "x1" in fe.columns
    kf = pd.read_csv(T / "07_key_findings.csv")
    assert kf["id"].str.match(r"F\d+").all() and len(kf) >= 3
    assert (tmp / "figures" / "fig_model_vs_baseline.png").exists()


def test_test_split_locked_until_final(synth_cfg, monkeypatch):
    import yaml
    tmp = synth_cfg()
    cfg_path = tmp / "config.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    cfg["final_eval"] = False
    cfg_path.write_text(yaml.safe_dump(cfg))
    run_pipeline()
    preds = pd.read_parquet(tmp / "processed" / "predictions.parquet")
    assert "test" not in set(preds["split"])
    mvb = pd.read_csv(tmp / "tables" / "03_model_vs_baseline.csv")
    assert (mvb["test"] == "LOCKED").all()
