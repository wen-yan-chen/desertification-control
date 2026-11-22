"""Render the Practice2 paper alternatives from the frozen v7 exports."""

import argparse
from calendar import month_abbr
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
import numpy as np
import pandas as pd

from mcm_library import bars, charts as C
from mcm_style import __version__, head, palette as P, panels, paper_context, save_paper
from mcm_style.accents import callout


ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = ROOT.parent
OUT = ROOT / "Figures/Paper2026_Shared"
RESULTS = ROOT / "Results/v7"
BASE = "base_nonstationary"
STATIONARY = "stationary_reference"
NO_DISASTERS = "no_random_disasters"
MONTHS = list(month_abbr)[1:]
M2_CAPS = "Data/v7/m2_inputs/scenario.json"
SPEND_COLUMNS = ["construction_cny", "om_cny", "pv_facilities_cny"]
SPEND_NAMES = ["Planting", "O&M incl. water", "PV capital"]
SPEND_COLORS = [P.TEAL, P.BLUE, P.PLUM]


class FrozenInputs:
    """Track exactly the tables read and audit their bytes after export."""

    def __init__(self):
        self.hashes = {}

    def read(self, path):
        path = ROOT / path
        data = path.read_bytes()
        self.hashes[path] = sha256(data).hexdigest()
        if path.suffix == ".json":
            return json.loads(data)
        return pd.read_csv(BytesIO(data))

    def result(self, model, table):
        return self.read(RESULTS / model / f"{table}.csv")

    def verify(self):
        for path, digest in self.hashes.items():
            if digest != sha256(path.read_bytes()).hexdigest():
                raise ValueError(f"Frozen input changed during rendering: {path}")
        return {p.relative_to(ROOT).as_posix(): digest for p, digest in self.hashes.items()}


def keyed(data, columns):
    indexed = data.set_index(columns)
    if not indexed.index.is_unique:
        raise ValueError(f"Duplicate keys: {columns}")
    return indexed


def lines(ax, x, series, *, xlabel, ylabel, **kwargs):
    C.scenario_trends(ax, x, series, xlabel=xlabel, ylabel=ylabel, legend=None, **kwargs)
    ax.grid(axis="y", color=P.GRID, linewidth=.55)


def irrigation(inputs):
    curve = keyed(inputs.result("model1", "water_cover_curve"), "irrigation_mm_yr").sort_index()
    paths = keyed(inputs.result("model1", "scenario_annual"), ["scenario", "calendar_year"])
    if not curve.converged_both.all():
        raise ValueError("The dose figure requires convergence from both initial states")
    doses = [300, 600]
    fig, axes = panels(4.9, rows=2)
    dose, stop = axes[:, 0]
    lines(dose, curve.index, [C.Series("Periodic steady state", curve.V_steady_pct,
                                      P.TEAL, "-", "o")],
          xlabel="Annual irrigation (mm/yr)", ylabel="Cover proxy (%)")
    dose.set(xlim=(-40, 2050), ylim=(0, 35), yticks=[0, 10, 20, 30])
    for x, offset in zip(doses, [(-8, 10), (11, -12)]):
        value = curve.at[x, "V_steady_pct"]
        callout(dose, f"{x} mm: {value:.1f}%", (x, value), offset=offset, color=P.TEAL)
    steady = paths.loc["I600"].sort_index()
    stopped = paths.loc["stop_after_10"].loc[steady.index]
    first_dry_year = int(stopped.index[stopped.irrigation_mm_yr.eq(0)][0])
    start, end = steady.index[[0, -1]]
    xx = np.r_[start-1, steady.index]
    lines(stop, xx, [
        C.Series("600 mm/yr throughout", np.r_[steady.V_start_pct.iloc[0], steady.V_end_pct],
                 P.BLUE, "-"),
        C.Series("600 mm/yr, then stop", np.r_[stopped.V_start_pct.iloc[0], stopped.V_end_pct],
                 P.AMBER, "--"),
    ], xlabel="Calendar year (year-end state)", ylabel="Cover proxy (%)")
    stop.axvline(first_dry_year-.5, color=P.MUTED, lw=.8, ls=":")
    stop.text(first_dry_year, 31, f"Irrigation stops in {first_dry_year}", color=P.MUTED)
    stop.set(xlim=(start-1.3, end+.3), xticks=[2025, 2030, 2035, 2040, 2045, 2050],
             ylim=(0, 35), yticks=[0, 10, 20, 30])
    head(dose, "a", "Diminishing cover gains at higher doses")
    head(stop, "b", "Cover trajectory after irrigation stops")
    fig.legend(*stop.get_legend_handles_labels(), loc="outside lower center", ncols=2)
    return fig


def water_pressure(inputs):
    monthly = inputs.result("model2", "monthly")
    annual = keyed(inputs.result("model2", "annual"), "year").sort_index()
    caps = inputs.read(M2_CAPS)
    utilization = (monthly.gross_water_m3/monthly.cap_m3)*100
    calendar = monthly.assign(use=utilization).pivot(index="month", columns="year", values="use")
    calendar = calendar.loc[range(1, 13), annual.index]
    if calendar.isna().any().any():
        raise ValueError("Missing monthly utilization in the baseline plan")
    fig, axes = panels(5.15, rows=2, height_ratios=[1.55, 1])
    heat, use = axes[:, 0]
    mesh = C.annotated_heatmap(heat, calendar, rows=MONTHS, cols=calendar.columns,
                               unit="Monthly cap used (%)", limits=(0, 100),
                               cmap="YlGnBu", annotate=False)
    C.colorbar(fig, mesh, ax=heat, ticks=[0, 25, 50, 75, 100], pad=.02, aspect=22)
    heat.add_patch(Rectangle((-.5, 3.5), calendar.shape[1], 1, fill=False,
                             edgecolor=P.INK, lw=.8, clip_on=False))
    heat.get_yticklabels()[4].set_fontweight("bold")
    may = calendar.loc[5]
    use_annual = 100*annual.water_m3/caps["annual_water_cap_m3"]
    lines(use, annual.index, [
        C.Series("May withdrawal / May cap", may, P.BLUE, "-", "o"),
        C.Series("Annual withdrawal / annual cap", use_annual, P.AMBER, "--", "s"),
    ], xlabel="Project year", ylabel="Cap used (%)")
    use.set(xlim=(.6, 15.4), xticks=range(1, 16), ylim=(0, 112), yticks=[0, 25, 50, 75, 100])
    year = int(may.idxmax())
    callout(use, f"{may.at[year]:.0f}%", (year, may.at[year]), offset=(6, 8), color=P.BLUE)
    callout(use, f"{use_annual.at[year]:.0f}%", (year, use_annual.at[year]),
            offset=(6, -9), color=P.AMBER)
    head(heat, "a", "Monthly limits reveal a May bottleneck")
    heat.set_xlabel("Project year")
    head(use, "b", "May and annual caps tell different stories")
    fig.legend(*use.get_legend_handles_labels(), loc="outside lower center", ncols=2)
    return fig


def finance(inputs):
    data = keyed(inputs.result("model2", "annual"), "year").sort_index()
    cap = inputs.read(M2_CAPS)["annual_budget_cny"]/1e6
    gross = data.gross_spending_cny
    if not np.allclose(data[SPEND_COLUMNS].sum(axis=1), gross, atol=.01, rtol=0):
        raise ValueError("Expenditure components must sum to gross spending")
    shown = data.loc[[1, 2, 3, 4, 5, 15]]
    shares = shown[SPEND_COLUMNS].div(shown.gross_spending_cny, axis=0)*100
    fig, axes = panels(4.85, rows=2, height_ratios=[1, 1.1])
    allocation, flows = axes[:, 0]
    bars.composition_bars(allocation, [f"Year {i}" for i in shown.index], shares,
                         segments=SPEND_NAMES, colors=SPEND_COLORS, orientation="vertical",
                         min_label_pct=8, axis_label="Gross spending share (%)")
    allocation.legend(loc="lower center", bbox_to_anchor=(.5, 1.11), ncols=3)
    head(allocation, "a", "Spending mix in selected years")
    lines(flows, data.index, [
        C.Series("Gross spending", gross/1e6, P.BLUE, "-", "o"),
        C.Series("Electricity income", data.revenue_cny/1e6, P.AMBER, "--", "D"),
    ], xlabel="Project year", ylabel="Annual flow (million CNY)",
          threshold=(cap, f"{cap:g} million spending cap"))
    flows.set(xlim=(.6, 15.4), xticks=range(1, 16), ylim=(-.35, 13), yticks=[0, 4, 8, 12])
    head(flows, "b", "Electricity income rises after PV comes online")
    fig.legend(*flows.get_legend_handles_labels(), loc="outside lower center", ncols=3)
    return fig


def recovery(inputs):
    data = inputs.result("model3", "project_annual")
    wide = keyed(data, ["post_year", "case"]).unstack("case")
    ever = wide["expected_ever_failed_area_ha"][BASE]
    now = wide["expected_current_failed_area_ha"][BASE]
    stationary = wide["expected_current_failed_area_ha"][STATIONARY]
    cumulative = wide["cumulative_cover_ha_year_mean"]
    year = int(wide.index.max())
    fig, axes = panels(5.0, rows=2, sharex=True)
    area, benefit = axes[:, 0]
    area.fill_between(wide.index, now, ever, color=P.TEAL, alpha=.13)
    lines(area, wide.index, [
        C.Series("Ever below, baseline", ever, P.TEAL, "-"),
        C.Series("Currently below, baseline", now, P.BLUE, "--"),
        C.Series("Currently below, stationary", stationary, P.MUTED, ":"),
    ], xlabel="", ylabel="Expected area (ha)")
    callout(area, f"{ever.at[year]-now.at[year]:.0f} ha back above", (year, (ever.at[year]+now.at[year])/2),
            offset=(-12, 0), color=P.TEAL)
    area.vlines(year, now.at[year], ever.at[year], color=P.TEAL, lw=.9)
    area.set(ylim=(0, 329), yticks=[0, 100, 200, 300])
    area.legend(loc="lower right", ncols=1, handlelength=1.7)
    lines(benefit, wide.index, [
        C.Series("Nonstationary hazards", cumulative[BASE], P.TEAL, "-"),
        C.Series("Stationary hazards", cumulative[STATIONARY], P.BLUE, "--"),
        C.Series("Climate drift only", cumulative[NO_DISASTERS], P.MUTED, ":"),
    ], xlabel="Years after construction", ylabel="Benefit (effective ha·yr)")
    fraction = cumulative.at[year, BASE]/cumulative.at[year, NO_DISASTERS]
    callout(benefit, f"{fraction:.1%} of climate-only benefit", (year, cumulative.at[year, BASE]),
            offset=(-11, -31), color=P.TEAL)
    benefit.set(xlim=(0, year+1), xticks=range(0, year+1, 10), ylim=(0, 8000))
    benefit.legend(loc="upper left", handlelength=1.7)
    head(area, "a", "A first warning can be followed by recovery")
    head(benefit, "b", "Recovery does not erase the cumulative loss")
    return fig


def storm_risk(inputs, *, axes=None, association_label="Unlinked hazards"):
    summary = keyed(inputs.result("model3", "summary").query("entity == 'project'"), "case")
    configs = inputs.read("Results/v7/model3/scenario_configs.json")
    metric = summary.restricted_mean_first_passage_years
    scenarios = [(p["storm_rate_per_year"], (p["storm_loss_low"]+p["storm_loss_high"])/2, metric.at[key])
                 for key, p in configs.items() if key.startswith("joint_rate_")]
    matrix = pd.DataFrame(scenarios, columns=["rate", "loss", "rmst"]).pivot(
        index="rate", columns="loss", values="rmst").sort_index()
    if matrix.shape != (3, 3) or matrix.isna().any().any():
        raise ValueError("Expected the nine frozen storm scenarios")
    keys = ["no_irrigation", "water_80pct", BASE, "no_drought_storm_association",
            "no_drought", "water_120pct"]
    labels = ["No irrigation", "Request −20%", "Baseline", association_label,
              "No drought", "Request +20%"]
    if axes is None:
        _, grid = panels(3.2, cols=2, width_ratios=[1, 1.26])
        axes = grid[0]
    heat, dots = axes
    fig = heat.figure
    mesh = C.annotated_heatmap(heat, matrix, rows=[f"{v:g}" for v in matrix.index],
                               cols=[f"{v:.0%}" for v in matrix.columns], limits=(0, 50),
                               unit="RMST (yr)", cmap="academic_plum")
    for label in heat.texts:
        label.set_fontweight("bold")
    C.colorbar(fig, mesh, ax=heat, ticks=range(0, 51, 10), pad=.025, aspect=20)
    heat.set(xlabel="Mean cover loss per storm", ylabel="Initial storm rate (1/yr)")
    C.comparison_dots(dots, labels, metric.loc[keys], xlabel="RMST (yr)",
                      baseline=(metric.at[BASE], "Baseline"), color=P.TEAL)
    head(heat, "a", "Joint storm scenarios")
    head(dots, "b", f"Controls vs. baseline ({metric.at[BASE]:.1f} yr)")
    return fig


def drought_delivery(inputs):
    raw = inputs.result("model3", "resources").query("case == @BASE and post_year == 1")
    data = keyed(raw, ["month", "drought"]).sort_index()
    normal = data.xs(False, level="drought").loc[range(1, 13)]
    drought = data.xs(True, level="drought").loc[normal.index]
    use = 100*drought.gross_water_m3/drought.cap_m3
    binds = drought.index[drought.slack_m3.abs().lt(1e-6)]
    fig, axes = panels(4.6, rows=2, sharex=True, height_ratios=[1.35, 1])
    water, pressure = axes[:, 0]
    for ax in (water, pressure):
        for month in binds:
            ax.axvspan(month-.5, month+.5, color=P.LIGHT, lw=0, zorder=0)
    lines(water, normal.index, [
        C.Series("Normal delivery", normal.delivered_eco_m3/1000, P.BLUE, "-", "o"),
        C.Series("Drought delivery", drought.delivered_eco_m3/1000, P.AMBER, "--", "s"),
    ], xlabel="", ylabel="Ecological water (thousand m³)")
    cut = 1-drought.at[5, "delivered_eco_m3"]/normal.at[5, "delivered_eco_m3"]
    callout(water, f"May: {cut:.0%} less", (5, drought.at[5, "delivered_eco_m3"]/1000),
            offset=(13, -13), color=P.AMBER)
    water.set(ylim=(-8, 225), yticks=[0, 50, 100, 150, 200])
    lines(pressure, drought.index, [C.Series("Drought withdrawals", use, P.PLUM, "-", "D")],
          xlabel="Month in first year after construction", ylabel="Drought cap used (%)",
          threshold=(100, "Drought cap"))
    pressure.set(xlim=(.5, 12.5), xticks=range(1, 13), xticklabels=MONTHS,
                 ylim=(-4, 113), yticks=[0, 25, 50, 75, 100])
    head(water, "a", "Ecological delivery under normal and drought conditions")
    head(pressure, "b", "Gross withdrawals including PV washing")
    handles, labels = water.get_legend_handles_labels()
    fig.legend([*handles, Patch(facecolor=P.LIGHT, edgecolor=P.GRID)],
               [*labels, "Drought cap binds"], loc="outside lower center", ncols=3)
    return fig


def numerical_check(inputs):
    data = inputs.result("model3", "markov_mc_comparison")
    metadata = inputs.read("Results/v7/model3/validation_summary.json")
    refinements = inputs.result("model3", "grid_validation").pivot(
        index="cohort_id", columns="comparison", values="max_absolute_probability_difference")
    ids = inputs.result("model3", "initial_cohorts").sort_values(
        ["age_year", "area_ha"], ascending=[False, False]).cohort_id.to_list()
    labels = dict(zip(ids, "ABC", strict=True))
    fine_nv, mid_nv = sorted(data.nv.unique())[-2:][::-1]
    index = pd.MultiIndex.from_product([ids, [10, 30, 50]], names=["cohort_id", "post_year"])
    fine = keyed(data[data.nv.eq(fine_nv)], index.names).loc[index]
    mid = keyed(data[data.nv.eq(mid_nv)], index.names).loc[index]
    if not np.allclose(mid.mc_failure_probability, fine.mc_failure_probability, rtol=0, atol=1e-9):
        raise ValueError("Grid points must use the same MC reference")
    fig, axes = panels(4.0, cols=2, width_ratios=[1.47, 1.0])
    error, checks = axes[0]
    x = 100*fine.mc_failure_probability
    grid_names = [f"{mid_nv} × {mid.nm.iloc[0]} grid", f"{fine_nv} × {fine.nm.iloc[0]} grid"]
    C.comparison_intervals(
        error, [f"{labels[cohort]} · {t} yr" for cohort, t in index],
        100*fine.mc_ci95_low-x, 100*fine.mc_ci95_high-x,
        [C.Series(grid_names[0], 100*mid.markov_failure_probability-x, P.BLUE, marker="o"),
         C.Series(grid_names[1], 100*fine.markov_failure_probability-x, P.TEAL, marker="D")],
        xlabel="Markov − Monte Carlo (pp)", interval_label="MC 95% interval",
        baseline=(0, "No difference"), show_legend=False, row_separation=.40)
    error.set(xticks=[-1, -.5, 0, .5, 1])
    bars.grouped_bars(checks, list(labels.values()), [
        bars.BarSeries("Finer state grid", 100*refinements.loc[ids, "state_grid"], P.BLUE),
        bars.BarSeries("More shock nodes", 100*refinements.loc[ids, "shock_quadrature"], P.PLUM),
    ], value_label="Max. probability change (pp)", orientation="horizontal",
       maximum=.27, fmt=".3f", legend=False)
    checks.set(xticks=[0, .10, .20])
    head(error, "a", "Stationary-chain comparison")
    head(checks, "b", "Refinement sensitivity")
    count = int(fine.inside_mc_ci95.sum())
    if count != metadata["finest_points_inside_mc_ci95"]:
        raise ValueError("Coverage count disagrees with frozen validation summary")
    h1, l1 = error.get_legend_handles_labels()
    h2, l2 = checks.get_legend_handles_labels()
    legend = dict(zip(l1, h1))
    left_labels = ["MC 95% interval", "No difference", *grid_names]
    fig.legend([*(legend[label] for label in left_labels), *h2], [*left_labels, *l2],
               loc="outside lower center", ncols=3)
    return fig


FIGURES = {
    "05_m1_irrigation_cover": irrigation,
    "08a_m2_water_pressure": water_pressure,
    "08b_m2_funding": finance,
    "12_m3_recovery_benefit": recovery,
    "13_m3_storm_sensitivity": storm_risk,
    "14_m3_numerical_check": numerical_check,
    "16_m3_drought_delivery": drought_delivery,
}

PAPER_FIGURES = (
    "08a_m2_water_pressure",
    "13_m3_storm_sensitivity",
    "14_m3_numerical_check",
)


def main(figures=FIGURES, defaults=PAPER_FIGURES, destination=OUT):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="+", choices=tuple(figures))
    parser.add_argument("--out", type=Path, default=destination)
    args = parser.parse_args()
    output = args.out.resolve()
    if not any(output.is_relative_to(parent) for parent in (ROOT/"Figures", WORKSPACE/"tmp")):
        parser.error("Output must go under Practice2/Figures or workspace tmp")
    names = tuple(args.only or defaults)
    report = output/("qa-all.json" if args.only is None else f"qa-{'-'.join(names)}.json")
    for path in [report, *(output/f"{n}.{ext}" for n in names for ext in ("pdf", "png"))]:
        if path.exists():
            raise FileExistsError(path)
    entries = {}
    with paper_context():
        for name in names:
            inputs = FrozenInputs()
            fig = figures[name](inputs)
            try:
                files, issues = save_paper(fig, output/name, title=name.replace("_", " "))
                entries[name] = {"files": {ext: f.name for ext, f in files.items()},
                                 "inputs_sha256": inputs.verify(),
                                 "layout_issues": [item.__dict__ for item in issues]}
            finally:
                plt.close(fig)
            print(f"{name}: {len(issues)} layout flag(s)")
    report.write_text(json.dumps({"style_version": __version__, "placed_width_in": 6.5,
                                  "figures": entries}, indent=2)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
