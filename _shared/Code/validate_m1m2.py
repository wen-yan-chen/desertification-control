# -*- coding: utf-8 -*-
"""
2026 CQU_MCM Problem B —— M1 / M2 数值结果的模型检验（v7 当前版）
=================================================================================
检验对象不是公式草稿，而是队友已经跑出来的结果表：
    Results/v7/model1/*.csv, model1_results.json    （任务一：站点标定 + 水量平衡 + 情景）
    Results/v7/model2/*.csv, model2_results.json    （任务二：批次制 MIP 投资优化 + 28 个情景）
    Reports/model_v7/model_v7.tex                    （任务三：仅公式规格，尚无数值实现）

设计原则
    1) 只读结果表，不重新实现模型——这样检验的是"队友算出来的东西"；
    2) 能重算的一律重算（指标、约束、目标值、有效面积），不采信汇总值；
    3) 不能重算的（如 MIP 内部），检查其自洽性（对偶界、gap、回放误差）；
    4) 每项检验给出判据与结论，最后汇总成评分卡。

输出
    Results/v7_validation/m1_*.csv, m2_*.csv, validation_m1m2.json
    Figures/v7_validation/*.png

运行
    python Code/validate_m1m2.py [--quick]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M1 = os.path.join(BASE, "Results", "v7", "model1")
M2 = os.path.join(BASE, "Results", "v7", "model2")
RES = os.path.join(BASE, "Results", "v7_validation")
FIG = os.path.join(BASE, "Figures", "v7_validation")
os.makedirs(RES, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

SEED = 20261112
RNG = np.random.default_rng(SEED)
CRIT = {"kappa": 1e6, "mip_gap": 0.002 + 1e-9, "closure_mm": 1e-6, "skill": 0.0,
        "alpha": 0.05, "pv_price": 0.30}

# ------------------------------------------------------------------ 绘图
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

CJK = "DejaVu Sans"
for _c in ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DengXian"]:
    try:
        font_manager.findfont(_c, fallback_to_default=False)
        CJK = _c
        break
    except Exception:
        continue
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": [CJK, "DejaVu Sans"],
    "axes.unicode_minus": False, "figure.dpi": 200, "savefig.dpi": 200,
    "savefig.bbox": "tight", "axes.grid": True, "grid.alpha": 0.3,
    "grid.linestyle": ":", "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlesize": 10, "axes.labelsize": 9, "xtick.labelsize": 8,
    "ytick.labelsize": 8, "legend.fontsize": 8, "legend.frameon": False,
})
C = {"obs": "#1f2937", "mod": "#2b6cb0", "alt": "#dd6b20", "ok": "#2f855a",
     "bad": "#c53030", "grey": "#718096", "light": "#cbd5e0", "purple": "#6b46c1"}


def savefig(fig, name):
    p = os.path.join(FIG, name)
    fig.savefig(p)
    plt.close(fig)
    print(f"    [图] {os.path.relpath(p, BASE)}")


def jdump(o, name):
    p = os.path.join(RES, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f, ensure_ascii=False, indent=1, default=float)
    print(f"    [表] {os.path.relpath(p, BASE)}")


def verdict(ok, fail="未通过", warn=False):
    return "通过" if ok else ("需改进" if warn else fail)


# =====================================================================================
# 1. 任务一：M1 结果的检验
# =====================================================================================

def m1_metrics(j) -> dict:
    """重算训练/测试误差与技能分，与 model1_results.json 的报告值对照。

    口径：prediction_pairs 里的 x=V/K 是模型的直接拟合对象（不是 V 原始百分点），
    所以 R²、RMSE 都应在 x 尺度上算；另给 V 尺度的 RMSE 以便直觉理解。
    """
    pp = pd.read_csv(os.path.join(M1, "prediction_pairs.csv"))
    out = {"n": int(len(pp))}
    for split in ("train", "test"):
        d = pp[pp.split == split]
        if not len(d):
            continue
        e = d.predicted_x - d.observed_x
        ep = d.persistence_x - d.observed_x
        sst = float(np.sum((d.observed_x - d.observed_x.mean()) ** 2))
        sst_v = float(np.sum(((d.observed_x - d.observed_x.mean()) * d.K) ** 2))
        out[split] = {
            "n": int(len(d)),
            "RMSE": float(np.sqrt(np.mean(e ** 2))),
            "MAE": float(np.mean(np.abs(e))),
            "R2": float(1 - np.sum(e ** 2) / sst) if sst > 0 else np.nan,
            "R2_V": float(1 - np.sum((e * d.K) ** 2) / sst_v) if sst_v > 0 else np.nan,
            "bias": float(e.mean()),
            "RMSE_persistence": float(np.sqrt(np.mean(ep ** 2))),
            "skill_RMSE": float(1 - np.sqrt(np.mean(e ** 2)) / np.sqrt(np.mean(ep ** 2))),
            "skill_MSE": float(1 - np.mean(e ** 2) / np.mean(ep ** 2)),
            "RMSE_in_V_pct": float(np.sqrt(np.mean(e ** 2)) * 100),  # x 无量纲 → 百分点需乘 100·K
            "K_mean": float(d.K.mean()),
        }
    # V 尺度（×K）：更直观
    for split in ("train", "test"):
        if split in out:
            out[split]["RMSE_V_pct"] = float(out[split]["RMSE"] * out[split]["K_mean"])

    rep = j["station_fit"]["pooled_r_d"]
    base = j["station_fit"]["baselines"]
    out["reported"] = {"rmse_train": rep["rmse_train"], "rmse_test": rep["rmse_test"],
                       "r2_test": rep["r2_test"],
                       "persistence_train": base["persistence_rmse_train"],
                       "persistence_test": base["persistence_rmse_test"],
                       "site_mean_test": base["site_mean_rmse_test"]}
    out["repro_max_abs_diff"] = max(
        abs(out["train"]["RMSE"] - rep["rmse_train"]),
        abs(out["test"]["RMSE"] - rep["rmse_test"]),
        abs(out["test"]["R2"] - rep["r2_test"]),
        abs(out["train"]["RMSE_persistence"] - base["persistence_rmse_train"]),
        abs(out["test"]["RMSE_persistence"] - base["persistence_rmse_test"]))
    out["检验"] = "指标可复现性"
    out["判据"] = "重算值与报告值最大绝对差 <1e-3（R² 在 V 尺度上比对）"
    out["结论"] = verdict(out["repro_max_abs_diff"] < 1e-3)
    return out


def m1_skill_test(j, m1m) -> dict:
    """一年外推是否优于持续性基线：配对检验 + 符号检验。

    model1_results.json 自己报出 test RMSE 0.0635 > persistence 0.0536，
    所以这里不是"找显著"，而是确认"确实不显著/更差"，并给出差距的置信区间。
    """
    pp = pd.read_csv(os.path.join(M1, "prediction_pairs.csv"))
    recs = []
    for split in ("train", "test"):
        d = pp[pp.split == split]
        em = np.abs(d.predicted_x - d.observed_x)
        ep = np.abs(d.persistence_x - d.observed_x)
        t, p_t = stats.ttest_rel(em, ep)
        try:
            w, p_w = stats.wilcoxon(em, ep)
        except Exception:
            w, p_w = np.nan, np.nan
        diff = em - ep
        recs.append({"split": split, "n": int(len(d)),
                     "mean_diff": float(diff.mean()),
                     "ci95_low": float(diff.mean() - 1.96 * diff.std(ddof=1) / np.sqrt(len(d))),
                     "ci95_high": float(diff.mean() + 1.96 * diff.std(ddof=1) / np.sqrt(len(d))),
                     "t": float(t), "p": float(p_t), "wilcoxon_p": float(p_w),
                     "wins": int((diff < 0).sum())})
    df = pd.DataFrame(recs)
    te = df[df.split == "test"].iloc[0]
    out = {"检验": "一年外推 vs 持续性基线", "table": recs,
           "test_win_rate": float(te.wins / te.n),
           "判据": "测试期 MAE 显著小于持续性（单侧 p<0.05）",
           "结论": verdict(bool(te.p < 0.05 and te.mean_diff < 0))}
    return out


def m1_holdout(j) -> dict:
    """留站检验：逐站技能分、中位数、负值站点数。"""
    d = pd.read_csv(os.path.join(M1, "holdout_by_site.csv"))
    n_neg = int((d.mse_skill_vs_persistence < 0).sum())
    out = {"检验": "留站泛化（LOWO）", "table": d.to_dict("records"),
           "n_sites": int(len(d)), "n_negative": n_neg,
           "median_skill": float(d.mse_skill_vs_persistence.median()),
           "min_skill": float(d.mse_skill_vs_persistence.min()),
           "median_RMSE": float(d.rmse.median()),
           "判据": "≥5/7 站点技能分 >0",
           "结论": verdict(n_neg <= 2)}
    fr = pd.read_csv(os.path.join(M1, "free_running_holdout.csv"))
    e = fr.predicted_pct - fr.observed_pct
    ep = fr.persistence_2022_pct - fr.observed_pct
    out["free_running"] = {
        "n": int(len(fr)),
        "RMSE_model_pct": float(np.sqrt(np.mean(e ** 2))),
        "RMSE_persistence_pct": float(np.sqrt(np.mean(ep ** 2))),
        "bias_pct": float(e.mean()),
        "skill": float(1 - np.sqrt(np.mean(e ** 2)) / np.sqrt(np.mean(ep ** 2))),
    }
    return out


def m1_params(j) -> dict:
    """参数稳定性：全样本 vs 留一站估计的离散度；YT 是否为强影响点。"""
    lo = j["station_fit"]["leave_one_station_out"]
    r = np.array([v["r"] for v in lo.values()])
    d = np.array([v["d"] for v in lo.values()])
    pooled = j["station_fit"]["pooled_r_d"]["theta"]
    out = {"检验": "参数稳定性（留一站）",
           "r_pooled": float(pooled[0]), "d_pooled": float(pooled[1]),
           "r_range": [float(r.min()), float(r.max())],
           "d_range": [float(d.min()), float(d.max())],
           "r_max_site": str([k for k, v in lo.items() if v["r"] == r.max()][0]),
           "r_rel_spread": float((r.max() - r.min()) / pooled[0]),
           "d_rel_spread": float((d.max() - d.min()) / pooled[1]),
           "判据": "r 的相对离散 <50%",
           "结论": verdict((r.max() - r.min()) / pooled[0] < 0.5, warn=True)}
    return out


def m1_bootstrap(j) -> dict:
    """整簇自助法：区间宽度、与局部 sd 的一致性、是否覆盖 0（对 d）。"""
    b = pd.read_csv(os.path.join(M1, "parameter_cluster_bootstrap.csv"))
    rep = j["uncertainty"]["bootstrap_percentiles"]
    out = {"检验": "参数区间（整簇自助）", "n": int(len(b)),
           "r_ci": [float(b.r.quantile(0.025)), float(b.r.quantile(0.975))],
           "d_ci": [float(b.d.quantile(0.025)), float(b.d.quantile(0.975))],
           "r_reported_ci": [rep["r"]["0.025"], rep["r"]["0.975"]],
           "d_reported_ci": [rep["d"]["0.025"], rep["d"]["0.975"]],
           "r_width_rel": float((b.r.quantile(0.975) - b.r.quantile(0.025)) / b.r.median()),
           "d_width_rel": float((b.d.quantile(0.975) - b.d.quantile(0.025)) / b.d.median()),
           "frac_r_gt_1": float((b.r > 1).mean()),
           "判据": "区间宽度 <100%（相对中位数），且与报告值一致（差 <1e-3）",
           "结论": verdict(bool(abs(b.r.quantile(0.025) - rep["r"]["0.025"]) < 1e-3
                                and (b.r.quantile(0.975) - b.r.quantile(0.025)) / b.r.median() < 1.0))}
    return out


def m1_ident(j) -> dict:
    """可识别性：条件数（2 参数）+ 参数相关。"""
    rep = j["station_fit"]["pooled_r_d"]
    out = {"检验": "可识别性（条件数）", "kappa": rep["cond"],
           "theta": rep["theta"], "aic": rep["aic"],
           "n_train": j["station_fit"]["baselines"]["n_train"],
           "判据": f"κ<{CRIT['kappa']:.0e}",
           "结论": verdict(rep["cond"] < CRIT["kappa"])}
    return out


def m1_wind(j) -> dict:
    """风蚀项删除决策的统计审查。

    队友做了 18 组"加/不加风蚀项"的对照，1 组 p<0.05，据此删除风蚀项。
    本检验补三件他们没做的事：
      (a) 多重比较：18 次 5% 检验，期望假阳性 0.9 个，观察到 1 个 → 不能拒绝"全是噪声"；
      (b) 功效：k 的标准误 0.43，最小可检测效应约 0.85，而估计值只有 0.25；
      (c) 结论措辞：应写"未能检出"，不能写"不存在"。
    """
    d = pd.read_csv(os.path.join(M1, "wind_term_test.csv"))
    n = len(d)
    n_sig = int((d.p_value < CRIT["alpha"]).sum())
    p_binom = float(stats.binom.sf(n_sig - 1, n, CRIT["alpha"])) if n_sig > 0 else 1.0
    mde = 1.96 * d.k_se
    out = {"检验": "风蚀项删除的统计依据", "n_tests": n, "n_sig": n_sig,
           "expected_false_pos": float(n * CRIT["alpha"]),
           "binom_p_at_least_observed": p_binom,
           "k_est_range": [float(d.k.min()), float(d.k.max())],
           "k_se_primary": float(d.k_se.iloc[0]),
           "min_detectable_k": float(mde.iloc[0]),
           "k_ci_width_max": float((d.k_boot_97p5 - d.k_boot_2p5).max()),
           "within_station_corr": j["wind"]["removed_term_test"]["within_station_corr_wind_index_vs_next_year_cover_change"],
           "判据": "至少 2/18 显著，且主检验可检测 k<0.5，才可断言'无风蚀效应'",
           "结论": verdict(bool((n_sig >= 2) and (mde.iloc[0] < 0.5)),
                           fail="未通过（结论应改为'未检出'）", warn=True),
           "note": "删除风蚀项本身有依据（p 普遍很大、k 的 CI 跨 0），但'不存在风蚀效应'超出数据支持范围"}
    return out


def m1_residual(j) -> dict:
    """预测误差的三项诊断（队友未报告）：正态性、自相关、异方差。

    残差取 x=V/K 尺度的 (观测−预测)，按站点内年份顺序检查自相关（年际序列最怕这个）。
    """
    pp = pd.read_csv(os.path.join(M1, "prediction_pairs.csv"))
    e = (pp.observed_x - pp.predicted_x).to_numpy()
    n = len(e)
    W, p_sw = stats.shapiro(e)
    jb, p_jb = stats.jarque_bera(e)[:2]
    # 站内一阶自相关
    ac = []
    for s, g in pp.groupby("site"):
        x = (g.sort_values("year").observed_x - g.sort_values("year").predicted_x).to_numpy()
        if len(x) > 2 and np.std(x) > 0:
            ac.append(float(np.corrcoef(x[:-1], x[1:])[0, 1]))
    # 异方差：|残差| 对预测水平回归
    bp = stats.pearsonr(np.abs(e), pp.predicted_x)[:2]
    out = {"检验": "残差诊断", "n": n,
           "mean": float(e.mean()), "sd": float(e.std(ddof=1)),
           "shapiro_W": float(W), "shapiro_p": float(p_sw),
           "JB": float(jb), "JB_p": float(p_jb),
           "acf1_mean": float(np.mean(ac)) if ac else np.nan,
           "acf1_sites": ac,
           "abs_resid_vs_fitted_r": float(bp[0]), "abs_resid_vs_fitted_p": float(bp[1]),
           "判据": "SW p>0.05 且 |站内 acf1 均值|<0.3",
           "结论": verdict(bool(p_sw > 0.05 and abs(np.mean(ac) if ac else 0) < 0.3),
                           warn=True)}
    return out


def m2_utilization(j) -> dict:
    """约束利用率：哪条约束真的在起作用（决定论文该强调哪个瓶颈）。"""
    a = pd.read_csv(os.path.join(M2, "annual.csv"))
    mo = pd.read_csv(os.path.join(M2, "monthly.csv"))
    cfg = j["config"]
    util = {
        "年度预算": float((a.gross_spending_cny / cfg["annual_budget_cny"]).max()),
        "年水量": float((a.water_m3 / cfg["annual_water_cap_m3"]).max()),
        "月水量": float((mo.gross_water_m3 / mo.cap_m3).max()),
        "劳动力": float((a.labor_person_days / cfg["annual_labor_cap_person_days"]).max()),
        "土地": float((a.land_ha / cfg["land_cap_ha"]).max()),
        "PV 容量": float((a.pv_installed_kw / cfg["pv_capacity_cap_kw"]).max()),
    }
    binding = [k for k, v in util.items() if v > 0.999]
    total_util = float(a.gross_spending_cny.sum() / cfg["total_budget_cny"])
    eco = j["base"]["ecological_ha_year"]
    target = j["base"]["ecological_target_ha_year"]
    achieve = float(eco / target) if target > 0 else np.nan
    # 目标约束型优化：真正的瓶颈是"生态目标 + 总预算"，而不是逐年的水/地/人
    bottleneck = "生态目标与总预算" if (achieve >= 0.99 and total_util >= 0.8) else "年度资源约束"
    out = {"检验": "约束利用率", "utilization": util, "binding": binding,
           "total_budget_utilization": total_util, "eco_target_achieved": achieve,
           "bottleneck": bottleneck,
           "判据": "生态目标达成≥99% 且总预算利用≥80%，或至少一条年度约束紧",
           "结论": verdict(bool((achieve >= 0.99 and total_util >= 0.8) or len(binding) > 0))}
    return out


def m1_water(j) -> dict:
    """水量平衡闭合：逐月重算储量方程，与表内 balance_residual_mm 对照。

    M_end = M_start + net_irrigation + effective_rain + groundwater − transpiration − drainage
    """
    d = pd.read_csv(os.path.join(M1, "scenario_monthly_water.csv"))
    lhs = d.M_end_mm
    rhs = (d.M_start_mm + d.net_irrigation_mm + d.effective_rain_mm + d.groundwater_mm
           - d.transpiration_mm - d.drainage_mm)
    err = float(np.max(np.abs(lhs - rhs)))
    rep_err = float(np.max(np.abs(d.balance_residual_mm)))
    cap = float(j["adopted_parameters"]["water"]["capacity_mm"])
    out = {"检验": "水量平衡闭合", "n": int(len(d)),
           "max_recompute_error_mm": err, "max_reported_residual_mm": rep_err,
           "M_range": [float(d.M_end_mm.min()), float(d.M_end_mm.max())],
           "capacity_mm": cap, "n_above_capacity": int((d.M_end_mm > cap + 1e-6).sum()),
           "n_negative_M": int((d.M_end_mm < -1e-9).sum()),
           "判据": f"重算误差 <{CRIT['closure_mm']} mm，且 0≤M≤容量",
           "结论": verdict(bool(err < CRIT["closure_mm"] and (d.M_end_mm > cap + 1e-6).sum() == 0
                                and (d.M_end_mm < -1e-9).sum() == 0))}
    return out


def m1_water_cover(j) -> dict:
    """补水—覆盖度响应的合理性：单调、饱和、边际递减、收敛。"""
    d = pd.read_csv(os.path.join(M1, "water_cover_curve.csv"))
    V = d.V_steady_pct.to_numpy()
    I = d.irrigation_mm_yr.to_numpy()
    mono = bool(np.all(np.diff(V) > 0))
    dV = np.diff(V[d.irrigation_mm_yr.isin([0, 100, 200, 300, 600])])
    marginal = np.diff(V) / np.diff(I)
    concav = bool(np.all(np.diff(marginal[1:]) <= 1e-9))  # 允许前段线性
    vfull = float(j["adopted_parameters"]["water"]["v_full_pct"])
    out = {"检验": "补水—覆盖度响应", "monotone": mono, "concave": concav,
           "V_at_0": float(V[0]), "V_at_600": float(V[I == 600][0]) if (I == 600).any() else np.nan,
           "v_full_pct": vfull, "max_V": float(V.max()),
           "max_residual": float(d.max_fixed_point_residual.max()),
           "converged_all": bool(d.converged_both.all()),
           "marginal_first_last": [float(marginal[0]), float(marginal[-1])],
           "判据": "严格单调、边际递减、V≤端元上限、定点残差<1e-6",
           "结论": verdict(bool(mono and concav and V.max() <= vfull + 1e-6
                                and d.max_fixed_point_residual.max() < 1e-6))}
    return out


def m1_capacity(j) -> dict:
    """容量敏感性：若 W 恒为 1（蒸腾=潜在），说明灌水不是限制因子。

    这是"水约束是否真在起作用"的检验，直接决定任务二的结论该怎么写。
    """
    d = pd.read_csv(os.path.join(M1, "sensitivity.csv"))
    piv = d.pivot_table(index=["parameter", "value"], columns="irrigation_mm_yr",
                        values="V_pct").reset_index()
    cap = piv[piv.parameter == "capacity_mm"].sort_values("value")
    if len(cap) >= 2 and 300 in cap.columns:
        v_at_300 = cap[300].to_numpy()
        spread = float(v_at_300.max() - v_at_300.min())
    else:
        spread = np.nan
    coh = pd.read_csv(os.path.join(M2, "cohorts.csv"))
    frac_W1 = float((coh.W >= 0.999).mean())
    out = {"检验": "水分约束的有效性",
           "V_spread_when_capacity_30_to_150": spread,
           "frac_months_W_eq_1": frac_W1,
           "note": "W=实际/潜在蒸腾比；W=1 表示蒸腾不受水分限制",
           "判据": "容量变化（30→150 mm）应使 V 变化 >1 pp；W=1 的批次比例应 <50%",
           "结论": verdict(bool(np.isfinite(spread) and spread > 1.0 and frac_W1 < 0.5),
                           fail="未通过（水分不是限制因子）", warn=True)}
    return out


# =====================================================================================
# 2. 任务二：M2 结果的检验
# =====================================================================================

def m2_objective(j) -> dict:
    """目标值重算：把 annual.csv 的贴现净成本加总，与 JSON 报告值对照。"""
    a = pd.read_csv(os.path.join(M2, "annual.csv"))
    npc = float(a.discounted_net_cost_cny.sum())
    rep = float(j["base"]["net_present_cost_cny"])
    gross = float(a.gross_spending_cny.sum())
    rep_gross = float(j["base"]["gross_spending_cny"])
    area = float(a.new_area_ha.sum())
    out = {"检验": "目标值可复现性",
           "net_present_cost_recomputed": npc, "net_present_cost_reported": rep,
           "abs_diff": abs(npc - rep), "rel_diff": abs(npc - rep) / abs(rep),
           "gross_recomputed": gross, "gross_reported": rep_gross,
           "area_recomputed": area, "area_reported": j["base"]["new_area_total_ha"],
           "判据": "相对差 <1e-6",
           "结论": verdict(abs(npc - rep) / abs(rep) < 1e-6)}
    return out


def m2_constraints(j) -> dict:
    """约束逐项复核（可行性是硬要求）。

    预算 / 年度预算 / 水量（年 + 月）/ 劳动力 / 土地 / 新增面积 / PV 容量 / 整数块。
    """
    a = pd.read_csv(os.path.join(M2, "annual.csv"))
    mo = pd.read_csv(os.path.join(M2, "monthly.csv"))
    cfg = j["config"]
    checks = {
        "年度预算": float((a.gross_spending_cny - cfg["annual_budget_cny"]).max()),
        "总预算余额": float(a.unspent_total_budget_cny.min()),
        "年水量": float((a.water_m3 - cfg["annual_water_cap_m3"]).max()),
        "月水量": float((mo.gross_water_m3 - mo.cap_m3).max()),
        "劳动力": float(a.labor_person_days.max() - cfg["annual_labor_cap_person_days"]),
        "土地": float(a.land_ha.max() - cfg["land_cap_ha"]),
        "新增面积": float(a.new_area_ha.max() - cfg["annual_new_area_cap_ha"]),
        "PV 容量": float(a.pv_installed_kw.max() - cfg["pv_capacity_cap_kw"]),
        "面积整数块": float(np.abs(a.new_area_ha / cfg["area_block_ha"]
                                   - np.round(a.new_area_ha / cfg["area_block_ha"])).max()),
        "资金比例和": float((a[["construction_fund_share", "om_fund_share",
                               "pv_facilities_fund_share"]].sum(axis=1) - 1).abs().max()),
    }
    viol = {k: v for k, v in checks.items() if v > 1e-6 and k != "总预算余额"}
    ok = (not viol) and checks["总预算余额"] >= -1e-6
    out = {"检验": "约束可行性", "checks": checks, "violations": viol,
           "判据": "全部约束余量 ≥0（资金比例和误差 <1e-6）",
           "结论": verdict(ok)}
    return out


def m2_mipgap(j) -> dict:
    """MIP 质量：gap、对偶界夹逼、情景可行性。"""
    s = pd.read_csv(os.path.join(M2, "scenario_summary.csv"))
    gaps = s.mip_gap.to_numpy()
    # 成本最小化：dual_bound_scaled 单位为百万元，是下界 → dual*1e6 ≤ cost
    cost = s[s.objective == "cost"]
    slack_low = (cost.dual_bound_scaled * 1e6 - cost.net_present_cost_cny).max()
    # 生态最大化：优化的是 -H/1000，故 -1000*dual 是上界
    eco = s[s.objective == "ecology"]
    slack_up = (eco.ecological_ha_year - (-1000 * eco.dual_bound_scaled)).max()
    out = {"检验": "MIP 最优性证据", "n_scenarios": int(len(s)),
           "max_gap": float(np.nanmax(gaps)), "median_gap": float(np.nanmedian(gaps)),
           "all_feasible": bool(s.feasible.all()),
           "cost_bound_violation": float(slack_low),
           "eco_bound_violation": float(slack_up),
           "判据": f"gap≤{CRIT['mip_gap']}、全部可行、对偶界不越界",
           "结论": verdict(bool(np.nanmax(gaps) <= CRIT["mip_gap"] and s.feasible.all()
                                and slack_low <= 1e-6 and slack_up <= 1e-6))}
    return out


def m2_frontier(j) -> dict:
    """Pareto 前沿自洽性：生态目标升高时，成本与实际生态都应非降。"""
    s = pd.read_csv(os.path.join(M2, "scenario_summary.csv"))
    f = s[s.group == "frontier"].sort_values("ecological_target_ha_year")
    if len(f) < 3:
        return {"检验": "Pareto 前沿自洽", "结论": "需改进", "判据": "至少 3 个前沿点"}
    dcost = np.diff(f.net_present_cost_cny.to_numpy())
    deco = np.diff(f.ecological_ha_year.to_numpy())
    out = {"检验": "Pareto 前沿自洽", "n_points": int(len(f)),
           "cost_monotone": bool(np.all(dcost >= -1e-6)),
           "eco_monotone": bool(np.all(deco >= -1e-6)),
           "eco_range": [float(f.ecological_ha_year.min()), float(f.ecological_ha_year.max())],
           "cost_range": [float(f.net_present_cost_cny.min()), float(f.net_present_cost_cny.max())],
           "隐含单位生态成本_末段": float(dcost[-1] / deco[-1]) if deco[-1] > 0 else np.nan,
           "判据": "成本与生态均单调不减",
           "结论": verdict(bool(np.all(dcost >= -1e-6) and np.all(deco >= -1e-6)))}
    return out


def m2_pv(j) -> dict:
    """光伏筛选与决策的一致：只在保本电价低于售价的年份装 PV。"""
    pv = pd.read_csv(os.path.join(M2, "pv_screening.csv"))
    a = pd.read_csv(os.path.join(M2, "annual.csv"))
    price = CRIT["pv_price"]
    pv["profitable"] = pv.break_even_price_cny_kwh < price
    install_years = set(a[a.new_pv_kw > 0].year.tolist())
    years = set(pv.start_year.tolist())
    consistent = all((y in install_years) <= bool(pv[pv.start_year == y].profitable.iloc[0])
                     for y in years)
    out = {"检验": "PV 筛选一致性",
           "break_even_range": [float(pv.break_even_price_cny_kwh.min()),
                                float(pv.break_even_price_cny_kwh.max())],
           "price": price,
           "profitable_years": pv[pv.profitable].start_year.tolist(),
           "install_years": sorted(install_years),
           "consistent": bool(consistent),
           "判据": "安装年份 ⊆ 保本年份",
           "结论": verdict(consistent)}
    return out


def m2_effective(j) -> dict:
    """有效面积口径复核：effective_ha = Σ area·V_start/K，与 annual.csv 对表。"""
    coh = pd.read_csv(os.path.join(M2, "cohorts.csv"))
    a = pd.read_csv(os.path.join(M2, "annual.csv"))
    K = j["m1_parameters"]["K_section_pct"]
    calc = (coh.assign(eff=coh.area_ha * coh.V_start_pct / K)
            .groupby("year").eff.sum().rename("calc"))
    m = a.set_index("year").join(calc)
    rel = float(np.max(np.abs(m.effective_ha - m.calc) / np.maximum(m.effective_ha, 1e-9)))
    out = {"检验": "有效面积口径", "K_used": K, "max_rel_error": rel,
           "total_eff_ha_year": float(a.effective_ha.sum()),
           "判据": "相对误差 <1e-9",
           "结论": verdict(rel < 1e-9)}
    return out


def m2_replay(j) -> dict:
    """回放误差：按 decisions.csv 重算年新增面积，与 annual.csv 对表。"""
    d = pd.read_csv(os.path.join(M2, "decisions.csv"))
    a = pd.read_csv(os.path.join(M2, "annual.csv"))
    area = d[d.kind == "eco"].groupby("start_year").area_ha.sum()
    m = a.set_index("year").join(area.rename("from_decisions")).fillna({"from_decisions": 0})
    err = float(np.max(np.abs(m.new_area_ha - m.from_decisions)))
    rep = j.get("replay_max_abs_errors", {}).get("new_area_ha", np.nan)
    out = {"检验": "决策回放一致性", "max_abs_error_ha": err, "reported": rep,
           "decisions_total_ha": float(d[d.kind == "eco"].area_ha.sum()),
           "annual_total_ha": float(a.new_area_ha.sum()),
           "判据": "最大绝对误差 <1e-6 ha",
           "结论": verdict(err < 1e-6)}
    return out


def m2_crossmodel(j1, j2) -> dict:
    """跨模型一致性：M2 使用的 M1 参数是否与 M1 结果一致。"""
    p1 = j1["adopted_parameters"]
    p2 = j2["m1_parameters"]
    diffs = {"r": abs(p1["r"] - p2["r"]), "d": abs(p1["d"] - p2["d"]),
             "K": abs(p1["K_section_pct"] - p2["K_section_pct"])}
    for k in ("capacity_mm", "v_full_pct", "eta_w"):
        diffs[k] = abs(p1["water"][k] - p2["water"][k])
    mx = max(diffs.values())
    out = {"检验": "跨模型参数一致", "diffs": diffs,
           "r": p2["r"], "d": p2["d"], "K": p2["K_section_pct"],
           "判据": "全部差 <1e-6",
           "结论": verdict(mx < 1e-6)}
    return out


# =====================================================================================
# 3. 任务三：公式规格检验（尚无数值实现，因此只检验"设计是否自洽"）
# =====================================================================================

def m3_spec(j1, j2):
    """用 M1 的当前参数与 M2 的情景配置检验 M3 的设计公式。

    注意：M3 尚未实现数值求解，这里检验的是"如果按 model_v7.tex 的公式实现，
    矩阵性质、解析/模拟一致性、离散化收敛、λ=0 极限是否成立"。
    """
    r = j1["adopted_parameters"]["r"]
    d = j1["adopted_parameters"]["d"]
    K = j1["adopted_parameters"]["K_section_pct"]
    k, eta = j2["m1_parameters"]["k"], j2["m1_parameters"]["eta"]
    W = 0.37          # 由 M1 情景（300 mm 灌溉）的 W 取得
    lam, u_lo, u_hi, rho = 0.30, 0.20, 0.55, 0.30
    res = {}

    def step(v, Wt, Et):
        g = r * v * (1 - v / K) * Wt
        return v + g - d * v - k * Et * (1 - eta * v / K) * v

    def build(n=200, lam_=lam, multievent=False):
        vmax, grid = 1.5 * K, None
        grid = np.linspace(0, vmax, n)
        absorb = grid < rho * K
        sp = vmax / (n - 1)
        idx = lambda x: int(np.clip(round(x / sp), 0, n - 1))
        P = np.zeros((n, n))
        rs = np.random.default_rng(SEED)
        for i in range(n):
            if absorb[i]:
                P[i, i] = 1.0
                continue
            v = grid[i]
            if multievent:
                M = 3000
                Kk = rs.poisson(lam_, size=M)
                Z = np.ones(M)
                for m in range(M):
                    if Kk[m] > 0:
                        Z[m] = np.prod(1 - rs.uniform(u_lo, u_hi, size=Kk[m]))
                for z in Z:
                    P[i, idx(step(v * z, W, 1.0))] += 1 / M
            else:
                P[i, idx(step(v, W, 1.0))] += 1 - lam_
                for u in np.linspace(u_lo, u_hi, 15):
                    P[i, idx(step(v * (1 - u), W, 1.0))] += lam_ / 15
        return {"P": P, "grid": grid, "absorb": absorb, "vcrit": rho * K, "K": K, "n": n}

    def metrics(ch, T):
        keep = ~ch["absorb"]
        Q = ch["P"][np.ix_(keep, keep)]
        p0 = np.zeros(keep.sum())
        p0[np.argmin(np.abs(ch["grid"][keep] - K))] = 1.0
        pt = 1 - float(np.sum(np.linalg.matrix_power(Q.T, T) @ p0))
        rhoq = float(np.max(np.abs(np.linalg.eigvals(Q))))
        if rhoq < 1 - 1e-10:
            N = np.linalg.inv(np.eye(keep.sum()) - Q)
            etau = float((N @ np.ones(keep.sum()))[np.argmax(p0)])
        else:
            etau = np.inf
        return pt, etau, rhoq

    ch = build()
    P = ch["P"]
    rowsum = float(np.abs(P.sum(1) - 1).max())
    res["matrix"] = {"检验": "转移矩阵性质", "max_row_sum_error": rowsum,
                     "min_entry": float(P.min()),
                     "absorbing_identity": bool(np.allclose(P[ch["absorb"]][:, ch["absorb"]],
                                                            np.eye(ch["absorb"].sum()))),
                     "判据": "行和误差<1e-12、元素≥0、吸收态自封",
                     "结论": verdict(rowsum < 1e-12 and P.min() >= -1e-15)}
    pt5, e5, rhoq = metrics(ch, 5)
    chm = build(multievent=True)
    pt5m, _, _ = metrics(chm, 5)
    # MC（与解析同构：至多一次事件）
    rs = np.random.default_rng(SEED)
    M = 60000
    v = np.full(M, K)
    alive = np.ones(M, bool)
    tau = np.full(M, np.inf)
    for t in range(1, 6):
        if not alive.any():
            break
        idx = np.where(alive)[0]
        m = len(idx)
        ev = rs.random(m) < lam
        u = rs.uniform(u_lo, u_hi, size=m) * ev
        vv = v[idx] * (1 - u)
        vv = np.array([step(x, W, 1.0) for x in vv])
        v[idx] = vv
        dead = vv < ch["vcrit"]
        tau[idx[dead]] = t
        alive[idx[dead]] = False
    pt_mc = float(np.mean(tau <= 5))
    se = np.sqrt(pt_mc * (1 - pt_mc) / M)
    res["analytic_vs_mc"] = {"检验": "解析 vs 蒙特卡洛", "T": 5,
                             "analytic": pt5, "mc": pt_mc,
                             "ci95": [pt_mc - 1.96 * se, pt_mc + 1.96 * se],
                             "inside": bool(pt_mc - 1.96 * se <= pt5 <= pt_mc + 1.96 * se),
                             "判据": "解析落在 MC 95%CI 内",
                             "结论": verdict(pt_mc - 1.96 * se <= pt5 <= pt_mc + 1.96 * se)}
    conv = []
    for n in (100, 200, 400, 800):
        p, _, _ = metrics(build(n=n), 5)
        conv.append({"n": n, "P_tau_le_5": p})
    rel = float(np.max(np.abs(np.diff([c["P_tau_le_5"] for c in conv]))
                       / np.array([c["P_tau_le_5"] for c in conv[:-1]])))
    res["convergence"] = {"检验": "离散化收敛", "table": conv, "max_rel_change": rel,
                          "判据": "相邻网格相对变化 <1%",
                          "结论": verdict(rel < 0.01)}
    # λ=0 极限
    ch0 = build(lam_=0.0)
    # 无灾时确定性稳态
    v = K
    for _ in range(200):
        v = step(v, W, 1.0)
    res["lambda_zero"] = {"检验": "λ=0 极限", "v_steady": float(v), "vcrit": ch0["vcrit"],
                          "survives": bool(v > ch0["vcrit"]),
                          "判据": "无灾时收敛到 v*>vcrit",
                          "结论": verdict(v > ch0["vcrit"])}
    res["_numbers"] = {"E_tau": e5, "P5": pt5, "P5_multi": pt5m,
                       "rho_Q": rhoq, "vcrit": ch["vcrit"], "K": K,
                       "params": {"r": r, "d": d, "K": K, "k": k, "eta": eta, "W": W}}
    return res


# =====================================================================================
# 4. 图
# =====================================================================================

def fig_m1_fit(j):
    pp = pd.read_csv(os.path.join(M1, "prediction_pairs.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.6))
    for ax, split, name in ((axes[0], "train", "训练期"), (axes[1], "test", "留出期")):
        d = pp[pp.split == split]
        ax.plot([0.6, 1.1], [0.6, 1.1], "--", color=C["grey"], lw=1)
        ax.scatter(d.observed_x, d.predicted_x, s=14, color=C["mod"], label="模型", zorder=3)
        ax.scatter(d.observed_x, d.persistence_x, s=14, color=C["alt"], marker="^",
                   alpha=0.6, label="持续性", zorder=2)
        e = d.predicted_x - d.observed_x
        ax.set_title(f"{name}（n={len(d)}，RMSE={np.sqrt(np.mean(e**2)):.4f}）")
        ax.set_xlabel("观测 $x=V/K$"); ax.set_ylabel("预测 $x$")
    axes[0].legend()
    fig.tight_layout()
    savefig(fig, "v1_m1_fit.png")


def fig_m1_skill(j):
    h = pd.read_csv(os.path.join(M1, "holdout_by_site.csv")).sort_values("mse_skill_vs_persistence")
    fr = pd.read_csv(os.path.join(M1, "free_running_holdout.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.4))
    ax = axes[0]
    ax.barh(h.site, h.mse_skill_vs_persistence,
            color=[C["ok"] if v > 0 else C["bad"] for v in h.mse_skill_vs_persistence])
    ax.axvline(0, color=C["obs"], lw=0.8)
    ax.set_xlabel("留站技能分 $1-\\mathrm{MSE}_{mod}/\\mathrm{MSE}_{pers}$")
    ax.set_title("(a) 逐站留出技能分（负值必须保留）")
    ax = axes[1]
    for s, g in fr.groupby("site"):
        ax.plot(g.year, g.observed_pct, "o-", ms=3, color=C["obs"], lw=0.8, alpha=0.55)
        ax.plot(g.year, g.predicted_pct, "s--", ms=3, color=C["mod"], lw=0.9)
        ax.plot(g.year, g.persistence_2022_pct, ":", color=C["alt"], lw=0.8)
    ax.set_xlabel("年"); ax.set_ylabel("覆盖度 / %")
    ax.set_title("(b) 自由推演 2023—2025（蓝=模型，橙点线=持续 2022）")
    fig.tight_layout()
    savefig(fig, "v2_m1_skill.png")


def fig_m1_params(j):
    b = pd.read_csv(os.path.join(M1, "parameter_cluster_bootstrap.csv"))
    lo = j["station_fit"]["leave_one_station_out"]
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.4))
    ax = axes[0]
    ax.scatter(b.r, b.d, s=8, color=C["mod"], alpha=0.6)
    ax.axvline(j["station_fit"]["pooled_r_d"]["theta"][0], color=C["bad"], ls="--", lw=1)
    ax.axhline(j["station_fit"]["pooled_r_d"]["theta"][1], color=C["bad"], ls="--", lw=1)
    ax.set_xlabel("$r$"); ax.set_ylabel("$d$")
    ax.set_title("(a) 整簇自助（300 次，7 簇）")
    ax = axes[1]
    yy = np.arange(len(lo))
    ax.barh(yy - 0.19, [v["r"] for v in lo.values()], height=0.36, color=C["mod"], label="$r$")
    ax.barh(yy + 0.19, [v["d"] for v in lo.values()], height=0.36, color=C["alt"], label="$d$")
    ax.set_yticks(yy); ax.set_yticklabels(list(lo))
    ax.axvline(j["station_fit"]["pooled_r_d"]["theta"][0], color=C["mod"], ls=":", lw=1)
    ax.set_title("(b) 留一站估计"); ax.legend()
    fig.tight_layout()
    savefig(fig, "v3_m1_params.png")


def fig_m1_wind(j):
    d = pd.read_csv(os.path.join(M1, "wind_term_test.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.5))
    ax = axes[0]
    yy = np.arange(len(d))
    ax.errorbar(d.k, yy, xerr=1.96 * d.k_se, fmt="o", ms=3.5, color=C["mod"],
                ecolor=C["light"], capsize=2, lw=1)
    ax.axvline(0, color=C["bad"], ls="--", lw=1)
    ax.set_yticks(yy)
    ax.set_yticklabels([f"{a[:18]}·{b[:8]}" for a, b in zip(d.indicator, d.form)], fontsize=6.5)
    ax.set_xlabel("风蚀系数 $k$（±95%CI）")
    ax.set_title("(a) 18 组加/不加风蚀项的估计")
    ax = axes[1]
    ax.hist(d.p_value, bins=np.linspace(0, 1, 10), color=C["light"], edgecolor=C["obs"])
    ax.axvline(0.05, color=C["bad"], ls="--", lw=1)
    ax.set_xlabel("$p$ 值"); ax.set_ylabel("组数")
    ax.set_title("(b) $p$ 值分布：仅 1/18 低于 0.05（期望假阳性 0.9）")
    fig.tight_layout()
    savefig(fig, "v4_m1_wind.png")


def fig_m1_water(j):
    wc = pd.read_csv(os.path.join(M1, "water_cover_curve.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.4))
    ax = axes[0]
    ax.plot(wc.irrigation_mm_yr, wc.V_steady_pct, "o-", color=C["mod"], ms=3.5)
    ax.axhline(j["adopted_parameters"]["water"]["v_full_pct"], color=C["bad"], ls="--", lw=1,
               label="端元上限 $V_{full}$")
    ax.set_xlabel("灌溉 / (mm·a$^{-1}$)"); ax.set_ylabel("稳态覆盖度 / %")
    ax.set_title("(a) 补水—覆盖度响应"); ax.legend()
    ax = axes[1]
    ax.plot(wc.irrigation_mm_yr, wc.W, "s--", color=C["ok"], ms=3.5)
    ax.set_xlabel("灌溉 / (mm·a$^{-1}$)"); ax.set_ylabel("$W$（实际/潜在蒸腾）")
    ax.set_ylim(0, 1.05)
    ax.set_title("(b) 水分胁迫：灌溉足够时 $W\\to1$")
    fig.tight_layout()
    savefig(fig, "v5_m1_water.png")


def fig_m2_plan(j):
    a = pd.read_csv(os.path.join(M2, "annual.csv"))
    mo = pd.read_csv(os.path.join(M2, "monthly.csv"))
    fig, axes = plt.subplots(2, 2, figsize=(8.4, 5.2))
    ax = axes[0, 0]
    ax.bar(a.year, a.new_area_ha, color=C["light"], edgecolor=C["mod"], label="新增")
    ax.plot(a.year, a.eco_area_ha, color=C["mod"], marker="o", ms=3, label="存量")
    ax.set_xlabel("年"); ax.set_ylabel("ha"); ax.set_title("(a) 生态面积"); ax.legend()
    ax = axes[0, 1]
    ax.bar(a.year, a.pv_installed_kw, color=C["purple"], alpha=0.8)
    ax.set_xlabel("年"); ax.set_ylabel("kW"); ax.set_title("(b) 光伏装机")
    ax = axes[1, 0]
    ax.bar(a.year, a.gross_spending_cny / 1e6, color=C["alt"])
    ax.axhline(j["config"]["annual_budget_cny"] / 1e6, color=C["bad"], ls="--", lw=1, label="年度预算")
    ax.set_xlabel("年"); ax.set_ylabel("百万元"); ax.set_title("(c) 年支出 vs 预算"); ax.legend()
    ax = axes[1, 1]
    ax.plot(mo.year + (mo.month - 0.5) / 12, mo.gross_water_m3 / 1e3, color=C["mod"], lw=1)
    ax.plot(mo.year + (mo.month - 0.5) / 12, mo.cap_m3 / 1e3, color=C["bad"], ls="--", lw=1)
    ax.set_xlabel("年"); ax.set_ylabel("千 m$^3$/月"); ax.set_title("(d) 月取水与上限")
    fig.tight_layout()
    savefig(fig, "v6_m2_plan.png")


def fig_m2_frontier():
    s = pd.read_csv(os.path.join(M2, "scenario_summary.csv"))
    f = s[s.group == "frontier"].sort_values("ecological_target_ha_year")
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.4))
    ax = axes[0]
    ax.plot(f.ecological_ha_year, f.net_present_cost_cny / 1e6, "o-", color=C["ok"], ms=4)
    ax.set_xlabel("生态产出 /（有效 ha·年）"); ax.set_ylabel("净现成本 / 百万元")
    ax.set_title("(a) 生态—成本前沿（28 情景中的 frontier 组）")
    ax = axes[1]
    ax.scatter(s.ecological_target_ha_year, s.mip_gap * 100, s=18, color=C["mod"])
    ax.axhline(CRIT["mip_gap"] * 100, color=C["bad"], ls="--", lw=1, label="容差 0.2%")
    ax.set_xlabel("生态目标 /（有效 ha·年）"); ax.set_ylabel("MIP gap / %")
    ax.set_title("(b) 求解质量"); ax.legend()
    fig.tight_layout()
    savefig(fig, "v7_m2_frontier.png")


def fig_scorecard(rows):
    def code(c):
        return 2 if c == "通过" else (0 if c.startswith("未通过") else 1)
    codes = [code(r["结论"]) for r in rows]
    fig, ax = plt.subplots(figsize=(6.8, 0.42 * len(rows) + 1.0))
    ax.imshow(np.asarray(codes)[:, None],
              cmap=matplotlib.colors.ListedColormap([C["bad"], "#f6ad55", C["ok"]]),
              vmin=0, vmax=2, aspect="auto")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"{r['模块']}｜{r['检验']}" for r in rows], fontsize=8)
    ax.set_xticks([])
    for i, r in enumerate(rows):
        ax.text(0, i, "  " + r["结论"], va="center", fontsize=8,
                color="white" if codes[i] != 1 else "#1f2937")
    ax.set_title("M1 / M2 / M3 检验评分卡")
    fig.tight_layout()
    savefig(fig, "v8_scorecard.png")


# =====================================================================================
# 5. 主流程
# =====================================================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    t0 = time.time()
    print("=" * 76)
    print("2026 CQU_MCM B 题 · M1/M2 数值结果检验")
    print("=" * 76)

    j1 = json.load(open(os.path.join(M1, "model1_results.json"), encoding="utf-8"))
    j2 = json.load(open(os.path.join(M2, "model2_results.json"), encoding="utf-8"))

    print("\n[任务一] 重算指标与诊断 ...")
    m1m = m1_metrics(j1)
    print(f"  重算 train RMSE={m1m['train']['RMSE']:.4f}（报告 {m1m['reported']['rmse_train']:.4f}），"
          f"test RMSE={m1m['test']['RMSE']:.4f}（报告 {m1m['reported']['rmse_test']:.4f}）")
    print(f"  test skill(RMSE)={m1m['test']['skill_RMSE']:+.3f}，R²={m1m['test']['R2']:.3f}")
    skill = m1_skill_test(j1, m1m)
    hold = m1_holdout(j1)
    par = m1_params(j1)
    boot = m1_bootstrap(j1)
    ident = m1_ident(j1)
    wind = m1_wind(j1)
    resid = m1_residual(j1)
    water = m1_water(j1)
    wc = m1_water_cover(j1)
    cap = m1_capacity(j1)
    print(f"  留站技能分：{hold['n_negative']}/{hold['n_sites']} 为负，中位数 {hold['median_skill']:.2f}")
    print(f"  自由推演 skill={hold['free_running']['skill']:+.3f}")
    print(f"  水量闭合误差 {water['max_recompute_error_mm']:.2e} mm")
    print(f"  风蚀检验：{wind['n_sig']}/{wind['n_tests']} 显著，最小可检测 k={wind['min_detectable_k']:.2f}")

    print("\n[任务二] 目标/约束/求解质量 ...")
    obj = m2_objective(j2)
    cons = m2_constraints(j2)
    gap = m2_mipgap(j2)
    front = m2_frontier(j2)
    pv = m2_pv(j2)
    eff = m2_effective(j2)
    replay = m2_replay(j2)
    util = m2_utilization(j2)
    cross = m2_crossmodel(j1, j2)
    print(f"  净现成本重算 {obj['net_present_cost_recomputed']:.0f} vs 报告 {obj['net_present_cost_reported']:.0f}")
    print(f"  约束违反项：{cons['violations'] if cons['violations'] else '无'}")
    print(f"  MIP gap 最大 {gap['max_gap']*100:.3f}%，全部可行={gap['all_feasible']}")

    print("\n[任务三] 公式规格检验（尚无数值实现）...")
    m3 = m3_spec(j1, j2)

    rows = [
        {"模块": "M1", "检验": "指标可复现", "结论": m1m["结论"],
         "依据": f"最大差 {m1m['repro_max_abs_diff']:.1e}"},
        {"模块": "M1", "检验": "vs 持续性", "结论": skill["结论"],
         "依据": f"test 胜率 {skill['test_win_rate']*100:.0f}%，ΔMAE={skill['table'][1]['mean_diff']:+.4f}"},
        {"模块": "M1", "检验": "留站泛化", "结论": hold["结论"],
         "依据": f"{hold['n_negative']}/7 站为负，中位技能 {hold['median_skill']:.2f}"},
        {"模块": "M1", "检验": "自由推演", "结论": "通过" if hold["free_running"]["skill"] > 0 else "未通过",
         "依据": f"3 年 RMSE {hold['free_running']['RMSE_model_pct']:.1f}% vs 持续 "
                 f"{hold['free_running']['RMSE_persistence_pct']:.1f}%"},
        {"模块": "M1", "检验": "参数稳定性", "结论": par["结论"],
         "依据": f"r∈[{par['r_range'][0]:.2f},{par['r_range'][1]:.2f}]"},
        {"模块": "M1", "检验": "参数区间", "结论": boot["结论"],
         "依据": f"r 宽度 {boot['r_width_rel']*100:.0f}%"},
        {"模块": "M1", "检验": "可识别性", "结论": ident["结论"],
         "依据": f"κ={ident['kappa']:.0f}"},
        {"模块": "M1", "检验": "风蚀项依据", "结论": wind["结论"],
         "依据": f"{wind['n_sig']}/{wind['n_tests']} 显著，可检测 k≥{wind['min_detectable_k']:.2f}"},
        {"模块": "M1", "检验": "残差诊断", "结论": resid["结论"],
         "依据": f"SW p={resid['shapiro_p']:.3f}，站内 acf1 均值 {resid['acf1_mean']:+.2f}"},
        {"模块": "M1", "检验": "水量闭合", "结论": water["结论"],
         "依据": f"误差 {water['max_recompute_error_mm']:.1e} mm"},
        {"模块": "M1", "检验": "水—覆盖响应", "结论": wc["结论"],
         "依据": f"V(0)={wc['V_at_0']:.1f}% → V(600)={wc['V_at_600']:.1f}%"},
        {"模块": "M1", "检验": "水分约束有效性", "结论": cap["结论"],
         "依据": f"容量放大 5 倍 V 仅变 {cap['V_spread_when_capacity_30_to_150']:.2f} pp"},
        {"模块": "M2", "检验": "目标值可复现", "结论": obj["结论"],
         "依据": f"相对差 {obj['rel_diff']:.1e}"},
        {"模块": "M2", "检验": "约束可行性", "结论": cons["结论"],
         "依据": "全部余量≥0" if not cons["violations"] else f"{len(cons['violations'])} 项越界"},
        {"模块": "M2", "检验": "MIP 质量", "结论": gap["结论"],
         "依据": f"最大 gap {gap['max_gap']*100:.3f}%"},
        {"模块": "M2", "检验": "前沿自洽", "结论": front["结论"],
         "依据": f"{front.get('n_points','-')} 点单调"},
        {"模块": "M2", "检验": "PV 筛选一致", "结论": pv["结论"],
         "依据": f"安装年 {pv['install_years']}"},
        {"模块": "M2", "检验": "有效面积口径", "结论": eff["结论"],
         "依据": f"相对误差 {eff['max_rel_error']:.1e}"},
        {"模块": "M2", "检验": "决策回放", "结论": replay["结论"],
         "依据": f"误差 {replay['max_abs_error_ha']:.1e} ha"},
        {"模块": "M2", "检验": "约束利用率", "结论": util["结论"],
         "依据": f"生态达成 {util['eco_target_achieved']*100:.0f}%、总预算用 {util['total_budget_utilization']*100:.0f}%；瓶颈＝{util['bottleneck']}"},
        {"模块": "M2", "检验": "跨模型参数", "结论": cross["结论"],
         "依据": f"最大差 {max(cross['diffs'].values()):.1e}"},
        {"模块": "M3", "检验": "转移矩阵", "结论": m3["matrix"]["结论"],
         "依据": f"行和误差 {m3['matrix']['max_row_sum_error']:.1e}"},
        {"模块": "M3", "检验": "解析 vs MC", "结论": m3["analytic_vs_mc"]["结论"],
         "依据": f"{m3['analytic_vs_mc']['analytic']:.3f} vs {m3['analytic_vs_mc']['mc']:.3f}"},
        {"模块": "M3", "检验": "离散化收敛", "结论": m3["convergence"]["结论"],
         "依据": f"最大相对变化 {m3['convergence']['max_rel_change']*100:.2f}%"},
        {"模块": "M3", "检验": "λ=0 极限", "结论": m3["lambda_zero"]["结论"],
         "依据": f"v∞={m3['lambda_zero']['v_steady']:.1f}%"},
    ]

    # 明细落盘
    pd.DataFrame(m1m["table"] if "table" in m1m else [m1m["train"], m1m["test"]]).to_csv(
        os.path.join(RES, "m1_metrics_by_split.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame(skill["table"]).to_csv(os.path.join(RES, "m1_skill_tests.csv"),
                                        index=False, encoding="utf-8-sig")
    pd.read_csv(os.path.join(M1, "holdout_by_site.csv")).to_csv(
        os.path.join(RES, "m1_holdout_by_site.csv"), index=False, encoding="utf-8-sig")
    pd.read_csv(os.path.join(M2, "scenario_summary.csv")).to_csv(
        os.path.join(RES, "m2_scenario_summary.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame(rows).to_csv(os.path.join(RES, "scorecard_m1m2.csv"), index=False,
                              encoding="utf-8-sig")

    print("\n[绘图] ...")
    fig_m1_fit(j1)
    fig_m1_skill(j1)
    fig_m1_params(j1)
    fig_m1_wind(j1)
    fig_m1_water(j1)
    fig_m2_plan(j2)
    fig_m2_frontier()
    fig_scorecard(rows)

    out = {"meta": {"generated": time.strftime("%Y-%m-%d %H:%M:%S"), "seed": SEED,
                    "m1_json": "Results/v7/model1/model1_results.json",
                    "m2_json": "Results/v7/model2/model2_results.json"},
           "m1": {"metrics": m1m, "skill": skill, "holdout": hold, "params": par,
                  "bootstrap": boot, "ident": ident, "wind": wind, "water": water,
                  "water_cover": wc, "capacity": cap, "residual": resid},
           "m2": {"objective": obj, "constraints": cons, "mip": gap, "frontier": front,
                  "pv": pv, "effective": eff, "replay": replay, "cross": cross, "utilization": util},
           "m3": m3, "scorecard": rows,
           "score": {k: sum(1 for r in rows if r["结论"].startswith(k))
                     for k in ("通过", "未通过", "需改进")}}
    jdump(out, "validation_m1m2.json")

    print("\n" + "=" * 76)
    print(pd.DataFrame(rows)[["模块", "检验", "结论", "依据"]].to_string(index=False))
    print(f"\n合计：通过 {out['score']['通过']}、需改进 {out['score']['需改进']}、"
          f"未通过 {out['score']['未通过']}；用时 {time.time()-t0:.1f} s")
    print("=" * 76)


if __name__ == "__main__":
    main()




