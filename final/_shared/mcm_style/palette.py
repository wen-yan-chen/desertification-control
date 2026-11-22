"""Central color palettes for the MCM figure style system.

Three historical palettes are preserved verbatim so no earlier training result
is lost. New projects should normally use ``DEFAULT`` (the academic serif-era
palette shared by FigureTraining and Practice2), or pick a named theme.

All values are hex strings. Nothing here imports matplotlib, so the constants
can be reused by any rendering backend.
"""

# ---------------------------------------------------------------------------
# Theme 1: Practice1 -- low-saturation Morandi / macaron (sans era)
# ---------------------------------------------------------------------------
MORANDI = {
    "ink": "#2E3438",
    "teal": "#3E7B8C", "teal_mid": "#6FA6AE", "teal_soft": "#B6D3D2",
    "coral": "#DE8868", "coral_soft": "#EDB59C",
    "gold": "#D2A450", "gold_soft": "#E5CB92",
    "sage": "#8CA48B", "rose": "#C78A9E", "slate": "#6E8CA8",
    "lavender": "#9B8FC0", "warm_gray": "#B6AEA4", "paper": "#FBFAF7",
}
# Ordered categorical cycle for the Morandi theme.
MORANDI_CYCLE = [
    MORANDI["teal"], MORANDI["coral"], MORANDI["gold"], MORANDI["sage"],
    MORANDI["slate"], MORANDI["rose"], MORANDI["lavender"],
    MORANDI["teal_mid"], MORANDI["warm_gray"],
]

# ---------------------------------------------------------------------------
# Theme 2: FigureTraining -- academic serif, deep ink + blue/green/orange
# ---------------------------------------------------------------------------
AWARD = {
    "ink": "#172A39", "muted": "#485D6E",
    "blue": "#235887", "green": "#167365", "orange": "#AA4D21",
}

# ---------------------------------------------------------------------------
# Theme 3: Practice2 paper figures -- page-width academic (teal/blue/plum)
# ---------------------------------------------------------------------------
PAPER = {
    "ink": "#22343D", "muted": "#50616B", "grid": "#DEE6E8",
    "blue": "#285987", "teal": "#08786F", "amber": "#9D5526",
    "plum": "#724C79", "light": "#F3F7F7",
}

# ---------------------------------------------------------------------------
# Default recommended palette (academic, aligned with the serif presets)
# ---------------------------------------------------------------------------
DEFAULT = {
    "ink": PAPER["ink"], "muted": PAPER["muted"], "grid": PAPER["grid"],
    "blue": PAPER["blue"], "teal": PAPER["teal"],
    "amber": PAPER["amber"], "plum": PAPER["plum"], "light": PAPER["light"],
}
# Categorical cycle used by data charts.
DEFAULT_CYCLE = [
    DEFAULT["teal"], DEFAULT["blue"], DEFAULT["plum"],
    DEFAULT["amber"], "#8F4F52", "#3A729A", "#6F563F",
]

# Bar and composition palettes distilled from FigureTraining 11. They remain
# separate from semantic economic/environment/social colors: ordinal levels,
# components and periods answer different questions.
BAR_PAIR = ("#2C5D86", "#B45E3E")
BAR_LIKERT = ("#285D78", "#2B7D86", "#D1D7D4", "#A76538", "#8F4F52")
BAR_COMPONENTS = ("#315F89", "#805C80", "#377866", "#9E652E")
BAR_PERIODS = ("#244F73", "#2D6F82", "#3F8276", "#9A743B", "#985B49")

# ---------------------------------------------------------------------------
# Semantic three-color encoding (kept consistent across every chart type):
#   blue = economic, teal/green = environmental, amber/plum = social
# ---------------------------------------------------------------------------
SEMANTIC = {
    "economic": DEFAULT["blue"],
    "environmental": DEFAULT["teal"],
    "social": DEFAULT["amber"],
}

# Neutral surface tokens shared by diagrams.
INK = DEFAULT["ink"]
MUTED = DEFAULT["muted"]
GRID = DEFAULT["grid"]
LIGHT = DEFAULT["light"]
BLUE = DEFAULT["blue"]
TEAL = DEFAULT["teal"]
AMBER = DEFAULT["amber"]
PLUM = DEFAULT["plum"]
