"""v7_m1_bucket_figure.py - how the M1 storage bucket (Algorithm 3) works.

Run from anywhere:  python Code/v7_m1_bucket_figure.py
Panels: (a) bucket schematic; (b) stress coefficient K_s; (c) daily storage over one long-run
year; (d) daily demand vs actual transpiration. Panels (c)-(d) re-run the bucket day by day
with the adopted M1 parameters and check the monthly totals against v7_m1_water.water_year.
Writes Figures/M1/m1_f10_bucket_mechanism.{pdf,png}.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v7_m1_figures import (BLUE, FULL_W, INK, INK2, LIMIT, MUTED, RAMP, RED, RES, plt, save)
from v7_m1_water import WaterParameters, equilibrium, water_year

QUOTAS = (300, 1500)  # mm/yr: one water-limited case, one case with overflow


def daily_year(v, m0, quota, forcing, p):
    """Same arithmetic as water_year, but keeps every day."""
    demand_m = p.c * min(1., 2 * v / p.v_full_pct) * forcing[:, 2]
    weights = forcing[:, 2] / forcing[:, 2].sum()
    m, rows = m0, []
    for i in range(12):
        days, rain, _ = forcing[i]
        days = int(days)
        inflow = p.rain_fraction * rain + p.eta_w * quota * weights[i] \
            + p.groundwater_mm_yr * days / forcing[:, 0].sum()
        for _ in range(days):
            b = m + inflow / days
            q = max(b - p.capacity_mm, 0.)
            b -= q
            ks = min(1., b / ((1 - p.depletion_fraction) * p.capacity_mm))
            d = demand_m[i] / days
            ta = min(b, ks * d)
            m = b - ta
            rows.append(dict(month=i + 1, M=m, D=d, Ta=ta, Q=q, Ks=ks))
    return pd.DataFrame(rows)


def panel_schematic(ax, p, runs, label=''):
    C, thr = p.capacity_mm, (1 - p.depletion_fraction) * p.capacity_mm
    t = np.arange(1, 366)
    ax.set_title(label + "One daily step of the bucket")
    ax.set_xlim(0, 10); ax.set_ylim(0, 8.0); ax.axis("off")
    x0, x1, y0, y1 = 3.0, 6.4, 0.6, 5.2               # bucket walls; top = capacity C
    lvl = y0 + (y1 - y0) * 0.38                         # storage level M
    ythr = y0 + (y1 - y0) * (thr / C)
    ax.add_patch(Rectangle((x0, y0), x1 - x0, lvl - y0, color=RAMP[0], lw=0, zorder=1))
    ax.plot([x0, x0, x1, x1], [y1, y0, y0, y1], color=INK, lw=1.2, zorder=3)
    ax.plot([x0 - 0.1, x1 + 0.1], [y1, y1], **LIMIT)
    ax.plot([x0, x1], [ythr, ythr], **LIMIT)
    ax.text(x1 + 0.2, y1, "capacity $C$", va="center", fontsize=7.5, color=INK2)
    ax.text(x1 + 0.2, ythr, "$(1-p)C$:\nstress below", va="center", fontsize=7.5, color=INK2)
    ax.text((x0 + x1) / 2, (y0 + lvl) / 2, "storage $M$\n(carried to\nnext day, year)",
            ha="center", va="center", fontsize=7.5, color=INK)
    arrow = dict(arrowstyle="-|>", mutation_scale=9, lw=1.1)
    ax.add_patch(FancyArrowPatch((4.4, 7.2), (4.4, y1 - 0.15), color=BLUE, **arrow))
    ax.text(4.4, 7.6, r"in: $\alpha_P P+\eta_w I$", fontsize=7.5, color=INK, ha="center", va="center")
    ax.add_patch(FancyArrowPatch((x1 - 0.1, y1 + 0.1), (8.9, 6.7), color=MUTED,
                                 connectionstyle="arc3,rad=-0.3", **arrow))
    ax.text(7.2, 6.95, "overflow $Q$ (lost)", fontsize=7.5, color=INK2)
    ax.add_patch(FancyArrowPatch((x0 + 0.5, lvl), (0.9, 6.3), color=RAMP[3],
                                 connectionstyle="arc3,rad=-0.25", **arrow))
    ax.text(0.0, 6.75, r"out: $T_a=\min(M,K_sD)$", fontsize=7.5, color=INK)



def panel_stress(ax, p, runs, label=''):
    C, thr = p.capacity_mm, (1 - p.depletion_fraction) * p.capacity_mm
    t = np.arange(1, 366)
    ax.set_title(label + "Stress coefficient $K_s$")
    m = np.linspace(0, C, 300)
    ax.plot(m, np.minimum(1, m / thr), color=BLUE, lw=1.6)
    ax.axvline(thr, **LIMIT); ax.axvline(C, **LIMIT)
    ax.text(thr * 0.56, 0.05, "stressed:\n$K_s=M/[(1-p)C]$", ha="center", fontsize=7.5, color=INK2)
    ax.text((thr + C) / 2, 0.55, "no stress:\n$K_s=1$", ha="center", fontsize=7.5, color=INK2)
    ax.set_xlim(0, C + 8); ax.set_ylim(0, 1.12)
    ax.set_xlabel("Storage after inflow (mm)"); ax.set_ylabel("$K_s$")
    ax.set_xticks([0, thr, C]); ax.set_xticklabels(["0", f"{thr:g}", f"{C:g}"])



def panel_storage(ax, p, runs, label=''):
    C, thr = p.capacity_mm, (1 - p.depletion_fraction) * p.capacity_mm
    t = np.arange(1, 366)
    ax.set_title(label + "Storage through a long-run year")
    t = np.arange(1, 366)
    colors = {QUOTAS[0]: BLUE, QUOTAS[1]: RAMP[4]}
    for quota, run in runs.items():
        ax.plot(t, run["day"].M, color=colors[quota], lw=1.4,
                label=f"{quota} mm/yr (V*={run['V']:.1f}%)")
    ax.axhline(C, **LIMIT); ax.axhline(thr, **LIMIT)
    ax.text(4, C + 2, "capacity", fontsize=7.5, color=RED)
    ax.text(4, thr + 2, "stress threshold", fontsize=7.5, color=RED)
    ax.set_xlim(1, 365); ax.set_ylim(0, C + 12)
    ax.set_xticks([1, 91, 182, 274, 365]); ax.set_xticklabels(["Jan", "Apr", "Jul", "Oct", "Dec"])
    ax.set_ylabel("Storage $M$ (mm)")
    ax.legend(loc="center left", bbox_to_anchor=(0, 0.6), fontsize=7.5)



def panel_demand(ax, p, runs, label=''):
    C, thr = p.capacity_mm, (1 - p.depletion_fraction) * p.capacity_mm
    t = np.arange(1, 366)
    q0 = QUOTAS[0]
    day = runs[q0]["day"]
    ax.set_title(label + f"Demand met at {q0} mm/yr")
    ax.fill_between(t, day.Ta, day.D, color=RAMP[0], lw=0, label="unmet demand")
    ax.plot(t, day.D, color=MUTED, lw=1.1, label="demand $D$")
    ax.plot(t, day.Ta, color=BLUE, lw=1.4, label="transpiration $T_a$")
    ax.text(362, day.D.max() * 1.33,
            rf"$\overline{{W}}=\Sigma T_a/\Sigma D={runs[q0]['W']:.2f}$",
            fontsize=8, color=INK, ha="right")
    ax.set_xlim(1, 365); ax.set_ylim(0, day.D.max() * 1.45)
    ax.set_xticks([1, 91, 182, 274, 365]); ax.set_xticklabels(["Jan", "Apr", "Jul", "Oct", "Dec"])
    ax.set_ylabel("mm/day")
    ax.legend(loc="upper left", fontsize=7.5, borderaxespad=0.2)



def main():
    js = json.loads((RES / "model1_results.json").read_text())
    ap = js["adopted_parameters"]
    p = WaterParameters(**ap["water"])
    clim = pd.read_csv(RES / "section_forcing_climatology.csv")
    forcing = clim[["days", "P_mm", "ET0g_mm"]].to_numpy(float)
    K, r, d = ap["K_section_pct"], ap["r"], ap["d"]

    runs = {}
    for quota in QUOTAS:
        eq = equilibrium(0.9 * K, p.capacity_mm / 2, K, r, d, forcing, quota, p)
        assert eq["converged"], quota
        # equilibrium returns end-of-year storage; that is the next year's start
        day = daily_year(eq["V_pct"], eq["M_mm"], quota, forcing, p)
        _, w, monthly = water_year(eq["V_pct"], eq["M_mm"], quota, forcing, p)
        ref = pd.DataFrame(monthly)
        mine = day.groupby("month")[["Ta", "Q"]].sum().to_numpy()
        assert np.allclose(mine, ref[["transpiration_mm", "drainage_mm"]].to_numpy(), atol=1e-9)
        assert abs(day.Ta.sum() / day.D.sum() - w) < 1e-9
        runs[quota] = dict(day=day, V=eq["V_pct"], W=w)

    # combined 2x2 (kept for the M1 README)
    fig = plt.figure(figsize=(FULL_W, 4.9))
    gs = fig.add_gridspec(2, 2, hspace=0.55, wspace=0.28)
    for k, (f, lab) in enumerate([(panel_schematic, "(a) "), (panel_stress, "(b) "),
                                  (panel_storage, "(c) "), (panel_demand, "(d) ")]):
        f(fig.add_subplot(gs[k // 2, k % 2]), p, runs, lab)
    save(fig, "m1_f10_bucket_mechanism")

    # separate figures for the paper
    fig, ax = plt.subplots(figsize=(3.6, 2.5))
    panel_schematic(ax, p, runs); ax.set_title("")
    save(fig, "m1_f10a_bucket_schematic")
    fig, ax = plt.subplots(figsize=(3.4, 2.3))
    panel_stress(ax, p, runs); ax.set_title("")
    fig.tight_layout(); save(fig, "m1_f10b_stress_ramp")
    fig, axs = plt.subplots(1, 2, figsize=(FULL_W, 2.4), gridspec_kw=dict(wspace=0.3))
    panel_storage(axs[0], p, runs, "(a) "); panel_demand(axs[1], p, runs, "(b) ")
    fig.tight_layout(); save(fig, "m1_f10c_year_water")

    for quota, run in runs.items():
        dd = run["day"]
        print(quota, "V*", round(run["V"], 2), "W", round(run["W"], 3), "overflow", round(dd.Q.sum(), 1),
              "stressed days", int((dd.Ks < 1).sum()), "min M", round(dd.M.min(), 1), "max M", round(dd.M.max(), 1))


if __name__ == "__main__":
    main()
