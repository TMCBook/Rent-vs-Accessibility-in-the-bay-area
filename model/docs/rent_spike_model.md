# Rent-Spike Risk Model and Help-First Ranking

**Datathon for Social Good 2026 · Bay Area Affordability Project · Advanced Track model**

This part of the project builds on Anna's essential-services table and Albert's housing-cost table. It adds a **trained predictive model** that forecasts which Bay Area ZIP codes are about to see the fastest rent increases. It then combines that forecast with access to essentials and the number of renters, to rank **where help would reach the most people at risk**.

Every number below comes from a table written by `python run.py all`. Validation results only: the test year stays locked until the team's final run (`python run.py final`).

---

## The question

> Will this ZIP code's rent growth over the next year be in the **top third** of Bay Area ZIP codes?

- **Unit:** one ZIP code in December of year *t*.
- **Target:** `1` if rent growth from December *t* to December *t*+1 (Zillow Observed Rent Index) ranks in the top third of ZIP codes that year, else `0`.
- **Why rank within each year:** rents fell region-wide in 2020 and jumped in 2021. Ranking within the year means the model has to tell ZIPs apart, not guess the regional trend.

## Data used

| Source | What it adds | Cleaner |
|---|---|---|
| Zillow Observed Rent Index + Home Value Index (Albert, `../housing_costs/data/zillow_research/`) | Rent and home value every December 2015–2025, plus September 2026 | `src/data/clean_zillow_research.py` |
| Essential services by ZIP (Anna, `../essential_services/`) | Access score, distance to grocery, pharmacy, doctor, transit, food bank | `src/data/clean_essentials.py` |
| Indeed Jobs (shared drive) | Postings per city, median posted hourly pay, share of low-wage postings, share listing pay | `src/data/clean_indeed.py` |

## Features (31)

- **Rent and value history, known at December *t*:** rent and value levels, growth over the last 1, 2 and 3 years, growth compared with the region, rent compared with the county, price-to-rent ratio.
- **Neighborhood structure:** access score and distances to essentials (Anna), job postings and local wages (Indeed), number of homes, county.

## Split and model selection

| Split | Years (*t* → *t*+1) | Rows |
|---|---|---|
| Train | 2016–2022 | 606 |
| Validation | 2023 → 2024 | 156 |
| Test (locked) | 2024 → 2025 | 166 |

The split is **by time**, so the model never learns from the future (`tests/test_leakage.py` checks this). The model was chosen by rolling cross-validation on train and validation years only: train on years before *y*, score year *y*, for *y* = 2019 to 2023 (`outputs/tables/09_model_selection_cv.csv`).

| Candidate | Mean AUC | Mean macro-F1 |
|---|---|---|
| Logistic regression, C = 1, all features | 0.635 | 0.552 |
| **Logistic regression, C = 0.1, all features (chosen)** | **0.634** | **0.561** |
| Logistic regression, C = 0.03, all features | 0.619 | 0.584 |
| Gradient boosting, small, all features | 0.599 | 0.509 |
| Logistic regression, rent history only | 0.578 | 0.523 |
| Random forest, all features | 0.574 | 0.529 |
| Gradient boosting, depth 3, all features | 0.559 | 0.513 |
| Persistence rule | 0.439 | 0.465 |

C = 0.1 and C = 1 tie on AUC. C = 0.1 was picked for its higher macro-F1 and stronger regularization on a small dataset. Neighbor-ZIP spillover features were also tried and didn't help, so they were left out.

## Results (validation year, `outputs/tables/03_model_vs_baseline.csv`)

| Model | AUC | Macro-F1 |
|---|---|---|
| **Logistic regression, all features** | **0.560** | **0.524** |
| Same model, rent history only | 0.474 | 0.479 |
| Majority class | 0.500 | 0.405 |
| Persistence ("last year's fastest risers stay fastest") | 0.344 | 0.388 |

**Key findings**

1. **Adding access and jobs data improves the forecast.** Across five validation years, the full model averages AUC 0.634, versus 0.578 with rent history alone.
2. **The signal is modest.** An AUC around 0.6 ranks ZIPs better than chance, but it can't pick out individual ZIPs with confidence.
3. **Persistence fails before 2024.** From 2020 to 2023, ZIPs that rose fastest one year tended to slow down the next. Persistence scores below chance on every fold after 2019.

## Fairness and error analysis

`outputs/tables/04_subgroup_performance.csv`, macro-F1 on the validation year:

| Subgroup | n | Model | Persistence |
|---|---|---|---|
| High access | 76 | 0.530 | 0.408 |
| Mid access | 71 | 0.546 | 0.383 |
| **Low access** | **9** | **0.182** | 0.250 |
| Cheapest third of rents | 51 | 0.531 | 0.542 |
| Middle third | 52 | 0.563 | 0.325 |
| Priciest third | 53 | 0.463 | 0.270 |

- **The model is worst where help matters most.** Only 9 low-access ZIPs have enough rent history to validate on, and the model does poorly on them. Zillow publishes rent indexes mainly for denser areas, so the communities this project cares about are the least represented.
- **In the cheapest third of ZIPs, it is no better than persistence.**
- County results are in the same table. Most counties have fewer than 30 rows and carry a small-sample caution.
- Concrete mispredictions, with blank `note` columns for a teammate to explain, are in `outputs/tables/05_failure_examples.csv`.

## Live check against 2026 (not the test set)

Zillow has published September 2026 rents, so the 2026 forecast can be checked against 9 months of real growth (`outputs/tables/08b_forecast_live_check.csv`):

| | AUC |
|---|---|
| Model's 2026 forecast | 0.153 |
| Persistence | 0.824 |

**The forecast is backwards for 2026.** The model learned the 2020–2023 pattern, when fast risers slowed down. In 2026 the market returned to momentum: fast risers kept rising. This is a **regime shift**, and it's the main limitation of a model trained on post-COVID years. Present it as a finding.

## Help-first ranking (`outputs/tables/08_help_first_ranking.csv`)

```
priority = P(high rent growth in 2026) × (1 − access_score / 100) × renters
```

- **P(high rent growth):** the model's forecast.
- **1 − access score / 100:** how far the ZIP is from essentials (Anna's score).
- **Renters:** rental listings in the ZIP, a stand-in for the number of renter households.
- Only ZIP codes at or below the median December 2025 rent ($3,157) are ranked (87 ZIPs), since that's where low-wage renters live.

Current top 10: Vacaville 95687, Pittsburg 94565, Fairfield 94533, Fremont 94538, Fairfield 94534, Dublin 94568, Napa 94558, Vacaville 95688, Rohnert Park 94928, Alameda 94501.

⚠️ **Don't present this ranking as validated.** The forecast part failed the 2026 live check (above). The access and renter parts are still sound, so the ranking is best read as "low-access, high-renter ZIPs below median rent", with rent risk as an uncertain extra.

## Data decisions and disclosure

All cleaning steps, joins, label rules and hand-check plans are in `docs/data_decisions.md`. That file includes a disclosure: one summary statistic covering the test period was seen during diagnosis. No model change was made after it.

## Still to do (team)

- [ ] Fill in the hand-check sheets in `docs/hand_checks_todo/` (40 parsed salaries, 30 rent-growth labels), then move them to `docs/hand_checks/`.
- [x] Rebuild the access table from raw Places inside `src/data/clean_essentials.py`. Done; it matches Anna's saved table on all 293 ZIPs (`outputs/tables/10_essentials_rebuild_check.csv`).
- [ ] Freeze features, then run `python run.py final` **once** to unlock the test year.
- [ ] Add notes to `outputs/tables/05_failure_examples.csv`.

## How to reproduce

```bash
pip install -r requirements.txt
# put the shared-drive folders in data/raw/ (indeed/indeed_job_listings.csv is the one this model reads)
python run.py all      # data -> features -> split -> select -> train -> predict -> eval -> tables -> figures -> priority
python -m pytest -q tests
```

## Files

| File | What it is |
|---|---|
| `src/features/build_features.py` | ZIP × year table, target, features, subgroups |
| `src/models/select.py` | Rolling cross-validation for model choice → `09_model_selection_cv.csv` |
| `src/models/baseline.py` | Persistence and rent-history-only baselines |
| `src/models/priority.py` | Help-first ranking and 2026 live check → `08_*.csv` |
| `src/data/sample_hand_check.py` | Draws the hand-check samples |
| `config.yaml` | Task, time split, model, baselines, ranking settings |
