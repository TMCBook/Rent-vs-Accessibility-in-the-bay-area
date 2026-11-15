# Housing Costs by Zip Code: Albert

**Datathon for Social Good 2026 · Bay Area Affordability Project**

This part of the project measures **what it costs to live in each Bay Area zip code**: the typical monthly rent and the typical home value. It's built to sit beside Anna's essential-services table: same 293 zip codes, same `n_homes` and `low_data` flags, joined one-to-one on `zipcode`, ready for the map.

**Main output for the team:** `outputs/tables/albert_housing_by_zip.csv`, one row per zip code with typical rent, typical home value, change since 2019, price-to-rent ratio, income needed to afford the rent, and an affordability score (0–100).

---

## Key findings

All figures are Zillow's indexes for **September 2026**, for the 255 zip codes that are not `low_data` in Anna's table. "Median zip code" is the middle zip code, not the middle home.

1. **The typical Bay Area zip code rents for $3,422 a month and its typical home is worth $1.21 million.** Rents range from **$2,055 in Vallejo (94590) to $8,082 in Los Altos (94024)**, and home values from **$437,781 in Pope Valley (94567) to $8.73 million in Atherton (94027)**.
2. **Renting the typical home in the median zip code takes about $136,900 a year in income** to stay within the usual 30%-of-income guideline. In San Francisco County's median zip code it takes **$190,000**; even in Solano County, the cheapest, it takes **$102,100**.
3. **The cheapest places to rent and buy are in Solano County, west Contra Costa and east Oakland.** The 10 most affordable zip codes (by affordability score) are Vallejo (94590, 94589, 94591), Richmond (94801, 94806), Oakland (94621, 94601), Fairfield (94533), Antioch (94509) and Pittsburg (94565).
4. **Rents in the median zip code are up 26.6% since December 2019** (119 zip codes with 2019 data), and **3.5% during 2025**. San Francisco rose the most: its median zip code is up 43%, led by the Marina (94123, +61.5%) and the Sunset (94116, +55.5%).
5. **Home values mostly fell in 2025**: 194 of 252 zip codes lost value between December 2024 and December 2025, with the biggest drops in Oakland (94612, −12.4%; 94607, −12.1%) and Emeryville (94608, −11.8%). Over the longer run they're still up 25.7% since 2019 in the median zip code.
6. **Buying costs 29 years of rent in the median zip code**, but over 70 years in Palo Alto (94301, 85.7), Los Gatos (95030, 76.1) and Burlingame/Hillsborough (94010, 70.8), and about 14–15 years in downtown Oakland (94612), downtown San Jose (95113) and SoMa (94103).
7. **Zillow's rent index and the datathon listings agree** (correlation 0.81 across 205 zip codes with 10+ listings). Zillow's index runs about 10% higher in the median zip code, and 77% of zip codes are within ±20%.

### By county (median zip code)

| County | Typical rent | Income needed for rent | Typical home value | Rent change since Dec 2019 |
|---|---|---|---|---|
| San Francisco | $4,751 | $190,000 | $1,406,332 | +43.0% |
| Marin | $4,235 | $169,400 | $1,500,236 | +35.3% |
| San Mateo | $3,936 | $157,400 | $1,585,013 | +26.0% |
| Santa Clara | $3,906 | $156,250 | $1,540,698 | +26.9% |
| Contra Costa | $3,016 | $120,600 | $772,049 | +26.8% |
| Napa | $2,907 | $116,250 | $898,943 | +27.7% |
| Alameda | $2,879 | $115,200 | $1,147,274 | +18.2% |
| Sonoma | $2,850 | $114,000 | $800,248 | +27.3% |
| Solano | $2,553 | $102,100 | $579,505 | +28.1% |

---

## Where the numbers come from

| Measure | Source | What it is |
|---|---|---|
| `typical_rent` | **Zillow Observed Rent Index (ZORI)**, all homes, smoothed | Zillow's typical monthly rent for the zip code, weighted to the whole rental stock rather than whatever is listed this month |
| `typical_home_value` | **Zillow Home Value Index (ZHVI)**, single-family + condo, middle tier, smoothed, seasonally adjusted | Zillow's typical home value: homes in the middle third (33rd to 67th percentile) of value |
| `listing_median_rent` | **Datathon Zillow listings** (via Anna's table) | Median asking rent of `FOR_RENT` listings in the provided dataset |

Both indexes are free public downloads from Zillow Research ([zillow.com/research/data](https://www.zillow.com/research/data/)).

### Why not the datathon's Zillow files directly?

The plan was to compute medians straight from the datathon's Zillow listing files (`04b_albert_listing_costs.ipynb` does exactly that). On Nov 14, Google Drive blocked downloads of all three files ("too many users have viewed or downloaded this file recently"), so they couldn't be read. Zillow's own indexes come from the same company's data, are built to measure "typical" rent and value per zip code, and are smoothed so one unusual listing can't swing a zip code. The datathon listings are still used as an independent check (finding 7), and `04b` can be run if the files become readable.

---

## What I did

| Step | What it does |
|---|---|
| 1. Load Zillow's indexes | Read ZORI and ZHVI for all US zip codes (or the saved Bay Area copies in `data/zillow_research/` when Zillow can't be reached); kept California zip codes in the 9 Bay Area counties: **210 zip codes with rent, 274 with home value**. Kept each December from 2015 and the latest month (September 2026). |
| 2. Line up with Anna | Started from Anna's 293 zip codes and joined Zillow's values on `zipcode`. Every zip code in Zillow's indexes is in Anna's table. |
| 3. Derived measures | Change during 2025 and since December 2019; price-to-rent ratio; income needed for rent at 30%. |
| 4. Affordability score | Ranked zip codes on rent and home value and averaged the ranks into a 0–100 score (method below). |
| 5. Hand-check | Compared Zillow's rent index with the datathon listing rents for every zip code with 10+ listings. |
| 6. County summary, charts, combined table | `albert_housing_by_county.csv`, 5 charts, and `housing_plus_essentials_by_zip.csv` (housing + Anna's access columns). |

### How the affordability score works

Same method as Anna's access score, so the two are on one scale.

1. Use zip codes with both a typical rent and a typical home value that aren't `low_data` (209 zip codes).
2. Rank them from cheapest (≈1) to most expensive (≈0) as a percentile on rent and on home value.
3. Average the two (equal weights) and multiply by 100.

**The score is relative**: 80 means "cheaper than most Bay Area zip codes", not affordable for a given income. `income_needed_for_rent` is the absolute measure.

---

## Data decisions (for the Advanced Track checklist)

- **Source switch (above):** Zillow Research indexes instead of medians of the datathon listings, because Drive blocked the listing files. Documented here and in the notebook's first cell.
- **Hand-check:** the two rent measures were compared for all 205 zip codes with 10+ listings (chart `albert_rent_check.png`, notebook section 6). Correlation 0.81; Zillow's index is about 10% above listing asking rents in the median zip code. Largest gaps are zip codes with few listings (Orinda 94563, 11 listings, +81%) or listings skewed to small units (San Francisco 94109, +51%), and one in the other direction, Saint Helena (94574, −50%), where listings are skewed to large homes.
- **Typical, not average:** ZHVI measures the middle third of homes by value, so mansions and teardowns don't move it; ZORI weights rentals to the whole rental stock.
- **Coverage:** Zillow only publishes ZORI where it has enough rentals. 45 of the 255 reliable zip codes have no `typical_rent` (mostly small or rural ones), and 3 have no `typical_home_value`. They're blank, not filled in. For those, `listing_median_rent` from the datathon is the fallback, with `listing_n_rentals` showing how much to trust it.
- **City and county labels come from Anna's table** so the two tables match. Zillow sometimes names a zip code differently (94303 is "East Palo Alto" in Zillow, "Palo Alto" in Anna's; 94010 is "Hillsborough" vs. "Burlingame").
- **2019 comparisons** use December 2019 (before the pandemic). Zillow's rent index starts later in many zip codes, so `rent_change_since_2019_pct` is filled for 119 zip codes.
- **Extraction check:** the Bay Area rows were read from Zillow's files through a browser and copied here; row counts and the sum of all values matched exactly between the two (ZORI 210 rows, ZHVI 274 rows).

---

## Potential biases

- **Typical rent isn't what long-time tenants pay.** ZORI is based on rents for homes listed for rent, so it reflects the market a mover faces. Under rent control, long-time tenants often pay much less. Census ACS median gross rent would show what current residents pay.
- **Missing rent data clusters in small and rural zip codes**, so findings about rent describe denser areas better.
- **Zestimate-based values are model estimates.** Zillow's error is larger where few homes sell, which can include rural and lower-income zip codes.
- **"Cheaper" isn't "affordable."** `income_needed_for_rent` shows what it takes, but not who has it. Adding Census median household income would give rent burden (rent as a share of local income), a much stronger affordability measure, and the natural next step for comparing with redlined areas.

---

## Files in this folder

| File | What it is |
|---|---|
| `notebooks/04_albert_housing_costs.ipynb` | **Main notebook.** Reads Zillow's indexes from their URLs, so anyone can rerun it (Colab or locally) |
| `notebooks/04b_albert_listing_costs.ipynb` | Backup: the same measures from the datathon listing files, for when Drive allows downloads |
| `data/zillow_research/zori_bay_area.csv`, `zhvi_bay_area.csv` | The Bay Area rows of Zillow's two files (December of each year from 2015, plus September 2026). The notebook uses them when it can't download from Zillow, and refreshes them when it can |
| `outputs/tables/albert_housing_by_zip.csv` | **Main result:** 293 zip codes |
| `outputs/tables/albert_housing_by_county.csv` | Median zip code per county |
| `outputs/tables/housing_plus_essentials_by_zip.csv` | Housing columns + Anna's access columns in one table, for the map |
| `outputs/figures/albert_*.png` | 5 charts, below |

### `albert_housing_by_zip.csv`: main result (293 rows, one per zip code)

| Column | Meaning |
|---|---|
| `zipcode` | 5-digit zip code. **Read as text** (`dtype={"zipcode": str}`) |
| `city`, `county`, `n_homes`, `low_data` | From Anna's table (same values). Filter `low_data == False` for findings |
| `in_anna_table` | `True` for all 293 rows |
| `typical_rent` | Zillow ZORI, $/month, September 2026 (blank if Zillow doesn't publish one) |
| `typical_home_value` | Zillow ZHVI, $, September 2026 |
| `affordability_score` | 0–100, higher = cheaper than other Bay Area zip codes (method above) |
| `income_needed_for_rent` | Yearly income at which `typical_rent` is 30% of income, rounded to $100 |
| `price_to_rent_ratio` | `typical_home_value` ÷ (12 × `typical_rent`): years of rent to equal the price of the typical home |
| `rent_change_2025_pct`, `value_change_2025_pct` | % change December 2024 → December 2025 |
| `rent_change_since_2019_pct`, `value_change_since_2019_pct` | % change December 2019 → September 2026 |
| `listing_median_rent`, `listing_n_rentals`, `listing_rent_per_bedroom` | From the datathon listings via Anna's table (her `median_rent`, `n_rentals`, `rent_per_bedroom`) |
| `zori_vs_listing_pct` | % difference between `typical_rent` and `listing_median_rent` |
| `rent_2015` … `rent_2025`, `value_2015` … `value_2025` | December value of each year, for trends or time sliders on the map |
| `rent_latest`, `value_latest` | Same as `typical_rent` / `typical_home_value` |
| `rent_month`, `value_month` | Month of the latest values (2026-09-30) |

### Charts

| File | What it shows |
|---|---|
| `albert_cost_by_county.png` | Typical rent and home value in each county's median zip code |
| `albert_rent_ranking.png` | The 10 cheapest (blue) and 10 most expensive (orange) zip codes to rent in |
| `albert_home_value_ranking.png` | The 10 cheapest and 10 most expensive zip codes to buy in |
| `albert_rent_vs_value.png` | Each dot is a zip code: rent (x) vs. home value (y); above the dashed line, buying costs more years of rent than the median |
| `albert_rent_check.png` | Hand-check: Zillow's rent index vs. datathon listing rents per zip code |

---

## Notes for Person 4 and the map

- **Join on `zipcode` as text.** Same 293 zip codes as Anna's table.
- **Filter `low_data == False`** before findings, as with Anna's table.
- **Good map layers:** `typical_rent`, `typical_home_value`, `income_needed_for_rent` (most intuitive for an audience), `affordability_score` (same 0–100 scale as Anna's `access_score`), `rent_change_since_2019_pct` (displacement pressure).
- **Blank rent:** 45 reliable zip codes have no `typical_rent`. Show them as "no data", or fall back to `listing_median_rent` and label it as listing-based.
- **For the redlining comparison:** the 1930s HOLC maps covered San Francisco, the East Bay (Oakland, Berkeley, Alameda) and San Jose. Joining HOLC polygons to zip codes (ZCTAs) by overlap would let the team compare `typical_rent`, `rent_change_since_2019_pct` and `access_score` across HOLC grades.
- **Ethics:** results are zip-code level only. No addresses or individual listings.
