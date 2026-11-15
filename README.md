# Rent vs. Reach: Affordability and Access in the Bay Area

**8th Annual Datathon for Social Good**

Bay Area cooks, aides and clerks are priced out of neighborhoods with good access to essentials. The places they can afford often have the fewest grocery stores, clinics, pharmacies and bus stops, so they pay twice: once in rent, and again in time and travel to reach basic needs. This project measures where affordability and access fail together, forecasts where rent pressure is coming next, and ranks where help would reach the most at-risk renters.

## Key findings

| Finding | Number | Source |
|---|---|---|
| Median asking rent across Bay Area rental listings | $3,108/month | `rent_vs_reach_map/data/summary.json` |
| Median pay in hourly job postings | $25.64/hour | `rent_vs_reach_map/data/summary.json` |
| Share of that worker's income the median rent takes | 70% (30% is the affordability line) | `rent_vs_reach_map/data/summary.json` |
| Rental listings affordable at that wage | 1% (721 homes) | `rent_vs_reach_map/data/summary.json` |
| ZIP codes that are cheaper than the median but underserved | 57 | `rent_vs_reach_map/data/summary.json` |
| Rent-spike forecast, access + jobs data vs. rent history only (rolling CV AUC) | 0.634 vs. 0.578 | `model/outputs/tables/09_model_selection_cv.csv` |

The forecast is modest and failed a 2026 check because the rental market shifted after 2023. See `model/docs/rent_spike_model.md`.

## What's in this repo

| Folder | What it is | Owner |
|---|---|---|
| [`housing_costs/`](housing_costs/) | Typical rent and home value per ZIP from Zillow's indexes, rent trends since 2015, affordability score | Albert |
| [`essential_services/`](essential_services/) | Distance from homes to groceries, pharmacies, doctors, banks, transit and food banks; access score per ZIP | Anna |
| [`rent_vs_reach_map/`](rent_vs_reach_map/) | Interactive map: ZIPs shaded by rent, click for rent burden and access details | ⚠️ TODO name |
| [`model/`](model/) | Rent-spike risk model, baselines, fairness analysis and help-first ranking; the reproducible pipeline | ⚠️ TODO name |

Each folder has its own README or write-up:
- `housing_costs/docs/albert_housing_costs.md`
- `essential_services/docs/anna_essential_services.md`
- `rent_vs_reach_map/README.md`
- `model/README.md` and `model/docs/rent_spike_model.md`

## See the map

Open `rent_vs_reach_map/index.html` in any browser. It works offline.

## Reproduce the model

```bash
cd model
```
```bash
pip install -r requirements.txt
```
Put the shared-drive Indeed, Google Maps Places and Zillow files in `model/data/raw/` (layout in `model/README.md`), then:
```bash
python run.py all
```

## Data

| Dataset | Used for | In this repo? |
|---|---|---|
| Zillow Housing listings (shared drive) | Rent, map, access distances | No, too large |
| Google Maps Places (shared drive) | Essential services | No, too large |
| Google Maps Reviews (shared drive) | Service quality on the map | No, too large |
| Indeed Jobs (shared drive) | Wages, low-wage job share | No, too large |
| Zillow Observed Rent Index, Home Value Index (public) | Rent history for the model | Yes, Bay Area rows in `housing_costs/data/` |
| Census 2010 ZIP code shapes (public) | Map outlines | Simplified, inside the map's data |

Most provided data is from Bright Data through The Bright Initiative.

## Ethics

Results are reported by ZIP code only: no addresses, listings or reviewer names. Low access isn't the same as hardship (some low-access ZIPs are wealthy suburbs), and the model is least accurate in low-access ZIPs, where rent data is thinnest. See `model/docs/ethics.md` ⚠️ TODO.

## Links

- Slide deck: ⚠️ TODO
- Video (≤ 5 min): ⚠️ TODO
