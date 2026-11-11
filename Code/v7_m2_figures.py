"""v7_m2_figures.py - Model 2 figures drawn from the current tables in Results/v7/model2.

Run from anywhere:  python Code/v7_m2_figures.py
Reads only Results/v7/model2/*.csv, model2_results.json and scenario_configs.json
(no optimisation re-run). Writes PDF (for LaTeX) and PNG (for preview) to Figures/M2/.

Style (fonts, sizes, neutrals) is shared with v7_m1_figures.py. Colour roles used here:
new build = aqua, stock maintenance (O&M incl. water cost) = violet, PV = orange,
water volume = blue. Everything plotted is a conditional scenario (formal_model_ready=false).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D

import v7_m1_figures as m1  # sets the shared rcParams on import

BASE = Path(__file__).resolve().parents[1]
RES = BASE / "Results" / "v7" / "model2"
FIG = BASE / "Figures" / "M2"
FIG.mkdir(parents=True, exist_ok=True)

BLUE, ORANGE, AQUA = m1.BLUE, m1.ORANGE, m1.AQUA
INK, INK2, MUTED = m1.INK, m1.INK2, m1.MUTED
GRID, AXIS, SURFACE, NEUTRAL, RAMP = m1.GRID, m1.AXIS, m1.SURFACE, m1.NEUTRAL, m1.RAMP
FULL_W = m1.FULL_W
VIOLET = "#6250d6"
# Roles. Validated (dataviz validator, light surface) as the stack aqua-violet-orange.
C_BUILD, C_KEEP, C_PV, C_WATER = AQUA, VIOLET, ORANGE, BLUE
DASH = (0, (3, 2))
# Every limit the plan is held against (caps, capacities, solver tolerance, base price) is drawn
# with the red dashed style shared with the M1 figures; plain reference values stay grey.
RED, LIMIT = m1.RED, m1.LIMIT
SEQ = LinearSegmentedColormap.from_list("seq_blue", ["#f4f8fe", "#cde2fb", "#86b6ef", "#2a78d6", "#0d366b"])
MON = list("JFMAMJJASOND")


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"{name}.{ext}")
    plt.close(fig)
    print("wrote", name)


def load():
    t = {p.stem: pd.read_csv(p) for p in RES.glob("*.csv")}
    t["json"] = json.loads((RES / "model2_results.json").read_text(encoding="utf-8"))
    t["configs"] = json.loads((RES / "scenario_configs.json").read_text(encoding="utf-8"))
    return t


def check_provenance(js):
    """Stop if the tables were produced from inputs or code that differ from the working tree."""
    bad = []
    for name, want in js["input_text_sha256_lf"].items():
        got = hashlib.sha256((BASE / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if got != want:
            bad.append(name)
    if bad:
        raise SystemExit("Results/v7/model2 is out of date for: " + ", ".join(bad)
                         + "\nRe-run Code/v7_model2.py before drawing.")
    print("provenance ok:", len(js["input_text_sha256_lf"]), "inputs match model2_results.json")


def year_axis(ax, label=True):
    ax.set_xticks([1, 3, 5, 7, 9, 11, 13, 15])
    ax.set_xlim(0.3, 15.7)
    ax.grid(axis="x", visible=False)
    if label:
        ax.set_xlabel("Project year")


# --------------------------------------------------------------------------- 1
def fig_build(t):
    """15-year build and maintenance: flows as bars, stocks as lines, spending by purpose."""
    a_, cfg = t["annual"], t["json"]["config"]
    y = a_.year.values
    fig, axes = plt.subplots(2, 2, figsize=(FULL_W, 4.5), sharex=True)
    (a, b), (c, d) = axes
    w = 0.66

    a.bar(y, a_.new_area_ha, w, color=C_BUILD, label="New area (flow)")
    a.plot(y, a_.eco_area_ha, color=C_KEEP, marker="o", ms=3, label="Managed area (stock)")
    a.set(title="(a) Shelter area", ylabel="ha", ylim=(0, a_.eco_area_ha.max() * 1.15))
    a.legend(loc="center right", fontsize=7.2)

    b.bar(y, a_.new_pv_kw / 1e3, w, color=C_PV, label="New capacity (flow)")
    b.plot(y, a_.pv_installed_kw / 1e3, color=INK, marker="o", ms=3, label="Installed (stock)")
    b.plot(y, a_.pv_operating_kw / 1e3, color=MUTED, marker="s", ms=2.8, ls=DASH,
           label="Operating (from next year)")
    b.set(title="(b) PV capacity", ylabel="MW", ylim=(0, max(a_.pv_installed_kw.max() / 1e3 * 1.15, 1)))
    b.legend(loc="center right", fontsize=7.2)

    parts = [("construction_cny", C_BUILD, "Shelter construction"),
             ("om_cny", C_KEEP, "O&M incl. water"),
             ("pv_facilities_cny", C_PV, "PV capital")]
    bottom = np.zeros(len(a_))
    for col, color, lab in parts:
        c.bar(y, a_[col] / 1e6, w, bottom=bottom, color=color, label=lab, edgecolor=SURFACE, lw=0.5)
        bottom += a_[col].values / 1e6
    c.plot(y, a_.revenue_cny / 1e6, color=INK, marker="D", ms=3, lw=1.0, label="PV revenue")
    cap = cfg["annual_budget_cny"] / 1e6
    c.axhline(cap, **LIMIT)
    c.text(15.6, cap + 0.45, "annual budget cap (scenario)", fontsize=7, color=INK2, ha="right")
    c.set(title="(c) Annual spending and PV revenue", ylabel="million CNY", ylim=(0, 14.5))
    c.legend(loc="center right", fontsize=7.2, bbox_to_anchor=(1.0, 0.58))

    bottom = np.zeros(len(a_))
    for col, color, lab in (("construction_fund_share", C_BUILD, ""), ("om_fund_share", C_KEEP, ""),
                            ("pv_facilities_fund_share", C_PV, "")):
        v = a_[col].fillna(0).values * 100  # share is blank in a zero-spending year: draw nothing
        d.bar(y, v, w, bottom=bottom, color=color, edgecolor=SURFACE, lw=0.5)
        bottom += v
    d.set(title="(d) Share of that year's spending", ylabel="% (colours as in c)", ylim=(0, 100))
    d.set_yticks([0, 25, 50, 75, 100])
    for ax in (c, d):
        year_axis(ax)
    for ax in (a, b):
        year_axis(ax, label=False)
    fig.tight_layout(h_pad=0.9, w_pad=1.2)
    save(fig, "m2_f01_build_and_spending")


# --------------------------------------------------------------------------- 2
def fig_cohorts(t):
    """Cover, irrigation and storage per planting batch, and the area-weighted contribution."""
    co, cfg = t["cohorts"], t["json"]["config"]
    K = t["json"]["m1_parameters"]["K_section_pct"]
    vmin, age = cfg.get("min_cover_pct", 0.), cfg.get("min_cover_by_age_year", 1)
    order = list(co.sort_values(["year", "cohort_id"]).cohort_id.unique())
    if not 1 <= len(order) <= len(RAMP):
        raise SystemExit(f"fig_cohorts draws 1-{len(RAMP)} batches, got {len(order)}")
    colors = [RAMP[k] for k in np.linspace(0, len(RAMP) - 1, len(order)).round().astype(int)]
    meta = {}
    for cid, color in zip(order, colors):
        s = co[co.cohort_id == cid].sort_values("year")
        steps = [f"{q:g}" for q in s.irrigation_mm_yr[s.irrigation_mm_yr.diff().fillna(1) != 0]]
        path = steps[0] if len(steps) == 1 else ", ".join(steps[:-1]) + " then " + steps[-1]
        meta[cid] = (color, f"Year {s.year.iloc[0]}, {s.area_ha.iloc[0]:g} ha: {path} mm",
                     bool(s.counts_toward_score.iloc[0]))
    fig, axes = plt.subplots(2, 2, figsize=(FULL_W, 4.5), sharex=True)
    (a, b), (c, d) = axes
    for cid in order:
        color, lab, _ = meta[cid]
        s = co[co.cohort_id == cid].sort_values("year")
        a.plot(s.year, s.V_start_pct, color=color, label=lab)
        if vmin > 0 and len(s) > age:  # cover at the end of the check age = start of the next year
            a.scatter(s.year.iloc[age], s.V_start_pct.iloc[age], s=26, color=color, edgecolor=INK,
                      linewidth=0.8, zorder=4)
        b.plot(s.year, s.irrigation_mm_yr, color=color, drawstyle="steps-mid")
        c.plot(s.year, s.M_end_mm, color=color)
    a.axhline(K, **LIMIT)
    a.text(0.6, K - 0.8, f"section K = {K:.1f}%", fontsize=7, color=INK2, va="top")
    if vmin > 0:
        a.axhline(vmin, **LIMIT)
        a.text(0.6, vmin + 0.7, f"minimum cover {vmin:g}% by age {age}", fontsize=7, color=INK2)
        a.scatter([], [], s=26, color=SURFACE, edgecolor=INK, linewidth=0.8, label=f"Cover at age {age}")
    a.set(title="(a) Cover proxy at start of year", ylabel="$V_{start}$ (%)", ylim=(0, 41))
    b.set(title="(b) Irrigation on the batch area", ylabel="mm/yr  (1 mm = 10 m$^3$/ha)",
          ylim=(0, max(660, co.irrigation_mm_yr.max() * 1.1)))
    b.set_yticks(sorted(set([0]) | set(co.irrigation_mm_yr.unique())))
    cap = t["json"]["m1_parameters"]["water"]["capacity_mm"]
    c.axhline(cap, **LIMIT)
    c.text(15.6, cap - 2, "storage capacity", fontsize=7, color=INK2, ha="right", va="top")
    c.set(title="(c) Available storage $M$ at year end", ylabel="mm", ylim=(0, 82))

    bottom, counted = np.zeros(15), np.zeros(15)
    yrs = np.arange(1, 16)
    for cid in order:
        s = co[co.cohort_id == cid].set_index("year").reindex(yrs)
        v = (s.area_ha * s.V_start_pct / K).fillna(0).values
        if meta[cid][2]:
            d.bar(yrs, v, 0.66, bottom=bottom, color=meta[cid][0], edgecolor=SURFACE, lw=0.5)
            counted += v
        else:  # below the minimum-cover rule: drawn, but hollow, because it scores nothing
            d.bar(yrs, v, 0.66, bottom=bottom, facecolor=SURFACE, edgecolor=meta[cid][0], lw=0.8)
        bottom += v
    ann = t["annual"].set_index("year").reindex(yrs)
    assert np.abs(bottom - ann.effective_ha.values).max() < 1e-6, "batches do not add to annual.effective_ha"
    assert np.abs(counted - ann.counted_effective_ha.values).max() < 1e-6, "counted batches do not add up"
    d.set(title=r"(d) Effective area, area $\times$ $V_{start}/K$", ylabel="effective ha",
          ylim=(0, bottom.max() * 1.22))
    note = f"15-year score {counted.sum():.0f} effective ha-yr"
    if bottom.sum() - counted.sum() > 1e-6:
        note += f"\nhollow: below minimum cover, not scored ({bottom.sum() - counted.sum():.0f})"
    d.text(0.03, 0.96, note, transform=d.transAxes, fontsize=7.2, color=INK2, va="top")
    for ax in (c, d):
        year_axis(ax)
    for ax in (a, b):
        year_axis(ax, label=False)
    h, l = a.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=7.2, bbox_to_anchor=(0.5, -0.035),
               handlelength=1.6, columnspacing=1.2)
    fig.tight_layout(h_pad=0.9, w_pad=1.2, rect=(0, 0.03, 1, 1))
    save(fig, "m2_f02_cohorts")


# --------------------------------------------------------------------------- 3
def fig_water(t):
    """Gross withdrawal against the scenario caps, by year and by month."""
    a_, m, cfg = t["annual"], t["monthly"], t["json"]["config"]
    fig = plt.figure(figsize=(FULL_W, 4.7))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.05], width_ratios=[1, 1.15])
    a = fig.add_subplot(gs[0, 0])
    b = fig.add_subplot(gs[0, 1])
    c = fig.add_subplot(gs[1, :])

    a.bar(a_.year, a_.water_m3 / 1e4, 0.66, color=C_WATER)
    cap = cfg["annual_water_cap_m3"] / 1e4
    a.axhline(cap, **LIMIT)
    a.text(0.6, cap + 4, "annual cap (scenario)", fontsize=7, color=INK2)
    last = a_.iloc[-1]
    a.text(15.4, last.water_m3 / 1e4 + 3, f"{last.water_m3 / cfg['annual_water_cap_m3']:.0%} of cap",
           fontsize=7, color=INK2, ha="right")
    a.set(title="(a) Annual gross withdrawal", ylabel="10$^4$ m$^3$/yr", ylim=(0, 172))
    year_axis(a)

    # Years with the same monthly profile are drawn once.
    prof = m.pivot(index="year", columns="month", values="gross_water_m3")
    groups, start = [], prof.index[0]
    for y0, y1 in zip(prof.index[:-1], prof.index[1:]):
        if not np.allclose(prof.loc[y0], prof.loc[y1], rtol=2e-3, atol=30):
            groups.append((start, y0))
            start = y1
    groups.append((start, prof.index[-1]))
    caps = m[m.year == 1].sort_values("month").cap_m3.values / 1e4
    b.step(np.arange(1, 13), caps, where="mid", label="Monthly cap (scenario)", **LIMIT)
    ramp = [RAMP[i] for i in np.linspace(0, len(RAMP) - 1, len(groups)).round().astype(int)] \
        if len(groups) <= len(RAMP) else [BLUE] * len(groups)
    for (y0, y1), color in zip(groups, ramp):
        lab = f"Year {y0}" if y0 == y1 else f"Years {y0}\u2013{y1}"
        b.plot(np.arange(1, 13), prof.loc[y1].values / 1e4, color=color, marker="o", ms=2.6, lw=1.2, label=lab)
    b.set(title="(b) Monthly withdrawal by stage", ylabel="10$^4$ m$^3$/month", ylim=(0, 26))
    b.set_xticks(np.arange(1, 13), MON)
    b.grid(axis="x", visible=False)
    b.legend(loc="upper left", fontsize=6.6, handlelength=1.5, labelspacing=0.25)

    use = (m.gross_water_m3 / m.cap_m3).values.reshape(15, 12).T * 100  # rows = months
    im = c.imshow(use, cmap=SEQ, vmin=0, vmax=100, aspect="auto", origin="upper",
                  extent=(0.5, 15.5, 12.5, 0.5))
    c.set_xticks(np.arange(1, 16))
    c.set_yticks(np.arange(1, 13), MON)
    c.grid(False)
    c.set_xticks(np.arange(0.5, 16), minor=True)
    c.set_yticks(np.arange(0.5, 13), minor=True)
    c.grid(which="minor", color=SURFACE, lw=0.8)
    c.tick_params(which="both", length=0)
    for sp in c.spines.values():
        sp.set_visible(False)
    for yy in range(15):
        for mm in range(12):
            if use[mm, yy] >= 80:
                c.text(yy + 1, mm + 1, f"{use[mm, yy]:.0f}", ha="center", va="center", fontsize=6.5,
                       color=SURFACE)
    tight = m.loc[m.slack_m3.idxmin()]
    c.set(title=f"(c) Share of the monthly cap in use (%); tightest month leaves "
                f"{tight.slack_m3 / 1e4:.1f} $\\times$ 10$^4$ m$^3$", xlabel="Project year")
    cb = fig.colorbar(im, ax=c, pad=0.015, fraction=0.03)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=7, length=0)
    cb.set_label("% of cap", fontsize=7.5)
    fig.tight_layout(h_pad=1.0, w_pad=1.2)
    save(fig, "m2_f03_water_pressure")


# --------------------------------------------------------------------------- 4
def fig_frontier(t):
    """Six solved cost-ecology points. Discrete points only; no curve is fitted or implied."""
    s = t["scenario_summary"]
    f = s[s.group == "frontier"].copy()
    f["frac"] = f.case.str.replace("frontier_", "").astype(float)
    f = f.sort_values("frac").reset_index(drop=True)
    tol = t["json"]["config"]["solver_relative_gap"] * 100
    base_frac = t["json"]["config"]["ecological_target_fraction"]
    fig = plt.figure(figsize=(FULL_W, 3.5))
    gs = fig.add_gridspec(3, 2, width_ratios=[1.55, 1], hspace=0.5, wspace=0.3)
    a = fig.add_subplot(gs[:, 0])
    b = fig.add_subplot(gs[0, 1])
    c = fig.add_subplot(gs[1, 1], sharex=b)
    d = fig.add_subplot(gs[2, 1], sharex=b)

    x, yv = f.ecological_ha_year, f.net_present_cost_cny / 1e6
    a.axhline(0, color=AXIS, lw=0.8)
    a.scatter(x, yv, s=34, color=BLUE, edgecolor=SURFACE, linewidth=0.8, zorder=3)
    for _, r in f.iterrows():
        is_base = np.isclose(r.frac, base_frac)
        lab = f"{r.frac:.0%} target" + (" (base)" if is_base else "")
        if is_base:
            a.scatter(r.ecological_ha_year, r.net_present_cost_cny / 1e6, s=110, facecolor="none",
                      edgecolor=INK, linewidth=0.9, zorder=4)
        right = r.frac == 0  # no room to the upper left of the first point
        a.annotate(f"{lab}\n{r.net_present_cost_cny / 1e6:.1f}".replace("-", "\u2212"),
                   (r.ecological_ha_year, r.net_present_cost_cny / 1e6),
                   xytext=(8, 0) if right else (-7, 7), textcoords="offset points",
                   ha="left" if right else "right", va="center" if right else "bottom",
                   fontsize=7, color=INK2, linespacing=1.15)
    a.set(xlabel="Ecological score over 15 years (effective ha-yr)",
          ylabel="Net present cost (million CNY)", xlim=(-0.2 * x.max(), 1.08 * x.max()),
          ylim=(yv.min() - 0.1 * (yv.max() - yv.min()) - 2, yv.max() + 0.22 * (yv.max() - yv.min())))
    a.set_title("(a) Solved points: cost against ecology")
    a.text(0.97, 0.04, "lower cost is better\npoints are separate solves", transform=a.transAxes,
           ha="right", va="bottom", fontsize=7, color=MUTED, linespacing=1.3)

    xs = f.frac.values * 100
    b.bar(xs, f.new_area_total_ha, 11, color=C_BUILD)
    b.set_title("(b) Shelter area built (ha)", fontsize=8.5)
    b.set_ylim(0, max(f.new_area_total_ha.max() * 1.12, 1))
    c.bar(xs, f.pv_installed_final_kw / 1e3, 11, color=C_PV)
    c.set_title("(c) PV installed by year 15 (MW)", fontsize=8.5)
    c.set_ylim(0, 11.5)
    d.axhline(tol, **LIMIT)
    d.text(-7, tol * 1.05, "solver tolerance", fontsize=6.6, color=INK2, ha="left", va="bottom")
    d.scatter(xs, f.mip_gap * 100, s=18, color=INK2, zorder=3)
    d.set_title("(d) MIP optimality gap (%)", fontsize=8.5)
    d.set_ylim(-0.03, tol * 1.55)
    d.set_xlabel("Ecological target (% of best feasible)")
    d.set_xticks(xs)
    for ax in (b, c):
        ax.tick_params(labelbottom=False)
    for ax in (b, c, d):
        ax.grid(axis="x", visible=False)
        ax.set_xlim(-9, 109)
    save(fig, "m2_f04_cost_ecology_points")


# --------------------------------------------------------------------------- 5 / 6
def case_rows(t, cases):
    s = t["scenario_summary"].set_index("case")
    sa = t["scenario_annual"]
    rows = []
    for case, label in cases:
        r = s.loc[case]
        spend = sa[sa.case == case][["construction_cny", "om_cny", "pv_facilities_cny"]].sum(min_count=1) / 1e6
        rows.append(dict(case=case, label=label, npc=r.net_present_cost_cny / 1e6,
                         area=r.new_area_total_ha, pv=r.pv_installed_final_kw / 1e3,
                         build=spend.construction_cny, keep=spend.om_cny, pvcap=spend.pv_facilities_cny))
    return pd.DataFrame(rows)


def cfg_value(t, case, key):
    return t["configs"][case]["scenario"][key]


def fig_investment(t):
    """Price, cost and PV-share assumptions at the same absolute ecological target."""
    v = lambda case, key: cfg_value(t, case, key)
    cases = [
        ("base", "Base"),
        ("no_pv", "No PV allowed"),
        ("pv_price_low", f"PV price {v('pv_price_low', 'pv_price_cny_kwh'):.2f} CNY/kWh"),
        ("pv_price_high", f"PV price {v('pv_price_high', 'pv_price_cny_kwh'):.2f} CNY/kWh"),
        ("pv_capex_low", f"PV capex {v('pv_capex_low', 'pv_capex_cny_kw'):.0f} CNY/kW"),
        ("pv_capex_high", f"PV capex {v('pv_capex_high', 'pv_capex_cny_kw'):.0f} CNY/kW"),
        ("om_low", "O&M unit costs $-$50%"),
        ("om_high", "O&M unit costs +50%"),
        ("eco_capex_low", "Shelter capex $-$25%"),
        ("eco_capex_high", "Shelter capex +25%"),
        ("pv_share_min_10pct", r"PV capital share $\geq$10%"),
        ("pv_share_min_30pct", r"PV capital share $\geq$30%"),
    ]
    r = case_rows(t, cases)
    base = r.iloc[0]
    ypos = np.arange(len(r))[::-1]
    fig, axes = plt.subplots(1, 3, figsize=(FULL_W, 3.7), sharey=True,
                             gridspec_kw={"width_ratios": [1.05, 0.75, 1.3]})
    a, b, c = axes
    a.axvline(base.npc, color=MUTED, lw=0.8, ls=DASH)
    a.hlines(ypos, base.npc, r.npc, color=AXIS, lw=1.4, zorder=1)
    a.scatter(r.npc, ypos, s=22, color=INK2, zorder=3)
    for yy, val in zip(ypos, r.npc):
        ha, dx = ("left", 5) if val >= base.npc else ("right", -5)
        a.annotate(f"{val:.1f}".replace("-", "\u2212"), (val, yy), xytext=(dx, 0), textcoords="offset points",
                   ha=ha, va="center", fontsize=7, color=INK2)
    pad = 0.3 * (r.npc.max() - r.npc.min()) + 1
    a.set(xlim=(r.npc.min() - pad, r.npc.max() + pad), xlabel="million CNY")
    a.set_title("(a) Net present cost")
    a.set_yticks(ypos, r.label)
    a.set_ylim(-0.6, len(r) - 0.4)

    b.barh(ypos, r.pv, 0.6, color=C_PV)
    for yy, val in zip(ypos, r.pv):
        b.text(val + 0.25, yy, f"{val:.1f}" if val else "0", va="center", fontsize=7, color=INK2)
    b.set(xlim=(0, 12.5), xlabel="MW")
    b.set_title("(b) PV by year 15")

    left = np.zeros(len(r))
    for col, color, lab in (("build", C_BUILD, "Shelter construction"), ("keep", C_KEEP, "O&M incl. water"),
                            ("pvcap", C_PV, "PV capital")):
        c.barh(ypos, r[col], 0.6, left=left, color=color, label=lab, edgecolor=SURFACE, lw=0.5)
        left += r[col].values
    c.set(xlim=(0, left.max() * 1.1), xlabel="million CNY, undiscounted")
    c.set_title("(c) 15-year spending")
    for ax in axes:
        ax.grid(axis="y", visible=False)
    h, l = c.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=7.2, bbox_to_anchor=(0.6, -0.03),
               handlelength=1.2, columnspacing=1.2)
    fig.tight_layout(w_pad=0.8, rect=(0, 0.035, 1, 1))
    save(fig, "m2_f05_investment_sensitivity")


def fig_assumptions(t):
    """State, resource-cap and search-space checks, as a change from the base solve."""
    v = lambda case, key: cfg_value(t, case, key)
    cap = lambda case: t["configs"][case]["m1"]["water"]["capacity_mm"]
    b0 = t["configs"]["base"]["scenario"]
    cases = [
        ("base", "Base"),
        ("initial_cover_low", f"Initial cover {v('initial_cover_low', 'initial_V_pct'):g}%"),
        ("initial_cover_high", f"Initial cover {v('initial_cover_high', 'initial_V_pct'):g}%"),
        ("storage_low", f"Storage capacity {cap('storage_low'):g} mm"),
        ("storage_high", f"Storage capacity {cap('storage_high'):g} mm"),
        ("water_low", f"Water caps {v('water_low', 'annual_water_cap_m3') / b0['annual_water_cap_m3'] - 1:+.0%}".replace("-", "\u2212")),
        ("water_relax_10pct",
         f"Water caps {v('water_relax_10pct', 'annual_water_cap_m3') / b0['annual_water_cap_m3'] - 1:+.0%}".replace("-", "\u2212")),
        ("budget_low", f"Total budget {v('budget_low', 'total_budget_cny') / b0['total_budget_cny'] - 1:+.0%}".replace("-", "\u2212")),
        ("labor_low",
         f"Labour cap {v('labor_low', 'annual_labor_cap_person_days') / b0['annual_labor_cap_person_days'] - 1:+.0%}".replace("-", "\u2212")),
        ("min_cover_off", "No minimum-cover rule"),
        ("min_cover_15pct", f"Minimum cover {v('min_cover_15pct', 'min_cover_pct'):g}%"),
        ("min_cover_25pct", f"Minimum cover {v('min_cover_25pct', 'min_cover_pct'):g}%"),
        ("min_cover_by_age_12", f"Minimum cover by age {v('min_cover_by_age_12', 'min_cover_by_age_year')}"),
        ("finer_area_grid", f"Area block {v('finer_area_grid', 'area_block_ha'):g} ha"),
        ("constant_irrigation_only", "Constant irrigation only"),
    ]
    r = case_rows(t, cases)
    base = r.iloc[0]
    r["dpct"] = (r.npc / base.npc - 1) * 100
    tol = t["json"]["config"]["solver_relative_gap"] * 100
    ypos = np.arange(len(r))[::-1]
    fig, axes = plt.subplots(1, 3, figsize=(FULL_W, 4.4), sharey=True,
                             gridspec_kw={"width_ratios": [1.7, 0.75, 0.75]})
    a, b, c = axes
    # Symmetric log axis (linear inside +/-1%): changes of 0.2% and 29% are both readable.
    a.set_xscale("symlog", linthresh=1, linscale=1)
    for edge in (-tol, tol):
        a.axvline(edge, **LIMIT)
    a.axvline(0, color=INK2, lw=0.8, zorder=2)
    ok = r.dpct.notna().values
    ok[0] = False
    a.hlines(ypos[ok], 0, r.dpct[ok], color=AXIS, lw=1.4, zorder=2)
    a.scatter(r.dpct[ok], ypos[ok], s=22, color=INK2, zorder=3)
    for yy, val in zip(ypos[1:], r.dpct[1:]):
        if np.isnan(val):  # no feasible plan reaches the target: nothing to plot, say so
            a.text(tol * 2.3, yy, "infeasible at this target", ha="left", va="center", fontsize=7,
                   color=INK2, style="italic")
            continue
        txt = (f"{val:+.2f}%" if abs(val) < 1 else f"{val:+.1f}%").replace("-", "\u2212")
        if abs(val) < 0.005:
            a.text(tol * 2.3, yy, "0 (same plan)", ha="left", va="center", fontsize=7, color=INK2)
        else:
            a.annotate(txt, (val, yy), xytext=(5 if val > 0 else -5, 0), textcoords="offset points",
                       ha="left" if val > 0 else "right", va="center", fontsize=7, color=INK2)
    a.text(tol * 2.3, ypos[0], f"{base.npc:.1f} million CNY", va="center", fontsize=7, color=MUTED)
    a.set_xlim(-900, 500)
    a.set_xticks([-100, -10, -1, 0, 1, 10, 100],
                 ["\u2212100", "\u221210", "\u22121", "0", "1", "10", "100"])
    a.minorticks_off()
    a.set_xlabel(f"% change from base (symmetric log)\nred lines: solver tolerance $\\pm${tol:g}%")
    a.set_title("(a) Net present cost")
    a.set_yticks(ypos, r.label)
    a.set_ylim(-0.6, len(r) - 0.4)

    for ax, col, color, unit, title, xmax in (
            (b, "area", C_BUILD, "shelter area, ha", "(b) Area built", r.area.max() * 1.45),
            (c, "pv", C_PV, "MW", "(c) PV by year 15", 13)):
        ax.barh(ypos, r[col].fillna(0), 0.6, color=color, zorder=2)
        for yy, val in zip(ypos, r[col]):
            if np.isnan(val):
                continue
            ax.text(val + xmax * 0.02, yy, f"{val:g}", va="center", fontsize=7, color=INK2)
        ax.set(xlim=(0, xmax), xlabel=unit)
        ax.set_title(title)
    for ax in axes:
        ax.grid(axis="y", visible=False)
    fig.tight_layout(w_pad=1.2)
    save(fig, "m2_f06_assumption_checks")


# --------------------------------------------------------------------------- 7
def fig_pv_screen(t):
    """Standalone PV screen by build year; no scarcity cost of water, land, labour or budget."""
    p, cfg, dec = t["pv_screening"], t["json"]["config"], t["decisions"]
    built = dec[dec.kind == "pv"].set_index("start_year").capacity_kw / 1e3
    price = cfg["pv_price_cny_kwh"]
    lo = cfg_value(t, "pv_price_low", "pv_price_cny_kwh")
    hi = cfg_value(t, "pv_price_high", "pv_price_cny_kwh")
    in_plan = p.start_year.isin(built.index)
    fig, (a, b) = plt.subplots(1, 2, figsize=(FULL_W, 2.8))

    # Threshold: build years whose break-even price is below the base price pay back on their own.
    a.axhline(price, **LIMIT)
    a.text(14.5, price * 0.955, f"base price {price:.2f} CNY/kWh", fontsize=7.2, color=INK,
           ha="right", va="top")
    # The high-price label sits under its line: the curve crosses just above it.
    for val, lab, above in ((lo, "low-price scenario", True), (hi, "high-price scenario", False)):
        a.axhline(val, color=MUTED, lw=0.7, ls=DASH, zorder=1)
        a.text(14.5, val * (1.03 if above else 0.965), f"{lab} {val:.2f}", fontsize=6.8, color=MUTED,
               ha="right", va="bottom" if above else "top")
    a.plot(p.start_year, p.break_even_price_cny_kwh, color=C_PV, lw=1.2, zorder=2)
    a.scatter(p.start_year[in_plan], p.break_even_price_cny_kwh[in_plan], s=26, color=C_PV,
              edgecolor=SURFACE, linewidth=0.6, zorder=4, label="Built in base plan")
    a.scatter(p.start_year[~in_plan], p.break_even_price_cny_kwh[~in_plan], s=22, facecolor=SURFACE,
              edgecolor=C_PV, linewidth=1.0, zorder=3, label="Not built")
    a.set_yscale("log")
    a.set_yticks([0.15, 0.3, 0.6, 1.2, 2.4], ["0.15", "0.30", "0.60", "1.20", "2.40"])
    a.minorticks_off()
    a.set(title="(a) Break-even price by build year", xlabel="Build year",
          ylabel="CNY/kWh (log scale)", ylim=(0.12, 3.2), xlim=(0.3, 14.7))
    a.set_xticks([1, 3, 5, 7, 9, 11, 13])
    a.legend(loc="upper left", fontsize=7.2, handletextpad=0.2)

    npv = p.standalone_npv_cny_per_kw
    b.axhline(0, color=INK2, lw=0.8)
    b.bar(p.start_year[in_plan], npv[in_plan], 0.66, color=C_PV)
    b.bar(p.start_year[~in_plan], npv[~in_plan], 0.66, facecolor=SURFACE, edgecolor=C_PV, lw=1.0)
    for yr, mw in built.items():
        val = npv[p.start_year == yr].item()
        b.text(yr, max(val, 0) + 90, f"{mw:g}", ha="center", fontsize=7, color=INK2)
    b.text(5.2, 760, "labels: MW built in the base plan", ha="left", fontsize=7, color=MUTED)
    b.set(title="(b) Standalone NPV to year 15", xlabel="Build year", ylabel="CNY per kW",
          xlim=(0.3, 14.7), ylim=(-2900, 1400))
    b.set_xticks([1, 3, 5, 7, 9, 11, 13])
    for ax in (a, b):
        ax.grid(axis="x", visible=False)
    fig.tight_layout(w_pad=1.4)
    save(fig, "m2_f07_pv_screening")


def main():
    t = load()
    check_provenance(t["json"])
    for f in (fig_build, fig_cohorts, fig_water, fig_frontier, fig_investment, fig_assumptions,
              fig_pv_screen):
        f(t)


if __name__ == "__main__":
    main()
