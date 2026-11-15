"""§8.2: every data/interim/*.parquet matches its SCHEMA in src/data/schemas.py."""
from __future__ import annotations

import pandas as pd
import pytest

from src.data.schemas import SCHEMAS
from src.data.validate import validate
from src.utils import load_config

INTERIM = sorted(load_config()["paths"]["interim"].glob("*.parquet"))


@pytest.mark.parametrize("path", INTERIM, ids=[p.stem for p in INTERIM])
def test_interim_matches_schema(path):
    assert path.stem in SCHEMAS, f"{path.name} has no SCHEMA in src/data/schemas.py"
    problems = validate(pd.read_parquet(path), SCHEMAS[path.stem])
    assert not problems, f"{path.name}:\n  " + "\n  ".join(problems)


def test_validator_catches_contract_breaks():
    schema = {"place_id": {"dtype": "string", "nullable": False, "unique": True},
              "lat": {"dtype": "float", "nullable": False}}
    good = pd.DataFrame({"place_id": ["a", "b"], "lat": [37.1, 37.2]})
    assert validate(good, schema) == []
    bad = pd.DataFrame({"place_id": ["a", "a"], "lat": ["37.1", None], "extra": [1, 2]})
    probs = " | ".join(validate(bad, schema))
    assert "duplicate" in probs and "expected float" in probs and "extra" in probs
