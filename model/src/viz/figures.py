"""Step `figures`: slide-ready PNG/SVG from outputs/tables (never from ad-hoc notebook state).

  fig_model_vs_baseline.{png,svg}  primary metric per model (val, and test once unlocked)
  fig_subgroup_<col>.{png,svg}      model vs baseline primary metric per group, overall line
Colors: fixed categorical order (model=slot 1 blue, baselines=slots 2..). Direct labels, thin marks.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.eval.metrics import PRIMARY  # noqa: E402
from src.utils import load_config  # noqa: E402

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
INK, MUTED, GRID = "#1f1f1e", "#6b6a63", "#e4e3dd"

plt.rcParams.update({"font.size": 11, "axes.edgecolor": GRID, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left"})


def _save(fig, cfg, stem):
    for ext in ("png", "svg"):
        fig.savefig(cfg["paths"]["figures"] / f"{stem}.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote figure {stem}")


def model_vs_baseline(cfg):
    path = cfg["paths"]["tables"] / "03_model_vs_baseline.csv"
    if not path.exists():
        return
    prim = PRIMARY[cfg["task"]["type"]]
    d = pd.read_csv(path)
    d = d[d["metric"] == prim]
    split = "test" if (d["test"].astype(str) != "LOCKED").all() else "val"
    models = [cfg["model"]["name"], *cfg["baselines"]]
    d = d.set_index("model").loc[models]
    vals = d[split].astype(float)
    fig, ax = plt.subplots(figsize=(7, 0.6 * len(models) + 1.2))
    y = list(range(len(models)))[::-1]
    ax.barh(y, vals, height=0.55, color=SERIES[: len(models)], edgecolor="white", linewidth=2)
    for yi, v in zip(y, vals):
        ax.text(v, yi, f"  {v:.3f}", va="center", color=INK)
    ax.set_yticks(y, [f"{m} ({d.loc[m, 'role']})" for m in models])
    ax.set_xlabel(f"{prim} ({split} split)")
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title(f"Model vs baselines: {prim}, {split} split")
    _save(fig, cfg, "fig_model_vs_baseline")


def subgroups(cfg):
    path = cfg["paths"]["tables"] / "04_subgroup_performance.csv"
    if not path.exists():
        return
    d = pd.read_csv(path)
    if d.empty:
        return
    base = next((b for b in cfg["baselines"] if b != "dummy"), cfg["baselines"][0])
    base_color = SERIES[1 + cfg["baselines"].index(base)]
    for col, g in d.groupby("subgroup_type"):
        g = g.sort_values("n", ascending=True).tail(15)
        fig, ax = plt.subplots(figsize=(7.5, 0.42 * len(g) + 1.4))
        y = list(range(len(g)))
        ax.barh(y, g["model_value"], height=0.55, color=SERIES[0], label=cfg["model"]["name"],
                edgecolor="white", linewidth=2)
        ax.scatter(g["baseline_value"], y, s=64, color=base_color, zorder=3, label=f"baseline: {base}",
                   edgecolors="white", linewidths=2)
        ax.axvline(g["overall_model_value"].iloc[0], color=MUTED, linestyle="--", linewidth=1.2)
        labels = [f"{grp}  (n={n}{', small n' if sm else ''})"
                  for grp, n, sm in zip(g["group"], g["n"], g["small_n_caution"])]
        ax.set_yticks(y, labels)
        ax.set_xlabel(f"{g['primary_metric'].iloc[0]} ({g['split'].iloc[0]} split); dashed = overall")
        ax.grid(axis="x", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, borderaxespad=0.2)
        ax.set_title(f"Performance by {col}", pad=28)
        _save(fig, cfg, f"fig_subgroup_{col}")


def main() -> None:
    cfg = load_config()
    model_vs_baseline(cfg)
    subgroups(cfg)


if __name__ == "__main__":
    main()
