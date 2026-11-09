# -*- coding: utf-8 -*-
"""
02_crosscheck_power.py —— 用 NASA POWER 独立交叉验证 ERA5-Land 数据
NASA POWER（MERRA-2 再分析）与 ERA5 是两条独立的技术路线，二者对比可量化站点气象数据的代表性误差。
输出：数据/processed/07_交叉验证_POWER.csv、图/fig8_交叉验证.png
"""
import gzip
import json
import os
import ssl
import time
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "数据", "raw")
CACHE = os.path.join(BASE, "数据", "cache")
PROC = os.path.join(BASE, "数据", "processed")
FIG = os.path.join(BASE, "图")
os.makedirs(CACHE, exist_ok=True)
os.makedirs(PROC, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.25
plt.rcParams["figure.dpi"] = 200
plt.rcParams["savefig.dpi"] = 200

STATIONS = [("塔中", "TZ", 38.97, 83.65), ("肖塘", "XT", 38.83, 84.02),
            ("且末", "QM", 38.13, 85.53), ("民丰", "MF", 37.06, 82.68),
            ("若羌", "RQ", 39.02, 88.17), ("库尔勒", "KEL", 41.76, 86.15),
            ("尉犁", "YL", 41.34, 86.26), ("阿拉尔", "ALE", 40.55, 81.28)]


def get(url, timeout=90):
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
                raw = r.read()
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            return raw.decode("utf-8")
        except Exception:
            time.sleep(3)
    return ""


def power_monthly(code, lat, lon):
    fp = os.path.join(CACHE, f"power_{code}.json")
    if os.path.exists(fp):
        return json.load(open(fp, encoding="utf-8"))
    q = {"parameters": "WS2M,T2M,PRECTOTCORR", "community": "AG",
         "longitude": lon, "latitude": lat, "start": "2015", "end": "2024", "format": "JSON"}
    txt = get("https://power.larc.nasa.gov/api/temporal/monthly/point?" + urllib.parse.urlencode(q))
    d = json.loads(txt) if txt.startswith("{") else {}
    json.dump(d, open(fp, "w", encoding="utf-8"), ensure_ascii=False)
    return d


def main():
    panel = pd.read_csv(os.path.join(RAW, "01_站点月尺度面板_real_raw.csv"), encoding="utf-8-sig")
    rows = []
    for name, code, lat, lon in STATIONS:
        d = power_monthly(code, lat, lon)
        par = d.get("properties", {}).get("parameter", {})
        if not par:
            print("skip", code)
            continue
        keys = list(par.get("WS2M", {}).keys())
        for k in keys:
            if not (k.isdigit() and len(k) == 6):
                continue
            y, m = int(k[:4]), int(k[4:])
            if y < 2015 or y > 2024:
                continue
            ws = par.get("WS2M", {}).get(k)
            t2 = par.get("T2M", {}).get(k)
            pr = par.get("PRECTOTCORR", {}).get(k)
            def ok(x):
                return x is not None and x != -999.0
            rows.append({"站代码": code, "月份": f"{y}-{m:02d}",
                         "POWER_风速": ws if ok(ws) else np.nan,
                         "POWER_气温": t2 if ok(t2) else np.nan,
                         "POWER_降水_日均": pr if ok(pr) else np.nan})
    pw = pd.DataFrame(rows)
    m = panel.merge(pw, on=["站代码", "月份"], how="inner")
    days = pd.to_datetime(m["月份"] + "-01").dt.days_in_month
    m["POWER_降水"] = m["POWER_降水_日均"] * days

    stats = []
    for v, pv in [("风速", "POWER_风速"), ("气温", "POWER_气温"), ("降水", "POWER_降水")]:
        a, b = m[v], m[pv]
        ok = a.notna() & b.notna()
        r = np.corrcoef(a[ok], b[ok])[0, 1] ** 2
        stats.append({"变量": v, "n": int(ok.sum()),
                      "ERA5均值": round(float(a[ok].mean()), 2),
                      "POWER均值": round(float(b[ok].mean()), 2),
                      "偏差(ERA5−POWER)": round(float((a[ok] - b[ok]).mean()), 2),
                      "RMSE": round(float(np.sqrt(((a[ok] - b[ok]) ** 2).mean())), 2),
                      "R²": round(float(r), 3)})
    st = pd.DataFrame(stats)
    st.to_csv(os.path.join(PROC, "07_交叉验证_POWER.csv"), index=False, encoding="utf-8-sig")

    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, (v, pv) in zip(axes, [("风速", "POWER_风速"), ("气温", "POWER_气温"), ("降水", "POWER_降水")]):
        a, b = m[v], m[pv]
        ok = a.notna() & b.notna()
        ax.scatter(b[ok], a[ok], s=6, alpha=.35, color="#4C78A8", edgecolors="none")
        lo = min(float(b[ok].min()), float(a[ok].min()))
        hi = max(float(b[ok].max()), float(a[ok].max()))
        ax.plot([lo, hi], [lo, hi], "--", color="#E45756", lw=1)
        row = st[st["变量"] == v].iloc[0]
        ax.set_title(f"{v}：R²={row['R²']:.3f}，RMSE={row['RMSE']}", fontsize=10)
        ax.set_xlabel(f"NASA POWER（MERRA-2）{v}")
        ax.set_ylabel(f"ERA5-Land {v}")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig8_交叉验证.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print(st.to_string(index=False))
    print("saved 07_交叉验证_POWER.csv, fig8_交叉验证.png")


if __name__ == "__main__":
    main()
