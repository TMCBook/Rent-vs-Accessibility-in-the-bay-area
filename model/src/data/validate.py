"""Schema validation against src/data/schemas.py. Returns a list of human-readable problems."""
from __future__ import annotations

import pandas as pd
from pandas.api import types as pdt

KIND_CHECK = {
    "int": pdt.is_integer_dtype,
    "float": pdt.is_float_dtype,
    "string": lambda s: pdt.is_string_dtype(s) or pdt.is_object_dtype(s),
    "bool": pdt.is_bool_dtype,
    "datetime": pdt.is_datetime64_any_dtype,
    "category": lambda s: isinstance(s.dtype, pd.CategoricalDtype),
}


def validate(df: pd.DataFrame, schema: dict[str, dict]) -> list[str]:
    problems = []
    for col, spec in schema.items():
        if col not in df.columns:
            problems.append(f"missing column {col!r}")
            continue
        s = df[col]
        kind = spec["dtype"]
        if not KIND_CHECK[kind](s):
            problems.append(f"column {col!r}: expected {kind}, got {s.dtype}")
        if not spec.get("nullable", True) and s.isna().any():
            problems.append(f"column {col!r}: {int(s.isna().sum())} nulls but nullable=False")
        if spec.get("unique") and s.duplicated().any():
            problems.append(f"column {col!r}: {int(s.duplicated().sum())} duplicate values but unique=True")
    extra = sorted(set(df.columns) - set(schema))
    if extra:
        problems.append(f"undocumented extra columns (add to schema or drop): {extra}")
    return problems
