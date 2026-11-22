"""mcm_style -- shared, importable figure style system for MCM projects.

The package consolidates the styling knowledge accumulated across Practice1,
FigureTraining and Practice2 into one importable layer, so every project calls
the same code instead of re-writing a private style module.

Quick start
-----------
>>> import mcm_style
>>> from mcm_style import typography
>>> typography.configure("academic_serif")
>>> import mcm_style.components as c
>>> fig, ax = c.sheet(3.0)
>>> c.box(ax, .1, .4, .3, .2, "Title", "detail", mcm_style.TEAL)

Submodules
----------
palette     : color constants, named themes and semantic encoding
colormaps   : custom sequential / diverging colormaps
typography  : serif / sans rcParams presets
components  : diagram primitives and rich canvas/stage cards
"""

from . import palette, colormaps, typography, components, page, accents
from .palette import (  # noqa: F401
    INK, MUTED, GRID, LIGHT, BLUE, TEAL, AMBER, PLUM,
    DEFAULT, MORANDI, AWARD, PAPER, SEMANTIC,
    DEFAULT_CYCLE, MORANDI_CYCLE, BAR_PAIR, BAR_LIKERT, BAR_COMPONENTS, BAR_PERIODS,
)
from .typography import PAGE_WIDTH, configure, paper_context
from .page import panels, head, grid, save_paper
from .colormaps import get as get_colormap, COLORMAPS  # noqa: F401

__version__ = "1.5.0"
__all__ = [
    "palette", "colormaps", "typography", "components", "page", "accents",
    "INK", "MUTED", "GRID", "LIGHT", "BLUE", "TEAL", "AMBER", "PLUM",
    "DEFAULT", "MORANDI", "AWARD", "PAPER", "SEMANTIC",
    "DEFAULT_CYCLE", "MORANDI_CYCLE", "BAR_PAIR", "BAR_LIKERT",
    "BAR_COMPONENTS", "BAR_PERIODS",
    "PAGE_WIDTH", "configure", "paper_context", "panels", "head", "grid",
    "save_paper", "get_colormap", "COLORMAPS", "__version__",
]
