"""Shared page-width styling and data access for the Practice2 paper figures."""

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "Data/v7"
RESULTS = ROOT / "Results/v7"
INK = "#22343D"
MUTED = "#50616B"
GRID = "#DEE6E8"
BLUE = "#285987"
TEAL = "#08786F"
AMBER = "#9D5526"
PLUM = "#724C79"
LIGHT = "#F3F7F7"
CASH = (TEAL, BLUE, PLUM)
COHORT = (TEAL, PLUM, AMBER)
MONTHS = tuple("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())


def configure():
    mpl.rcParams.update({
        "figure.facecolor": "white", "savefig.facecolor": "white",
        "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
        "mathtext.fontset": "stix", "pdf.fonttype": 42,
        "font.size": 9, "text.color": INK,
        "axes.labelcolor": INK, "axes.labelsize": 9,
        "axes.edgecolor": "#8B9A9F", "axes.linewidth": .65,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.axisbelow": True, "axes.titlesize": 10,
        "axes.titleweight": "bold", "axes.titlepad": 7,
        "xtick.color": INK, "ytick.color": INK,
        "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
        "xtick.major.size": 3, "ytick.major.size": 3,
        "grid.color": GRID, "grid.linewidth": .65,
        "legend.fontsize": 8.4, "legend.frameon": False,
        "lines.linewidth": 1.65, "lines.markersize": 4,
        "image.interpolation": "nearest",
    })


def csv(model, name):
    return pd.read_csv(RESULTS / model / f"{name}.csv")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def panels(height, rows=1, cols=1, **kwargs):
    fig, axes = plt.subplots(rows, cols, figsize=(6.5, height),
                             layout="constrained", squeeze=False, **kwargs)
    fig.get_layout_engine().set(w_pad=.09, h_pad=.06, wspace=.10, hspace=.13)
    return fig, axes


def head(ax, letter, title):
    ax.set_title(f"({letter})  {title}", loc="left")


def grid(ax, axis="y"):
    ax.grid(axis=axis)


def sheet(height):
    fig = plt.figure(figsize=(6.5, height))
    ax = fig.add_axes([0, 0, 1, 1], xlim=(0, 1), ylim=(0, 1))
    ax.set_axis_off()
    return fig, ax


def box(ax, x, y, w, h, title, detail, color, fill="white"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=.012",
                               linewidth=.9, edgecolor=color, facecolor=fill, zorder=2))
    ax.text(x + w / 2, y + h * .70, title, color=color, fontsize=10,
            weight="bold", ha="center", va="center", zorder=3)
    ax.text(x + w / 2, y + h * .32, detail, ha="center", va="center",
            linespacing=1.26, fontsize=8.6, zorder=3)


def arrow(ax, start, end, color=MUTED, **kwargs):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=9,
                                color=color, lw=.95, shrinkA=0, shrinkB=0, **kwargs))


def foot(ax, message, y=.065):
    ax.text(.5, y, message, ha="center", va="center", color=MUTED, fontsize=8.4)


def cohort_order():
    initial = csv("model3", "initial_cohorts")
    return initial.sort_values(["age_year", "area_ha"], ascending=[False, False])
