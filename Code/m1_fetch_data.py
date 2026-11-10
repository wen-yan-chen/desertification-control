"""Model 1 data download.  Run from the repository root:

    .venv/bin/python Code/m1_fetch_data.py

What it does (each step is skipped when its output already exists, so the run is
resumable and the committed raw files make everything downstream offline):

  A. MODIS MOD13Q1 summer NDVI over the Yutian-Minfeng area, 2001-03 and 2022-24
     -> used only to LOCATE windows objectively (no hand-picked pixels).
  B. Window selection: 9x9-pixel windows per land class (see m1_config.CLASS_RULES).
  C. MODIS NDVI + pixel_reliability time series 2001-2024 for every window.
  D. ERA5 / ERA5-Land daily forcing and hourly 10 m wind + gusts (Open-Meteo archive,
     model fixed to 'era5_seamless') for three forcing sites.
  E. NASA POWER daily meteorology at the same sites (independent ET0 cross-check).
  F. Legacy-source check: default 'best_match' vs explicit 'era5' at two legacy points.

Design rules (answers to the 2026-11-09 audit):
  * HTTPS certificates are verified (the legacy fetchers disabled verification).
  * The reanalysis model is requested explicitly and recorded.
  * Raw values are stored unmodified (gzip JSON) with URL, parameters, SHA-256, date.
  * A failed download stops the run; nothing is ever filled with synthetic values.
"""
import concurrent.futures as cf
import gzip
import hashlib
import json
import sys
import time
import warnings
from datetime import datetime, timezone

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")
import requests  # noqa: E402

import m1_config as C  # noqa: E402

MANIFEST = C.RAW / "manifest.json"
SESSION = requests.Session()
SESSION.headers.update({"Accept": "application/json", "User-Agent": C.USER_AGENT})


# ----------------------------------------------------------------------------- helpers
def get_json(url, params, timeout=180, retries=5):
    """GET with TLS verification, retries with back-off; returns parsed JSON."""
    last = None
    for k in range(retries):
        try:
            r = SESSION.get(url, params=params, timeout=timeout)
            if r.status_code != 200:                      # rate limit / server error: say so
                print(f"  HTTP {r.status_code} (try {k + 1}) {r.url[:150]}", flush=True)
                last = f"HTTP {r.status_code}"
                time.sleep(10 + 10 * k)
                continue
            return r.json()
        except Exception as exc:                          # network hiccup: retry
            last = exc
            print(f"  {type(exc).__name__} (try {k + 1}) {url[-40:]} {str(exc)[:80]}", flush=True)
            time.sleep(3 + 4 * k)
    raise RuntimeError(f"download failed after {retries} tries: {url} {params} :: {last}")


def save_gz(path, obj):
    """Write JSON deterministically (sorted keys, mtime=0) so hashes are stable."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    with open(path, "wb") as fh:
        with gzip.GzipFile(fileobj=fh, mode="wb", mtime=0) as gz:
            gz.write(payload)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_gz(path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def manifest_load():
    return json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {"files": {}}


def manifest_add(man, path, **meta):
    rel = path.relative_to(C.ROOT).as_posix()
    man["files"][rel] = dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                             retrieved_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d"), **meta)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")


def sin_to_lonlat(x, y):
    """MODIS sinusoidal metres -> geographic degrees (sphere radius SIN_R)."""
    lat = y / C.SIN_R
    lon = x / (C.SIN_R * np.cos(lat))
    return np.degrees(lon), np.degrees(lat)


# ----------------------------------------------------------------------------- A. area maps
def fetch_area(man):
    out = C.RAW / "modis_area"
    dates = [f"A{y}{d:03d}" for y in C.EPOCH_EARLY + C.EPOCH_LATE for d in C.SUMMER_DOYS]
    for date in dates:
        path = out / f"NDVI_{date}.json.gz"
        if path.exists():
            continue
        params = dict(latitude=C.AREA["lat"], longitude=C.AREA["lon"], band="250m_16_days_NDVI",
                      startDate=date, endDate=date,
                      kmAboveBelow=C.AREA["km_ns"], kmLeftRight=C.AREA["km_ew"])
        d = get_json(f"{C.MODIS_API}/{C.MODIS_PRODUCT}/subset", params)
        assert len(d["subset"]) == 1 and len(d["subset"][0]["data"]) == d["nrows"] * d["ncols"], date
        save_gz(path, d)
        manifest_add(man, path, source="ORNL DAAC MODIS subset API", product="MOD13Q1 v061",
                     url=f"{C.MODIS_API}/{C.MODIS_PRODUCT}/subset", request=params)
        print("area", date, d["nrows"], "x", d["ncols"], flush=True)
    return [out / f"NDVI_{d}.json.gz" for d in dates]


def area_epoch_means(files):
    """Mean summer NDVI for the early and late epochs + pixel lon/lat grids."""
    early, late, grid = [], [], None
    for f in files:
        d = load_gz(f)
        a = np.array(d["subset"][0]["data"], float).reshape(d["nrows"], d["ncols"]) * 1e-4
        a[a < -0.2] = np.nan                                   # fill value -3000
        year = int(d["subset"][0]["modis_date"][1:5])
        (early if year in C.EPOCH_EARLY else late).append(a)
        if grid is None:
            x = float(d["xllcorner"]) + (np.arange(d["ncols"]) + 0.5) * d["cellsize"]
            y = float(d["yllcorner"]) + (d["nrows"] - np.arange(d["nrows"]) - 0.5) * d["cellsize"]
            grid = sin_to_lonlat(*np.meshgrid(x, y))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanmean(early, axis=0), np.nanmean(late, axis=0), grid


# ----------------------------------------------------------------------------- B. windows
def classify(E, L):
    """Pixel classes exactly as written in m1_config.CLASS_RULES."""
    cls = np.full(E.shape, "", dtype=object)
    cls[(E < 0.08) & (L < 0.08)] = "desert"
    cls[(E >= 0.09) & (E <= 0.20) & (np.abs(L - E) < 0.04)] = "ecotone"
    cls[(E < 0.10) & (L >= 0.25)] = "converted"
    cls[(E >= 0.40) & (L >= 0.40)] = "oasis"
    return cls


def select_windows(E, L, grid):
    """Greedy choice of the purest 9x9 windows per class, separated by >= MIN_SEPARATION_KM.

    'converted' and 'ecotone' windows must lie on the desert fringe: at least 20 % of
    the surrounding ~10 km box is bare desert.  'desert' windows must be surrounded
    by desert only (>= 95 %), 'oasis' windows need no fringe condition.
    """
    from scipy.ndimage import uniform_filter
    lon, lat = grid
    cls = classify(E, L)
    px = 0.231656358264                                        # km per pixel
    half = 4                                                   # 9x9 window
    desert_big = uniform_filter((cls == "desert").astype(float), size=43, mode="constant")
    rows = []
    for name, n_win in C.WINDOWS_PER_CLASS.items():
        frac = uniform_filter((cls == name).astype(float), size=2 * half + 1, mode="constant")
        ok = np.ones(E.shape, bool)
        ok[:half + 1] = ok[-half - 1:] = False
        ok[:, :half + 1] = ok[:, -half - 1:] = False
        if name in ("converted", "ecotone"):
            ok &= desert_big >= 0.20
        if name == "desert":
            ok &= desert_big >= 0.95
        score = np.where(ok, frac, -1.0)
        chosen = []
        while len(chosen) < n_win:
            i, j = np.unravel_index(np.argmax(score), score.shape)
            if score[i, j] < 0.35:                             # window must be >= 35 % pure
                break
            chosen.append((i, j, score[i, j]))
            ii, jj = np.ogrid[:E.shape[0], :E.shape[1]]
            score[((ii - i) ** 2 + (jj - j) ** 2) * px ** 2 < C.MIN_SEPARATION_KM ** 2] = -1.0
        # order west -> east so that ids are stable and readable
        for k, (i, j, s) in enumerate(sorted(chosen, key=lambda t: lon[t[0], t[1]])):
            rows.append(dict(window=f"{name[:3].upper()}{k + 1}", cls=name,
                             lat=round(float(lat[i, j]), 5), lon=round(float(lon[i, j]), 5),
                             class_fraction=round(float(s), 3),
                             ndvi_early=round(float(np.nanmean(E[i - half:i + half + 1, j - half:j + half + 1])), 4),
                             ndvi_late=round(float(np.nanmean(L[i - half:i + half + 1, j - half:j + half + 1])), 4)))
    win = pd.DataFrame(rows)
    # nearest forcing site (great-circle distance is overkill at this scale)
    for idx, r in win.iterrows():
        d2 = {k: ((r.lat - la) * 111.0) ** 2 + ((r.lon - lo) * 111.0 * np.cos(np.radians(37))) ** 2
              for k, (la, lo) in C.FORCING_SITES.items()}
        win.loc[idx, "forcing_site"] = min(d2, key=d2.get)
        win.loc[idx, "forcing_dist_km"] = round(float(np.sqrt(min(d2.values()))), 1)
    area_stats = {k: int((cls == k).sum()) for k in C.CLASS_RULES}
    area_stats["total_pixels"] = int(cls.size)
    return win, area_stats


# ----------------------------------------------------------------------------- C. window series
def fetch_window_band(win, band, dates):
    """All composites of one band for one 9x9 window (API limit: 10 dates per request)."""
    url = f"{C.MODIS_API}/{C.MODIS_PRODUCT}/subset"
    chunks = [dates[i:i + 10] for i in range(0, len(dates), 10)]

    def one(chunk):
        p = dict(latitude=win.lat, longitude=win.lon, band=band, startDate=chunk[0], endDate=chunk[-1],
                 kmAboveBelow=C.WINDOW_KM, kmLeftRight=C.WINDOW_KM)
        d = get_json(url, p)
        got = [s["modis_date"] for s in d["subset"]]
        assert got == chunk, (win.window, band, chunk[0], got[:2])
        return d

    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        parts = list(pool.map(one, chunks))
    head = {k: parts[0][k] for k in ("xllcorner", "yllcorner", "cellsize", "nrows", "ncols", "band", "units", "scale")}
    head.update(window=win.window, request_lat=win.lat, request_lon=win.lon,
                modis_date=[s["modis_date"] for p in parts for s in p["subset"]],
                calendar_date=[s["calendar_date"] for p in parts for s in p["subset"]],
                proc_date=[s["proc_date"] for p in parts for s in p["subset"]],
                data=[s["data"] for p in parts for s in p["subset"]])
    assert all(len(v) == head["nrows"] * head["ncols"] for v in head["data"])
    return head


def fetch_windows(man, win):
    out = C.RAW / "modis_windows"
    first = win.iloc[0]
    all_dates = get_json(f"{C.MODIS_API}/{C.MODIS_PRODUCT}/dates",
                         dict(latitude=first.lat, longitude=first.lon))["dates"]
    dates = [d["modis_date"] for d in all_dates if C.Y0 <= int(d["modis_date"][1:5]) <= C.Y1]
    for w in win.itertuples():
        for band in C.MODIS_BANDS:
            path = out / f"{w.window}_{band.replace('250m_16_days_', '')}.json.gz"
            if path.exists():
                continue
            t0 = time.time()
            head = fetch_window_band(w, band, dates)
            save_gz(path, head)
            manifest_add(man, path, source="ORNL DAAC MODIS subset API", product="MOD13Q1 v061",
                         url=f"{C.MODIS_API}/{C.MODIS_PRODUCT}/subset",
                         request=dict(latitude=w.lat, longitude=w.lon, band=band, kmAboveBelow=C.WINDOW_KM,
                                      kmLeftRight=C.WINDOW_KM, first=dates[0], last=dates[-1]),
                         note="assembled from 10-date chunk responses; values unmodified")
            print(f"window {w.window} {band} {len(head['data'])} composites {time.time() - t0:.0f}s", flush=True)


# ----------------------------------------------------------------------------- D. reanalysis
def fetch_openmeteo(man):
    out = C.RAW / "openmeteo_era5"
    for site, (lat, lon) in C.FORCING_SITES.items():
        base = dict(latitude=lat, longitude=lon, models=C.OPENMETEO_MODEL, timezone=C.OPENMETEO_TZ,
                    wind_speed_unit="ms")
        # daily, whole period in one request
        path = out / f"{site}_daily.json.gz"
        if not path.exists():
            p = dict(base, start_date=f"{C.Y0}-01-01", end_date=f"{C.Y1}-12-31", daily=C.OM_DAILY)
            d = get_json(C.OPENMETEO_API, p, timeout=300)
            assert len(d["daily"]["time"]) > 8700, site
            save_gz(path, d)
            manifest_add(man, path, source="Open-Meteo Historical Weather API", url=C.OPENMETEO_API, request=p,
                         model=C.OPENMETEO_MODEL, grid=dict(lat=d["latitude"], lon=d["longitude"],
                                                            elevation_m=d.get("elevation")),
                         units=d["daily_units"])
            print("daily", site, len(d["daily"]["time"]), "days", flush=True)
            time.sleep(8)
        # hourly wind in 4-year blocks (keeps each response small)
        for y in range(C.Y0, C.Y1 + 1, 4):
            path = out / f"{site}_hourly_{y}_{min(y + 3, C.Y1)}.json.gz"
            if path.exists():
                continue
            p = dict(base, start_date=f"{y}-01-01", end_date=f"{min(y + 3, C.Y1)}-12-31", hourly=C.OM_HOURLY)
            d = get_json(C.OPENMETEO_API, p, timeout=300)
            save_gz(path, d)
            manifest_add(man, path, source="Open-Meteo Historical Weather API", url=C.OPENMETEO_API, request=p,
                         model=C.OPENMETEO_MODEL, grid=dict(lat=d["latitude"], lon=d["longitude"]),
                         units=d["hourly_units"])
            print("hourly", site, y, len(d["hourly"]["time"]), "h", flush=True)
            time.sleep(8)


# ----------------------------------------------------------------------------- E. NASA POWER
def fetch_power(man):
    out = C.RAW / "nasa_power_daily"
    for site, (lat, lon) in C.FORCING_SITES.items():
        path = out / f"{site}.json.gz"
        if path.exists():
            continue
        p = dict(parameters=C.POWER_PARAMS, community="AG", longitude=lon, latitude=lat,
                 start=f"{C.Y0}0101", end=f"{C.Y1}1231", format="JSON")
        d = get_json(C.POWER_API, p, timeout=300)
        assert d["properties"]["parameter"], site
        save_gz(path, d)
        manifest_add(man, path, source="NASA POWER daily API (MERRA-2 / CERES SYN1deg)", url=C.POWER_API,
                     request=p, units={k: v.get("units") for k, v in d["parameters"].items()})
        print("power", site, flush=True)


# ----------------------------------------------------------------------------- F. legacy check
def legacy_break_check(man):
    """Quantify the audit claim 'legacy meteorology model unspecified'.

    The legacy panel called Open-Meteo WITHOUT models=..., i.e. 'best_match'.  We
    request the same daily variables at two legacy points with (a) no model and
    (b) models=era5 and store yearly means.  If (a) == (b) up to some year and then
    departs, the legacy series contains a source change (a spurious break).
    """
    path = C.RES / "legacy_source_break.csv"
    if path.exists():
        return
    rows = []
    daily = ("wind_speed_10m_mean,wind_speed_10m_max,precipitation_sum,"
             "soil_moisture_0_to_7cm_mean,soil_moisture_0_to_100cm_mean,temperature_2m_mean")
    for code, lat, lon in (("MF", 37.06, 82.68), ("TZ", 38.97, 83.65)):
        for label, model in (("best_match_default", None), ("era5_explicit", "era5")):
            p = dict(latitude=lat, longitude=lon, start_date="2015-01-01", end_date="2024-12-31",
                     timezone="Asia/Shanghai", wind_speed_unit="ms", daily=daily)
            if model:
                p["models"] = model
            d = get_json(C.OPENMETEO_API, p, timeout=300)
            df = pd.DataFrame(d["daily"])
            df["year"] = df["time"].str[:4].astype(int)
            g = df.drop(columns="time").groupby("year").mean()
            g["precipitation_sum"] = df.groupby("year")["precipitation_sum"].sum()     # mm / yr
            for year, r in g.iterrows():
                rows.append(dict(point=code, source=label, year=year, **r.round(4).to_dict()))
            time.sleep(8)
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    print("legacy source check ->", path.relative_to(C.ROOT), flush=True)


# ----------------------------------------------------------------------------- main
def main():
    man = manifest_load()
    files = fetch_area(man)
    E, L, grid = area_epoch_means(files)
    C.PROC.mkdir(parents=True, exist_ok=True)
    wpath = C.PROC / "windows.csv"
    if wpath.exists():                                         # keep selection frozen once made
        win = pd.read_csv(wpath)
    else:
        win, stats = select_windows(E, L, grid)
        win.to_csv(wpath, index=False)
        (C.PROC / "area_class_counts.json").write_text(json.dumps(stats, indent=1))
        np.savez_compressed(C.PROC / "area_ndvi_epochs.npz", early=E.astype("float32"),
                            late=L.astype("float32"), lon=grid[0].astype("float32"),
                            lat=grid[1].astype("float32"))
    print(win.to_string(index=False), flush=True)
    fetch_windows(man, win)
    fetch_openmeteo(man)
    fetch_power(man)
    legacy_break_check(man)
    print("all model-1 raw data present; manifest:", MANIFEST.relative_to(C.ROOT))


if __name__ == "__main__":
    sys.exit(main())
