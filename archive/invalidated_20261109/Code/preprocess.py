# -*- coding: utf-8 -*-
r"""
preprocess.py —— 《治沙是一项精细活》B 题：全流程数据预处理
=================================================================
功能：读取原始多源数据 → 审计 → 规范化 → 去重 → 单位统一 → 物理阈值
      → 异常值检测与截尾 → 缺失值插补（5 种策略对比）→ 面板对齐
      → 特征工程 → 共线性筛选 → 标准化（3 种方案对比）→ 时序划分
      → 输出处理后数据 / 图表 / 统计报告

运行环境：Python 3.9+；依赖：pandas, numpy, matplotlib
        pip install pandas numpy matplotlib

=================================================================
【路径设置】
  BASE     ：本文件所在 Code 目录的上一级（即项目根目录），无需手工修改
  下方各路径均基于 BASE 拼接；如目录结构不同，再改写对应的子目录名
  Windows 示例：r"C:\...\Practice2\Data\raw"
  macOS/Linux 示例："/Users/.../Practice2/Data/raw"
  注意：路径中尽量避免中文与空格；若必须使用，保留 r"" 原始字符串前缀
=================================================================
"""

import json
import os
import re
import sys

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ============================ 路径配置 ============================
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE, "Data", "raw")
OUT_DATA = os.path.join(BASE, "Data", "processed")
OUT_FIG = os.path.join(BASE, "Figures")
STATS_PATH = os.path.join(BASE, "Data", "processed", "stats.json")
# ==================================================================

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 200
plt.rcParams["savefig.dpi"] = 200
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.25
plt.rcParams["axes.edgecolor"] = "#666666"

RAW_FILE = "01_站点月尺度面板_real_raw.csv"      # 真实数据（01_fetch_real_data.py 生成）
RAW_FILE_FALLBACK = "02_站点月尺度面板_raw.csv"   # 早期合成数据（仅用于流程自测）

NUM_COLS = ["经度", "纬度", "风速", "降水", "气温", "土壤含水率", "植被覆盖度",
            "输沙率", "输沙势"]

# 真实数据里的列名 → 流程内部统一列名
RENAME = {"土壤含水率_0_7cm": "土壤含水率", "风速日最大_月均": "风速日最大"}

STATION_MAP = {"塔中站": "塔中", "TZ": "塔中", "XT": "肖塘", "QM": "且末", "MF": "民丰",
               "RQ": "若羌", "KEL": "库尔勒", "YL": "尉犁", "ALE": "阿拉尔"}
SURF_MAP = {"mobile dune": "流动沙丘", "semi-fixed sandy land": "半固定沙地",
            "gobi": "戈壁", "oasis-desert ecotone": "绿洲—荒漠过渡带",
            "oasis fringe": "绿洲边缘", "oasis-desert interlaced zone": "绿洲—沙漠交错带"}
UNIT_FACTOR = {
    ("风速", "km/h"): 1 / 3.6,
    ("风速", "m/s"): 1.0,
    ("降水", "cm"): 10.0,
    ("降水", "mm"): 1.0,
    ("输沙率", "g/(cm·min)"): 525.6,      # 1 g/(cm·min) = 525.6 t/(km²·a)
    ("输沙率", "t/(km²·a)"): 1.0,
}
PHYS_BOUNDS = {
    "风速": (0.0, 40.0), "风速日最大": (0.0, 50.0), "降水": (0.0, 400.0),
    "气温": (-45.0, 50.0), "土壤含水率": (0.2, 40.0), "植被覆盖度": (0.0, 100.0),
    "NDVI": (-0.2, 1.0), "输沙率": (0.0, 5000.0), "输沙势": (0.0, 5000.0),
}


# ------------------------------------------------------------------
# 0. 读取
# ------------------------------------------------------------------
def load(path):
    if not os.path.exists(path):
        sys.exit(f"[读取失败] 找不到文件：{path}\n"
                 f"→ 请检查：① 路径拼写与盘符；② 是否把数据放在了 数据/raw/ 下；"
                 f"③ 文件名是否与脚本一致。")
    for enc in ("utf-8-sig", "gbk", "utf-8"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    sys.exit(f"[读取失败] 编码无法识别：{path}\n→ 请用记事本另存为 UTF-8 后重试。")


# ------------------------------------------------------------------
# 1. 审计
# ------------------------------------------------------------------
def audit(df):
    rep = {
        "n_rows": int(len(df)),
        "n_cols": int(df.shape[1]),
        "dup_all": int(df.duplicated().sum()),
        "missing": {c: int(df[c].isna().sum()) for c in df.columns},
        "n_station_raw": int(df["站点"].nunique()),
        "n_station_code": int(df["站代码"].nunique()),
        "station_raw_values": sorted(map(str, df["站点"].dropna().unique())),
        "surf_raw_values": sorted(map(str, df["地表类型"].dropna().unique())),
        "month_samples": [str(x) for x in df["月份"].dropna().astype(str).unique()[:8]],
        "unit_values": {c: sorted(map(str, df[c].dropna().unique())) for c in
                        ["风速_单位", "降水_单位", "输沙率_单位"] if c in df.columns},
        "numeric_as_text": int(df["风速"].map(lambda x: isinstance(x, str)).sum()),
        "source_file": os.path.basename(src_path) if "src_path" in globals() else "",
    }
    return rep


# ------------------------------------------------------------------
# 2. 规范化：站点名、地表类型、时间、数值文本
# ------------------------------------------------------------------
def to_number(x):
    """'3.2 m/s' → 3.2；无法解析 → NaN"""
    if pd.isna(x):
        return np.nan
    if isinstance(x, (int, float, np.number)):
        return float(x)
    s = re.sub(r"[^0-9\.\-]", "", str(x))
    try:
        return float(s) if s not in ("", "-", ".") else np.nan
    except ValueError:
        return np.nan


def parse_month(s):
    s = str(s).strip()
    m = re.match(r"^(\d{4})[-/年](\d{1,2})", s)
    if m:
        return pd.Period(f"{m.group(1)}-{int(m.group(2)):02d}", freq="M")
    return pd.NaT


def normalize(df):
    df = df.copy()
    df["月份"] = df["月份"].map(parse_month)
    df["站点"] = df["站点"].astype(str).str.strip().replace(STATION_MAP)
    df["站点"] = df["站点"].str.replace(r"站$", "", regex=True)   # 去掉“XX站”后缀
    df["地表类型"] = df["地表类型"].astype(str).str.strip().str.lower().replace(SURF_MAP)
    for c in ["风速", "降水", "气温", "土壤含水率", "植被覆盖度", "输沙率"]:
        df[c] = df[c].map(to_number)
    df["月份_str"] = df["月份"].astype(str)
    return df


# ------------------------------------------------------------------
# 3. 去重
# ------------------------------------------------------------------
def dedup(df):
    n0 = len(df)
    df = df.drop_duplicates()                                    # 完全重复
    df = df.sort_values(["站代码", "月份_str", "土壤含水率"],
                        na_position="last")
    df = df.drop_duplicates(subset=["站代码", "月份_str"], keep="first")  # 键重复
    df = df.sort_values(["站代码", "月份_str"]).reset_index(drop=True)
    df["row_id"] = np.arange(len(df))
    return df, n0 - len(df)


# ------------------------------------------------------------------
# 4. 单位统一
# ------------------------------------------------------------------
def unify_units(df, log):
    df = df.copy()
    if "风速_单位" not in df.columns:
        log["unit_converted"] = {"说明": "无单位列，抓取阶段已统一为 SI（m/s、mm、t·km⁻²·月⁻¹）"}
        log["unknown_units"] = {}
        return df
    for var, ucol in [("风速", "风速_单位"), ("降水", "降水_单位"), ("输沙率", "输沙率_单位")]:
        f = df.apply(lambda r: UNIT_FACTOR.get((var, str(r[ucol]).strip()), np.nan), axis=1)
        bad = f.isna() & df[var].notna()
        log.setdefault("unknown_units", {})[var] = int(bad.sum())
        df[var] = df[var] * f
    df["输沙率"] = df["输沙率"].round(2)
    log["unit_converted"] = {
        "风速_km/h": int((df["风速_单位"].str.strip() == "km/h").sum()),
        "降水_cm": int((df["降水_单位"].str.strip() == "cm").sum()),
        "输沙率_g/(cm·min)": int((df["输沙率_单位"].str.strip() == "g/(cm·min)").sum()),
    }
    return df


# ------------------------------------------------------------------
# 5. 物理阈值
# ------------------------------------------------------------------
def physical_bounds(df, log):
    df = df.copy()
    hits = {}
    for c, (lo, hi) in PHYS_BOUNDS.items():
        if c not in df:
            continue
        bad = df[c].notna() & ((df[c] < lo) | (df[c] > hi))
        hits[c] = int(bad.sum())
        df.loc[bad, c] = np.nan
    log["phys_bounds_hits"] = hits
    return df


# ------------------------------------------------------------------
# 6. 异常值：IQR + MAD 双准则 + 时序残差
# ------------------------------------------------------------------
def detect_outliers(df, cols, k_iqr=1.5, k_mad=3.5, log_vars=("降水", "输沙率")):
    """三准则异常检测：IQR、MAD 稳健 Z、时序残差 3σ；重尾变量先取 log1p 再定界"""
    res = {}
    for c in cols:
        x = df[c].dropna()
        if c in log_vars:
            v = np.log1p(np.clip(x, 0, None))
        else:
            v = x
        q1, q3 = v.quantile(0.25), v.quantile(0.75)
        iqr = q3 - q1
        med = v.median()
        mad = (v - med).abs().median()
        lim_iqr = (q1 - k_iqr * iqr, q3 + k_iqr * iqr)
        lim_mad = (med - k_mad * 1.4826 * mad, med + k_mad * 1.4826 * mad)
        if c in log_vars:
            lo_i, hi_i = np.expm1(lim_iqr[0]), np.expm1(lim_iqr[1])
            lo_m, hi_m = np.expm1(lim_mad[0]), np.expm1(lim_mad[1])
        else:
            lo_i, hi_i = lim_iqr
            lo_m, hi_m = lim_mad
        m_iqr = (df[c] < lo_i) | (df[c] > hi_i)
        m_mad = (df[c] < lo_m) | (df[c] > hi_m)
        r = df.groupby("站代码")[c].transform(
            lambda t: t - t.rolling(12, center=True, min_periods=6).median())
        sd = r.std()
        m_res = (r.abs() > 3 * sd) & r.notna()
        union = m_iqr | m_mad | m_res
        res[c] = dict(iqr=int(m_iqr.sum()), mad=int(m_mad.sum()), res=int(m_res.sum()),
                      union=int(union.sum()),
                      lim_iqr=[round(float(lo_i), 3), round(float(hi_i), 3)],
                      lim_mad=[round(float(lo_m), 3), round(float(hi_m), 3)],
                      n=int(x.shape[0]),
                      ratio=round(float(union.sum()) / max(x.shape[0], 1), 4),
                      log_space=c in log_vars)
    return res


def winsorize(df, cols, train_mask, p=0.01):
    """以训练期分位数截尾（避免用未来信息）"""
    df = df.copy()
    params = {}
    for c in cols:
        ref = df.loc[train_mask, c].dropna()
        lo, hi = ref.quantile(p), ref.quantile(1 - p)
        params[c] = [round(float(lo), 3), round(float(hi), 3)]
        df[c] = df[c].clip(lo, hi)
    return df, params


# ------------------------------------------------------------------
# 7. 缺失插补：5 种策略 + 掩码评估
# ------------------------------------------------------------------
def strat_mean(s, d):
    return s.fillna(d[s.name].mean())


def strat_median(s, d):
    return s.fillna(d[s.name].median())


def strat_linear(s, d):
    return s.interpolate(method="linear", limit_direction="both")


def strat_seasonal(s, d):
    """同站同月气候态（跨年同月均值）"""
    key = d.loc[s.index, ["站代码", "month"]]
    clim = d.groupby(["站代码", "month"])[s.name].mean()
    fill = pd.Series(
        [clim.get((k.站代码, k.month), np.nan) for k in key.itertuples()],
        index=s.index, dtype="float64")
    out = s.fillna(fill)
    return out.fillna(d[s.name].mean())


def strat_knn(s, d, k=5):
    """k 近邻：用同站相邻月份的其它变量标准化后找最近邻"""
    feats = ["风速", "降水", "气温", "植被覆盖度"]
    feats = [f for f in feats if f != s.name]
    X = d[feats].copy().astype(float)
    X = X.fillna(X.mean())                      # 特征内缺失用均值兜底，避免距离 NaN
    X = (X - X.mean()) / X.std(ddof=0).replace(0, 1)
    X["t"] = d["month_index"].astype(float) / 12.0
    known = s.notna()
    if known.sum() < k + 1:
        return s.fillna(d[s.name].median())
    out = s.copy()
    Xk = X[known].to_numpy()
    yk = s[known].to_numpy()
    for idx in s[~known].index:
        x = X.loc[idx].to_numpy()
        dist = np.sqrt(((Xk - x) ** 2).sum(axis=1))
        nn = np.argsort(dist)[:k]
        w = 1 / (dist[nn] + 1e-6)
        out.loc[idx] = float((yk[nn] * w).sum() / w.sum())
    return out


def eval_strategies(df, col, frac=0.1, seed=0):
    """人为挖洞 → 各策略插补 → RMSE/MAE"""
    rng = np.random.default_rng(seed)
    s = df.set_index("row_id")[col]
    obs = s.dropna()
    mask_idx = rng.choice(obs.index.values, size=int(len(obs) * frac), replace=False)
    s_hold = s.copy()
    s_hold.loc[mask_idx] = np.nan
    d = df.set_index("row_id").copy()
    d[col] = s_hold
    table = {}
    for name, fn in [("均值", strat_mean), ("中位数", strat_median), ("线性插值", strat_linear),
                     ("同月气候态", strat_seasonal), ("KNN(k=5)", strat_knn)]:
        filled = fn(d[col], d)
        pred = filled.loc[mask_idx].to_numpy()
        truth = s.loc[mask_idx].to_numpy()
        err = pred - truth
        table[name] = dict(RMSE=round(float(np.sqrt(np.mean(err ** 2))), 4),
                           MAE=round(float(np.mean(np.abs(err))), 4),
                           MAPE=round(float(np.mean(np.abs(err) / np.maximum(np.abs(truth), 1e-6)) * 100), 2))
    return table


def structural_fill(df, col, station, year):
    """结构性缺失（整年）修复：本站同月气候态 × 区域当年异常指数"""
    df = df.copy()
    d = df.copy()
    d["year"] = d["月份"].dt.year
    clim = d[d.year < year].groupby(["站代码", "month"])[col].mean()
    reg = d[(d.year == year)].groupby("month")[col].mean()
    reg0 = d[d.year < year].groupby("month")[col].mean()
    ratio = (reg / reg0).replace([np.inf, -np.inf], np.nan).fillna(1.0)
    m = (d["站代码"] == station) & (d["year"] == year) & d[col].isna()
    for idx in d[m].index:
        mo = d.at[idx, "month"]
        base = clim.get((station, mo), np.nan)
        if not np.isnan(base):
            d.at[idx, col] = base * float(ratio.get(mo, 1.0))
    return d


# ------------------------------------------------------------------
# 8. 特征工程
# ------------------------------------------------------------------
def build_features(df):
    d = df.copy()
    g = d.groupby("站代码")
    d["月份_sin"] = np.sin(2 * np.pi * d["month"] / 12)
    d["月份_cos"] = np.cos(2 * np.pi * d["month"] / 12)
    d["干燥度"] = d["降水"] / (d["气温"] + 10).clip(lower=1.0)       # de Martonne
    d["风蚀动力"] = d["风速"] ** 3
    d["水分抑制"] = np.exp(-0.22 * d["土壤含水率"])
    d["覆盖抑制"] = np.exp(-0.075 * d["植被覆盖度"])
    d["覆盖度年变化"] = d["植被覆盖度"] - g["植被覆盖度"].shift(12)
    d["输沙率_年滑和"] = g["输沙率"].transform(
        lambda s: s.rolling(12, min_periods=12).sum())
    for lag in (1, 3):
        d[f"风速_lag{lag}"] = g["风速"].shift(lag)
    d["治理年限"] = d["month_index"] / 12.0
    # 治理面积与投资属“情景参数”（决策变量），真实数据面板中不含；
    # 若提供则生成对数特征，否则跳过（不伪造观测）
    if "累计治理面积" in d.columns:
        d["log治理面积"] = np.log1p(d["累计治理面积"])
    if "月度投资" in d.columns:
        d["log投资"] = np.log1p(d["月度投资"])
    d["log输沙率"] = np.log1p(d["输沙率"])
    surf = d["地表类型"].copy()
    d = pd.get_dummies(d, columns=["地表类型"], prefix="地表", dtype=float)
    d["地表类型"] = surf          # 保留原始类别列，便于分组统计与建模时识别
    return d


# ------------------------------------------------------------------
# 9. 共线性 VIF
# ------------------------------------------------------------------
def vif_table(X):
    out = {}
    Xc = X.dropna()
    if Xc.shape[1] < 2:
        return out
    Xv = Xc.to_numpy(dtype=float)
    for j, c in enumerate(Xc.columns):
        y = Xv[:, j]
        A = np.delete(Xv, j, axis=1)
        A = np.column_stack([np.ones(len(A)), A])
        beta, *_ = np.linalg.lstsq(A, y, rcond=None)
        pred = A @ beta
        ss_res = ((y - pred) ** 2).sum()
        ss_tot = ((y - y.mean()) ** 2).sum()
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        out[c] = round(float(1 / max(1 - r2, 1e-6)), 2)
    return out


def drop_collinear(df, feats, thresh=10.0, core=None):
    """迭代 VIF 剔除：优先删“派生特征”，核心物理量在非核心伙伴存在时不被删"""
    core = list(core or [])
    feats = list(feats)
    dropped = []
    corr = df[feats].corr().abs()
    # 2.1 先删与核心变量完全共线的派生特征（|r|>0.98）
    for c in feats[:]:
        if c in core:
            continue
        for k in core:
            if k in corr.columns and corr.loc[c, k] > 0.98:
                feats.remove(c)
                dropped.append([c, f"与{k}相关系数{corr.loc[c, k]:.3f}>0.98"])
                break
    # 2.2 迭代 VIF
    while len(feats) > 2:
        v = vif_table(df[feats])
        if not v:
            break
        worst = max(v, key=v.get)
        if v[worst] <= thresh:
            break
        if worst in core:
            cand = [(x, corr.loc[worst, x]) for x in feats
                    if x != worst and x not in core]
            if not cand:
                break
            victim = max(cand, key=lambda t: t[1])[0]
            feats.remove(victim)
            dropped.append([victim, f"与核心变量{worst}共线(VIF={v[victim]:.1f})"])
        else:
            feats.remove(worst)
            dropped.append([worst, f"VIF={v[worst]:.1f}"])
    return feats, dropped, vif_table(df[feats])


# ------------------------------------------------------------------
# 10. 标准化方案对比
# ------------------------------------------------------------------
def scaling_compare(df, feats, train_mask):
    """三种标准化方案对比：偏度不变（线性变换的性质），故比较“离群点拉伸度”"""
    ref = df.loc[train_mask, feats]
    rows = {}
    for name in ["Z-score", "Robust(中位数/IQR)", "MinMax"]:
        if name == "Z-score":
            loc, scale = ref.mean(), ref.std(ddof=0).replace(0, 1)
        elif name.startswith("Robust"):
            loc = ref.median()
            scale = (ref.quantile(0.75) - ref.quantile(0.25)).replace(0, 1)
        else:
            loc, scale = ref.min(), (ref.max() - ref.min()).replace(0, 1)
        Z = (df[feats] - loc) / scale
        a = Z.abs()
        rows[name] = dict(
            max_abs=round(float(a.max().max()), 2),
            p99_abs=round(float(a.quantile(0.99).max()), 2),
            stretch=round(float(a.max().max() / max(a.quantile(0.99).max(), 1e-9)), 2),
            covers_neg=bool((Z.min().min() < 0)))
    return rows


def save_fig(fig, name):
    p = os.path.join(OUT_FIG, name)
    fig.tight_layout()
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p


def make_figures(raw, clean, stats, impute_cmp, vif_after, fig_paths):
    raw = raw.copy()
    for c in ["风速", "降水", "气温", "土壤含水率", "植被覆盖度", "输沙率"]:
        if c in raw:
            raw[c] = pd.to_numeric(raw[c], errors="coerce")
    # 图1 缺失率与记录数
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    miss = (raw.isna().mean() * 100).sort_values()
    miss = miss[miss > 0]
    ax[0].barh(miss.index, miss.values, color="#4C78A8")
    ax[0].set_xlabel("缺失率（%）")
    ax[0].set_title("(a) 各字段缺失率（原始数据）", fontsize=11)
    for y, v in enumerate(miss.values):
        ax[0].text(v + 0.2, y, f"{v:.1f}", va="center", fontsize=8)
    cnt = raw["站代码"].value_counts().sort_index()
    ax[1].bar(cnt.index, cnt.values, color="#F58518")
    ax[1].set_ylabel("记录数")
    ax[1].set_title("(b) 各站点记录数（原始数据，含重复）", fontsize=11)
    ax[1].tick_params(axis="x", rotation=45)
    fig_paths["fig1_数据审计"] = save_fig(fig, "fig1_数据审计.png")

    # 图2 异常值：清洗前后箱线
    cols = ["风速", "土壤含水率", "植被覆盖度", "输沙率"]
    fig, axes = plt.subplots(2, 4, figsize=(13, 6))
    for j, c in enumerate(cols):
        b = raw[c].dropna()
        a = clean[c].dropna()
        axes[0, j].boxplot(b, widths=0.55, patch_artist=True,
                           boxprops=dict(facecolor="#E45756", alpha=.65))
        axes[0, j].set_title(f"{c}·清洗前", fontsize=10)
        axes[1, j].boxplot(a, widths=0.55, patch_artist=True,
                           boxprops=dict(facecolor="#54A24B", alpha=.65))
        axes[1, j].set_title(f"{c}·清洗后", fontsize=10)
        axes[0, j].set_xticks([]); axes[1, j].set_xticks([])
    fig_paths["fig2_异常值对比"] = save_fig(fig, "fig2_异常值箱线图.png")

    # 图3 插补策略对比
    fig, axes = plt.subplots(1, len(impute_cmp), figsize=(6 * len(impute_cmp), 3.8))
    if len(impute_cmp) == 1:
        axes = [axes]
    for ax, (col, tab) in zip(axes, impute_cmp.items()):
        names = list(tab.keys())
        rmse = [tab[n]["RMSE"] for n in names]
        bars = ax.bar(names, rmse, color=["#BAB0AC"] * len(names))
        best = int(np.argmin(rmse))
        bars[best].set_color("#4C78A8")
        ax.set_title(f"{col}：五种插补策略 RMSE", fontsize=11)
        ax.set_ylabel("RMSE")
        ax.tick_params(axis="x", rotation=20)
        for i, v in enumerate(rmse):
            ax.text(i, v, f"{v:.3f}", ha="center", va="bottom", fontsize=8)
    fig_paths["fig3_插补对比"] = save_fig(fig, "fig3_插补策略对比.png")

    # 图4 分布：变换前后
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
    axes[0].hist(clean["输沙率"], bins=50, color="#E45756", alpha=.75)
    axes[0].set_title("(a) 输沙率（原始量纲，右偏）", fontsize=11)
    axes[0].set_xlabel("t/(km²·a)")
    axes[1].hist(clean["log输沙率"], bins=50, color="#4C78A8", alpha=.75)
    axes[1].set_title("(b) log(1+输沙率)（近似正态）", fontsize=11)
    axes[1].set_xlabel("log(1+x)")
    fig_paths["fig4_分布变换"] = save_fig(fig, "fig4_分布变换.png")

    # 图5 时序清洗示例（含结构性缺失修复）
    fig, axes = plt.subplots(2, 1, figsize=(11, 6.2))
    _miss = raw.groupby("站代码")["风速"].apply(lambda x: x.isna().sum()).sort_values(ascending=False)
    _top = list(_miss.index[:2])
    _name = raw.drop_duplicates("站代码").set_index("站代码")["站点"].to_dict()
    for ax, code in zip(axes, _top):
        st = _name.get(code, code)
        r = raw[raw["站代码"] == code].sort_values("月份")
        c = clean[clean["站代码"] == code].sort_values("月份")
        ax.plot(r["月份"].dt.to_timestamp(), r["风速"], "o", ms=3,
                color="#E45756", alpha=.6, label="原始观测（含 km/h 未换算、哨兵值、缺失）")
        ax.plot(c["月份"].dt.to_timestamp(), c["风速"], "-", lw=1.7,
                color="#4C78A8", label="清洗 + 插补后")
        _gap = c[c["风速"].isna()]["月份"]
        if len(_gap):
            _t0 = _gap.min().to_timestamp()
            _t1 = (_gap.max().to_timestamp() + pd.Timedelta(days=31))
            ax.axvspan(_t0, _t1, color="#F58518", alpha=.13)
            ax.text(_t0 + (_t1 - _t0) / 2, 18.4,
                    "缺测时段（已用同月气候态×区域异常修复）",
                    ha="center", fontsize=8, color="#8A4B00")
        ax.set_ylim(0, 20)
        ax.set_ylabel("月均风速（m/s）")
        ax.set_title(f"{st}站：月均风速的清洗与结构性缺失修复", fontsize=11)
        ax.legend(fontsize=8, loc="lower right", ncol=2, framealpha=.9)
    fig_paths["fig5_时序清洗"] = save_fig(fig, "fig5_时序清洗示例.png")

    # 图6 相关热图
    num = [c for c in ["风速", "风速日最大", "输沙势", "降水", "气温", "土壤含水率",
                       "NDVI", "植被覆盖度", "输沙率", "log治理面积"] if c in clean.columns]
    corr = clean[num].corr()
    fig, ax = plt.subplots(figsize=(7.4, 6))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(num))); ax.set_xticklabels(num, rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(len(num))); ax.set_yticklabels(num, fontsize=9)
    for i in range(len(num)):
        for j in range(len(num)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center",
                    fontsize=7.5, color="white" if abs(corr.iloc[i, j]) > 0.6 else "black")
    ax.set_title("清洗后主要变量的相关系数", fontsize=11)
    fig.colorbar(im, ax=ax, shrink=0.82)
    fig_paths["fig6_相关热图"] = save_fig(fig, "fig6_相关性热图.png")

    # 图7 VIF
    v = pd.Series(vif_after).sort_values()
    fig, ax = plt.subplots(figsize=(7.2, max(3.2, 0.32 * len(v))))
    colors = ["#E45756" if x > 10 else "#54A24B" for x in v.values]
    ax.barh(v.index, v.values, color=colors)
    ax.axvline(10, ls="--", color="#333333", lw=1)
    ax.set_xlabel("VIF（>10 视为强共线）")
    ax.set_title("特征共线性诊断（保留特征）", fontsize=11)
    for y, val in enumerate(v.values):
        ax.text(val + 0.2, y, f"{val:.1f}", va="center", fontsize=7.5)
    fig_paths["fig7_共线性"] = save_fig(fig, "fig7_共线性VIF.png")


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------
def main():
    os.makedirs(OUT_DATA, exist_ok=True)
    os.makedirs(OUT_FIG, exist_ok=True)
    stats, fig_paths = {}, {}

    fp_real = os.path.join(RAW_DIR, RAW_FILE)
    fp_old = os.path.join(RAW_DIR, RAW_FILE_FALLBACK)
    src_path = fp_real if os.path.exists(fp_real) else fp_old
    raw = load(src_path)
    raw = raw.rename(columns=RENAME)
    print("数据文件：", os.path.basename(src_path), raw.shape)
    stats["raw_audit"] = audit(raw)
    raw0 = raw.copy()
    raw0["month"] = raw0["月份"].astype(str).str[:7]
    n_raw = len(raw0)

    # 2 规范化
    df = normalize(raw)
    raw_parsed = df.copy()          # 保留“解析后、未清洗”的版本，用于前后对比图
    df["month"] = df["月份"].dt.month
    df["month_index"] = ((df["月份"].dt.year - 2015) * 12 + df["月份"].dt.month - 1)

    # 3 去重
    df, n_dup = dedup(df)
    stats["dedup"] = {"raw_rows": int(n_raw), "removed": int(n_dup), "kept": int(len(df))}

    # 4 单位统一
    log = {}
    df = unify_units(df, log)
    stats["units"] = log

    # 5 物理阈值
    log2 = {}
    df = physical_bounds(df, log2)
    stats["physical"] = log2["phys_bounds_hits"]

    # 6 异常值检测（在插补前，基于有效观测）
    num_check = ["风速", "降水", "气温", "土壤含水率", "植被覆盖度", "输沙率"]
    stats["outliers"] = detect_outliers(df, num_check, log_vars=("降水", "输沙率"))

    # 7 掩码评估插补策略
    impute_cmp = {}
    for col in ["土壤含水率", "植被覆盖度", "风速"]:
        impute_cmp[col] = eval_strategies(df, col, frac=0.1, seed=1)
    stats["impute_compare"] = impute_cmp
    best = {c: min(t, key=lambda k: t[k]["RMSE"]) for c, t in impute_cmp.items()}
    stats["impute_best"] = best

    # 8 结构性缺失修复（自动检测：同一站点连续 ≥6 个月缺测）
    struct_hits = []
    for var in ["风速", "土壤含水率", "植被覆盖度"]:
        for code, sub in df.groupby("站代码"):
            miss = sub.sort_values("月份")[var].isna().to_numpy()
            run = best = 0
            for m in miss:
                run = run + 1 if m else 0
                best = max(best, run)
            if best >= 6:
                yr = int(sub.sort_values("月份")["月份"].dt.year.mode().iloc[0])
                df = structural_fill(df, var, code, yr)
                struct_hits.append({"station": code, "var": var, "year": yr,
                                    "consecutive_missing": int(best)})
    stats["structural_gap"] = struct_hits

    # 9 截尾（训练期分位）+ 插补
    train_mask = df["月份"] < pd.Period("2023-01", freq="M")
    df, wins = winsorize(df, num_check, train_mask, p=0.01)
    stats["winsorize"] = wins

    # 线性插值（时序）+ 同月气候态兜底
    for col in ["风速", "降水", "气温", "土壤含水率", "植被覆盖度"]:
        df[col] = df.groupby("站代码")[col].transform(
            lambda s: s.interpolate(method="linear", limit_direction="both"))
        df[col] = strat_seasonal(df[col], df)
    df["输沙率"] = df["输沙率"].fillna(df["输沙率"].median())

    # 10 面板补齐
    full = pd.MultiIndex.from_product(
        [sorted(df["站代码"].unique()), pd.period_range("2015-01", "2024-12", freq="M")],
        names=["站代码", "月份"])
    panel = df.set_index(["站代码", "月份"]).reindex(full)
    panel["月份_str"] = panel.index.get_level_values("月份").astype(str)
    panel = panel.reset_index()
    panel["month"] = panel["月份"].dt.month
    panel["month_index"] = ((panel["月份"].dt.year - 2015) * 12 + panel["月份"].dt.month - 1)
    panel["year"] = panel["月份"].dt.year
    stats["panel_fill"] = {"rows": int(len(panel)),
                           "added": int(len(panel) - len(df)),
                           "still_missing": {c: int(panel[c].isna().sum()) for c in NUM_COLS}}

    # 补：站点名/地表类型（面板补齐产生的空行用前向填充）
    for c in ["站点", "地表类型"]:
        panel[c] = panel.groupby("站代码")[c].transform(lambda s: s.ffill().bfill())
    panel = build_features(panel)
    stats["missing_after"] = {c: int(panel[c].isna().sum()) for c in panel.columns
                              if panel[c].isna().any()}

    # 11 输入特征集
    feats = ["风速", "降水", "气温", "土壤含水率", "植被覆盖度", "干燥度",
             "月份_sin", "月份_cos", "覆盖度年变化", "log治理面积", "治理年限",
             "风速_lag1", "风速_lag3"]
    feats = [f for f in feats if f in panel.columns]
    CORE = ["风速", "降水", "气温", "土壤含水率", "植被覆盖度"]
    feats, dropped, vif_after = drop_collinear(
        panel.dropna(subset=feats), feats, thresh=10.0, core=CORE)
    stats["collinear_dropped"] = [[a, b] for a, b in dropped]
    stats["vif_final"] = vif_after

    # 12 标准化
    tr = panel["月份"] < pd.Period("2023-01", freq="M")
    stats["scaling_compare"] = scaling_compare(panel, feats, tr)
    ref = panel.loc[tr, feats]
    loc, scale = ref.median(), (ref.quantile(0.75) - ref.quantile(0.25)).replace(0, 1)
    Z = (panel[feats] - loc) / scale
    for c in feats:
        panel[f"z_{c}"] = Z[c]
    stats["scaler_params"] = {c: [round(float(loc[c]), 4), round(float(scale[c]), 4)]
                              for c in feats}

    # 13 划分
    train = panel[panel["月份"] < pd.Period("2023-01", freq="M")].copy()
    test = panel[panel["月份"] >= pd.Period("2023-01", freq="M")].copy()
    stats["split"] = {"train_rows": int(len(train)), "test_rows": int(len(test)),
                      "train_period": f"{train['月份'].min()}~{train['月份'].max()}",
                      "test_period": f"{test['月份'].min()}~{test['月份'].max()}"}

    # 14 输出
    keep = ["站代码", "站点", "月份_str", "year", "month", "month_index", "地表类型",
            "经度", "纬度", "风速", "风速日最大", "降水", "气温",
            "土壤含水率", "土壤含水率_0_100cm", "NDVI", "植被覆盖度",
            "输沙率", "输沙势", "log输沙率"]
    keep = [c for c in keep if c in panel.columns]
    panel[keep].to_csv(os.path.join(OUT_DATA, "02_panel_clean.csv"), index=False, encoding="utf-8-sig")
    feat_out = ["站代码", "月份_str"] + feats + [f"z_{c}" for c in feats]
    panel[feat_out].to_csv(os.path.join(OUT_DATA, "03_features.csv"), index=False, encoding="utf-8-sig")
    train[feat_out + ["输沙率", "log输沙率"]].to_csv(
        os.path.join(OUT_DATA, "04_train.csv"), index=False, encoding="utf-8-sig")
    test[feat_out + ["输沙率", "log输沙率"]].to_csv(
        os.path.join(OUT_DATA, "05_test.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame([{"特征": c, "中位数": loc[c], "IQR": scale[c]} for c in feats]).to_csv(
        os.path.join(OUT_DATA, "06_scaler_params.csv"), index=False, encoding="utf-8-sig")

    # 15 图
    make_figures(raw_parsed, panel, stats, impute_cmp, vif_after, fig_paths)
    stats["figures"] = fig_paths

    # 16 缺失/异常前后
    stats["missing_before_after"] = {
        c: [int(raw[c].isna().sum()) if c in raw else 0, int(panel[c].isna().sum())]
        for c in ["风速", "降水", "气温", "土壤含水率", "植被覆盖度", "输沙率"]}
    stats["n_features"] = len(feats)
    stats["features"] = feats

    with open(STATS_PATH, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1, default=str)

    print("=" * 60)
    print("原始记录：", stats["raw_audit"]["n_rows"], "→ 去重后：", stats["dedup"]["kept"],
          "→ 面板：", stats["panel_fill"]["rows"])
    print("缺失（前→后）：", stats["missing_before_after"])
    print("异常值检出：", {k: v["union"] for k, v in stats["outliers"].items()})
    print("最优插补策略：", best)
    print("共线剔除：", stats["collinear_dropped"])
    print("保留特征数：", len(feats), "训练/测试：", stats["split"])
    print("输出目录：", OUT_DATA)
    print("=" * 60)


if __name__ == "__main__":
    main()
