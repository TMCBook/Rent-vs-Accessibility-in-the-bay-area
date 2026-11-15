"""Data contract: expected schema of every data/interim/<name>.parquet.

Owned by the Integrator. Each cleaner's output must match its SCHEMA here (tests/test_schemas.py).
dtype strings are pandas dtype *kinds*: "int", "float", "string", "bool", "datetime", "category".
Mirror every entry in docs/data_decisions.md (name, dtype, meaning, null handling).

Example (adapt once datasets are chosen):

SCHEMAS["places"] = {
    "place_id": {"dtype": "string", "nullable": False, "unique": True},
    "name":     {"dtype": "string", "nullable": True},
    "category": {"dtype": "string", "nullable": False},
    "lat":      {"dtype": "float",  "nullable": False},
    "lon":      {"dtype": "float",  "nullable": False},
    "zip":      {"dtype": "string", "nullable": True},
}
"""
from __future__ import annotations

SCHEMAS: dict[str, dict[str, dict]] = {}

S, F, I, B, D = "string", "float", "int", "bool", "datetime"


def _cols(spec: str) -> dict[str, dict]:
    """'name:kind[!][u]' items: ! = not nullable, u = unique."""
    out = {}
    for item in spec.split():
        name, k = item.split(":")
        kind = {"s": S, "f": F, "i": I, "b": B, "d": D}[k[0]]
        out[name] = {"dtype": kind, "nullable": "!" not in k, **({"unique": True} if "u" in k else {})}
    return out


# ZIP x year Zillow Research indexes (src/data/clean_zillow_research.py)
SCHEMAS["zillow_research"] = _cols(
    "zipcode:s! zillow_city:s county:s! month:d! year:i! rent:f value:f is_partial_year:b!")

# Essential-services access per ZIP, from Anna's table (src/data/clean_essentials.py)
SCHEMAS["essentials"] = _cols(
    "zipcode:s!u city:s! county:s! n_homes:i! low_data:b! access_score:f "
    "dist_grocery_mi:f dist_pharmacy_mi:f dist_primary_care_mi:f dist_transit_mi:f "
    "dist_food_bank_mi:f dist_bank_mi:f dist_check_cashing_mi:f "
    "count_grocery_1mi:f count_pharmacy_1mi:f count_primary_care_1mi:f count_transit_1mi:f "
    "count_food_bank_1mi:f bank_to_checkcash_ratio:f median_rent:f n_rentals:f!")

# Deduplicated Bay Area Indeed postings (src/data/clean_indeed.py)
SCHEMAS["indeed"] = _cols(
    "jobid:s city:s! zipcode:s job_title:s has_pay:b! hourly_pay:f pay_unit:s date_posted:d")
