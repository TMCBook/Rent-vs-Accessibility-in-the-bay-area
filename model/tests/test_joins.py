"""audited_merge logs counts and refuses silent many-to-many joins."""
from __future__ import annotations

import pandas as pd
import pytest

from src.features.joins import audit_rows, audited_merge, reset_audit


def test_audit_logs_unmatched():
    reset_audit()
    left = pd.DataFrame({"k": [1, 2, 3, 4]})
    right = pd.DataFrame({"k": [1, 2], "v": ["a", "b"]})
    out = audited_merge(left, right, on="k", step="demo")
    a = audit_rows().iloc[0]
    assert len(out) == 4 and a["matched_n"] == 2 and a["pct_left_unmatched"] == 50.0


def test_many_to_many_rejected():
    dup = pd.DataFrame({"k": [1, 1]})
    with pytest.raises(ValueError):
        audited_merge(dup, dup, on="k", step="x", validate="many_to_many")
    with pytest.raises(pd.errors.MergeError):  # default many_to_one catches duplicated right keys
        audited_merge(dup, dup, on="k", step="x")
