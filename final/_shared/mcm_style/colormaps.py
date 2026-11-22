"""Custom sequential / diverging colormaps (Morandi-derived, plus helpers).

The colormaps originate from the Practice1 polished style and are rebuilt here
from the shared palette tokens so they stay in sync with ``palette.py``.
"""

from matplotlib.colors import LinearSegmentedColormap

from . import palette as P

# Sequential single-hue ramps.
morandi_teal = LinearSegmentedColormap.from_list(
    "morandi_teal", [P.MORANDI["teal"], P.MORANDI["teal_mid"], P.MORANDI["teal_soft"]])
morandi_coral = LinearSegmentedColormap.from_list(
    "morandi_coral", [P.MORANDI["coral"], P.MORANDI["coral_soft"]])
morandi_gold = LinearSegmentedColormap.from_list(
    "morandi_gold", [P.MORANDI["gold"], P.MORANDI["gold_soft"]])
morandi_rose = LinearSegmentedColormap.from_list(
    "morandi_rose", [P.MORANDI["rose"], "#E2C4CE"])

# Multi-hue heat ramp (cool -> warm).
morandi_heat = LinearSegmentedColormap.from_list(
    "morandi_heat", [P.MORANDI["slate"], P.MORANDI["teal"],
                     P.MORANDI["sage"], P.MORANDI["gold"], P.MORANDI["coral"]])

# Diverging ramp (teal -> neutral paper -> coral), centered on a neutral.
morandi_diverge = LinearSegmentedColormap.from_list(
    "morandi_diverge", [P.MORANDI["teal"], "#A9C7C9",
                        "#EFE7DC", "#E8B39A", P.MORANDI["coral"]])

# Academic ramps built from the default palette.
academic_teal = LinearSegmentedColormap.from_list(
    "academic_teal", [P.DEFAULT["light"], P.DEFAULT["teal"]])
academic_blue = LinearSegmentedColormap.from_list(
    "academic_blue", [P.DEFAULT["light"], P.DEFAULT["blue"]])
academic_plum = LinearSegmentedColormap.from_list(
    "academic_plum", ["#F2E8F4", "#A773A5", "#512756"])

# Registry for easy lookup by name.
COLORMAPS = {
    "morandi_teal": morandi_teal,
    "morandi_coral": morandi_coral,
    "morandi_gold": morandi_gold,
    "morandi_rose": morandi_rose,
    "morandi_heat": morandi_heat,
    "morandi_diverge": morandi_diverge,
    "academic_teal": academic_teal,
    "academic_blue": academic_blue,
    "academic_plum": academic_plum,
}


def get(name):
    """Look up a shared ramp, then fall back to Matplotlib's registry."""
    if name in COLORMAPS:
        return COLORMAPS[name]
    # Fall back to a built-in matplotlib colormap name.
    from matplotlib import colormaps
    return colormaps[name]
