"""Practice1 accents for a measured quantity already plotted on an axes."""

import numpy as np
from matplotlib.colors import Normalize
from matplotlib.path import Path
from matplotlib.patches import FancyBboxPatch

from . import colormaps, palette as P


def gradient_bar(ax, start, length, position, thickness, *, horizontal=False,
                 cmap="morandi_teal", rounding=0, zorder=2):
    """Draw a signed bar, with dark-to-light ramp in the direction of growth.

    position is the lower (vertical) or left (horizontal) categorical edge
    measured on the orthogonal axis; rounding is in data units. PDF keeps
    text and axes vector while rasterizing the small gradient.
    """
    if not np.isfinite([start, length, position, thickness, rounding]).all():
        raise ValueError("bar coordinates must be finite")
    if thickness <= 0 or rounding < 0:
        raise ValueError("thickness must be positive and rounding nonnegative")
    if length == 0:
        return None
    lo, hi = sorted((start, start + length))
    end = position + thickness
    x0, x1, y0, y1 = ((lo, hi, position, end) if horizontal else (position, end, lo, hi))
    ramp = np.linspace(.12, 1, 256)
    if length < 0:
        ramp = ramp[::-1]
    image = ax.imshow(ramp[None, :] if horizontal else ramp[:, None],
                      extent=(x0, x1, y0, y1), cmap=colormaps.get(cmap),
                      norm=Normalize(0, 1), origin="lower", aspect="auto", zorder=zorder)
    radius = min(rounding, (x1-x0)/2, (y1-y0)/2)
    if radius:
        box = FancyBboxPatch((x0, y0), x1-x0, y1-y0,
                             boxstyle=f"round,pad=0,rounding_size={radius}",
                             transform=ax.transData)
        image.set_clip_path(box)
    return image


def gradient_area(ax, x, y, *, baseline=0, cmap="morandi_teal", alpha=1, zorder=1):
    """Shade between supplied coordinates and a baseline, without smoothing."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if (x.ndim != 1 or len(x) < 2 or x.shape != y.shape or
        not np.isfinite(x).all() or not np.isfinite(y).all() or
        not np.isfinite(baseline) or not 0 <= alpha <= 1 or not np.all(np.diff(x) > 0)):
        raise ValueError("gradient area expects aligned finite values and strictly increasing x")
    # A single polygon can self-intersect at the baseline. Plot separate
    # polygons for the two sides and let fill_between locate crossings.
    if np.all(y == baseline):
        return None
    paths = []
    for mask in (y >= baseline, y <= baseline):
        area = ax.fill_between(x, y, baseline, where=mask, interpolate=True, facecolor="none")
        paths.extend(area.get_paths())
        area.remove()
    image = ax.imshow(np.linspace(.10, 1, 256)[:, None],
                      extent=(x[0], x[-1], min(baseline, y.min()), max(baseline, y.max())),
                      aspect="auto", cmap=colormaps.get(cmap), norm=Normalize(0, 1),
                      origin="lower", alpha=alpha, zorder=zorder)
    image.set_clip_path(Path.make_compound_path(*paths), transform=ax.transData)
    return image


def callout(ax, text, point, *, offset=(10, 12), color=P.MUTED, **kwargs):
    """Annotate a result with a leader anchored to its actual coordinate."""
    return ax.annotate(text, point, xytext=offset, textcoords="offset points",
                       color=color, ha="left" if offset[0] >= 0 else "right",
                       va="bottom" if offset[1] >= 0 else "top",
                       arrowprops={"arrowstyle": "-", "color": color, "lw": .7}, **kwargs)
