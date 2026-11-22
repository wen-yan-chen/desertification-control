"""Paper chart recipes. Pass results in plotting units; no data files are read."""

from dataclasses import dataclass

import numpy as np
from matplotlib.colors import Normalize, TwoSlopeNorm, to_rgba
from matplotlib.patches import Rectangle

from mcm_style import grid, head, panels, palette as P
from mcm_style import colormaps
from mcm_style.accents import callout


def _vector(name, values, size=None, *, missing=False):
    vector = np.asarray(values, dtype=float)
    if vector.ndim != 1 or len(vector) == 0 or (size is not None and len(vector) != size):
        raise ValueError(f"{name}: expected an aligned, nonempty vector")
    if np.isinf(vector).any() or (not missing and np.isnan(vector).any()):
        raise ValueError(f"{name}: unexpected nonfinite value")
    return vector


def _labels(labels, expected=None):
    labels = tuple(map(str, labels))
    if (not labels or any(not label.strip() for label in labels)
            or len(labels) != len(set(labels))
            or (expected is not None and len(labels) != expected)):
        raise ValueError("Expected unique, nonempty labels aligned to the data")
    return labels


def _text_ink(rgba):
    # WCAG relative luminance, applied to the rendered color over white.
    r, g, b, alpha = rgba
    rgb = np.array([r, g, b]) * alpha + (1-alpha)
    rgb = np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)
    lum = rgb @ [.2126, .7152, .0722]
    return "#171717" if (lum+.05)/.058 >= 1.05/(lum+.05) else "white"


def annotated_heatmap(ax, values, *, rows, cols, unit, cmap="academic_teal", limits=None,
                      center=None, fmt=".1f", annotate=True):
    """Draw observed cells in row/column order; NaN is missing and marked NA.

    Use fixed limits across comparable panels. A center requires explicit
    limits that straddle it. Returns the vector QuadMesh for a shared colorbar.
    """
    rows, cols = _labels(rows), _labels(cols)
    values = np.asarray(values, dtype=float)
    if values.shape != (len(rows), len(cols)) or np.isinf(values).any():
        raise ValueError("Heatmap data must match rows × cols and contain no infinities")
    finite = values[np.isfinite(values)]
    if not finite.size:
        raise ValueError("Heatmap has no observed cells")
    if center is not None and limits is None:
        raise ValueError("A diverging center requires explicit limits")
    if limits is None:
        lo, hi = finite.min(), finite.max()
        if lo == hi:
            pad = .01 * max(abs(lo), 1)
            lo, hi = lo-pad, hi+pad
    else:
        lo, hi = limits
    if (not np.isfinite([lo, hi]).all() or not lo < hi or
            finite.min() < lo or finite.max() > hi or
            (center is not None and not lo < center < hi)):
        raise ValueError("Color limits must include the observed cells and straddle any center")
    norm = Normalize(lo, hi) if center is None else TwoSlopeNorm(center, lo, hi)
    colors = colormaps.get(cmap).with_extremes(bad=P.GRID)
    ax.grid(False)
    mesh = ax.pcolormesh(np.arange(len(cols)+1)-.5, np.arange(len(rows)+1)-.5,
                         values, cmap=colors, norm=norm)
    ax.set(xticks=range(len(cols)), xticklabels=cols, yticks=range(len(rows)), yticklabels=rows,
           ylim=(len(rows)-.5, -.5))
    ax.tick_params(length=0)
    if annotate:
        for (i, j), value in np.ndenumerate(values):
            text = "NA" if np.isnan(value) else format(value, fmt)
            shade = colors.get_bad() if np.isnan(value) else colors(norm(value))
            ax.text(j, i, text, ha="center", va="center", color=_text_ink(shade))
    mesh.set_label(unit)
    return mesh


def colorbar(fig, mesh, *, ax, ticks=None, **kwargs):
    """Set a labeled colorbar; keep small heatmaps and their legends vector."""
    bar = fig.colorbar(mesh, ax=ax, ticks=ticks, **kwargs)
    if bar.solids is not None:
        bar.solids.set_rasterized(False)
        bar.solids.set_edgecolor("face")
    bar.set_label(mesh.get_label())
    return bar


def comparison_dots(ax, categories, values, *, xlabel, compare=None, series_labels=None,
                    baseline=None, fmt=".1f", color=P.TEAL):
    """Horizontal dot or paired comparison on a categorical axis.

    baseline is (value, label). Return point artists; use a legend when a
    comparison or a reference is present. Values occupy a small aligned
    column beyond the furthest point/reference, away from the baseline line.
    """
    categories = _labels(categories)
    values = _vector("values", values, len(categories))
    y = np.arange(len(categories))
    if compare is not None:
        compare = _vector("comparison", compare, len(categories))
        if series_labels is None or len(series_labels) != 2:
            raise ValueError("Paired dots require two series labels")
        ax.hlines(y, np.minimum(values, compare), np.maximum(values, compare),
                  color=P.GRID, lw=1.5, zorder=2)
        ax.scatter(compare, y, facecolor="white", edgecolor=P.MUTED, zorder=3,
                   label=series_labels[1])
    if baseline is not None:
        value, label = baseline
        if not np.isfinite(value) or not label:
            raise ValueError("Baseline needs a finite value and a label")
        ax.axvline(value, color=P.MUTED, lw=.9, ls=":", label=label)
    result = ax.scatter(values, y, color=color, zorder=4,
                        label=None if compare is None else series_labels[0])
    bounds = [values]
    if compare is not None:
        bounds.append(compare)
    if baseline is not None:
        bounds.append(np.array([baseline[0]]))
    left = min(part.min() for part in bounds)
    right = max(part.max() for part in bounds)
    span = right-left or max(abs(right), 1)
    if fmt is not None:
        value_column = right + .09*span
        for value, row in zip(values, y):
            ax.text(value_column, row, format(value, fmt), va="center", ha="left",
                    fontsize=8.4, color=P.INK)
        ax.set_xlim(left-.10*span, right+.46*span)
    else:
        ax.margins(x=.10)
    ax.set(yticks=y, yticklabels=categories, ylim=(len(y)-.45, -.55), xlabel=xlabel)
    ax.tick_params(axis="y", length=0)
    grid(ax, "x")
    return result


def comparison_intervals(ax, categories, low, high, estimates, *, xlabel,
                         interval_label, baseline=None, show_legend=True,
                         row_separation=0):
    """Draw reference intervals behind aligned estimates (e.g. solver checks).

    Each Series contains one estimate per categorical row; the supports are
    independent reference intervals, so estimates may fall outside them.
    ``row_separation`` is the total vertical spread of the markers in row
    units (0 to 0.5). Use it for near-coincident series. The band then spans
    the marker positions while its left and right endpoints stay unchanged.
    """
    categories = _labels(categories)
    lo = _vector("interval lower", low, len(categories))
    hi = _vector("interval upper", high, len(categories))
    if (lo > hi).any() or not interval_label:
        raise ValueError("Reference intervals must be ordered and labeled")
    estimates = tuple(estimates)
    _labels(s.label for s in estimates)
    prepared = [(s, _vector(s.label, s.values, len(categories))) for s in estimates]
    if not np.isfinite(row_separation) or not 0 <= row_separation <= .5:
        raise ValueError("row_separation must be between 0 and 0.5")
    if baseline is not None and (not np.isfinite(baseline[0]) or not baseline[1]):
        raise ValueError("Interval baseline needs a finite value and a label")
    rows = np.arange(len(categories))
    spread = row_separation if len(prepared) > 1 else 0
    if spread:
        height = spread+.18
        ax.barh(rows, hi-lo, left=lo, height=height, color=P.BLUE, alpha=.16,
                linewidth=0, label=interval_label, zorder=2)
        ax.vlines(lo, rows-height/2, rows+height/2, color=P.BLUE, alpha=.55, lw=.65, zorder=2)
        ax.vlines(hi, rows-height/2, rows+height/2, color=P.BLUE, alpha=.55, lw=.65, zorder=2)
    else:
        ax.hlines(rows, lo, hi, color=P.MUTED, alpha=.6, lw=1.65, label=interval_label, zorder=2)
    if baseline is not None:
        value, label = baseline
        ax.axvline(value, ls=":", color=P.MUTED, lw=.8, label=label,
                   zorder=2.5 if spread else 2)
    shifts = np.linspace(-spread/2, spread/2, len(prepared))
    for i, ((s, values), shift) in enumerate(zip(prepared, shifts)):
        ax.scatter(values, rows+shift, marker=s.marker or ("o" if i % 2 else "D"), color=s.color,
                   s=26 if i == 0 else 20, facecolor="none" if i == 0 else s.color,
                   linewidth=.95, label=s.label, zorder=3+i)
    ax.set(yticks=rows, yticklabels=categories, xlabel=xlabel, ylim=(len(rows)-.45, -.55))
    ax.tick_params(axis="y", length=0)
    grid(ax, "x")
    if show_legend:
        ax.legend(loc="best")
    return ax


def target_tradeoff(targets, benefit, cost, capacity, *, chosen, benefit_label,
                    cost_label, capacity_label, target_label="Target", screening=None,
                    height=4.8):
    """Pair solved targets with categorical capacity bars and optional screening.

    Targets are ordered labels and chosen is one of them. Dashed segments
    connect solved points in that order, as a guide only. For an unsolved
    target pass NaN in all three vectors. Screening, if used, is
    (x, y, x_label, y_label, threshold, threshold_label).
    """
    targets = _labels(targets)
    benefit, cost, capacity = (_vector(k, v, len(targets), missing=True)
                               for k, v in zip(("benefit", "cost", "capacity"), (benefit, cost, capacity)))
    solved = np.isfinite(benefit)
    if (not np.array_equal(solved, np.isfinite(cost)) or
            not np.array_equal(solved, np.isfinite(capacity)) or (capacity[solved] < 0).any()):
        raise ValueError("Targets must all align; use NaN in all three vectors for an unsolved target")
    idx = targets.index(str(chosen))
    if not solved[idx]:
        raise ValueError("Chosen target must be solved")
    if screening is None:
        fig, axes = panels(height, 2)
        trade, pv = axes[:, 0]
    else:
        x, y, xlabel, ylabel, threshold, threshold_label = screening
        x = _vector("screening x", x)
        y = _vector("screening y", y, len(x))
        if not (np.diff(x) > 0).all() or not np.isfinite(threshold) or not threshold_label:
            raise ValueError("Screening requires increasing x and a labeled finite threshold")
        fig, axes = panels(height, 2, 2, height_ratios=[1.1, 1])
        spec = axes[0, 0].get_gridspec()
        for old in axes[0]:
            old.remove()
        trade = fig.add_subplot(spec[0, :])
        pv, gate = axes[1]
        gate.plot(x, y, "o-", color=P.PLUM, label="Break-even")
        gate.axhline(threshold, color=P.AMBER, lw=1.1, ls="--", label=threshold_label)
        gate.legend(loc="best")
        gate.set(xlabel=xlabel, ylabel=ylabel)
        head(gate, "c", "Screening threshold")
        grid(gate)
    trade.plot(benefit, cost, "o--", color=P.BLUE, lw=1.2)
    trade.scatter(benefit[idx], cost[idx], marker="*", s=100, color=P.TEAL,
                  edgecolors="white", linewidths=.5, zorder=4)
    valid = np.flatnonzero(solved)
    middle = (benefit[solved].min() + benefit[solved].max())/2
    for i in valid:
        dx = 6 if benefit[i] <= middle else -5
        dy = -6 if i == idx else 5
        if i == idx:
            callout(trade, targets[i], (benefit[i], cost[i]), offset=(dx * 2, dy * 2), color=P.TEAL)
        else:
            trade.annotate(targets[i], (benefit[i], cost[i]), (dx, dy), textcoords="offset points",
                           ha="left" if dx > 0 else "right", va="bottom", fontsize=8.4)
    trade.margins(x=.09, y=.21)
    trade.set(xlabel=benefit_label, ylabel=cost_label)
    pv.bar(valid, capacity[solved], color=[P.TEAL if i == idx else P.BLUE for i in valid], width=.64)
    for i in np.flatnonzero(~solved):
        pv.text(i, .025, "NA", transform=pv.get_xaxis_transform(), ha="center", color=P.MUTED)
    for i in np.flatnonzero(solved & (capacity == 0)):
        pv.text(i, .025, "0", transform=pv.get_xaxis_transform(), ha="center", color=P.INK)
    pv.set(xticks=range(len(targets)), xticklabels=targets, xlim=(-.55, len(targets)-.45),
           xlabel=target_label, ylabel=capacity_label)
    pv.set_ylim(bottom=0)
    for axis, letter, title in ((trade, "a", "Solved target trade-off"), (pv, "b", "Capacity by target")):
        head(axis, letter, title)
        grid(axis)
    return fig


@dataclass(frozen=True)
class Series:
    label: str
    values: object
    color: str
    linestyle: str = "-"
    marker: str | None = None
    band: tuple | None = None  # (lower, upper, label)


def scenario_trends(ax, x, series, *, xlabel, ylabel, threshold=None, legend="best"):
    """Draw aligned scenarios with consistent styles, optional bands and threshold.

    x is a shared increasing axis; NaN creates a visible gap. Supply each
    scenario's style once and reuse it across all panels. Bands are drawn
    behind lines; intervals are caller-supplied and must be labeled.
    """
    x = _vector("x", x)
    if not (np.diff(x) > 0).all():
        raise ValueError("Scenario x must be strictly increasing")
    series = tuple(series)
    _labels(s.label for s in series)
    prepared = []
    for s in series:
        to_rgba(s.color)
        y = _vector(s.label, s.values, len(x), missing=True)
        if np.isnan(y).all():
            raise ValueError(f"{s.label}: no observed values")
        band = None
        if s.band is not None:
            low, high, label = s.band
            low = _vector("band lower", low, len(x), missing=True)
            high = _vector("band upper", high, len(x), missing=True)
            if (not label or not np.array_equal(np.isnan(low), np.isnan(high))
                    or np.all(np.isnan(low)) or np.any(low > high)
                    or np.any(np.isnan(y) & np.isfinite(low))):
                raise ValueError("Invalid or unlabeled interval bounds")
            band = (low, high, label)
        prepared.append((s, y, band))
    if threshold is not None:
        value, label = threshold
        if not np.isfinite(value) or not label:
            raise ValueError("Threshold must have a finite value and a label")
        ax.axhline(value, ls=":", color=P.MUTED, lw=1, label=label)
    for s, y, band in prepared:
        if band is not None:
            low, high, label = band
            ax.fill_between(x, low, high, color=s.color, alpha=.14, lw=0, label=label)
        ax.plot(x, y, color=s.color, ls=s.linestyle, marker=s.marker, label=s.label)
    ax.set(xlabel=xlabel, ylabel=ylabel)
    grid(ax)
    if legend is not None:
        ax.legend(loc=legend)
    return ax


def pareto_cloud(points, *, axis_labels, scores=None, score_label=None, selected=None,
                 selected_label="Selected plan", cmap="academic_teal", height=None):
    """Plot supplied 2D/3D candidates as points, without fitting a surface."""
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or not len(pts) or pts.shape[1] not in (2, 3) or not np.isfinite(pts).all():
        raise ValueError("Expected finite points of shape (n, 2) or (n, 3)")
    dim = pts.shape[1]
    labels = _labels(axis_labels, dim)
    score = None if scores is None else _vector("scores", scores, len(pts))
    if score is not None and not score_label:
        raise ValueError("Provide a scale label for colored points")
    selected_pt = None if selected is None else _vector("selected", selected, dim)
    fig, axes = panels(height or (4.45 if dim == 3 else 3.4),
                       subplot_kw={"projection": "3d", "computed_zorder": False} if dim == 3 else None)
    ax = axes[0, 0]
    style = {"color": P.BLUE} if score is None else {"c": score, "cmap": colormaps.get(cmap)}
    if dim == 3:
        style.update(depthshade=False)
    artist = ax.scatter(*pts.T, s=15, alpha=.88, linewidths=0, zorder=2, **style)
    if selected_pt is not None:
        ax.scatter(*([v] for v in selected_pt), marker="*", s=170, color=P.INK,
                   edgecolors="white", linewidths=.95, zorder=5, label=selected_label)
        ax.legend(loc="upper left")
    ax.set(xlabel=labels[0], ylabel=labels[1])
    if dim == 3:
        ax.set_zlabel(labels[2])
        ax.view_init(elev=23, azim=-58)
        ax.set_box_aspect((1.2, 1, .78), zoom=.85)
        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis.pane.fill = False
    else:
        grid(ax)
    if score is not None:
        bar = fig.colorbar(artist, ax=ax, pad=.05 if dim == 2 else .095, shrink=.72)
        bar.set_label(score_label)
    return fig


def radar_profile(labels, profiles, *, height=3.7):
    """Compare normalized benefit-oriented scores in [0, 1], never polygon area."""
    labels = _labels(labels)
    if not 3 <= len(labels) <= 10:
        raise ValueError("Radar needs 3–10 axes")
    profiles = tuple(profiles)
    _labels(s.label for s in profiles)
    prepared = [(s, _vector(s.label, s.values, len(labels))) for s in profiles]
    if any(((v < 0) | (v > 1)).any() or s.band is not None for s, v in prepared):
        raise ValueError("Radar needs normalized scores without intervals")
    fig, axes = panels(height, subplot_kw={"projection": "polar"})
    ax = axes[0, 0]
    ang = np.linspace(0, 2*np.pi, len(labels), endpoint=False)
    ax.set_theta_offset(np.pi/2)
    ax.set_theta_direction(-1)
    ax.set(xticks=ang, xticklabels=labels, ylim=(0, 1), yticks=[.25, .5, .75, 1])
    # Ring values belong in a compact key outside the polygon: any spoke can
    # carry a data edge or marker, so an internal radial label is fragile.
    ax.set_yticklabels([])
    fig.text(.025, .96, "Center 0 · rings 0.25 / 0.50 / 0.75 / 1.00", color=P.MUTED,
             fontsize=8.4, va="top")
    ax.tick_params(axis="x", pad=9)
    for angle, label in zip(ang, ax.get_xticklabels()):
        horizontal = np.sin(angle)
        vertical = np.cos(angle)
        label.set_ha("left" if horizontal > .15 else "right" if horizontal < -.15 else "center")
        label.set_va("bottom" if vertical > .15 else "top" if vertical < -.15 else "center")
    ax.grid(True)
    for s, v in prepared:
        ax.plot(np.r_[ang, ang[0]], np.r_[v, v[0]], color=s.color, ls=s.linestyle,
                marker=s.marker, label=s.label)
        ax.fill(ang, v, color=s.color, alpha=.07)
    fig.legend(loc="outside lower center", ncols=min(len(profiles), 4))
    return fig


# ---------------------------------------------------------------------------
# Promoted from FigureTraining toolkit (1.4.0): signed sensitivity, tornado,
# break-even / dual-axis, feasible bands and 3D columns. All functions take
# caller-supplied data only; no project files are read.
# ---------------------------------------------------------------------------

_SIGN = (P.BLUE, "#B45E3E")  # positive / negative response, from BAR_PAIR


def signed_bars(ax, labels, values, *, xlabel, fmt="+.2f", sort_by="magnitude"):
    """Horizontal signed bars for elasticities or directional effects.

    Sorted by absolute value by default; the sign selects the bar color and
    the label side. This is a screening view: magnitudes are comparable,
    signs are directional only (see FigureTraining 10).
    """
    labels = _labels(labels)
    values = _vector("values", values, len(labels))
    if sort_by not in ("magnitude", "input"):
        raise ValueError("sort_by must be 'magnitude' or 'input'")
    order = (np.argsort(-np.abs(values)) if sort_by == "magnitude"
             else np.arange(len(labels)))
    lo, hi = min(values.min(), 0), max(values.max(), 0)
    span = hi - lo or 1
    ax.axvline(0, color=P.MUTED, lw=.9, zorder=1)
    for rank, i in enumerate(order):
        value = values[i]
        color = _SIGN[0] if value >= 0 else _SIGN[1]
        ax.barh(rank, value, color=color, height=.5, zorder=3)
        offset = .035*span if value >= 0 else -.035*span
        ax.text(value + offset, rank, format(value, fmt), va="center",
                ha="left" if value >= 0 else "right", fontsize=8.4, color=P.INK)
    ax.set(yticks=np.arange(len(order)), yticklabels=[labels[i] for i in order],
           xlim=(lo - .22*span, hi + .28*span), ylim=(len(order)-.55, -.55),
           xlabel=xlabel)
    ax.tick_params(axis="y", length=0)
    grid(ax, "x")
    return ax


def tornado(ax, labels, low, high, *, baseline, xlabel, fmt=".1f", sort_by="range"):
    """One-at-a-time tornado: bars span each input's low-to-high output.

    Bars are sorted by their range; the dashed line marks the baseline
    output. Bar color follows the high side relative to the baseline so a
    directionally consistent input stays one color. Only caller-computed
    scenario outputs are plotted; no model is re-run here.
    """
    labels = _labels(labels)
    low = _vector("low", low, len(labels))
    high = _vector("high", high, len(labels))
    if (low > high).any():
        raise ValueError("Tornado low bounds must not exceed high bounds")
    if not np.isfinite(baseline):
        raise ValueError("Tornado baseline must be finite")
    if sort_by not in ("range", "input"):
        raise ValueError("sort_by must be 'range' or 'input'")
    order = (np.argsort(-(high - low)) if sort_by == "range"
             else np.arange(len(labels)))
    y = np.arange(len(labels))
    for rank, i in enumerate(order):
        ax.barh(rank, high[i] - low[i], left=low[i], height=.48,
                color=_SIGN[0] if high[i] >= baseline else _SIGN[1],
                alpha=.9, zorder=3)
        ax.text(low[i] - .012*(high.max()-low.min() or 1), rank, format(low[i], fmt),
                va="center", ha="right", fontsize=8.0, color=P.MUTED)
        ax.text(high[i] + .012*(high.max()-low.min() or 1), rank, format(high[i], fmt),
                va="center", ha="left", fontsize=8.0, color=P.MUTED)
    ax.axvline(baseline, color=P.INK, lw=1.05, ls="--", zorder=2)
    ax.set(yticks=y, yticklabels=[labels[i] for i in order],
           ylim=(len(order)-.55, -.55), xlabel=xlabel)
    ax.tick_params(axis="y", length=0)
    ax.margins(x=.06)
    grid(ax, "x")
    return ax


def break_even_points(x, revenue, cost):
    """Linear interpolation of revenue-cost crossings on increasing x."""
    x, revenue, cost = (np.asarray(v, dtype=float) for v in (x, revenue, cost))
    if (x.ndim != 1 or len(x) < 2 or revenue.shape != x.shape
            or cost.shape != x.shape or not np.isfinite(x).all()
            or not np.isfinite(revenue).all() or not np.isfinite(cost).all()
            or np.any(np.diff(x) <= 0)):
        raise ValueError("x, revenue and cost must be aligned finite arrays; x must increase")
    d = revenue - cost
    roots = []
    for i in range(len(x)-1):
        if d[i] == 0:
            roots.append(float(x[i]))
        elif d[i]*d[i+1] < 0:
            roots.append(float(x[i] - d[i]*(x[i+1]-x[i])/(d[i+1]-d[i])))
    if d[-1] == 0:
        roots.append(float(x[-1]))
    return np.asarray(roots)


def break_even_curves(x, revenue, cost, *, xlabel, ylabel, note=None, height=3.65):
    """Revenue, cost and net benefit on one unit with marked break-even points.

    The shaded band shows where revenue covers cost; the best net point is
    annotated separately because "break-even" and "max net" answer different
    questions. ``note`` should carry the unit and any scenario caveats.
    """
    x = _vector("x", x)
    revenue = _vector("revenue", revenue, len(x))
    cost = _vector("cost", cost, len(x))
    if not (np.diff(x) > 0).all():
        raise ValueError("Break-even x must be strictly increasing")
    roots = break_even_points(x, revenue, cost)
    net = revenue - cost
    fig, axes = panels(height)
    ax = axes[0, 0]
    viable = net >= 0
    ax.fill_between(x, cost, revenue, where=viable, interpolate=True,
                    color=P.TEAL, alpha=.15, lw=0, label="revenue ≥ cost")
    ax.plot(x, revenue, color=P.TEAL, lw=1.8, label="Revenue")
    ax.plot(x, cost, color=P.BLUE, lw=1.8, label="Cost")
    ax.plot(x, net, color=_SIGN[1], lw=1.8, label="Net benefit")
    ax.axhline(0, color=P.MUTED, lw=.7)
    for root in roots:
        value = float(np.interp(root, x, revenue))
        ax.plot(root, value, "o", ms=4.2, mfc="white", mec=P.INK, mew=1.0, zorder=5)
        ax.vlines(root, 0, value, color=P.MUTED, lw=.75, ls=(0, (2.5, 2.5)), zorder=2)
    best = int(np.argmax(net))
    ax.plot(x[best], net[best], "o", ms=4.6, color=_SIGN[1], zorder=6)
    ax.annotate(f"Max net  {net[best]:.1f}", (x[best], net[best]),
                xytext=(x[best] + (x[-1]-x[0])*.05, net[best] + (net.max()-net.min())*.10),
                fontsize=8.2, color=_SIGN[1], arrowprops=dict(arrowstyle="-",
                color=_SIGN[1], lw=.7))
    ax.set(xlabel=xlabel, ylabel=ylabel)
    grid(ax)
    ax.legend(loc="best", frameon=False)
    if note:
        fig.text(.05, .02, note, fontsize=8.0, color=P.MUTED)
    return fig


def dual_axis_lines(x, primary, secondary, *, primary_label, secondary_label,
                    xlabel, ylabel_primary, ylabel_secondary, note=None, height=3.65):
    """Two y-axes for two units, with the axes colored to match their series.

    A crossing on two different scales moves when limits change, so it is
    never presented as an optimum; pass ``note`` to say so explicitly.
    """
    x = _vector("x", x)
    primary = _vector(primary_label, primary, len(x))
    secondary = _vector(secondary_label, secondary, len(x))
    if not (np.diff(x) > 0).all():
        raise ValueError("Dual-axis x must be strictly increasing")
    color1, color2 = P.BLUE, _SIGN[1]
    fig, axes = panels(height)
    ax = axes[0, 0]
    ax.plot(x, primary, color=color1, lw=1.9, label=primary_label)
    ax.set(xlabel=xlabel, ylabel=ylabel_primary)
    ax.yaxis.label.set_color(color1)
    ax.tick_params(axis="y", colors=color1)
    ax.spines["left"].set_color(color1)
    ax.set_axisbelow(True)
    grid(ax, "y")
    twin = ax.twinx()
    twin.plot(x, secondary, color=color2, lw=1.9, label=secondary_label)
    twin.set_ylabel(ylabel_secondary, color=color2)
    twin.tick_params(axis="y", colors=color2)
    twin.spines["right"].set_color(color2)
    twin.spines[["top", "left"]].set_visible(False)
    twin.grid(False)
    lines = ax.get_lines() + twin.get_lines()
    ax.legend(lines, [line.get_label() for line in lines], loc="best", frameon=False)
    if note:
        fig.text(.05, .02, note, fontsize=8.0, color=P.MUTED)
    return fig


def feasible_band(ax, x, lower, upper, *, samples=None, observed=None,
                  xlabel, ylabel, legend=True):
    """Shade a constraint-defined feasible band with optional points.

    The band must come from explicit constraints, never from a convex hull or
    an interpolation of the samples. ``observed`` points get a star marker.
    """
    x = _vector("x", x)
    lower = _vector("lower", lower, len(x))
    upper = _vector("upper", upper, len(x))
    if not (np.diff(x) > 0).all():
        raise ValueError("Feasible band x must be strictly increasing")
    if (lower > upper).any():
        raise ValueError("Feasible band lower bounds must not exceed upper bounds")
    ax.fill_between(x, lower, upper, color=P.TEAL, alpha=.16, lw=0,
                    label="Feasible region")
    ax.plot(x, lower, color=P.TEAL, lw=.95)
    ax.plot(x, upper, color=P.TEAL, lw=.95)
    if samples is not None:
        sx = _vector("samples x", samples[0])
        sy = _vector("samples y", samples[1], len(sx))
        ax.scatter(sx, sy, s=9, c=P.BLUE, alpha=.7, linewidths=0, zorder=3,
                   label="Feasible samples")
    if observed is not None:
        ox = _vector("observed x", observed[0])
        oy = _vector("observed y", observed[1], len(ox))
        ax.scatter(ox, oy, s=68, marker="*", c=_SIGN[1], edgecolors="white",
                   linewidths=.65, zorder=5, label="Observed points")
    ax.set(xlabel=xlabel, ylabel=ylabel)
    grid(ax)
    if legend:
        ax.legend(loc="best", frameon=False)
    return ax


def three_d_columns(values, *, rows, cols, unit, xlabel="", ylabel="", title=None,
                    detail=None, note=None, cmap="academic_teal", limits=None,
                    height=4.05, elev=27, azim=-56, orthographic=True):
    """3D columns over a discrete rows × cols grid with an optional value table.

    One metric and one unit for every column; color only repeats the height.
    No surface or in-between values are inferred. The orthographic side table
    prints the same grid values so short or hidden columns stay readable.
    """
    rows, cols = _labels(rows), _labels(cols)
    values = np.asarray(values, dtype=float)
    if values.shape != (len(rows), len(cols)) or not np.isfinite(values).all():
        raise ValueError("3D columns need a finite rows × cols matrix")
    if limits is None:
        lo, hi = min(0.0, values.min()), values.max()*1.02
    else:
        lo, hi = limits
        if (not np.isfinite([lo, hi]).all() or not lo < hi
                or values.min() < lo or values.max() > hi):
            raise ValueError("3D limits must be ordered and cover all columns")
    norm = Normalize(lo, hi)
    colors = colormaps.get(cmap)
    fig, axes = panels(height, subplot_kw={"projection": "3d", "computed_zorder": False})
    ax = axes[0, 0]
    xx, yy = np.meshgrid(np.arange(len(cols)), np.arange(len(rows)))
    xpos, ypos = xx.ravel() - .33, yy.ravel() - .33
    heights = values.ravel()
    ax.bar3d(xpos, ypos, np.zeros(heights.size), .66, .66, heights,
             color=colors(norm(heights)), shade=True, edgecolor="#F7FAFA",
             linewidth=.45, zsort="average")
    ax.view_init(elev=elev, azim=azim)
    ax.set(xlim=(-.6, len(cols)-.4), ylim=(-.6, len(rows)-.4), zlim=(lo, hi),
           xlabel=xlabel, ylabel=ylabel, zlabel=unit)
    ax.set_xticks(range(len(cols)), cols)
    ax.set_yticks(range(len(rows)), rows)
    ax.tick_params(labelsize=8, pad=0)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.fill = False
        axis.pane.set_edgecolor((1, 1, 1, 0))
        axis._axinfo["grid"].update({"color": (.78, .82, .82, .65), "linewidth": .55})
        axis.line.set_color("#8B9A9D")
        axis.label.set_size(8)
    ax.set_box_aspect((1.15, 1.0, .78), zoom=.92)
    if title:
        fig.text(.07, .955, title, fontsize=10.8, weight="bold", color=P.INK, va="top")
    if detail:
        fig.text(.07, .886, detail, fontsize=8.0, color=P.MUTED, va="top")
    if orthographic:
        table = fig.add_axes((.73, .26, .24, .47))
        table.set(xlim=(-.5, len(cols)-.5), ylim=(len(rows)-.5, -.5))
        table.set_aspect("equal")
        for (i, j), value in np.ndenumerate(values):
            table.add_patch(Rectangle((j-.5, i-.5), 1, 1, facecolor=colors(norm(value)),
                                      edgecolor="white", linewidth=1.0))
        table.set_xticks(range(len(cols)), cols, fontsize=8)
        table.set_yticks(range(len(rows)), rows, fontsize=8)
        table.tick_params(length=0, pad=2)
        table.set_xlabel("column", fontsize=8, labelpad=2)
        table.set_ylabel("row", fontsize=8, labelpad=2)
        for spine in table.spines.values():
            spine.set_visible(False)
        for (i, j), value in np.ndenumerate(values):
            table.text(j, i, format(value, ".1f"), ha="center", va="center",
                       fontsize=8.0, weight="bold", color=_text_ink(colors(norm(value))))
        fig.text(.73, .78, f"Exact {unit}, discrete", fontsize=8.0, weight="bold",
                 color=P.INK)
    if note:
        fig.text(.07, .05, note, fontsize=8.0, color=P.MUTED)
    return fig


def recovery_gap(ax, time, ever, current, *, xlabel, unit,
                 labels=("Ever below threshold", "Currently below threshold", "Recovered")):
    """Plot two nested amounts on the same cohort and mark their last paired difference."""
    x = _vector("time", time)
    ever = _vector("ever", ever, len(x), missing=True)
    current = _vector("current", current, len(x), missing=True)
    labels = _labels(labels, 3)
    paired = np.isfinite(ever) & np.isfinite(current)
    if np.any(np.diff(x) <= 0) or not paired.any():
        raise ValueError("time must increase and contain a paired observation")
    if (np.any(np.diff(ever[np.isfinite(ever)]) < 0) or np.any(current < 0)
            or np.any(ever < 0) or np.any(current[paired] > ever[paired])):
        raise ValueError("ever must be cumulative and both amounts must be nested and nonnegative")
    ax.plot(x, ever, color=P.PLUM, label=labels[0])
    ax.plot(x, current, color=P.AMBER, linestyle="--", label=labels[1])
    ax.fill_between(x, current, ever, where=paired, color=P.TEAL, alpha=.18, label=labels[2])
    i = np.flatnonzero(paired)[-1]
    ax.plot([x[i], x[i]], [current[i], ever[i]], color=P.TEAL, linewidth=1)
    ax.annotate(f"{ever[i] - current[i]:,.2f} {unit}", (x[i], (ever[i] + current[i]) / 2),
                xytext=(-5, 0), textcoords="offset points", ha="right", va="center",
                color=P.INK, bbox=dict(facecolor="white", alpha=.85, edgecolor="none", pad=1))
    ax.set(xlabel=xlabel, ylabel=unit, ylim=(0, None))
    ax.legend()
    return ax


def quota_pressure(usage, period_caps, annual_caps, *, years, periods, unit):
    """Compare annual totals, the tightest year's profile and period utilisation.

    usage is years × periods. Period caps may be common to all years or aligned
    to usage. Annual caps may be scalar or one per year. NaN means unknown.
    A closed period with demand takes priority when selecting the detail year.
    """
    usage = np.asarray(usage, dtype=float)
    years, periods = _labels(years), _labels(periods)
    if usage.shape != (len(years), len(periods)):
        raise ValueError("usage must align to years × periods")
    caps = np.asarray(period_caps, dtype=float)
    annual = np.asarray(annual_caps, dtype=float)
    if caps.shape not in {(len(periods),), usage.shape} or annual.shape not in {(), (len(years),)}:
        raise ValueError("cap dimensions do not match usage")
    caps = np.broadcast_to(caps, usage.shape)
    annual = np.broadcast_to(annual, (len(years),))
    if any(np.isinf(a).any() or (a < 0).any() for a in (usage, caps, annual)):
        raise ValueError("usage and caps must be nonnegative or NaN")
    ratio = np.full_like(usage, np.nan)
    np.divide(usage, caps, out=ratio, where=caps > 0)
    breach = (caps == 0) & (usage > 0)
    priority = np.where(breach, np.inf, ratio)
    if np.isnan(priority).all():
        raise ValueError("no comparable period with a positive cap or unmet demand")
    year, period = np.unravel_index(np.nanargmax(priority), usage.shape)
    fig, axes = panels(7.3, 3)
    totals, detail, matrix = axes[:, 0]
    y, p = np.arange(len(years)), np.arange(len(periods))
    totals.bar(y, usage.sum(axis=1), color=P.BLUE, label="Total use")
    totals.plot(y, annual, "--o", color=P.AMBER, label="Annual cap")
    totals.set(xticks=y, xticklabels=years, ylabel=unit)
    totals.legend()
    head(totals, "a", "Annual use and cap")
    detail.bar(p, usage[year], color=P.BLUE, label="Period use")
    detail.stairs(caps[year], np.arange(len(p) + 1) - .5, baseline=None,
                  color=P.AMBER, linestyle="--", label="Period cap")
    detail.set(xticks=p, xticklabels=periods, ylabel=unit)
    detail.legend()
    peak = "use with zero cap" if breach[year, period] else f"{ratio[year, period]:.1%} of cap"
    head(detail, "b", f"Year {years[year]} · {periods[period]}: {peak}")
    cmap = colormaps.get("academic_teal").with_extremes(bad=P.GRID)
    finite = ratio[np.isfinite(ratio)]
    maximum = max(100., 100 * finite.max()) if finite.size else 100.
    mesh = matrix.imshow(ratio.T * 100, aspect="auto", origin="upper", interpolation="nearest",
                         cmap=cmap, vmin=0, vmax=maximum)
    matrix.set(xticks=y, xticklabels=years, yticks=p, yticklabels=periods, xlabel="Year")
    matrix.plot(year, period, "s", markerfacecolor="none", markeredgecolor=P.INK, markersize=9)
    for yi, pi in zip(*np.where(breach)):
        matrix.text(yi, pi, "×", ha="center", va="center", color=P.INK)
    head(matrix, "c", "Period use as a share of cap")
    fig.colorbar(mesh, ax=matrix, label="% of cap")
    if (~np.isfinite(ratio)).any():
        matrix.set_xlabel("Year · Grey: missing or zero cap" + ("   ×: use with zero cap" if breach.any() else ""))
    return fig
