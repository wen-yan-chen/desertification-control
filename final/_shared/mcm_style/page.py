"""Page layout, figure audit and fixed-width export."""

from dataclasses import dataclass
from itertools import combinations
from math import isclose, isfinite
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.text import Text

from .typography import PAGE_WIDTH


def panels(height, rows=1, cols=1, *, width=PAGE_WIDTH, **kwargs):
    """Create a paper-sized panel grid. Axes always has shape (rows, cols)."""
    fig, axes = plt.subplots(rows, cols, figsize=(width, height),
                             layout="constrained", squeeze=False, **kwargs)
    fig.get_layout_engine().set(w_pad=.09, h_pad=.06, wspace=.10, hspace=.13)
    return fig, axes


def head(ax, letter, title):
    """Set a left-aligned subfigure heading."""
    return ax.set_title(f"({letter})  {title}", loc="left")


def grid(ax, axis="y"):
    ax.set_axisbelow(True)
    ax.grid(True, axis=axis)


@dataclass(frozen=True)
class Issue:
    code: str
    detail: str
    severity: str = "error"


def _texts(fig):
    yield from fig.texts
    legends = list(fig.legends)
    for ax in fig.axes:
        if not ax.get_visible():
            continue
        yield from ax.texts
        for loc in ("left", "center", "right"):
            # Matplotlib exposes only the centered title as an Artist.
            if ax.get_title(loc=loc):
                yield {"left": ax._left_title, "center": ax.title, "right": ax._right_title}[loc]
        if ax.axison:
            axes = [ax.xaxis, ax.yaxis] + ([ax.zaxis] if ax.name == "3d" else [])
            for axis in axes:
                if axis.get_visible():
                    yield axis.label
                    yield axis.get_offset_text()
                    # Locators also generate off-range ticks that the axis never draws.
                    for tick in axis._update_ticks():
                        yield tick.label1
                        yield tick.label2
        if ax.get_legend() is not None:
            legends.append(ax.get_legend())
    for legend in legends:
        if legend.get_visible():
            yield legend.get_title()
            yield from legend.get_texts()


def audit(fig, *, width=PAGE_WIDTH, placed_width=None, min_pt=8):
    """Check rendered text size/overflow, and flag possible text collisions.

    placed_width is the physical size in the paper if LaTeX scales the PDF.
    Axis/data/arrow collisions and legibility still need a visual review.
    """
    actual = fig.get_figwidth()
    placed_width = width if placed_width is None else placed_width
    if not all(isfinite(v) and v > 0 for v in (width, placed_width, min_pt)):
        raise ValueError("width, placed_width and min_pt must be positive and finite")
    issues = []
    if not isclose(actual, width, abs_tol=.001, rel_tol=0):
        issues.append(Issue("width", f"{actual:g} in; expected {width:g} in"))
    canvas = fig.canvas
    try:
        probe = FigureCanvasAgg(fig)
        probe.draw()
        renderer = probe.get_renderer()
        frame = fig.bbox
        pt = fig.dpi / 72
        bounds = []
        for artist in dict.fromkeys(_texts(fig)):
            if not artist.get_visible() or not artist.get_text().strip():
                continue
            # A callout's leader is not part of its text footprint.
            box = Text.get_window_extent(artist, renderer=renderer)
            if not all(isfinite(v) for v in box.extents) or box.width <= 0 or box.height <= 0:
                continue
            label = artist.get_text().replace("\n", " / ")
            size = artist.get_fontsize() * placed_width / actual
            if size < min_pt - .001:
                issues.append(Issue("small_text", f"{label!r}: {size:.1f} pt at placement"))
            if (box.x0 < frame.x0 - pt or box.y0 < frame.y0 - pt or
                box.x1 > frame.x1 + pt or box.y1 > frame.y1 + pt):
                issues.append(Issue("off_page", f"{label!r} goes beyond the canvas"))
            bounds.append((label, box))
        for (a, u), (b, v) in combinations(bounds, 2):
            dx = min(u.x1, v.x1) - max(u.x0, v.x0)
            dy = min(u.y1, v.y1) - max(u.y0, v.y0)
            if min(dx, dy) > pt and dx * dy > .18 * min(u.width*u.height, v.width*v.height):
                issues.append(Issue("text_overlap", f"{a!r} / {b!r}", "review"))
    finally:
        fig.set_canvas(canvas)
    return issues


def save_paper(fig, stem, *, width=PAGE_WIDTH, placed_width=None, dpi=300,
               strict=True, overwrite=False, svg=False, title=None):
    """Export a fixed-sized PDF and matching PNG; return paths and audit issues."""
    if not isfinite(dpi) or dpi <= 0:
        raise ValueError("dpi must be positive and finite")
    stem = Path(stem)
    paths = {fmt: stem.parent / f"{stem.name}.{fmt}"
             for fmt in ("pdf", "png", "svg") if fmt != "svg" or svg}
    if not overwrite:
        for path in paths.values():
            if path.exists():
                raise FileExistsError(path)
    with mpl.rc_context({"savefig.bbox": None, "pdf.fonttype": 42,
                         "pdf.use14corefonts": False, "text.usetex": False,
                         "svg.fonttype": "none"}):
        issues = audit(fig, width=width, placed_width=placed_width)
        errors = [item for item in issues if item.severity == "error"]
        if strict and errors:
            raise ValueError("Paper audit failed: " + "; ".join(i.detail for i in errors))
        stem.parent.mkdir(parents=True, exist_ok=True)
        for fmt, path in paths.items():
            metadata = {"Title": title or stem.name} if fmt == "pdf" else None
            fig.savefig(path, format=fmt, dpi=dpi, bbox_inches=None, metadata=metadata)
    return paths, issues
