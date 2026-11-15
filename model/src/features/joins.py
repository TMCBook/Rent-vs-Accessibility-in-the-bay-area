"""Audited joins. Every join in the project goes through `audited_merge`:
logs left/right/matched counts and % unmatched to 02_join_audit.csv, and refuses
silent many-to-many joins.
"""
from __future__ import annotations

import pandas as pd

_AUDIT: list[dict] = []
COLUMNS = ["step", "left_n", "right_n", "matched_n", "result_n", "pct_left_unmatched", "how", "keys"]


def reset_audit() -> None:
    _AUDIT.clear()


def audit_rows() -> pd.DataFrame:
    return pd.DataFrame(_AUDIT, columns=COLUMNS)


def audited_merge(left: pd.DataFrame, right: pd.DataFrame, on, step: str, how: str = "left",
                  validate: str = "many_to_one", **kw) -> pd.DataFrame:
    """pd.merge with logging. `validate` defaults to many_to_one; many_to_many is rejected."""
    if validate in ("many_to_many", "m:m"):
        raise ValueError(f"[{step}] many-to-many joins are not allowed; aggregate one side first.")
    keys = [on] if isinstance(on, str) else list(on)
    probe = left[keys].merge(right[keys].drop_duplicates(), on=keys, how="left", indicator=True)
    matched = int((probe["_merge"] == "both").sum())
    out = left.merge(right, on=on, how=how, validate=validate, **kw)
    pct = round(100 * (1 - matched / max(len(left), 1)), 2)
    _AUDIT.append({"step": step, "left_n": len(left), "right_n": len(right), "matched_n": matched,
                   "result_n": len(out), "pct_left_unmatched": pct, "how": how, "keys": "+".join(keys)})
    print(f"[join:{step}] left={len(left)} right={len(right)} matched={matched} -> {len(out)} rows "
          f"({pct}% left unmatched)")
    return out
