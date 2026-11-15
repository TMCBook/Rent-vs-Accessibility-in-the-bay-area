"""One-command pipeline runner. `python run.py all` == `make all`.

Targets: data features split select train predict eval tables figures priority all final check
         clean-clone-check test clean
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable

STEPS = {
    "data": ["src.data.make_dataset"],
    "features": ["src.features.make_master"],
    "split": ["src.models.split"],
    "select": ["src.models.select"],
    "train": ["src.models.train"],
    "predict": ["src.models.predict"],
    "eval": ["src.eval.evaluate"],
    "tables": ["src.eval.make_tables"],
    "figures": ["src.viz.figures"],
    "priority": ["src.models.priority"],
}
ALL = ["data", "features", "split", "select", "train", "predict", "eval", "tables", "figures", "priority"]


def _run(module: str, *args: str) -> None:
    print(f"\n=== python -m {module} {' '.join(args)}", flush=True)
    subprocess.run([PY, "-m", module, *args], cwd=ROOT, check=True)


def run_target(target: str) -> None:
    if target in STEPS:
        for m in STEPS[target]:
            _run(m)
    elif target == "all":
        for t in ALL:
            run_target(t)
    elif target == "final":
        # Final, one-time test-set evaluation (features must be frozen).
        os.environ["DATATHON_FINAL_EVAL"] = "1"
        for t in ["predict", "eval", "tables", "figures"]:
            run_target(t)
    elif target == "test":
        subprocess.run([PY, "-m", "pytest", "-q", "tests"], cwd=ROOT, check=True)
    elif target == "check":
        run_target("all")
        run_target("test")
        _run("src.check")
    elif target == "clean-clone-check":
        clean_clone_check()
    elif target == "clean":
        for sub in ["data/interim", "data/processed", "outputs/tables", "outputs/figures", "outputs/models"]:
            for p in (ROOT / sub).glob("*"):
                if p.name != ".gitkeep":
                    shutil.rmtree(p) if p.is_dir() else p.unlink()
        print("Cleaned derived data and outputs (data/raw untouched).")
    else:
        sys.exit(f"Unknown target {target!r}. Options: {', '.join([*STEPS, 'all', 'final', 'check', 'clean-clone-check', 'test', 'clean'])}")


def clean_clone_check() -> None:
    """Clone the committed repo to a temp dir and run `all` there, using this checkout's raw data.
    Works when the pipeline lives in a subfolder (e.g. model/) of the repo."""
    raw = os.environ.get("DATATHON_RAW_DIR", str(ROOT / "data" / "raw"))
    top = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip())
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "clone"
        subprocess.run(["git", "clone", "--quiet", str(top), str(dest)], check=True)
        env = {**os.environ, "DATATHON_RAW_DIR": raw}
        r = subprocess.run([PY, "run.py", "all"], cwd=dest / ROOT.relative_to(top), env=env)
        print("\nCLEAN CLONE CHECK:", "PASS" if r.returncode == 0 else "FAIL")
        sys.exit(r.returncode)


if __name__ == "__main__":
    targets = sys.argv[1:] or ["all"]
    try:
        for t in targets:
            run_target(t)
    except subprocess.CalledProcessError as e:
        sys.exit(f"\nFAILED: {e.cmd}")
