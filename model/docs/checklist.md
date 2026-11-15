# Advanced Track checklist — evidence links

Tick an item ONLY when the linked file proves it. Judges read this list first.
Track target: ⚠️ TODO(team) Advanced / Open

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | **Model**: trained/fine-tuned predictive or NLP model (not descriptive, not an API as-is) | [ ] | `src/models/train.py`, `outputs/models/<model>.json` |
| 2 | **Baseline**: simple baseline compared on same split + metric | [ ] | `outputs/tables/03_model_vs_baseline.csv` (role = baseline) |
| 3 | **Evaluation**: task-appropriate metrics on a held-out test set never used for training/tuning | [ ] | `src/models/split.py`, `data/processed/split_ids.parquet`, `tests/test_leakage.py`, `03_…csv` test column |
| 4a | **Fairness**: performance across ≥3 meaningful subgroups (with n) | [ ] | `outputs/tables/04_subgroup_performance.csv`, `outputs/figures/fig_subgroup_*.png` |
| 4b | **Error analysis**: concrete failure examples, with human notes | [ ] | `outputs/tables/05_failure_examples.csv` (`note` column filled) |
| 5 | **Data decisions**: labels / cleaning / joins documented + hand-checked sample | [ ] | `docs/data_decisions.md`, `02_join_audit.csv`, `06_hand_check_sample.csv` |
| 6 | **Reproducibility**: raw data → reported results with one command | [ ] | `README.md`, `run.py` / `Makefile`, `outputs/check_report.md` |
| 7 | Uses ≥1 provided dataset | [ ] | `outputs/tables/01_dataset_summary.csv` |
| 8 | Ethics: who could be disadvantaged | [ ] | `docs/ethics.md`, deck slide 10 |

## Submission (one teammate, one Google Form)
- [ ] Project link public (GitHub / Colab / Deepnote / site) — opened in an incognito window
- [ ] Slide deck: project, methodology, findings, social-good impact
- [ ] Video ≤ 5:00 (check actual runtime)
- [ ] Form submitted before deadline ⚠️ TODO time
