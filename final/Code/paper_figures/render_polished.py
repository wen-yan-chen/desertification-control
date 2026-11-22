"""Practice2 Figure 5–16 alternatives, rendered from the frozen v7 exports."""

from functools import partial

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import FixedLocator, FuncFormatter, MultipleLocator

from mcm_library import charts as C
from mcm_style import head, palette as P, panels
from mcm_style.accents import callout
from mcm_style.components import arrow, label, panel, sheet

from render_mechanisms import stress_switches
from render_revision import cohort_handoff, storm_and_delivery, tradeoff
from render_shared import BASE, M2_CAPS, MONTHS, NO_DISASTERS, ROOT, STATIONARY
from render_shared import keyed, lines, main, numerical_check


def stress(inputs):
    fig = stress_switches(inputs)
    water, season = fig.axes
    water.texts[0].remove()
    water.xaxis.set_major_locator(FixedLocator([0, 37.5, 75]))
    water.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    water.text(4, .92, "Water-limited", color=P.BLUE, va="top")
    water.text(71, .82, "No water stress", color=P.MUTED, ha="right")
    water.scatter([37.5], [1], edgecolors="white", facecolors=P.BLUE, s=30, zorder=4)
    season.set(xticks=[-10, 5, 25, 32], ylim=water.get_ylim())
    season.legend(loc="upper left", handletextpad=.35)
    return fig


def holdout(inputs):
    metrics = inputs.result("model1", "holdout_by_site").sort_values("persistence_rmse")
    pairs = inputs.result("model1", "prediction_pairs").query("split == 'test'")
    annual = keyed(inputs.result("model1", "yearly_table"), ["site", "year"])
    free = keyed(inputs.result("model1", "free_running_holdout"), ["site", "year"])
    fig, axes = panels(4.45, rows=2, cols=3, height_ratios=[1.35, 1])
    spec = axes[0, 0].get_gridspec()
    for ax in axes[0]:
        ax.remove()
    score = fig.add_subplot(spec[0, :])
    for row in np.flatnonzero(metrics.site.isin(["YT", "MF"])):
        score.axhspan(row-.41, row+.41, color=P.LIGHT, lw=0)
    C.comparison_dots(score, metrics.site, metrics.rmse, compare=metrics.persistence_rmse,
                      series_labels=("Model 1", "Persistence"), fmt=None, color=P.BLUE,
                      xlabel=r"$V/K$ RMSE (lower is better)")
    score.xaxis.set_major_locator(MultipleLocator(.02))
    score.legend(loc="upper right", ncols=2)
    e_model, e_persist = (np.sqrt(np.mean((pairs.observed_x-pairs[col])**2))
                          for col in ("predicted_x", "persistence_x"))
    score.text(1, 1.037, f"Pooled (n={len(pairs)}):  M1 {e_model:.4f} · persistence {e_persist:.4f}",
               transform=score.transAxes, ha="right", va="bottom", fontsize=8.5, color=P.INK)
    for tick in score.get_yticklabels():
        if tick.get_text() in {"YT", "MF"}:
            tick.set(color=P.TEAL, fontweight="bold")
    head(score, "a", "One-step errors · 2023–2025 holdout")
    years = np.arange(2022, 2026)
    for i, (ax, site, name) in enumerate(zip(axes[1], ["YT", "MF", "RQ"],
                                             ["Yutian", "Minfeng", "Ruoqiang"])):
        observed = annual.loc[site].loc[years, "V"]
        predicted = np.r_[observed.iloc[0], free.loc[site].loc[years[1:], "predicted_pct"]]
        ax.axvspan(2022.5, 2025.25, color=P.LIGHT, lw=0)
        lines(ax, years, [C.Series("Observed", observed, P.INK, "-", "o"),
                          C.Series("Model 1 free run", predicted, P.AMBER, "--", "^")],
              xlabel="", ylabel="Cover proxy (%)" if i == 0 else "")
        ax.set(xlim=(2021.8, 2025.25), ylim=(21, 44), xticks=years, yticks=[25, 30, 35, 40])
        ax.tick_params(axis="y", labelleft=i == 0)
        head(ax, "bcd"[i], name)
    fig.legend(*axes[1, 0].get_legend_handles_labels(), loc="outside lower center", ncols=2)
    return fig


def irrigation(inputs):
    curve = keyed(inputs.result("model1", "water_cover_curve"), "irrigation_mm_yr").sort_index()
    paths = keyed(inputs.result("model1", "scenario_annual"), ["scenario", "calendar_year"])
    params = inputs.read("Results/v7/model1/model1_results.json")["adopted_parameters"]
    if not curve.converged_both.all():
        raise ValueError("Dose response requires convergence from both initial states")
    scenarios = [("I0", "Rain only", P.MUTED, ":"), ("I300", "300 mm/yr", P.TEAL, "--"),
                 ("I600", "600 mm/yr", P.BLUE, "-"), ("stop_after_10", "600 mm/yr then stop", P.AMBER, "-.")]
    years = paths.loc["I600"].sort_index().index
    stopped = paths.loc["stop_after_10"].loc[years]
    first_dry = int(stopped.index[stopped.irrigation_mm_yr.eq(0)][0])
    fig, axes = panels(4.45, rows=2, cols=2)
    rows = [
        ("V_steady_pct", "V_start_pct", "V_end_pct", "Cover proxy (%)",
         params["K_section_pct"]*(1-params["d"]/params["r"]), "Water-unlimited cover", (0, 36)),
        ("M_periodic_end_mm", "M_start_mm", "M_end_mm", "Root-zone water (mm)",
         params["water"]["capacity_mm"], "Storage capacity", (0, 88)),
    ]
    for i, (steady, start, end, ylabel, cap, cap_label, ylim) in enumerate(rows):
        left, right = axes[i]
        lines(left, curve.index, [C.Series("Periodic steady state", curve[steady], P.TEAL, "-", "o")],
              xlabel="Irrigation (mm/yr)" if i else "", ylabel=ylabel)
        left.axhline(cap, color=P.MUTED, lw=.8, ls=":")
        left.text(1980, cap+.035*ylim[1], cap_label, color=P.MUTED, ha="right", fontsize=8.3)
        left.scatter([300, 600], curve.loc[[300, 600], steady], s=32, facecolor="white",
                     edgecolor=P.TEAL, zorder=3)
        series = []
        for key, name, color, ls in scenarios:
            subset = paths.loc[key].loc[years]
            series.append(C.Series(name, np.r_[subset[start].iloc[0], subset[end]], color, ls))
        right.axvspan(first_dry-.5, years[-1]+.4, color=P.LIGHT, lw=0)
        right.axvline(first_dry-.5, color=P.AMBER, lw=.85, ls=":")
        lines(right, np.r_[years[0]-1, years], series, xlabel="Calendar year end" if i else "", ylabel="")
        left.set(xlim=(-65, 2070), ylim=ylim, xticks=[0, 500, 1000, 1500, 2000])
        right.set(xlim=(years[0]-1.4, years[-1]+.4), ylim=ylim, xticks=[2025, 2035, 2045, 2050])
        right.tick_params(axis="y", labelleft=False)
    axes[0, 1].text(first_dry+.2, 33.1, f"Stop case: {first_dry} onward", color=P.AMBER, fontsize=8.3)
    for ax, letter, title in zip(axes.flat, "abcd", ("Long-run cover", "Cover after planting",
                                                   "Long-run year-end storage", "Water after planting")):
        head(ax, letter, title)
    fig.legend(*axes[0, 1].get_legend_handles_labels(), loc="outside lower center", ncols=4)
    return fig


def drivers(inputs):
    forcing = keyed(inputs.result("model1", "section_forcing_climatology"), "month").sort_index()
    wind = keyed(inputs.result("model1", "wind_channel"), ["irrigation_mm_yr", "wind_speed_scale"])
    sens = keyed(inputs.result("model1", "sensitivity"), ["irrigation_mm_yr", "parameter", "value"]).sort_index()
    base = keyed(inputs.result("model1", "water_cover_curve"), "irrigation_mm_yr")
    fig, axes = panels(4.65, rows=2, cols=2, height_ratios=[.94, 1.06])
    season, wind_ax = axes[0]
    season.fill_between(forcing.index, forcing.ET0g_mm, forcing.ET0_mm, color=P.BLUE, alpha=.11)
    lines(season, forcing.index, [C.Series(r"Reference $ET_0$", forcing.ET0_mm, P.MUTED, "--"),
                                  C.Series("Temperature-scaled", forcing.ET0g_mm, P.BLUE, "-", "s")],
          xlabel="", ylabel="Demand (mm/month)")
    season.set(xticks=range(1, 13, 2), xticklabels=MONTHS[::2], ylim=(0, 380), yticks=[0, 100, 200, 300])
    season.legend(loc="upper left", handlelength=1.15)
    head(season, "a", "Seasonal demand")

    palette = {300: P.TEAL, 600: P.BLUE}
    speeds = wind.loc[300].sort_index().index
    lines(wind_ax, (speeds-1)*100, [
        C.Series(f"{quota} mm/yr", wind.loc[quota].loc[speeds, "V_steady_pct"], palette[quota], ls, marker)
        for quota, ls, marker in ((300, "-", "o"), (600, "--", "s"))
    ], xlabel="Change in wind speed (%)", ylabel="Long-run cover (%)")
    wind_ax.axvline(0, color=P.MUTED, ls=":", lw=.8)
    wind_ax.set(xticks=[-20, -10, 0, 10, 20], ylim=(15, 27))
    wind_ax.legend(loc="center right")
    head(wind_ax, "b", "Cover response to wind")

    parameters = [
        ("c", "Demand coeff.  [0.70, 1.20]"), ("eta_w", "Irrigation eff.  [0.65, 0.85]"),
        ("rain_fraction", "Effective rain  [0, 1]"), ("v_full_pct", "Cover scale  [64.85, 69.4]"),
        ("capacity_mm", "Capacity  [30, 150 mm]"), ("depletion_fraction", "Stress frac.  [0.30, 0.70]"),
    ]
    for i, (ax, quota) in enumerate(zip(axes[1], [300, 600])):
        color = palette[quota]
        data = [sens.loc[(quota, key)].sort_index().V_pct.to_numpy()-base.at[quota, "V_steady_pct"]
                for key, _ in parameters]
        low, high = np.array(data).T
        y = np.arange(len(parameters))
        for row in y[::2]:
            ax.axhspan(row-.41, row+.41, color=P.LIGHT, lw=0)
        ax.hlines(y, np.minimum(low, high), np.maximum(low, high), color=color, lw=1.5)
        ax.scatter(low, y-.085, facecolors="white", edgecolors=color, s=27, zorder=3)
        ax.scatter(high, y+.085, color=color, marker="|", s=55, linewidths=1.4, zorder=4)
        ax.axvline(0, color=P.MUTED, lw=.85)
        ax.set(xlim=(-2.35, 3.85), yticks=y, yticklabels=[title for _, title in parameters],
               ylim=(5.52, -.5), xticks=[-2, 0, 2], xlabel="Change in cover (pp)")
        ax.tick_params(axis="y", labelleft=i == 0, length=0)
        ax.grid(axis="x", lw=.55)
        head(ax, "cd"[i], f"Input ranges at {quota} mm/yr")
    handles = [Line2D([], [], color=P.MUTED, marker="o", markerfacecolor="white", ls="none"),
               Line2D([], [], color=P.MUTED, marker="|", ls="none")]
    fig.legend(handles, ["Lower input", "Upper input"], loc="outside lower center", ncols=2)
    return fig


def optimiser(_inputs):
    fig, ax = sheet(1.65)
    for x, color, title, text in (
        (.025, P.TEAL, "Inputs to both solves", "Cohort water and cover\nInteger planting and PV lots"),
        (.375, P.BLUE, "1  Ecological ceiling", r"Maximise benefit $H$" "\n" r"Output $H_{\max}$"),
        (.725, P.PLUM, "2  Least-cost plans", r"Minimise net cost $N$" "\n" r"Require $H\geq\varphi H_{\max}$"),
    ):
        panel(ax, x, .14, .25, .69, "white", P.GRID)
        panel(ax, x, .62, .25, .21, color)
        label(ax, x+.125, .725, title, color="white", size=9, weight="bold", ha="center")
        label(ax, x+.125, .399, text, ha="center", size=9)
    arrow(ax, (.28, .48), (.37, .48), color=P.INK)
    arrow(ax, (.63, .48), (.72, .48), color=P.INK)
    label(ax, .5, .942, "Both solves use the same budget, water, labour and land limits",
          ha="center", size=8.7, color=P.MUTED)
    return fig


def cohort_plan(inputs):
    fig = cohort_handoff(inputs)
    timeline, cash = fig.axes
    head(timeline, "a", "Cohort irrigation and year-15 handoff")
    timeline.set_xticks(range(1, 16, 2))
    timeline.set_xlabel("Project year · block labels in mm/yr", labelpad=1)
    for block in timeline.collections:
        block.set(edgecolor="white", linewidth=.55)
    cash.set_yticks([0, 4, 8, 12])
    for container, hatch in zip(cash.containers, ("", "//", "."), strict=True):
        for bar in container:
            bar.set(edgecolor="white", linewidth=.45, hatch=hatch)
    fig.legends[0].remove()
    fig.legend(*cash.get_legend_handles_labels(), loc="outside lower center", ncols=4)
    head(cash, "b", "Annual spending and electricity income")
    return fig


def water_use(inputs, *, smooth=False):
    monthly = inputs.result("model2", "monthly")
    annual = keyed(inputs.result("model2", "annual"), "year").sort_index()
    caps = inputs.read(M2_CAPS)
    calendar = monthly.assign(use=100*monthly.gross_water_m3/monthly.cap_m3).pivot(
        index="month", columns="year", values="use").loc[range(1, 13), annual.index]
    may = calendar.loc[5]
    values = calendar.to_numpy()
    if not (np.isfinite(values).all() and values.min() >= 0 and values.max() <= 100):
        raise ValueError("Monthly utilisation must be present and within 0–100%")
    year = int(may.idxmax())
    annual_pct = 100*annual.water_m3/caps["annual_water_cap_m3"]
    fig, axes = panels(4.50, rows=2, cols=2, height_ratios=[1.45, 1], width_ratios=[1, .035])
    (heat, scale), (trend, unused) = axes
    unused.remove()
    if smooth:
        # Bilinear values between monthly/yearly sample centres. Repeat edge
        # values to cover the half-cell margins without extrapolating.
        ny, nx = calendar.shape
        x = np.linspace(-.5, nx-.5, nx*4+1)
        y = np.linspace(-.5, ny-.5, ny*4+1)
        across_years = np.array([np.interp(x, np.arange(nx), row) for row in values])
        surface = np.array([np.interp(y, np.arange(ny), column) for column in across_years.T]).T
        mesh = heat.pcolormesh(x, y, surface, shading="gouraud", cmap="GnBu", vmin=0, vmax=100)
        mesh.set_label("Monthly cap used (%)")
        heat.set(ylim=(ny-.5, -.5), yticks=range(ny), yticklabels=MONTHS)
        heat.tick_params(axis="y", length=0)
    else:
        mesh = C.annotated_heatmap(heat, calendar, rows=MONTHS, cols=annual.index,
                                   unit="Monthly cap used (%)", limits=(0, 100), cmap="YlGnBu",
                                   annotate=False)
        heat.add_patch(Rectangle((-.5, 3.5), calendar.shape[1], 1, fill=False, ec=P.INK, lw=.95))
    C.colorbar(fig, mesh, ax=heat, cax=scale, ticks=[0, 25, 50, 75, 100])
    heat.get_yticklabels()[4].set(color=P.INK, fontweight="bold")
    heat.tick_params(axis="x", labelbottom=False, length=0)
    heat.set_xticks([])
    head(heat, "a", "Monthly withdrawal relative to each monthly cap")

    lines(trend, annual.index, [C.Series("May / May cap", may, P.BLUE, "-", "o"),
                                C.Series("Full year / annual cap", annual_pct, P.AMBER, "--", "s")],
          xlabel="Project year", ylabel="Cap used (%)")
    trend.axhline(100, color=P.MUTED, lw=.8, ls=":")
    trend.axvline(year, color=P.GRID, lw=1)
    for series, color, shift in ((may, P.BLUE, 8), (annual_pct, P.AMBER, -12)):
        callout(trend, f"{series.at[year]:.0f}%", (year, series.at[year]), offset=(7, shift), color=color)
    trend.set(xlim=(annual.index.min()-.5, annual.index.max()+.5), xticks=annual.index,
              ylim=(0, 114), yticks=[0, 25, 50, 75, 100])
    head(trend, "b", "May and full-year utilisation")
    fig.legend(*trend.get_legend_handles_labels(), loc="outside lower center", ncols=2)
    return fig


def planning_tradeoff(inputs):
    fig = tradeoff(inputs)
    pv, tariff, frontier = fig.axes
    head(frontier, "a", "Cost of the discrete ecological targets")
    head(pv, "b", "PV capacity by target")
    head(tariff, "c", "Tariff and standalone PV screen")
    frontier.set_ylabel("Net present cost (M CNY)")
    frontier.xaxis.set_major_locator(MultipleLocator(500))
    for item in frontier.texts:
        if item.get_text().endswith("k"):
            item.set_text(item.get_text().removesuffix("k"))
    frontier.text(.97, .10, "Slopes in thousand CNY per additional effective ha·yr",
                  transform=frontier.transAxes, color=P.AMBER, ha="right", fontsize=8.2)
    for bar in pv.patches:
        if bar.get_facecolor() != pv.patches[0].get_facecolor():
            bar.set(edgecolor="white", hatch="///", lw=.5)
    tariff.set(xticks=[1, 2, 4, 6, 8, 10])
    return fig


def investment(inputs):
    data = keyed(inputs.result("model2", "scenario_summary"), "case")
    cases = {"constant_irrigation_only": "Constant irrigation only", "pv_price_low": "Lower PV tariff",
             "pv_capex_high": "Higher PV capital cost", "om_high": "O&M rates +50%",
             "initial_cover_low": "Initial cover halved"}
    base = data.loc["base"]
    subset = data.loc[list(cases)].sort_values("net_present_cost_cny", kind="stable")
    if not subset.feasible.all() or not subset.ecological_target_ha_year.eq(base.ecological_target_ha_year).all():
        raise ValueError("Cost sensitivity requires a common feasible ecological target")
    fig, axes = panels(2.30)
    ax = axes[0, 0]
    totals = subset.net_present_cost_cny/1e6
    delta = totals-base.net_present_cost_cny/1e6
    y = np.arange(len(delta))
    ax.barh(y, delta, color=[P.BLUE]*(len(y)-1)+[P.AMBER], height=.52)
    ax.axvline(0, color=P.INK, lw=.8)
    for row, change, total in zip(y, delta, totals):
        ax.text(change+.13, row, f"{change:+.2f}", va="center", color=P.INK, fontsize=8.6)
        ax.text(.995, row, f"{total:.2f}", transform=ax.get_yaxis_transform(),
                va="center", ha="right", fontsize=8.6, color=P.MUTED)
    ax.text(.995, 1.015, "Total (M CNY)", transform=ax.transAxes, ha="right", va="bottom", fontsize=8.3)
    ax.set(xlim=(0, delta.max()+1.9), yticks=y, yticklabels=[cases[k] for k in subset.index],
           ylim=(len(y)-.47, -.56), xlabel=f"Increase from {base.net_present_cost_cny/1e6:.2f} M CNY baseline")
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", lw=.55)
    ax.set_title(f"Ecological target held at {base.ecological_target_ha_year:,.0f} effective ha·yr", loc="left")
    return fig


def validation(inputs):
    fig = numerical_check(inputs)
    error, checks = fig.axes
    for y in (2.5, 5.5):
        error.axhline(y, color=P.GRID, lw=.7)
    head(error, "a", "Markov estimates against MC intervals")
    head(checks, "b", "Maximum change by refinement")
    for bar in checks.containers[1]:
        bar.set(edgecolor="white", lw=.45, hatch="//")
    legend = fig.legends[0]
    handles = legend.legend_handles[:-2]
    labels = [text.get_text() for text in legend.get_texts()]
    legend.remove()
    fig.legend([*handles, *checks.containers], labels, loc="outside lower center", ncols=3)
    return fig


def resilience(inputs):
    raw = inputs.result("model3", "project_annual")
    project = keyed(raw, ["case", "post_year"])
    cohort = keyed(inputs.result("model3", "cohort_annual"), ["case", "cohort_id", "post_year"]).sort_index()
    summary = keyed(inputs.result("model3", "summary"), ["case", "entity"])
    params = inputs.read("Results/v7/model1/model1_results.json")["adopted_parameters"]
    config = inputs.read("Results/v7/model3/scenario_configs.json")[BASE]
    threshold = params["K_section_pct"]*config["failure_cover_fraction_K"]
    ids = inputs.result("model3", "initial_cohorts").sort_values(
        ["age_year", "area_ha"], ascending=[False, False]).cohort_id
    base = project.loc[BASE].sort_index()
    t = base.index
    stationary = project.loc[STATIONARY].loc[t]
    climate = project.loc[NO_DISASTERS].loc[t]
    fig, axes = panels(4.8, rows=2, cols=2)
    risk, area, cover, benefit = axes.flat
    risk_series = [C.Series("Belt", base.project_failure_probability*100, P.INK,
                            band=(base.ci95_low*100, base.ci95_high*100, "Belt Wilson 95%"))]
    cover_series = []
    for key, letter, color, ls in zip(ids, "ABC", [P.TEAL, P.PLUM, P.AMBER], [":", "--", "-."], strict=True):
        data = cohort.loc[(BASE, key)].loc[t]
        risk_series.append(C.Series(letter, data.failure_probability*100, color, ls))
        band = (data.V_p05_pct, data.V_p95_pct, "B path P5–P95") if letter == "B" else None
        cover_series.append(C.Series(letter, data.V_mean_pct, color, ls, band=band))
    lines(risk, t, risk_series, xlabel="", ylabel="First-warning probability (%)")
    risk.set(ylim=(0, 105), yticks=[0, 25, 50, 75, 100])
    risk.legend(loc="lower right", ncols=2, handlelength=1.15, columnspacing=.7)
    core, belt = [summary.at[(BASE, entity), "restricted_mean_first_passage_years"]
                  for entity in (ids.iloc[1], "project")]
    risk.text(.97, .545, f"50-year restricted mean\nBelt {belt:.1f} yr · B {core:.1f} yr",
              transform=risk.transAxes, ha="right", fontsize=8.3)

    ever, now = base.expected_ever_failed_area_ha, base.expected_current_failed_area_ha
    area.fill_between(t, now, ever, color=P.TEAL, alpha=.14)
    lines(area, t, [C.Series("Ever below", ever, P.TEAL),
                    C.Series("Currently below", now, P.BLUE, "--"),
                    C.Series("Stationary, currently below", stationary.expected_current_failed_area_ha,
                             P.MUTED, ":")], xlabel="", ylabel="Expected area (ha)")
    area.vlines(50, now.at[50], ever.at[50], color=P.TEAL, lw=.8)
    area.text(48.8, (now.at[50]+ever.at[50])/2, f"{ever.at[50]-now.at[50]:.0f} ha back above",
              color=P.TEAL, ha="right", va="center", fontsize=8.4)
    area.set(ylim=(0, 329), yticks=[0, 100, 200, 300])
    for y, text, color, align in ((309, "Ever below", P.TEAL, "bottom"),
                                  (151, "Currently below", P.BLUE, "top"),
                                  (90, "Stationary, currently below", P.MUTED, "top")):
        area.text(49, y, text, color=color, ha="right", va=align, fontsize=8.4)

    lines(cover, t, cover_series, xlabel="Years after construction", ylabel="Cover proxy (%)",
          threshold=(threshold, f"Warning {threshold:.1f}%"))
    cover.set(ylim=(0, 34))
    cover.legend(loc="upper right", ncols=2, handlelength=1.1, columnspacing=.7)
    effective = "cumulative_cover_ha_year_mean"
    lines(benefit, t, [C.Series("Nonstationary hazards", base[effective], P.TEAL),
                       C.Series("Stationary hazards", stationary[effective], P.BLUE, "--"),
                       C.Series("Climate drift only", climate[effective], P.MUTED, ":")],
          xlabel="Years after construction", ylabel="Benefit (effective ha·yr)")
    benefit.set(ylim=(0, 7900))
    benefit.legend(loc="upper left", handlelength=1.2)
    ratio = base.at[50, effective]/climate.at[50, effective]
    callout(benefit, f"{ratio:.1%} of climate-only", (50, base.at[50, effective]),
            offset=(-8, -39), color=P.TEAL)
    for ax, letter, title in zip(axes.flat, "abcd", ("First-warning risk", "Area below threshold",
                                                   "Cover by cohort", "Cumulative benefit")):
        ax.set(xlim=(0, 51.5), xticks=range(0, 51, 10))
        head(ax, letter, title)
    return fig


def hazards(inputs):
    fig = storm_and_delivery(inputs)
    heat, dots = fig.axes[:2]
    head(heat, "a", "Joint storm sensitivity")
    head(dots, "b", "Scenario controls")
    for i, tick in enumerate(dots.get_yticklabels()):
        if tick.get_text() == "Baseline":
            tick.set(color=P.TEAL, fontweight="bold")
            dots.axhspan(i-.40, i+.40, color=P.LIGHT, lw=0, zorder=0)
    collected = [child for child in fig.axes if child.get_ylabel() == "Water (10³ m³)"]
    if len(collected) != 1:
        raise ValueError("Expected one May delivery panel")
    delivery = collected[0]
    delivered = delivery.containers[1].datavalues
    if not np.isclose(delivered[0], delivered[1], atol=.001, rtol=0):
        raise ValueError("May comparison expects the same capped delivery")
    delivery.axhline(delivered[0], color=P.AMBER, ls=":", lw=.9, zorder=1)
    for bar in delivery.containers[1]:
        bar.set(edgecolor="white", linewidth=.5, hatch="//")
    delivery.legend(loc="upper right", ncols=2, bbox_to_anchor=(1, 1.29))
    head(delivery, "c", "May drought delivery · first year after construction")
    return fig


FIGURES = {
    "fig05_stress_switches": stress,
    "fig06_holdout": holdout,
    "fig07_irrigation_response": irrigation,
    "fig08_drivers": drivers,
    "fig09_two_stage_optimisation": optimiser,
    "fig10_cohort_plan": cohort_plan,
    "fig11_water_use": water_use,
    "fig12_tradeoff": planning_tradeoff,
    "fig13_investment_sensitivity": investment,
    "fig14_markov_validation": validation,
    "fig15_resilience": resilience,
    "fig16_storm_and_delivery": hazards,
}

if __name__ == "__main__":
    available_figures = {**FIGURES, "fig11_water_use_smooth": partial(water_use, smooth=True)}
    main(available_figures, tuple(FIGURES), ROOT / "Figures/Paper2026_Polished")
