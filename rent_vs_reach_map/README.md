# Rent vs. Reach: Bay Area map

An interactive map of 273 Bay Area ZIP codes, shaded by median asking rent (darker red = cheaper). Click a ZIP to see what living there gets a low-wage worker: rent burden, distance to groceries, clinics, pharmacies, transit and food banks, Walk and Transit Scores, and nearby services.

## Open it

Double-click **`index.html`**. It opens in any browser and works offline (`d3.min.js` is included).

Fonts come from Google Fonts when online, with a system-font fallback offline.

To put it online, upload the whole folder to any static host (GitHub Pages, Netlify, a school web space). Keep `index.html` and `d3.min.js` together.

## What's in this folder

| File | What it is |
|---|---|
| `index.html` | The map. All data is built into the page; no server needed |
| `d3.min.js` | d3 v7.8.5, the library that draws the map |
| `data/zips.json` | Per-ZIP numbers + simplified ZIP outlines (what the page shows) |
| `data/summary.json` | Region-wide headline numbers |
| `scripts/build_data.py` | Raw datasets → `data/zips.json` and `data/summary.json` |
| `scripts/render.py` | `data/*.json` + `scripts/template.html` → `index.html` |
| `scripts/template.html` | Page design and code, with placeholders for the data |

## Rebuild from raw data

1. Install Python packages:
   ```bash
   pip install duckdb pandas numpy scipy shapely
   ```
2. Put the raw files in a folder `raw/` next to this README (or set `DATA_DIR`):
   ```
   raw/zillow/zillow_part1.csv, zillow_part2.csv, zillow_part3.csv   (shared drive: Zillow Housing)
   raw/places/google_maps.csv                                        (shared drive: Google Maps Places)
   raw/reviews/google_maps_reviews.csv                               (shared drive: Google Maps Reviews)
   raw/indeed/indeed_job_listings.csv                                (shared drive: Indeed Jobs)
   raw/ca_california_zip_codes_geo.min.json                          (Census 2010 ZIP shapes, see below)
   ```
   ZIP shapes: `ca_california_zip_codes_geo.min.json` from the public GitHub repo `OpenDataDE/State-zip-code-GeoJSON`.
3. Run:
   ```bash
   python scripts/build_data.py
   ```
   ```bash
   python scripts/render.py
   ```

`build_data.py` takes about 1–2 minutes and reads about 10 GB.

## How the numbers are built

- **Housing cost:** median asking rent of `FOR_RENT` Zillow listings per ZIP (rents $500–$20,000 kept). ZIPs with fewer than 8 rentals are grey. Colors split ZIPs into seven equal-count groups.
- **Wages:** median posted pay of hourly Indeed postings in the ZIP's city (20+ postings needed), otherwise the Bay Area median ($25.64/hr). Salary text is converted to hourly; reposts are removed.
- **Rent burden:** median rent ÷ (wage × 2,080 hours ÷ 12). Over 30% = cost-burdened.
- **Essentials nearby:** share of a ZIP's rentals with a grocery store, a clinic and a pharmacy each within 1 mile, plus a bus stop or transit station within ¼ mile. Straight-line distance to the nearest Google Maps place. Permanently closed places are dropped.
- **Pattern:** each ZIP is compared with the median ZIP on rent and on essentials nearby. "Affordable but underserved" = cheaper than the median, with fewer essentials nearby.
- **Service quality:** average Google rating of rated grocery stores, clinics and pharmacies (a rating of 0 = no reviews yet, excluded).

## Limits

- Asking rents describe listings on the market, not what current tenants pay.
- Places shows which services exist, not whether they're affordable.
- Straight-line distance understates real travel across hills and freeways.
- These numbers come from the listings, so they differ from the team repo's Zillow rent index (Albert) and access score (Anna). Use one source per slide.
- Results are by ZIP only; no addresses or reviewer names are shown.
