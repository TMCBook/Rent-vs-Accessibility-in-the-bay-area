# Ethics: who could be disadvantaged?

Every number here comes from a table in `outputs/tables/` or the pipeline's data files.

## Who is in and out of the data

- **The model can't see most low-access ZIP codes.** Zillow publishes a rent index (ZORI) for only 173 of the 255 ZIPs with enough homes to analyze. Coverage follows density and wealth:

  | Access tier | ZIPs | Covered by the model |
  |---|---|---|
  | Low access | 56 | **11 (20%)** |
  | Mid access | 114 | 85 (75%) |
  | High access | 85 | 77 (91%) |

  By county, coverage ranges from 25% in Napa, 39% in Marin and 41% in Sonoma to 81% in Santa Clara and 83% in Alameda. The communities the project cares most about, those far from essentials, are the ones the forecast knows least about.
- **Early years are thin.** Zillow's rent index covered 9 Bay Area ZIPs in 2015 and 182 by 2025, so what the model learned about the 2010s comes from a handful of mostly urban ZIPs.
- **38 ZIPs are excluded** for having fewer than 20 homes in the listings (`low_data`), mostly small and rural places.
- **Job data misses small places.** 28 of 293 ZIPs (9.6%) have no Indeed postings under their city name (`02_join_audit.csv`), so their wage features are missing.
- **Scraped sources over-represent the formal market.**
  - Zillow captures listed rentals, not informal ones (rooms, in-law units rented by word of mouth), which are common among low-wage renters.
  - Google Maps may miss small or informal services (community pantries, corner produce stands), which makes some neighborhoods look worse served than they are.
  - Indeed covers formal postings, not day labor or informal work.
- **Asking rent isn't what tenants pay.** Under rent control, long-time tenants often pay much less, so the numbers describe what someone moving now would face.

## Who the model serves worse

On the held-out test year (2024 → 2025, `04_subgroup_performance.csv`, macro-F1):

| Group | ZIPs | Model | Persistence baseline |
|---|---|---|---|
| **Low access** | 11 | **0.083** | 0.450 |
| **Cheapest third of rents** | 57 | **0.193** | 0.472 |
| Mid access | 78 | 0.355 | 0.511 |
| High access | 77 | 0.337 | 0.617 |
| Priciest third of rents | 53 | 0.467 | 0.581 |

- The model performs worst in **low-access** and **cheapest-rent** ZIPs, exactly where low-wage renters live. The cheapest-rent group is the worst group with 30+ ZIPs (`07_key_findings.csv`, F6).
- Overall the model fails on the test year (AUC 0.328 vs. 0.589 for persistence, F1–F5) because the market shifted after 2023. Anyone relying on it in 2025 would have been steered to the wrong neighborhoods.
- Concrete mispredictions are listed in `05_failure_examples.csv`. Most are false alarms: ZIPs flagged for a spike that didn't come.

## How it could be misused

- **Speculation.** A list of ZIPs "about to see rent spikes" is useful to investors and landlords looking for neighborhoods to buy into or raise rents in. That could speed up the displacement the project is trying to prevent.
- **Disinvestment or stigma.** Labeling places "underserved" or "high risk" could be read as a reason to avoid them (insurers, lenders, businesses choosing where to locate), not to invest in them.
- **Mistaking the ranking for a verdict.** The help-first ranking multiplies a forecast that failed its test by a relative access score and a rough renter count. Used to allocate money without local knowledge, it could send help to the wrong places, for example to car-oriented wealthy suburbs that score low on access.
- **Screening people.** Applying ZIP-level risk to individual tenants or applicants (housing, credit, jobs) would be discriminatory. Nothing here supports decisions about individuals.

## Privacy

- All results are by ZIP code. No addresses, listing IDs or coordinates of individual homes are published.
- Google review text, reviewer names, profile photos and URLs are never shown; reviews only feed average ratings and reply rates.
- Job postings are summarized per city (counts, median pay); no individual postings are published.
- The hand-check sheets contain posting IDs and salary text only, no personal information.

## Mitigations and limitations

- **Report the failure prominently.** The test result, the regime shift and the subgroup gaps are in the README, the model write-up and this document, not hidden in an appendix.
- **The ranking is labeled "not validated"** everywhere it appears, and it ranks only ZIPs at or below median rent, so wealthy low-access suburbs don't top the list.
- **Coverage is stated next to results.** Anyone reading a ZIP's forecast should know the model covers 20% of low-access ZIPs.
- **Publish at ZIP level only.** The ranking file is in this repo so judges can check it; outside the datathon, it should go to tenant organizations, community groups and local agencies with these caveats attached, not be promoted as a public "where rents will rise" list.
- **Human review before action.** Any use should combine the list with local knowledge: income data (Census), car ownership, and what residents report.

**Intended use:** a starting point for city planners, housing nonprofits and transit agencies to ask "where should we look first?" It is not a decision-making tool for individuals, and not a rent forecast to act on without retraining on recent years.
