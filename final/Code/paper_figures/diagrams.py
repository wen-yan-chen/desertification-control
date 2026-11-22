"""Methods and public-facing diagrams, tied to the implemented model chain."""

from style import AMBER, BLUE, INK, LIGHT, MUTED, PLUM, TEAL, arrow, box, csv, foot, sheet


def overview():
    fig, ax = sheet(2.82)
    titles = ("M1  Water and cover", "M2  Build and operate", "M3  Withstand and recover")
    detail = (
        "Calibrate annual cover\nRun a daily water balance",
        "Schedule planting, water,\nlabour and PV over 15 years",
        "Simulate 50 years of drought,\nwind and sand shocks",
    )
    x = [.025, .355, .685]
    w = .29
    for xi, title, description, color in zip(x, titles, detail, (TEAL, BLUE, PLUM)):
        box(ax, xi, .385, w, .24, title, description, color, LIGHT)
    box(ax, .025, .755, .29, .205, "Evidence", "Station cover and weather", TEAL)
    box(ax, .355, .755, .29, .205, "Planning assumptions", "Resource caps and unit costs", BLUE)
    box(ax, .685, .755, .29, .205, "Hazard assumptions", "Storm, drought and climate", PLUM)
    for xi in x:
        arrow(ax, (xi + w / 2, .755), (xi + w / 2, .63))
    for xi, xj, label in zip(x, x[1:], ("Water–cover trajectories", "Year-15 cohort states")):
        arrow(ax, (xi + w, .505), (xj, .505))
        ax.text((xi + w + xj) / 2, .325, label, ha="center", va="center", fontsize=8.4)
    ax.plot([.50, .50, .83, .83], [.385, .26, .26, .385], color=MUTED, lw=.8)
    arrow(ax, (.665, .26), (.665, .203))
    box(ax, .355, .035, .62, .165, "Operating brief",
        "Secure water, fund upkeep and monitor recovery", INK)
    return fig


def water_cycle():
    fig, ax = sheet(3.0)
    box(ax, .02, .74, .29, .21, "Water supply",
        "Effective rain $+$ net irrigation\n$+$ groundwater assumption", TEAL)
    box(ax, .355, .74, .29, .21, "Atmospheric demand",
        r"Wind enters $ET_0$" "\n" r"Temperature scales $ET_0$", BLUE)
    box(ax, .69, .74, .29, .21, "Start-of-year state",
        r"Cover $V_t$ and storage $M_{t,0}$", PLUM)
    box(ax, .17, .365, .58, .25, "Daily root-zone water balance",
        r"Add inflow; drain excess above $C$" "\n"
        r"Remove stress-limited uptake $T_a$; carry $M$ forward", TEAL, LIGHT)
    for start, end in [((.165, .74), (.27, .619)), ((.50, .74), (.46, .619)),
                       ((.835, .74), (.675, .619))]:
        arrow(ax, start, end)
    arrow(ax, (.40, .365), (.40, .253), TEAL)
    ax.text(.42, .307, r"$\overline{W}_t=\sum T_a/\sum D$", va="center", color=TEAL)
    box(ax, .14, .045, .52, .205, "Annual cover update",
        r"$V_{t+1}=V_t+rV_t(1-V_t/K)\overline{W}_t-dV_t$", PLUM)
    box(ax, .72, .045, .26, .205, "Sand exposure",
        r"Diagnostic $E(1-V_t/K)$", AMBER)
    ax.plot([.67, .89], [.307, .307], color=PLUM, lw=.95)
    arrow(ax, (.66, .133), (.668, .307), PLUM, connectionstyle="angle,angleA=0,angleB=90")
    arrow(ax, (.75, .485), (.89, .485), TEAL)
    ax.plot([.89, .89], [.307, .485], color=TEAL, lw=.95)
    arrow(ax, (.89, .485), (.89, .738), PLUM)
    ax.text(.90, .57, "Next\nyear", fontsize=8.5, color=PLUM, va="center")
    ax.plot([.98, .99], [.845, .845], color=AMBER, lw=.8)
    ax.plot([.99, .99], [.148, .845], color=AMBER, lw=.8)
    arrow(ax, (.99, .148), (.981, .148), AMBER)
    return fig


def hazard_cycle():
    fig, ax = sheet(2.95)
    box(ax, .035, .747, .42, .20, "Initial condition",
        "Carry year-15 cover and stored water\nfrom the three M2 cohorts", PLUM)
    box(ax, .545, .747, .42, .20, "Shared annual hazards",
        "Climate drift and drought alter forcing;\ndrought also raises the storm rate", AMBER)
    box(ax, .035, .405, .27, .225, "Monthly water",
        "PV washing first; share\nthe remainder by request", BLUE, LIGHT)
    box(ax, .365, .405, .27, .225, "Growth",
        "Run M1 with delivered\nwater for each cohort", TEAL, LIGHT)
    box(ax, .695, .405, .27, .225, "Storm damage",
        "Apply shared cover loss\nat the annual census", AMBER, LIGHT)
    arrow(ax, (.245, .747), (.42, .632), PLUM)
    for end in ((.17, .632), (.50, .632), (.83, .632)):
        arrow(ax, (.755, .747), end, AMBER)
    arrow(ax, (.305, .518), (.365, .518))
    arrow(ax, (.635, .518), (.695, .518))
    arrow(ax, (.83, .405), (.83, .247), AMBER)
    box(ax, .56, .037, .405, .208, "Record the first warning",
        r"At least 50% of area below $0.30K$" "\n"
        "at the same annual census", PLUM)
    ax.plot([.695, .50], [.445, .305], color=TEAL, lw=.95)
    arrow(ax, (.50, .305), (.50, .405), TEAL)
    ax.text(.475, .286, "Carry both states to next year", ha="right", color=TEAL)
    ax.text(.475, .199, "Growth and recovery continue", ha="right", color=TEAL)
    return fig


def policy():
    fig, ax = sheet(2.13)
    schedule = csv("model2", "annual")
    project = csv("model3", "project_annual")
    end = project.loc[project["post_year"].eq(project["post_year"].max())].set_index("case")
    benefit = (end.loc["base_nonstationary", "cumulative_cover_ha_year_mean"]
               / end.loc["no_random_disasters", "cumulative_cover_ha_year_mean"])
    monthly = csv("model2", "monthly")
    may = monthly[monthly["month"].eq(5)]
    may_peak = (may["gross_water_m3"] / may["cap_m3"]).max()
    area = schedule["new_area_ha"].sum() / 100
    total_pv = schedule["new_pv_kw"].sum() / 1000
    early = schedule[schedule["new_pv_kw"].gt(0)]
    capital = early[["construction_cny", "pv_facilities_cny"]].sum().sum() / 1e6
    stages = [
        ("Years 1–2", "Confirm supply; plant", f"{area:g} km² in the scenario\nWater authority + contractor", TEAL),
        ("Years 1–4", "Screen and build PV", f"Up to {total_pv:g} MW in plan\nOperator + finance team", PLUM),
        ("Years 5–15", "Fund and inspect", "Service pumps before May\nOperator + irrigation team", BLUE),
        ("Year 16 onward", "Keep stands viable", "Inspect after droughts/storms\nMonitoring + maintenance", AMBER),
    ]
    for i, (period, heading, detail, color) in enumerate(stages):
        x = .025 + i * .243
        ax.text(x + .110, .88, period, ha="center", va="center", weight="bold", color=color)
        box(ax, x, .38, .22, .40, heading, detail, color, LIGHT)
    foot(ax, f"Scenario: CNY {capital:.2f}m initial capital   •   May delivery up to {may_peak:.0%} of cap", .25)
    foot(ax, f"With continued care: {benefit:.1%} of the no-disaster cover benefit over 50 years", .105)
    return fig
