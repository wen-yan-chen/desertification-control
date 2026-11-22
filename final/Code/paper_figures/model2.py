"""Fifteen-year cohort schedule, resource use and investment trade-offs."""

from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
import numpy as np

from style import (
    AMBER, BLUE, CASH, DATA, INK, MONTHS, MUTED, PLUM, TEAL, cohort_order,
    csv, grid, head, panels, read_json,
)


SPEND = ["construction_cny", "om_cny", "pv_facilities_cny"]
SPEND_NAMES = ["Planting", "O&M incl. water", "PV capital"]
YEAR_TICKS = [1, 3, 5, 7, 9, 11, 13, 15]


def cohort_schedule():
    cohorts = csv("model2", "cohorts")
    annual = csv("model2", "annual")
    fig, ax = panels(3.55, 2, 2, height_ratios=[1, 1.08], width_ratios=[1, 1.32])
    spec = ax[0, 0].get_gridspec()
    for old in ax[0]:
        old.remove()
    timeline = fig.add_subplot(spec[0, :])
    ribbon = {100: "#D6E8E6", 300: "#67A79D", 600: TEAL}
    labels = []
    for row, item in enumerate(cohort_order().itertuples()):
        name = "ABC"[row]
        block = cohorts[cohorts.cohort_id.eq(item.cohort_id)]
        labels.append(f"{name}  ·  {item.area_ha:g} ha")
        for irrigation, same_level in block.groupby("irrigation_mm_yr"):
            x0 = same_level.year.min() - .5
            width = len(same_level)
            timeline.broken_barh([(x0, width)], (row-.34, .68), facecolor=ribbon[irrigation])
            timeline.text(x0+width/2, row, f"{irrigation:g}", ha="center", va="center",
                          color="white" if irrigation == 600 else INK, fontsize=8.5)
    timeline.set(xlim=(.5, 15.5), ylim=(2.55, -.55), xticks=range(1, 16),
                 yticks=range(3), yticklabels=labels)
    timeline.tick_params(axis="y", length=0)
    timeline.spines["left"].set_visible(False)
    head(timeline, "a", "Irrigation by cohort and project year (mm/yr)")
    plant, pv = ax[1]
    plant.bar(annual.year, annual.new_area_ha, color=TEAL, width=.68)
    plant.set(ylabel="New area (ha)", xlabel="Project year", xticks=YEAR_TICKS[::2],
              xlim=(.5, 15.5), ylim=(0, 180), yticks=[0, 50, 100, 150])
    pv.bar(annual.year, annual.new_pv_kw/1000, color="#C5ACCF", label="New build", width=.68)
    pv.step(annual.year, annual.pv_operating_kw/1000, where="post", color=PLUM, label="Operating")
    pv.set(ylabel="Capacity (MW)", xlabel="Project year", xticks=YEAR_TICKS[::2],
           xlim=(.5, 15.5), ylim=(0, 12))
    pv.legend(loc="center right")
    for plot in (plant, pv):
        grid(plot)
    head(plant, "b", "Planting in years 1–2")
    head(pv, "c", "PV operates from the year after build")
    return fig


def resources():
    annual = csv("model2", "annual")
    monthly = csv("model2", "monthly")
    caps = read_json(DATA / "m2_inputs/scenario.json")
    monthly["utilization"] = 100 * monthly.gross_water_m3 / monthly.cap_m3
    table = monthly.pivot(index="month", columns="year", values="utilization")
    fig, ax = panels(6.65, 3, 2, height_ratios=[1.6, 1, 1.02])
    spec = ax[0, 0].get_gridspec()
    for old in ax[0]:
        old.remove()
    heat = fig.add_subplot(spec[0, :])
    colors = ["#F4F8F7", "#CDE7E3", "#8DC3BC", "#3B928B", "#116C65"]
    bounds = [0, 20, 40, 60, 80, 100]
    img = heat.pcolormesh(np.arange(16)-.5, np.arange(13)-.5, table,
                          cmap=ListedColormap(colors), norm=BoundaryNorm(bounds, len(colors), clip=True))
    heat.invert_yaxis()
    heat.axhline(3.5, color=INK, lw=.52)
    heat.axhline(4.5, color=INK, lw=.52)
    for x, val in enumerate(table.loc[5]):
        heat.text(x, 4, f"{val:.0f}", ha="center", va="center",
                  fontsize=8.3, color="white" if val >= 80 else INK)
    heat.set(xticks=range(15), xticklabels=table.columns, yticks=range(12), yticklabels=MONTHS)
    heat.tick_params(length=0)
    colorbar = fig.colorbar(img, ax=heat, ticks=bounds, pad=.025, aspect=16)
    colorbar.set_label("Monthly cap used (%)")
    head(heat, "a", "Canal use by month and project year")
    use, share = ax[1]
    use.plot(annual.year, 100*annual.water_m3/caps["annual_water_cap_m3"],
             "o-", label="Water", color=BLUE)
    use.plot(annual.year, 100*annual.labor_person_days/caps["annual_labor_cap_person_days"],
             "^--", label="Labour", color=AMBER)
    use.set(ylim=(0, 108), ylabel="Annual cap used (%)")
    use.legend(loc="upper right", ncols=2, handlelength=1.25)
    ratios = annual[SPEND].div(annual.gross_spending_cny, axis=0)*100
    bottom = np.zeros(len(annual))
    for key, color in zip(SPEND, CASH):
        share.bar(annual.year, ratios[key], bottom=bottom, color=color, width=.78)
        bottom += ratios[key]
    share.set(ylabel="Share of spending (%)", ylim=(0, 105))
    head(use, "b", "Annual water and labour")
    head(share, "c", "Investment allocation")
    for old in ax[2]:
        old.remove()
    cash = fig.add_subplot(spec[2, :])
    bottom = np.zeros(len(annual))
    for key, name, color in zip(SPEND, SPEND_NAMES, CASH):
        values = annual[key] / 1e6
        cash.bar(annual.year, values, bottom=bottom, width=.73, color=color, label=name)
        bottom += values
    cash.plot(annual.year, annual.revenue_cny/1e6, "D-", color=AMBER, label="PV revenue", ms=3.5)
    cash.axhline(caps["annual_budget_cny"]/1e6, ls=":", color=MUTED, lw=1)
    cash.set(ylabel="Annual flows (M CNY)", ylim=(0, 16), xlabel="Project year", yticks=[0, 4, 8, 12])
    cash.legend(loc="upper right", ncols=4, handlelength=1.35, columnspacing=.9)
    head(cash, "d", "Gross spending and electricity income")
    for area in (use, share, cash):
        area.set(xticks=YEAR_TICKS, xlim=(.5, 15.5))
        grid(area)
    return fig


def tradeoff():
    runs = csv("model2", "scenario_summary").query("group == 'frontier' and feasible").copy()
    if len(runs) != 6:
        raise ValueError("Expected six feasible ecological targets")
    runs["target_pct"] = runs.case.str.removeprefix("frontier_").astype(float)*100
    runs = runs.sort_values("target_pct")
    base = runs[runs.target_pct.eq(60)].iloc[0]
    pvs = csv("model2", "pv_screening")
    tariff = read_json(DATA / "m2_inputs/scenario.json")["pv_price_cny_kwh"]
    fig, ax = panels(4.55, 2, 2, height_ratios=[1.1, 1])
    spec = ax[0, 0].get_gridspec()
    for old in ax[0]:
        old.remove()
    trade = fig.add_subplot(spec[0, :])
    h = runs.ecological_ha_year
    cost = runs.net_present_cost_cny / 1e6
    trade.axhline(0, color=MUTED, lw=.85)
    trade.plot(h, cost, "o--", color=BLUE, lw=1.3)
    trade.scatter(base.ecological_ha_year, base.net_present_cost_cny/1e6,
                  color=TEAL, s=118, marker="*", zorder=4)
    for row in runs.itertuples():
        dx, dy = (4, 6) if row.target_pct != 60 else (4, -16)
        if row.target_pct == 100:
            dx, dy = -25, 4
        trade.annotate(f"{row.target_pct:.0f}%", (row.ecological_ha_year, row.net_present_cost_cny/1e6),
                       xytext=(dx, dy), textcoords="offset points", color=INK, fontsize=8.5)
    trade.set(xlim=(-90, 2190), ylim=(-10, 74), xticks=[0, 500, 1000, 1500, 2000],
              ylabel="Net present cost (M CNY)", xlabel="Achieved benefit (effective ha·yr)")
    head(trade, "a", "Cost of meeting six ecological targets")
    pv, gate = ax[1]
    pv.bar(runs.target_pct, runs.pv_installed_final_kw/1000, width=12,
           color=[TEAL if pct == 60 else "#7296B5" for pct in runs.target_pct])
    pv.set(xlabel="Target (% of maximum benefit)", ylabel="Installed PV (MW)",
           xticks=runs.target_pct, ylim=(0, 11.3))
    head(pv, "b", "Higher targets displace PV")
    pvs = pvs.loc[pvs.start_year.le(10)]
    gate.axhline(tariff, color=AMBER, lw=1.15, ls="--", label=f"Tariff {tariff:.2f}")
    gate.plot(pvs.start_year, pvs.break_even_price_cny_kwh, "o-", color=PLUM, label="Break-even")
    gate.scatter([4, 5], pvs.set_index("start_year").loc[[4, 5], "break_even_price_cny_kwh"],
                 facecolor="white", edgecolor=PLUM, zorder=4, s=24)
    gate.set(xlabel="PV build year", ylabel="Tariff (CNY/kWh)", xticks=[1, 2, 4, 6, 8, 10],
             xlim=(.75, 10.25), ylim=(.215, .563))
    gate.legend(loc="upper left", handlelength=1.45)
    head(gate, "c", "Break-even passes tariff in year 5")
    for area in (trade, pv, gate):
        grid(area)
    return fig


def investment():
    summary = csv("model2", "scenario_summary").set_index("case")
    annual = csv("model2", "scenario_annual")
    scenarios = {
        "base": "Baseline", "pv_price_low": "Lower PV tariff", "pv_price_high": "Higher PV tariff",
        "pv_capex_low": "Lower PV capital cost", "pv_capex_high": "Higher PV capital cost",
        "pv_share_min_30pct": "30% PV spending floor", "om_low": "Lower upkeep cost",
        "om_high": "Higher upkeep cost", "eco_capex_low": "Lower planting cost",
        "eco_capex_high": "Higher planting cost", "initial_cover_low": "Lower initial cover",
        "initial_cover_high": "Higher initial cover", "water_low": "Tighter water caps",
        "water_relax_10pct": "Higher water caps", "budget_low": "Lower gross budget",
        "labor_low": "Lower labour capacity", "finer_area_grid": "Smaller planting blocks",
    }
    runs = summary.loc[list(scenarios)]
    if not runs.feasible.all() or not np.allclose(runs.ecological_target_ha_year, runs.ecological_target_ha_year.iat[0]):
        raise ValueError("Investment comparison requires a common target and feasible solves")
    totals = annual.groupby("case")[SPEND].sum().loc[list(scenarios)]
    mix = totals.div(totals.sum(axis=1), axis=0)*100
    fig, ax = panels(4.95, 1, 3, width_ratios=[1.14, .72, 1.24], sharey=True)
    cost, pv, spending = ax[0]
    base = runs.net_present_cost_cny.iat[0]
    delta = (runs.net_present_cost_cny/base-1)*100
    y = np.arange(len(runs))
    for area in ax[0]:
        area.axhspan(-.5, .5, color="#EAF5F3", zorder=0, lw=0)
        area.spines["left"].set_visible(False)
        area.tick_params(axis="y", length=0)
        area.set_ylim(len(runs)-.45, -.56)
        for split in [5.5, 9.5, 13.5]:
            area.axhline(split, lw=.6, color="#D9E4E5", zorder=0)
    cost.axvline(0, color=MUTED, lw=.8)
    cost.hlines(y, 0, delta, lw=1.2, color="#A6B4B9")
    cost.scatter(delta, y, c=[TEAL if d < 0 else AMBER for d in delta], s=21, zorder=3)
    cost.set(xlim=(-47, 33), xticks=[-40, -20, 0, 20], xlabel="vs. baseline (%)",
             yticks=y, yticklabels=list(scenarios.values()))
    pv.barh(y, runs.pv_installed_final_kw/1000, color=PLUM, height=.48)
    pv.scatter(runs.pv_installed_final_kw/1000, y, c=PLUM, s=10, zorder=3)
    pv.set(xlim=(-.45, 10.65), xticks=[0, 5, 10], xlabel="Capacity (MW)")
    pv.axvline(runs.pv_installed_final_kw.iat[0]/1000, color=PLUM, lw=.75, ls=":")
    left = np.zeros(len(y))
    for key, name, color in zip(SPEND, SPEND_NAMES, CASH):
        spending.barh(y, mix[key], left=left, height=.61, color=color, label=name)
        left += mix[key]
    spending.set(xlim=(0, 101), xticks=[0, 50, 100], xlabel="% of 15-year gross spending")
    fig.legend(handles=[Patch(facecolor=color, label=name) for name, color in zip(SPEND_NAMES, CASH)],
               loc="outside lower center", ncols=3)
    head(cost, "a", "Net present cost")
    head(pv, "b", "PV")
    head(spending, "c", "Funding mix")
    return fig
