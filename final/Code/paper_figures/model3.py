"""Post-construction resistance, recovery, and numerical checks."""

from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
import numpy as np

from style import (
    AMBER, BLUE, COHORT, INK, MONTHS, MUTED, PLUM, RESULTS, TEAL, cohort_order,
    csv, grid, head, panels, read_json,
)


BASE = "base_nonstationary"
STATIONARY = "stationary_reference"
NO_DISASTERS = "no_random_disasters"
POST_TICKS = [0, 10, 20, 30, 40, 50]


def outcomes():
    project = csv("model3", "project_annual")
    cohort = csv("model3", "cohort_annual")
    summary = csv("model3", "summary")
    m1 = read_json(RESULTS / "model1/model1_results.json")
    config = read_json(RESULTS / "model3/scenario_configs.json")[BASE]
    warning = config["failure_cover_fraction_K"] * m1["adopted_parameters"]["K_section_pct"]
    p = project[project.case.eq(BASE)]
    stationary = project[project.case.eq(STATIONARY)]
    counter = project[project.case.eq(NO_DISASTERS)]
    s = summary[summary.case.eq(BASE)].set_index("entity")
    years = p.post_year
    fig, ax = panels(4.95, 2, 2)
    odds, recovery = ax[0]
    cover, benefit = ax[1]
    odds.fill_between(years, p.ci95_low*100, p.ci95_high*100, color=INK, alpha=.12)
    odds.plot(years, p.project_failure_probability*100, color=INK, lw=1.9, label="Belt warning")
    letters = "ABC"
    for i, (row, color, ls) in enumerate(zip(cohort_order().itertuples(), COHORT, [":", "--", "-."])):
        block = cohort[(cohort.case.eq(BASE)) & (cohort.cohort_id.eq(row.cohort_id))]
        odds.plot(block.post_year, block.failure_probability*100, color=color, ls=ls, lw=1.3,
                  label=f"Cohort {letters[i]}")
        cover.plot(block.post_year, block.V_mean_pct, color=color, ls=ls, label=letters[i])
        if letters[i] == "B":
            cover.fill_between(block.post_year, block.V_p05_pct, block.V_p95_pct,
                               color=color, alpha=.14, label="B path P5–P95")
    mean = s.loc["project", "restricted_mean_first_passage_years"]
    mean_core = s.loc[cohort_order().iloc[1].cohort_id, "restricted_mean_first_passage_years"]
    odds.text(.98, .56, f"Restricted mean (50 years)\nBelt: {mean:.1f} yr   B: {mean_core:.1f} yr",
              transform=odds.transAxes, ha="right", va="center", fontsize=8.5, color=INK)
    odds.set(ylabel="First-warning probability (%)", ylim=(0, 105))
    odds.legend(loc="lower right", ncol=2, handlelength=1.3, columnspacing=.8)
    recovery.fill_between(years, p.expected_current_failed_area_ha,
                          p.expected_ever_failed_area_ha, color=TEAL, alpha=.15)
    recovery.plot(years, p.expected_ever_failed_area_ha, color=TEAL, label="Ever below")
    recovery.plot(years, p.expected_current_failed_area_ha, color=BLUE, ls="--", label="Currently below")
    recovery.plot(years, stationary.expected_current_failed_area_ha, color=MUTED,
                  ls=":", label="Currently below, stationary")
    recovered = p.expected_ever_failed_area_ha.iat[-1] - p.expected_current_failed_area_ha.iat[-1]
    recovery.text(47, 245, f"{recovered:.0f} ha above again", ha="right", va="center",
                  color=TEAL, fontsize=8.5)
    recovery.set(ylabel="Expected area (ha)", ylim=(0, 318))
    recovery.legend(loc="lower right", handlelength=1.6, labelspacing=.18, borderaxespad=.35)
    cover.axhline(warning, color=MUTED, ls="--", lw=.8)
    cover.text(49, warning+.65, f"Warning {warning:.1f}%", ha="right", fontsize=8.3, color=MUTED)
    cover.set(ylabel="Cover proxy (%)", ylim=(0, 34))
    cover.legend(loc="upper right", ncol=2, handlelength=1.25, columnspacing=.95)
    for frame, label, color, ls in [
        (p, "Nonstationary hazards", TEAL, "-"), (stationary, "Stationary hazards", BLUE, "--"),
        (counter, "Climate drift, no disasters", MUTED, ":"),
    ]:
        benefit.plot(frame.post_year, frame.cumulative_cover_ha_year_mean, ls=ls, color=color, label=label)
    ratio = p.cumulative_cover_ha_year_mean.iat[-1] / counter.cumulative_cover_ha_year_mean.iat[-1]
    benefit.annotate(f"{ratio:.1%} retained", (50, p.cumulative_cover_ha_year_mean.iat[-1]),
                     xytext=(-8, -30), textcoords="offset points", ha="right", color=TEAL)
    benefit.set(ylabel="Benefit (effective ha·yr)", ylim=(0, 7900))
    benefit.legend(loc="upper left", handlelength=1.5, frameon=True, framealpha=.85)
    for i, plot in enumerate(ax.flat):
        plot.set(xlim=(0, 50), xticks=POST_TICKS)
        if i >= 2:
            plot.set_xlabel("Years after construction")
        grid(plot)
    for plot, letter, title in zip(ax.flat, "abcd", (
        "Timing of the first warning", "Damage and recovery", "Mean cover by cohort",
        "Cumulative vegetation benefit",
    )):
        head(plot, letter, title)
    return fig


def stress_tests():
    results = csv("model3", "summary").query("entity == 'project'").set_index("case")
    configs = read_json(RESULTS / "model3/scenario_configs.json")
    hazards = []
    for case, params in configs.items():
        if case.startswith("joint_rate_"):
            hazards.append((case, params["storm_rate_per_year"],
                            (params["storm_loss_low"] + params["storm_loss_high"]) / 2))
    rates = sorted({rate for _, rate, _ in hazards})
    losses = sorted({loss for _, _, loss in hazards})
    matrix = np.full((len(rates), len(losses)), np.nan)
    for case, rate, loss in hazards:
        matrix[rates.index(rate), losses.index(loss)] = results.loc[case, "restricted_mean_first_passage_years"]
    if matrix.shape != (3, 3) or np.isnan(matrix).any():
        raise ValueError("Incomplete joint hazard grid")
    scenarios = {
        "no_irrigation": "No irrigation", "water_80pct": "Request −20%", BASE: "Baseline",
        "no_drought_storm_association": "Unlinked drought/storm", "no_drought": "No drought",
        "water_120pct": "Request +20%",
    }
    fig, ax = panels(4.93, 2, 2, height_ratios=[1.15, 1], width_ratios=[.96, 1.04])
    heat, controls = ax[0]
    palette = LinearSegmentedColormap.from_list("resistance", ["#F2E8F4", "#A773A5", "#512756"])
    img = heat.pcolormesh(np.arange(4)-.5, np.arange(4)-.5, matrix,
                         vmin=0, vmax=50, cmap=palette)
    heat.invert_yaxis()
    for i, row in enumerate(matrix):
        for j, val in enumerate(row):
            heat.text(j, i, f"{val:.1f}", ha="center", va="center",
                      color="white" if val >= 30 else INK, weight="bold")
    heat.set(xticks=range(len(losses)), xticklabels=[f"{v:.0%}" for v in losses],
             yticks=range(len(rates)), yticklabels=[f"{v:g}" for v in rates],
             xlabel="Mean cover loss per storm", ylabel="Initial storm rate (1/yr)")
    heat.tick_params(length=0)
    cb = fig.colorbar(img, ax=heat, ticks=[0, 10, 20, 30, 40, 50], pad=.03, aspect=13)
    cb.set_label("Restricted mean (yr)")
    m = results.loc[list(scenarios), "restricted_mean_first_passage_years"]
    y = np.arange(len(m))
    baseline = m.loc[BASE]
    controls.axvline(baseline, color=MUTED, lw=.9, ls=":")
    controls.scatter(m, y, c=[INK if name == BASE else TEAL for name in m.index], s=28, zorder=3)
    for x, i in zip(m, y):
        dx = -.19 if 4 < x < baseline else .19
        controls.text(x+dx, i, f"{x:.1f}", va="center", ha="right" if dx < 0 else "left", fontsize=8.4)
    controls.set(yticks=y, yticklabels=list(scenarios.values()), ylim=(5.55, -.55),
                 xlim=(2.1, 9.5), xticks=[3, 5, 7, 9], xlabel="Restricted mean (yr)")
    controls.tick_params(axis="y", length=0)
    grid(controls, "x")
    spec = ax[1, 0].get_gridspec()
    for old in ax[1]:
        old.remove()
    water = fig.add_subplot(spec[1, :])
    resources = csv("model3", "resources").query("case == @BASE and post_year == 1")
    wet = resources[~resources.drought]
    dry = resources[resources.drought]
    binds = dry[dry.slack_m3.abs().lt(1e-6)]
    if not binds.empty:
        water.axvspan(binds.month.min()-.49, binds.month.max()+.49, color="#F4E9E2",
                      lw=0, label="Drought cap binds")
    water.plot(wet.month, wet.delivered_eco_m3/1000, "o-", color=BLUE, label="Normal delivery")
    water.plot(dry.month, dry.delivered_eco_m3/1000, "s--", color=AMBER, label="Drought delivery")
    water.plot(dry.month, dry.cap_m3/1000, ":", color=MUTED, label="Drought cap incl. PV")
    normal_may = wet.loc[wet.month.eq(5), "delivered_eco_m3"].iat[0]
    dry_may = dry.loc[dry.month.eq(5), "delivered_eco_m3"].iat[0]
    water.annotate(f"May: {(1-dry_may/normal_may):.0%} less", (5, dry_may/1000),
                   xytext=(5.9, 52), ha="center", color=AMBER,
                   arrowprops={"arrowstyle": "-", "color": AMBER, "lw": .8})
    water.set(xlim=(.6, 12.4), ylim=(0, 270), xticks=range(1, 13), xticklabels=MONTHS,
              ylabel="Water (thousand m³)")
    water.legend(loc="upper center", ncol=4, columnspacing=.8, handlelength=1.45)
    grid(water)
    head(heat, "a", "Storm frequency × severity")
    head(controls, "b", "Water and drought contrasts")
    head(water, "c", "Canal delivery in the first post-construction year")
    return fig


def numerical_check():
    compare = csv("model3", "markov_mc_comparison")
    refined = csv("model3", "grid_validation")
    finest = compare.nv.max()
    medium = sorted(compare.nv.unique())[-2]
    fig, ax = panels(3.64, 1, 2, width_ratios=[1.55, 1])
    residual, precision = ax[0]
    for i, (identifier, color) in enumerate(zip(cohort_order().cohort_id, COHORT)):
        detail = compare[compare.cohort_id.eq(identifier)]
        high = detail[detail.nv.eq(finest)].sort_values("post_year")
        mid = detail[detail.nv.eq(medium)].sort_values("post_year")
        y = i*3.6 + np.arange(len(high))
        residual.hlines(y, 100*(high.mc_ci95_low-high.mc_failure_probability),
                        100*(high.mc_ci95_high-high.mc_failure_probability), color="#A6B3B8", lw=2.1)
        residual.scatter(100*(high.markov_failure_probability-high.mc_failure_probability), y,
                         marker="D", c=color, s=24, zorder=4)
        residual.scatter(100*(mid.markov_failure_probability-mid.mc_failure_probability), y,
                         marker="o", facecolor="white", edgecolor=color, s=29, zorder=3)
        if i < 2:
            residual.axhline(y[-1]+.8, lw=.7, color="#DFE7E9")
    residual.axvline(0, color=MUTED, lw=.8, ls=":")
    ypos = [i*3.6+j for i in range(3) for j in range(3)]
    residual.set(xlim=(-1.5, 1.47), xticks=[-1, -.5, 0, .5, 1], ylim=(ypos[-1]+.6, -.61),
                 yticks=ypos, yticklabels=[f"{c} · {t} yr" for c in "ABC" for t in [10, 30, 50]],
                 xlabel="Markov − Monte Carlo (pp)")
    for i, (test, label, marker) in enumerate([
        ("state_grid", "Finer state grid", "o"), ("shock_quadrature", "More shock nodes", "D"),
    ]):
        rows = refined[refined.comparison.eq(test)].set_index("cohort_id").loc[list(cohort_order().cohort_id)]
        y = np.arange(3) + (-.14 if i == 0 else .14)
        precision.scatter(rows.max_absolute_probability_difference*100, y, color=COHORT,
                          marker=marker, s=35, zorder=4)
    precision.set(xlim=(0, .225), xticks=[0, .05, .10, .15, .20], ylim=(2.55, -.55),
                  yticks=range(3), yticklabels=list("ABC"), xlabel="Max. probability change (pp)")
    fig.legend(handles=[
        Line2D([], [], lw=2, color="#A6B3B8", label="MC 95% interval"),
        Line2D([], [], ls="none", marker="o", color=MUTED, markerfacecolor="white",
               label=f"{medium} × 21 grid"),
        Line2D([], [], ls="none", marker="D", color=MUTED, label=f"{finest} × 41 grid"),
    ], loc="outside lower left", ncol=3, handlelength=1.3, columnspacing=.85)
    precision.legend(handles=[
        Line2D([], [], ls="none", marker="o", color=MUTED, label="Finer state grid"),
        Line2D([], [], ls="none", marker="D", color=MUTED, label="More shock nodes"),
    ], loc="upper right", handlelength=1, frameon=True, framealpha=.9)
    head(residual, "a", "Stationary-chain comparison")
    head(precision, "b", "Refinement sensitivity")
    grid(residual, "x")
    grid(precision, "x")
    return fig
