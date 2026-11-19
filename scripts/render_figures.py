"""Render both companion figures using only the verified replay JSON. Requires Matplotlib."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "figures"
OUT.mkdir(exist_ok=True)
models = json.loads((ROOT / "reference/replay.json").read_text(encoding="utf-8"))["models"]
qwen, smol = (models[key] for key in ("Qwen2.5-3B-Instruct", "SmolLM2-1.7B-Instruct"))
green, blue, ink, grid = "#15624f", "#415c82", "#172c29", "#dde5e0"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "text.color": ink,
                     "axes.labelcolor": ink, "xtick.color": ink, "ytick.color": ink,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.spines.left": False, "axes.spines.bottom": False})


def canvas(title):
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=160)
    fig.subplots_adjust(left=.32, right=.905, top=.69, bottom=.18)
    fig.text(.07, .91, title, fontsize=16, fontweight="bold")
    fig.legend(handles=[plt.Line2D([], [], marker="o", linestyle="", color=green, label="Qwen2.5-3B"),
                        plt.Line2D([], [], marker="s", linestyle="", color=blue, label="SmolLM2-1.7B")],
               loc="upper left", bbox_to_anchor=(.057, .86), frameon=False, ncol=2, fontsize=11)
    ax.tick_params(axis="both", length=0, pad=8)
    ax.xaxis.grid(color=grid, zorder=0)
    ax.set_axisbelow(True)
    return fig, ax


def plot_pair(ax, y, a, b):
    ax.plot([min(a,b), max(a,b)], [y,y], lw=2.0, color=grid, zorder=1)
    ax.plot(b, y+.095, "s", ms=7, color=blue, zorder=3)
    ax.plot(a, y-.095, "o", ms=8, color=green, zorder=4)


def export(fig, name):
    fig.savefig(OUT / name, dpi=160, facecolor="white", metadata={"Software":"PAIRSAFE research companion"})
    plt.close(fig)


fig, ax = canvas("Three ways to score the same 150 pairs")
fields = [("Ordering (PSA)", "psa"), ("Best shared threshold", "oracle_pcda"),
          ("Held-out threshold", "calibrated_pcda")]
for i, (_, key) in enumerate(fields):
    plot_pair(ax, i, qwen["contrastive_margin"][key], smol["contrastive_margin"][key])
ax.set(yticks=range(3), yticklabels=[s for s,_ in fields], ylim=(2.55,-.55), xlim=(.70,1.015),
       xticks=[.70,.75,.80,.85,.90,.95,1.0], xlabel="Share of matched pairs")
ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
export(fig, "paired-decisions.png")

fig, ax = canvas("A shared threshold within each category")
fields = [("Definitions","definitions"), ("Figurative language","figurative_language"),
          ("Historical events","historical_events"), ("Homonyms","homonyms"),
          ("Safe contexts","safe_contexts"), ("Safe targets","safe_targets")]
for i, (_, key) in enumerate(fields):
    plot_pair(ax, i, qwen["by_type"][key]["oracle_pcda"], smol["by_type"][key]["oracle_pcda"])
ax.set(yticks=range(6), yticklabels=[s for s,_ in fields], ylim=(5.55,-.55), xlim=(.66,1.02),
       xticks=[.68,.76,.84,.92,1.0], xlabel="Oracle-PCDA across 25 pairs per category")
ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
export(fig, "category-thresholds.png")
