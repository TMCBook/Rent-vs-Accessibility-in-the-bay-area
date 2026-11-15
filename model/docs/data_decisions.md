# Data decisions log

Every label we create, heavy cleaning step, and join goes here, with row counts and a
hand-checked sample. `run.py check` fails while any TODO marker remains in this file.

## 1. Geography unit and split
- Geography unit (`config.yaml: geography_unit`): **zip**. Zillow's rent/value indexes, Anna's
  essential-services table and Albert's housing table are all published per ZIP; job postings are
  attached through the ZIP's city.
- Prediction unit: **one ZIP in December of year t** (`id = <zipcode>_<t>`). The model predicts
  whether that ZIP's rent growth from Dec t to Dec t+1 is in the top third of Bay Area ZIPs.
- Split: **time-based**, not random (`config.yaml: split.time_col`), because this is a forecast and
  a random split would let the model learn from later years. Train t ≤ 2022 (606 rows), validation
  t = 2023 (156), test t = 2024, i.e. Dec 2024 → Dec 2025 growth (166). `tests/test_leakage.py`
  checks that no training row comes from the validation/test period.
- Model selection used rolling-origin CV on train+val years only (`src/models/select.py`,
  `outputs/tables/09_model_selection_cv.csv`): fit on years < y, score y, for y = 2019…2023.
- Test set touched once, at final eval (`run.py final`), after features froze at **2026-11-15 18:00 UTC**.
  `config.yaml: final_eval` is now `true`, so later runs re-report the same test results; features
  and model settings must not change from here.
- **Disclosure (test-period exposure):** while diagnosing the live check (section 7), a summary
  statistic over all years was printed: the Spearman correlation between a ZIP's growth in one year
  and the next. One of its rows covered the test period (2024 → 2025: +0.12). No model, feature or
  parameter was changed after it was seen. A "no momentum features" variant was tested
  afterwards, scored on train/val years only, and **rejected** by the pre-set rule (best mean CV AUC:
  0.572 vs 0.634). The model in `config.yaml` is the one chosen before the exposure.

## 2. Schemas (data contract — mirrors `src/data/schemas.py`)
### zillow_research — owner: Albert (source data), adapter by Integrator
| column | dtype | meaning | null handling |
|---|---|---|---|
| zipcode | string | 5-digit ZIP | never null |
| zillow_city, county | string | Zillow's city name; county without " County" | county never null |
| month, year | datetime, int | Dec of each year 2015–2025; Sep 2026 for year 2026 | never null |
| rent | float | Zillow Observed Rent Index (ZORI), $/month | null where Zillow publishes none |
| value | float | Zillow Home Value Index (ZHVI), $ | null where Zillow publishes none |
| is_partial_year | bool | True for the Sep 2026 row | never null |

### essentials — owner: Anna (method), rebuilt from raw by Integrator
`src/data/clean_essentials.py` is a port of Anna's notebook (cells 4–31): same category lists,
filters and formulas, run on raw Places + Zillow listings. One row per ZIP (293). Columns as in
`../essential_services/docs/anna_essential_services.md`:
`access_score` (0–100, relative), `dist_*_mi` (median home's miles to nearest service),
`count_*_1mi`, `bank_to_checkcash_ratio`, `n_homes`, `low_data`, `median_rent`, `n_rentals`
(null → 0).

### indeed — owner: Integrator
| column | dtype | meaning | null handling |
|---|---|---|---|
| jobid | string | Indeed posting id | |
| city, zipcode | string | parsed from `location` ("…, City, CA 94105") | zipcode null when not given |
| job_title | string | | |
| has_pay | bool | `salary_formatted` present | never null |
| hourly_pay | float | pay normalized to $/hour (rules in `src/data/clean_indeed.py`) | null if unparsed or outside $10–500 |
| pay_unit | string | hour / year / month / week / day | null if unparsed |
| date_posted | datetime | | |

## 3. Cleaning steps
| dataset | step | rows before | rows after | reason |
|---|---|---|---|---|
| zillow_research | drop ZIP-months with neither rent nor value | 3,300 | 3,269 | outer join of ZORI and ZHVI |
| essentials (places) | drop permanently closed | 147,429 | 135,262 | closed places aren't access |
| essentials (homes) | Zillow listings with coordinates + ZIP, deduped on zpid, 9 Bay Area counties | 149,005 | 147,395 | distances are measured from homes |
| essentials (places) | in a service bucket and within 3 miles of a home | 58,091 | 55,439 | drop places outside the Bay Area |
| indeed | location parses as "City, CA" | 140,816 | 138,895 | need a city to attach to ZIPs |
| indeed | city or ZIP in the 9 Bay Area counties | 138,895 | 47,564 | file covers all of California |
| indeed | dedupe title + company + location | 47,564 | 45,877 | reposts (dataset README) |
| master | drop ZIP-years without current rent and last year's growth, and `low_data` ZIPs | 2,994 | 928 (+173 forecast rows) | need history to forecast |

## 4. Joins
See `outputs/tables/02_join_audit.csv`.
- **Indeed → ZIP via city: 9.6% of ZIPs unmatched** (28 of 293): small places with no postings
  under their city name. Their job features are null (imputed by the model); `log_jobs_n` = 0.
- Zillow Research → essentials: 0% unmatched.
- **Who is lost before the join:** Zillow publishes a rent index for only 210 ZIPs, and coverage
  grows over time (9 ZIPs in 2015 → 182 in 2025). Rural and small ZIPs are under-represented,
  especially in early years.

## 5. Labels we created
- **Target:** `target = 1` if `next_rent_growth` (ZORI Dec t+1 ÷ Dec t − 1) ranks in the top third
  of all ZIPs with data in that year (`rank(pct=True) > 2/3`), else 0. Ranking within year removes
  region-wide shocks (2020: median −3.2%; 2021: +6.5%). Positive rate 33.1%.
- **Known label noise / bias:**
  - ZORI is smoothed and built from listed rents, so it tracks what movers pay, not sitting tenants.
  - Near the one-third cut, ZIPs with almost the same growth get different labels.
  - **Regime instability:** whether growth persists flips sign across years (≈ +0.1 before 2020,
    −0.13 to −0.27 in 2020–2023). A model trained mostly on post-COVID years learns mean reversion.
- **Static context assumption:** access (Places, scraped 2026) and job postings (2024–2026) are
  used for every year as slow-moving neighborhood structure. This is not time-respecting. Treat
  them as "what kind of neighborhood this is", not as information available in 2017.

## 6. Hand-checked samples
Samples were drawn by `python -m src.data.sample_hand_check` (seed 42) with `checked_value` blank,
filled in by hand, and saved in `docs/hand_checks/`. Agreement is computed by `run.py tables` into
`outputs/tables/06_hand_check_sample.csv` (numbers agree within 0.01; rows marked N/A are counted as
not checked and left out of the rate).

| check | sample size | sampled how | checked by | agreement | what we changed after |
|---|---|---|---|---|---|
| Indeed pay → hourly | 40 (39 checked) | random postings with pay, seed 42 | Jason Shorey | 100% (39/39) | Nothing. One row ("$60 per class") has no hourly equivalent; the code leaves it unparsed and the checker marked it N/A |
| Rent-growth label | 30 | random train/val ZIP-years, seed 42 (no test rows); checker computed growth from the two December ZORI rents and compared it with that year's top-third cutoff | Jason Shorey | 100% (30/30) | Nothing |
| ZORI vs listing rents (Albert) | 205 ZIPs | all ZIPs with 10+ listings | Albert | r = 0.81 | used ZORI as rent source |
| Rebuilt access table vs Anna's saved table (automated, not a hand-check) | 293 ZIPs × 20 columns | every ZIP | `src/data/clean_essentials.py` | 100% identical (`outputs/tables/10_essentials_rebuild_check.csv`) | pipeline now rebuilds from raw instead of reading her CSV |

## 7. Live check (not the test set)
`src/models/priority.py` compares the 2026 forecast with Zillow's Sep 2026 rents
(`outputs/tables/08b_forecast_live_check.csv`). It is a partial year (9 months), so it is reported
separately and never used for model choice.
