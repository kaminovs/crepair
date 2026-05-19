"""
scoring/visualise.py

Charts for CRepair results.

  plot_radar(results)        — one radar per model, D/R/V/S axes
  plot_comparison(results)   — grouped bar chart across models
  plot_by_type(results)      — C_repair heatmap: model × failure type
  save_all(results, outdir)  — generates all three and saves PNGs

Requires: matplotlib (pip install matplotlib)
"""

import json
import csv
from pathlib import Path
from typing import Optional
from collections import defaultdict


def _load_matplotlib():
    try:
        import matplotlib
        matplotlib.use("Agg")          # no display needed
        import matplotlib.pyplot as plt
        import numpy as np
        return plt, np
    except ImportError:
        raise ImportError("pip install matplotlib numpy")


# ── Radar chart ───────────────────────────────────────────────────────────────

def plot_radar(
    model_scores: dict[str, dict],   # {model: {D, R, V, S, C_repair}}
    title: str = "C_repair Component Scores by Model",
    outpath: Optional[Path] = None
):
    """
    model_scores example:
        {
          "gpt-4o":  {"D": 0.8, "R": 0.7, "V": 0.4, "S": 0.9},
          "claude":  {"D": 0.6, "R": 0.8, "V": 0.7, "S": 0.85},
        }
    """
    plt, np = _load_matplotlib()

    components = ["D", "R", "V", "S"]
    N = len(components)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]   # close the polygon

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

    colors = ["#4F46B2", "#1D9E75", "#D85A30", "#BA7517", "#7c74dc"]
    for i, (model, scores) in enumerate(model_scores.items()):
        vals = [scores.get(c, 0) for c in components]
        vals += vals[:1]
        c = colors[i % len(colors)]
        ax.plot(angles, vals, "o-", linewidth=2, label=model, color=c)
        ax.fill(angles, vals, alpha=0.08, color=c)

    ax.set_thetagrids(
        [a * 180 / 3.14159 for a in angles[:-1]],
        labels=["D\n(Detection)", "R\n(Repair)", "V\n(Verification)", "S\n(Stability)"]
    )
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0.25", "0.5", "0.75", "1.0"], fontsize=8)
    ax.set_title(title, pad=20, fontsize=13, fontweight="bold")
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=10)

    plt.tight_layout()
    if outpath:
        plt.savefig(outpath, dpi=150, bbox_inches="tight")
        print(f"  Saved radar: {outpath}")
    else:
        plt.show()
    plt.close()


# ── Grouped bar chart ─────────────────────────────────────────────────────────

def plot_comparison(
    model_scores: dict[str, dict],
    title: str = "C_repair Component Comparison",
    outpath: Optional[Path] = None
):
    plt, np = _load_matplotlib()

    components = ["D", "R", "V", "S", "C_repair"]
    models = list(model_scores.keys())
    x = np.arange(len(components))
    width = 0.8 / len(models)

    fig, ax = plt.subplots(figsize=(9, 5))
    colors = ["#4F46B2", "#1D9E75", "#D85A30", "#BA7517", "#7c74dc", "#888680"]

    for i, (model, scores) in enumerate(model_scores.items()):
        vals = [scores.get(c, 0) for c in components]
        offset = (i - len(models) / 2 + 0.5) * width
        bars = ax.bar(x + offset, vals, width * 0.9,
                      label=model, color=colors[i % len(colors)], alpha=0.85)
        for bar, val in zip(bars, vals):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                        f"{val:.2f}", ha="center", va="bottom", fontsize=7)

    ax.set_xticks(x)
    ax.set_xticklabels(components, fontsize=11)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Score", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.axhline(y=1.0, color="gray", linewidth=0.5, linestyle="--")

    # Highlight C_repair column
    ax.axvspan(len(components) - 1.5, len(components) - 0.5,
               alpha=0.06, color="#4F46B2")

    plt.tight_layout()
    if outpath:
        plt.savefig(outpath, dpi=150, bbox_inches="tight")
        print(f"  Saved comparison: {outpath}")
    else:
        plt.show()
    plt.close()


# ── Heatmap: model × failure type ────────────────────────────────────────────

def plot_heatmap(
    data: dict[str, dict[str, float]],  # {model: {failure_type: C_repair}}
    title: str = "C_repair by Model × Failure Type",
    outpath: Optional[Path] = None
):
    plt, np = _load_matplotlib()

    models = list(data.keys())
    types  = list(next(iter(data.values())).keys())

    matrix = np.array([[data[m].get(t, float("nan")) for t in types]
                        for m in models])

    fig, ax = plt.subplots(figsize=(max(8, len(types) * 1.4), max(4, len(models) * 0.9)))
    im = ax.imshow(matrix, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")

    ax.set_xticks(range(len(types)))
    ax.set_xticklabels([t.replace("_", "\n") for t in types], fontsize=9)
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(models, fontsize=10)

    for i in range(len(models)):
        for j in range(len(types)):
            val = matrix[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        fontsize=9, color="black" if 0.3 < val < 0.8 else "white")

    plt.colorbar(im, ax=ax, label="C_repair")
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()

    if outpath:
        plt.savefig(outpath, dpi=150, bbox_inches="tight")
        print(f"  Saved heatmap: {outpath}")
    else:
        plt.show()
    plt.close()


# ── Load from leaderboard CSV ──────────────────────────────────────────────────

def load_leaderboard(path: Path) -> list[dict]:
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def aggregate_by_model_condition(rows: list[dict]) -> dict[str, dict]:
    """Average D, R, V, S, C_repair per (model, condition)."""
    buckets: dict[str, list] = defaultdict(list)
    for row in rows:
        if row.get("D", "?") == "?":
            continue
        key = f"{row['model']} ({row['condition']})"
        buckets[key].append({
            "D": float(row["D"]), "R": float(row["R"]),
            "V": float(row["V"]), "S": float(row["S"]),
            "C_repair": float(row["C_repair"]),
        })
    return {
        k: {c: sum(r[c] for r in v) / len(v) for c in ["D","R","V","S","C_repair"]}
        for k, v in buckets.items()
    }


def aggregate_by_type(rows: list[dict]) -> dict[str, dict[str, float]]:
    """Average C_repair per model per failure_type."""
    buckets: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if row.get("C_repair", "?") == "?":
            continue
        buckets[row["model"]][row["scenario_type"]].append(float(row["C_repair"]))
    return {
        model: {t: sum(v)/len(v) for t, v in types.items()}
        for model, types in buckets.items()
    }


# ── Generate all charts ────────────────────────────────────────────────────────

def save_all(leaderboard_path: Path, outdir: Optional[Path] = None):
    outdir = outdir or leaderboard_path.parent / "charts"
    outdir.mkdir(exist_ok=True)

    rows = load_leaderboard(leaderboard_path)
    if not any(r.get("D", "?") != "?" for r in rows):
        print("[Visualise] No real results yet — charts will be empty.")
        return

    model_scores = aggregate_by_model_condition(rows)
    type_scores  = aggregate_by_type(rows)

    plot_radar(model_scores,      outpath=outdir / "radar.png")
    plot_comparison(model_scores, outpath=outdir / "comparison.png")
    if type_scores:
        plot_heatmap(type_scores, outpath=outdir / "heatmap.png")

    print(f"[Visualise] All charts saved to {outdir}/")


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    lb = Path(sys.argv[1]) if len(sys.argv) > 1 else \
         Path(__file__).parent.parent / "results" / "leaderboard.csv"
    save_all(lb)
