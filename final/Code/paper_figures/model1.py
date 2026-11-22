"""Study location, out-of-time checks and the water/cover scenario response."""

import math

import matplotlib.patheffects as pe
from matplotlib.ticker import MultipleLocator
import numpy as np
import pandas as pd
from PIL import Image, ImageEnhance

from style import (
    AMBER, BLUE, DATA, INK, MONTHS, MUTED, PLUM, RESULTS, TEAL, csv, grid, head,
    panels, read_json,
)


CATEGORIES = {
    "YT": "Margin", "MF": "Margin", "QM": "Margin", "RQ": "Margin",
    "ALE": "Margin", "KEL": "Margin", "YL": "Margin",
    "XT": "Corridor", "TZ": "Desert interior",
}
SITE_STYLES = {"Margin": (TEAL, "o"), "Corridor": (AMBER, "^"),
               "Desert interior": (PLUM, "s")}


def mercator(lat):
    return np.degrees(np.arcsinh(np.tan(np.radians(lat))))


def basemap(extent):
    left, right, bottom, top = extent
    x0, x1 = (np.array([left, right]) + 180) / 360 * 128
    y0, y1 = (180 - mercator([top, bottom])) / 360 * 128
    a, b, c, d = map(math.floor, (x0, x1, y0, y1))
    mosaic = Image.new("RGB", ((b - a + 1) * 256, (d - c + 1) * 256))
    for i in range(a, b + 1):
        for j in range(c, d + 1):
            with Image.open(DATA / f"raw/basemap_tiles/7_{i}_{j}.jpg") as tile:
                mosaic.paste(tile, ((i - a) * 256, (j - c) * 256))
    crop = tuple(round((frac - origin) * 256)
                 for frac, origin in zip((x0, y0, x1, y1), (a, c, a, c)))
    return ImageEnhance.Color(mosaic.crop(crop)).enhance(.72)


def study_area():
    meta = read_json(DATA / "raw/manifest.json")
    section = read_json(DATA / "m1_audited/section_definition.json")
    frame = pd.read_csv(DATA / "m1_audited/panel_m1.csv", parse_dates=["date"])
    years = frame.loc[frame.date.dt.month.between(6, 9)].groupby(
        ["site", frame.date.dt.year]
    )["V_pct"].agg(["count", "mean"])
    covers = years.loc[years["count"].ge(2), "mean"].groupby(level="site").agg(["mean", "std"])
    fig, axes = panels(4.15, 1, 2, width_ratios=[1.78, 1])
    ax, stat = axes[0]
    extent = (80, 89.5, 36.0, 42.55)
    left, right, bottom, top = extent
    ax.imshow(basemap(extent), extent=(left, right, mercator(bottom), mercator(top)),
              interpolation="bilinear")
    ax.set(xlim=(left, right), ylim=(mercator(bottom), mercator(top)),
           xticks=[81, 83, 85, 87, 89], xticklabels=[f"{n}°E" for n in [81, 83, 85, 87, 89]],
           yticks=mercator([37, 39, 41]), yticklabels=["37°N", "39°N", "41°N"])
    ax.grid(color="white", alpha=.22, linewidth=.5)
    outline = [pe.withStroke(linewidth=2.6, foreground=INK)]
    path = section["centerline"]
    ax.plot([p["lon"] for p in path], mercator([p["lat"] for p in path]),
            color="#FFE391", ls=(0, (4, 2)), lw=2.0, path_effects=outline,
            label="Study transect", zorder=4)
    offsets = {"KEL": (-22, 6), "YL": (6, -7), "ALE": (-20, 7), "YT": (-4, -13),
               "MF": (7, 5), "QM": (6, -5), "RQ": (6, 3), "XT": (7, -5), "TZ": (-17, 6)}
    shown = set()
    for s in meta["sites"]:
        code = s["code"]
        category = CATEGORIES[code]
        color, marker = SITE_STYLES[category]
        x, y = s["lon"], mercator(s["lat"])
        ax.scatter(x, y, c=color, marker=marker, s=50, edgecolor="white",
                   linewidth=1.05, zorder=5, label=category if category not in shown else None)
        shown.add(category)
        ax.annotate(code, (x, y), xytext=offsets[code], textcoords="offset points",
                    color="white", weight="bold", path_effects=outline, zorder=6)
    ax.annotate("N", (.95, .96), xycoords="axes fraction", ha="center",
                va="top", color="white", weight="bold", path_effects=outline)
    ax.annotate("", (.95, .88), (.95, .79), xycoords="axes fraction",
                arrowprops={"arrowstyle": "-|>", "color": "white", "lw": 1.2})
    lat = 36.46
    lon = 87.25
    length = np.degrees(2 * np.arcsin(np.sin(100 / (2 * 6371.0088)) / np.cos(np.radians(lat))))
    ax.plot([lon, lon+length], [mercator(lat)]*2, color="white", lw=2, path_effects=outline)
    ax.text(lon+length/2, mercator(lat)+.19, "100 km", color="white", ha="center",
            path_effects=outline, fontsize=8.3)
    ax.text(.015, .028, "Esri World Imagery", transform=ax.transAxes, color="white",
            fontsize=8.1, path_effects=outline)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=4,
               columnspacing=1.2, handlelength=1.5)
    head(ax, "a", "Stations and Yutian–Minfeng study transect")
    order = ["YT", "MF", "QM", "RQ", "ALE", "KEL", "YL", "XT", "TZ"]
    stat.axhspan(-.45, 1.45, color="#E4F3EF", lw=0, zorder=0)
    for i, code in enumerate(order):
        color, marker = SITE_STYLES[CATEGORIES[code]]
        mean, sd = covers.loc[code]
        stat.errorbar(mean, i, xerr=sd, fmt=marker, color=color, capsize=2.5, zorder=3)
    stat.set(ylim=(8.6, -.6), xlim=(0, 50), yticks=range(9), yticklabels=order,
             xticks=[0, 10, 20, 30, 40, 50], xlabel="Cover proxy (%)")
    stat.text(2.5, .51, "Reference pair", color=TEAL, va="center", fontsize=8.3)
    grid(stat, "x")
    head(stat, "b", "Summer cover, 2015–2025")
    return fig


def validation():
    pairs = csv("model1", "prediction_pairs").query("split == 'test'")
    metrics = csv("model1", "holdout_by_site").sort_values("persistence_rmse")
    annual = csv("model1", "yearly_table")
    free = csv("model1", "free_running_holdout")
    fig, ax = panels(4.45, 2, 3, height_ratios=[1.25, 1.0])
    spec = ax[0, 0].get_gridspec()
    for old in ax[0]:
        old.remove()
    score = fig.add_subplot(spec[0, :])
    yi = np.arange(len(metrics))
    score.axhspan(-.5, 6.5, color="white", zorder=0)
    for y, row in zip(yi, metrics.itertuples()):
        color = TEAL if row.site in {"YT", "MF"} else "#A0ABAF"
        score.hlines(y, row.persistence_rmse, row.rmse, color=color, lw=1.7, zorder=2)
    score.scatter(metrics.persistence_rmse, yi, c="white", edgecolor=MUTED, zorder=3,
                  s=35, linewidths=1.2, label="Persistence")
    score.scatter(metrics.rmse, yi, c=BLUE, marker="D", zorder=4, s=24, label="M1 one-step")
    e_model = np.sqrt(np.mean((pairs.observed_x - pairs.predicted_x) ** 2))
    e_persist = np.sqrt(np.mean((pairs.observed_x - pairs.persistence_x) ** 2))
    score.set(xlim=(.015, .125), ylim=(6.55, -.55), yticks=yi, yticklabels=metrics.site,
              xlabel="$V/K$ RMSE (lower is better)")
    score.xaxis.set_major_locator(MultipleLocator(.02))
    for tick in score.get_yticklabels():
        if tick.get_text() in {"YT", "MF"}:
            tick.set_color(TEAL)
            tick.set_weight("bold")
    score.legend(loc="upper right")
    score.text(.096, 4.35, f"Pooled, $n={len(pairs)}$\nM1   {e_model:.4f}\nPersistence   {e_persist:.4f}",
               color=INK, va="center", linespacing=1.30)
    grid(score, "x")
    head(score, "a", "One-step errors in the 2023–2025 holdout")
    for i, (sub, site) in enumerate(zip(ax[1], ("YT", "MF", "RQ"))):
        hist = annual[(annual.site.eq(site)) & annual.year.between(2022, 2025)]
        sim = free[free.site.eq(site)]
        sub.axvspan(2022.5, 2025.27, color="#F4F0E8", lw=0)
        sub.plot(hist.year, hist.V, "o-", color=INK, label="Observed")
        sub.plot(hist.year, [hist.V.iloc[0], *sim.predicted_pct], "^--", color=AMBER, label="M1 free run")
        sub.set(xlim=(2021.82, 2025.27), ylim=(21, 44), xticks=[2022, 2023, 2024, 2025],
                xticklabels=["2022", "2023", "2024", "2025"], yticks=[25, 30, 35, 40])
        sub.tick_params(labelleft=i == 0)
        if i == 0:
            sub.set_ylabel("Cover proxy (%)")
        if i == 2:
            sub.legend(loc="lower right", handlelength=1.5)
        grid(sub)
        head(sub, "bcd"[i], {"YT": "Yutian", "MF": "Minfeng", "RQ": "Ruoqiang"}[site])
    return fig


def irrigation():
    curve = csv("model1", "water_cover_curve")
    annual = csv("model1", "scenario_annual")
    reference = read_json(RESULTS / "model1/model1_results.json")["adopted_parameters"]
    ceiling = reference["K_section_pct"] * (1 - reference["d"] / reference["r"])
    capacity = reference["water"]["capacity_mm"]
    fig, ax = panels(4.35, 2, 2)
    colors = (AMBER, TEAL, BLUE, PLUM)
    scenarios = [("I0", "Rain only", "-"), ("I300", "300 mm/yr", "--"),
                 ("I600", "600 mm/yr", "-"), ("stop_after_10", "600 then stop", "-.")]
    variables = [("V_steady_pct", "V_end_pct", "V_start_pct", "Cover proxy (%)", (0, 34)),
                 ("M_periodic_end_mm", "M_end_mm", "M_start_mm", "Available water (mm)", (0, 81))]
    for i, (steady, end, start, label, limits) in enumerate(variables):
        left, right = ax[i]
        left.plot(curve.irrigation_mm_yr, curve[steady], "o-", color=TEAL, lw=1.5, ms=3.7)
        left.axhline((ceiling, capacity)[i], ls="--", lw=.95, color=MUTED)
        left.text(1990, (ceiling, capacity)[i]+.035*(limits[1]),
                  ("Water-unlimited cover", "Storage capacity")[i], ha="right", color=MUTED, fontsize=8.4)
        for (key, name, ls), color in zip(scenarios, colors):
            subset = annual.loc[annual.scenario.eq(key)]
            right.plot(np.r_[2025, subset.calendar_year], np.r_[subset[start].iat[0], subset[end]],
                       ls=ls, color=color, label=name)
        right.axvline(2035, color=PLUM, alpha=.5, ls=":", lw=1)
        left.set(xlim=(-55, 2070), xticks=[0, 500, 1000, 1500, 2000], ylabel=label, ylim=limits)
        right.set(xlim=(2024.7, 2050.5), xticks=[2025, 2035, 2045, 2050], ylim=limits)
        for a in (left, right):
            grid(a)
        if i == 1:
            left.set_xlabel("Irrigation (mm/yr)")
            right.set_xlabel("Year end")
    handles, labels = ax[0, 1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncols=4)
    head(ax[0, 0], "a", "Long-run cover response")
    head(ax[0, 1], "b", "Cover after planting")
    head(ax[1, 0], "c", "Long-run year-end storage")
    head(ax[1, 1], "d", "Storage after planting")
    return fig


def drivers():
    forcing = csv("model1", "section_forcing_climatology")
    sens = csv("model1", "sensitivity")
    baseline = csv("model1", "water_cover_curve").set_index("irrigation_mm_yr")
    wind = csv("model1", "wind_channel")
    fig, ax = panels(4.80, 2, 2, height_ratios=[.9, 1.1])
    season, wind_plot = ax[0]
    season.plot(forcing.month, forcing.ET0_mm, "o--", color=MUTED, label=r"Reference $ET_0$")
    season.plot(forcing.month, forcing.ET0g_mm, "s-", color=BLUE, label="Temperature-scaled")
    season.fill_between(forcing.month, forcing.ET0g_mm, forcing.ET0_mm, color=BLUE, alpha=.08)
    season.set(xticks=[1, 3, 5, 7, 9, 11], xticklabels=MONTHS[:12:2], ylabel="Demand index (mm/month)",
               ylim=(0, 320))
    season.legend(loc="upper left", handlelength=1.25, borderaxespad=.35)
    head(season, "a", "Seasonal atmospheric demand")
    for quota, color, ls, marker in zip([300, 600], [TEAL, BLUE], ["-", "--"], ["o", "s"]):
        frame = wind[wind.irrigation_mm_yr.eq(quota)]
        wind_plot.plot((frame.wind_speed_scale-1)*100, frame.V_steady_pct, marker=marker,
                       ls=ls, color=color, label=f"{quota} mm/yr")
    wind_plot.axvline(0, color=MUTED, lw=.9, ls=":")
    wind_plot.set(xlabel="Change in wind speed (%)", ylabel="Long-run cover (%)",
                  xticks=[-20, -10, 0, 10, 20], ylim=(15, 27))
    wind_plot.legend(loc="center right", handlelength=1.6)
    head(wind_plot, "b", "Wind acts through demand")
    tested = [("c", "Demand coefficient [0.70, 1.20]"), ("eta_w", "Irrigation efficiency [0.65, 0.85]"),
              ("rain_fraction", "Effective rain [0, 1]"), ("v_full_pct", "Cover scaling [64.85, 69.4]"),
              ("capacity_mm", "Storage capacity [30, 150 mm]"),
              ("depletion_fraction", "Stress fraction [0.30, 0.70]")]
    for i, (chart, quota, color) in enumerate(zip(ax[1], [300, 600], [TEAL, BLUE])):
        for y, (parameter, label) in enumerate(tested):
            endpoints = sens[(sens.parameter.eq(parameter)) & sens.irrigation_mm_yr.eq(quota)].sort_values("value")
            low, high = endpoints.V_pct.to_numpy() - baseline.loc[quota, "V_steady_pct"]
            chart.hlines(y, low, high, color=color, lw=2, alpha=.75)
            chart.scatter(low, y, facecolor="white", edgecolor=color, marker="o", s=27, zorder=3)
            chart.scatter(high, y, c=color, marker="|", s=74, linewidth=1.5, zorder=4)
        chart.axvline(0, color=MUTED, lw=.8)
        chart.set(xlim=(-2.05, 3.85), ylim=(5.55, -.7), yticks=range(6),
                  yticklabels=[label for _, label in tested], xticks=[-2, 0, 2],
                  xlabel="Change in cover (pp)")
        chart.tick_params(axis="y", labelleft=i == 0, length=0)
        grid(chart, "x")
        head(chart, "cd"[i], f"One-at-a-time at {quota} mm/yr")
    ax[1, 1].scatter([], [], facecolor="white", edgecolor=MUTED, label="Lower input", s=27)
    ax[1, 1].scatter([], [], c=MUTED, marker="|", label="Upper input", s=74, linewidth=1.5)
    ax[1, 1].legend(loc="lower right", handletextpad=.25)
    grid(season)
    grid(wind_plot)
    return fig
