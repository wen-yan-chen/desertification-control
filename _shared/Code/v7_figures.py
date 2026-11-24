# -*- coding: utf-8 -*-
"""v7_figures.py —— 预处理报告用图（全部由 Results/v7 与 processed 数据生成）"""
from __future__ import annotations

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "Data", "v7", "processed")
RES = os.path.join(BASE, "Results", "v7")
FIG = os.path.join(BASE, "Figures", "v7_init_test")
os.makedirs(FIG, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 140
plt.rcParams["savefig.bbox"] = "tight"
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.25

CODES = ["YT", "MF", "QM", "RQ", "KEL", "YL", "ALE", "XT", "TZ"]
NAME = {"YT": "于田", "MF": "民丰", "QM": "且末", "RQ": "若羌", "KEL": "库尔勒",
        "YL": "尉犁", "ALE": "阿拉尔", "XT": "肖塘", "TZ": "塔中"}
C_MAIN, C_ACC, C_WARN = "#2b6cb0", "#dd6b20", "#c53030"


def load():
    raw = pd.read_csv(os.path.join(OUT, "panel_monthly_raw.csv"), parse_dates=["date"])
    clean = pd.read_csv(os.path.join(OUT, "panel_monthly_clean.csv"), parse_dates=["date"])
    with open(os.path.join(RES, "qc_report.json"), encoding="utf-8") as f:
        qc = json.load(f)
    return raw, clean, qc


# ---------------------------------------------------------------- 图1 缺失热图
def fig_missing(raw):
    cols = ["T2M", "T2M_MAX", "T2M_MIN", "RH2M", "WS10M", "WS10M_MAX",
            "ALLSKY_SFC_SW_DWN", "PRECTOTCORR", "GWETROOT", "GWETTOP",
            "ndvi_mvc_qa", "qa_med", "era_sm_root", "era_et0_mm", "era_P_mm"]
    labels = {"T2M": "气温", "T2M_MAX": "日最高气温", "T2M_MIN": "日最低气温",
              "RH2M": "相对湿度", "WS10M": "10m风速", "WS10M_MAX": "10m最大风速",
              "ALLSKY_SFC_SW_DWN": "短波辐射", "PRECTOTCORR": "降水",
              "GWETROOT": "根区土壤湿度", "GWETTOP": "表层土壤湿度",
              "ndvi_mvc_qa": "MODIS NDVI（QA 过滤后）", "qa_med": "MODIS QA",
              "era_sm_root": "ERA5 根区含水量", "era_et0_mm": "ERA5 ET0",
              "era_P_mm": "ERA5 降水"}
    m = raw.groupby("site")[cols].apply(lambda g: g.isna().mean() * 100).T
    m = m.loc[[c for c in cols if c in m.index], CODES]
    fig, ax = plt.subplots(figsize=(8.2, 5.4))
    im = ax.imshow(m.values, aspect="auto", cmap="OrRd", vmin=0, vmax=max(5, m.values.max()))
    ax.set_xticks(range(len(CODES)), [NAME[c] for c in CODES], rotation=0)
    ax.set_yticks(range(len(m.index)), [labels.get(c, c) for c in m.index])
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            v = m.values[i, j]
            if v > 0.05:
                ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=7,
                        color="white" if v > m.values.max() * 0.55 else "#333")
    ax.set_title("清洗前各变量缺失率（%，9 站 × 132 月）", fontsize=12)
    fig.colorbar(im, ax=ax, shrink=0.8, label="缺失率 %")
    fig.savefig(os.path.join(FIG, "fig01_缺失率热图.png"))
    plt.close(fig)


# ---------------------------------------------------------------- 图2 量纲陷阱
def fig_units(raw, clean):
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.2))
    ax = axes[0]
    x = raw["PRECTOTCORR"].dropna()
    y = (raw["PRECTOTCORR"] * raw["days_in_month"]).dropna()
    ax.scatter(x, y, s=6, alpha=0.35, color=C_MAIN)
    xs = np.linspace(0, max(2.0, x.max()), 50)
    ax.plot(xs, xs * 30.4, "--", color=C_WARN, lw=1.2, label="×30.4（月平均天数）")
    ax.set_xlabel("POWER 月产品原值（标注 mm/day）")
    ax.set_ylabel("月总量（mm/月）= 原值 × 当月天数")
    ax.set_title("(a) 降水：日均强度 ≠ 月总量", fontsize=11)
    ax.legend(fontsize=8)

    ax = axes[1]
    a = clean[["WS10M", "era_ws_max"]].dropna()
    ax.scatter(a["WS10M"], a["era_ws_max"] * 3.6, s=6, alpha=0.3, color=C_ACC,
               label="ERA5 原始交付单位 km/h")
    ax.scatter(a["WS10M"], a["era_ws_max"], s=6, alpha=0.5, color=C_MAIN,
               label="换算后 m/s")
    lim = [0, max(a["WS10M"].max(), (a["era_ws_max"] * 3.6).max()) * 1.05]
    ax.plot(lim, lim, "k--", lw=1, label="1:1")
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("NASA POWER 10 m 风速（m/s）")
    ax.set_ylabel("ERA5 10 m 风速")
    ax.set_title("(b) 风速：km/h 与 m/s 差 3.6 倍", fontsize=11)
    ax.legend(fontsize=8)
    fig.suptitle("两个最容易被忽略的量纲/聚合口径陷阱", fontsize=12)
    fig.savefig(os.path.join(FIG, "fig02_量纲陷阱.png"))
    plt.close(fig)


# ---------------------------------------------------------------- 图3 时序与质控
def fig_series(raw, clean):
    s = "YT"
    d = clean[clean["site"] == s].sort_values("date")
    r = raw[raw["site"] == s].sort_values("date")
    fig, axes = plt.subplots(3, 1, figsize=(10.2, 7.2), sharex=True)
    ax = axes[0]
    ax.plot(d["date"], d["V_pct"], color=C_MAIN, lw=1.2, label="V（QA 过滤 + 月最大合成）")
    ax.plot(r["date"], r["ndvi_mean"] * 100, ".", ms=3, color=C_ACC, alpha=0.7,
            label="未质控（NDVI×100，月均值）")
    imp = r["ndvi_mvc"].isna() | r["ndvi_mvc_qa"].isna()
    ax.plot(d.loc[imp.values, "date"], d.loc[imp.values, "V_pct"], "v", ms=7,
            color=C_WARN, label="该月 NDVI 缺测 / 全部被 QA 剔除 → 插补")
    ax.set_ylabel("植被覆盖度 V / %")
    ax.legend(fontsize=8, ncol=3)
    ax.set_title(f"{NAME[s]}站：原始序列 → 质控 → 插补（2015—2025）", fontsize=12)

    ax = axes[1]
    ax.plot(d["date"], d["W"], color="#276749", lw=1.2, label="W（GWETROOT 训练期分位归一，左轴）")
    ax.set_ylabel("W（0—1）")
    ax.set_ylim(0, 1.05)
    ax2e = ax.twinx()
    ax2e.plot(d["date"], d["E"], color=C_ACC, lw=1.0, alpha=0.8, label="侵蚀指数 E（右轴）")
    ax2e.set_ylabel("E（无量纲）")
    ax2e.grid(False)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2e.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=8, ncol=2, loc="upper left")

    ax = axes[2]
    ax.bar(d["date"], d["P_mm"], width=25, color="#4299e1", label="月降水（POWER，mm/月）")
    ax.set_ylabel("降水 / mm")
    ax2 = ax.twinx()
    ax2.plot(d["date"], d["WS10M_MAX"], color=C_WARN, lw=0.9, alpha=0.8, label="10m 最大风速")
    ax2.set_ylabel("风速 / (m/s)")
    ax2.grid(False)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=8, ncol=2, loc="upper left")
    fig.savefig(os.path.join(FIG, "fig03_时序与质控.png"))
    plt.close(fig)


# ---------------------------------------------------------------- 图4 异常值
def fig_outlier(clean):
    cols = [("WS10M_MAX", "10m 最大风速 / (m/s)"), ("P_mm", "月降水 / mm"),
            ("GWETROOT", "根区土壤湿度（0-1）"), ("V_pct", "植被覆盖度 / %")]
    fig, axes = plt.subplots(1, 4, figsize=(12.4, 4.0))
    for ax, (c, lab) in zip(axes, cols):
        data = [clean.loc[clean["site"] == s, c].dropna().values for s in CODES]
        bp = ax.boxplot(data, tick_labels=[NAME[s] for s in CODES], patch_artist=True,
                        showfliers=True, flierprops=dict(marker="o", ms=2.5, alpha=0.5,
                                                         markerfacecolor=C_WARN,
                                                         markeredgecolor="none"))
        for b in bp["boxes"]:
            b.set(facecolor="#bee3f8", edgecolor=C_MAIN, lw=0.8)
        ax.set_title(lab, fontsize=9.5)
        ax.tick_params(axis="x", rotation=45, labelsize=7.0)
    fig.suptitle("关键变量的站间分布与极端值（红点为稳健 z > 3.5 的候选异常，只标记不删除）",
                 fontsize=11)
    fig.savefig(os.path.join(FIG, "fig04_异常与极端值.png"))
    plt.close(fig)


# ---------------------------------------------------------------- 图5 跨源一致性
def fig_cross(clean, qc):
    pairs = [("T2M", "era_T", "气温 / °C", "r"),
             ("P_mm", "era_P_mm", "月降水 / mm", "r"),
             ("GWETROOT", "era_sm_root", "根区水分（0—1 vs m³/m³）", "r"),
             ("ET0_hargreaves", "era_et0_mm", "参考蒸散 / mm", "r")]
    xlabs = ["ERA5 气温 / °C", "ERA5 月降水 / mm", "ERA5 根区含水量 / (m³/m³)", "ERA5 ET0 / mm"]
    ylabs = ["POWER 气温 / °C", "POWER 月降水 / mm", "POWER GWETROOT（0—1 饱和度）", "Hargreaves ET0 / mm"]
    fig, axes = plt.subplots(2, 2, figsize=(9.6, 7.2))
    for k, (ax, (a, b, lab, _)) in enumerate(zip(axes.ravel(), pairs)):
        d = clean[[a, b]].dropna()
        ax.scatter(d[b], d[a], s=5, alpha=0.3, color=C_MAIN)
        lo = min(d[a].min(), d[b].min()); hi = max(d[a].max(), d[b].max())
        ax.plot([lo, hi], [lo, hi], "--", color=C_WARN, lw=1)
        rr = float(np.corrcoef(d[a], d[b])[0, 1])
        ax.set_title(f"{lab}    r = {rr:.2f} (n={len(d)})", fontsize=9)
        ax.set_xlabel(xlabs[k])
        ax.set_ylabel(ylabs[k])
    fig.suptitle("两个独立来源的交叉核验（全部站点逐月合并；虚线为 1:1；土壤湿度量纲不同，只看相关性）",
                 fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(os.path.join(FIG, "fig05_跨源一致性.png"))
    plt.close(fig)


# ---------------------------------------------------------------- 图6 共线性
def fig_collinear(clean):
    cols = ["W", "E", "T2M", "P_mm", "AI", "WS10M", "RH2M", "SW_MJ"]
    d = clean[cols].dropna()
    C = d.corr().values
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.4),
                             gridspec_kw={"width_ratios": [1.15, 1]})
    ax = axes[0]
    im = ax.imshow(C, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(cols)), cols, rotation=45, ha="right")
    ax.set_yticks(range(len(cols)), cols)
    for i in range(len(cols)):
        for j in range(len(cols)):
            ax.text(j, i, f"{C[i, j]:.2f}", ha="center", va="center", fontsize=6.5,
                    color="white" if abs(C[i, j]) > 0.6 else "#333")
    ax.set_title("(a) Pearson 相关矩阵", fontsize=10)
    fig.colorbar(im, ax=ax, shrink=0.8)
    ax.grid(False)

    ax = axes[1]
    vif = []
    for i, c in enumerate(cols):
        X = np.delete(C[i], i)
        R = np.delete(np.delete(C, i, axis=0), i, axis=1)
        beta = np.linalg.solve(R, X)
        r2 = float(X @ beta)
        vif.append(1 / max(1 - r2, 1e-6))
    order = np.argsort(vif)
    ax.barh([cols[i] for i in order], [vif[i] for i in order], color=C_ACC, alpha=0.85)
    ax.axvline(10, color=C_WARN, ls="--", lw=1, label="VIF = 10")
    ax.axvline(5, color="#718096", ls=":", lw=1, label="VIF = 5")
    ax.set_xlabel("方差膨胀因子 VIF")
    ax.set_title("(b) 共线性诊断", fontsize=10)
    ax.legend(fontsize=8)
    fig.suptitle("派生特征的相关性与共线性（用于决定进入模型的变量集）", fontsize=11)
    fig.savefig(os.path.join(FIG, "fig06_相关与共线性.png"))
    plt.close(fig)


# ---------------------------------------------------------------- 图7 消融
def fig_ablation():
    p = os.path.join(RES, "tab_ablation_summary.csv")
    d = pd.read_csv(p)
    labels = {"P0": "P0\n原始直用", "P1": "P1\n+量纲", "P2": "P2\n+插补",
              "P3": "P3\n+质控", "P4": "P4\n+训练隔离"}
    x = np.arange(len(d))
    fig, axes = plt.subplots(2, 2, figsize=(10.4, 6.6))
    specs = [("R2_train_median", "(a) 任务一：训练期 R² 中位数", C_MAIN),
             ("RMSE_one_year_median", "(b) 任务一：一年外推 RMSE（覆盖度百分点）", C_WARN),
             ("NPV_median", "(c) 任务二：基准情景 NPV（万元）", "#276749"),
             ("Pdeg_median", "(d) 任务三：30 年退化概率（λ=0.3）", "#6b46c1")]
    for ax, (c, title, col) in zip(axes.ravel(), specs):
        vals = d[c].values
        bars = ax.bar(x, vals, color=col, alpha=0.85)
        ax.set_xticks(x, [labels[k] for k in d["pipeline"]], rotation=0, fontsize=7.8)
        ax.set_title(title, fontsize=10)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.3f}" if abs(v) < 10 else f"{v:.0f}",
                    ha="center", va="bottom", fontsize=7.5)
        ax.axhline(0, color="k", lw=0.6)
    fig.suptitle("预处理方案消融：同一份原始数据、五种处理方式对三问结果的影响",
                 fontsize=11.5)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig07_消融影响.png"))
    plt.close(fig)


def main():
    raw, clean, qc = load()
    print("绘制图1 缺失率热图 ...", flush=True); fig_missing(raw)
    print("绘制图2 量纲陷阱 ...", flush=True); fig_units(raw, clean)
    print("绘制图3 时序与质控 ...", flush=True); fig_series(raw, clean)
    print("绘制图4 异常与极端值 ...", flush=True); fig_outlier(clean)
    print("绘制图5 跨源一致性 ...", flush=True); fig_cross(clean, qc)
    print("绘制图6 相关与共线性 ...", flush=True); fig_collinear(clean)
    if os.path.exists(os.path.join(RES, "tab_ablation_summary.csv")):
        print("绘制图7 消融 ...", flush=True); fig_ablation()
    print("全部图件已写入 Figures/v7_init_test", flush=True)


if __name__ == "__main__":
    main()








