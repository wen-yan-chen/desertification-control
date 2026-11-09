"""
MCM/ICM figure template
=======================
One consistent style + one function per chart type commonly used in MCM papers.
Every function takes your data as arguments; the __main__ block shows example data.

Run: python mcm_figures.py
Outputs: ../Images/<category>/*.pdf (vector) and *.png (300 dpi).
The example block uses synthetic tourism data; these are style demos, not results.

Chart types (mirrors the Juneau paper, plus a few that judges like):
  fig_bar_trend          Fig 1  style: yearly bars with value labels
  fig_flowchart          Fig 2  style: "Our Work" pipeline of boxes and arrows
  fig_fit                4.1    style: data points + fitted curve + residuals
  fig_policy_curve       Fig 4/6 style: model curve vs ideal line vs capacity cap
  fig_composition        Fig 5  style: share of each component (donut + sorted bars)
  fig_pareto_2d          Fig 8  style: Pareto front, chosen solution highlighted
  fig_pareto_3d          Fig 8  style: 3D Pareto surface
  fig_convergence        NSGA-II / GA convergence (hypervolume / best fitness)
  fig_sensitivity_lines  Fig 9  style: one-at-a-time sensitivity, small multiples
  fig_tornado            sensitivity ranking (cleaner alternative to Fig 9)
  fig_sensitivity_heat   Fig 10 style: two-parameter heatmap grid
"""
from pathlib import Path
from figure_paths import output_path
import numpy as np
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# --------------------------------------------------------------------------
# 1. GLOBAL STYLE  (change once, every figure follows)
# --------------------------------------------------------------------------
PALETTE = {
    "main":   "#2F5D8A",   # navy  - primary series
    "accent": "#D1495B",   # red   - highlight / "actual" / chosen point
    "second": "#EDAE49",   # amber - second series
    "third":  "#00798C",   # teal
    "fourth": "#66A182",   # green
    "grey":   "#8C8C8C",   # reference lines, de-emphasised data
    "light":  "#DCE6F0",   # box fills
}
SERIES = [PALETTE[k] for k in ("main", "accent", "second", "third", "fourth", "grey")]

FULL_W = 6.3     # inches: full text width of an MCM page (A4 / Letter, ~2.5 cm margins)
HALF_W = 3.1

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
    "mathtext.fontset": "stix",            # Times-like math: $\lambda_1$, $y_5$
    "font.size": 10, "axes.titlesize": 10.5, "axes.labelsize": 10,
    "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.fontsize": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.8, "axes.edgecolor": "#333333",
    "axes.grid": True, "grid.color": "#E5E5E5", "grid.linewidth": 0.6,
    "axes.axisbelow": True, "axes.prop_cycle": mpl.cycler(color=SERIES),
    "legend.frameon": False, "lines.linewidth": 1.8,
    "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
    "pdf.fonttype": 42,                    # editable text in PDF
})

OUT = Path(__file__).resolve().parent.parent / "Images"


def save(fig, name):
    """Save as vector PDF (best for LaTeX) and 300-dpi PNG (best for Word)."""
    fig.savefig(output_path("template", name, "pdf"))
    fig.savefig(output_path("template", name, "png"))
    plt.close(fig)
    print("saved", name)


# --------------------------------------------------------------------------
# 2. CHART FUNCTIONS
# --------------------------------------------------------------------------
def fig_bar_trend(labels, values, ylabel, source=None, highlight=None, name="bar_trend"):
    """Yearly bars with value labels. `highlight` = index of the bar to colour as accent;
    np.nan values are drawn as an explicit gap (e.g. 2020: no data)."""
    fig, ax = plt.subplots(figsize=(FULL_W, 2.8))
    colors = [PALETTE["accent"] if i == highlight else PALETTE["main"] for i in range(len(values))]
    bars = ax.bar(labels, np.nan_to_num(values), color=colors, width=0.62)
    for b, v, lab in zip(bars, values, labels):
        if np.isnan(v):
            ax.text(b.get_x() + b.get_width() / 2, 0, "no data", ha="center", va="bottom",
                    fontsize=8, color=PALETTE["grey"], style="italic")
        else:
            ax.text(b.get_x() + b.get_width() / 2, v, f"{v:,.0f}", ha="center", va="bottom", fontsize=8)
    ax.set_ylabel(ylabel)
    ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: f"{v/1e6:g}M"))
    ax.grid(axis="x", visible=False)
    ax.set_ylim(0, np.nanmax(values) * 1.12)
    if source:
        fig.text(0.01, -0.02, f"Source: {source}", fontsize=7.5, color=PALETTE["grey"], ha="left")
    save(fig, name)


def fig_flowchart(columns, name="flowchart"):
    """'Our Work' diagram. columns = [(column_title, [step1, step2, ...]), ...];
    steps run top-to-bottom inside a column, columns are linked left-to-right."""
    n = len(columns)
    fig, ax = plt.subplots(figsize=(FULL_W, 3.4))
    ax.set_xlim(0, n); ax.set_ylim(0, 1); ax.axis("off")
    fills = [PALETTE["main"], PALETTE["third"], PALETTE["second"], PALETTE["accent"], PALETTE["fourth"]]
    col_w, gap = 0.86, 0.14
    for c, (title, steps) in enumerate(columns):
        x0 = c + gap / 2
        color = fills[c % len(fills)]
        # column frame + title band
        ax.add_patch(FancyBboxPatch((x0, 0.02), col_w, 0.96, boxstyle="round,pad=0,rounding_size=0.03",
                                    fc=color, alpha=0.08, ec=color, lw=1))
        ax.add_patch(FancyBboxPatch((x0, 0.86), col_w, 0.12, boxstyle="round,pad=0,rounding_size=0.03",
                                    fc=color, ec=color))
        ax.text(x0 + col_w / 2, 0.92, title, ha="center", va="center", color="white",
                fontsize=9, weight="bold", wrap=True)
        # step boxes
        k = len(steps); top, bot = 0.80, 0.06
        h = (top - bot) / k
        for i, s in enumerate(steps):
            y = top - (i + 1) * h + 0.015
            ax.add_patch(FancyBboxPatch((x0 + 0.06, y), col_w - 0.12, h - 0.03,
                                        boxstyle="round,pad=0,rounding_size=0.02",
                                        fc="white", ec=color, lw=1))
            ax.text(x0 + col_w / 2, y + (h - 0.03) / 2, s, ha="center", va="center", fontsize=8)
            if i < k - 1:
                ax.annotate("", xy=(x0 + col_w / 2, y - 0.03), xytext=(x0 + col_w / 2, y),
                            arrowprops=dict(arrowstyle="-|>", color=color, lw=1))
        if c < n - 1:
            ax.add_patch(FancyArrowPatch((x0 + col_w + 0.005, 0.45), (x0 + 1 - 0.005, 0.45),
                                         arrowstyle="simple,head_width=7,head_length=6",
                                         color=PALETTE["grey"], lw=0))
    save(fig, name)


def fig_fit(x, y, model, params, xlabel, ylabel, eq_label, name="fit"):
    """Data + fitted curve (top) and residuals (bottom). `model(x, *params)`."""
    xs = np.linspace(x.min(), x.max(), 300)
    yhat = model(x, *params)
    ss_res = np.sum((y - yhat) ** 2); ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(HALF_W * 1.4, 3.6), sharex=True,
                                 gridspec_kw=dict(height_ratios=[3, 1], hspace=0.08))
    a1.scatter(x, y, s=18, color=PALETTE["main"], alpha=0.75, label="Observed data", zorder=3)
    a1.plot(xs, model(xs, *params), color=PALETTE["accent"], label=f"Fit: {eq_label}")
    a1.text(0.03, 0.95, f"$R^2 = {r2:.3f}$", transform=a1.transAxes, va="top")
    a1.set_ylabel(ylabel); a1.legend(loc="lower right")
    a2.axhline(0, color=PALETTE["grey"], lw=0.8)
    a2.vlines(x, 0, y - yhat, color=PALETTE["main"], lw=0.8, alpha=0.6)
    a2.scatter(x, y - yhat, s=8, color=PALETTE["main"])
    a2.set_ylabel("Residual"); a2.set_xlabel(xlabel)
    save(fig, name)


def fig_policy_curve(x, actual, ideal, cap, xlabel, ylabel, labels, name="policy_curve"):
    """Model response vs. ideal (no-friction) line vs. hard cap — like paper Fig 4 & Fig 6."""
    fig, ax = plt.subplots(figsize=(FULL_W, 2.8))
    ax.plot(x, actual, color=PALETTE["accent"], label=labels[0])
    ax.plot(x, ideal, "--", color=PALETTE["main"], lw=1.4, label=labels[1])
    if cap is not None:
        ax.axhline(cap, ls=":", color=PALETTE["fourth"], lw=1.6, label=labels[2])
        ax.fill_between(x, actual, cap, where=actual < cap, color=PALETTE["accent"], alpha=0.06)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.set_xlim(x.min(), x.max()); ax.set_ylim(0, (cap or actual.max()) * 1.2)
    ax.legend(loc="lower right")
    save(fig, name)


def fig_composition(labels, shares, title_total=None, name="composition"):
    """Composition shown two ways side by side: donut (whole) + sorted bars (exact compare).
    Use either panel alone if space is tight. Prefer this over a 3D pie."""
    order = np.argsort(shares)[::-1]
    labels = [labels[i] for i in order]; shares = np.asarray(shares)[order]
    cols = SERIES[: len(shares)]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(FULL_W, 2.6), gridspec_kw=dict(width_ratios=[1, 1.3], wspace=0.55))
    w, _ = a1.pie(shares, colors=cols, startangle=90, counterclock=False,
                  wedgeprops=dict(width=0.38, edgecolor="white", linewidth=1.5))
    if title_total:
        a1.text(0, 0, title_total, ha="center", va="center", fontsize=9, weight="bold")
    a1.set_aspect("equal")
    y = np.arange(len(shares))
    a2.barh(y, shares, color=cols, height=0.62)
    a2.set_yticks(y, labels); a2.invert_yaxis()
    for yi, s in zip(y, shares):
        a2.text(s + 0.6, yi, f"{s:.0f}%", va="center", fontsize=8.5)
    a2.set_xlim(0, shares.max() * 1.2); a2.set_xlabel("Share of total (%)")
    a2.grid(axis="y", visible=False)
    save(fig, name)


def fig_pareto_2d(f1, f2, f3, chosen, xlabel, ylabel, clabel, name="pareto_2d"):
    """2D projection of a 3-objective Pareto set; 3rd objective as colour.
    `chosen` = index of the compromise solution you report. Much easier to read than 3D."""
    fig, ax = plt.subplots(figsize=(FULL_W * 0.75, 3.4))
    sc = ax.scatter(f1, f2, c=f3, cmap="viridis", s=22, edgecolor="white", lw=0.3, zorder=3)
    cb = fig.colorbar(sc, ax=ax, pad=0.02); cb.set_label(clabel); cb.outline.set_visible(False)
    ax.scatter(f1[chosen], f2[chosen], s=180, facecolor="none", edgecolor=PALETTE["accent"], lw=2, zorder=4)
    ax.annotate("Selected\ncompromise", (f1[chosen], f2[chosen]), xytext=(50, -12),
                textcoords="offset points", fontsize=8.5, color=PALETTE["accent"],
                bbox=dict(fc="white", ec="none", alpha=0.85, pad=1),
                arrowprops=dict(arrowstyle="-", color=PALETTE["accent"], lw=0.8))
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    save(fig, name)


def fig_pareto_3d(F1, F2, F3, chosen_xyz, labels, name="pareto_3d"):
    """3D Pareto surface (meshgrid arrays) with the chosen point marked."""
    fig = plt.figure(figsize=(FULL_W * 0.8, 4.0))
    ax = fig.add_subplot(projection="3d")
    surf = ax.plot_surface(F1, F2, F3, cmap="viridis", lw=0, antialiased=True, alpha=0.9)
    ax.scatter(*chosen_xyz, color=PALETTE["accent"], s=90, depthshade=False, edgecolor="white", zorder=10)
    ax.text(*chosen_xyz, "  Selected", color=PALETTE["accent"], fontsize=8.5, zorder=11)
    ax.set_xlabel(labels[0], labelpad=6); ax.set_ylabel(labels[1], labelpad=6)
    ax.set_zlabel(labels[2], labelpad=6)
    for a in (ax.xaxis, ax.yaxis, ax.zaxis):
        a.pane.fill = False; a.pane.set_edgecolor("#DDDDDD")
    ax.view_init(elev=24, azim=-55)
    save(fig, name)


def fig_convergence(gens, curves, ylabel, name="convergence"):
    """Algorithm convergence. curves = {label: (mean, std)} over generations."""
    fig, ax = plt.subplots(figsize=(FULL_W * 0.75, 2.6))
    for (lab, (m, s)), c in zip(curves.items(), SERIES):
        ax.plot(gens, m, color=c, label=lab)
        ax.fill_between(gens, m - s, m + s, color=c, alpha=0.15, lw=0)
    ax.set_xlabel("Generation"); ax.set_ylabel(ylabel); ax.legend(loc="lower right")
    ax.set_xlim(gens.min(), gens.max())
    save(fig, name)


def fig_sensitivity_lines(steps, panels, name="sensitivity_lines"):
    """One-at-a-time sensitivity, one panel per objective.
    panels = [(objective_title, {param_label: response_array}), ...]
    Responses are best given as % change from baseline so panels share a scale."""
    n = len(panels)
    fig, axes = plt.subplots(1, n, figsize=(FULL_W, 2.4), sharey=True)
    for ax, (title, series) in zip(np.atleast_1d(axes), panels):
        for (lab, r), c in zip(series.items(), SERIES):
            ax.plot(steps, r, color=c, label=lab)
        ax.axhline(0, color="#999999", lw=0.6); ax.axvline(0, color="#999999", lw=0.6)
        ax.set_title(title); ax.set_xlabel("Parameter change (%)")
    np.atleast_1d(axes)[0].set_ylabel("Objective change (%)")
    h, l = np.atleast_1d(axes)[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=len(l), bbox_to_anchor=(0.5, -0.12))
    fig.tight_layout()
    save(fig, name)


def fig_tornado(params, low, high, objective, name="tornado"):
    """Tornado chart: objective change when each parameter goes -X% (low) / +X% (high).
    Sorted so the most influential parameter is on top."""
    span = np.abs(np.asarray(high) - np.asarray(low))
    o = np.argsort(span)
    params = [params[i] for i in o]; low = np.asarray(low)[o]; high = np.asarray(high)[o]
    fig, ax = plt.subplots(figsize=(FULL_W * 0.75, 0.32 * len(params) + 0.9))
    y = np.arange(len(params))
    ax.barh(y, low, color=PALETTE["main"], height=0.6, label="Parameter −20%")
    ax.barh(y, high, color=PALETTE["accent"], height=0.6, label="Parameter +20%")
    ax.axvline(0, color="#333333", lw=0.8)
    ax.set_yticks(y, params); ax.grid(axis="y", visible=False)
    ax.set_xlabel(f"Change in {objective} (%)")
    ax.legend(loc="lower right", fontsize=8)
    save(fig, name)


def fig_sensitivity_heat(param_names, grid_fn, steps, objective, name="sensitivity_heat"):
    """Two-parameter sensitivity: one heatmap per parameter pair, shared colour scale.
    grid_fn(i, j, P, Q) -> objective % change when param i takes P and param j takes Q."""
    pairs = [(i, j) for i in range(len(param_names)) for j in range(i + 1, len(param_names))]
    nc = min(3, len(pairs)); nr = int(np.ceil(len(pairs) / nc))
    P, Q = np.meshgrid(steps, steps)
    Z = [grid_fn(i, j, P, Q) for i, j in pairs]
    vmax = max(np.abs(z).max() for z in Z)
    fig, axes = plt.subplots(nr, nc, figsize=(FULL_W, 2.0 * nr + 0.3), squeeze=False)
    for ax, (i, j), z in zip(axes.flat, pairs, Z):
        im = ax.pcolormesh(steps, steps, z, cmap="RdBu_r", vmin=-vmax, vmax=vmax, shading="auto")
        ax.contour(steps, steps, z, levels=[0], colors="k", linewidths=0.6)
        ax.set_xlabel(param_names[i] + " change (%)", fontsize=8.5)
        ax.set_ylabel(param_names[j] + " change (%)", fontsize=8.5)
        ax.tick_params(labelsize=7.5); ax.grid(False); ax.set_aspect("equal")
    for ax in list(axes.flat)[len(pairs):]:
        ax.axis("off")
    fig.tight_layout()
    cb = fig.colorbar(im, ax=axes, shrink=0.8, pad=0.02)
    cb.set_label(f"Change in {objective} (%)"); cb.outline.set_visible(False)
    save(fig, name)


# --------------------------------------------------------------------------
# 3. EXAMPLE DATA  (replace with yours)
# --------------------------------------------------------------------------
if __name__ == "__main__":
    rng = np.random.default_rng(7)

    # Fig 1 — passenger volume, 2020 deliberately missing
    years = [str(y) for y in range(2014, 2024)]
    pax = np.array([961e3, 983e3, 1015e3, 1072e3, 1151e3, 1306e3, np.nan, 117e3, 1167e3, 1670e3])
    fig_bar_trend(years, pax, "Cruise passengers", source="City and Borough of Juneau; CLIA Alaska",
                  highlight=9)

    # Fig 2 — workflow
    fig_flowchart([
        ("Task 1: Model", ["Problem analysis", "Objectives &\ndecision variables",
                           "Objective functions\n& constraints", "Data fitting"]),
        ("Solve", ["NSGA-II", "Pareto front", "Select compromise\nsolution"]),
        ("Validate", ["Single-parameter\nsensitivity", "Two-parameter\nsensitivity", "Strengths &\nweaknesses"]),
        ("Tasks 2–3", ["Adapt to other\ndestinations", "Memo to\ntourism council"]),
    ])

    # 4.1 — linear fit of transportation revenue vs tourists
    x = np.sort(rng.uniform(2e3, 1.8e4, 40))
    y = 1051.23 * x + 2e5 + rng.normal(0, 1.2e6, x.size)
    lin = lambda t, a, b: a * t + b
    a, b = np.polyfit(x, y, 1)
    fig_fit(x, y / 1e6, lambda t, a, b: (a * t + b) / 1e6, (a, b),
            "Daily tourists $x$", "Transportation revenue $D$ (million USD)",
            r"$D=\lambda_2 x+\varepsilon_2$", name="fit")

    # Fig 6 — tourist cap vs actual arrivals
    cap_set = np.linspace(0, 20000, 300)
    lam29, capacity = 10053.49, 9000
    actual = capacity * (1 - np.exp(-cap_set / lam29))
    fig_policy_curve(cap_set, actual, cap_set, capacity, "Daily tourist limit $y_1$",
                     "Number of tourists",
                     ["Actual expected tourists", "Limit (if fully used)", "Maximum capacity"])

    # Fig 5 — revenue composition
    fig_composition(["Accommodation", "Catering", "Other attractions", "Shopping", "Transportation"],
                    [33, 28, 16, 12, 11], title_total="$375M\n2023")

    # Fig 8 — Pareto set (synthetic, 3 objectives)
    t = rng.uniform(0, 1, 160)
    econ = 1.2 + 2.0 * t + rng.normal(0, 0.05, t.size)          # revenue ($B) ↑ better
    env = 0.3 + 2.2 * t ** 1.6 + rng.normal(0, 0.08, t.size)    # stress ↓ better
    soc = 0.95 - 0.55 * (t - 0.35) ** 2 + rng.normal(0, 0.02, t.size)
    chosen = int(np.argmax(soc - 0.15 * env))
    fig_pareto_2d(econ, env, soc, chosen, "Tourism revenue $Z_1$ (billion USD)",
                  "Environmental stress $Z_3$", "Satisfaction $Z_2$")

    U, V = np.meshgrid(np.linspace(0, 1, 50), np.linspace(0, 1, 50))
    F1 = 1.2 + 2 * U; F2 = 0.4 + 0.6 * V; F3 = 0.3 + 2.2 * U ** 1.6 * (1 - 0.4 * V)
    fig_pareto_3d(F1, F2, F3, (F1[25, 20], F2[25, 20], F3[25, 20]),
                  ["Revenue $Z_1$", "Satisfaction $Z_2$", "Env. stress $Z_3$"])

    # Convergence over 30 independent runs
    g = np.arange(1, 201)
    hv = 0.82 * (1 - np.exp(-g / 28)); hv2 = 0.76 * (1 - np.exp(-g / 45))
    fig_convergence(g, {"NSGA-II": (hv, 0.04 * np.exp(-g / 60) + 0.006),
                        "Weighted-sum GA": (hv2, 0.05 * np.exp(-g / 70) + 0.01)},
                    "Hypervolume")

    # Fig 9 — one-at-a-time sensitivity (% change)
    s = np.linspace(-20, 20, 41)
    fig_sensitivity_lines(s, [
        ("Revenue $Z_1$", {"$y_1$ tourist limit": 0.55 * s, "$y_3$ tax": 0.18 * s - 0.004 * s**2,
                           "$y_6$ infrastructure": 0.30 * s}),
        ("Satisfaction $Z_2$", {"$y_1$ tourist limit": -0.35 * s, "$y_3$ tax": -0.10 * s,
                                "$y_6$ infrastructure": 0.22 * s}),
        ("Env. stress $Z_3$", {"$y_1$ tourist limit": 0.62 * s, "$y_3$ tax": -0.05 * s,
                               "$y_6$ infrastructure": 0.15 * s}),
    ])

    # Tornado
    fig_tornado(["$y_1$ tourist limit", "$y_2$ alcohol limit", "$y_3$ tourism tax", "$y_4$ tourist fee",
                 "$y_5$ env. spending", "$y_6$ infrastructure", "$y_7$ promotion"],
                low=[-11, -1.2, 3.1, 1.5, -0.8, -6.2, -2.4],
                high=[9.5, 1.0, -4.0, -1.9, 1.1, 5.8, 2.1], objective="revenue $Z_1$")

    # Fig 10 — two-parameter sensitivity heatmaps
    coef = {0: 0.55, 1: 0.18, 2: 0.30, 3: 0.12}
    fig_sensitivity_heat(["$y_1$", "$y_3$", "$y_6$", "$y_7$"],
                         lambda i, j, P, Q: coef[i] * P + coef[j] * Q - 0.004 * P * Q,
                         np.linspace(-20, 20, 41), "revenue $Z_1$")
