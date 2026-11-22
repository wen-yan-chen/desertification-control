# -*- coding: utf-8 -*-
"""
preprocess_v7.py —— 治沙工程（2026 CQU_MCM B 题）数据预处理主程序（Python 版）

运行环境
    Python 3.8–3.11（Anaconda 默认环境即可）
    pip install pandas numpy matplotlib openpyxl

输入
    Data/v7/processed/panel_monthly_raw.csv
    —— 由 v7_fetch.py（抓取）+ v7_finalize_fetch.py（合并）生成；
       若你只有原始 JSON，请先跑那两个脚本；本脚本只负责"清洗与派生"。

输出
    Data/v7/processed/panel_monthly_clean.csv     清洗后的建模面板
    Data/v7/processed/panel_monthly_clean.xlsx    同内容 Excel（便于核对）
    Data/v7/processed/qc_summary.json             质量审计汇总
    Figures/v7_init_test/pre_before.png / pre_after.png     预处理前后可视化

运行
    python preprocess_v7.py
"""
from __future__ import annotations

import json
import os
import sys
import traceback

import numpy as np
import pandas as pd

# =============================================================================
# ========== 1. 路径配置（学生只需改这一块） ==================================
# =============================================================================
# Windows 示例：BASE = r"D:\CQU\大三上\比赛\美赛\第一次校赛"
# macOS/Linux 示例：BASE = "/Users/xxx/Desktop/desertification"
# 注意：路径中尽量避免中文与空格；若必须使用，请保持原始字符串 r"..." 写法。
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_CSV = os.path.join(BASE, "Data", "v7", "processed", "panel_monthly_raw.csv")
OUT_DIR = os.path.join(BASE, "Data", "v7", "processed")
FIG_DIR = os.path.join(BASE, "Figures", "v7_init_test")
OUT_CSV = os.path.join(OUT_DIR, "panel_monthly_clean.csv")
OUT_XLSX = os.path.join(OUT_DIR, "panel_monthly_clean.xlsx")
OUT_JSON = os.path.join(OUT_DIR, "qc_summary.json")

TRAIN_YEARS = (2015, 2022)          # 训练期：所有统计量只在这段上拟合
SITES = {                            # 站点经纬度（Hargreaves 公式需要纬度）
    "YT": ("于田", 36.85, 81.67), "MF": ("民丰", 37.06, 82.68),
    "QM": ("且末", 38.13, 85.53), "RQ": ("若羌", 39.02, 88.17),
    "KEL": ("库尔勒", 41.76, 86.15), "YL": ("尉犁", 41.34, 86.26),
    "ALE": ("阿拉尔", 40.55, 81.28), "XT": ("肖塘", 38.83, 84.02),
    "TZ": ("塔中", 38.97, 83.65),
}
# =============================================================================

# ------------------------------------------------------------------ 常量
NDVI_SOIL, NDVI_VEG = 0.05, 0.85     # 像元二分端元
Z0, KAPPA, C_L, RHO, G = 0.001, 0.40, 6.7, 1.225, 9.81
U_T = 5.0                            # 起沙阈值 m/s @10m
COLS_KEY = ["T2M", "PRECTOTCORR", "GWETROOT", "WS10M_MAX", "ndvi_mvc_qa"]


def banner(text: str) -> None:
    print("\n" + "=" * 78)
    print(text)
    print("=" * 78)


# ------------------------------------------------------------------ 读取
def load_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"找不到输入文件：{path}\n"
            "排查：① 路径是否写错（Windows 用双反斜杠或 r\"...\"）；\n"
            "      ② 是否忘记运行 v7_fetch.py / v7_finalize_fetch.py；\n"
            "      ③ 文件是否被 Excel 占用（关闭后重试）。")
    try:
        df = pd.read_csv(path, parse_dates=["date"])
    except UnicodeDecodeError:
        df = pd.read_csv(path, parse_dates=["date"], encoding="gbk")
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"读取失败：{exc}\n请检查文件是否完整、是否被占用。") from exc
    missing_cols = [c for c in COLS_KEY if c not in df.columns]
    if missing_cols:
        raise ValueError(f"缺少必要字段 {missing_cols}；当前字段：{list(df.columns)[:20]}...")
    df = df.sort_values(["site", "date"]).reset_index(drop=True)
    print(f"读入 {df.shape[0]} 行 × {df.shape[1]} 列，站点 {df['site'].nunique()} 个，"
          f"时间 {df['date'].min():%Y-%m} ~ {df['date'].max():%Y-%m}")
    return df


# ------------------------------------------------------------------ 审计
def audit_before(df: pd.DataFrame) -> dict:
    rep = {}
    rep["shape"] = list(df.shape)
    rep["duplicates_site_month"] = int(df.duplicated(["site", "date"]).sum())
    rep["missing"] = {c: {"n": int(df[c].isna().sum()),
                          "pct": round(100 * float(df[c].isna().mean()), 2)}
                      for c in COLS_KEY}
    rep["range_violation"] = {
        "Tmin>Tmean": int((df["T2M_MIN"] > df["T2M"]).sum()) if "T2M_MIN" in df else 0,
        "P<0": int((df["PRECTOTCORR"] < 0).sum()),
        "GWET∉[0,1]": int(((df["GWETROOT"] < 0) | (df["GWETROOT"] > 1)).sum()),
    }
    print("缺失：", json.dumps(rep["missing"], ensure_ascii=False))
    return rep


# ------------------------------------------------------------------ 单位与口径
def fix_units(df: pd.DataFrame) -> pd.DataFrame:
    """POWER 月度产品给的是日均值 → 月总量必须乘当月天数"""
    df["days_in_month"] = df["date"].dt.days_in_month
    df["P_mm"] = df["PRECTOTCORR"] * df["days_in_month"]
    df["SW_MJ"] = df["ALLSKY_SFC_SW_DWN"] * df["days_in_month"]
    df["EVLAND_mm"] = df["EVLAND"] * df["days_in_month"]
    return df


def extraterrestrial_radiation(lat_deg: float, doy: np.ndarray) -> np.ndarray:
    """FAO-56 天文辐射 Ra，单位 MJ m-2 d-1"""
    phi = np.deg2rad(lat_deg)
    dr = 1 + 0.033 * np.cos(2 * np.pi * doy / 365)
    delta = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(delta), -1, 1))
    return (24 * 60 / np.pi) * 0.0820 * dr * (
        ws * np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.sin(ws))


def hargreaves(df: pd.DataFrame) -> np.ndarray:
    """ET0 = 0.0023 * 0.408 * Ra * (T+17.8) * sqrt(Tmax-Tmin) * 天数"""
    out = np.full(len(df), np.nan)
    for i, row in enumerate(df.itertuples(index=False)):
        name, lat, _ = SITES[row.site]
        doy0 = int(pd.Timestamp(year=row.date.year, month=row.date.month, day=1).dayofyear)
        ra = extraterrestrial_radiation(lat, doy0 + np.arange(row.days_in_month)).mean()
        tr = row.T2M_MAX - row.T2M_MIN
        if np.isfinite(tr) and tr > 0:
            out[i] = 0.0023 * 0.408 * ra * (row.T2M + 17.8) * np.sqrt(tr) * row.days_in_month
    return out


# ------------------------------------------------------------------ 质控与派生
def modis_qa(df: pd.DataFrame) -> pd.DataFrame:
    """像元二分反演覆盖度；同时保留"未质控"口径用于对比"""
    df["V_pct"] = np.clip((df["ndvi_mvc_qa"] - NDVI_SOIL) / (NDVI_VEG - NDVI_SOIL), 0, 1) * 100
    df["V_unqa"] = np.clip((df["ndvi_mvc"] - NDVI_SOIL) / (NDVI_VEG - NDVI_SOIL), 0, 1) * 100
    return df


def erosion_index(df: pd.DataFrame) -> np.ndarray:
    """Lettau 单位宽度通量 → 站内归一的无量纲侵蚀指数"""
    us = KAPPA * df["WS10M_MAX"] / np.log(10 / Z0)
    ust = KAPPA * U_T / np.log(10 / Z0)
    q = np.clip(C_L * RHO / G * us ** 2 * (us - ust), 0, None)
    base = float(np.nanmean(q[df["date"].dt.year.between(*TRAIN_YEARS)]))
    return q / base if base > 0 else q


def normalize_water(df: pd.DataFrame) -> pd.DataFrame:
    """根区湿度按训练期 5%/95% 分位线性归一"""
    tr = df["date"].dt.year.between(*TRAIN_YEARS)
    lo, hi = np.nanpercentile(df.loc[tr, "GWETROOT"], [5, 95])
    df["W"] = np.clip((df["GWETROOT"] - lo) / (hi - lo), 0, 1)
    return df


# ------------------------------------------------------------------ 缺失填补
def impute(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """站内线性插值（≤2 月）→ 训练期同月气候态；逐变量留痕"""
    log = {}
    for col in ["V_pct", "W"]:
        n0 = int(df[col].isna().sum())
        if n0 == 0:
            continue
        filled = df[col].copy()
        for site in df["site"].unique():
            idx = df["site"] == site
            s = df.loc[idx, col].copy()
            s = s.interpolate(method="linear", limit=2, limit_direction="both")
            tr = df.loc[idx & df["date"].dt.year.between(*TRAIN_YEARS)]
            clim = tr.groupby(tr["date"].dt.month)[col].mean()
            still = s.isna()
            if still.any():
                s.loc[still] = df.loc[s[still].index, "date"].dt.month.map(clim).values
            filled.loc[idx] = s.values
        df[col] = filled
        log[col] = {"missing_before": n0, "missing_after": int(df[col].isna().sum())}
        print(f"  {col}：{n0} → {int(df[col].isna().sum())}")
    return df, log


def dynamic_v(df: pd.DataFrame) -> pd.DataFrame:
    """动态端元的覆盖度（训练期 5%/95% 分位），用于端元敏感性"""
    df["V_dyn"] = np.nan
    for site, g in df.groupby("site"):
        tr = g[g["date"].dt.year.between(*TRAIN_YEARS)]
        lo, hi = np.nanpercentile(tr["ndvi_mvc"], [5, 95])
        df.loc[g.index, "V_dyn"] = np.clip((g["ndvi_mvc"] - lo) / (hi - lo), 0, 1) * 100
    return df


def dust_days(df: pd.DataFrame) -> pd.DataFrame:
    """由 POWER 日最大风速统计各阈值下的沙尘事件日数（任务三的 λ 锚点）"""
    raw_dir = os.path.join(BASE, "Data", "v7", "raw")
    for th in (8, 10, 12, 15):
        df[f"dust_days_{th}"] = np.nan
    for site in df["site"].unique():
        fp = os.path.join(raw_dir, f"power_daily_{site}.json")
        if not os.path.exists(fp):
            print(f"  [提示] 缺少 {fp}，dust_days 留空")
            continue
        with open(fp, encoding="utf-8") as f:
            d = json.load(f)["properties"]["parameter"]["WS10M_MAX"]
        s = pd.Series(d)
        s.index = pd.to_datetime(s.index, format="%Y%m%d")
        per = s.index.to_period("M")
        for th in (8, 10, 12, 15):
            cnt = (s >= th).groupby(per).sum()
            for ym, v in cnt.items():
                mask = (df["site"] == site) & (df["date"].dt.to_period("M") == ym)
                df.loc[mask, f"dust_days_{th}"] = int(v)
    return df

def flag_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """稳健 z>3.5 只打标记，不删除（极端降水/沙尘是任务三的输入）"""
    for col in ["P_mm", "WS10M_MAX", "GWETROOT"]:
        s = df[col]
        med, mad = float(np.nanmedian(s)), float(np.nanmedian(np.abs(s - np.nanmedian(s))))
        df[f"flag_{col}"] = (0.6745 * (s - med) / mad).abs() > 3.5 if mad > 0 else False
    return df


# ------------------------------------------------------------------ 可视化
def plot_before_after(raw: pd.DataFrame, clean: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    os.makedirs(FIG_DIR, exist_ok=True)

    # 图 1：缺失率热图（前）
    cols = ["T2M", "PRECTOTCORR", "WS10M_MAX", "GWETROOT", "ndvi_mvc_qa"]
    m = raw.groupby("site")[cols].apply(lambda g: g.isna().mean() * 100).T
    fig, ax = plt.subplots(figsize=(7.6, 3.6))
    im = ax.imshow(m.values, aspect="auto", cmap="OrRd", vmin=0, vmax=max(5, m.values.max()))
    ax.set_xticks(range(m.shape[1]), m.columns)
    ax.set_yticks(range(m.shape[0]), m.index)
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            if m.values[i, j] > 0.05:
                ax.text(j, i, f"{m.values[i, j]:.1f}", ha="center", va="center", fontsize=8,
                        color="white" if m.values[i, j] > 5 else "#333")
    ax.set_title("预处理前：各变量缺失率（%）")
    ax.grid(False)
    fig.colorbar(im, ax=ax, shrink=0.85)
    fig.savefig(os.path.join(FIG_DIR, "pre_before.png"))
    plt.close(fig)

    # 图 2：清洗后的覆盖度与水分（后）
    s = clean[clean["site"] == "YT"].sort_values("date")
    fig, axes = plt.subplots(2, 1, figsize=(9.2, 5.2), sharex=True)
    axes[0].plot(s["date"], s["V_unqa"], ".", ms=3, color="#dd6b20", alpha=0.6,
                 label="未质控（NDVI×100 近似）")
    axes[0].plot(s["date"], s["V_pct"], "-", lw=1.2, color="#2b6cb0", label="质控+派生后的覆盖度")
    axes[0].set_ylabel("覆盖度 / %")
    axes[0].legend(fontsize=8)
    axes[0].set_title("预处理后：于田站覆盖度与水分状态")
    axes[1].plot(s["date"], s["W"], color="#276749", lw=1.2)
    axes[1].set_ylabel("W（0—1）")
    fig.savefig(os.path.join(FIG_DIR, "pre_after.png"))
    plt.close(fig)
    print(f"  图件已保存：{FIG_DIR}")


# ------------------------------------------------------------------ 主流程
def main() -> None:
    banner("步骤 0：读取原始面板")
    df = load_data(INPUT_CSV)

    banner("步骤 1：质量审计（预处理前）")
    rep_before = audit_before(df)

    banner("步骤 2：单位与聚合口径修正")
    df = fix_units(df)
    df["ET0_hargreaves"] = hargreaves(df)
    print("  降水 mm/d → mm/月；辐射 MJ/m2/d → MJ/m2/月；ET0 由 Hargreaves 计算（含 0.408 换算）")

    banner("步骤 3：遥感质控与覆盖度派生")
    df = modis_qa(df)
    print(f"  覆盖度有效值 {df['V_pct'].notna().sum()}/{len(df)}；"
          f"未质控口径均值 {df['V_unqa'].mean():.2f}%，质控后 {df['V_pct'].mean():.2f}%")

    banner("步骤 4：派生变量")
    df["E"] = erosion_index(df)
    df = normalize_water(df)
    df["AI"] = df["P_mm"] / df["ET0_hargreaves"].replace(0, np.nan)
    df = dynamic_v(df)
    df = dust_days(df)
    print(f"  侵蚀指数 E：中位 {np.nanmedian(df['E']):.3f}，最大 {np.nanmax(df['E']):.2f}")
    print(f"  水分状态 W：被压到边界 0 的比例 {100*(df['W']<=0).mean():.2f}%")

    banner("步骤 5：缺失填补（线性≤2 月 → 训练期同月气候态）")
    df, imp_log = impute(df)

    banner("步骤 6：异常值标记（只标记不删除）")
    df = flag_outliers(df)
    for c in ["P_mm", "WS10M_MAX", "GWETROOT"]:
        print(f"  {c}：标记 {int(df[f'flag_{c}'].sum())} 个月")

    banner("步骤 7：保存结果")
    os.makedirs(OUT_DIR, exist_ok=True)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print(f"  CSV：{OUT_CSV}（{os.path.getsize(OUT_CSV)/1024:.0f} KB）")
    try:
        df.to_excel(OUT_XLSX, index=False)
        print(f"  XLSX：{OUT_XLSX}（{os.path.getsize(OUT_XLSX)/1024:.0f} KB）")
    except Exception as exc:  # noqa: BLE001
        print(f"  [警告] 写 Excel 失败（可能未装 openpyxl）：{exc}")

    banner("步骤 8：完整性校验")
    checks = {
        "行数": len(df),
        "站点数": int(df["site"].nunique()),
        "月份数": int(df["date"].nunique()),
        "重复主键": int(df.duplicated(["site", "date"]).sum()),
        "V_pct 仍缺失": int(df["V_pct"].isna().sum()),
        "W 越界": int(((df["W"] < 0) | (df["W"] > 1)).sum()),
        "V 越界": int(((df["V_pct"] < 0) | (df["V_pct"] > 100)).sum()),
    }
    print(json.dumps(checks, ensure_ascii=False, indent=1))
    assert checks["V_pct 仍缺失"] == 0 and checks["W 越界"] == 0 and checks["V 越界"] == 0

    banner("步骤 9：处理前后对比（前 10 行 / 后 5 行）")
    show = ["site", "date", "P_mm", "GWETROOT", "W", "ndvi_mvc_qa", "V_pct", "E"]
    print(df[show].head(10).to_string(index=False))
    print("...")
    print(df[show].tail(5).to_string(index=False))

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"before": rep_before, "imputation": imp_log, "checks": checks},
                  f, ensure_ascii=False, indent=1)

    banner("步骤 10：可视化（预处理前后）")
    plot_before_after(pd.read_csv(INPUT_CSV, parse_dates=["date"]), df)

    banner("完成：所有产物已写入")
    print(f"  {OUT_CSV}\n  {OUT_XLSX}\n  {OUT_JSON}\n  {FIG_DIR}\\pre_before.png, pre_after.png")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        print("\n[运行失败] 错误详情如下，请按提示排查：")
        traceback.print_exc()
        sys.exit(1)

