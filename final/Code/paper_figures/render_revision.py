"""Render the revised Practice2 paper figures from existing v7 exports."""

import numpy as np

from render_shared import BASE, M2_CAPS, ROOT, SPEND_COLORS, SPEND_COLUMNS, SPEND_NAMES
from render_shared import keyed, main, storm_risk
from mcm_library import bars, charts as C
from mcm_library.diagrams import Stage, research_framework
from mcm_style import head, palette as P, panels
from mcm_style.accents import callout
from mcm_style.components import arrow, box, label, panel, sheet


def workflow(_inputs):
    return research_framework(
        [
            Stage("M1  Water and cover", "Fit annual growth\nSimulate the daily water balance",
                  "Weather and satellite data", "Rain, wind and vegetation cover", P.TEAL),
            Stage("M2  Plan and budget", "Select planting and PV lots\nCompare cost and ecology",
                  "Resource limits", "Water, labour, land and capital", P.BLUE),
            Stage("M3  Stress-test the belt", "Apply climate drift and hazards\nTrack warning and recovery",
                  "Hazard assumptions", "Drought, storms and climate trends", P.PLUM),
        ],
        handoffs=["Growth parameters and water balance", "Year-15 cohort cover, storage and quotas"],
        deliverable=("Task 4  Operating priorities", "Secure water, fund upkeep and prepare for drought"),
        contributors=(1, 2), height=2.75,
    )


def daily_annual(_inputs):
    fig, ax = sheet(2.40)
    panel(ax, .025, .19, .34, .67, P.LIGHT, P.TEAL)
    panel(ax, .58, .19, .395, .67, P.LIGHT, P.BLUE)
    label(ax, .045, .77, "Annual cover", size=11, color=P.TEAL, weight="bold")
    label(ax, .045, .60, r"Hold cover $V_t$ fixed during year $t$.", size=9)
    label(ax, .045, .34, r"Scale growth by demand met $\overline{W}_t$."
          "\n" r"Subtract decay to get $V_{t+1}$.", size=9)
    label(ax, .60, .77, "Daily root-zone balance", size=11, color=P.BLUE, weight="bold")
    label(ax, .60, .59, r"Add effective inflow and spill above $C$.", size=9)
    label(ax, .60, .45, "Use the remaining water to compute\nstress and actual transpiration.", size=9)
    label(ax, .60, .29, r"Carry unused storage to day $j+1$.", size=9)
    arrow(ax, (.37, .61), (.575, .61), color=P.TEAL)
    arrow(ax, (.575, .32), (.37, .32), color=P.BLUE)
    label(ax, .472, .69, r"Daily demand $D_j$", size=8.8, ha="center", color=P.TEAL)
    label(ax, .472, .40, r"End-of-year $\overline{W}_t$", size=8.8, ha="center", color=P.BLUE)
    label(ax, .50, .08, "The last day's water store carries into the next year.",
          size=9, ha="center", color=P.MUTED)
    return fig


def milp_workflow(_inputs):
    fig, ax = sheet(2.24)
    box(ax, .02, .51, .29, .36, "Precompute cohort paths",
        "Run M1 for each irrigation\npolicy and stand age.", P.TEAL, P.LIGHT)
    box(ax, .355, .51, .29, .36, "Assemble lot decisions",
        "Planting year × irrigation policy\nPV build year × capacity lot", P.BLUE, P.LIGHT)
    box(ax, .69, .51, .29, .36, "Solve on the same limits",
        "1. Maximize ecological benefit\n2. Minimize cost at each target", P.PLUM, P.LIGHT)
    arrow(ax, (.314, .69), (.352, .69), head=8)
    arrow(ax, (.648, .69), (.687, .69), head=8)
    box(ax, .20, .075, .60, .235, "Resource limits and net cost",
        "Gross budget, water, labour and land constrain both solves.", P.INK)
    arrow(ax, (.79, .313), (.817, .505), head=8)
    return fig


def cohort_handoff(inputs):
    cohorts = inputs.result("model2", "cohorts")
    state = keyed(inputs.result("model3", "initial_cohorts"), "cohort_id")
    annual = keyed(inputs.result("model2", "annual"), "year").sort_index()
    caps = inputs.read(M2_CAPS)
    horizon = int(annual.index.max())
    end = keyed(cohorts[cohorts.year.eq(horizon)], "cohort_id")
    order = state.sort_values(["age_year", "area_ha"], ascending=[False, False]).index
    columns = ["area_ha", "V_end_pct", "M_end_mm", "irrigation_mm_yr"]
    if set(end.index) != set(order) or not np.allclose(
        end.loc[order, columns], state.loc[order, columns], atol=1e-6, rtol=0
    ):
        raise ValueError("M3 must inherit the plotted M2 end states")
    if not np.allclose(annual[SPEND_COLUMNS].sum(axis=1), annual.gross_spending_cny,
                       atol=.01, rtol=0):
        raise ValueError("Expenditure components must sum to gross spending")

    fig, axes = panels(3.85, rows=2, height_ratios=[1, 1.24])
    timeline, cash = axes[:, 0]
    quotas = sorted(cohorts.irrigation_mm_yr.unique())
    colors = dict(zip(quotas, [P.GRID, P.BLUE, P.TEAL], strict=True))
    labels = []
    for y, (name, cohort_id) in enumerate(zip("ABC", order, strict=True)):
        group = cohorts[cohorts.cohort_id.eq(cohort_id)].sort_values("year")
        labels.append(f"{name} · {state.at[cohort_id, 'area_ha']:g} ha")
        for _, run in group.groupby(group.irrigation_mm_yr.ne(group.irrigation_mm_yr.shift()).cumsum()):
            quota = run.irrigation_mm_yr.iloc[0]
            x = run.year.iloc[0] - .5
            timeline.broken_barh([(x, len(run))], (y-.30, .60), facecolor=colors[quota])
            timeline.text(x+len(run)/2, y, f"{quota:g}", ha="center", va="center",
                          color=P.INK if quota == quotas[0] else "white", fontsize=9)
        timeline.text(horizon+2.0, y, f"{state.at[cohort_id, 'V_end_pct']:.2f}%",
                      ha="center", va="center", fontsize=8.6)
        timeline.text(horizon+4.1, y, f"{state.at[cohort_id, 'M_end_mm']:.2f}",
                      ha="center", va="center", fontsize=8.6)
    timeline.axvline(horizon+.75, color=P.GRID, lw=.8)
    timeline.text(horizon+2.0, -.68, "V (%)", ha="center", color=P.MUTED, fontsize=8.6)
    timeline.text(horizon+4.1, -.68, "M (mm)", ha="center", color=P.MUTED, fontsize=8.6)
    ticks = np.arange(1, horizon+1, 2)
    timeline.set(xlim=(.5, horizon+5.25), ylim=(2.48, -1.02), xticks=ticks,
                 yticks=range(len(labels)), yticklabels=labels)
    timeline.tick_params(axis="y", length=0)
    timeline.spines["left"].set_visible(False)
    head(timeline, "a", "Irrigation by project year (mm/yr) and final state")

    bottom = np.zeros(len(annual))
    for column, name, color in zip(SPEND_COLUMNS, SPEND_NAMES, SPEND_COLORS, strict=True):
        values = annual[column]/1e6
        cash.bar(annual.index, values, bottom=bottom, color=color, width=.72, label=name)
        bottom += values
    cash.plot(annual.index, annual.revenue_cny/1e6, "D--", color=P.AMBER, ms=3.4, label="PV revenue")
    cap = caps["annual_budget_cny"]/1e6
    cash.axhline(cap, ls=":", lw=.9, color=P.MUTED)
    cash.text(horizon, cap+.65, f"Annual cap: {cap:g} M CNY", ha="right", fontsize=8.4, color=P.MUTED)
    cash.set(xlabel="Project year", ylabel="Annual flow (M CNY)", xticks=ticks,
             xlim=(.5, horizon+.5), ylim=(0, cap*1.18))
    head(cash, "b", "Annual spending and electricity income")
    fig.legend(*cash.get_legend_handles_labels(), loc="outside lower center", ncols=4)
    return fig


def tradeoff(inputs):
    data = inputs.result("model2", "scenario_summary").query("group == 'frontier' and feasible")
    data = data.sort_values("ecological_target_ha_year")
    if len(data) != 6:
        raise ValueError("Expected six feasible ecological targets")
    targets = [f"{float(case.removeprefix('frontier_')):.0%}" for case in data.case]
    benefit = data.ecological_ha_year.to_numpy()
    cost = data.net_present_cost_cny.to_numpy()/1e6
    pv = data.pv_installed_final_kw.to_numpy()/1e3
    price = inputs.read(M2_CAPS)["pv_price_cny_kwh"]
    screen = inputs.result("model2", "pv_screening").query("start_year <= 10").sort_values("start_year")
    fig = C.target_tradeoff(targets, benefit, cost, pv, chosen="60%",
                           benefit_label="Achieved benefit (effective ha·yr)",
                           cost_label="Net present cost (M CNY)", capacity_label="Installed PV (MW)",
                           target_label="Ecological target (% of maximum)",
                           screening=(screen.start_year, screen.break_even_price_cny_kwh,
                                      "PV build year", "Tariff (CNY/kWh)", price, f"Tariff {price:.2f}"),
                           height=4.55)
    capacity, gate, frontier = fig.axes
    frontier.axhline(0, color=P.GRID, lw=.8, zorder=0)
    for j in (3, 4):
        rate = 1000*(cost[j+1]-cost[j])/(benefit[j+1]-benefit[j])
        anchor = ((benefit[j]+benefit[j+1])/2, (cost[j]+cost[j+1])/2)
        callout(frontier, f"{rate:.1f}k", anchor, color=P.AMBER, offset=(14, -9), fontsize=8.6)
    head(frontier, "a", "Cost of meeting six ecological targets")
    head(capacity, "b", "Higher targets displace PV")
    head(gate, "c", "Standalone PV tariff screen")
    return fig


def sensitivity(inputs):
    data = keyed(inputs.result("model2", "scenario_summary"), "case")
    cases = {
        "constant_irrigation_only": "Constant irrigation only",
        "pv_price_low": "Lower PV tariff",
        "pv_capex_high": "Higher PV capital cost",
        "om_high": "O&M unit costs +50%",
        "initial_cover_low": "Initial cover halved",
    }
    selected = data.loc[["base", *cases]]
    base = selected.loc["base"]
    if not selected.feasible.all() or not selected.ecological_target_ha_year.eq(
        base.ecological_target_ha_year
    ).all():
        raise ValueError("Compare feasible cases at the same absolute ecological target")
    fig, grid = panels(2.35)
    ax = grid[0, 0]
    reference = base.net_present_cost_cny/1e6
    C.comparison_dots(ax, list(cases.values()), selected.loc[list(cases), "net_present_cost_cny"]/1e6,
                      xlabel="Net present cost (M CNY)", color=P.BLUE, fmt=".2f",
                      baseline=(reference, f"Baseline {reference:.2f}"))
    ax.set_title(f"Fixed ecological target: {base.ecological_target_ha_year:,.0f} effective ha·yr",
                 loc="left", fontweight="bold")
    ax.legend(loc="upper center", bbox_to_anchor=(.57, 1.015))
    return fig


def storm_and_delivery(inputs):
    fig, axes = panels(4.75, rows=2, cols=2, width_ratios=[1, 1.26], height_ratios=[2.0, 1])
    storm_risk(inputs, axes=axes[0], association_label="No drought–storm link")
    spec = axes[1, 0].get_gridspec()
    for old in axes[1]:
        old.remove()
    ax = fig.add_subplot(spec[1, :])
    resources = inputs.result("model3", "resources").query("post_year == 1 and month == 5 and drought")
    cases = keyed(resources, "case").loc[[BASE, "water_120pct"]]
    bars.grouped_bars(ax, ["Baseline request", "Request +20%"], [
        bars.BarSeries("Requested", cases.requested_eco_m3/1000, P.BLUE),
        bars.BarSeries("Delivered", cases.delivered_eco_m3/1000, P.AMBER),
    ], value_label="Water (10³ m³)", maximum=250, fmt=".0f", legend=False)
    ax.legend(loc="upper right", ncols=2, bbox_to_anchor=(1.0, 1.29))
    head(ax, "c", "May deliveries in the first post-construction drought year")
    return fig


FIGURES = {
    "workflow_revision": workflow,
    "m1_daily_annual": daily_annual,
    "m2_milp_workflow": milp_workflow,
    "m2_cohort_handoff": cohort_handoff,
    "m2_tradeoff_revision": tradeoff,
    "m2_investment_sensitivity": sensitivity,
    "m3_storm_and_delivery": storm_and_delivery,
}


if __name__ == "__main__":
    main(FIGURES, tuple(FIGURES), ROOT / "Figures/Paper2026_Revision")
