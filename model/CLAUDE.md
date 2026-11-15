# CLAUDE.md — 8th Annual Datathon for Social Good (Team Repo)

> **Location note:** this file governs the `model/` folder of the repo. Paths below (`src/`, `data/`,
> `outputs/`, `docs/`, …) are relative to `model/`. Teammates' inputs live beside it in
> `../housing_costs/` (Albert) and `../essential_services/` (Anna); the map demo is `../rent_vs_reach_map/`.

> Read this file at the start of every session. I am **Person 4: the Integrator**. My job is to
> make everyone else's work fit together into one reproducible pipeline, one results table set,
> one slide deck and one submission. When in doubt, optimize for "it runs end-to-end and the
> judges' checklist is visibly satisfied."

## 0. TODO — fill these in from the team plan (marked ⚠️ = not yet confirmed)
- ⚠️ Team name / members / who is Person 1, 2, 3 (and what each owns): `___`
- ⚠️ Chosen social good cause + one-sentence problem statement: `___`
- ⚠️ Track target: Advanced (must meet EVERY checklist item) or Open: `___`
- ⚠️ Datasets chosen (see §2): `___`
- ⚠️ Event start/end, submission deadline, Google Form deadline: `___`
- ⚠️ Shared drive / GitHub repo / Colab or Deepnote link: `___`

## 1. Event facts (from the official Tracks & Guide)
- 2-day event, Bay Area. Each team picks its own social good cause; any datasets, alone or combined.
- **Open Track**: analysis, visualization, dashboards (Tableau fine) and models all welcome.
- **Advanced Track**: only if the project meets **every** item below, else judged in Open Track.
  Judges check the list first, then score technical depth, social good impact, presentation.
  - [ ] **Model**: trained / fine-tuned predictive or NLP model. Descriptive analysis, keyword lists,
        or an off-the-shelf API used as-is do NOT count.
  - [ ] **Baseline**: compare to a simple baseline (majority class, linear regression, published rule).
  - [ ] **Evaluation**: metrics suited to the task (macro-F1, precision/recall, RMSE, AUC…) on a
        **held-out test set never used for training or tuning**.
  - [ ] **Error + fairness analysis**: performance across **≥3 meaningful subgroups**
        (neighborhoods, subreddits, job types, student groups…) AND concrete failure examples.
  - [ ] **Data decisions**: if we create labels, clean heavily, or join datasets — document how and
        **hand-check a sample**.
  - [ ] **Reproducibility**: code runs from raw data to reported results.
- Advanced requires ≥1 provided dataset (external data allowed).
- **Final submission (one teammate submits one Google Form):**
  1. Project link (public GitHub repo, Colab/Deepnote notebook, or deployed site)
  2. Slide deck (Google Slides / PowerPoint): project, methodology, findings, social good impact
  3. Video overview, **max 5 minutes**
- Must explicitly discuss ethics: who could be disadvantaged by this project?

## 2. Datasets (shared drive; each folder has a README with columns, quality notes, ideas)
| Dataset | Size / content | Join keys / notes |
|---|---|---|
| Zillow Housing | ~148k Bay Area listings: price, rent est., features, lat/lon, price history | lat/lon, zip/city |
| Google Maps Places | ~100k Bay Area services: clinics, pharmacies, grocery, food banks, bus stops, schools, banks | `place_id`, lat/lon |
| Google Maps Reviews | ~100k reviews: stars, text, owner responses | `place_id` → Places |
| Indeed Jobs | ~100k Bay Area postings since 2024: title, company, salary (some), description | city, title |
| Glassdoor Reviews | ~100k California reviews since 2025: ratings, pros/cons text | company name |
| Reddit Posts | ~230k posts since 2025, Bay Area/housing/money/work subreddits | subreddit |
| College Affordability | 2 institution-level tables: grad rates, debt, earnings by race/gender, affordability gaps | institution id |
| Health Risk | 1,000 anonymized vitals records labeled Normal/Low/Medium/High | — |

Most data is from Bright Data / The Bright Initiative. Read each folder's README before using it.

## 3. My role as Integrator — responsibilities
1. **Own the repo skeleton, environment, and the "one command" pipeline** (`make all`).
2. **Own the data contract**: agreed column names, dtypes, join keys, geography unit (e.g. zip/tract/city),
   and file formats between teammates. Changes go through me.
3. **Merge teammates' outputs** into final tables: master analytic table, model comparison table
   (model vs baseline), subgroup/fairness table, failure-examples table, data-decisions log.
4. **Enforce the Advanced checklist** — keep `docs/checklist.md` ticked with links to evidence.
5. **Own final deliverables**: README, slide deck assembly, video script/timeline, submission form.
6. Run integration checks on a schedule (see §8), and flag blockers early.

## 4. Repo layout (create if missing; do not reorganize without asking)
```
.
├── CLAUDE.md
├── README.md                # how to reproduce; one-paragraph pitch; results summary
├── Makefile                 # make data | features | train | eval | tables | figures | all
├── environment.yml / requirements.txt
├── config.yaml              # paths, seeds, geography unit, split definition
├── data/
│   ├── raw/                 # READ-ONLY, gitignored (big). Never edit.
│   ├── interim/             # per-person cleaned datasets (parquet)
│   └── processed/           # master tables used by models/figures
├── src/
│   ├── data/                # load_*.py, clean_*.py (one per dataset)
│   ├── features/            # build_features.py, joins.py
│   ├── models/              # baseline.py, train.py, predict.py
│   ├── eval/                # metrics.py, subgroup_eval.py, error_analysis.py
│   └── viz/                 # figures + Tableau-export helpers
├── notebooks/               # EDA only; named NN_owner_topic.ipynb; strip outputs before commit
├── outputs/
│   ├── tables/              # CSVs that go straight into slides
│   ├── figures/             # PNG/SVG for slides
│   └── models/              # saved model + metadata json
├── docs/
│   ├── checklist.md         # Advanced Track checklist + evidence links
│   ├── data_decisions.md    # labels, cleaning, joins, hand-check sample results
│   ├── ethics.md            # who might be harmed, mitigations, limitations
│   ├── slides_outline.md
│   └── video_script.md
└── tests/                   # schema + split-leakage + smoke tests
```

## 5. Integration conventions (apply to ALL code I write or review)
- **Raw data is immutable.** Cleaning writes to `data/interim/` as parquet, never overwrites raw.
- **Each dataset has one `load_*`/`clean_*` module** that outputs a documented schema; schemas live in
  `docs/data_decisions.md` (name, dtype, meaning, null handling).
- **Join keys**: Places↔Reviews on `place_id`. Geographic joins use ONE agreed unit from `config.yaml`;
  log row counts before/after every join and the % unmatched. No silent many-to-many joins.
- **Train/val/test split is defined once** in `src/models/split.py` with a fixed seed, saved to
  `data/processed/split_ids.parquet`. Test set is touched only for final reporting.
  If we group-split (e.g. by place, company, subreddit, institution) to avoid leakage, document why.
- **Seeds fixed** (`config.yaml: seed`), library versions pinned.
- **Every model result must include the baseline** in the same table, same split, same metric.
- **Subgroup eval needs ≥3 named subgroups** with n per group; report small-n caution.
- **Failure examples**: save ≥10 concrete mispredictions per major subgroup to `outputs/tables/`.
- **Any hand-labeled or hand-checked sample** (size, who checked, agreement/accuracy) goes in
  `docs/data_decisions.md`.
- Notebooks are for exploration; anything reported must be reproducible from `src/` + `make`.
- No secrets/API keys in the repo. LLM/API usage (if any) must be wrapped, cached, and not be the
  *only* "model" (an off-the-shelf API as-is doesn't satisfy the Model requirement).
- Commit small, pull/rebase often; I resolve merge conflicts in shared files (Makefile, config, docs).

## 6. Standard output tables I assemble (names are fixed so slides can link to them)
- `outputs/tables/01_dataset_summary.csv` — rows, cols, date range, missingness per dataset used
- `outputs/tables/02_join_audit.csv` — step, left n, right n, matched n, % unmatched
- `outputs/tables/03_model_vs_baseline.csv` — model, metric(s), val, **test**
- `outputs/tables/04_subgroup_performance.csv` — subgroup type, group, n, metrics, gap vs overall
- `outputs/tables/05_failure_examples.csv` — id, subgroup, true, pred, short note
- `outputs/tables/06_hand_check_sample.csv` — sample size, accuracy/agreement, notes
- `outputs/tables/07_key_findings.csv` — finding, number, source figure/table (for the deck)

## 7. How Claude should work with me here
- Be concise; lead with what changed and what I need to do next.
- Before large refactors or anything touching shared files (Makefile, config, schemas), tell me the
  plan and wait. Small fixes: just do them.
- Never edit `data/raw/`. Never commit large data or credentials. Never fabricate numbers —
  every figure/stat in docs or slides must come from a script in this repo.
- Whenever someone's output doesn't match the data contract, say exactly which column/dtype differs
  and propose the minimal fix on *my* side (adapter) before asking them to change theirs.
- When asked "are we ready?", run the checks in §8 and report pass/fail per item.
- Keep `docs/checklist.md` honest: tick an item only with a link to code/table proving it.

## 8. Integration checks (run `make check`)
1. `make all` runs from a clean clone with only `data/raw/` present.
2. Schema tests pass for every `data/interim/*.parquet`.
3. No test-set IDs appear in train/val (leakage test).
4. Baseline present in `03_model_vs_baseline.csv`; metrics are on the test split.
5. ≥3 subgroups in `04_subgroup_performance.csv`; failure examples exist.
6. `docs/data_decisions.md` documents each label/clean/join + hand-check result.
7. README reproduction steps verified by running them.
8. Slides numbers match `07_key_findings.csv`.

## 9. Timeline (fill real clock times once confirmed ⚠️)
- Hour 0–2: lock cause, datasets, geography unit, split, schemas; repo + env working for everyone.
- Hour 2–8: each person's loaders/features/model; I merge daily snapshots into master table.
- Midpoint: first end-to-end run (even with a dumb baseline) — `make all` green.
- Final ~6 hours: freeze features; final test-set eval ONCE; tables/figures; deck; video.
- Final 2 hours: record video (≤5 min), proofread, submit Form, verify links are public.
