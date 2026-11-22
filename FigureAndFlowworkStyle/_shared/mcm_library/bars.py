"""Data-parameterized bars distilled from FigureTraining 11.

All values arrive already in plotting units. Composition values are percentages
and are never silently normalized. These functions draw on the supplied Axes
and return it; callers own titles, captions and export.
"""

from dataclasses import dataclass

import numpy as np
from matplotlib.colors import to_rgba

from mcm_style import palette as P


@dataclass(frozen=True)
class BarSeries:
    label: str
    values: object
    color: str | None = None


def _names(values, expected=None):
    names = tuple(map(str, values))
    if (not names or any(not name.strip() for name in names)
            or len(set(names)) != len(names)
            or (expected is not None and len(names) != expected)):
        raise ValueError("Expected unique, nonempty labels aligned to values")
    return names


def _palette(colors, count, default):
    colors = tuple(default if colors is None else colors)
    if len(colors) != count:
        raise ValueError("Provide one color per segment or series")
    for color in colors:
        to_rgba(color)
    return colors


def _ink(color):
    r, g, b, alpha = to_rgba(color)
    rgb = np.array([r, g, b])*alpha + (1-alpha)
    rgb = np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)
    luminance = rgb @ [.2126, .7152, .0722]
    return "white" if 1.05/(luminance+.05) >= 4.5 else P.INK


def composition_bars(ax, labels, shares, *, segments, orientation="horizontal",
                     colors=None, show_values=True, min_label_pct=10,
                     total_tolerance=.15, axis_label="Share (%)", fmt=".0f"):
    """Draw 100% composition bars, with aligned inputs and a fixed 0–100 axis.

    ``shares`` has one row per label and one column per segment, in percentage
    points. Rounded source percentages may sum to 100 ± total_tolerance;
    neither values nor bar lengths are rescaled. Small segments omit in-bar
    labels so callers can place them in a table/caption instead.
    """
    labels, segments = _names(labels), _names(segments)
    values = np.asarray(shares, dtype=float)
    if (values.shape != (len(labels), len(segments)) or
            not np.isfinite(values).all() or (values < 0).any() or
            (values > 100).any()):
        raise ValueError("shares must be finite nonnegative percentages aligned to labels × segments")
    if (not np.isfinite(total_tolerance) or total_tolerance < 0 or
            not np.all(np.abs(values.sum(axis=1)-100) <= total_tolerance)):
        raise ValueError("Every composition row must total 100% within tolerance")
    if orientation not in ("horizontal", "vertical"):
        raise ValueError("orientation must be horizontal or vertical")
    if not np.isfinite(min_label_pct) or min_label_pct < 0:
        raise ValueError("min_label_pct must be nonnegative")
    if colors is None:
        default = P.BAR_LIKERT if len(segments) == 5 else (
            P.BAR_COMPONENTS if len(segments) == 4 else P.DEFAULT_CYCLE[:len(segments)])
    else:
        default = ()
    colors = _palette(colors, len(segments), default)
    positions = np.arange(len(labels))
    cumulative = np.zeros(len(labels), dtype=float)
    for j, (name, color) in enumerate(zip(segments, colors)):
        amount = values[:, j]
        kw = dict(color=color, edgecolor="white", linewidth=.7, label=name, zorder=2)
        if orientation == "horizontal":
            ax.barh(positions, amount, left=cumulative, height=.66, **kw)
        else:
            ax.bar(positions, amount, bottom=cumulative, width=.66, **kw)
        if show_values:
            for i, value in enumerate(amount):
                if value < min_label_pct:
                    continue
                center = cumulative[i]+value/2
                x, y = (center, positions[i]) if orientation == "horizontal" else (positions[i], center)
                ax.text(x, y, format(value, fmt)+"%", ha="center", va="center",
                        color=_ink(color), fontsize=8, fontweight="bold", zorder=3)
        cumulative += amount
    ax.grid(False)
    ax.tick_params(axis="y" if orientation == "horizontal" else "x", length=0)
    if orientation == "horizontal":
        ax.set(xlim=(0, 100), yticks=positions, yticklabels=labels, xlabel=axis_label)
        ax.invert_yaxis()
    else:
        ax.set(ylim=(0, 100), xticks=positions, xticklabels=labels, ylabel=axis_label)
    return ax


def grouped_bars(ax, categories, series, *, value_label, orientation="vertical",
                 show_values=True, fmt=".2f", maximum=None, legend=True):
    """Draw one to five nonnegative aligned series on a zero baseline.

    Supply a meaningful ``value_label`` with units. Bar position and legend
    duplicate color encoding. Missing values are rejected; use separate
    categories or a point plot if NA has a scientific meaning.
    """
    categories = _names(categories)
    series = tuple(series)
    _names((s.label for s in series))
    if len(series) > 5:
        raise ValueError("More than five grouped series need faceting or another chart")
    if orientation not in ("horizontal", "vertical"):
        raise ValueError("orientation must be horizontal or vertical")
    if not value_label or not str(value_label).strip():
        raise ValueError("value_label must include the metric and its unit")
    values = np.asarray([s.values for s in series], dtype=float)
    if (values.shape != (len(series), len(categories)) or
            not np.isfinite(values).all() or (values < 0).any()):
        raise ValueError("Series need aligned, finite nonnegative values")
    color_default = P.BAR_PAIR if len(series) == 2 else P.BAR_PERIODS[:len(series)]
    colors = tuple(s.color if s.color is not None else color_default[i]
                   for i, s in enumerate(series))
    for color in colors:
        to_rgba(color)
    top = float(values.max())
    if maximum is not None and (not np.isfinite(maximum) or maximum < top or maximum <= 0):
        raise ValueError("maximum must be positive and include every value")
    limit = float(maximum) if maximum is not None else (top*1.22 if show_values else top*1.08)
    if limit == 0:
        limit = 1.0
    positions = np.arange(len(categories))
    width = .78/len(series)
    for i, (s, color, row) in enumerate(zip(series, colors, values)):
        offset = (i-(len(series)-1)/2)*width
        centers = positions+offset
        if orientation == "vertical":
            ax.bar(centers, row, width=width*.88, color=color, label=s.label, zorder=2)
        else:
            ax.barh(centers, row, height=width*.88, color=color, label=s.label, zorder=2)
        if show_values:
            for center, value in zip(centers, row):
                if orientation == "vertical":
                    inside = value > 0 and value+limit*.055 >= limit
                    x = center
                    y = value-limit*.015 if inside else value+limit*.012
                    ha, va = "center", "top" if inside else "bottom"
                else:
                    inside = value > 0 and value+limit*.055 >= limit
                    x = value-limit*.012 if inside else value+limit*.012
                    y = center
                    ha, va = ("right" if inside else "left"), "center"
                ax.text(x, y, format(value, fmt), ha=ha, va=va,
                        color=_ink(color) if inside else P.INK, fontsize=8, zorder=3)
    ax.grid(False)
    if orientation == "vertical":
        ax.set(ylim=(0, limit), xticks=positions, xticklabels=categories,
               xlim=(-.55, len(categories)-.45), ylabel=value_label)
        ax.tick_params(axis="x", length=0)
    else:
        ax.set(xlim=(0, limit), yticks=positions, yticklabels=categories,
               ylim=(-.55, len(categories)-.45), xlabel=value_label)
        ax.invert_yaxis()
        ax.tick_params(axis="y", length=0)
    if legend and len(series) > 1:
        ax.legend(loc="upper right", ncol=min(len(series), 5))
    return ax
