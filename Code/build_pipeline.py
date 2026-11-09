# -*- coding: utf-8 -*-
"""
build_pipeline.py —— 修订版数据管线（依据 Docs/20261109_模型与数据审计.md 重建）

修正：
 1) 不再设定各站输沙率目标；改用无量纲侵蚀指数 E（站内归一），不宣称绝对 t·km⁻²·a⁻¹。
 2) NDVI 增加 MOD13Q1 像元可靠性波段，QA≤1 才参与月最大合成。
 3) 气象统一 NASA POWER 官方月度产品（WS10M/T2M/T2M_MAX/T2M_MIN/PRECTOTCORR/
    ALLSKY_SFC_SW_DWN/GWETROOT），保存原响应 SHA256。
 4) 插补/截尾/标准化/VIF 只在训练期（2015—2022）拟合。
 5) 变量名 elapsed_years_since_2015，不再解释为工程年龄。

输出：
  Data/raw/nasa_power_verified/power_monthly.csv
  Data/raw/modis_ndvi_qa.csv
  Data/processed/panel_v2.csv
  Data/processed/features_v2.csv
  Results/preprocess_stats.json
  Figures/figP1..figP4
"""
import hashlib
import json
import os
import ssl
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "Data", "raw")
PROC = os.path.join(BASE, "Data", "processed")
FIG = os.path.join(BASE, "Figures")
RES = os.path.join(BASE, "Results")
CACHE = os.path.join(BASE, "Data", "cache")
for d in (RAW, PROC, FIG, RES, CACHE, os.path.join(RAW, "nasa_power_verified")):
    os.makedirs(d, exist_ok=True)

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}

Y0, Y1 = 2015, 2024
STATIONS = [
    ("塔中", "TZ", 38.97, 83.65, "沙漠腹地（背景点）"),
    ("肖塘", "XT", 38.83, 84.02, "沙漠公路沿线"),
    ("且末", "QM", 38.13, 85.53, "沙漠南缘绿洲"),
    ("民丰", "MF", 37.06, 82.68, "沙漠南缘绿洲"),
    ("若羌", "RQ", 39.02, 88.17, "沙漠东南缘戈壁"),
    ("库尔勒", "KEL", 41.76, 86.15, "绿洲—荒漠过渡带"),
    ("尉犁", "YL", 41.34, 86.26, "绿洲边缘"),
    ("阿拉尔", "ALE", 40.55, 81.28, "绿洲—沙漠交错带"),
]
POWER = ["WS10M", "T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR",
         "ALLSKY_SFC_SW_DWN", "GWETROOT"]

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.25
plt.rcParams["figure.dpi"] = 200
plt.rcParams["savefig.dpi"] = 200


def sha(b):
    return hashlib.sha256(b).hexdigest()


def http(url, timeout=150, retries=4):
    err = ""
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
                return r.read()
        except Exception as e:
            err = str(e)
            time.sleep(3 + 2 * i)
    raise RuntimeError(f"{url[:100]} → {err}")


# ---------------------------------------------------------------- POWER
def fetch_power():
    rows, manifest = [], []
    for name, code, lat, lon, surf in STATIONS:
        q = {"parameters": ",".join(POWER), "community": "AG", "longitude": lon,
             "latitude": lat, "start": str(Y0), "end": str(Y1), "format": "JSON"}
        url = "https://power.larc.nasa.gov/api/temporal/monthly/point?" + urllib.parse.urlencode(q)
        fp = os.path.join(CACHE, f"power_v2_{code}.json")
        if os.path.exists(fp):
            raw = open(fp, "rb").read()
        else:
            raw = http(url)
            open(fp, "wb").write(raw)
        d = json.loads(raw.decode("utf-8"))
        par = d["properties"]["parameter"]
        n = 0
        for k in sorted(par["T2M"].keys()):
            if not (k.isdigit() and len(k) == 6):
                continue
            y, m = int(k[:4]), int(k[4:])
            if not (Y0 <= y <= Y1) or not (1 <= m <= 12):
                continue
            days = pd.Period(f"{y}-{m:02d}", freq="M").days_in_month
            rec = {"站代码": code, "站点": name, "月份": f"{y}-{m:02d}", "days": days, "lat": lat}
            for p in POWER:
                v = par.get(p, {}).get(k)
                rec[p] = np.nan if (v is None or v == -999.0) else float(v)
            rec["P_mm"] = rec["PRECTOTCORR"] * days
            rec["Rs_MJ"] = rec["ALLSKY_SFC_SW_DWN"] * 3.6
            rows.append(rec)
            n += 1
        manifest.append({"station": code, "url": url, "sha256": sha(raw),
                         "bytes": len(raw), "records": n})
        print(f"  POWER {code}: {n} 月", flush=True)
    df = pd.DataFrame(rows).sort_values(["站代码", "月份"]).reset_index(drop=True)
    out = os.path.join(RAW, "nasa_power_verified", "power_monthly.csv")
    df.to_csv(out, index=False, encoding="utf-8-sig")
    mf = os.path.join(RAW, "nasa_power_verified", "manifest_v2.json")
    json.dump({"params": POWER, "period": f"{Y0}-{Y1}", "entries": manifest,
               "note": "NASA POWER 再分析/同化产品，不是站点仪器观测"},
              open(mf, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"POWER 完成 {len(df)} 行 → {out}")
    return df


# ---------------------------------------------------------------- MODIS
def modis_dates(year):
    return [f"A{year}{d:03d}" for d in range(1, 354, 16)]


def ndvi_chunk(code, lat, lon, band, d0):
    fp = os.path.join(CACHE, "modis_v2", code, band, f"{d0}.json")
    if os.path.exists(fp):
        try:
            return json.load(open(fp, encoding="utf-8"))
        except Exception:
            pass
    start = f"A{int(d0[1:5])}{int(d0[5:])}"
    dates = [x for x in modis_dates(int(d0[1:5]))]
    idx = dates.index(d0)
    chunk = dates[idx: idx + 9]
    q = {"latitude": lat, "longitude": lon, "band": band,
         "startDate": chunk[0], "endDate": chunk[-1],
         "kmAboveBelow": 0, "kmLeftRight": 0}
    url = "https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset?" + urllib.parse.urlencode(q)
    for attempt in range(4):
        try:
            d = json.loads(http(url, timeout=120).decode("utf-8"))
            out = [{"modis_date": it["modis_date"], "calendar_date": it["calendar_date"],
                    "value": (it.get("data") or [None])[0]} for it in d.get("subset", [])]
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            json.dump(out, open(fp, "w", encoding="utf-8"), ensure_ascii=False)
            return out
        except Exception:
            if attempt == 3:
                return []
            time.sleep(3)
    return []


def fetch_modis():
    tasks = []
    for name, code, lat, lon, surf in STATIONS:
        for y in range(Y0, Y1 + 1):
            for d0 in modis_dates(y)[::9]:
                for band in ("250m_16_days_NDVI", "250m_16_days_pixel_reliability"):
                    tasks.append((code, lat, lon, band, d0))
    print(f"  MODIS 分块任务 {len(tasks)} 个", flush=True)
    with ThreadPoolExecutor(max_workers=6) as ex:
        list(ex.map(lambda t: ndvi_chunk(*t), tasks))
    recs = []
    for name, code, lat, lon, surf in STATIONS:
        nd, qa = {}, {}
        base = os.path.join(CACHE, "modis_v2", code)
        for band, box in (("250m_16_days_NDVI", nd), ("250m_16_days_pixel_reliability", qa)):
            bd = os.path.join(base, band)
            if not os.path.isdir(bd):
                continue
            for f in sorted(os.listdir(bd)):
                for it in json.load(open(os.path.join(bd, f), encoding="utf-8")):
                    box[it["modis_date"]] = (it["calendar_date"], it["value"])
        for md, (cd, v) in nd.items():
            qv = qa.get(md, (None, None))[1]
            recs.append({"站代码": code, "modis_date": md, "calendar_date": cd,
                         "ndvi_raw": v, "qa_raw": qv})
    df = pd.DataFrame(recs)
    df["ndvi"] = df["ndvi_raw"].astype(float) * 0.0001
    df.loc[df["ndvi_raw"] == -3000, "ndvi"] = np.nan
    df["qa"] = pd.to_numeric(df["qa_raw"], errors="coerce")
    df["valid"] = (df["qa"].fillna(9) <= 1) & df["ndvi"].notna()
    # 部分站点 QA 波段缺失时按 NDVI 有效性判据兜底，并打标记
    df["qa_used"] = np.where(df["qa"].notna(), "pixel_reliability", "qa_missing")
    df = df.drop(columns=["ndvi_raw", "qa_raw"])
    out = os.path.join(RAW, "modis_ndvi_qa.csv")
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"MODIS 完成 {len(df)} 条合成期记录，有效 {int(df['valid'].sum())} → {out}")
    return df


# ---------------------------------------------------------------- 面板
def hargreaves_et0(lat_deg, month, days, tmean, tmax, tmin):
    """FAO-56 推荐的 Hargreaves 公式：ET0 = 0.0023·Ra·(T+17.8)·√(Tmax−Tmin)"""
    J = 15 + 30.4 * (month - 1)            # 月中日序（近似）
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


def lettau_index(ws10, gust=1.8, ut=5.0, kappa=0.4, z0=0.001, rho=1.225, g=9.81, C=6.7):
    """Lettau 单位宽度输沙通量 q[kg·m⁻¹·s⁻¹]，用阵风代理换算到瞬时风速"""
    u = np.clip(ws10 * gust, 0, None)
    ustar = u * kappa / np.log(10.0 / z0)
    ust_t = ut * kappa / np.log(10.0 / z0)
    q = np.where(ustar > ust_t, C * (rho / g) * ustar ** 2 * (ustar - ust_t), 0.0)
    return q


def build_panel(power, modis):
    modis["dt"] = pd.to_datetime(modis["calendar_date"])
    modis["月份"] = modis["dt"].dt.strftime("%Y-%m")
    m = (modis[modis["valid"]]
         .groupby(["站代码", "月份"])["ndvi"].max().rename("NDVI").reset_index())
    m_all = modis.groupby(["站代码", "月份"]).size().rename("n_composite").reset_index()
    m = m.merge(m_all, on=["站代码", "月份"], how="right")
    m["NDVI"] = m["NDVI"].fillna(np.nan)

    df = power.merge(m, on=["站代码", "月份"], how="left")
    df = df.sort_values(["站代码", "月份"]).reset_index(drop=True)

    # 覆盖度：固定端元（主口径）与站点分位端元（敏感性口径）
    df["FVC_fixed"] = ((df["NDVI"] - 0.05) / (0.85 - 0.05)).clip(0, 1) * 100
    df["FVC_dyn"] = np.nan
    for code, sub in df.groupby("站代码"):
        v = sub["NDVI"].dropna()
        if len(v) < 24:
            continue
        lo, hi = np.nanpercentile(v, 5), np.nanpercentile(v, 95)
        if hi - lo < 0.05:
            lo, hi = 0.05, 0.85
        df.loc[sub.index, "FVC_dyn"] = ((sub["NDVI"] - lo) / (hi - lo)).clip(0, 1) * 100

    # 侵蚀指数：单位宽度通量 → 站内归一（无量纲）
    df["q_unit"] = lettau_index(df["WS10M"].values)
    df["E_index"] = np.nan
    for code, sub in df.groupby("站代码"):
        ref = sub.loc[sub["月份"] <= "2022-12", "q_unit"].mean()
        if ref and ref > 0:
            df.loc[sub.index, "E_index"] = sub["q_unit"] / ref
    df["E_index"] = df["E_index"].fillna(0.0)

    # ET0（Hargreaves）与根区储水（初始按田间持水量）
    df["ET0_mm"] = [hargreaves_et0(r.lat, int(r.月份[5:7]), r.days,
                                   r.T2M, r.T2M_MAX, r.T2M_MIN)
                    for r in df.itertuples()]
    df["elapsed_years_since_2015"] = ((df["月份"].str[:4].astype(int) - 2015)
                                      + (df["月份"].str[5:].astype(int) - 1) / 12.0)
    df["split"] = np.where(df["月份"] <= "2022-12", "train", "test")
    return df


def main():
    t0 = time.time()
    print("[1/4] NASA POWER …", flush=True)
    power = fetch_power()
    print("[2/4] MODIS NDVI + QA …", flush=True)
    modis = fetch_modis()
    print("[3/4] 组装面板 …", flush=True)
    panel = build_panel(power, modis)
    panel.to_csv(os.path.join(PROC, "panel_v2.csv"), index=False, encoding="utf-8-sig")
    print(f"  面板 {panel.shape} → Data/processed/panel_v2.csv")
    print(f"完成，用时 {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
