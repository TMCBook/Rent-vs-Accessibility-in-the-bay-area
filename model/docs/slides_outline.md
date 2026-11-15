# Slide deck outline

Every number on a slide is written as a finding id like `[F3]` that resolves to
`outputs/tables/07_key_findings.csv`; `run.py check` fails on unknown ids.
Figures come only from `outputs/figures/`.

1. **Title**: project name, team, cause (one sentence)
2. **The problem & who it affects**: social-good framing, why it matters in the Bay Area
3. **Data**: datasets used, rows, coverage (`01_dataset_summary.csv`), join audit (`02`)
4. **Data decisions**: labels, cleaning, hand-check agreement (`06`)
5. **Method**: split (group split?), baseline(s), model, metric choice
6. **Results**: model vs baseline on held-out test (`fig_model_vs_baseline.png`) [F1] [F2]
7. **Fairness**: ≥3 subgroups (`fig_subgroup_*.png`), worst gap
8. **Failure examples**: 2–3 concrete cases from `05` with notes
9. **Social-good impact**: who acts on this and how
10. **Ethics & limitations**: from `docs/ethics.md`
11. **Advanced checklist**: one slide mirroring `docs/checklist.md` with links
12. **Reproduce it**: repo link + `make all`
