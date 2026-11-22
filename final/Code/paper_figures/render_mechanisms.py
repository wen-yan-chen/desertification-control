"""Render the compact workflow and mechanism plates for the current paper."""

from matplotlib.patches import Ellipse
import numpy as np
import pandas as pd

from mcm_style import head, palette as P, panels
from mcm_style.components import arrow, label, panel, sheet
from render_shared import ROOT, main


def workflow(_inputs):
    fig, ax = sheet(2.50)
    columns = (
        (.02, P.AWARD["blue"], "1   Water and cover", "Weather and satellite cover",
         "Fit growth and decay", "Simulate daily root-zone water", "Growth and water model"),
        (.36, P.PLUM, "2   Plan and budget", "Water, land, labour and budget",
         "Simulate cohorts", "Solve the 15-year plan", "Final cohort states"),
        (.70, P.AMBER, "3   Stress-test the belt", "Climate trends and hazards",
         "Ration water and apply shocks", "Track warning and recovery", "Risk and recovery"),
    )
    for x, color, title, evidence, first, second, output in columns:
        panel(ax, x, .23, .28, .70, "white", P.GRID)
        panel(ax, x, .77, .28, .16, color)
        label(ax, x+.016, .85, title, size=10, color="white", weight="bold")
        label(ax, x+.016, .68, evidence, size=8.3, color=color)
        for y, description in ((.52, first), (.40, second)):
            panel(ax, x+.012, y-.049, .256, .095, P.LIGHT)
            label(ax, x+.022, y, description, size=8.4)
        label(ax, x+.14, .284, output, size=8.4, color=color, weight="bold", ha="center")
    for x in (.30, .64):
        arrow(ax, (x+.004, .284), (x+.056, .284), color=P.INK)
    arrow(ax, (.84, .225), (.84, .17), color=P.AWARD["green"], head=7)
    panel(ax, .02, .035, .96, .132, P.AWARD["green"])
    label(ax, .04, .101, "4   Operating priorities", size=10.2, color="white", weight="bold")
    label(ax, .405, .101, "Water delivery, upkeep funding and drought response", size=8.8, color="white")
    return fig


def water_feedback(_inputs):
    fig, ax = sheet(1.67)
    nodes = [
        (.24, .77, P.TEAL, r"Annual cover  $V_t$"),
        (.76, .77, P.BLUE, r"Daily demand  $D_j$"),
        (.76, .23, P.BLUE, r"Actual uptake  $T_{a,j}$"),
        (.24, .23, P.TEAL, r"Annual demand met  $\overline{W}_t$"),
    ]
    for x, y, color, text in nodes:
        panel(ax, x-.171, y-.083, .342, .166, P.LIGHT, color)
        label(ax, x, y, text, size=9.3, weight="bold", color=color, ha="center")
    arrow(ax, (.418, .78), (.582, .78), color=P.BLUE, connectionstyle="arc3,rad=-.25")
    arrow(ax, (.79, .664), (.79, .336), color=P.BLUE, connectionstyle="arc3,rad=-.33")
    arrow(ax, (.582, .22), (.418, .22), color=P.TEAL, connectionstyle="arc3,rad=-.25")
    arrow(ax, (.21, .336), (.21, .664), color=P.TEAL, connectionstyle="arc3,rad=-.33")
    label(ax, .50, .50, "Daily water balance\nAnnual cover update", ha="center", size=9, color=P.MUTED)
    label(ax, .133, .50, r"$t\to t+1$", ha="center", size=9, color=P.TEAL)
    label(ax, .879, .50, r"$K_s(M_j^{\mathrm{wet}})$", ha="center", size=9, color=P.BLUE)
    return fig


def root_zone(_inputs):
    fig, ax = sheet(1.83)
    panel(ax, .36, .19, .26, .53, P.LIGHT, radius=0)
    panel(ax, .36, .19, .26, .24, P.GRID, radius=0)
    ax.plot([.36,.36,.62,.62], [.72,.19,.19,.72], color=P.INK, lw=1.3, zorder=3)
    for y, detail in ((.72, r"Capacity  $C$"), (.48, r"Stress threshold  $(1-p)C$")):
        ax.plot([.36,.62], [y,y], ls="--", lw=.9, color=P.AMBER, zorder=3)
        label(ax, .644, y-.04, detail, size=8.7, color=P.AMBER)
    label(ax, .49, .31, r"Available water  $M_j^{\mathrm{wet}}$", ha="center", size=8.7)
    label(ax, .32, .86, r"Effective inflow  $\alpha_PP_j+\eta_w I_j$", ha="center", size=9, color=P.BLUE)
    arrow(ax, (.456, .80), (.456, .60), color=P.BLUE, zorder=4)
    arrow(ax, (.62, .72), (.71, .86), color=P.MUTED, connectionstyle="arc3,rad=.13")
    label(ax, .724, .86, "Overflow", size=8.7)
    arrow(ax, (.351, .33), (.255, .60), color=P.TEAL, connectionstyle="arc3,rad=.16")
    ax.plot([.229,.229], [.64,.78], lw=1.3, color=P.TEAL)
    for x, angle in ((.209, 31), (.249, -31)):
        ax.add_patch(Ellipse((x,.734), .063, .069, angle=angle, fc=P.TEAL, ec="none"))
    label(ax, .205, .53, r"Transpiration  $T_{a,j}$", ha="right", size=9, color=P.TEAL)
    label(ax, .49, .079, r"Carry forward  $M_{j+1}=M_j^{\mathrm{wet}}-T_{a,j}$",
          ha="center", size=9, weight="bold")
    return fig


def stress_switches(inputs):
    data = inputs.read("Data/v7/m1_audited/panel_m1.csv")
    dates = pd.to_datetime(data.date)
    reference = data[data.site.isin(["YT", "MF"]) & dates.dt.year.between(2015, 2022)]
    temperatures = reference.groupby(dates.dt.month).era_T.mean().sort_index()
    if len(temperatures) != 12:
        raise ValueError("Monthly temperature markers require all 12 months")

    fig, axes = panels(2.18, cols=2)
    water, season = axes[0]
    capacity, threshold = 75, 37.5
    water.axvspan(0, threshold, color=P.LIGHT, lw=0)
    water.plot([0, threshold, capacity], [0, 1, 1], color=P.BLUE, lw=1.7)
    water.axvline(threshold, color=P.AMBER, ls="--", lw=.9)
    water.text(40, .12, "37.5 mm", color=P.AMBER, fontsize=8.5)
    water.set(xlim=(0, capacity), ylim=(-.05, 1.13), xticks=[0, 25, 50, 75],
              yticks=[0, .5, 1], xlabel="Available root-zone water (mm)", ylabel=r"$K_s$")
    head(water, "a", "Water-stress coefficient")

    season.plot([-12, 5, 25, 32], [0, 0, 1, 1], color=P.AMBER, lw=1.7, zorder=2)
    for boundary in (5, 25):
        season.axvline(boundary, color=P.GRID, ls="--", lw=.9)
    season.scatter(temperatures, np.clip((temperatures-5)/20, 0, 1),
                   s=22, color=P.TEAL, edgecolors="white", linewidths=.5,
                   zorder=3, label="Reference monthly means")
    season.legend(loc="upper left", fontsize=8.1)
    season.set(xlim=(-12, 32), ylim=(-.05, 1.13), xticks=[-10, 5, 15, 25],
               yticks=[0, .5, 1], xlabel="Mean temperature (°C)", ylabel=r"$f(T)$")
    head(season, "b", "Temperature response")
    return fig


def milp(_inputs):
    fig, ax = sheet(1.45)
    label(ax, .5, .9, "Budget, water, labour and land limits apply to both solves",
          size=9, color=P.MUTED, ha="center")
    for x, title, detail, color in (
        (.028, "Cohort trajectories", "Water and cover from M1", P.TEAL),
        (.371, "Ecological ceiling", r"Maximise benefit $H$", P.BLUE),
        (.714, "Least-cost plans", r"Minimise $N$ at each target", P.PLUM),
    ):
        panel(ax, x, .29, .258, .42, P.LIGHT, color)
        label(ax, x+.129, .585, title, size=9.6, weight="bold", color=color, ha="center")
        label(ax, x+.129, .422, detail, size=8.5, ha="center")
    for x in (.293, .636):
        arrow(ax, (x, .50), (x+.071, .50), color=P.INK, head=8)
    label(ax, .327, .252, "Lot inputs", size=8.2, ha="center")
    label(ax, .674, .252, r"$H_{\max}$", size=8.5, ha="center")
    label(ax, .843, .118, r"Plan at $H\geq\varphi H_{\max}$", size=8.8, ha="center", color=P.PLUM)
    return fig


FIGURES = {
    "workflow_cards": workflow,
    "m1_water_feedback": water_feedback,
    "m1_root_zone": root_zone,
    "m1_stress_switches": stress_switches,
    "m2_two_stage": milp,
}

if __name__ == "__main__":
    main(FIGURES, tuple(FIGURES), ROOT / "Figures/Paper2026_Mechanisms")
