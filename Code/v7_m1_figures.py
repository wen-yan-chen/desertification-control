"""v7_m1_figures.py - Model 1 figures drawn from the current tables in Results/v7/model1.

Run from anywhere:  python Code/v7_m1_figures.py
Reads only Results/v7/model1/*.csv and model1_results.json (no model re-run).
Writes PDF (for LaTeX) and PNG (for preview) to Figures/M1/.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

BASE = Path(__file__).resolve().parents[1]
RES = BASE / "Results" / "v7" / "model1"
FIG = BASE / "Figures" / "M1"
FIG.mkdir(exist_ok=True)

# Palette: validated with the dataviz validator (light surface #fcfcfb).
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURFACE = "#e1e0d9", "#c3c2b7", "#ffffff"
RAMP = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#0d366b"]  # ordinal, light -> dark
NEUTRAL = "#a8a7a0"
RED = "#d03b3b"  # limit lines only, never a data series
# Limits a state is held against (capacity K, plateau, W = 1, storage capacity) share one style;
# reference values, interval bounds and event markers stay grey. Drawn just under the data lines
# (and above bars), so a curve that reaches its limit is not hidden by it.
LIMIT = dict(color=RED, lw=1.2, ls=(0, (5, 2.5)), zorder=1.9)
FULL_W, HALF_W = 6.3, 3.1  # inches, MCM text width

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 9, "axes.titlesize": 9.5, "axes.labelsize": 9,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.6, "axes.labelcolor": INK,
    "xtick.color": INK2, "ytick.color": INK2, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5,
    "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True,
    "axes.titlelocation": "left", "axes.titleweight": "bold",
    "legend.frameon": False, "lines.linewidth": 1.4, "lines.markersize": 4,
    "figure.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "savefig.dpi": 300, "savefig.bbox": "tight", "pdf.fonttype": 42,
})

SITE_NAME = {"YT": "Yutian", "MF": "Minfeng", "QM": "Qiemo", "RQ": "Ruoqiang",
             "KEL": "Korla", "YL": "Yuli", "ALE": "Alar"}
SITES = ["YT", "MF", "QM", "RQ", "KEL", "YL", "ALE"]
V_LABEL = "Cover proxy $V$ (%)"


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"{name}.{ext}")
    plt.close(fig)
    print("wrote", name)



def load():
    t = {p.stem: pd.read_csv(p) for p in RES.glob("*.csv")}
    t["json"] = json.loads((RES / "model1_results.json").read_text(encoding="utf-8"))
    return t


# --------------------------------------------------------------------------- 1
def fig_station_series(t):
    """Observed cover, one-step predictions, free run from 2022, and persistence per site."""
    yt, pp, fr = t["yearly_table"], t["prediction_pairs"], t["free_running_holdout"]
    fig, axes = plt.subplots(2, 4, figsize=(FULL_W, 3.6), sharex=True)
    for ax, s in zip(axes.flat, SITES):
        y = yt[yt.site == s].sort_values("year")
        p = pp[pp.site == s].sort_values("target_year")
        f = fr[fr.site == s].sort_values("year")
        K = y.K.iloc[0]
        ax.axvspan(2022.5, 2025.5, color="#f0efec", lw=0, zorder=0)
        ax.axhline(K, **LIMIT)
        ax.plot(y.year, y.V, color=INK, lw=1.0, marker="o", ms=3.2, zorder=3)
        ax.plot(p.target_year, p.predicted_x * p.K, color=BLUE, lw=0, marker="D", ms=3.4, zorder=4)
        ax.plot(np.r_[2022, f.year], np.r_[f.persistence_2022_pct.iloc[0], f.predicted_pct],
                color=ORANGE, lw=2.0, zorder=5)
        # Thinner line drawn on top so it stays visible where the free run is flat.
        ax.hlines(f.persistence_2022_pct.iloc[0], 2022, 2025, color=AQUA, lw=1.0, zorder=6)
        ax.set_title(f"{SITE_NAME[s]} ({s})", fontsize=8.5)
        ax.text(2015, K, "K", fontsize=7, color=INK2, va="bottom")
        lo, hi = min(y.V.min(), f.predicted_pct.min()), max(K, y.V.max())
        ax.set_ylim(lo - 2.5, hi + 2.5)
        ax.set_xticks([2015, 2019, 2023])
    for ax in axes[:, 0]:
        ax.set_ylabel(V_LABEL)
    leg = axes.flat[-1]
    leg.axis("off")
    handles = [Line2D([], [], color=INK, marker="o", ms=3.2, lw=1.0, label="Observed (Jun-Sep)"),
               Line2D([], [], color=BLUE, marker="D", ms=3.4, lw=0, label="One-step prediction"),
               Line2D([], [], color=ORANGE, lw=1.4, label="Free run from 2022"),
               Line2D([], [], color=AQUA, lw=1.2, label="Persistence (2022 value)"),
               Line2D([], [], label="Local capacity K", **LIMIT),
               plt.Rectangle((0, 0), 1, 1, color="#f0efec", label="Hold-out 2023-2025")]
    leg.legend(handles=handles, loc="center left", fontsize=7.5, handlelength=1.8)
    fig.suptitle("Station cover proxy: calibration years and hold-out", x=0.01, ha="left",
                 fontweight="bold", fontsize=10)
    fig.tight_layout(h_pad=0.6, w_pad=0.6)
    save(fig, "m1_f01_station_series")


# --------------------------------------------------------------------------- 2
def fig_holdout_skill(t):
    pp, hs, js = t["prediction_pairs"], t["holdout_by_site"], t["json"]
    fit, base = js["station_fit"]["M0 (r,d)"], js["station_fit"]["baselines"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(FULL_W, 2.9), gridspec_kw={"width_ratios": [1, 1.15]})

    lim = (0.55, 1.0)
    a.plot(lim, lim, color=AXIS, lw=0.8, zorder=1)
    for split, col, mk, lab in (("train", NEUTRAL, "o", "Train (target <= 2022)"),
                                ("test", BLUE, "D", "Hold-out (2023-2025)")):
        d = pp[pp.split == split]
        a.scatter(d.observed_x, d.predicted_x, s=16, color=col, marker=mk,
                  edgecolor=SURFACE, linewidth=0.6, label=f"{lab}, n={len(d)}", zorder=3)
    a.set(xlim=lim, ylim=lim, xlabel="Observed $x_{t+1}=V/K$", ylabel="Predicted $x_{t+1}$")
    a.set_aspect("equal")
    a.set_title("(a) One-step transfer, pooled $r,d$")
    a.legend(loc="upper left", fontsize=7.2, handletextpad=0.3)
    a.text(0.98, 0.03,
           f"RMSE train {fit['rmse_train']:.4f}\nRMSE hold-out {fit['rmse_test']:.4f}\n"
           f"persistence {base['persistence_rmse_test']:.4f}\n$R^2$ hold-out {fit['r2_test']:.3f}",
           transform=a.transAxes, ha="right", va="bottom", fontsize=7, color=INK2)

    hs = hs.sort_values("mse_skill_vs_persistence").reset_index(drop=True)
    ypos = np.arange(len(hs))
    for i, r in hs.iterrows():
        b.plot([r.persistence_rmse, r.rmse], [i, i], color=AXIS, lw=1.2, zorder=1)
    b.scatter(hs.persistence_rmse, ypos, s=26, color=AQUA, label="Persistence", zorder=3,
              edgecolor=SURFACE, linewidth=0.6)
    b.scatter(hs.rmse, ypos, s=26, color=BLUE, marker="D", label="Model M0", zorder=3,
              edgecolor=SURFACE, linewidth=0.6)
    b.set_yticks(ypos, [f"{SITE_NAME[s]} ({s})" for s in hs.site])
    xmax = max(hs.rmse.max(), hs.persistence_rmse.max())
    b.set_xlim(0, xmax * 1.45)
    for i, r in hs.iterrows():
        b.text(xmax * 1.43, i, f"{r.mse_skill_vs_persistence:+.2f}", ha="right", va="center",
               fontsize=7.5, color=INK if r.mse_skill_vs_persistence > 0 else INK2)
    b.text(xmax * 1.43, len(hs) - 0.35, "MSE skill", ha="right", va="bottom", fontsize=7, color=MUTED)
    b.set_xlabel("Hold-out RMSE (V/K), n = 3 per site")
    b.set_title("(b) Hold-out error by site vs persistence")
    b.grid(axis="y", visible=False)
    b.legend(loc="upper left", ncol=2, fontsize=7.2, handletextpad=0.2, columnspacing=0.8)
    b.set_ylim(-0.6, len(hs) + 0.5)
    fig.tight_layout(w_pad=1.2)
    save(fig, "m1_f02_holdout_skill")


# --------------------------------------------------------------------------- 3
def fig_bootstrap(t):
    bs, js = t["parameter_cluster_bootstrap"], t["json"]
    th = js["station_fit"]["M0 (r,d)"]["theta"]
    pct = js["uncertainty"]["bootstrap_percentiles"]
    loso = js["station_fit"]["leave_one_station_out_M0"]
    fig = plt.figure(figsize=(HALF_W * 1.35, HALF_W * 1.35))
    gs = fig.add_gridspec(2, 2, width_ratios=[4, 1], height_ratios=[1, 4], hspace=0.05, wspace=0.05)
    ax = fig.add_subplot(gs[1, 0])
    hx = fig.add_subplot(gs[0, 0], sharex=ax)
    hy = fig.add_subplot(gs[1, 1], sharey=ax)
    ax.scatter(bs.r, bs.d, s=8, color=BLUE, alpha=0.35, lw=0, label=f"Cluster bootstrap ({len(bs)})")
    lx = [v["r"] for v in loso.values()]
    ly = [v["d"] for v in loso.values()]
    ax.scatter(lx, ly, s=14, marker="s", facecolor="none", edgecolor=INK2, lw=0.8,
               label="Leave one station out", zorder=4)
    for s, v in loso.items():
        if s == "YT":
            ax.annotate("drop YT", (v["r"], v["d"]), xytext=(-4, 4), textcoords="offset points",
                        ha="right", fontsize=7, color=INK2)
    ax.scatter(*th, s=60, marker="*", color=ORANGE, edgecolor=SURFACE, lw=0.6, zorder=5,
               label=f"Pooled fit r={th[0]:.3f}, d={th[1]:.3f}")
    ax.set(xlabel="Intrinsic growth rate $r$ (yr$^{-1}$)", ylabel="Loss rate $d$ (yr$^{-1}$)")
    ax.legend(loc="upper left", fontsize=7, handletextpad=0.2)
    for h, col, key, orient in ((hx, "r", "r", "vertical"), (hy, "d", "d", "horizontal")):
        h.hist(bs[col], bins=30, color=BLUE, alpha=0.55, orientation=orient, lw=0)
        lines = h.axvline if orient == "vertical" else h.axhline
        for q in ("0.025", "0.975"):
            lines(pct[key][q], color=INK2, lw=0.8, ls=(0, (3, 2)))
        lines(th[0] if key == "r" else th[1], color=ORANGE, lw=1.2)
        h.grid(False)
        h.tick_params(labelbottom=False, labelleft=False, length=0)
        for sp in h.spines.values():
            sp.set_visible(False)
    hx.set_title(f"95% r: {pct['r']['0.025']:.2f}-{pct['r']['0.975']:.2f};  "
                 f"d: {pct['d']['0.025']:.3f}-{pct['d']['0.975']:.3f}", fontsize=8, fontweight="normal")
    fig.suptitle("Parameter uncertainty from 7 station clusters", x=0.02, ha="left",
                 fontweight="bold", fontsize=10, y=0.99)
    save(fig, "m1_f03_parameter_bootstrap")


# --------------------------------------------------------------------------- 4
def fig_cohort(t):
    c, js = t["cohort_diagnostic_pairs"], t["json"]["cohort_transfer"]
    fig, axes = plt.subplots(1, 2, figsize=(FULL_W, 2.7), sharey=True)
    for ax, split, title, key in (
            (axes[0], "fit", "(a) Calibration windows CON1-3", "calibration_CON1_3"),
            (axes[1], "spatial_diagnostic", "(b) Spatial diagnostic CON4", "spatial_diagnostic_CON4")):
        d = c[c.diagnostic_split == split]
        ax.scatter(d.tau, d.V, s=np.clip(d.n, 4, 60) * 0.8, color=BLUE, alpha=0.45, lw=0,
                   label="Cohort-year mean (size = pixels)")
        curve = c[["tau", "predicted_transfer_pct"]].drop_duplicates().sort_values("tau")
        curve = curve[curve.tau <= d.tau.max()]
        ax.plot(curve.tau, curve.predicted_transfer_pct, color=ORANGE, lw=1.6,
                label="Station r, d transferred")
        ax.axhline(js["plateau"], **LIMIT)
        m = js[key]
        # Stats go in empty corners: top-right in (a), top-left in (b).
        x0, ha = (0.98, "right") if split == "fit" else (0.03, "left")
        ax.text(x0, 0.97, f"n = {m['n']}\ntransfer $R^2$ = {m['transfer_r2']:.2f}\n"
                          f"RMSE = {m['transfer_rmse']:.1f} pp", transform=ax.transAxes,
                ha=ha, va="top", fontsize=7.2, color=INK2)
        ax.set_title(title)
        ax.set_xlabel(r"Years since establishment $\tau$")
    axes[0].text(0.2, js["plateau"], "plateau", fontsize=7, color=INK2, va="bottom")
    axes[0].set_ylabel(V_LABEL)
    axes[0].legend(loc="upper left", fontsize=7)
    fig.tight_layout(w_pad=1.0)
    save(fig, "m1_f04_cohort_diagnostic")


# --------------------------------------------------------------------------- 5
def fig_forcing(t):
    f = t["section_forcing_climatology"]
    mon = list("JFMAMJJASOND")
    fig, axes = plt.subplots(1, 3, figsize=(FULL_W, 2.3))
    a, b, c = axes
    a.bar(f.month, f.P_mm, color=BLUE, width=0.7)
    a.set(title=f"(a) Precipitation, {f.P_mm.sum():.0f} mm/yr", ylabel="mm/month")
    b.plot(f.month, f.ET0_mm, color=NEUTRAL, marker="o", ms=3, label=f"$ET_0$ ({f.ET0_mm.sum():.0f})")
    b.plot(f.month, f.ET0g_mm, color=ORANGE, marker="o", ms=3,
           label=f"Growing-season $ET_{{0g}}$ ({f.ET0g_mm.sum():.0f})")
    b.set(title="(b) Reference ET (mm/yr)", ylabel="mm/month")
    b.legend(loc="upper left", fontsize=6.8)
    b.set_ylim(0, f.ET0_mm.max() * 1.35)
    c.bar(f.month, f.E, color=BLUE, width=0.7)
    c.axhline(1, color=MUTED, lw=0.8, ls=(0, (3, 2)))
    c.set(title="(c) Wind index $E$", ylabel="relative to training mean")
    for ax in axes:
        ax.set_xticks(f.month, mon)
        ax.grid(axis="x", visible=False)
    fig.tight_layout(w_pad=0.8)
    save(fig, "m1_f05_forcing_climatology")


# --------------------------------------------------------------------------- 6
def fig_water_cover(t):
    w = t["water_cover_curve"]
    I = w.irrigation_mm_yr
    fig, axes = plt.subplots(2, 2, figsize=(FULL_W, 4.2), sharex=True)
    (a, b), (c, d) = axes
    a.plot(I, w.V_steady_pct, color=BLUE, marker="o", ms=3.5, label="Periodic steady state")
    a.plot(I, w.V_from_planting_pct, color=ORANGE, lw=0, marker="x", ms=4, label="From planting (V=2%)")
    for x0 in (300, 600):
        v = w.loc[I == x0, "V_steady_pct"].item()
        a.annotate(f"{v:.1f}%", (x0, v), xytext=(4, -10), textcoords="offset points", fontsize=7.2,
                   color=INK2)
    a.set(title="(a) Periodic steady cover", ylabel=V_LABEL)
    a.legend(loc="lower right", fontsize=7)
    b.plot(I, w.W, color=BLUE, marker="o", ms=3.5)
    b.axhline(1, **LIMIT)
    b.set(title="(b) Transpiration ratio $W$ (actual/potential)", ylabel="$W$", ylim=(0, 1.08))
    c.plot(I, w.M_periodic_end_mm, color=BLUE, marker="o", ms=3.5)
    c.axhline(75, **LIMIT)
    c.text(30, 76, "capacity 75 mm", fontsize=7, color=INK2, va="bottom")
    c.set(title="(c) Available storage $M$ at year end", ylabel="mm", ylim=(0, 85))
    d.plot(I, w.relative_erosion_scenario, color=BLUE, marker="o", ms=3.5)
    d.set(title="(d) Relative erosion (shelter function)", ylabel="relative to bare", ylim=(0, 1.02))
    for ax in (c, d):
        ax.set_xlabel("Irrigation on treated area (mm/yr)")
        sec = ax.secondary_xaxis("bottom", functions=(lambda x: x * 10, lambda x: x / 10))
        sec.spines["bottom"].set_position(("outward", 26))
        sec.set_xlabel("m$^3$/ha/yr", fontsize=7.5, color=INK2)
        sec.tick_params(labelsize=7, colors=INK2)
    fig.tight_layout(h_pad=0.8, w_pad=1.0)
    save(fig, "m1_f06_water_cover_curve")


# --------------------------------------------------------------------------- 7
SCEN = [("I0", "0", NEUTRAL), ("I100", "100", RAMP[0]), ("I300", "300", RAMP[1]),
        ("I600", "600", RAMP[2]), ("I1000", "1000", RAMP[3]), ("I2000", "2000", RAMP[4])]


def fig_scenarios(t):
    a_ = t["scenario_annual"]
    fig, axes = plt.subplots(1, 3, figsize=(FULL_W, 2.6), sharex=True)
    cols = [("V_end_pct", "(a) Cover proxy $V$", "%"),
            ("M_end_mm", "(b) Storage $M$ at year end", "mm"),
            ("W", "(c) Transpiration ratio $W$", "")]
    for ax, (col, title, unit) in zip(axes, cols):
        for sc, lab, color in SCEN:
            d = a_[a_.scenario == sc]
            ax.plot(d.calendar_year, d[col], color=color, lw=1.3, label=f"{lab} mm/yr")
        # Same as 600 mm/yr through 2035, so draw it only from where it departs.
        d = a_[(a_.scenario == "stop_after_10") & (a_.calendar_year >= 2035)]
        ax.plot(d.calendar_year, d[col], color=ORANGE, lw=1.6, label="600, stop after 2035")
        ax.axvline(2035.5, color=MUTED, lw=0.6, ls=(0, (3, 2)))
        ax.set_title(title)
        ax.set_ylabel(unit)
        ax.set_xticks([2026, 2034, 2042, 2050])
    axes[2].set_ylim(0, 1.05)
    end = a_[a_.calendar_year == 2050].set_index("scenario").V_end_pct
    for sc, lab, color in SCEN[1:]:
        axes[0].text(2050.6, end[sc], f"{end[sc]:.0f}", fontsize=6.8, color=INK2, va="center")
    axes[0].text(2050.6, end["stop_after_10"], f"{end['stop_after_10']:.0f}", fontsize=6.8,
                 color=INK2, va="center")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=7, fontsize=7, bbox_to_anchor=(0.5, -0.07),
               handlelength=1.4, columnspacing=0.9)
    fig.tight_layout(w_pad=1.0, rect=(0, 0.04, 1, 1))
    save(fig, "m1_f07_scenario_trajectories")


# --------------------------------------------------------------------------- 8
def fig_monthly_water(t):
    m = t["scenario_monthly_water"]
    d = m[(m.scenario == "I300") & (m.calendar_year == 2050)].sort_values("month")
    mon = list("JFMAMJJASOND")
    fig = plt.figure(figsize=(FULL_W, 4.3))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.25, 1], width_ratios=[1, 1])
    a = fig.add_subplot(gs[0, 0])
    b = fig.add_subplot(gs[0, 1])
    c = fig.add_subplot(gs[1, :])
    x = d.month.values
    wdt = 0.7
    a.bar(x, d.effective_rain_mm, wdt, color=AQUA, label="Effective rain", edgecolor=SURFACE, lw=0.5)
    a.bar(x, d.net_irrigation_mm, wdt, bottom=d.effective_rain_mm, color=BLUE,
          label="Net irrigation", edgecolor=SURFACE, lw=0.5)
    a.bar(x, -d.transpiration_mm, wdt, color=ORANGE, label="Transpiration", edgecolor=SURFACE, lw=0.5)
    a.bar(x, -d.drainage_mm, wdt, bottom=-d.transpiration_mm, color=NEUTRAL, label="Deep drainage",
          edgecolor=SURFACE, lw=0.5)
    a.axhline(0, color=AXIS, lw=0.8)
    a.set(title="(a) Monthly fluxes, 300 mm/yr, 2050", ylabel="mm/month (in + / out -)")
    a.legend(loc="lower left", fontsize=6.8, ncol=2, columnspacing=0.8)
    a.set_ylim(-75, 70)
    b.plot(x, d.potential_transpiration_mm, color=NEUTRAL, marker="o", ms=3, label="Potential")
    b.plot(x, d.transpiration_mm, color=ORANGE, marker="o", ms=3, label="Actual")
    b.set(title="(b) Transpiration demand vs supply", ylabel="mm/month")
    b.legend(loc="upper left", fontsize=7)
    for ax in (a, b):
        ax.set_xticks(x, mon)
        ax.grid(axis="x", visible=False)
    for sc, lab, color in (("I300", "300 mm/yr", RAMP[1]), ("I600", "600 mm/yr", RAMP[2]),
                           ("stop_after_10", "600, stop after 2035", ORANGE)):
        s = m[m.scenario == sc].sort_values(["calendar_year", "month"])
        if sc == "stop_after_10":  # same as 600 mm/yr through 2035
            s = s[(s.calendar_year >= 2036) | ((s.calendar_year == 2035) & (s.month == 12))]
        tt = s.calendar_year + (s.month - 0.5) / 12
        c.plot(tt, s.M_end_mm, color=color, lw=1.0 if sc != "stop_after_10" else 1.3, label=lab)
    c.axhline(75, **LIMIT)
    c.axvline(2036, color=MUTED, lw=0.6, ls=(0, (3, 2)))
    c.text(2036.2, 60, "irrigation stops", fontsize=7, color=MUTED)
    c.text(2050.9, 76, "capacity", fontsize=7, color=INK2, ha="right", va="bottom")
    c.set(title="(c) Monthly available storage $M$, 2026-2050", ylabel="mm", ylim=(0, 82),
          xlim=(2026, 2051))
    c.legend(loc="center right", bbox_to_anchor=(1.0, 0.55), fontsize=7, ncol=3)
    resid = m.balance_residual_mm.abs().max()
    fig.tight_layout(h_pad=1.0, w_pad=1.2)
    save(fig, "m1_f08_monthly_water_balance")


# --------------------------------------------------------------------------- 9
def fig_sensitivity(t):
    s, w = t["sensitivity"], t["water_cover_curve"]
    base = w.set_index("irrigation_mm_yr").V_steady_pct
    js = t["json"]["adopted_parameters"]["water"]
    labels = {"capacity_mm": ("Storage capacity", "mm", js["capacity_mm"]),
              "rain_fraction": ("Effective rain fraction", "", js["rain_fraction"]),
              "c": ("Demand coefficient c", "", js["c"]),
              "eta_w": ("Irrigation efficiency $\\eta_w$", "", js["eta_w"]),
              "depletion_fraction": ("Depletion fraction p", "", js["depletion_fraction"]),
              "v_full_pct": ("End-member $V_{full}$", "%", js["v_full_pct"])}
    fig, axes = plt.subplots(1, 3, figsize=(FULL_W, 2.9), gridspec_kw={"width_ratios": [1, 1, 0.8]})
    # One row order for both panels (ranked by the 300 mm/yr swing) so labels on (a) apply to (b).
    d300 = s[s.irrigation_mm_yr == 300]
    swing = {p: (d300[d300.parameter == p].V_pct - base[300]).abs().max() for p in labels}
    order = sorted(labels, key=lambda p: swing[p])
    for ax, I, title in ((axes[0], 300, "(a) 300 mm/yr"), (axes[1], 600, "(b) 600 mm/yr")):
        rows = []
        for p in order:
            lab, unit, b0 = labels[p]
            d = s[(s.parameter == p) & (s.irrigation_mm_yr == I)].sort_values("value")
            lo, hi = d.iloc[0], d.iloc[-1]
            rows.append((lab, lo.value, hi.value, lo.V_pct - base[I], hi.V_pct - base[I], b0))
        for i, (lab, vlo, vhi, dlo, dhi, b0) in enumerate(rows):
            ax.barh(i, dlo, 0.6, color=BLUE, edgecolor=SURFACE, lw=0.5)
            ax.barh(i, dhi, 0.6, color=ORANGE, edgecolor=SURFACE, lw=0.5)
            fmt = (lambda v: f"{v:g}")
            ax.text(min(dlo, dhi, 0) - 0.12, i, fmt(vlo if dlo < dhi else vhi), ha="right", va="center",
                    fontsize=6.8, color=INK2)
            ax.text(max(dlo, dhi, 0) + 0.12, i, fmt(vhi if dhi > dlo else vlo), ha="left", va="center",
                    fontsize=6.8, color=INK2)
        ax.axvline(0, color=INK2, lw=0.8)
        ax.set_yticks(range(len(rows)), [r[0] for r in rows] if I == 300 else [])
        ax.set_xlim(-4.2, 4.2)
        ax.set_ylim(-0.6, len(rows) - 0.4)
        ax.set_xlabel(f"Change in steady V (pp)\nbaseline {base[I]:.1f}%")
        ax.set_title(title)
        ax.grid(axis="y", visible=False)
    fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=BLUE, label="Low tested value"),
                        plt.Rectangle((0, 0), 1, 1, color=ORANGE, label="High tested value")],
               loc="lower center", ncol=2, fontsize=7.2, bbox_to_anchor=(0.4, -0.05))
    k = s[s.parameter == "k_scenario"].sort_values("value")
    c = axes[2]
    c.plot(k.value, k.V_pct, color=BLUE, marker="o", ms=4)
    for _, r in k.iterrows():
        c.annotate(f"{r.V_pct:.1f}", (r.value, r.V_pct), xytext=(3, 3), textcoords="offset points",
                   fontsize=7, color=INK2)
    c.set(title="(c) Wind damage k, 300 mm/yr", xlabel="Wind-damage coefficient k", ylabel=V_LABEL,
          ylim=(12, 19.5), xlim=(-0.01, 0.12))
    fig.tight_layout(w_pad=0.9, rect=(0, 0.05, 1, 1))
    save(fig, "m1_f09_sensitivity")


def main():
    t = load()
    for f in (fig_station_series, fig_holdout_skill, fig_bootstrap, fig_cohort, fig_forcing,
              fig_water_cover, fig_scenarios, fig_monthly_water, fig_sensitivity):
        f(t)


if __name__ == "__main__":
    main()
