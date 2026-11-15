# Rent-Spike Risk Model

Forecasts which Bay Area ZIP codes will see the fastest rent increases next year, then ranks where help would reach the most at-risk renters. This folder is the model's code and results. It reads Albert's and Anna's tables from the neighboring folders `../housing_costs/` and `../essential_services/`.

Full write-up with every result: **`docs/rent_spike_model.md`**. Cleaning, joins, labels and disclosures: **`docs/data_decisions.md`**.

## Run it

All commands run from inside `model/`.

```bash
cd model
```
```bash
pip install -r requirements.txt
```
Put the shared-drive files in `data/raw/` like this, or point to a folder laid out the same way:
```
data/raw/indeed/indeed_job_listings.csv     (Indeed Jobs)
data/raw/places/google_maps.csv             (Google Maps Places)
data/raw/zillow/*.csv                       (Zillow Housing: all parts)
```
```bash
export DATATHON_RAW_DIR=/path/to/shared-drive-folders
```
```bash
python run.py all
```
```bash
python -m pytest -q tests
```
`run.py all` takes about 3 minutes (most of it reading the Zillow files) and rewrites everything in `outputs/`. The test year stays locked until `python run.py final`, which the team runs **once** at the end.

## How it works, step by step

Each step is one command in `run.py`; `all` runs them in order.

| Step | Code | What happens |
|---|---|---|
| 1. `data` | `src/data/clean_zillow_research.py` | Reads Zillow's rent index (ZORI) and home value index (ZHVI) per ZIP: every December 2015–2025, plus September 2026 |
| | `src/data/clean_essentials.py` | Rebuilds Anna's access table from raw Places + Zillow listings with her exact method: distance to grocery, pharmacy, doctor, transit, food bank per ZIP and the access score. Checks the result against her saved table → `10_essentials_rebuild_check.csv` |
| | `src/data/clean_indeed.py` | Reads Indeed postings, keeps Bay Area ones, removes reposts, converts salary text to an hourly rate |
| | `src/data/schemas.py`, `validate.py` | Checks each cleaned table has the agreed columns and types |
| 2. `features` | `src/features/build_features.py` | Builds one row per **ZIP × year**. Features use only what was known that December: rent and value levels, growth over the last 1–3 years, rent vs. county, price-to-rent, plus access and jobs. **Label:** 1 if next year's rent growth is in the top third of ZIPs that year |
| | `src/features/joins.py` | Every join is logged to `outputs/tables/02_join_audit.csv` |
| 3. `split` | `src/models/split.py` | Splits **by time**: train on 2016–2022, validate on 2023 → 2024, test on 2024 → 2025 (locked) |
| 4. `select` | `src/models/select.py` | Compares 8 candidate models by rolling cross-validation on train and validation years only → `09_model_selection_cv.csv` |
| 5. `train` | `src/models/train.py`, `baseline.py` | Fits the chosen model (logistic regression, C = 0.1, balanced classes) and three baselines: majority class, persistence ("last year's fastest risers stay fastest"), and the same model on rent history only |
| 6. `predict` | `src/models/predict.py` | Predicts the validation year (and the test year only in `final`) |
| 7. `eval` | `src/eval/*.py` | Model vs. baselines (`03`), results by county / access tier / rent tier (`04`), worst mispredictions (`05`) |
| 8. `tables`, `figures` | `src/eval/make_tables.py`, `src/viz/figures.py` | Hand-check summary (`06`), key findings (`07`), charts in `outputs/figures/` |
| 9. `priority` | `src/models/priority.py` | Scores every ZIP for 2026 and ranks where to help first → `08_help_first_ranking.csv`. Checks the 2026 forecast against Zillow's September 2026 rents → `08b_forecast_live_check.csv` |

**Help-first score:**

```
priority = P(rent spike next year) × (1 − access_score / 100) × renters
```
Only ZIPs at or below median rent are ranked, since that's where low-wage renters live.

## Results so far (validation year)

| Model | AUC |
|---|---|
| Logistic regression, all features | 0.560 |
| Same model, rent history only | 0.474 |
| Majority class | 0.500 |
| Persistence | 0.344 |

- Access and jobs data improve the forecast (rolling CV: AUC 0.634 vs. 0.578 with rent history only).
- **The 2026 live check failed (AUC 0.153):** the model learned the 2020–2023 pattern of fast risers cooling off, and in 2026 they kept rising. Don't present the ranking as validated.
- The model is weakest in low-access ZIPs (9 in validation), where Zillow has little rent data.

## Inputs

| File | From |
|---|---|
| `../housing_costs/data/zillow_research/zori_bay_area.csv`, `zhvi_bay_area.csv` | Albert (Zillow Research public downloads) |
| `data/raw/places/google_maps.csv`, `data/raw/zillow/*.csv` | Shared drive: Google Maps Places, Zillow Housing (**not included**, ~8 GB). Used to rebuild Anna's access table |
| `../essential_services/outputs/tables/anna_essentials_by_zip.csv` | Anna's saved table, used only to check the rebuild |
| `data/raw/indeed/indeed_job_listings.csv` | Shared drive: Indeed Jobs (**not included**, 2.1 GB) |

## Adding to the pipeline
1. **Cleaner**: copy `src/data/clean_TEMPLATE.py` to `clean_<name>.py`, add `<name>` to
   `config.yaml: datasets`, and ask the Integrator to add its schema to `src/data/schemas.py`.
2. **Features**: implement `build()` in `src/features/build_features.py`; use
   `src.features.joins.audited_merge` for every join.
3. **Task**: set `task.*` (target, id, subgroup columns) and `split.group_col` in `config.yaml`.
4. **Hand checks**: drop `docs/hand_checks/<name>.csv` (`item_id, auto_value, checked_value, checker`).
5. Notebooks go in `notebooks/NN_owner_topic.ipynb`, outputs stripped. Reported numbers must come from `run.py`.


## Still to do

- [ ] Fill in the hand-check sheets in `docs/hand_checks_todo/` and move them to `docs/hand_checks/`.
- [x] Rebuild Anna's access table from raw Places inside `src/data/clean_essentials.py` (matches her table exactly: `10_essentials_rebuild_check.csv`).
- [ ] Freeze features, then run `python run.py final` once.
- [ ] Add notes to `outputs/tables/05_failure_examples.csv`.
