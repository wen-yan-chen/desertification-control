# -*- coding: utf-8 -*-
"""v7_fig_pre.py —— 《数据预处理》专用图：缺失图谱与插补方法对比"""
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
MN = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]
C1, C2 = "#2b6cb0", "#dd6b20"


def fig_pattern(miss: dict):
    p = pd.read_csv(os.path.join(OUT, "panel_monthly_raw.csv"), parse_dates=["date"])
    p["missing"] = p["ndvi_mvc_qa"].isna()
    p["month"] = p["date"].dt.month
    tab = p.pivot_table(index="site", columns="month", values="missing", aggfunc="sum")
    tab = tab.reindex(CODES).fillna(0)

    fig = plt.figure(figsize=(10.4, 6.6))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.15, 1], height_ratios=[1, 1])
    ax = fig.add_subplot(gs[0, :])
    im = ax.imshow(tab.values, aspect="auto", cmap="OrRd", vmin=0, vmax=max(1, tab.values.max()))
    ax.set_xticks(range(12), MN)
    ax.set_yticks(range(len(CODES)), [NAME[c] for c in CODES])
    for i in range(tab.shape[0]):
        for j in range(tab.shape[1]):
            v = int(tab.values[i, j])
            if v:
                ax.text(j, i, str(v), ha="center", va="center", fontsize=7.5,
                        color="white" if v >= tab.values.max() * 0.6 else "#333")
    ax.set_title("(a) 缺失月份分布：站点 × 日历月（数字为缺失年数，最多 11）", fontsize=10)
    ax.grid(False)
    fig.colorbar(im, ax=ax, shrink=0.85, pad=0.01)

    ax = fig.add_subplot(gs[1, 0])
    bm = miss["by_calendar_month"]
    vals = [bm[str(m)]["pct"] for m in range(1, 13)]
    bars = ax.bar(MN, vals, color=[C2 if v > 10 else C1 for v in vals], alpha=0.85)
    for b, v in zip(bars, vals):
        if v > 0:
            ax.text(b.get_x() + b.get_width() / 2, v + 0.4, f"{v:.0f}", ha="center", fontsize=7.5)
    ax.set_ylabel("缺失率 / %")
    ax.set_title("(b) 缺失率按日历月：冬季高、夏季为零", fontsize=10)
    ax.tick_params(axis="x", labelsize=7.5)

    ax = fig.add_subplot(gs[1, 1])
    rd = {int(k): v for k, v in miss["run_length_dist"].items()}
    ks = sorted(rd)
    ax.bar([str(k) for k in ks], [rd[k] for k in ks], color=C1, alpha=0.85)
    for i, k in enumerate(ks):
        ax.text(i, rd[k] + 0.5, str(rd[k]), ha="center", fontsize=7.5)
    ax.set_xlabel("连续缺失长度（月）")
    ax.set_ylabel("出现次数")
    ax.set_title("(c) 连续缺失长度分布（共 65 段）", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig08_缺失模式.png"))
    plt.close(fig)


def fig_impute():
    d = pd.read_csv(os.path.join(RES, "tab_impute_compare.csv"))
    labs = {"mean": "均值", "median": "中位数", "linear": "线性插值",
            "clim": "同月气候态", "persistence": "去年同期"}
    order = ["mean", "median", "linear", "clim", "persistence"]
    x = np.arange(len(order))
    w = 0.38
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 3.9))
    for ax, sch, ttl in ((axes[0], "MCAR_10pct", "(a) 随机缺失 10%"),
                         (axes[1], "dust_10pct", "(b) 沙尘型缺失 10%")):
        sub = d[d.scheme == sch].set_index("method").reindex(order)
        b1 = ax.bar(x - w / 2, sub["RMSE_pp"], w, label="RMSE", color=C1, alpha=0.9)
        b2 = ax.bar(x + w / 2, sub["MAE_pp"], w, label="MAE", color=C2, alpha=0.9)
        for bs in (b1, b2):
            for b in bs:
                ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.12,
                        f"{b.get_height():.2f}", ha="center", fontsize=7)
        ax.set_xticks(x, [labs[k] for k in order], fontsize=8)
        ax.set_ylabel("误差 / 覆盖度百分点")
        ax.set_title(ttl, fontsize=10)
        ax.legend(fontsize=8)
    fig.suptitle("五种插补方法的还原误差（参照序列：未质控的月最大合成反演覆盖度）", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(os.path.join(FIG, "fig09_插补方法对比.png"))
    plt.close(fig)


if __name__ == "__main__":
    miss = json.load(open(os.path.join(RES, "missing.json"), encoding="utf-8"))
    fig_pattern(miss)
    fig_impute()
    print("fig08 / fig09 已生成")
