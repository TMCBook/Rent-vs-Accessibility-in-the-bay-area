"""Model + baseline factories. Every pipeline uses the same preprocessing so comparisons are fair."""
from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import (HistGradientBoostingClassifier, HistGradientBoostingRegressor,
                              RandomForestClassifier, RandomForestRegressor)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


class PersistenceClassifier(ClassifierMixin, BaseEstimator):
    """Published-rule style baseline: 'what was high stays high'. Predicts the positive class when
    one input column (already a 0-1 percentile, e.g. last year's growth rank) is above `threshold`.
    Its score is that column itself, so AUC is meaningful. Fitting only records the classes."""

    def __init__(self, threshold: float = 2 / 3):
        self.threshold = threshold

    def fit(self, X, y):
        self.classes_ = np.unique(y)
        return self

    def _col(self, X):
        x = np.asarray(X, dtype=float)[:, 0]
        return np.nan_to_num(x, nan=0.5)

    def predict(self, X):
        return np.where(self._col(X) > self.threshold, self.classes_[1], self.classes_[0])

    def predict_proba(self, X):
        s = self._col(X)
        return np.c_[1 - s, s]


def preprocessor(num_cols: list[str], cat_cols: list[str]) -> ColumnTransformer:
    return ColumnTransformer([
        ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num_cols),
        ("cat", make_pipeline(SimpleImputer(strategy="most_frequent"),
                              OneHotEncoder(handle_unknown="ignore", min_frequency=5)), cat_cols),
    ])


def estimator(name: str, task: str, seed: int, params: dict | None = None):
    params = params or {}
    clf = task == "classification"
    table = {
        "dummy": (lambda: DummyClassifier(strategy="most_frequent")) if clf else (lambda: DummyRegressor()),
        "linear": (lambda: LogisticRegression(max_iter=2000, class_weight="balanced"))
                  if clf else (lambda: LinearRegression()),
        "logistic": lambda: LogisticRegression(max_iter=2000, random_state=seed, **params),
        "ridge": lambda: Ridge(random_state=seed, **params),
        "hist_gb": (lambda: HistGradientBoostingClassifier(random_state=seed, **params)) if clf
                   else (lambda: HistGradientBoostingRegressor(random_state=seed, **params)),
        "random_forest": (lambda: RandomForestClassifier(random_state=seed, n_jobs=-1, **params)) if clf
                         else (lambda: RandomForestRegressor(random_state=seed, n_jobs=-1, **params)),
    }
    if name not in table:
        raise ValueError(f"unknown model {name!r}; options: {sorted(table)}")
    return table[name]()


def build_pipeline(name: str, cfg: dict, num_cols: list[str], cat_cols: list[str]) -> Pipeline:
    t = cfg["task"]
    if name == "persistence":
        # Uses ONE column, passed through untouched (no scaling), set in config baseline_params.
        col = cfg.get("baseline_params", {}).get("persistence", {}).get("column")
        if col not in num_cols:
            raise SystemExit(f"persistence baseline needs numeric feature column {col!r}")
        sel = ColumnTransformer([("keep", "passthrough", [col])])
        return Pipeline([("prep", sel), ("est", PersistenceClassifier())])
    if name == "history_logistic":
        # Same learner as the main model, restricted to one dataset's features (e.g. rent history
        # only), so the comparison isolates what the other datasets add.
        cols = [c for c in cfg["baseline_params"]["history_logistic"]["columns"] if c in num_cols]
        params = cfg["model"].get("params") or {}
        return Pipeline([("prep", preprocessor(cols, [])),
                         ("est", LogisticRegression(max_iter=2000, random_state=cfg["seed"], **params))])
    params = cfg["model"].get("params") if name == cfg["model"]["name"] else None
    return Pipeline([("prep", preprocessor(num_cols, cat_cols)),
                     ("est", estimator(name, t["type"], cfg["seed"], params))])
