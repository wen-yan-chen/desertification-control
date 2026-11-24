# -*- coding: utf-8 -*-
"""
v7_clean.py —— 数据质量审计 + 预处理流水线（2026-11-10 版）

输入：Data/v7/raw/ 下由 v7_fetch.py 采集的原始响应（只读，不修改）
输出：
  Data/v7/processed/panel_monthly_raw.csv     合并后、未清洗的"脏"面板（保留供审计）
  Data/v7/processed/panel_monthly_clean.csv   清洗 + 派生后的建模面板
  Data/v7/processed/features_{train,test}.csv 建模特征表（训练期拟合的标准化参数）
  Data/v7/processed/soil_profile.csv          站点土壤剖面与有效持水量
  Data/v7/processed/norm_params.json          所有"只在训练期拟合"的参数
  Results/v7/qc_report.json                   全量质量审计数字
  Results/v7/tab_*.csv                        报告用表格
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "Data", "v7", "raw")
OUT = os.path.join(BASE, "Data", "v7", "processed")
RES = os.path.join(BASE, "Results", "v7")
os.makedirs(OUT, exist_ok=True)
os.makedirs(RES, exist_ok=True)

Y0, Y1 = 2015, 2025
TRAIN = (2015, 2022)
SITES = [
    ("YT", "于田", 36.85, 81.67, "南缘锁边区段"),
    ("MF", "民丰", 37.06, 82.68, "南缘锁边区段"),
    ("QM", "且末", 38.13, 85.53, "南缘锁边区段"),
    ("RQ", "若羌", 39.02, 88.17, "东南缘锁边区段"),
    ("KEL", "库尔勒", 41.76, 86.15, "北缘"),
    ("YL", "尉犁", 41.34, 86.26, "北缘"),
    ("ALE", "阿拉尔", 40.55, 81.28, "西北缘"),
    ("XT", "肖塘", 38.83, 84.02, "公路走廊"),
    ("TZ", "塔中", 38.97, 83.65, "腹地对照"),
]
CODES = [s[0] for s in SITES]
NAME = {s[0]: s[1] for s in SITES}
ROLE = {s[0]: s[3] for s in SITES}
LAT = {s[0]: s[2] for s in SITES}

MONTHS = pd.period_range(f"{Y0}-01", f"{Y1}-12", freq="M")
N_MONTH = len(MONTHS)

P_FILL = -999.0
NDVI_FILL = -3000
Z0 = 0.001          # m
KAPPA = 0.40
C_LETTAU = 6.7
RHO = 1.225
G = 9.81
U_T_THRESH = 5.0    # m/s @10m 起沙阈值（情景假设，敏感性另测）

REPORT: dict = {"meta": {}, "sources": {}, "checks": {}, "tables": {}}


# --------------------------------------------------------------------- 工具
def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def load_power_monthly(code):
    d = jload(os.path.join(RAW, f"power_monthly_{code}.json"))
    par = d["properties"]["parameter"]
    ks = [k for k in par["T2M"].keys() if not k.endswith("13")]
    out = pd.DataFrame({"ym": ks})
    out["date"] = pd.to_datetime(out["ym"], format="%Y%m")
    for k in par:
        out[k] = [par[k][i] for i in ks]
    num = out.columns.difference(["ym", "date"])
    out[num] = out[num].replace([P_FILL], np.nan)
    out[num] = out[num].mask(out[num] <= -990)
    out["site"] = code
    out["units"] = json.dumps({k: v.get("units") for k, v in d["parameters"].items()},
                              ensure_ascii=False)
    return out.drop(columns=["units"])


def load_power_daily(code):
    d = jload(os.path.join(RAW, f"power_daily_{code}.json"))
    par = d["properties"]["parameter"]
    ks = sorted(par["T2M"].keys())
    out = pd.DataFrame({"ymd": ks})
    out["date"] = pd.to_datetime(out["ymd"], format="%Y%m%d")
    for k in par:
        out[k] = [par[k][i] for i in ks]
    num = out.columns.difference(["ymd", "date"])
    out[num] = out[num].mask(out[num] <= -990)
    out["site"] = code
    return out


def agg_daily_to_month(d: pd.DataFrame) -> pd.DataFrame:
    """由日值重算月值，用于核验 POWER 月度产品的聚合口径"""
    d = d.copy()
    d["ym"] = d["date"].dt.to_period("M")
    d["days"] = d["date"].dt.days_in_month
    g = d.groupby("ym")
    out = pd.DataFrame({
        "P_sum_daily": g["PRECTOTCORR"].sum(min_count=1),
        "T_mean_daily": g["T2M"].mean(),
        "Tmax_daily": g["T2M_MAX"].mean(),
        "Tmin_daily": g["T2M_MIN"].mean(),
        "WS_mean_daily": g["WS10M"].mean(),
        "WSmax_daily": g["WS10M_MAX"].mean(),
        "WS_gust_max": g["WS10M_MAX"].max(),
        "GWET_mean_daily": g["GWETROOT"].mean(),
        "SW_sum_daily": g["ALLSKY_SFC_SW_DWN"].sum(min_count=1),
        "n_days": g["T2M"].count(),
    })
    out["P_days"] = g["days"].first()
    return out.reset_index()


def load_modis(code, tag):
    recs = jload(os.path.join(RAW, f"modis_{code}_{tag}.json"))
    rows = []
    for r in recs:
        v = np.array(r["data"], dtype=float) if r.get("data") else np.array([np.nan])
        if tag == "NDVI":
            v = v / 10000.0
            v = np.where(v <= -0.29, np.nan, v)   # 填充 -3000 → -0.3
            v = np.where((v < -0.2) | (v > 1.0), np.nan, v)
        else:
            v = np.where(v < 0, np.nan, v)        # QA 填充值
        ok = v[~np.isnan(v)]
        rows.append({
            "modis_date": r["modis_date"],
            "date": pd.to_datetime(r["calendar_date"]),
            "px_valid": int(ok.size),
            "px_total": int(v.size),
            "mean": float(np.mean(ok)) if ok.size else np.nan,
            "median": float(np.median(ok)) if ok.size else np.nan,
            "std": float(np.std(ok, ddof=1)) if ok.size > 1 else np.nan,
            "q90": float(np.percentile(ok, 90)) if ok.size else np.nan,
        })
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    df["site"] = code
    df["tag"] = tag
    return df


def load_era5(code):
    d = jload(os.path.join(RAW, f"era5land_{code}.json"))
    day = d["daily"]
    df = pd.DataFrame(day)
    df["date"] = pd.to_datetime(df["time"])
    df = df.drop(columns=["time"])
    # 单位统一：km/h → m/s
    for c in ["wind_speed_10m_max", "wind_gusts_10m_max"]:
        df[c] = df[c] / 3.6
    df["site"] = code
    return df


def era5_monthly(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ym"] = df["date"].dt.to_period("M")
    g = df.groupby("ym")
    out = pd.DataFrame({
        "era_sm_0_7": g["soil_moisture_0_to_7cm_mean"].mean(),
        "era_sm_7_28": g["soil_moisture_7_to_28cm_mean"].mean(),
        "era_sm_28_100": g["soil_moisture_28_to_100cm_mean"].mean(),
        "era_sm_100_255": g["soil_moisture_100_to_255cm_mean"].mean(),
        "era_et0_mm": g["et0_fao_evapotranspiration"].sum(min_count=1),
        "era_P_mm": g["precipitation_sum"].sum(min_count=1),
        "era_T": g["temperature_2m_mean"].mean(),
        "era_Tmax": g["temperature_2m_max"].mean(),
        "era_Tmin": g["temperature_2m_min"].mean(),
        "era_ws_max": g["wind_speed_10m_max"].mean(),
        "era_gust": g["wind_gusts_10m_max"].mean(),
        "era_sw_MJ": g["shortwave_radiation_sum"].sum(min_count=1),
        "era_vpd": g["vapour_pressure_deficit_max"].mean(),
        "era_rh": g["relative_humidity_2m_mean"].mean(),
        "era_days": g["temperature_2m_mean"].count(),
    }).reset_index()
    # 0–100 cm 厚度加权根区含水量（7,21,72 cm 层厚）
    w = np.array([7, 21, 72], dtype=float)
    w = w / w.sum()
    out["era_sm_root"] = (out["era_sm_0_7"] * w[0] + out["era_sm_7_28"] * w[1]
                          + out["era_sm_28_100"] * w[2])
    return out


def load_soil(code):
    d = jload(os.path.join(RAW, f"soilgrids_{code}.json"))
    layers = d["properties"]["layers"]
    rows = []
    for L in layers:
        name = L["name"]
        um = L.get("unit_measure", {})
        for dep in L["depths"]:
            rows.append({"site": code, "property": name, "depth": dep["label"],
                         "value": dep["values"].get("mean"),
                         "mapped": um.get("mapped_units", ""),
                         "target": um.get("target_units", ""),
                         "dfactor": um.get("d_factor", 1)})
    return pd.DataFrame(rows)


def saxton_rawls(sand, clay, om, bd=None):
    """Saxton & Rawls (2006) 简式：由砂/黏/有机质百分数估算田间持水量与凋萎点"""
    A, B, C = sand, clay, om
    t1500 = (-0.024 * A + 0.487 * B + 0.006 * C + 0.005 * A * C
             - 0.013 * C * B + 0.068 * A * B + 0.031)
    t33 = (-0.251 * A + 0.195 * B + 0.011 * C + 0.006 * A * B
           - 0.027 * A * C + 0.452)
    th1500 = t1500 + (0.14 * t1500 - 0.02)
    th33 = t33 + (1.283 * t33 ** 2 - 0.374 * t33 - 0.015)
    return np.clip(th33, 0.02, 0.6), np.clip(th1500, 0.005, 0.4)


def rh_from_tdew(t, td):
    """由气温与露点算相对湿度（%），用于交叉核验"""
    es = 6.112 * np.exp(17.67 * t / (t + 243.5))
    e = 6.112 * np.exp(17.67 * td / (td + 243.5))
    return np.clip(100 * e / es, 0, 100)


def extraterrestrial_radiation(lat_deg, doy):
    """Ra, MJ m-2 d-1（FAO-56）"""
    phi = np.deg2rad(lat_deg)
    dr = 1 + 0.033 * np.cos(2 * np.pi * doy / 365)
    delta = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(delta), -1, 1))
    Ra = (24 * 60 / np.pi) * 0.0820 * dr * (
        ws * np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.sin(ws))
    return Ra


# --------------------------------------------------------------------- 主流程
def main():
    print("== 1. 读取原始响应 ==", flush=True)
    man = jload(os.path.join(RAW, "manifest.json"))
    REPORT["meta"] = {
        "generated": datetime.now().astimezone().isoformat(timespec="seconds"),
        "period": f"{Y0}-01..{Y1}-12",
        "n_sites": len(SITES),
        "n_requests": len(man["requests"]),
        "n_bytes": int(sum(r["bytes"] for r in man["requests"])),
        "sites": [{"code": s[0], "name": s[1], "lat": s[2], "lon": s[3], "role": s[3]} for s in SITES],
    }
    print(f"   manifest: {len(man['requests'])} 个请求, "
          f"{sum(r['bytes'] for r in man['requests'])/1e6:.1f} MB", flush=True)

    pm, pdly, md, qa, e5, soil = {}, {}, {}, {}, {}, {}
    for s in SITES:
        c = s[0]
        pm[c] = load_power_monthly(c)
        pdly[c] = load_power_daily(c)
        md[c] = load_modis(c, "NDVI")
        qa[c] = load_modis(c, "QA")
        e5[c] = load_era5(c)
        try:
            soil[c] = load_soil(c)
        except FileNotFoundError:
            soil[c] = pd.DataFrame()
        print(f"   {c} {NAME[c]}: POWER月 {len(pm[c])}, 日 {len(pdly[c])}, "
              f"NDVI {len(md[c])}, QA {len(qa[c])}, ERA5 {len(e5[c])}", flush=True)

    # ------------------------------------------------------------- 2. 聚合口径核验
    print("== 2. 聚合口径核验（月度产品 vs 日值重算） ==", flush=True)
    agg_rows = []
    for c in CODES:
        m = pm[c].set_index("date")
        dd = agg_daily_to_month(pdly[c])
        dd["date"] = dd["ym"].dt.to_timestamp()
        dd = dd.drop(columns=["ym"]).set_index("date")
        j = m.join(dd, how="inner").reset_index()
        j["dim"] = j["date"].dt.days_in_month
        P_prod = j["PRECTOTCORR"] * j["dim"]
        agg_rows.append(pd.DataFrame([{
            "site": c,
            "P_corr_product_daysum": float(np.corrcoef(P_prod, j["P_sum_daily"])[0, 1]),
            "P_ratio_median": float(np.nanmedian(P_prod / j["P_sum_daily"].replace(0, np.nan))),
            "T_corr": float(np.corrcoef(j["T2M"], j["T_mean_daily"])[0, 1]),
            "T_bias": float(np.nanmean(j["T2M"] - j["T_mean_daily"])),
            "WS_corr": float(np.corrcoef(j["WS10M"], j["WS_mean_daily"])[0, 1]),
            "WS_ratio_median": float(np.nanmedian(j["WS10M"] / j["WS_mean_daily"].replace(0, np.nan))),
            "GWET_corr": float(np.corrcoef(j["GWETROOT"], j["GWET_mean_daily"])[0, 1]),
            "SW_ratio_median": float(np.nanmedian(
                j["ALLSKY_SFC_SW_DWN"] / (j["SW_sum_daily"] / j["dim"]).replace(0, np.nan))),
            "days_per_month_median": float(j["dim"].median()),
        }]))
    agg = pd.concat(agg_rows, ignore_index=True)
    agg.to_csv(os.path.join(RES, "tab_aggregation_check.csv"), index=False, encoding="utf-8-sig")
    REPORT["checks"]["aggregation"] = agg.round(4).to_dict("records")
    print(agg[["site", "P_ratio_median", "WS_ratio_median", "T_bias"]].to_string(index=False), flush=True)

    # ------------------------------------------------------------- 3. 组装"脏"面板
    print("== 3. 组装未清洗面板 ==", flush=True)
    frames = []
    for c in CODES:
        m = pm[c].copy()
        m["ym"] = m["date"].dt.to_period("M")
        m["days_in_month"] = m["date"].dt.days_in_month
        # 派生：NDVI 月合成
        n = md[c].copy()
        q = qa[c].copy()
        n["ym"] = n["date"].dt.to_period("M")
        q["ym"] = q["date"].dt.to_period("M")
        nm = n.groupby("ym").agg(ndvi_mvc=("mean", "max"),
                                 ndvi_mean=("mean", "mean"),
                                 ndvi_median=("median", "mean"),
                                 n_comp=("mean", "size")).reset_index()
        qm = q.groupby("ym").agg(qa_med=("median", "mean"),
                                 qa_bad_frac=("mean", lambda x: float(np.mean(x > 1))),
                                 n_comp_qa=("mean", "size")).reset_index()
        # QA 过滤后的月最大合成（只保留 pixel_reliability ≤ 1 的合成期）
        nq = n[["modis_date", "ym", "mean"]].merge(
            q[["modis_date", "median"]].rename(columns={"median": "qa"}),
            on="modis_date", how="left")
        nmq = (nq[nq["qa"] <= 1].groupby("ym")
               .agg(ndvi_mvc_qa=("mean", "max"), n_comp_ok=("mean", "size")).reset_index())
        mm = nm.merge(qm, on="ym", how="outer").merge(nmq, on="ym", how="left")
        e = e5[c].copy()
        em = era5_monthly(e)
        panel = (m.merge(mm, on="ym", how="left")
                  .merge(em, on="ym", how="left"))
        panel["site"] = c
        frames.append(panel)
    raw = pd.concat(frames, ignore_index=True)
    raw = raw.sort_values(["site", "date"]).reset_index(drop=True)
    raw.to_csv(os.path.join(OUT, "panel_monthly_raw.csv"), index=False, encoding="utf-8-sig")
    REPORT["checks"]["modis_qa"] = qa_summary(md, qa)
    print("   MODIS QA：", json.dumps(REPORT["checks"]["modis_qa"]["overall"], ensure_ascii=False), flush=True)
    print(f"   未清洗面板 {raw.shape[0]} 行 × {raw.shape[1]} 列", flush=True)

    # ------------------------------------------------------------- 4. 质量审计（清洗前）
    print("== 4. 质量审计 ==", flush=True)
    num_cols = [c for c in raw.columns if c not in ("site", "date", "ym")]
    miss = []
    for c in COLS_AUDIT:
        if c not in raw:
            continue
        g = raw.groupby("site")[c]
        miss.append({
            "variable": c,
            "missing_total": int(raw[c].isna().sum()),
            "missing_pct": round(100 * raw[c].isna().mean(), 2),
            "sites_affected": int((g.apply(lambda s: s.isna().any())).sum()),
            "max_missing_run": int(_max_run(raw, c)),
        })
    miss_df = pd.DataFrame(miss)
    miss_df.to_csv(os.path.join(RES, "tab_missing.csv"), index=False, encoding="utf-8-sig")
    REPORT["checks"]["missing"] = miss_df.to_dict("records")

    # 重复
    dup = {
        "duplicate_site_month_rows": int(raw.duplicated(["site", "date"]).sum()),
        "duplicate_full_rows": int(raw.duplicated().sum()),
        "monthly_annual_overlap_rows": int(sum(1 for k in pm[CODES[0]]["ym"] if False)),
        "modis_duplicate_dates": int(sum(len(md[c]) - md[c]["modis_date"].nunique() for c in CODES)),
        "era5_duplicate_dates": int(sum(len(e5[c]) - e5[c]["date"].nunique() for c in CODES)),
    }
    # POWER 月度原始 JSON 中的年度汇总行（YYYY13）——已剔除，统计剔除数量
    annual_rows = 0
    for c in CODES:
        d = jload(os.path.join(RAW, f"power_monthly_{c}.json"))
        annual_rows += sum(1 for k in d["properties"]["parameter"]["T2M"] if k.endswith("13"))
    dup["power_annual_rows_dropped"] = int(annual_rows)
    REPORT["checks"]["duplicates"] = dup

    # 取值范围 / 物理一致性
    viol = {}
    viol["Tmin_gt_Tmean"] = int((raw["T2M_MIN"] > raw["T2M"]).sum())
    viol["Tmean_gt_Tmax"] = int((raw["T2M"] > raw["T2M_MAX"]).sum())
    viol["RH_out_0_100"] = int(((raw["RH2M"] < 0) | (raw["RH2M"] > 100)).sum())
    viol["GWET_out_0_1"] = int(((raw["GWETROOT"] < 0) | (raw["GWETROOT"] > 1)).sum())
    viol["NDVI_out_range"] = int(((raw["ndvi_mvc"] < -0.2) | (raw["ndvi_mvc"] > 1)).sum())
    viol["P_negative"] = int((raw["PRECTOTCORR"] < 0).sum())
    viol["P_zero_fraction"] = round(float((raw["PRECTOTCORR"] == 0).mean()), 3)
    viol["WS_negative"] = int((raw["WS10M"] < 0).sum())
    REPORT["checks"]["physical_violations"] = viol

    # 异常值（稳健 z，MAD）
    outl = []
    for c in COLS_OUTLIER:
        if c not in raw:
            continue
        s = raw[c].dropna()
        med = float(np.median(s))
        mad = float(np.median(np.abs(s - med)))
        if mad == 0:
            continue
        z = 0.6745 * (s - med) / mad
        outl.append({"variable": c, "n_absz_gt_3.5": int((np.abs(z) > 3.5).sum()),
                     "pct": round(100 * float((np.abs(z) > 3.5).mean()), 2),
                     "median": round(med, 4),
                     "p01": round(float(np.percentile(s, 1)), 4),
                     "p99": round(float(np.percentile(s, 99)), 4),
                     "skew": round(float(s.skew()), 3),
                     "kurt": round(float(s.kurt()), 3)})
    outl_df = pd.DataFrame(outl)
    outl_df.to_csv(os.path.join(RES, "tab_outliers.csv"), index=False, encoding="utf-8-sig")
    REPORT["checks"]["outliers"] = outl_df.to_dict("records")

    # 时序规整性
    tm = {}
    cnt = raw.groupby("site")["date"].nunique()
    tm["months_per_site"] = {k: int(v) for k, v in cnt.items()}
    tm["expected_months"] = int(N_MONTH)
    tm["sites_with_missing_months"] = [k for k, v in cnt.items() if v < N_MONTH]
    gaps = []
    for c in CODES:
        s = raw.loc[raw["site"] == c, "date"].sort_values()
        d = s.diff().dt.days.dropna()
        gaps.append({"site": c, "median_gap_days": float(d.median()),
                     "max_gap_days": float(d.max()) if len(d) else np.nan,
                     "irregular_gaps": int((d > 32).sum())})
    tm["month_gaps"] = gaps
    tm["modis_composites_per_year"] = {
        c: {int(y): int(g.size) for y, g in md[c].groupby(md[c]["date"].dt.year)}
        for c in CODES}
    tm["modis_doy_interval_median"] = float(
        np.median(np.diff(md[CODES[0]]["date"].values).astype("timedelta64[D]").astype(float)))
    REPORT["checks"]["temporal"] = tm

    # 数据不平衡
    imb = {"site_month_counts": {k: int(v) for k, v in raw.groupby("site").size().items()},
           "invalid_ndvi_months_by_site": {},
           "dust_event_day_fraction": {}}
    for c in CODES:
        s = raw.loc[raw["site"] == c, "ndvi_mvc"]
        imb["invalid_ndvi_months_by_site"][c] = int(s.isna().sum())
    for c in CODES:
        d = pdly[c]
        for th in (8, 10, 12, 15):
            frac = float((d["WS10M_MAX"] >= th).mean())
            imb["dust_event_day_fraction"].setdefault(f">={th}m/s", {})[c] = round(frac, 4)
    REPORT["checks"]["imbalance"] = imb

    # ------------------------------------------------------------- 5. 单位 / 量纲修正
    print("== 5. 单位与聚合口径修正 ==", flush=True)
    clean = raw.copy()
    clean["P_mm"] = clean["PRECTOTCORR"] * clean["days_in_month"]      # mm/d → mm/月
    clean["ET0_hargreaves"] = hargreaves(clean)                        # mm/月
    clean["SW_MJ"] = clean["ALLSKY_SFC_SW_DWN"] * clean["days_in_month"]
    clean["EVLAND_mm"] = clean["EVLAND"] * clean["days_in_month"]
    vsrc = clean["ndvi_mvc_qa"] if "ndvi_mvc_qa" in clean else clean["ndvi_mvc"]
    clean["V_pct"] = np.clip((vsrc - 0.05) / (0.85 - 0.05), 0, 1) * 100
    clean["E"] = erosion_index(clean)
    clean["AI"] = clean["P_mm"] / clean["ET0_hargreaves"].replace(0, np.nan)
    REPORT["derived"] = {
        "V_pct": "V = clip((NDVI-0.05)/(0.85-0.05),0,1)*100（像元二分，固定端元）",
        "E": "Lettau 单位宽度通量 q，站内按训练期均值归一",
        "ET0_hargreaves": "0.0023*Ra*(T+17.8)*sqrt(Tmax-Tmin)*days",
    }

    # ------------------------------------------------------------- 6. 缺失填补（仅训练期拟合气候态）
    print("== 6. 缺失填补 ==", flush=True)
    clean, imp_log = impute(clean)
    imp_log["masking_test"] = masking_test(clean)
    REPORT["imputation"] = imp_log
    REPORT["checks"]["qa_effect"] = qa_effect(clean)

    # ------------------------------------------------------------- 7. 归一化 / 标准化（训练期）
    print("== 7. 归一化参数（仅训练期） ==", flush=True)
    tr = clean[clean["date"].dt.year.between(*TRAIN)]
    norm = {}
    for c in ["GWETROOT", "era_sm_root", "E", "V_pct"]:
        q05, q95 = np.nanpercentile(tr[c], [5, 95])
        norm[c] = {"p05": float(q05), "p95": float(q95)}
    clean["W"] = np.clip((clean["GWETROOT"] - norm["GWETROOT"]["p05"])
                         / (norm["GWETROOT"]["p95"] - norm["GWETROOT"]["p05"]), 0, 1)
    clean["W_era"] = np.clip((clean["era_sm_root"] - norm["era_sm_root"]["p05"])
                             / (norm["era_sm_root"]["p95"] - norm["era_sm_root"]["p05"]), 0, 1)
    norm["zscore"] = {}
    for c in ["T2M", "P_mm", "WS10M", "RH2M", "SW_MJ", "ET0_hargreaves", "AI"]:
        mu, sd = float(np.nanmean(tr[c])), float(np.nanstd(tr[c], ddof=1))
        norm["zscore"][c] = {"mean": mu, "sd": sd}
    norm["clip_frac"] = {"W_at_0_pct": round(100 * float((clean["W"] <= 0).mean()), 2),
                         "W_at_1_pct": round(100 * float((clean["W"] >= 1).mean()), 2),
                         "E_at_0_pct": round(100 * float((clean["E"] <= 0).mean()), 2)}
    with open(os.path.join(OUT, "norm_params.json"), "w", encoding="utf-8") as f:
        json.dump(norm, f, ensure_ascii=False, indent=1)
    REPORT["normalization"] = norm

    # ------------------------------------------------------------- 8. 交叉来源一致性
    print("== 8. 交叉来源核验 ==", flush=True)
    cs = []
    for c in CODES:
        s = clean[clean["site"] == c]
        def cc(a, b):
            m = s[[a, b]].dropna()
            return float(np.corrcoef(m[a], m[b])[0, 1]) if len(m) > 5 else np.nan
        cs.append({
            "site": c,
            "T_corr_POWER_ERA5": cc("T2M", "era_T"), "T_bias_POWER_ERA5": float((s["T2M"] - s["era_T"]).mean()),
            "P_corr_POWER_ERA5": cc("P_mm", "era_P_mm"),
            "P_ratio_sum": float(s["P_mm"].sum() / s["era_P_mm"].sum()),
            "WS_corr_POWER_ERA5": cc("WS10M", "era_ws_max"),
            "SM_corr_GWET_ERA5": cc("GWETROOT", "era_sm_root"),
            "ET0_corr_Harg_ERA5": cc("ET0_hargreaves", "era_et0_mm"),
            "ET0_ratio": float(s["ET0_hargreaves"].sum() / s["era_et0_mm"].sum()),
            "SW_ratio": float(s["SW_MJ"].sum() / s["era_sw_MJ"].sum()),
        })
    cs_df = pd.DataFrame(cs)
    cs_df.to_csv(os.path.join(RES, "tab_cross_source.csv"), index=False, encoding="utf-8-sig")
    REPORT["checks"]["cross_source"] = cs_df.round(3).to_dict("records")
    print(cs_df[["site", "T_corr_POWER_ERA5", "P_ratio_sum", "SM_corr_GWET_ERA5",
                 "ET0_ratio"]].round(2).to_string(index=False), flush=True)

    # ------------------------------------------------------------- 9. 土壤剖面
    print("== 9. 土壤剖面与有效持水量 ==", flush=True)
    soil_tab = build_soil(soil)
    soil_tab.to_csv(os.path.join(OUT, "soil_profile.csv"), index=False, encoding="utf-8-sig")
    REPORT["soil"] = soil_tab.round(3).to_dict("records")

    # ------------------------------------------------------------- 10. 输出
    print("== 10. 输出 ==", flush=True)
    keep = ["site", "date", "ym", "days_in_month",
            "T2M", "T2M_MAX", "T2M_MIN", "RH2M", "QV2M", "PS", "WS10M", "WS10M_MAX",
            "WS2M", "WD10M", "SW_MJ", "P_mm", "PRECTOTCORR",
            "GWETROOT", "GWETTOP", "GWETPROF", "EVLAND_mm",
            "ET0_hargreaves", "AI", "E", "W", "W_era",
            "ndvi_mvc", "ndvi_mean", "n_comp", "qa_med", "qa_bad_frac",
            "V_pct", "V_dyn",
            "era_sm_0_7", "era_sm_7_28", "era_sm_28_100", "era_sm_100_255",
            "era_sm_root", "era_et0_mm", "era_P_mm", "era_T", "era_ws_max",
            "era_gust", "era_sw_MJ", "era_vpd", "era_rh",
            "dust_days_8", "dust_days_10", "dust_days_12", "dust_days_15"]
    clean["V_dyn"] = dynamic_v(clean, tr)
    for th in (8, 10, 12, 15):
        clean[f"dust_days_{th}"] = dust_days(pdly, clean, th)
    cols = [c for c in keep if c in clean.columns]
    out = clean[cols].copy()
    out.to_csv(os.path.join(OUT, "panel_monthly_clean.csv"), index=False, encoding="utf-8-sig")

    # 特征表
    feat_cols = ["W", "E", "T2M", "P_mm", "AI", "V_pct"]
    trf = out[out["date"].dt.year.between(*TRAIN)].dropna(subset=feat_cols)
    tef = out[~out["date"].dt.year.between(*TRAIN)].dropna(subset=["W", "E", "T2M", "P_mm", "AI"])
    trf.to_csv(os.path.join(OUT, "features_train.csv"), index=False, encoding="utf-8-sig")
    tef.to_csv(os.path.join(OUT, "features_test.csv"), index=False, encoding="utf-8-sig")
    REPORT["shapes"] = {"raw": list(raw.shape), "clean": list(out.shape),
                        "train": list(trf.shape), "test": list(tef.shape)}

    with open(os.path.join(RES, "qc_report.json"), "w", encoding="utf-8") as f:
        json.dump(REPORT, f, ensure_ascii=False, indent=1)
    print("完成：qc_report.json / tab_*.csv / panel_monthly_{raw,clean}.csv", flush=True)


COLS_AUDIT = ["T2M", "T2M_MAX", "T2M_MIN", "RH2M", "QV2M", "PS", "WS10M", "WS10M_MAX",
              "WS2M", "ALLSKY_SFC_SW_DWN", "PRECTOTCORR", "GWETROOT", "GWETTOP",
              "GWETPROF", "EVLAND", "WD10M", "ndvi_mvc", "ndvi_mvc_qa", "ndvi_mean", "n_comp",
              "qa_med", "qa_bad_frac", "era_sm_root", "era_et0_mm", "era_P_mm",
              "era_T", "era_ws_max", "era_sw_MJ", "era_rh"]

COLS_OUTLIER = ["T2M", "T2M_MAX", "T2M_MIN", "RH2M", "WS10M", "WS10M_MAX",
                "PRECTOTCORR", "GWETROOT", "ndvi_mvc", "era_sm_root", "era_et0_mm"]


def _max_run(df, col):
    best = cur = 0
    for c in CODES:
        s = df.loc[df["site"] == c, col].isna().values
        cur = 0
        for v in s:
            cur = cur + 1 if v else 0
            best = max(best, cur)
    return best


def hargreaves(df):
    """Hargreaves ET0（mm/月），Ra 由纬度与日序解析计算后取月内平均"""
    out = np.full(len(df), np.nan)
    for i, (lat, year, month, days) in enumerate(
            zip(df["site"].map(LAT), df["date"].dt.year,
                df["date"].dt.month, df["days_in_month"])):
        doys = np.arange(1, days + 1)
        # 该月第一天在年内的日序
        doy0 = int(pd.Timestamp(year=year, month=month, day=1).dayofyear)
        Ra = extraterrestrial_radiation(lat, doy0 + doys - 1).mean()
        t = df["T2M"].iloc[i]
        tr = df["T2M_MAX"].iloc[i] - df["T2M_MIN"].iloc[i]
        if np.isnan(t) or np.isnan(tr) or tr <= 0:
            continue
        out[i] = 0.0023 * 0.408 * Ra * (t + 17.8) * np.sqrt(tr) * days
    return out


def erosion_index(df):
    # 用"月内日最大风速的月均值"而非月均风速：沙粒起动由阵风控制，月均值会系统性低估
    ustar = KAPPA * df["WS10M_MAX"] / np.log(10 / Z0)
    ustar_t = KAPPA * U_T_THRESH / np.log(10 / Z0)
    q = C_LETTAU * RHO / G * ustar ** 2 * (ustar - ustar_t)
    q = np.clip(q, 0, None)
    base = np.nanmean(q[df["date"].dt.year.between(*TRAIN)])
    return q / base if base and base > 0 else q


def dust_days(pdly, clean, th):
    vals = {}
    for c in CODES:
        d = pdly[c].copy()
        d["ym"] = d["date"].dt.to_period("M")
        cnt = d.assign(ev=(d["WS10M_MAX"] >= th)).groupby("ym")["ev"].sum()
        vals.update({(c, k): int(v) for k, v in cnt.items()})
    return clean.apply(lambda r: vals.get((r["site"], r["ym"]), np.nan), axis=1)


def dynamic_v(clean, tr):
    out = np.full(len(clean), np.nan)
    for c in CODES:
        m = (clean["site"] == c) & clean["date"].dt.year.between(*TRAIN)
        lo, hi = np.nanpercentile(clean.loc[m, "ndvi_mvc"], [5, 95])
        v = np.clip((clean.loc[clean["site"] == c, "ndvi_mvc"] - lo) / (hi - lo), 0, 1) * 100
        out[clean["site"] == c] = v.values
    return out


def impute(clean):
    """站内线性插值（≤2 月）+ 训练期同月气候态；逐变量留痕"""
    log = {"method": "站内线性插值(limit=2月) → 训练期(2015-2022)同月气候态", "detail": []}
    targets = ["GWETROOT", "GWETTOP", "GWETPROF", "ndvi_mvc", "ndvi_mean", "qa_med",
               "qa_bad_frac", "T2M", "T2M_MAX", "T2M_MIN", "RH2M", "QV2M", "PS",
               "WS10M", "WS10M_MAX", "WS2M", "ALLSKY_SFC_SW_DWN", "PRECTOTCORR",
               "EVLAND", "WD10M", "P_mm", "ET0_hargreaves", "SW_MJ", "EVLAND_mm",
               "era_sm_root", "era_et0_mm", "era_P_mm", "era_T", "era_ws_max",
               "era_sw_MJ", "era_rh", "era_vpd", "V_pct"]
    for c in CODES:
        idx = clean["site"] == c
        sub = clean.loc[idx].sort_values("date")
        for col in targets:
            if col not in sub:
                continue
            n0 = int(sub[col].isna().sum())
            if n0 == 0:
                continue
            s = sub[col].copy()
            s = s.interpolate(method="linear", limit=2, limit_direction="both")
            tr_sub = sub[sub["date"].dt.year.between(*TRAIN)]
            clim = tr_sub.groupby(tr_sub["date"].dt.month)[col].mean()
            still = s.isna()
            if still.any():
                s.loc[still] = sub.loc[still, "date"].dt.month.map(clim).values
            clean.loc[sub.index, col] = s.values
            n1 = int(pd.isna(s).sum())
            log["detail"].append({"site": c, "variable": col, "missing_before": n0,
                                  "missing_after": n1, "filled": n0 - n1})
    tot = {}
    for r in log["detail"]:
        tot[r["variable"]] = tot.get(r["variable"], 0) + r["filled"]
    log["total_filled_by_variable"] = tot
    return clean, log


def qa_summary(md, qa):
    """MODIS 像元可靠性统计：多少合成期被 QA 判为可疑，逐站"""
    per_site = {}
    tot = tot_bad = 0
    for c in CODES:
        q = qa[c]
        bad = int((q["median"] > 1).sum())
        tot += len(q)
        tot_bad += bad
        per_site[c] = {"n_composites": int(len(q)),
                       "n_qa_gt1": bad,
                       "qa_gt1_frac": round(bad / len(q), 4) if len(q) else None,
                       "n_all_invalid": int((q["px_valid"] == 0).sum())}
    return {"overall": {"n_composites": tot, "n_qa_gt1": tot_bad,
                        "qa_gt1_frac": round(tot_bad / tot, 4)},
            "by_site": per_site}


def qa_effect(clean):
    """QA 过滤 + 月最大合成 相对"不质控"的覆盖度差异（百分点）"""
    v_raw = np.clip((clean["ndvi_mean"] - 0.05) / 0.80, 0, 1) * 100
    v_qa = clean["V_pct"]
    d = (v_qa - v_raw).dropna()
    return {"mean_abs_diff_pp": round(float(np.mean(np.abs(d))), 3),
            "max_abs_diff_pp": round(float(np.max(np.abs(d))), 3),
            "p95_abs_diff_pp": round(float(np.percentile(np.abs(d), 95)), 3),
            "corr": round(float(np.corrcoef(v_qa.dropna(), v_raw.loc[v_qa.dropna().index])[0, 1]), 4)}


def masking_test(clean, frac=0.10, seed=20261110):
    """人工掩蔽实验：随机遮住 10% 的月份，比较三种插补策略的还原误差"""
    rng = np.random.default_rng(seed)
    out = []
    for strat in ("linear", "clim", "persistence"):
        errs = []
        for c in CODES:
            s = clean[clean["site"] == c].sort_values("date")
            v = s["V_pct"].to_numpy(dtype=float)
            n = len(v)
            mon = s["date"].dt.month.to_numpy()
            yr = s["date"].dt.year.to_numpy()
            idx = rng.choice(n, size=int(n * frac), replace=False)
            keep = np.ones(n, bool)
            keep[idx] = False
            obs = v.copy()
            obs[~keep] = np.nan
            pred = obs.copy()
            if strat == "linear":
                pred = pd.Series(obs).interpolate(limit=3, limit_direction="both").to_numpy()
            else:
                clim = {}
                for m in np.unique(mon):
                    sel = (mon == m) & keep & (yr <= TRAIN[1])
                    clim[m] = float(np.nanmean(v[sel])) if sel.any() else float(np.nanmean(v[keep]))
                if strat == "clim":
                    pred[~keep] = [clim[mon[i]] for i in np.where(~keep)[0]]
                else:  # 去年同期
                    for i in np.where(~keep)[0]:
                        j = i - 12
                        pred[i] = obs[j] if j >= 0 and np.isfinite(obs[j]) else clim[mon[i]]
                pred = pd.Series(pred).interpolate(limit_direction="both").to_numpy()
            errs.append(pred[idx] - v[idx])
        e = np.concatenate(errs)
        out.append({"strategy": strat, "n_masked": int(e.size),
                    "RMSE_pp": round(float(np.sqrt(np.mean(e ** 2))), 3),
                    "MAE_pp": round(float(np.mean(np.abs(e))), 3),
                    "bias_pp": round(float(np.mean(e)), 3)})
    return {"mask_fraction": frac, "seed": seed, "results": out}


def build_soil(soil):
    rows = []
    for c in CODES:
        if c not in soil or soil[c] is None or len(soil[c]) == 0:
            continue
        d = soil[c].copy()
        # SoilGrids v2：原始 mean 为整数，除以 d_factor 得到目标单位；
        # sand/clay/silt 的 target 为 %，soc 的 target 为 g/kg（需再 /10 变 %）
        d["val"] = d["value"] / d["dfactor"]
        d.loc[d["target"] == "g/kg", "val"] = d.loc[d["target"] == "g/kg", "val"] / 10.0
        piv = d.pivot_table(index="depth", columns="property", values="val", aggfunc="mean")
        row = {"site": c}
        top = piv.loc[[x for x in ["0-5cm", "5-15cm", "15-30cm"] if x in piv.index]]
        for p in ["sand", "silt", "clay", "soc", "bdod"]:
            row[p] = float(np.nanmean(top[p])) if p in top else np.nan
        row["om_pct"] = row["soc"] * 0.1 / 0.58 if pd.notna(row["soc"]) else np.nan
        if pd.notna(row["sand"]) and pd.notna(row["clay"]):
            fc, wp = saxton_rawls(row["sand"], row["clay"],
                                  max(row["om_pct"] if pd.notna(row["om_pct"]) else 0.5, 0.05))
            row["field_capacity"] = float(fc)
            row["wilting_point"] = float(wp)
            row["AWC"] = float(fc - wp)
            row["rootzone_AWC_mm"] = float((fc - wp) * 600)
        rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    main()






