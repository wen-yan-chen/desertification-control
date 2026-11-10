"""O-award-style MCM figure demo — BATCH 2 (new, advanced, placeholder data).

12 new chart types, none repeated from batch 1: alluvial/Sankey, ridge plot,
bump chart, raincloud, force network, waterfall, streamgraph, hexbin joint,
nested sunburst, phase-plane quiver, dumbbell, clustered heatmap.
All static, printable and reproducible with matplotlib/seaborn/numpy/scipy only.
Run:  python demo_figures2.py
"""
from pathlib import Path
from figure_paths import output_path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path as MplPath
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import gaussian_kde
from scipy.integrate import solve_ivp
import seaborn as sns

# ----------------------------------------------------------------------------
# Extended but harmonious brand palette
# ----------------------------------------------------------------------------
BLUE, GOLD, GREEN = "#286187", "#BA8B33", "#7A8560"
STEEL, CLAY, SAGE = "#5B8FB9", "#C97B63", "#9AA68C"
MAUVE, PINK, SAND, SLATE = "#8A7A99", "#B96583", "#D8C39B", "#6B7B8C"
PALETTE = [BLUE, GOLD, GREEN, STEEL, CLAY, SAGE, MAUVE, PINK]
NOTE = "Illustrative placeholder data; not based on observed measurements."
rng = np.random.default_rng(7)

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "axes.titlesize": 13, "axes.labelsize": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 100, "savefig.dpi": 300, "axes.unicode_minus": False,
})
OUT = Path(__file__).resolve().parent.parent / "Images"

SEQ_BLUE = LinearSegmentedColormap.from_list("seq_blue", ["#EAF1F7", "#9FBFD8", BLUE])
DIVERGING = LinearSegmentedColormap.from_list("div", [GOLD, "#FFFFFF", BLUE])


def save(fig, name, title):
    fig.suptitle(title, y=0.99, fontweight="bold")
    fig.text(0.015, 0.012, NOTE, fontsize=8, color="#555555")
    fig.tight_layout(rect=(0, 0.05, 1, 0.95))
    fig.savefig(output_path("batch2", name, "png"), bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------------
# 1. Alluvial / Sankey flow (hand-built ribbons)
# ----------------------------------------------------------------------------
def fig_alluvial():
    left = ["Fiscal grant", "Local fund", "PV revenue", "Social capital"]
    right = ["Construction", "O&M", "Ecology", "Reserve"]
    flow = np.array([[38, 12, 14, 6], [10, 16, 8, 4], [6, 8, 18, 10], [4, 6, 8, 6]], float)
    nL, nR = len(left), len(right)
    total = flow.sum()
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(-0.12, 1.12); ax.set_ylim(0, 1); ax.axis("off")
    gap = 0.04
    def blocks(sums):
        usable = 1 - gap * (len(sums) - 1)
        y = 1.0; pos = []
        for s in sums:
            h = s / total * usable
            pos.append((y, y - h)); y -= h + gap
        return pos
    lb, rb = blocks(flow.sum(1)), blocks(flow.sum(0))
    lcur = [p[0] for p in lb]; rcur = [p[0] for p in rb]
    xL, xR, w = 0.0, 1.0, 0.035
    for i in range(nL):
        for j in range(nR):
            v = flow[i, j]
            if v <= 0:
                continue
            h = v / total * (1 - gap * (nL - 1))
            lt, lbt = lcur[i], lcur[i] - h
            rt, rbt = rcur[j], rcur[j] - h
            lcur[i] -= h; rcur[j] -= h
            verts = [(xL, lbt), (0.5, lbt), (0.5, rbt), (xR, rbt),
                     (xR, rt), (0.5, rt), (0.5, lt), (xL, lt), (xL, lbt)]
            codes = [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
                     MplPath.LINETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4, MplPath.CLOSEPOLY]
            ax.add_patch(PathPatch(MplPath(verts, codes), fc=PALETTE[i], alpha=0.42, ec="none"))
    for (t, b), name, col in zip(lb, left, PALETTE):
        ax.add_patch(Rectangle((xL - w, b), w, t - b, fc=col, ec="none"))
        ax.text(xL - w - 0.01, (t + b) / 2, name, ha="right", va="center", fontsize=10)
    for (t, b), name, col in zip(rb, right, PALETTE):
        ax.add_patch(Rectangle((xR, b), w, t - b, fc=col, ec="none"))
        ax.text(xR + w + 0.01, (t + b) / 2, name, ha="left", va="center", fontsize=10)
    save(fig, "B1_alluvial", "Alluvial diagram of resource flow across stages")


# ----------------------------------------------------------------------------
# 2. Ridge / joy plot
# ----------------------------------------------------------------------------
def fig_ridge():
    groups = ["Site A", "Site B", "Site C", "Site D", "Site E", "Site F"]
    means = np.linspace(0.4, 0.9, 6)
    x = np.linspace(0, 1, 300)
    fig, ax = plt.subplots(figsize=(11, 7))
    overlap = 0.62
    for i, (g, m) in enumerate(zip(groups, means)):
        vals = rng.normal(m, 0.09, 200)
        kde = gaussian_kde(vals)
        y = kde(x)
        base = (len(groups) - 1 - i) * overlap
        ax.fill_between(x, base, base + y, color=PALETTE[i % len(PALETTE)], alpha=0.78)
        ax.plot(x, base + y, color="white", lw=1.2)
        ax.text(-0.02, base + 0.3, g, ha="right", va="center", fontsize=10)
    ax.set_xlim(-0.05, 1.05); ax.set_yticks([])
    ax.set_xlabel("Outcome value")
    save(fig, "B2_ridge", "Ridge plot of distributions across sites")


# ----------------------------------------------------------------------------
# 3. Bump chart (rank changes)
# ----------------------------------------------------------------------------
def fig_bump():
    entities = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
    times = np.arange(2019, 2026)
    ranks = np.array([[1, 1, 2, 3, 4, 3, 2], [2, 3, 1, 1, 2, 2, 3],
                      [3, 2, 3, 2, 1, 4, 4], [4, 4, 4, 4, 3, 1, 1],
                      [5, 5, 5, 5, 5, 5, 5]], float)
    fig, ax = plt.subplots(figsize=(11, 6.5))
    for i, e in enumerate(entities):
        ax.plot(times, ranks[i], "-o", color=PALETTE[i], lw=2.6, ms=9, zorder=3)
        ax.text(times[-1] + 0.15, ranks[i, -1], e, va="center", fontsize=10, color=PALETTE[i])
    ax.invert_yaxis()
    ax.set_yticks(range(1, 6), [f"Rank {i}" for i in range(1, 6)])
    ax.set_xticks(times); ax.set_xlim(2018.6, 2026.2)
    save(fig, "B3_bump", "Bump chart of ranking changes over time")


# ----------------------------------------------------------------------------
# 4. Raincloud plot
# ----------------------------------------------------------------------------
def fig_raincloud():
    data = [rng.normal(m, s, 150) for m, s in [(0.4, 0.12), (0.6, 0.1), (0.75, 0.13), (0.55, 0.09)]]
    pos = np.arange(4)
    fig, ax = plt.subplots(figsize=(11, 6.5))
    parts = ax.violinplot(data, positions=pos, showmeans=False, showmedians=False, showextrema=False)
    for pc, col in zip(parts["bodies"], PALETTE):
        pc.set_facecolor(col); pc.set_alpha(0.35); pc.set_edgecolor("none")
    ax.boxplot(data, positions=pos, widths=0.08, showfliers=False,
               medianprops=dict(color="#333333", lw=1.5), boxprops=dict(color="#444444"))
    for x, d, col in zip(pos, data, PALETTE):
        jitter = rng.uniform(0.14, 0.3, len(d))
        ax.scatter(x + jitter, d, s=10, color=col, alpha=0.6, zorder=3)
    ax.set_xticks(pos, ["Quarter 1", "Quarter 2", "Quarter 3", "Quarter 4"])
    ax.set_ylabel("Outcome")
    save(fig, "B4_raincloud", "Raincloud plot: distribution, box and raw observations")


# ----------------------------------------------------------------------------
# 5. Force-directed network (manual Fruchterman-Reingold)
# ----------------------------------------------------------------------------
def fig_network():
    n = 14
    adj = np.zeros((n, n))
    # spanning backbone first, so the graph is connected (no isolated nodes)
    order = rng.permutation(n)
    for k in range(n - 1):
        a, b = order[k], order[k + 1]
        adj[a, b] = adj[b, a] = rng.uniform(0.6, 1.8)
    for _ in range(20):
        a, b = rng.integers(0, n, 2)
        if a != b and adj[a, b] == 0:
            adj[a, b] = adj[b, a] = rng.uniform(0.5, 2)
    pos = rng.uniform(-1, 1, (n, 2))
    for it in range(200):
        temp = 0.05 * (1 - it / 200) + 0.005
        disp = np.zeros_like(pos)
        for i in range(n):
            diff = pos[i] - pos
            dist = np.linalg.norm(diff, axis=1) + 1e-6
            disp[i] += (diff / dist[:, None] * (0.08 / dist**2)[:, None]).sum(0)
        for i in range(n):
            for j in range(n):
                if adj[i, j] > 0:
                    d = pos[i] - pos[j]; dist = np.linalg.norm(d) + 1e-6
                    f = dist**2 / 0.85
                    disp[i] -= d / dist * f; disp[j] += d / dist * f
        disp -= pos * 0.12  # gravity toward the centre keeps the layout compact
        pos += disp * temp
        pos -= pos.mean(0)
    fig, ax = plt.subplots(figsize=(10, 8))
    for i in range(n):
        for j in range(i + 1, n):
            if adj[i, j] > 0:
                ax.plot([pos[i, 0], pos[j, 0]], [pos[i, 1], pos[j, 1]],
                        color=SLATE, lw=adj[i, j], alpha=0.45, zorder=1)
    community = np.array([0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2])
    for i in range(n):
        ax.scatter(*pos[i], s=380 + (adj[i] > 0).sum() * 60, color=PALETTE[community[i]],
                   edgecolor="white", lw=1.5, zorder=3)
        ax.text(*pos[i], str(i + 1), ha="center", va="center", fontsize=9, color="white", fontweight="bold")
    ax.set_xticks([]); ax.set_yticks([]); ax.axis("off")
    save(fig, "B5_network", "Force-directed network with communities and edge weights")


# ----------------------------------------------------------------------------
# 6. Waterfall chart
# ----------------------------------------------------------------------------
def fig_waterfall():
    labels = ["Start", "Grant", "PV gain", "O&M", "Disaster", "Labor", "End"]
    vals = [42, 18, 12, -14, -9, -8, None]
    fig, ax = plt.subplots(figsize=(11, 6))
    cum = 0; xs = np.arange(len(labels))
    for i, (lab, v) in enumerate(zip(labels, vals)):
        if v is None:
            ax.bar(i, cum, color=BLUE, width=0.6)
            ax.text(i, cum + 1, f"{cum:.0f}", ha="center", fontsize=10)
            continue
        if i == 0:
            ax.bar(i, v, color=BLUE, width=0.6); cum = v
            ax.text(i, v + 1, f"{v:.0f}", ha="center", fontsize=10)
        else:
            color = GREEN if v >= 0 else CLAY
            ax.bar(i, v, bottom=cum, color=color, width=0.6)
            ax.text(i, cum + v + (1 if v >= 0 else -2.5), f"{v:+.0f}", ha="center", fontsize=10)
            if i < len(labels) - 2:
                ax.plot([i + 0.32, i + 0.68], [cum + v] * 2, color=SLATE, ls="--", lw=1)
            cum += v
    ax.set_xticks(xs, labels); ax.set_ylabel("Cumulative budget units")
    save(fig, "B6_waterfall", "Waterfall chart of cumulative budget changes")


# ----------------------------------------------------------------------------
# 7. Streamgraph
# ----------------------------------------------------------------------------
def fig_streamgraph():
    x = np.linspace(0, 12, 200)
    series = [(1 + np.sin(x * 0.6 + k) * 0.4 + rng.normal(0, 0.05, len(x))).clip(0.2) for k in range(5)]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.stackplot(x, series, baseline="wiggle", colors=PALETTE[:5], alpha=0.9)
    ax.set_xlabel("Time"); ax.set_yticks([]); ax.set_ylabel("Volume")
    save(fig, "B7_streamgraph", "Streamgraph with a wiggle baseline")


# ----------------------------------------------------------------------------
# 8. Hexbin joint plot with marginals
# ----------------------------------------------------------------------------
def fig_hexbin():
    n = 900
    x = rng.normal(0.6, 0.22, n)
    y = 0.5 * x + rng.normal(0.3, 0.12, n)
    fig = plt.figure(figsize=(9.5, 8.5))
    gs = fig.add_gridspec(4, 4, hspace=0.08, wspace=0.08)
    ax = fig.add_subplot(gs[1:4, 0:3]); axt = fig.add_subplot(gs[0, 0:3], sharex=ax); axr = fig.add_subplot(gs[1:4, 3], sharey=ax)
    hb = ax.hexbin(x, y, gridsize=32, cmap=SEQ_BLUE, mincnt=1)
    fig.colorbar(hb, ax=ax, fraction=0.046, pad=0.04, label="Count")
    axt.hist(x, bins=30, color=BLUE, alpha=0.8); axt.axis("off")
    axr.hist(y, bins=30, orientation="horizontal", color=GOLD, alpha=0.85); axr.axis("off")
    ax.set(xlabel="Driver variable", ylabel="Response variable")
    save(fig, "B8_hexbin_joint", "Hexbin density with marginal histograms")


# ----------------------------------------------------------------------------
# 9. Nested sunburst
# ----------------------------------------------------------------------------
def fig_sunburst():
    parents = ["Ecology", "Economy", "Society"]
    children = [["Water", "Vegetation"], ["Construction", "PV", "O&M"], ["Labor", "Community"]]
    inner = [34, 40, 26]
    outer = [16, 18, 15, 14, 11, 12, 14]
    outer_cols = [SAGE, GREEN, STEEL, BLUE, GOLD, SAND, MAUVE]
    fig, ax = plt.subplots(figsize=(9.5, 9))
    ax.pie(outer, radius=1, colors=outer_cols, wedgeprops=dict(width=0.32, edgecolor="white"),
           labels=[c for cs in children for c in cs], labeldistance=0.82, textprops=dict(fontsize=9))
    ax.pie(inner, radius=0.66, colors=[GREEN, BLUE, GOLD],
           wedgeprops=dict(width=0.34, edgecolor="white"), labels=parents,
           labeldistance=0.5, textprops=dict(color="white", fontsize=10, fontweight="bold"))
    ax.set(aspect="equal")
    save(fig, "B9_sunburst", "Nested sunburst of hierarchical composition")


# ----------------------------------------------------------------------------
# 10. Phase plane with vector field and trajectories
# ----------------------------------------------------------------------------
def fig_phase():
    def sys(t, z):
        x, y = z
        return [x * (2 - x - 0.6 * y), y * (1.8 - 0.5 * x - y)]
    fig, ax = plt.subplots(figsize=(9.5, 8))
    gx = np.linspace(0.05, 2.2, 18); gy = np.linspace(0.05, 2.2, 18)
    X, Y = np.meshgrid(gx, gy)
    U, V = sys(0, [X, Y])
    M = np.hypot(U, V)
    ax.quiver(X, Y, U / M, V / M, M, cmap=SEQ_BLUE, pivot="mid", alpha=0.85)
    xx = np.linspace(0.05, 2.2, 100)
    ax.plot(xx, (2 - xx) / 0.6, color=GOLD, lw=1.6, label="x nullcline")
    ax.plot(xx, 1.8 - 0.5 * xx, color=CLAY, lw=1.6, label="y nullcline")
    for start in [(0.2, 2.0), (2.0, 0.2), (0.3, 0.3), (1.9, 1.9)]:
        sol = solve_ivp(sys, [0, 12], start, max_step=0.05, rtol=1e-7)
        ax.plot(sol.y[0], sol.y[1], color=BLUE, lw=1.4, alpha=0.8)
    # interior equilibrium: solve [1 0.6; 0.5 1] [x;y] = [2; 1.8]
    xe, ye = np.linalg.solve([[1, 0.6], [0.5, 1]], [2, 1.8])
    ax.scatter(xe, ye, s=220, color=PINK, marker="*", edgecolor="black", zorder=6, label="Equilibrium")
    ax.set(xlabel="State x", ylabel="State y", xlim=(0, 2.2), ylim=(0, 2.2))
    ax.legend(fontsize=9, loc="upper right")
    save(fig, "B10_phase_plane", "Phase plane: vector field, nullclines and trajectories")


# ----------------------------------------------------------------------------
# 11. Dumbbell chart
# ----------------------------------------------------------------------------
def fig_dumbbell():
    items = ["Region 1", "Region 2", "Region 3", "Region 4", "Region 5", "Region 6"]
    before = rng.uniform(0.2, 0.7, 6)
    after = before + rng.uniform(0.08, 0.3, 6)
    fig, ax = plt.subplots(figsize=(10.5, 6.5))
    y = np.arange(6)
    for i in range(6):
        ax.plot([before[i], after[i]], [y[i]] * 2, color=SLATE, lw=2, zorder=1)
        ax.text(after[i] + 0.02, y[i], f"+{after[i]-before[i]:.2f}", va="center", fontsize=9, color=GREEN)
    ax.scatter(before, y, color=GOLD, s=130, zorder=3, label="Before")
    ax.scatter(after, y, color=BLUE, s=130, zorder=3, label="After")
    ax.set_yticks(y, items); ax.invert_yaxis()
    ax.set_xlabel("Indicator level"); ax.legend()
    save(fig, "B11_dumbbell", "Dumbbell chart of before-after change")


# ----------------------------------------------------------------------------
# 12. Clustered heatmap with dendrograms
# ----------------------------------------------------------------------------
def fig_clustermap():
    data = rng.normal(0, 1, (12, 10))
    cols = [f"V{i+1}" for i in range(10)]; rows = [f"R{i+1}" for i in range(12)]
    df = pd.DataFrame(data, index=rows, columns=cols)
    g = sns.clustermap(df, cmap=DIVERGING, center=0, figsize=(10.5, 9.5),
                       method="ward", linewidths=0.4, linecolor="white")
    g.fig.suptitle("Clustered heatmap with hierarchical dendrograms", y=1.02, fontweight="bold", fontsize=14)
    g.fig.text(0.02, 0.01, NOTE, fontsize=8, color="#555555")
    g.savefig(output_path("batch2", "B12_clustermap", "png"), dpi=300, bbox_inches="tight")
    plt.close(g.fig)


if __name__ == "__main__":
    for fn in [fig_alluvial, fig_ridge, fig_bump, fig_raincloud, fig_network,
               fig_waterfall, fig_streamgraph, fig_hexbin, fig_sunburst,
               fig_phase, fig_dumbbell, fig_clustermap]:
        fn()
    print("Saved 12 batch-2 demo figures to", OUT)
