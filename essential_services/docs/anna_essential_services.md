# Essential Services Access: Anna (Person 3)

**Datathon for Social Good 2026 · Bay Area Affordability Project**

This part of the project measures how easy it is for people in each Bay Area zip code to reach everyday essentials (groceries, pharmacies, doctors, banks and transit) and combines that with rent to find communities that are **affordable but cut off**.

**Main output for the team:** `outputs/tables/anna_essentials_by_zip.csv`, one row per zip code with distances, counts, an access score (0–100) and rent.

---

## Key findings

1. **Food banks are the hardest essential to reach.** The typical Bay Area home is **1.08 miles** from the nearest food bank, about twice as far as any other service. Only **47%** of homes have a food bank within 1 mile, and **26%** are more than 2 miles away.
2. **Dense cities have essentials within a short walk.** Downtown San Francisco, Oakland and Berkeley score 94–98, with groceries, pharmacies and doctors about 0.05–0.25 miles away.
3. **Rural Napa, Sonoma and coastal areas are the least accessible.** For example, the nearest pharmacy is about 24 miles from the typical home in The Sea Ranch, and the nearest grocery store is about 9 miles from Pope Valley.
4. **Among denser zip codes, the lowest access is in car-oriented suburbs**, often wealthy ones (Danville, Lafayette, San Ramon, Walnut Creek). Access alone does not mean hardship, which is why it has to be combined with affordability.
5. **50 zip codes are "affordable but cut off":** below-median rent per bedroom and bottom-third access. Examples include **Vallejo (94589, 94591), Oakley (94561), Cloverdale (95425)** and several Solano County zip codes (Vacaville, Fairfield, Suisun City).
6. **Check-cashing and money-transfer shops outnumber banks** in some neighborhoods, notably **94110 San Francisco (Mission), 94601 Oakland (Fruitvale) and 95116 San Jose (East San Jose)**.

### Distance to each service (Bay Area homes)

| Service | Places in Bay Area | Median miles to nearest | % of homes within 1 mile | % of homes over 2 miles away |
|---|---|---|---|---|
| Bus or transit stop | 20,768 | 0.12 | 96.20 | 1.55 |
| Primary care doctor | 27,595 | 0.23 | 94.99 | 1.78 |
| Grocery store | 2,204 | 0.33 | 90.68 | 2.52 |
| Bank or credit union | 1,668 | 0.45 | 83.56 | 3.83 |
| Check cashing / money transfer | 1,725 | 0.46 | 84.35 | 4.41 |
| Pharmacy | 1,110 | 0.49 | 82.93 | 4.01 |
| Food bank | 369 | 1.08 | 47.09 | 25.85 |

---

## What I did

| Step | What it does |
|---|---|
| 1. Load Places | Loaded Google Maps Places (`google_maps.csv`, 147,429 places). |
| 2. Keep open places | Removed places marked `permanently_closed`. |
| 3. List categories | Found 394 distinct categories. |
| 4. Sort into buckets | Grouped the relevant categories into 7 service types using **exact category names** (see table below). Everything else is ignored. |
| 5. Hand-check | Reviewed a random sample of 10 places per bucket to confirm the sorting. |
| 6. Load homes | Loaded home locations from all 3 Zillow files (`Zillow_part1.csv`, `zillow_part2.csv`, `zillow_part3.csv`) and **kept only the 9 Bay Area counties**. |
| 7. Measure distances | For every home, found the distance to the nearest place in each bucket and the count within 1 mile (`sklearn` `BallTree`, haversine distance). Places more than 3 miles from any home were dropped as outside the Bay Area. |
| 8. Summarize by zip | Took the **median home** in each zip code → 293 zip codes. |
| 9. Access score | Ranked zip codes on distance to 5 everyday services and averaged the ranks into a 0–100 score (method below). |
| 10. Add rent | Added median rent and rent per bedroom from Zillow `FOR_RENT` listings. |

### Places per bucket (all of Google Maps Places, before the Bay Area filter)

| Bucket | Places |
|---|---|
| primary_care | 28,779 |
| transit | 21,845 |
| grocery | 2,324 |
| check_cashing | 1,836 |
| bank | 1,724 |
| pharmacy | 1,168 |
| food_bank | 415 |
| not used (other categories) | 77,171 |

### Zillow homes kept per county (after the Bay Area filter)

| County | Homes |
|---|---|
| Santa Clara | 38,424 |
| Alameda | 34,487 |
| Contra Costa | 19,403 |
| San Francisco | 15,608 |
| San Mateo | 13,630 |
| Sonoma | 10,150 |
| Solano | 8,410 |
| Marin | 4,438 |
| Napa | 2,845 |

### Service buckets

| Bucket | Google Maps categories included |
|---|---|
| `grocery` | Grocery store, Supermarket, Asian grocery store, Indian grocery store, Produce market |
| `food_bank` | Food bank |
| `pharmacy` | Pharmacy |
| `primary_care` | Doctor, Medical clinic, Internist, Pediatrician, Family practice physician, Clinic, Community health center, Urgent care center, Women's health clinic, Medical Center, Hospital |
| `bank` | Bank, Credit union |
| `check_cashing` | Money transfer service, Check cashing service, Pawn shop |
| `transit` | Bus stop, Transit station, Transport hub |

### How the access score works

1. For each zip code, take the median home's distance to the nearest **grocery store, pharmacy, primary care doctor, bank and transit stop**.
2. For each of these 5 services, rank all zip codes from closest (≈1) to farthest (≈0) as a percentile.
3. Average the 5 percentiles (equal weights) and multiply by 100.

```python
ranks = pd.concat([1 - by_zip[c].rank(pct=True) for c in access_parts], axis=1)
by_zip["access_score"] = (ranks.mean(axis=1) * 100).round(1)
```

**The score is relative.** 30 means "worse access than most Bay Area zip codes," not a fixed distance. Food banks and check cashing are not part of the score; they're kept as separate measures.

---

## Data decisions (for the Advanced Track checklist)

- **Zillow covered all of California, not just the Bay Area.** The Zillow files include homes from Los Angeles, San Diego and elsewhere, despite what the README says. We kept only Alameda, Contra Costa, Marin, Napa, San Francisco, San Mateo, Santa Clara, Solano and Sonoma counties. This reduced the zip codes from 803 to 293. **Persons 1 and 2 must apply the same filter.**
- **Exact category lists, not keywords.** A first keyword approach matched "atm" inside "treatment", which would have counted addiction treatment centers as banks. Exact names avoid this.
- **Primary care excludes specialists** (surgeons, oncologists, cardiologists, etc.), since everyday access means a regular doctor.
- **"Money transfer service" is counted with check cashing** (about 1,764 of 1,836 places in that bucket). These shops often cash checks too, but many mainly serve people sending money abroad, so present this as "check-cashing and money-transfer shops."
- **Convenience stores are not counted as grocery stores.**
- **Distances are measured from homes**, not zip code centers, so they reflect where people actually live.
- **Zip codes with fewer than 20 homes are flagged** (`low_data = True`) and left out of the findings and charts.
- **Rent per bedroom** is used for the "affordable" test, so studios and in-law units in wealthy areas don't look cheaper than they are.

---

## Potential biases

- **Median listing rent can make wealthy areas look affordable.** Using plain median rent, Orinda, Moraga, San Ramon, Walnut Creek and Berkeley 94708 (the Berkeley hills) appeared as "affordable but cut off." They're wealthy areas; their rental listings just happen to be smaller units, like apartments and in-law units, while homes there are expensive. Switching to rent per bedroom reduces this, but listing rent is still an imperfect measure of how affordable a neighborhood is. Census median household income would be better.
- **Low access is not the same as hardship.** Many low-access zip codes are rural or car-oriented wealthy suburbs, where residents can easily drive. Access matters most combined with low income or no car.
- **Google Maps coverage may be uneven.** Small or informal businesses (corner produce stands, community pantries) may be missing, which would make some neighborhoods look worse than they are.
- **Rental listings are a sample.** They reflect what's on the market now, not what current residents pay.

---

## Files in this repo

| File | What it is |
|---|---|
| `outputs/tables/anna_essentials_by_zip.csv` | Main result: 293 zip codes (255 with `low_data == False`) |
| `outputs/tables/anna_service_summary.csv` | Distance-to-service summary table (above) |
| `outputs/figures/anna_*.png` | The 4 charts described below |
| `notebooks/03_anna_essential_services.ipynb` | Code that produces all of the above |

`places_clean.csv` (16 MB, the cleaned list of places) is not committed because of its size. Rerun the notebook to recreate it, or get it from the `datathon_outputs` Google Drive folder.

### `anna_essentials_by_zip.csv`: main result (293 rows, one per zip code)

| Column | Meaning |
|---|---|
| `zipcode` | 5-digit zip code. **Read as text** (`dtype={"zipcode": str}`) |
| `dist_<service>_mi` | Miles from the median home to the nearest place of that type. Services: `grocery`, `food_bank`, `pharmacy`, `primary_care`, `bank`, `check_cashing`, `transit` |
| `count_<service>_1mi` | Number of places of that type within 1 mile of the median home |
| `n_homes` | Number of Zillow homes in the zip code |
| `city`, `county` | Most common city and county among those homes |
| `low_data` | `True` if fewer than 20 homes; treat these numbers as unreliable |
| `access_score` | 0–100, higher = closer to everyday essentials (method above) |
| `bank_to_checkcash_ratio` | Banks within 1 mile ÷ (check-cashing shops within 1 mile + 1). Low = fewer banks relative to check cashing |
| `median_rent` | Median monthly rent of Zillow `FOR_RENT` listings ($300–$30,000 kept) |
| `n_rentals` | Number of rental listings behind `median_rent` |
| `rent_per_bedroom` | Median monthly rent ÷ bedrooms |

### `places_clean.csv` (Google Drive only): cleaned list of places

Every place used in the analysis: name, category, bucket, latitude/longitude, rating and the zip code of the nearest home. Person 5 can use it to show service locations as dots on the map.

### Charts

| File | What it shows | How to read it |
|---|---|---|
| `anna_distance_by_service.png` | Median distance from a home to the nearest of each of the 7 services | Food banks (1.08 mi) stand out as farthest; transit (0.12 mi) and doctors (0.23 mi) are closest |
| `anna_access_score_ranking.png` | The 10 most (blue) and 10 least (orange) accessible zip codes | Mostly downtown vs. rural. Useful context, not the main story |
| `anna_banks_vs_checkcashing.png` | Each dot is a zip code: banks within 1 mile (x) vs. check-cashing / money-transfer shops within 1 mile (y) | Dots above the dashed line have more check-cashing shops than banks. Labeled: 94110 SF, 94601 Oakland, 95116 San Jose |
| `anna_affordable_but_cut_off.png` | Each dot is a zip code: rent per bedroom (x) vs. access score (y). Orange = affordable but cut off | Bottom-left corner = cheaper rent and worse access. **Main finding**: 50 zip codes, labeled Vallejo 94589, Cloverdale 95425, Oakley 94561, Discovery Bay 94505 |

---

## Notes for Person 4

- **Join on `zipcode` as text** so leading zeros and types match across files.
- **Filter `low_data == False`** before using results in findings or the fairness analysis.
- **`access_score` is ready to use** as the "essentials access" sub-score (already 0–100, higher = better).
- **There is no cost score yet.** County-level costs from the MIT Living Wage Calculator were not added.
- **Known data issues:**
    - A few `low_data` rows carry wrong county labels from Zillow. For example, 93463 (Solvang) and 96045 (Horse Creek) are labeled San Mateo County. They're excluded once you filter `low_data == False`.
    - 95377 (Tracy) and 95391 (Mountain House) are labeled Alameda County but are mostly in San Joaquin County; both are `low_data`.
- **Limitations to mention in the slides:**
    - Distance to a bus stop doesn't say how often the bus comes.
    - The score uses equal weights for the 5 services; other weightings are possible.
    - Rent comes from listings, not from what current residents actually pay. Census median household income would be a stronger affordability measure.
    - Results are shown at zip code level only, never individual addresses.
