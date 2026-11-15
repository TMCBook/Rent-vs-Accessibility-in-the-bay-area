# Advanced Track checklist: evidence links

Each item is ticked only when the linked file proves it. Paths are relative to `model/`.
**Track target: Advanced.**

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | **Model**: trained predictive model (not descriptive, not an API as-is) | [x] | Logistic regression forecasting top-third rent growth per ZIP: `src/models/train.py`, settings in `config.yaml`; chosen over gradient boosting and random forests by rolling cross-validation: `outputs/tables/09_model_selection_cv.csv`, `src/models/select.py` |
| 2 | **Baseline**: simple baselines compared on the same split and metric | [x] | Majority class, persistence rule ("last year's fastest risers stay fastest") and a rent-history-only model: `src/models/baseline.py`, `outputs/tables/03_model_vs_baseline.csv` (role = baseline) |
| 3 | **Evaluation**: task-appropriate metrics on a held-out test set never used for training or tuning | [x] | AUC, macro-F1, precision, recall, accuracy on the test year (Dec 2024 → Dec 2025, 166 ZIPs): `03_model_vs_baseline.csv` `test` column. Time-based split in `src/models/split.py`, leakage checks in `tests/test_leakage.py`, evaluated once on 2026-11-15 (`docs/data_decisions.md` §1, which also discloses one summary statistic seen during diagnosis) |
| 4a | **Fairness**: performance across ≥ 3 meaningful subgroups, with n | [x] | County, access tier and rent tier, with n and small-sample flags: `outputs/tables/04_subgroup_performance.csv`, `outputs/figures/fig_subgroup_*.png`; discussed in `docs/ethics.md` |
| 4b | **Error analysis**: concrete failure examples, with human notes | [ ] | 110 test-year mispredictions listed in `outputs/tables/05_failure_examples.csv`; **`note` column not filled yet** (`python -m src.eval.failure_notes worksheet`, then `apply`) |
| 5 | **Data decisions**: labels, cleaning and joins documented, plus a hand-checked sample | [x] | `docs/data_decisions.md`; joins logged in `outputs/tables/02_join_audit.csv`; hand-checks (39 salaries, 30 labels, both 100% agreement) in `docs/hand_checks/` and `outputs/tables/06_hand_check_sample.csv`; access-table rebuild check in `outputs/tables/10_essentials_rebuild_check.csv` |
| 6 | **Reproducibility**: raw data → reported results with one command | [x] | `python run.py all` (steps in `README.md`), `run.py`, `Makefile`; 13 tests in `tests/`; integration report `outputs/check_report.md` |
| 7 | Uses ≥ 1 provided dataset | [x] | Indeed Jobs, Google Maps Places and Zillow Housing listings: `outputs/tables/01_dataset_summary.csv`, `src/data/clean_indeed.py`, `src/data/clean_essentials.py` |
| 8 | **Ethics**: who could be disadvantaged | [x] | `docs/ethics.md` (coverage gaps, worst subgroups, misuse, privacy, mitigations); add a slide to the deck |

## Submission (one teammate, one Google Form)
- [ ] Project link public (GitHub repo), opened in an incognito window
- [ ] Slide deck: project, methodology, findings, social-good impact
- [ ] Video ≤ 5:00 (check actual runtime)
- [ ] Form submitted before the deadline
