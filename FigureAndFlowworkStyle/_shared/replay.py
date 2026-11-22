"""Replay selected Practice1 and Practice2 papers from frozen inputs, for review."""

import argparse
import hashlib
import json
from math import isclose
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from pypdf import PdfReader

from mcm_library import bars as B, charts as C, diagrams as D, maps as M
from mcm_style import __version__, grid, head, palette as P, panels, paper_context, save_paper
from mcm_style.accents import callout, gradient_area, gradient_bar

ROOT = Path(__file__).resolve().parent.parent
P1 = ROOT / "Practice1/Code"
P2 = ROOT / "Practice2"
R = P2 / "Results/v7"
DATA = P2 / "Data/v7"
M1 = P1 / "M1_equilibrium/results"
BASE = "base_nonstationary"
SCENARIOS = (
    (BASE, "Nonstationary", P.TEAL, "-"),
    ("stationary_reference", "Stationary", P.BLUE, "--"),
)


def investment(rec):
    rec = rec.iloc[0]
    fig, axes = panels(3.25)
    ax = axes[0, 0]
    values = rec[["spend_I", "spend_E", "spend_C"]].astype(float).to_numpy()*100
    for i, (v, cmap) in enumerate(zip(values, ("morandi_teal", "morandi_gold", "morandi_coral"))):
        gradient_bar(ax, 0, v, i-.27, .54, cmap=cmap, rounding=.12)
        ax.annotate(f"{v:.2f}", (i, v), (0, 4), textcoords="offset points", ha="center")
    ax.set(xlim=(-.55, 2.55), ylim=(0, max(values)*1.18), xticks=range(3),
           xticklabels=["Infrastructure", "Ecology", "Community"],
           ylabel="New investment (million USD/yr)")
    grid(ax)
    return fig


def investment_solid(rec):
    """Same frozen investment data, using the formal solid-bar recipe."""
    values = rec.iloc[0][["spend_I", "spend_E", "spend_C"]].astype(float).to_numpy()*100
    fig, axes = panels(3.25)
    B.grouped_bars(axes[0, 0], ["Infrastructure", "Ecology", "Community"], [
        B.BarSeries("Annual investment", values, P.BLUE),
    ], value_label="New investment (million USD/yr)", fmt=".2f", legend=False)
    return fig


def pareto(front, rec):
    columns = ["x", "R", "C_env"]
    return C.pareto_cloud(front[columns], selected=rec[columns].iloc[0],
                          scores=front.S, score_label="Resident satisfaction",
                          axis_labels=("Visitors (10,000/yr)", "Revenue (100M USD/yr)",
                                       "Environmental pressure"), cmap="morandi_heat")


def response(front, rec):
    x, y = front.x/100, front.R*100
    # Only the visual guide uses grouped means; every original sample is shown.
    grouped = pd.Series(y.to_numpy(), index=x).groupby(level=0).mean()
    fig, axes = panels(3.1)
    ax = axes[0, 0]
    gradient_area(ax, grouped.index, grouped.values, cmap="morandi_teal", alpha=.40)
    ax.scatter(x, y, s=8, color=P.MORANDI["slate"], label="Sampled results")
    ax.plot(grouped.index, grouped.values, color=P.BLUE, lw=1.15, label="Guide through sample means")
    xy = (rec.x.iat[0]/100, rec.R.iat[0]*100)
    ax.scatter(*xy, color=P.AMBER, marker="*", s=75, zorder=4, label="Selected plan")
    ax.set(xlabel="Annual visitors (million)", ylabel="Annual revenue (million USD)",
           ylim=(0, y.max()*1.18))
    ax.legend(loc="lower right")
    grid(ax)
    return fig


def radar(policy):
    scores = policy.pivot(index="policy_id", columns="destination", values="closeness")
    labels = ("Capacity", "Shore power", "Visitor cap", "Fee / tax",
              "Rent subsidy", "Transit", "Alcohol control")
    scores = scores.loc[[f"P{i}" for i in range(1, len(labels)+1)]]
    return C.radar_profile(labels, [
        C.Series("Juneau", scores.Juneau, P.TEAL, "-", "o"),
        C.Series("Venice", scores.Venice, P.AMBER, "--", "s"),
    ])


def framework():
    return D.research_framework([
        D.Stage("M1  Water and cover", "Calibrate cover; run a\ndaily water balance",
                "Evidence", "Station cover and weather", P.TEAL),
        D.Stage("M2  Build and operate", "Schedule planting, water,\nlabour and PV over 15 years",
                "Planning assumptions", "Resource caps and unit costs", P.BLUE),
        D.Stage("M3  Withstand shocks", "Simulate 50 years of\ndrought and storm damage",
                "Hazard assumptions", "Storm, drought and climate", P.PLUM),
    ], handoffs=("Water–cover trajectories", "Year-15 cohort states"), contributors=(1, 2),
        deliverable=("Operating brief", "Secure water, fund upkeep and monitor recovery"))


def study_map(meta, section, tile_paths):
    extent = (80, 89.5, 36, 42.55)
    categories = {"XT": "Corridor", "TZ": "Interior"}
    styles = {"Margin": (P.TEAL, "o"), "Corridor": (P.AMBER, "^"), "Interior": (P.PLUM, "s")}
    offsets = {"KEL": (-22, 6), "YL": (6, -7), "ALE": (-20, 7), "YT": (-4, -13),
               "MF": (7, 5), "QM": (6, 7), "RQ": (6, 3), "XT": (7, -5), "TZ": (-17, 6)}
    sites = [M.Site(s["code"], s["lon"], s["lat"], categories.get(s["code"], "Margin"),
                    offsets[s["code"]]) for s in meta["sites"]]
    tile_dir = next(iter(tile_paths)).parent
    fig, axes = panels(4.9)
    ax = axes[0, 0]
    M.study_map(ax, extent, sites, image=M.cached_tiles(tile_dir, extent, zoom=7),
                attribution="Esri World Imagery", styles=styles,
                route=[(p["lon"], p["lat"]) for p in section["centerline"]],
                route_label="Study transect", scale=(87.25, 36.46, 100),
                longitude_ticks=(81, 83, 85, 87, 89), latitude_ticks=(37, 39, 41))
    fig.legend(loc="outside lower center", ncols=4)
    return fig


def tradeoff(summary, screening, config):
    runs = summary.query("group == 'frontier'").copy()
    runs["target"] = runs.case.str.removeprefix("frontier_").astype(float)
    runs = runs.sort_values("target")
    screening = screening.query("start_year <= 10").sort_values("start_year")
    tariff = config["pv_price_cny_kwh"]
    # Keep all target positions, even if a future replay marks one infeasible.
    feasible = runs.feasible
    return C.target_tradeoff([f"{v:.0%}" for v in runs.target],
                             runs.ecological_ha_year.where(feasible),
                             runs.net_present_cost_cny.where(feasible)/1e6,
                             runs.pv_installed_final_kw.where(feasible)/1000,
                             chosen="60%", benefit_label="Achieved benefit (effective ha·yr)",
                             cost_label="Net present cost (million CNY)", capacity_label="PV (MW)",
                             target_label="Ecological target", screening=(
                                 screening.start_year, screening.break_even_price_cny_kwh,
                                 "PV build year", "Price (CNY/kWh)", tariff, f"Tariff {tariff:.2f}"))


def trends(annual):
    aligned = annual.set_index(["post_year", "case"]).sort_index()
    idx = aligned.index.get_level_values("post_year").unique()
    fig, axes = panels(3.55, 1, 2, sharey=True)
    for i, (ax, measure, title) in enumerate(zip(
        axes[0], ["expected_ever_failed_area_ha", "expected_current_failed_area_ha"],
        ["Ever below threshold", "Currently below threshold"],
    )):
        wide = aligned[measure].unstack("case").loc[idx]
        series = [C.Series(label, wide[case], color, style) for case, label, color, style in SCENARIOS]
        C.scenario_trends(ax, idx, series, xlabel="Years after construction",
                          ylabel="Expected area (ha)" if i == 0 else "", legend=None)
        ax.set(xlim=(0, 50), ylim=(0, 320))
        head(ax, "ab"[i], title)
    fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="outside lower center", ncols=2)
    return fig


def stress(summary, config, resources):
    metric = "restricted_mean_first_passage_years"
    results = summary.query("entity == 'project'").set_index("case")[metric]
    rows = [{"rate": cfg["storm_rate_per_year"],
             "loss": (cfg["storm_loss_low"]+cfg["storm_loss_high"])/2,
             "value": results.loc[case]}
            for case, cfg in config.items() if case.startswith("joint_rate_")]
    mat = pd.DataFrame(rows).pivot(index="rate", columns="loss", values="value")
    fig, axes = panels(5.2, 2, 2, width_ratios=[1, 1.18])
    heat, dots = axes[0]
    mesh = C.annotated_heatmap(heat, mat, rows=[f"{v:g}" for v in mat.index],
                               cols=[f"{v:.0%}" for v in mat.columns], limits=(0, 50),
                               unit="Restricted mean (yr)", cmap="academic_plum")
    C.colorbar(fig, mesh, ax=heat, ticks=range(0, 51, 10), pad=.035)
    heat.set(xlabel="Mean cover loss per storm", ylabel="Storm rate (1/yr)")
    keys = ["no_irrigation", "water_80pct", BASE, "no_drought_storm_association",
            "no_drought", "water_120pct"]
    categories = ["No irrigation", "Request −20%", "Baseline", "Unlinked hazards",
                  "No drought", "Request +20%"]
    C.comparison_dots(dots, categories, results.loc[keys], xlabel="Restricted mean (yr)",
                      baseline=(results.loc[BASE], "Baseline"))
    # Put the reference in the title to leave room for measured dot labels.
    head(dots, "b", f"Contrasts · baseline {results.loc[BASE]:.1f} yr")
    spec = axes[1, 0].get_gridspec()
    for ax in axes[1]:
        ax.remove()
    water = fig.add_subplot(spec[1, :])
    monthly = resources.query("case == @BASE and post_year == 1").set_index(["month", "drought"])
    delivery = monthly.delivered_eco_m3.unstack("drought")/1000
    cap = monthly.cap_m3.unstack("drought")[True]/1000
    C.scenario_trends(water, delivery.index, [
        C.Series("Normal delivery", delivery[False], P.BLUE, "-", "o"),
        C.Series("Drought delivery", delivery[True], P.AMBER, "--", "s"),
        C.Series("Drought cap incl. PV", cap.reindex(delivery.index), P.MUTED, ":"),
    ], xlabel="Month", ylabel="Water (thousand m³)", legend=None)
    water.set(xticks=range(1, 13), xticklabels="Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())
    may = delivery.loc[5]
    callout(water, f"May: {1-may[True]/may[False]:.0%} less", (5, may[True]),
            offset=(9, -16), color=P.AMBER)
    fig.legend(*water.get_legend_handles_labels(), loc="outside lower center", ncols=3)
    head(heat, "a", "Joint storm scenarios")
    head(water, "c", "Canal delivery in year one")
    return fig


def numerical(compare):
    high, low = sorted(compare.nv.unique())[-2:][::-1]
    fine = compare[compare.nv.eq(high)].set_index(["cohort_id", "post_year"]).sort_index()
    medium = (compare[compare.nv.eq(low)].set_index(["cohort_id", "post_year"])
              .loc[fine.index])
    letters = {key: f"Cohort {letter}" for key, letter in
               zip(fine.index.unique(level="cohort_id"), "ABC", strict=True)}
    labels = [f"{letters[cohort]} · {t:g} yr" for cohort, t in fine.index]
    fig, axes = panels(3.45)
    ax = axes[0, 0]
    def residual(x):
        return 100*(x.markov_failure_probability-x.mc_failure_probability)
    C.comparison_intervals(ax, labels, 100*(fine.mc_ci95_low-fine.mc_failure_probability),
                           100*(fine.mc_ci95_high-fine.mc_failure_probability), [
        C.Series(f"{low} × {medium.nm.iat[0]} grid", residual(medium), P.BLUE, marker="o"),
        C.Series(f"{high} × {fine.nm.iat[0]} grid", residual(fine), P.TEAL, marker="D"),
    ], xlabel="Markov − Monte Carlo (percentage points)",
       interval_label="MC 95% interval (centered)", baseline=(0, "No difference"),
       show_legend=False)
    fig.legend(*ax.get_legend_handles_labels(), loc="outside lower center", ncols=2)
    return fig


class Example:
    def __init__(self, source, render, *inputs, fixed=()):
        self.source = source
        self.render = render
        self.inputs = inputs
        self.fixed = tuple(fixed)

    def draw(self):
        values = [pd.read_csv(p) if p.suffix == ".csv" else json.loads(p.read_text(encoding="utf-8"))
                  for p in self.inputs]
        return self.render(*values, self.fixed) if self.fixed else self.render(*values)


EXAMPLES = {
    "p1_01_gradient_bars": Example("Practice1 M1P_01", investment, M1/"recommended.csv"),
    "p1_01_solid_bars": Example("Practice1 M1P_01 / FigureTraining 11", investment_solid,
                                 M1/"recommended.csv"),
    "p1_03_pareto_cloud": Example("Practice1 M1P_03", pareto, M1/"pareto.csv", M1/"recommended.csv"),
    "p1_04_gradient_area": Example("Practice1 M1P_04", response, M1/"pareto.csv", M1/"recommended.csv"),
    "p1_06_radar": Example("Practice1 M4P_04", radar, P1/"M4_migration/results/M4_policy_ranking.csv"),
    "p2_01_framework": Example("Practice2 01", framework),
    "p2_02_study_map": Example("Practice2 02 (map panel)", study_map, DATA/"raw/manifest.json",
                               DATA/"m1_audited/section_definition.json",
                               fixed=sorted((DATA/"raw/basemap_tiles").glob("7_*.jpg"))),
    "p2_09_tradeoff": Example("Practice2 09", tradeoff, R/"model2/scenario_summary.csv",
                              R/"model2/pv_screening.csv", DATA/"m2_inputs/scenario.json"),
    "p2_12_trends": Example("Practice2 12b / FigureTraining paired trends", trends,
                             R/"model3/project_annual.csv"),
    "p2_13_stress": Example("Practice2 13", stress, R/"model3/summary.csv",
                            R/"model3/scenario_configs.json", R/"model3/resources.csv"),
    "p2_14_numerical_check": Example("Practice2 14 (stationary grid panel)", numerical,
                                     R/"model3/markov_mc_comparison.csv"),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_files(paths):
    pdf, = PdfReader(paths["pdf"]).pages
    width = float(pdf.mediabox.width)
    if not isclose(width, 468, abs_tol=.01) or not pdf.extract_text().strip():
        raise ValueError("PDF must be 6.5 inches wide and have selectable text")
    resources = pdf["/Resources"].get("/Font", {})
    fonts = {str(value.get_object()["/Subtype"]) for value in resources.get_object().values()}
    if "/Type3" in fonts or "/Type0" not in fonts:
        raise ValueError(f"Expected embedded TrueType text, got {fonts}")
    with Image.open(paths["png"]) as png:
        if png.width != 1950 or not all(isclose(v, 300, abs_tol=.02) for v in png.info["dpi"]):
            raise ValueError("PNG must match 6.5 inches at 300 dpi")
        if abs(png.height - float(pdf.mediabox.height)*300/72) > 1:
            raise ValueError("PDF and PNG canvas heights differ")
        return {"pdf_width_pt": width, "png_px": png.size, "dpi": 300, "pdf_fonts": sorted(fonts)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="+", choices=tuple(EXAMPLES))
    parser.add_argument("--out", type=Path, default=ROOT/"tmp"/f"figure-review-v{__version__}")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing replay files.")
    parser.add_argument("--against", type=Path, help="Verify inputs match an archived QA report.")
    args = parser.parse_args()
    out = args.out.resolve()
    protected = [ROOT/"Practice1", ROOT/"Practice2", ROOT/"FigureTraining"]
    if any(out.is_relative_to(path) for path in protected):
        parser.error("replay output must be outside the historical training directories")
    selected = args.only or EXAMPLES
    baseline = (json.loads(args.against.read_text(encoding="utf-8"))["figures"]
                if args.against else None)
    names = "-".join(selected) if args.only else "all"
    report = out / (f"qa-{names}.json" if len(names) < 140 else "qa-selected.json")
    if not args.overwrite and report.exists():
        raise FileExistsError(report)
    entries = {}
    for name in selected:
        example = EXAMPLES[name]
        hashes = {p: digest(p) for p in (*example.inputs, *example.fixed)}
        sources = {p.relative_to(ROOT).as_posix(): v for p, v in hashes.items()}
        if baseline is not None and baseline.get(name, {}).get("source_sha256") != sources:
            raise ValueError(f"Frozen inputs differ from the archived baseline: {name}")
        with paper_context():
            fig = example.draw()
            try:
                paths, issues = save_paper(fig, out/name, overwrite=args.overwrite)
                facts = verify_files(paths)
            finally:
                plt.close(fig)
        if any(digest(p) != value for p, value in hashes.items()):
            raise ValueError(f"Frozen inputs changed during replay: {name}")
        entries[name] = {"reference": example.source, "spec": facts,
                         "issues": [i.__dict__ for i in issues],
                         "source_sha256": sources}
        print(f"{name}: {len(issues)} visual review flag(s)")
    report.write_text(json.dumps({"style_version": __version__, "matplotlib": matplotlib.__version__,
                                  "figures": entries}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
