# -*- coding: utf-8 -*-
"""
01b_fetch_ndvi.py —— 并发抓取 MODIS MOD13Q1 NDVI（分块缓存，可断点续跑）
服务端单次请求最多约 9 个合成日期，故按“每年 3 块（9+9+5）”切分；
用线程池并发（默认 6 并发），单块结果落盘到 数据/cache/ndvi/<站代码>/<起日期>.json
"""
import gzip
import json
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(BASE, "数据", "cache", "ndvi")
os.makedirs(CACHE, exist_ok=True)

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}

Y0, Y1 = 2015, 2024
STATIONS = [("塔中", "TZ", 38.97, 83.65), ("肖塘", "XT", 38.83, 84.02),
            ("且末", "QM", 38.13, 85.53), ("民丰", "MF", 37.06, 82.68),
            ("若羌", "RQ", 39.02, 88.17), ("库尔勒", "KEL", 41.76, 86.15),
            ("尉犁", "YL", 41.34, 86.26), ("阿拉尔", "ALE", 40.55, 81.28)]
WORKERS = 6


def fetch_chunk(code, lat, lon, dates):
    """dates: 该块包含的 MODIS 日期列表（≤9 个）"""
    fp = os.path.join(CACHE, code, f"{dates[0]}.json")
    if os.path.exists(fp):
        try:
            return json.load(open(fp, encoding="utf-8")), "cached"
        except Exception:
            pass
    q = {"latitude": lat, "longitude": lon, "band": "250m_16_days_NDVI",
         "startDate": dates[0], "endDate": dates[-1],
         "kmAboveBelow": 0, "kmLeftRight": 0}
    url = "https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset?" + urllib.parse.urlencode(q)
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=90, context=CTX) as r:
                raw = r.read()
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            d = json.loads(raw.decode("utf-8"))
            out = [{"modis_date": it["modis_date"], "calendar_date": it["calendar_date"],
                    "ndvi_raw": (it.get("data") or [None])[0]} for it in d.get("subset", [])]
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            json.dump(out, open(fp, "w", encoding="utf-8"), ensure_ascii=False)
            return out, "ok"
        except Exception as e:
            if attempt == 3:
                return None, f"fail:{str(e)[:60]}"
            time.sleep(2 * (attempt + 1))


def main():
    tasks = []
    for name, code, lat, lon in STATIONS:
        for y in range(Y0, Y1 + 1):
            ds = [f"A{y}{d:03d}" for d in range(1, 354, 16)]
            for i in range(0, len(ds), 9):
                tasks.append((code, lat, lon, ds[i:i + 9]))
    print(f"共 {len(tasks)} 个分块，{WORKERS} 并发", flush=True)
    t0 = time.time()
    done = ok = fail = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(fetch_chunk, c, la, lo, d): (c, d[0]) for c, la, lo, d in tasks}
        for f in as_completed(futs):
            c, d0 = futs[f]
            res, status = f.result()
            done += 1
            if status.startswith("fail"):
                fail += 1
                print(f"  [fail] {c} {d0} {status}", flush=True)
            else:
                ok += 1
            if done % 20 == 0 or done == len(tasks):
                el = time.time() - t0
                print(f"  进度 {done}/{len(tasks)}  成功 {ok}  失败 {fail}  "
                      f"用时 {el/60:.1f} min", flush=True)
    print(f"完成：{ok} 成功 / {fail} 失败，总用时 {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
