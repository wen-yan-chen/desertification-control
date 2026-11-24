"""Wind in Model 1 (added 2026-11-11). Tables only, no figures.

The cover equation V[t+1] = V + r V (1 - V/K) W - d V has NO wind term. This module
holds the evidence for that choice and the two places where wind does act.

1. wind_term_test()   Record of the test that removed the old term k*E*(1 - eta*V/K)*V.
                      Nine wind indicators, with and without the shelter factor, are
                      added one at a time to the pooled (r, d) fit.  None is supported.
2. Channel A  wind -> evaporative demand -> water satisfaction W -> cover.
              Wind speed u2 is an input of FAO-56 Penman-Monteith ET0 (Eq. 6).  ET0 sets
              the daily demand D_j of the water bucket, so a windier climate lowers W
              and, through W, the cover.  wind_demand_factors() gives the monthly factor
              by which ET0 changes when wind speed is scaled.
3. Channel B  cover -> sand.  The exposure index S = E * (1 - V/K) is an OUTPUT
              (v7_model1.yearly_table, v7_m1_water.trajectory); E never enters the
              cover equation.

Why not keep k as a scenario?  At average wind (E = 1) and full shelter (eta = 1) the
old term is k*(1 - V/K)*V, the same shape as growth r*V*(1 - V/K) at W = 1: only r - k
can be estimated.  r and d are fitted on stations standing in real wind, so the average
wind loss is already inside them.
"""
import os

import numpy as np
import pandas as pd
from scipy import stats

import v7_model1 as model

LEGACY = os.path.join(model.BASE, "Data", "v7", "processed", "panel_monthly_clean.csv")
LAT = {"YT": 36.85, "MF": 37.06, "QM": 38.13, "RQ": 39.02, "KEL": 41.76, "YL": 41.34,
       "ALE": 40.55, "XT": 38.83, "TZ": 38.97}                     # Data/v7/README.md


def _monthly():
    """v7 monthly weather (POWER) joined with the audited M1 panel. Read-only."""
    old = pd.read_csv(LEGACY, encoding="utf-8-sig", parse_dates=["date"])
    new = pd.read_csv(model.PANEL, encoding="utf-8-sig", parse_dates=["date"])
    keep = ["site", "date", "E", "Tmax_daily_mean", "Tmin_daily_mean", "era_T", "era_et0_mm"]
    d = old.drop(columns=["E", "era_T", "era_et0_mm"], errors="ignore").merge(
        new[keep], on=["site", "date"], validate="one_to_one")
    d["year"], d["m"] = d.date.dt.year, d.date.dt.month
    return d


# ----------------------------------------------------------------------------- 1. the test
def wind_term_test(annual, eligible, train_end=model.TRAIN_END, repetitions=400):
    """Add k*Z*g(V)*V to the pooled fit for each wind indicator Z and report whether it helps.

    form 'shelter'    g = 1 - V/K   (old model, eta = 1)
    form 'no shelter' g = 1         (eta = 0)
    Z is divided by the station's training-period mean (or the pooled mean when a station
    mean is zero), so Z = 1 is average wind and k has the same meaning for every indicator.
    Reported: k with its least-squares s.e., F-test p-value against the (r, d) model,
    AIC change (positive = worse), station-cluster bootstrap 95 % interval, hold-out RMSE.
    """
    d = _monthly()

    def ann(col, months=None, how="mean"):
        q = d if months is None else d[d.m.between(*months)]
        return q.groupby(["site", "year"])[col].agg(how)

    indicators = {
        "E index, year (the one the old term used)": ann("E"),
        "E index, Mar-Jun (wind season)": ann("E", (3, 6)),
        "E index, Jun-Sep (growing season)": ann("E", (6, 9)),
        "daily-max wind, year mean": ann("WS10M_MAX"),
        "mean wind speed, year": ann("WS10M"),
        "ERA gust, year mean": ann("era_gust"),
        "days with max wind >= 8 m/s": ann("dust_days_8", how="sum"),
        "days with max wind >= 10 m/s": ann("dust_days_10", how="sum"),
        "days with max wind >= 12 m/s": ann("dust_days_12", how="sum"),
    }
    t = annual[annual.site.isin(eligible)].dropna(subset=["V", "V_next"]).copy()
    t["x"], t["x1"] = t.V / t.K, t.V_next / t.K

    def fit(q, z, shelter):
        g = (1 - q.x) if shelter else 1.0
        X = np.column_stack([q.x * (1 - q.x), -q.x, -z * g * q.x])
        y = (q.x1 - q.x).to_numpy()
        b = np.linalg.lstsq(X, y, rcond=None)[0]
        e = y - X @ b
        se = np.sqrt(np.diag(e @ e / (len(y) - 3) * np.linalg.pinv(X.T @ X)))
        return b, se, float(e @ e)

    tr = t[t.year < train_end]
    X0 = np.column_stack([tr.x * (1 - tr.x), -tr.x])
    y0 = (tr.x1 - tr.x).to_numpy()
    b0 = np.linalg.lstsq(X0, y0, rcond=None)[0]
    e0 = y0 - X0 @ b0
    sse0, n = float(e0 @ e0), len(tr)
    te0 = t[t.year >= train_end]
    rmse0 = model.rmse(te0.x1, te0.x + b0[0] * te0.x * (1 - te0.x) - b0[1] * te0.x)
    rows = []
    for name, series in indicators.items():
        z = series.rename("z").reset_index()
        z = z[z.site.isin(eligible)]
        base = z[z.year <= train_end].groupby("site").z.mean()
        z["zn"] = z.z / (z.site.map(base) if (base > 0).all() else z[z.year <= train_end].z.mean())
        q = t.merge(z[["site", "year", "zn"]], on=["site", "year"], validate="one_to_one")
        qtr, qte = q[q.year < train_end], q[q.year >= train_end]
        zz = z[z.year <= train_end]
        cv = float((zz.groupby("site").zn.std() / zz.groupby("site").zn.mean()).mean())
        for shelter in (True, False):
            b, se, sse = fit(qtr, qtr.zn.to_numpy(), shelter)
            F = max((sse0 - sse) / (sse / (n - 3)), 0.0)
            g = (1 - qte.x) if shelter else 1.0
            pred = qte.x + b[0] * qte.x * (1 - qte.x) - b[1] * qte.x - b[2] * qte.zn * g * qte.x
            rng, ks = np.random.default_rng(20261111), []
            for _ in range(repetitions):
                pick = rng.choice(list(eligible), len(eligible), replace=True)
                qq = pd.concat([qtr[qtr.site == s] for s in pick])
                ks.append(fit(qq, qq.zn.to_numpy(), shelter)[0][2])
            lo, hi = np.percentile(ks, [2.5, 97.5])
            rows.append(dict(indicator=name, form="shelter" if shelter else "no shelter",
                             year_to_year_cv=cv, k=b[2], k_se=se[2],
                             p_value=float(1 - stats.f.cdf(F, 1, n - 3)),
                             aic_change=n * np.log(sse / n) + 6 - (n * np.log(sse0 / n) + 4),
                             k_boot_2p5=lo, k_boot_97p5=hi,
                             rmse_holdout=model.rmse(qte.x1, pred), rmse_holdout_no_wind=rmse0,
                             n_train=n, n_holdout=len(qte)))
    out = pd.DataFrame(rows)
    # within-station association between this year's wind index and next year's cover change
    q = t.assign(dx=t.x1 - t.x)
    q["Ec"] = q.E - q.groupby("site").E.transform("mean")
    q["dxc"] = q.dx - q.groupby("site").dx.transform("mean")
    r, p = stats.pearsonr(q.Ec, q.dxc)
    used = out.iloc[0]
    summary = dict(
        decision="wind term removed from the cover equation",
        tests=int(len(out)), tests_with_p_below_0p05=int((out.p_value < 0.05).sum()),
        tests_that_lower_holdout_rmse=int((out.rmse_holdout < out.rmse_holdout_no_wind).sum()),
        old_term=dict(k=float(used.k), k_se=float(used.k_se), p_value=float(used.p_value),
                      aic_change=float(used.aic_change), k_boot_95=[float(used.k_boot_2p5), float(used.k_boot_97p5)],
                      rmse_holdout=float(used.rmse_holdout), rmse_holdout_no_wind=float(rmse0)),
        within_station_corr_wind_index_vs_next_year_cover_change=dict(r=float(r), p=float(p), n=int(len(q))),
        wind_index_year_to_year_cv=float(used.year_to_year_cv),
        note="not detectable in these data is not the same as no effect; see limitations")
    return out, summary


# ----------------------------------------------------------------------------- 2. channel A
def penman_monteith_mm(q, wind_scale=1.0):
    """FAO-56 Penman-Monteith reference ET (Eq. 6), mm per month, from monthly means.

    Inputs (POWER): mean daily Tmax/Tmin [deg C], RH2M [%], WS2M [m/s at 2 m], PS [kPa],
    ALLSKY_SFC_SW_DWN [MJ m-2 day-1].  Returns (total, aerodynamic part); the aerodynamic
    part is the wind-driven term.  wind_scale multiplies the 2 m wind speed.
    """
    tmax, tmin = q.Tmax_daily_mean.to_numpy(), q.Tmin_daily_mean.to_numpy()
    tmean = (tmax + tmin) / 2
    e0 = lambda t: 0.6108 * np.exp(17.27 * t / (t + 237.3))                    # Eq. 11
    es = (e0(tmax) + e0(tmin)) / 2                                             # Eq. 12
    ea = es * q.RH2M.to_numpy() / 100                                          # Eq. 19
    delta = 4098 * e0(tmean) / (tmean + 237.3) ** 2                            # Eq. 13
    gamma = 0.000665 * q.PS.to_numpy()                                         # Eq. 8
    u2, rs = q.WS2M.to_numpy() * wind_scale, q.ALLSKY_SFC_SW_DWN.to_numpy()
    elev = (1 - (q.PS.to_numpy() / 101.3) ** (1 / 5.26)) * 293 / 0.0065        # Eq. 7 inverted
    doy = (q.date + pd.offsets.Day(14)).dt.dayofyear.to_numpy()
    lat = np.radians(q.site.map(LAT).to_numpy())
    dr = 1 + 0.033 * np.cos(2 * np.pi * doy / 365)                             # Eq. 23
    dec = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)                         # Eq. 24
    ws = np.arccos(-np.tan(lat) * np.tan(dec))                                 # Eq. 25
    ra = 24 * 60 / np.pi * 0.0820 * dr * (ws * np.sin(lat) * np.sin(dec)
                                         + np.cos(lat) * np.cos(dec) * np.sin(ws))   # Eq. 21
    rnl = 4.903e-9 * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2 \
        * (0.34 - 0.14 * np.sqrt(ea)) * (1.35 * np.minimum(rs / ((0.75 + 2e-5 * elev) * ra), 1) - 0.35)
    rn = 0.77 * rs - rnl                                                       # Eq. 38-40
    denom = delta + gamma * (1 + 0.34 * u2)
    radiation = 0.408 * delta * rn / denom
    aerodynamic = gamma * 900 / (tmean + 273) * u2 * (es - ea) / denom
    days = q.days_in_month.to_numpy()
    return np.maximum(radiation + aerodynamic, 0) * days, aerodynamic * days


def wind_demand_factors(scales=(0.8, 0.9, 1.0, 1.1, 1.2), train_end=model.TRAIN_END):
    """Monthly factor on the model's ET0 forcing when wind speed is scaled.

    Uses the same months as the forcing climatology (section stations, training years).
    The model keeps the provider ET0 as forcing; Penman-Monteith is used only for the
    RATIO ET0(scaled wind) / ET0(observed wind), month by month.
    Returns (factors: DataFrame month x scale, check: dict).
    """
    d = _monthly()
    sec = d[d.site.isin(model.SECTION) & (d.year <= train_end)].copy()
    base, aero = penman_monteith_mm(sec)
    sec["pm"], sec["aero"] = base, aero
    w = model.f_temp(sec.era_T)                       # same growing-season weight as the forcing
    table = {}
    for s in scales:
        sec["scaled"] = penman_monteith_mm(sec, s)[0]
        g = sec.groupby("m")
        table[s] = g.scaled.mean() / g.pm.mean()
    years = sec.year.nunique() * sec.site.nunique()
    check = dict(
        penman_monteith_vs_provider_monthly_r=float(np.corrcoef(sec.pm, sec.era_et0_mm)[0, 1]),
        penman_monteith_mm_yr=float(sec.pm.sum() / years), provider_et0_mm_yr=float(sec.era_et0_mm.sum() / years),
        wind_driven_share_of_et0=float(sec.aero.sum() / sec.pm.sum()),
        et0_change_per_scale={str(s): float(penman_monteith_mm(sec, s)[0].sum() / sec.pm.sum() - 1) for s in scales},
        et0g_change_per_scale={str(s): float((w * penman_monteith_mm(sec, s)[0]).sum() / (w * sec.pm).sum() - 1)
                               for s in scales},
        mean_wind_2m_ms=float(sec.WS2M.mean()))
    return pd.DataFrame(table).rename_axis("month").reset_index(), check
