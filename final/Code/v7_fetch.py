# -*- coding: utf-8 -*-
"""
v7_fetch.py —— 重新采集原始数据（2026-11-10 版，不复用任何既有工作区数据）

四个互相独立的来源：
  1) NASA POWER  point API   —— 月度（16 参数）+ 日值（10 参数），2015-01-01 ~ 2025-12-31
  2) ORNL DAAC MODIS RST     —— MOD13Q1 NDVI + pixel_reliability，250 m / 16 d，9x9 像元窗口
  3) Open-Meteo ERA5-Land    —— 日值：4 层土壤含水量、ET0、降水、气温、风速、辐射、VPD
  4) ISRIC SoilGrids v2.0    —— 6 层砂/粉/黏/有机碳/容重（用于计算有效持水量）

所有原始响应按"请求"落盘并写入 manifest（URL / 字节数 / SHA256 / UTC 时间 / 状态），
保证报告里的每个数字都能回溯到一次具体请求。断点续跑：MODIS 分块缓存在 _cache/。
"""
from __future__ import annotations

import concurrent.futures as cf
import gzip
import hashlib
import json
import os
import ssl
import sys
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "Data", "v7", "raw")
CACHE = os.path.join(RAW, "_cache")
MANIFEST = os.path.join(RAW, "manifest.json")

Y0, Y1 = 2015, 2025
WORKERS = 14

SITES = [
    ("YT",  "于田",   36.85,  81.67, "南缘锁边区段（于田—民福段）"),
    ("MF",  "民丰",   37.06,  82.68, "南缘锁边区段"),
    ("QM",  "且末",   38.13,  85.53, "南缘锁边区段"),
    ("RQ",  "若羌",   39.02,  88.17, "东南缘锁边区段"),
    ("KEL", "库尔勒", 41.76,  86.15, "北缘（塔里木河下游）"),
    ("YL",  "尉犁",   41.34,  86.26, "北缘（塔里木河下游）"),
    ("ALE", "阿拉尔", 40.55,  81.28, "西北缘（阿克苏河）"),
    ("XT",  "肖塘",   38.83,  84.02, "沙漠公路走廊（人工防护林）"),
    ("TZ",  "塔中",   38.97,  83.65, "腹地对照点（非锁边带）"),
]

POWER_MONTHLY_PARAMS = [
    "PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "RH2M", "QV2M", "PS",
    "WS10M", "WS10M_MAX", "WS2M", "GWETROOT", "GWETPROF", "GWETTOP",
    "ALLSKY_SFC_SW_DWN", "EVLAND", "WD10M",
]
POWER_DAILY_PARAMS = [
    "PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "WS10M", "WS10M_MAX",
    "WS2M", "RH2M", "GWETROOT", "ALLSKY_SFC_SW_DWN",
]
ERA5_VARS = [
    "soil_moisture_0_to_7cm_mean", "soil_moisture_7_to_28cm_mean",
    "soil_moisture_28_to_100cm_mean", "soil_moisture_100_to_255cm_mean",
    "et0_fao_evapotranspiration", "precipitation_sum",
    "temperature_2m_mean", "temperature_2m_max", "temperature_2m_min",
    "wind_speed_10m_max", "wind_gusts_10m_max", "shortwave_radiation_sum",
    "vapour_pressure_deficit_max", "relative_humidity_2m_mean",
]
SOIL_PROPS = ["sand", "silt", "clay", "soc", "bdod", "cec"]
SOIL_DEPTHS = ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"]

UA = {"User-Agent": "Mozilla/5.0 (research data collection; CQU_MCM 2026 B)"}
_LOCK = threading.Lock()
_MAN: list[dict] = []
CTX = ssl.create_default_context()


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def get(url: str, retries: int = 5, timeout: int = 240) -> bytes:
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
                raw = r.read()
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            if raw[:1] == b"<":
                raise RuntimeError("HTML/error page")
            return raw
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (2 ** i))
    raise RuntimeError(f"GET failed: {last}")


def save(rel: str, raw: bytes, url: str, note: str = "") -> None:
    fp = os.path.join(RAW, rel)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, "wb") as f:
        f.write(raw)
    with _LOCK:
        _MAN.append({"file": rel.replace("\\", "/"), "url": url, "bytes": len(raw),
                     "sha256": _sha(raw),
                     "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                     "note": note})


def record_cached(rel: str, url: str, note: str) -> None:
    """复用上一轮已落盘的文件，仍写入 manifest（哈希取本地文件）"""
    fp = os.path.join(RAW, rel)
    if not os.path.exists(fp):
        return
    with open(fp, "rb") as f:
        raw = f.read()
    with _LOCK:
        _MAN.append({"file": rel.replace("\\", "/"), "url": url, "bytes": len(raw),
                     "sha256": _sha(raw),
                     "fetched_utc": datetime.fromtimestamp(
                         os.path.getmtime(fp), timezone.utc).isoformat(timespec="seconds"),
                     "note": note + "（复用前一轮缓存）"})


# ------------------------------------------------------------------ 单个任务
def t_power_monthly(s):
    code, lat, lon = s[0], s[2], s[3]
    rel = f"power_monthly_{code}.json"
    url = ("https://power.larc.nasa.gov/api/temporal/monthly/point"
           f"?parameters={','.join(POWER_MONTHLY_PARAMS)}&community=AG"
           f"&longitude={lon}&latitude={lat}&start={Y0}&end={Y1}&format=JSON")
    if os.path.exists(os.path.join(RAW, rel)):
        record_cached(rel, url, f"POWER monthly {lat},{lon}")
        return rel, "cached"
    save(rel, get(url), url, f"POWER monthly {lat},{lon}")
    return rel, "ok"


def t_power_daily(s):
    code, lat, lon = s[0], s[2], s[3]
    rel = f"power_daily_{code}.json"
    url = ("https://power.larc.nasa.gov/api/temporal/daily/point"
           f"?parameters={','.join(POWER_DAILY_PARAMS)}&community=AG"
           f"&longitude={lon}&latitude={lat}&start={Y0}0101&end={Y1}1231&format=JSON")
    if os.path.exists(os.path.join(RAW, rel)):
        record_cached(rel, url, f"POWER daily {lat},{lon}")
        return rel, "cached"
    save(rel, get(url), url, f"POWER daily {lat},{lon}")
    return rel, "ok"


def t_era5(s):
    code, lat, lon = s[0], s[2], s[3]
    rel = f"era5land_{code}.json"
    url = ("https://archive-api.open-meteo.com/v1/archive"
           f"?latitude={lat}&longitude={lon}&start_date={Y0}-01-01&end_date={Y1}-12-31"
           f"&daily={','.join(ERA5_VARS)}&timezone=Asia%2FShanghai")
    if os.path.exists(os.path.join(RAW, rel)):
        record_cached(rel, url, f"ERA5 daily {lat},{lon}")
        return rel, "cached"
    save(rel, get(url), url, f"ERA5-Land daily {lat},{lon}")
    return rel, "ok"


def t_soil(s):
    code, lat, lon = s[0], s[2], s[3]
    rel = f"soilgrids_{code}.json"
    props = "&".join(f"property={p}" for p in SOIL_PROPS)
    depth = "&".join(f"depth={d}" for d in SOIL_DEPTHS)
    url = (f"https://rest.isric.org/soilgrids/v2.0/properties/query"
           f"?lon={lon}&lat={lat}&{props}&{depth}&value=mean")
    if os.path.exists(os.path.join(RAW, rel)):
        record_cached(rel, url, f"SoilGrids {lat},{lon}")
        return rel, "cached"
    save(rel, get(url, retries=3, timeout=300), url, f"SoilGrids {lat},{lon}")
    return rel, "ok"


def modis_task(band, s, ds):
    """ds: 至多 10 个合成期（服务端限制 'maximum subset tiles support of 10'）"""
    code, lat, lon = s[0], s[2], s[3]
    ck = os.path.join(CACHE, "modis", code, f"{band}_{ds[0]}.json")
    q = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon, "band": band,
        "startDate": ds[0], "endDate": ds[-1],
        "kmAboveBelow": 1, "kmLeftRight": 1,
    })
    url = "https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset?" + q
    if os.path.exists(ck):
        record_cached(os.path.join("_cache", "modis", code, f"{band}_{ds[0]}.json"),
                      url, f"MOD13Q1 {band} {code} {ds[0]}-{ds[-1]}")
        return ck, "cached"
    raw = get(url, timeout=150)
    d = json.loads(raw.decode("utf-8"))
    recs = [{"modis_date": it["modis_date"], "calendar_date": it["calendar_date"],
             "tile": it.get("tile"), "data": it.get("data") or []}
            for it in d.get("subset", [])]
    os.makedirs(os.path.dirname(ck), exist_ok=True)
    with open(ck, "w", encoding="utf-8") as f:
        json.dump(recs, f)
    save(os.path.join("_cache", "modis", code, f"{band}_{ds[0]}.json"), raw, url,
         f"MOD13Q1 {band} {code} {ds[0]}-{ds[-1]}")
    return ck, "ok"


def merge_modis():
    out = {}
    for band, tag in (("250m_16_days_NDVI", "NDVI"),
                      ("250m_16_days_pixel_reliability", "QA")):
        for s in SITES:
            code = s[0]
            d = os.path.join(CACHE, "modis", code)
            if not os.path.isdir(d):
                continue
            recs = []
            for fn in sorted(os.listdir(d)):
                if not fn.startswith(band):
                    continue
                with open(os.path.join(d, fn), encoding="utf-8") as f:
                    recs.extend(json.load(f))
            seen, uniq = set(), []
            for r in sorted(recs, key=lambda x: x["modis_date"]):
                if r["modis_date"] in seen:
                    continue
                seen.add(r["modis_date"])
                uniq.append(r)
            rel = f"modis_{code}_{tag}.json"
            with open(os.path.join(RAW, rel), "w", encoding="utf-8") as f:
                json.dump(uniq, f, ensure_ascii=False)
            out[f"{code}_{tag}"] = len(uniq)
    return out


def main():
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(CACHE, exist_ok=True)
    t0 = time.time()

    tasks = []
    # 先排 MODIS（请求多、单次 ~4 s），再排 POWER/ERA5，SoilGrids 单独放最后
    for s in SITES:
        for y in range(Y0, Y1 + 1):
            doys = list(range(1, 361, 16))
            for i in range(0, len(doys), 10):
                ds = [f"A{y}{d:03d}" for d in doys[i:i + 10]]
                for band in ("250m_16_days_NDVI", "250m_16_days_pixel_reliability"):
                    tasks.append((modis_task, (band, s, ds)))
    for s in SITES:
        tasks += [(t_power_monthly, (s,)), (t_power_daily, (s,)), (t_era5, (s,))]
    print(f"任务数 {len(tasks)}，并发 {WORKERS}", flush=True)

    done = 0
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(f, *a): (f.__name__, a) for f, a in tasks}
        for f in cf.as_completed(futs):
            name, a = futs[f]
            done += 1
            try:
                f.result()
            except Exception as e:  # noqa: BLE001
                print(f"[FAIL] {name} {a[0] if a else ''}: {str(e)[:160]}", flush=True)
            if done % 60 == 0 or done == len(tasks):
                print(f"  进度 {done}/{len(tasks)}  {time.time()-t0:.0f}s", flush=True)

    mm = merge_modis()
    print("MODIS 合并：", mm, flush=True)

    # SoilGrids 单请求 60 s 量级，不与 MODIS 争并发
    print("--- SoilGrids ---", flush=True)
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(t_soil, s): s[0] for s in SITES}
        for f in cf.as_completed(futs):
            c = futs[f]
            try:
                f.result()
                print(f"[ok] soil_{c}", flush=True)
            except Exception as e:  # noqa: BLE001
                print(f"[FAIL] soil_{c}: {str(e)[:160]}", flush=True)

    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump({"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "period": f"{Y0}-01-01..{Y1}-12-31",
                   "sites": [{"code": s[0], "name": s[1], "lat": s[2], "lon": s[3],
                              "role": s[4]} for s in SITES],
                   "requests": _MAN}, f, ensure_ascii=False, indent=1)
    print(f"完成 {(time.time()-t0)/60:.1f} min，本轮新请求 {len(_MAN)} 条", flush=True)


if __name__ == "__main__":
    main()

