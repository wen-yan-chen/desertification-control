"""Unified adapter over the heterogeneous training-function interfaces.

The validated scripts were written in three styles:

* ``fig``      -- return a matplotlib Figure directly.
* ``tuple``    -- return ``(fig, ...extra)``; the Figure is the first element.
* ``selfwrite``-- write outputs internally and return ``None`` (batch/ReportLab).

This module normalizes the first two (the common case for data charts) so callers
always receive a Figure. ``selfwrite`` functions are listed explicitly and are
meant to be run as batch entry points, not adapted.
"""

from . import get

# Modules whose public chart functions return a Figure directly.
FIG_MODULES = [
    "templates", "workflow01", "concept03", "heatmap08",
    "feasible09", "seasonal04", "three_d07_style",
]

# Modules whose chart functions return a (Figure, ...) tuple.
TUPLE_MODULES = ["tradeoff05", "radar06", "three_d07"]

# Modules whose chart functions write their own files and return None.
SELFWRITE_MODULES = ["sensitivity10", "bars11", "demo_figures",
                     "demo_figures2", "mcm_figures"]


def is_figure(obj):
    """Return True if the object looks like a matplotlib Figure."""
    return hasattr(obj, "savefig") and hasattr(obj, "axes")


def first_figure(result):
    """Extract a Figure from a Figure or a (Figure, ...) result."""
    if is_figure(result):
        return result
    if isinstance(result, (tuple, list)) and result and is_figure(result[0]):
        return result[0]
    if result is None:
        raise ValueError(
            "function returned None (self-writing batch style); call it directly "
            "instead of requesting a Figure")
    raise TypeError(f"cannot locate a Figure in result of type {type(result)}")


def call_figure(module_name, func_name, *args, **kwargs):
    """Call a module function and always return its Figure.

    Works for the ``fig`` and ``tuple`` styles. ``selfwrite`` modules raise a
    clear error directing the caller to run them directly.
    """
    if module_name in SELFWRITE_MODULES:
        raise ValueError(
            f"{module_name} is a self-writing module; call "
            f"lib.get({module_name!r}).{func_name}(...) directly and read its "
            "output files, or use a fig-returning module for the same chart type")
    module = get(module_name)
    result = getattr(module, func_name)(*args, **kwargs)
    return first_figure(result)


def interface_of(module_name):
    """Return the interface style name for a module."""
    if module_name in FIG_MODULES:
        return "fig"
    if module_name in TUPLE_MODULES:
        return "tuple"
    if module_name in SELFWRITE_MODULES:
        return "selfwrite"
    return "unknown"
