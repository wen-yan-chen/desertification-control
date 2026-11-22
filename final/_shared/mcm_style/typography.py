"""Typography and global rcParams presets.

Two presets are provided so neither historical style is lost:

* ``academic_serif`` -- Times New Roman serif, for in-paper data charts
  (matches the O-award mplstyle and the FigureTraining / Practice2 work).
* ``modern_sans`` -- DejaVu Sans, for diagrams, dashboards and the Morandi
  polished figures (Practice1).

Call :func:`configure` once at the start of a rendering script.
"""

import matplotlib as mpl

from . import palette as P

# Default text block width used by the team's Letter paper (inches).
PAGE_WIDTH = 6.5

_BASE = {
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.dpi": 300,
    "savefig.bbox": None,
    "pdf.fonttype": 42,  # embed editable TrueType text, not outlined paths
    "ps.fonttype": 42,
    "text.usetex": False,
    "text.color": P.INK,
    "axes.labelcolor": P.INK,
    "axes.edgecolor": "#8B9A9F",
    "axes.linewidth": 0.7,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.axisbelow": True,
    "axes.grid": False,
    "axes.facecolor": "white",
    "xtick.color": P.INK,
    "ytick.color": P.INK,
    "grid.color": P.GRID,
    "grid.linewidth": 0.65,
    "legend.frameon": False,
    "figure.figsize": (PAGE_WIDTH, 4.0),
}

PRESETS = {
    "academic_serif": {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 9,
        "axes.labelsize": 9,
        "axes.titlesize": 10,
        "axes.titleweight": "bold",
        "axes.titlepad": 7,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8.4,
        "lines.linewidth": 1.65,
        "lines.markersize": 4,
        "axes.prop_cycle": mpl.cycler(color=P.DEFAULT_CYCLE),
    },
    "modern_sans": {
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial"],
        "font.size": 11,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "lines.linewidth": 2.0,
        "lines.markersize": 6,
        "axes.edgecolor": "#C9C2B8",
        "axes.prop_cycle": mpl.cycler(color=P.MORANDI_CYCLE),
    },
}


def _settings(preset, overrides):
    if preset not in PRESETS:
        raise KeyError(f"unknown preset {preset!r}; choose from {list(PRESETS)}")
    settings = dict(_BASE)
    settings.update(PRESETS[preset])
    settings.update(overrides)
    return settings


def configure(preset="academic_serif", **overrides):
    """Apply a named preset to the global rcParams, with optional overrides."""
    settings = _settings(preset, overrides)
    mpl.rcParams.update(settings)
    return settings


def paper_context(preset="academic_serif", **overrides):
    """Scope typography to one figure; keep this context through export."""
    return mpl.rc_context(_settings(preset, overrides))
