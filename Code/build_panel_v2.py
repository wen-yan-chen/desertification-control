# -*- coding: utf-8 -*-
"""
build_panel_v2.py —— 由已下载缓存组装分析面板（不发网络请求）

数据来源：
  Data/raw/nasa_power_verified/power_monthly.csv   NASA POWER 月度（8 站 × 120 月）
  Data/cache/ndvi/<站>/A*.json                      MOD13Q1 NDVI 逐合成期（8 站，2015—2024）
  Data/cache/modis_v2/<站>/250m_16_days_pixel_reliability/...   仅 TZ、XT 两站完整

关于 NDVI 质量控制（对应审计意见“NDVI 无 QA”）：
  MOD13Q1 官方 QA 波段仅在 TZ、XT 两站完整取得（ORNL 服务端限速，其余站点未取全）。
  因此本脚本：(1) 用两站完整 QA 估计 QA>1 的比例，并比较“QA 过滤前后”月合成覆盖度的差异；
           (2) 全序列采用“NDVI 有效性 + 相对气候态偏离筛查（|ΔNDVI|>3σ）”作为替代质控；
  报告中明确标注这是抽样 QA 而非全量官方 QA。

输出：
  Data/raw/modis_ndvi_qa_sample.csv      两站逐合成期 NDVI 与 QA（可审计）
  Data/processed/panel_v2.csv            分析面板
  Results/qa_assessment.json             QA 抽样评估结果
"""
import json
import os

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "Data", "raw")
PROC = os.path.join(BASE, "Data", "processed")
RES = os.path.join(BASE, "Results")
CACHE = os.path.join(BASE, "Data", "cache")

STATIONS = [("塔中", "TZ", 38.97, 83.65), ("肖塘", "XT", 38.83, 84.02),
            ("且末", "QM", 38.13, 85.53), ("民丰", "MF", 37.06, 82.68),
            ("若羌", "RQ", 39.02, 88.17), ("库尔勒", "KEL", 41.76, 86.15),
            ("尉犁", "YL", 41.34, 86.26), ("阿拉尔", "ALE", 40.55, 81.28)]
SCALE = 0.0001


def hargreaves_et0(lat_deg, month, days, tmean, tmax, tmin):
    J = 15 + 30.4 * (month - 1)
    phi = np.deg2rad(lat_deg)
    dr = 1 + 0.033 * np.cos(2 * np.pi * J / 365)
    dec = 0.409 * np.sin(2 * np.pi * J / 365 - 1.39)
    x = np.clip(-np.tan(phi) * np.tan(dec), -1, 1)
    ws = np.arccos(x)
    Ra = (24 * 60 / np.pi) * 0.0820 * dr * (
        ws * np.sin(phi) * np.sin(dec) + np.cos(phi) * np.cos(dec) * np.sin(ws))
    Ra_mm = Ra * 0.408
    dT = np.clip(tmax - tmin, 0.1, None)
    et0 = 0.0023 * Ra_mm * np.clip(tmean + 17.8, 0, None) * np.sqrt(dT)
    return float(np.clip(et0, 0.2, None) * days)


def lettau_unit_flux(ws10, gust=1.8, ut=5.0, kappa=0.4, z0=0.001,
                     rho=1.225, g=9.81, C=6.7):
    u = np.clip(ws10 * gust, 0, None)
    ustar = u * kappa / np.log(10.0 / z0)
    ust_t = ut * kappa / np.log(10.0 / z0)
    return np.where(ustar > ust_t, C * (rho / g) * ustar ** 2 * (ustar - ust_t), 0.0)


def read_cache_ndvi(code):
    """读旧缓存：{站}/A*.json，每块含 9 个合成期"""
    d = os.path.join(CACHE, "ndvi", code)
    recs = []
    if not os.path.isdir(d):
        return pd.DataFrame()
    for f in sorted(os.listdir(d)):
        if not f.endswith(".json"):
            continue
        try:
            for it in json.load(open(os.path.join(d, f), encoding="utf-8")):
                recs.append({"calendar_date": it["calendar_date"],
                             "modis_date": it["modis_date"],
                             "ndvi": (it.get("ndvi_raw") or np.nan) * SCALE
                             if it.get("ndvi_raw") is not None else np.nan,
                             "raw": it.get("ndvi_raw")})
        except Exception:
            continue
    df = pd.DataFrame(recs)
    if len(df):
        df.loc[df["raw"] == -3000, "ndvi"] = np.nan
        df["dt"] = pd.to_datetime(df["calendar_date"])
        df = df.drop_duplicates("modis_date").sort_values("dt")
    return df


def read_cache_qa(code):
    d = os.path.join(CACHE, "modis_v2", code)
    nd, qa = {}, {}
    for band, box in (("250m_16_days_NDVI", nd), ("250m_16_days_pixel_reliability", qa)):
        bd = os.path.join(d, band)
        if not os.path.isdir(bd):
            continue
        for f in sorted(os.listdir(bd)):
            try:
                for it in json.load(open(os.path.join(bd, f), encoding="utf-8")):
                    box[it["modis_date"]] = (it["calendar_date"], it.get("value"))
            except Exception:
                continue
    out = []
    for md, (cd, v) in nd.items():
        qv = qa.get(md, (None, None))[1]
        out.append({"modis_date": md, "calendar_date": cd,
                    "ndvi": (v * SCALE) if v not in (None, -3000) else np.nan,
                    "qa": qv})
    return pd.DataFrame(out)


def main():
    power = pd.read_csv(os.path.join(RAW, "nasa_power_verified", "power_monthly.csv"),
                        encoding="utf-8-sig")
    frames = []
    qa_rows = []
    qa_stats = {}
    for name, code, lat, lon in STATIONS:
        nd = read_cache_ndvi(code)
        if len(nd) == 0:
            continue
        nd["月份"] = nd["dt"].dt.strftime("%Y-%m")
        m = nd.groupby("月份")["ndvi"].max().rename("NDVI").reset_index()
        sub = power[power["站代码"] == code].merge(m, on="月份", how="left")

        # 替代质控：相对同月气候态偏离 > 3σ 视为可疑（在训练期内建立）
        clim = sub[sub["月份"] <= "2022-12"].groupby(sub["月份"].str[5:].astype(int))["NDVI"].mean()
        sd = sub[sub["月份"] <= "2022-12"].groupby(sub["月份"].str[5:].astype(int))["NDVI"].std()
        mo = sub["月份"].str[5:].astype(int)
        dev = (sub["NDVI"] - mo.map(clim)) / mo.map(sd).replace(0, np.nan)
        sub["ndvi_flag"] = np.where(dev.abs() > 3, "climatology_outlier", "ok")
        sub["NDVI_qc"] = np.where(sub["ndvi_flag"] == "ok", sub["NDVI"], np.nan)

        # 若该站有官方 QA，则计算过滤前后差异
        q = read_cache_qa(code)
        if len(q):
            q["dt"] = pd.to_datetime(q["calendar_date"])
            q["月份"] = q["dt"].dt.strftime("%Y-%m")
            q["valid"] = (pd.to_numeric(q["qa"], errors="coerce").fillna(9) <= 1) & q["ndvi"].notna()
            n_all, n_bad = len(q), int((pd.to_numeric(q["qa"], errors="coerce") > 1).sum())
            mf = q[q["valid"]].groupby("月份")["ndvi"].max().rename("NDVI_qa")
            merged = sub[["月份", "NDVI"]].merge(mf, on="月份", how="left")
            diff = (merged["NDVI_qa"] - merged["NDVI"]).abs()
            qa_stats[code] = {
                "composites": n_all,
                "qa_gt1_ratio": round(n_bad / max(n_all, 1), 4),
                "months_with_qa": int(merged["NDVI_qa"].notna().sum()),
                "mean_abs_diff_pp": round(float(diff.mean() * 100), 2),
                "max_abs_diff_pp": round(float(diff.max() * 100), 2)}
            for _, r in q.iterrows():
                qa_rows.append({"站代码": code, "modis_date": r["modis_date"],
                                "calendar_date": r["calendar_date"],
                                "ndvi": r["ndvi"], "qa": r["qa"], "valid": bool(r["valid"])})

        sub["站代码"] = code
        sub["站点"] = name
        frames.append(sub)

    panel = pd.concat(frames, ignore_index=True).sort_values(["站代码", "月份"]).reset_index(drop=True)

    # 覆盖度：固定端元（主口径）+ 站点分位端元（敏感性）
    panel["FVC_fixed"] = ((panel["NDVI_qc"] - 0.05) / 0.80).clip(0, 1) * 100
    panel["FVC_dyn"] = np.nan
    for code, sub in panel.groupby("站代码"):
        tr = sub[sub["月份"] <= "2022-12"]["NDVI_qc"].dropna()
        if len(tr) < 24:
            continue
        lo, hi = np.nanpercentile(tr, 5), np.nanpercentile(tr, 95)
        if hi - lo < 0.05:
            lo, hi = 0.05, 0.85
        panel.loc[sub.index, "FVC_dyn"] = ((sub["NDVI_qc"] - lo) / (hi - lo)).clip(0, 1) * 100

    # 风蚀：单位宽度通量 → 站内归一（无量纲）
    panel["q_unit"] = lettau_unit_flux(panel["WS10M"].values)
    panel["E_index"] = np.nan
    for code, sub in panel.groupby("站代码"):
        ref = sub.loc[sub["月份"] <= "2022-12", "q_unit"].mean()
        if ref and ref > 0:
            panel.loc[sub.index, "E_index"] = sub["q_unit"] / ref
    panel["E_index"] = panel["E_index"].fillna(0.0)

    panel["ET0_mm"] = [hargreaves_et0(r.lat, int(r.月份[5:7]), r.days,
                                       r.T2M, r.T2M_MAX, r.T2M_MIN)
                       for r in panel.itertuples()]
    panel["elapsed_years_since_2015"] = ((panel["月份"].str[:4].astype(int) - 2015)
                                         + (panel["月份"].str[5:].astype(int) - 1) / 12.0)
    panel["split"] = np.where(panel["月份"] <= "2022-12", "train", "test")

    keep = ["站代码", "站点", "月份", "days", "lat", "P_mm", "T2M", "T2M_MAX", "T2M_MIN",
            "WS10M", "Rs_MJ", "GWETROOT", "ET0_mm", "NDVI", "NDVI_qc", "ndvi_flag",
            "FVC_fixed", "FVC_dyn", "q_unit", "E_index",
            "elapsed_years_since_2015", "split"]
    panel[keep].to_csv(os.path.join(PROC, "panel_v2.csv"), index=False, encoding="utf-8-sig")
    if qa_rows:
        pd.DataFrame(qa_rows).to_csv(os.path.join(RAW, "modis_ndvi_qa_sample.csv"),
                                     index=False, encoding="utf-8-sig")

    stats = {"stations": int(panel["站代码"].nunique()), "rows": int(len(panel)),
             "missing": {c: int(panel[c].isna().sum()) for c in
                         ["NDVI", "NDVI_qc", "FVC_fixed", "P_mm", "ET0_mm", "GWETROOT"]},
             "ndvi_flag_counts": panel["ndvi_flag"].value_counts().to_dict(),
             "qa_sampling": qa_stats,
             "qa_note": "只有 TZ/XT 取得完整官方 QA；其余站点用相对气候态偏离筛查替代",
             "train": "2015-01—2022-12", "test": "2023-01—2024-12"}
    json.dump(stats, open(os.path.join(RES, "qa_assessment.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(json.dumps(stats, ensure_ascii=False, indent=1)[:1500])
    print("panel:", panel.shape)


if __name__ == "__main__":
    main()
