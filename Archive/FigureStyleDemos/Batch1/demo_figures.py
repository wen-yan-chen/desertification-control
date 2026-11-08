"""O-award-style MCM figure demo (placeholder / synthetic data only).

Generates 12 representative paper figures to demonstrate chart vocabulary,
style and palette. No real data is used; every figure carries an honest note.
Run:  python demo_figures.py
Outputs PNG (300 dpi) into ./png alongside this script.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

# ----------------------------------------------------------------------------
# Shared visual system
# ----------------------------------------------------------------------------
BLUE, GOLD, GREEN = "#286187", "#BA8B33", "#7A8560"
PINK, GRAY, LIGHT = "#B96583", "#888888", "#B5C8D5"
PALETTE = [BLUE, GOLD, GREEN, PINK, GRAY]
CAT = ["Infrastructure", "Ecology", "Community"]
NOTE = "Illustrative placeholder data; not based on observed measurements."
rng = np.random.default_rng(42)

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "axes.titlesize": 13, "axes.labelsize": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 100, "savefig.dpi": 300, "svg.fonttype": "path",
    "axes.unicode_minus": False,
})
OUT = Path(__file__).resolve().parent / "png"
OUT.mkdir(parents=True, exist_ok=True)


def save(fig, name, title):
    fig.suptitle(title, y=0.99, fontweight="bold")
    fig.text(0.015, 0.012, NOTE, fontsize=8, color="#555555")
    fig.tight_layout(rect=(0, 0.05, 1, 0.95))
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------------
# 1. Designed workflow flowchart
# ----------------------------------------------------------------------------
def fig_workflow():
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 8); ax.axis("off")
    boxes = [
        (0.5, 5.5, 2.6, 1.2, "Policy levers\nTax / budget / rules", BLUE),
        (3.7, 5.5, 2.6, 1.2, "Investment\nConstruction / O&M / PV", GOLD),
        (6.9, 5.5, 2.6, 1.2, "Water scheduling\nReplenishment volume", GREEN),
        (3.7, 3.0, 2.6, 1.2, "System state\nVegetation / soil moisture", "#5B7FA3"),
        (0.5, 0.7, 2.6, 1.2, "Feasibility\nHard constraints", GRAY),
        (3.7, 0.7, 2.6, 1.2, "Trade-off\nEcology vs. economy", PINK),
        (6.9, 0.7, 2.6, 1.2, "Resilience\nStochastic shocks", "#9C7A4A"),
    ]
    for x, y, w, h, text, col in boxes:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.12",
                                    fc=col, ec="white", alpha=0.9, mutation_aspect=1))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                color="white", fontsize=10, fontweight="bold")
    links = [((3.1, 6.1), (3.7, 6.1)), ((6.3, 6.1), (6.9, 6.1)),
             ((5.0, 5.5), (5.0, 4.2)), ((1.8, 5.5), (1.8, 1.9)),
             ((8.2, 5.5), (8.2, 1.9)), ((5.0, 3.0), (5.0, 1.9)),
             ((3.1, 1.3), (3.7, 1.3)), ((6.3, 1.3), (6.9, 1.3))]
    for a, b in links:
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=14,
                                     color="#444444", lw=1.4))
    save(fig, "Fig01_workflow", "Designed workflow of the modeling pipeline")


# ----------------------------------------------------------------------------
# 2. EDA multi-panel dashboard
# ----------------------------------------------------------------------------
def fig_eda():
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    years = np.arange(2014, 2024)
    series = np.linspace(40, 78, 10) + rng.normal(0, 2, 10)
    series[6] = 22  # shock dip
    ax = axes[0, 0]
    ax.plot(years, series, "-o", color=BLUE, lw=2, ms=5)
    ax.axvspan(2019.5, 2020.5, color=PINK, alpha=0.18)
    ax.annotate("external shock", (2020, 22), xytext=(2016.3, 30),
                arrowprops=dict(arrowstyle="->", color="#444444"))
    ax.set(title="State variable over time", xlabel="Year", ylabel="Index value")

    ax = axes[0, 1]
    items = ["Crowding", "Traffic", "Water stress", "Wind erosion", "Funding gap"]
    vals = np.sort(rng.uniform(15, 80, 5))
    ax.barh(items, vals, color=GREEN)
    for y, v in enumerate(vals):
        ax.text(v + 1, y, f"{v:.0f}", va="center", fontsize=9)
    ax.set(title="Reported concern factors", xlabel="Share (%)")

    ax = axes[1, 0]
    comp = ["Construction", "O&M", "PV facilities", "Reserve"]
    shares = [42, 24, 20, 14]
    ax.pie(shares, labels=comp, colors=[BLUE, GOLD, GREEN, GRAY],
           autopct="%1.0f%%", startangle=90, wedgeprops=dict(width=0.42, edgecolor="white"))
    ax.set(title="Budget composition")

    ax = axes[1, 1]
    ax.axis("off")
    kpis = [("Treated area", "1,240", "ha"), ("Coverage", "0.82", ""), ("Feasible", "96%", "")]
    for i, (k, v, u) in enumerate(kpis):
        ax.add_patch(FancyBboxPatch((0.05, 0.68 - i * 0.32), 0.9, 0.24,
                                    boxstyle="round,pad=0.03", fc=LIGHT, ec="none", alpha=0.6))
        ax.text(0.12, 0.80 - i * 0.32, k, fontsize=10, color="#333333")
        ax.text(0.85, 0.78 - i * 0.32, f"{v} {u}", fontsize=15,
                ha="right", fontweight="bold", color=BLUE)
    ax.set_title("Key indicators", fontsize=13)
    save(fig, "Fig02_eda_dashboard", "Multi-panel exploratory data overview")


# ----------------------------------------------------------------------------
# 3. Schematic site map
# ----------------------------------------------------------------------------
def fig_map():
    fig, ax = plt.subplots(figsize=(10, 7))
    t = np.linspace(0, 2 * np.pi, 200)
    bx = 8 * np.cos(t) * (1 + 0.15 * np.sin(3 * t))
    by = 6 * np.sin(t) * (1 + 0.12 * np.cos(2 * t))
    ax.fill(bx, by, color="#E7D9B8", alpha=0.7, label="Desert region")
    ax.plot(bx * 0.82, by * 0.82, color=GREEN, lw=3, label="Edge-locking belt")
    nodes = [(bx[i] * 0.82, by[i] * 0.82) for i in (10, 55, 110, 160)]
    for i, (x, y) in enumerate(nodes, 1):
        ax.scatter(x, y, s=130, color=BLUE, zorder=5, edgecolor="white")
        ax.text(x, y - 0.7, f"N{i}", ha="center", fontsize=10, fontweight="bold")
    ax.annotate("", xy=(6.5, 4.6), xytext=(5.2, 3.6),
                arrowprops=dict(arrowstyle="-|>", lw=1.6, color="#444444"))
    ax.text(5.4, 3.9, "sand transport", fontsize=9)
    ax.annotate("N", xy=(-7.2, 5.6), ha="center", fontsize=12, fontweight="bold")
    ax.annotate("", xy=(-7.2, 6.2), xytext=(-7.2, 5.0),
                arrowprops=dict(arrowstyle="-|>", color="black"))
    ax.plot([-7.5, -5.5], [-6.2, -6.2], color="black", lw=2)
    ax.text(-6.5, -6.6, "10 km", ha="center", fontsize=9)
    ax.set(title="Schematic site map (not to scale)", xlim=(-9, 9), ylim=(-7, 7))
    ax.set_xticks([]); ax.set_yticks([])
    ax.legend(loc="lower right", fontsize=9)
    save(fig, "Fig03_schematic_map", "Schematic spatial layout of the belt and nodes")


# ----------------------------------------------------------------------------
# 4. Annotated correlation heatmap
# ----------------------------------------------------------------------------
def fig_heatmap():
    cols = ["Area", "Water", "Veg.", "Labor", "PV", "Cost", "Accept."]
    n = 120
    base = rng.normal(size=(n, 1))
    data = np.hstack([base * s + rng.normal(0, 0.5, (n, 1)) for s in (1, -0.8, 0.9, 0.4, -0.5, 0.7, 0.85)])
    corr = np.corrcoef(data, rowvar=False)
    fig, ax = plt.subplots(figsize=(9, 7.5))
    cmap = LinearSegmentedColormap.from_list("brand", [GOLD, "#FFFFFF", BLUE])
    im = ax.imshow(corr, cmap=cmap, vmin=-1, vmax=1)
    ax.set_xticks(range(7), cols); ax.set_yticks(range(7), cols)
    for i in range(7):
        for j in range(7):
            ax.text(j, i, f"{corr[i, j]:.2f}", ha="center", va="center",
                    color="white" if abs(corr[i, j]) > 0.55 else "#333333", fontsize=9)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Correlation")
    save(fig, "Fig04_corr_heatmap", "Annotated correlation heatmap with colorbar")


# ----------------------------------------------------------------------------
# 5. 3D Pareto surface
# ----------------------------------------------------------------------------
def fig_pareto_3d():
    fig = plt.figure(figsize=(10, 7.5))
    ax = fig.add_subplot(111, projection="3d")
    gx = np.linspace(0.3, 1, 30); gy = np.linspace(0.3, 1, 30)
    X, Y = np.meshgrid(gx, gy)
    Z = 1.4 - 0.6 * X - 0.5 * Y + 0.25 * X * Y  # benefit surface
    surf = ax.plot_surface(X, Y, Z, cmap="cividis", alpha=0.85, edgecolor="none")
    ax.scatter(0.62, 0.58, 1.4 - 0.6 * 0.62 - 0.5 * 0.58 + 0.25 * 0.62 * 0.58,
               marker="*", s=300, color=PINK, edgecolor="black", label="Recommended")
    ax.set(xlabel="Pressure A", ylabel="Pressure B", zlabel="Benefit")
    ax.view_init(elev=20, azim=-55)
    fig.colorbar(surf, ax=ax, shrink=0.55, fraction=0.03, label="Benefit")
    ax.legend(fontsize=9)
    save(fig, "Fig05_pareto_3d", "Three-dimensional Pareto surface with recommended point")


# ----------------------------------------------------------------------------
# 6. Parallel coordinates
# ----------------------------------------------------------------------------
def fig_parallel():
    axes_labels = ["Revenue", "Env. pressure", "Soc. pressure", "Infra. pressure", "Acceptance"]
    n = 60
    raw = rng.uniform(0, 1, (n, 5))
    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(5)
    mn, mx = raw.min(0), raw.max(0)
    norm = (raw - mn) / (mx - mn)
    for i in range(n):
        ax.plot(x, norm[i], color=GRAY, alpha=0.25, lw=1)
    rec = norm[0]
    ax.plot(x, rec, color=PINK, lw=2.6, marker="o", label="Recommended")
    ax.set_xticks(x, axes_labels); ax.set_ylabel("Normalized value (0-1)")
    ax.set_ylim(-0.05, 1.05); ax.legend()
    save(fig, "Fig06_parallel_coords", "Parallel coordinates of the multi-objective candidates")


# ----------------------------------------------------------------------------
# 7. Tornado chart
# ----------------------------------------------------------------------------
def fig_tornado():
    params = ["Revenue calibration", "Discount rate", "Water availability", "PV yield",
              "Labor cost", "O&M ratio", "Demand elasticity"]
    base = 0
    low = -np.sort(-rng.uniform(0.02, 0.16, 7))
    high = rng.uniform(0.02, 0.15, 7) * rng.choice([-1, 1], 7)
    fig, ax = plt.subplots(figsize=(10, 6))
    y = np.arange(7)
    ax.barh(y, low, color=BLUE, alpha=0.85, label="Low case")
    ax.barh(y, high, color=GOLD, alpha=0.85, label="High case")
    ax.axvline(0, color="#333333", lw=1)
    ax.set_yticks(y, params); ax.invert_yaxis()
    ax.set_xlabel("Change in objective vs. baseline")
    ax.legend()
    save(fig, "Fig07_tornado", "Tornado diagram of single-factor sensitivity")


# ----------------------------------------------------------------------------
# 8. Uncertainty: KDE + fan chart
# ----------------------------------------------------------------------------
def fig_uncertainty():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    samples = rng.normal(0.82, 0.09, 800)
    ax = axes[0]
    ax.hist(samples, bins=30, density=True, color=LIGHT, alpha=0.7, label="Histogram")
    kde_x = np.linspace(0.5, 1.1, 200)
    from scipy.stats import gaussian_kde
    ax.plot(kde_x, gaussian_kde(samples)(kde_x), color=BLUE, lw=2.2, label="KDE")
    for q, c in zip(np.quantile(samples, [0.05, 0.5, 0.95]), [GRAY, PINK, GRAY]):
        ax.axvline(q, color=c, ls="--", lw=1.3)
    ax.set(title="Output distribution", xlabel="Outcome", ylabel="Density"); ax.legend(fontsize=9)

    ax = axes[1]
    periods = np.arange(1, 16)
    median = 0.7 + 0.015 * periods
    spread = 0.03 + 0.006 * periods
    ax.plot(periods, median, color=BLUE, lw=2, label="Median")
    ax.fill_between(periods, median - spread, median + spread, color=BLUE, alpha=0.25, label="50% band")
    ax.fill_between(periods, median - 2 * spread, median + 2 * spread, color=BLUE, alpha=0.13, label="90% band")
    ax.set(title="Fan chart projection", xlabel="Year ahead", ylabel="Outcome"); ax.legend(fontsize=9)
    save(fig, "Fig08_uncertainty", "Uncertainty distribution and confidence fan chart")


# ----------------------------------------------------------------------------
# 9. Violin / box of constraint margins
# ----------------------------------------------------------------------------
def fig_violin():
    data = [rng.normal(m, s, 200) for m, s in [(0.12, 0.05), (0.25, 0.08), (0.08, 0.03), (0.18, 0.06)]]
    fig, ax = plt.subplots(figsize=(10, 6))
    parts = ax.violinplot(data, showmedians=True)
    for i, pc in enumerate(parts["bodies"]):
        pc.set_facecolor(PALETTE[i % 3]); pc.set_alpha(0.8)
    ax.set_xticks(range(1, 5), ["Capacity", "Ecology", "Daily cap", "Budget"])
    ax.set_ylabel("Constraint margin")
    ax.axhline(0, color="#333333", ls="--", lw=1)
    save(fig, "Fig09_violin", "Distribution of constraint margins across feasible solutions")


# ----------------------------------------------------------------------------
# 10. Response curves with fill_between
# ----------------------------------------------------------------------------
def fig_response():
    fig, ax = plt.subplots(figsize=(10, 6))
    spend = np.linspace(0, 50, 200)
    for (eta, ceil, k), col, name in zip(
            [(0.7, 0.5, 8), (0.8, 0.9, 9), (0.6, 0.8, 6)], PALETTE, CAT):
        resp = eta * ceil * (1 - np.exp(-spend / k))
        ax.plot(spend, resp * 100, color=col, lw=2.2, label=name)
        idx = 40
        ax.scatter(spend[idx], resp[idx] * 100, color=col, s=60, edgecolor="white", zorder=5)
        ax.fill_between(spend, 0, resp * 100, color=col, alpha=0.08)
    ax.set(xlabel="Annual investment (million USD)", ylabel="Response fraction (%)")
    ax.legend(title="Category")
    save(fig, "Fig10_response_curves", "Saturating investment response curves")


# ----------------------------------------------------------------------------
# 11. Radar chart
# ----------------------------------------------------------------------------
def fig_radar():
    labels = ["Coverage", "Moisture", "Capacity", "Acceptance", "PV share", "Resilience"]
    ang = np.linspace(0, 2 * np.pi, 6, endpoint=False).tolist()
    ang += ang[:1]
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    for vals, col, name in [
        ([0.8, 0.65, 0.7, 0.82, 0.4, 0.6], BLUE, "Baseline"),
        ([0.9, 0.8, 0.85, 0.88, 0.7, 0.78], GOLD, "Optimized"),
    ]:
        vals += vals[:1]
        ax.plot(ang, vals, color=col, lw=2, label=name)
        ax.fill(ang, vals, color=col, alpha=0.15)
    ax.set_xticks(ang[:-1], labels); ax.set_ylim(0, 1)
    ax.legend(loc="lower right", bbox_to_anchor=(1.15, -0.05))
    save(fig, "Fig11_radar", "Multi-attribute radar comparison")


# ----------------------------------------------------------------------------
# 12. Scenario grouped / stacked bars
# ----------------------------------------------------------------------------
def fig_scenario():
    scenarios = ["Default", "Eco priority", "Economy priority", "Community", "Robust"]
    x = np.arange(5)
    series = np.array([[12, 18, 10, 15, 14], [8, 6, 14, 9, 10], [5, 4, 9, 6, 8]], float)
    fig, ax = plt.subplots(figsize=(11, 6))
    left = np.zeros(5)
    for s, col, name in zip(series, [BLUE, GOLD, GREEN], ["Construction", "O&M", "PV & reserve"]):
        ax.bar(x, s, bottom=left, color=col, label=name, width=0.6)
        left += s
    ax.set_xticks(x, scenarios); ax.set_ylabel("Allocation (million USD)")
    ax.legend()
    save(fig, "Fig12_scenario_bars", "Stacked allocation across preference scenarios")


if __name__ == "__main__":
    for fn in [fig_workflow, fig_eda, fig_map, fig_heatmap, fig_pareto_3d,
               fig_parallel, fig_tornado, fig_uncertainty, fig_violin,
               fig_response, fig_radar, fig_scenario]:
        fn()
    print("Saved 12 demo figures to", OUT)
