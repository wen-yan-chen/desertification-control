# -*- coding: utf-8 -*-
"""
v7_finalize_fetch.py —— 合并 MODIS 分块 + 重建 manifest

背景：v7_fetch.py 里 MODIS 分块缓存与"原始响应另行落盘"用了同一路径，
      结果 _cache/modis/**.json 里保存的是服务端原始响应（dict，含 subset），
      不是解析后的列表。原始响应是完好的，本脚本直接从缓存重新解析并合并，
      不需要重新请求；同时按文件重建 manifest（哈希可逐文件复核）。
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.parse
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "Data", "v7", "raw")
CACHE = os.path.join(RAW, "_cache")
Y0, Y1 = 2015, 2025

SITES = [
    ("YT", "于田", 36.85, 81.67), ("MF", "民丰", 37.06, 82.68),
    ("QM", "且末", 38.13, 85.53), ("RQ", "若羌", 39.02, 88.17),
    ("KEL", "库尔勒", 41.76, 86.15), ("YL", "尉犁", 41.34, 86.26),
    ("ALE", "阿拉尔", 40.55, 81.28), ("XT", "肖塘", 38.83, 84.02),
    ("TZ", "塔中", 38.97, 83.65),
]
POWER_M = ["PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "RH2M", "QV2M", "PS",
           "WS10M", "WS10M_MAX", "WS2M", "GWETROOT", "GWETPROF", "GWETTOP",
           "ALLSKY_SFC_SW_DWN", "EVLAND", "WD10M"]
POWER_D = ["PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "WS10M", "WS10M_MAX",
           "WS2M", "RH2M", "GWETROOT", "ALLSKY_SFC_SW_DWN"]
ERA5 = ["soil_moisture_0_to_7cm_mean", "soil_moisture_7_to_28cm_mean",
        "soil_moisture_28_to_100cm_mean", "soil_moisture_100_to_255cm_mean",
        "et0_fao_evapotranspiration", "precipitation_sum", "temperature_2m_mean",
        "temperature_2m_max", "temperature_2m_min", "wind_speed_10m_max",
        "wind_gusts_10m_max", "shortwave_radiation_sum",
        "vapour_pressure_deficit_max", "relative_humidity_2m_mean"]
SOIL = ["sand", "silt", "clay", "soc", "bdod", "cec"]
DEPTHS = ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"]
LAT = {s[0]: s[2] for s in SITES}
LON = {s[0]: s[3] for s in SITES}


def parse_records(d):
    if isinstance(d, list):
        return d
    return [{"modis_date": it["modis_date"], "calendar_date": it["calendar_date"],
             "tile": it.get("tile"), "proc_date": it.get("proc_date"),
             "data": it.get("data") or []}
            for it in d.get("subset", [])]


def merge_modis():
    stat = {}
    for band, tag in (("250m_16_days_NDVI", "NDVI"),
                      ("250m_16_days_pixel_reliability", "QA")):
        for code, *_ in SITES:
            d = os.path.join(CACHE, "modis", code)
            recs = []
            if os.path.isdir(d):
                for fn in sorted(os.listdir(d)):
                    if not fn.startswith(band):
                        continue
                    with open(os.path.join(d, fn), encoding="utf-8") as f:
                        recs.extend(parse_records(json.load(f)))
            seen, uniq = set(), []
            for r in sorted(recs, key=lambda x: x["modis_date"]):
                if r["modis_date"] in seen:
                    continue
                seen.add(r["modis_date"])
                uniq.append(r)
            rel = os.path.join(RAW, f"modis_{code}_{tag}.json")
            with open(rel, "w", encoding="utf-8") as f:
                json.dump(uniq, f, ensure_ascii=False)
            stat[f"{code}_{tag}"] = len(uniq)
    return stat


def sha(fp):
    h = hashlib.sha256()
    with open(fp, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def url_for(fn: str) -> tuple[str, str]:
    stem = fn.rsplit(".", 1)[0]
    if stem.startswith("power_monthly_"):
        c = stem.split("_")[-1]
        u = ("https://power.larc.nasa.gov/api/temporal/monthly/point"
             f"?parameters={','.join(POWER_M)}&community=AG"
             f"&longitude={LON[c]}&latitude={LAT[c]}&start={Y0}&end={Y1}&format=JSON")
        return u, f"POWER monthly {LAT[c]},{LON[c]}"
    if stem.startswith("power_daily_"):
        c = stem.split("_")[-1]
        u = ("https://power.larc.nasa.gov/api/temporal/daily/point"
             f"?parameters={','.join(POWER_D)}&community=AG"
             f"&longitude={LON[c]}&latitude={LAT[c]}&start={Y0}0101&end={Y1}1231&format=JSON")
        return u, f"POWER daily {LAT[c]},{LON[c]}"
    if stem.startswith("era5land_"):
        c = stem.split("_")[-1]
        u = ("https://archive-api.open-meteo.com/v1/archive"
             f"?latitude={LAT[c]}&longitude={LON[c]}&start_date={Y0}-01-01&end_date={Y1}-12-31"
             f"&daily={','.join(ERA5)}&timezone=Asia%2FShanghai")
        return u, f"ERA5-Land daily {LAT[c]},{LON[c]}"
    if stem.startswith("soilgrids_"):
        c = stem.split("_")[-1]
        u = ("https://rest.isric.org/soilgrids/v2.0/properties/query"
             f"?lon={LON[c]}&lat={LAT[c]}"
             + "".join(f"&property={p}" for p in SOIL)
             + "".join(f"&depth={d}" for d in DEPTHS) + "&value=mean")
        return u, f"SoilGrids {LAT[c]},{LON[c]}"
    return "", ""


def rebuild_manifest():
    req = []
    for root, _, files in os.walk(RAW):
        for fn in sorted(files):
            if not fn.endswith(".json") or fn == "manifest.json":
                continue
            fp = os.path.join(root, fn)
            rel = os.path.relpath(fp, RAW).replace("\\", "/")
            if rel.startswith("_cache/modis"):
                # _cache/modis/<CODE>/<band>_<Ayyyyddd>.json
                parts = rel.split("/")
                code = parts[-2]
                band, start = fn.rsplit(".", 1)[0].split("_A")
                doys = f"A{start}"
                q = urllib.parse.urlencode({
                    "latitude": LAT[code], "longitude": LON[code], "band": band,
                    "startDate": doys, "endDate": doys,
                    "kmAboveBelow": 1, "kmLeftRight": 1})
                # endDate 取该块最后一期：由文件名只能确定首期，这里标注为分块首期
                u = "https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset?" + q
                note = f"MOD13Q1 {band} {code} 分块起始 {doys}"
            else:
                u, note = url_for(fn)
            req.append({"file": rel, "url": u,
                        "bytes": os.path.getsize(fp), "sha256": sha(fp),
                        "fetched_utc": datetime.fromtimestamp(
                            os.path.getmtime(fp), timezone.utc).isoformat(timespec="seconds"),
                        "note": note})
    man = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "period": f"{Y0}-01-01..{Y1}-12-31",
           "sites": [{"code": s[0], "name": s[1], "lat": s[2], "lon": s[3]} for s in SITES],
           "requests": req, "n_requests": len(req),
           "n_bytes": int(sum(r["bytes"] for r in req))}
    with open(os.path.join(RAW, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=1)
    return man


if __name__ == "__main__":
    st = merge_modis()
    print("MODIS 合并：", json.dumps(st, ensure_ascii=False), flush=True)
    man = rebuild_manifest()
    print(f"manifest: {man['n_requests']} 个文件, {man['n_bytes']/1e6:.1f} MB", flush=True)
