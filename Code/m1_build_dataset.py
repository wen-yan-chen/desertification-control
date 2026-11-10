"""Model 1 dataset: turn the raw downloads into the tables the model uses.  Offline.

    .venv/bin/python Code/m1_build_dataset.py

Outputs in Data/processed/model1/ :
  forcing_<site>.csv        daily P, T, ET0 (own FAO-56 Penman-Monteith + provider value),
                            ERA5-Land soil layers, drift potential DP (hourly based)
  endmembers.json           NDVI of bare sand / dense vegetation read from the data
  pixel_annual_fvc.csv      peak-season cover of every window pixel, every year, with QA counts
  class_annual_fvc.csv      class medians / quartiles per year
  cohort_converted.csv      converted pixels aligned on their establishment year
  data_summary.json         numbers quoted in the documentation

How the audit findings are handled here
  * NDVI quality: MOD13Q1 pixel_reliability is used; only 0 (good) and 1 (marginal)
    are kept; snow/ice (2), cloud (3) and fill (-1) are dropped.  Nothing is interpolated.
  * Cover (FVC): end-members come from this section's own desert and oasis pixels,
    not from fixed 0.05 / 0.85.
  * ET0: full FAO-56 Penman-Monteith from Tmax, Tmin, dew point, wind, radiation,
    pressure - not a temperature proxy.  Cross-checked against two independent sources.
  * Sand driver: drift potential from HOURLY wind, never from monthly or daily means.
  * No winsorising: extremes are the signal for Task 3.
"""
import gzip
import json
import warnings

import numpy as np
import pandas as pd

import m1_config as C

KNOT = 0.514444                 # m/s per knot
U_T_KNOTS = 12.0                # threshold wind at 10 m, = 6.2 m/s (Fryberger 1979; "about 6 m/s"
#                                 in Yizhaq & Ashkenazy 2021 p.5; >= 6.0 m/s in Zhang et al. 2016 p.5)
DP_MULT = np.array([1.0, 1.15, 1.3, 1.5, 1.75, 2.0, 2.5, 3.0])   # threshold multipliers (wet surface)
PEAK_DOYS = (193, 209, 225, 241)   # composites of mid-Jul .. early-Sep = "peak season"


def load_gz(path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------------------- ET0
def et0_fao56(tmax, tmin, tdew, u10, rs, ps_hpa, lat_deg, elev_m, doy):
    """Daily reference evapotranspiration, FAO-56 Eq. 6 (mm/day).

    tmax, tmin, tdew [deg C]; u10 = wind speed at 10 m [m/s]; rs = shortwave radiation
    [MJ m-2 day-1]; ps_hpa = surface pressure [hPa].  Equation numbers refer to FAO-56.
    """
    tmean = (tmax + tmin) / 2.0
    e0 = lambda t: 0.6108 * np.exp(17.27 * t / (t + 237.3))                 # Eq. 11, kPa
    es = (e0(tmax) + e0(tmin)) / 2.0                                          # Eq. 12
    ea = e0(tdew)                                                             # Eq. 14
    delta = 4098.0 * e0(tmean) / (tmean + 237.3) ** 2                         # Eq. 13
    gamma = 0.000665 * ps_hpa / 10.0                                          # Eq. 8 (kPa)
    u2 = u10 * 4.87 / np.log(67.8 * 10.0 - 5.42)                              # Eq. 47, 10 m -> 2 m
    lat = np.radians(lat_deg)
    dr = 1.0 + 0.033 * np.cos(2 * np.pi * doy / 365.0)                        # Eq. 23
    dec = 0.409 * np.sin(2 * np.pi * doy / 365.0 - 1.39)                      # Eq. 24
    ws = np.arccos(-np.tan(lat) * np.tan(dec))                                # Eq. 25
    ra = 24 * 60 / np.pi * 0.0820 * dr * (ws * np.sin(lat) * np.sin(dec)
                                         + np.cos(lat) * np.cos(dec) * np.sin(ws))   # Eq. 21
    rso = (0.75 + 2e-5 * elev_m) * ra                                         # Eq. 37
    rns = (1.0 - 0.23) * rs                                                   # Eq. 38
    sigma = 4.903e-9
    rnl = sigma * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2.0 \
        * (0.34 - 0.14 * np.sqrt(ea)) * (1.35 * np.minimum(rs / rso, 1.0) - 0.35)    # Eq. 39
    rn = rns - rnl
    num = 0.408 * delta * rn + gamma * 900.0 / (tmean + 273.0) * u2 * (es - ea)
    return np.maximum(num / (delta + gamma * (1.0 + 0.34 * u2)), 0.0)


# ------------------------------------------------------------------------------- forcing
def build_forcing(site):
    raw = C.RAW / "openmeteo_era5"
    d = load_gz(raw / f"{site}_daily.json.gz")
    df = pd.DataFrame(d["daily"]).rename(columns={"time": "date"})
    df["date"] = pd.to_datetime(df["date"])
    lat, elev = d["latitude"], d["elevation"]
    doy = df["date"].dt.dayofyear.values
    df["ET0"] = et0_fao56(df.temperature_2m_max.values, df.temperature_2m_min.values,
                          df.dew_point_2m_mean.values, df.wind_speed_10m_mean.values,
                          df.shortwave_radiation_sum.values, df.surface_pressure_mean.values,
                          lat, elev, doy).round(3)
    df = df.rename(columns={"precipitation_sum": "P", "temperature_2m_mean": "T",
                            "et0_fao_evapotranspiration": "ET0_provider"})
    # 15-day centred mean temperature drives phenology (avoids day-to-day flicker)
    df["Tsm"] = df["T"].rolling(15, center=True, min_periods=1).mean().round(2)

    # hourly wind -> daily drift potential for each threshold multiplier
    hh = []
    for f in sorted(raw.glob(f"{site}_hourly_*.json.gz")):
        h = load_gz(f)["hourly"]
        hh.append(pd.DataFrame(h))
    h = pd.concat(hh, ignore_index=True)
    h["date"] = pd.to_datetime(h["time"].str[:10])
    for name, col in (("mean", "wind_speed_10m"), ("gust", "wind_gusts_10m")):
        u = h[col].values / KNOT
        for m in DP_MULT:
            h[f"x_{name}_{m}"] = u ** 2 * np.clip(u - U_T_KNOTS * m, 0, None)
    h["h6_mean"] = (h["wind_speed_10m"] >= 6.0).astype(float)
    h["h6_gust"] = (h["wind_gusts_10m"] >= 6.0).astype(float)
    g = h.groupby("date")
    daily = g[[c for c in h.columns if c.startswith("x_")]].mean()     # DP_day = <U^2 (U-Ut)+>
    daily.columns = [c.replace("x_", "DP_") for c in daily.columns]
    daily["hours_ge6_mean"] = g["h6_mean"].sum()
    daily["hours_ge6_gust"] = g["h6_gust"].sum()
    daily["n_hours"] = g["wind_speed_10m"].count()
    # resultant drift direction needs the vector sum; store daily vector components (mean wind)
    u = h["wind_speed_10m"].values / KNOT
    w = u ** 2 * np.clip(u - U_T_KNOTS, 0, None)
    ang = np.radians(h["wind_direction_10m"].values)             # direction the wind comes FROM
    h["dpx"], h["dpy"] = -w * np.sin(ang), -w * np.cos(ang)       # transport vector (towards)
    daily["DPx"], daily["DPy"] = g["dpx"].mean(), g["dpy"].mean()
    df = df.merge(daily.reset_index(), on="date", how="left")
    assert df[["P", "ET0", "T", "DP_mean_1.0"]].notna().all().all(), site
    assert (df["n_hours"] == 24).all(), site
    df.attrs.update(lat=lat, lon=d["longitude"], elev=elev)
    return df


def power_et0(site):
    """Independent ET0 from NASA POWER (MERRA-2 / CERES) with the same FAO-56 function."""
    d = load_gz(C.RAW / "nasa_power_daily" / f"{site}.json.gz")
    par = d["properties"]["parameter"]
    df = pd.DataFrame(par)
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df = df.replace(-999.0, np.nan)
    elev = d["geometry"]["coordinates"][2]
    lat = d["geometry"]["coordinates"][1]
    # POWER gives RH and 2 m wind: convert to the function's inputs
    tmean = (df.T2M_MAX + df.T2M_MIN) / 2
    es = (0.6108 * np.exp(17.27 * df.T2M_MAX / (df.T2M_MAX + 237.3))
          + 0.6108 * np.exp(17.27 * df.T2M_MIN / (df.T2M_MIN + 237.3))) / 2
    ea = es * df.RH2M / 100.0
    tdew = 237.3 * np.log(ea / 0.6108) / (17.27 - np.log(ea / 0.6108))
    u10 = df.WS2M * np.log(67.8 * 10.0 - 5.42) / 4.87            # inverse of Eq. 47
    et0 = et0_fao56(df.T2M_MAX.values, df.T2M_MIN.values, tdew.values, u10.values,
                    df.ALLSKY_SFC_SW_DWN.values, df.PS.values * 10.0, lat, elev,
                    df.index.dayofyear.values)
    return pd.DataFrame({"ET0_power": et0, "P_power": df.PRECTOTCORR.values, "T_power": tmean.values},
                        index=df.index)


# ------------------------------------------------------------------------------- NDVI
def load_window(w):
    nd = load_gz(C.RAW / "modis_windows" / f"{w}_NDVI.json.gz")
    qa = load_gz(C.RAW / "modis_windows" / f"{w}_pixel_reliability.json.gz")
    assert nd["modis_date"] == qa["modis_date"], w
    a = np.array(nd["data"], float)
    q = np.array(qa["data"], float)
    good = (a > -2000) & ((q == 0) | (q == 1))
    ndvi = np.where(good, a * 1e-4, np.nan)
    dates = pd.to_datetime(nd["calendar_date"])
    return ndvi, q, dates


def build_ndvi(win):
    rec, qa_stats = [], {}
    store = {}
    for r in win.itertuples():
        ndvi, q, dates = load_window(r.window)
        store[r.window] = (ndvi, dates)
        qa_stats[r.window] = {str(int(k)): int((q == k).sum()) for k in np.unique(q)}
        doy, year = dates.dayofyear.values, dates.year.values
        peak = np.isin(doy, PEAK_DOYS)
        for y in range(C.Y0, C.Y1 + 1):
            sel = peak & (year == y)
            block = ndvi[sel]                                        # composites x pixels
            n_good = np.isfinite(block).sum(axis=0)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                mean = np.nanmean(block, axis=0)
            mean[n_good < 2] = np.nan                                # need >= 2 good composites
            for px in range(ndvi.shape[1]):
                rec.append((r.window, r.cls, px, y, mean[px], n_good[px]))
    pix = pd.DataFrame(rec, columns=["window", "window_cls", "pixel", "year", "ndvi_peak", "n_good"])
    return pix, qa_stats, store


def endmembers(pix):
    """NDVI_soil: median peak-season NDVI of desert-window pixels (all years).
    NDVI_veg : 95th percentile of peak-season NDVI of oasis-window pixels (all years)."""
    soil = pix.loc[pix.window_cls == "desert", "ndvi_peak"].dropna()
    veg = pix.loc[pix.window_cls == "oasis", "ndvi_peak"].dropna()
    return dict(ndvi_soil=round(float(soil.median()), 4), ndvi_soil_iqr=[round(float(soil.quantile(q)), 4) for q in (.25, .75)],
                ndvi_soil_sd_interannual=round(float(soil.groupby(pix.loc[soil.index, "year"]).median().std()), 4),
                ndvi_veg=round(float(veg.quantile(0.95)), 4), ndvi_veg_p90_p99=[round(float(veg.quantile(q)), 4) for q in (.90, .99)],
                method="linear mixing (Gutman & Ignatov 1998): FVC=(NDVI-soil)/(veg-soil), clipped to [0,1]")


def classify_pixels(pix):
    """Re-apply the class rules of m1_config to every pixel using ITS OWN epoch means."""
    E = pix[pix.year.isin(C.EPOCH_EARLY)].groupby(["window", "pixel"])["ndvi_peak"].mean()
    L = pix[pix.year.isin(C.EPOCH_LATE)].groupby(["window", "pixel"])["ndvi_peak"].mean()
    k = pd.DataFrame({"E": E, "L": L})
    k["cls"] = "other"
    k.loc[(k.E < 0.08) & (k.L < 0.08), "cls"] = "desert"
    k.loc[(k.E >= 0.09) & (k.E <= 0.20) & ((k.L - k.E).abs() < 0.04), "cls"] = "ecotone"
    k.loc[(k.E < 0.10) & (k.L >= 0.25), "cls"] = "converted"
    k.loc[(k.E >= 0.40) & (k.L >= 0.40), "cls"] = "oasis"
    return k.reset_index()


def establishment_year(years, fvc, thr=0.10):
    """First year whose cover is >= thr and stays >= thr on average over the next 3 years."""
    for i, y in enumerate(years):
        nxt = fvc[i:i + 4]
        if np.isfinite(fvc[i]) and fvc[i] >= thr and np.nanmean(nxt) >= thr and np.nanmin(nxt) >= 0.5 * thr:
            return int(y)
    return None


# ------------------------------------------------------------------------------- main
def main():
    C.PROC.mkdir(parents=True, exist_ok=True)
    win = pd.read_csv(C.PROC / "windows.csv")
    summary = {}

    # ---- forcing -------------------------------------------------------------------
    for site in C.FORCING_SITES:
        f = build_forcing(site)
        grid = dict(f.attrs)                                   # grid cell actually returned by the API
        pw = power_et0(site)
        f = f.merge(pw, left_on="date", right_index=True, how="left")
        f.to_csv(C.PROC / f"forcing_{site}.csv", index=False)
        yr = f.groupby(f.date.dt.year)
        ok = f[["ET0", "ET0_provider", "ET0_power"]].dropna()
        summary[site] = dict(
            grid=grid,
            P_mm_yr=round(float(yr["P"].sum().mean()), 1), P_power_mm_yr=round(float(yr["P_power"].sum().mean()), 1),
            ET0_mm_yr=round(float(yr["ET0"].sum().mean()), 0),
            ET0_provider_mm_yr=round(float(yr["ET0_provider"].sum().mean()), 0),
            ET0_power_mm_yr=round(float(yr["ET0_power"].sum().mean()), 0),
            ET0_daily_r_vs_provider=round(float(np.corrcoef(ok.ET0, ok.ET0_provider)[0, 1]), 3),
            ET0_daily_r_vs_power=round(float(np.corrcoef(ok.ET0, ok.ET0_power)[0, 1]), 3),
            T_mean=round(float(f["T"].mean()), 2), u10_mean=round(float(f["wind_speed_10m_mean"].mean()), 2),
            DP_mean_wind_VU=round(float(f["DP_mean_1.0"].mean()), 1),
            DP_gust_VU=round(float(f["DP_gust_1.0"].mean()), 1),
            hours_ge6_per_yr_mean_wind=round(float(yr["hours_ge6_mean"].sum().mean()), 0),
            hours_ge6_per_yr_gust=round(float(yr["hours_ge6_gust"].sum().mean()), 0),
            RDP_over_DP=round(float(np.hypot(f.DPx.mean(), f.DPy.mean()) / f["DP_mean_1.0"].mean()), 2),
            RDD_deg_towards=round(float(np.degrees(np.arctan2(f.DPx.mean(), f.DPy.mean())) % 360), 0),
            sm_0_7=round(float(f["soil_moisture_0_to_7cm_mean"].mean()), 4),
            sm_28_100=round(float(f["soil_moisture_28_to_100cm_mean"].mean()), 4))

    # ---- NDVI -> cover ---------------------------------------------------------------
    pix, qa_stats, store = build_ndvi(win)
    em = endmembers(pix)
    pix["fvc"] = ((pix.ndvi_peak - em["ndvi_soil"]) / (em["ndvi_veg"] - em["ndvi_soil"])).clip(0, 1)
    cls = classify_pixels(pix)
    pix = pix.merge(cls[["window", "pixel", "cls"]], on=["window", "pixel"])
    pix.round(4).to_csv(C.PROC / "pixel_annual_fvc.csv", index=False)
    (C.PROC / "endmembers.json").write_text(json.dumps(em, indent=1))

    g = pix.groupby(["cls", "year"])["fvc"]
    ca = pd.DataFrame({"n": g.count(), "median": g.median(), "q25": g.quantile(.25), "q75": g.quantile(.75),
                       "mean": g.mean()}).reset_index()
    ca.round(4).to_csv(C.PROC / "class_annual_fvc.csv", index=False)

    # 16-day class medians (seasonal cycle; used for phenology check only)
    rows = []
    for w, (ndvi, dates) in store.items():
        cw = cls[cls.window == w].set_index("pixel")["cls"]
        for k in cw.unique():
            cols = cw.index[cw == k].values
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                med = np.nanmedian(ndvi[:, cols], axis=1)
            rows += [(w, k, d, m, len(cols)) for d, m in zip(dates, med)]
    s16 = pd.DataFrame(rows, columns=["window", "cls", "date", "ndvi_median", "n_pixels"])
    s16["fvc"] = ((s16.ndvi_median - em["ndvi_soil"]) / (em["ndvi_veg"] - em["ndvi_soil"])).clip(0, 1)
    s16.round(4).to_csv(C.PROC / "window_16day_ndvi.csv", index=False)

    # ---- converted cohort: align on establishment year ----------------------------------
    coh = []
    for (w, px), s in pix[pix.cls == "converted"].groupby(["window", "pixel"]):
        s = s.sort_values("year")
        t0 = establishment_year(s.year.values, s.fvc.values)
        if t0 is None or t0 <= C.Y0 + 1:       # need >= 2 bare years before establishment
            continue
        for y, v in zip(s.year.values, s.fvc.values):
            coh.append((w, px, t0, y, y - t0, v))
    coh = pd.DataFrame(coh, columns=["window", "pixel", "t0", "year", "tau", "fvc"])
    coh.round(4).to_csv(C.PROC / "cohort_converted.csv", index=False)

    summary["endmembers"] = em
    summary["pixel_reliability_counts"] = qa_stats
    summary["pixels_per_class"] = cls.groupby("cls").size().to_dict()
    summary["pixels_per_window_class"] = {f"{a}|{b}": int(n) for (a, b), n in cls.groupby(["window", "cls"]).size().items()}
    summary["cohort"] = dict(n_pixels=int(coh.groupby(["window", "pixel"]).ngroups),
                             t0_counts={int(k): int(v) for k, v in coh.drop_duplicates(["window", "pixel"]).t0.value_counts().sort_index().items()})
    valid = pix["ndvi_peak"].notna().mean()
    summary["peak_season_valid_fraction"] = round(float(valid), 4)
    (C.PROC / "data_summary.json").write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps({k: v for k, v in summary.items() if k != "pixel_reliability_counts"}, indent=1, default=str))


if __name__ == "__main__":
    main()
