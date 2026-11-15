# Integration check report

| check | status | detail |
|---|---|---|
| 1 make all end-to-end | PASS | pipeline ran in this checkout; run `python run.py clean-clone-check` for a true clean clone |
| 2 schema tests | PASS | 3 interim parquet(s) validated by tests/test_schemas.py |
| 3 no test leakage | PASS | 0 overlapping ids |
| 4 baseline + test metrics | PASS | baseline rows: True; test metrics: yes |
| 5 >=3 subgroups + failure examples | PASS | 15 subgroup rows, 110 failure examples |
| 6 data decisions + hand-check | PASS | 0 TODO markers in data_decisions.md; 2 hand-check(s) |
| 7 README repro verified | MANUAL | follow README from a fresh clone on a teammate's laptop |
| 8 slide numbers match 07 | MANUAL | 3 [F#] refs resolve; eyeball deck numbers against 07_key_findings.csv |
