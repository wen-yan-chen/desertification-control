# -*- coding: utf-8 -*-
"""Numerical M1 entry point and pooled annual vegetation calibration.

Current contract: Docs/20261110_m1_audit_and_implementation.md.
Run python Code/v7_model1.py. Exports CSV/JSON only, no figures.
The annual vegetation equation is retained; v7_m1_water supplies dynamic storage.

2026-11-11: the wind-damage term k*E*(1 - eta*V/K)*V was removed from the cover
equation. The data do not support it (Results/v7/model1/wind_term_test.csv) and,
at average wind, it has the same shape as the growth term, so it cannot be told
apart from r. Wind now acts where it can be computed: through evaporative demand
(ET0) and through the sand-exposure output. See Code/v7_m1_wind.py.
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.optimize import least_squares


try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANEL = os.path.join(BASE, "Data", "v7", "m1_audited", "panel_m1.csv")
SEC = os.path.join(BASE, "Data", "v7", "section_modis")
RES = os.path.join(BASE, "Results", "v7", "model1")
os.makedirs(RES, exist_ok=True)

VEG = ["YT", "MF", "QM", "RQ", "KEL", "YL", "ALE"]      # vegetated (oasis-fringe) stations
BARE = ["XT", "TZ"]  # context sites; TZ is not evidence of rain-only vegetation
SECTION = ["YT", "MF"]                                  # stations on the modelled section
TRAIN_END = 2022                                        # v7 split: 2015-2022 / 2023-2025

# Local endmembers are remotely derived scaling proxies, not ground-truth cover.
ND_S7, ND_V7 = 0.05, 0.85
ND_S_LOC, ND_V_LOC = 0.0505, 0.5827
V_FULL = 100 * (ND_V_LOC - ND_S7) / (ND_V7 - ND_S7)

# ----------------------------------------------------------------------------- model
def f_temp(t):
    """v7 Eq. fT: trapezoid, 0 below 5 C, 1 above 25 C."""
    return np.clip((np.asarray(t, float) - 5.0) / 20.0, 0.0, 1.0)


def step(v, K, W, r, d):
    """One year of the cover equation: logistic growth scaled by water, minus decay.
    v, K in the same unit; W dimensionless in [0, 1].  No wind term (see module note):
    r and d are fitted on stations under real wind, so average wind loss is inside them.
    f(T) is absorbed into the fitted annual rate (a scale convention, not proof
    that temperature has no interannual variation)."""
    x = v / K
    return np.maximum(v + r * v * (1 - x) * W - d * v, 0.0)


def r2(obs, sim):
    obs, sim = np.asarray(obs, float), np.asarray(sim, float)
    denom = np.sum((obs - obs.mean()) ** 2)
    return float(1 - np.sum((obs - sim) ** 2) / denom) if denom > 0 else None


def rmse(obs, sim):
    return float(np.sqrt(np.mean((np.asarray(obs, float) - np.asarray(sim, float)) ** 2)))


# ----------------------------------------------------------------------------- data
def yearly_table():
    d = pd.read_csv(PANEL, encoding="utf-8-sig", parse_dates=["date"])
    expected = pd.MultiIndex.from_product([sorted(VEG+BARE), pd.date_range('2015-01-01','2025-12-01',freq='MS')])
    actual = pd.MultiIndex.from_frame(d[['site','date']])
    if actual.has_duplicates or set(actual) != set(expected):
        raise ValueError('M1 panel must contain exactly one row per site-month, 2015-2025')
    weather = d[['E','T2M','P_mm','GWETROOT','W','era_T','era_et0_mm','era_P_mm']]
    if not np.isfinite(weather.to_numpy()).all() or (d[['E','P_mm','era_et0_mm','era_P_mm']] < 0).any().any():
        raise ValueError('Missing/nonphysical forcing must be resolved before M1')
    d["year"], d["m"] = d.date.dt.year, d.date.dt.month
    d["V_pct"] = 100 * ((d["ndvi_mvc_qa"] - ND_S7) / (ND_V7 - ND_S7)).clip(0, 1)
    d["obs"] = d["ndvi_mvc_qa"].notna()  # missing remains missing, never imputed
    rows = []
    for (s, y), x in d.groupby(["site", "year"]):
        gs = x[x.m.between(6, 9) & x.obs]
        rows.append(dict(site=s, year=y, V=gs.V_pct.mean() if len(gs) >= 2 else np.nan, n_obs=len(gs),
                         E_raw=float(np.average(x.E, weights=x.date.dt.days_in_month)), T=x.T2M.mean(), P=x.P_mm.sum(), GWET=x.GWETROOT.mean(),
                         W_v7=x.W.mean(), ET0=x.era_et0_mm.sum(),
                         ET0g=float((f_temp(x.era_T) * x.era_et0_mm).sum())))
    a = pd.DataFrame(rows).sort_values(["site", "year"]).reset_index(drop=True)
    tr = a[a.year <= TRAIN_END]
    a["K"] = a.site.map(1.15 * tr.groupby("site").V.quantile(0.95))          # v7 Eq. K, unchanged
    a["E"] = a.E_raw / a.site.map(tr.groupby("site").E_raw.mean())           # station-normalised
    # Output only (cover -> sand): wind index times the unsheltered share of the surface.
    # E is NOT an input of the cover equation.
    a["sand_exposure"] = a.E * (1 - (a.V / a.K).clip(0, 1))
    a["V_next"] = a.groupby("site").V.shift(-1)
    a["n_obs_next"] = a.groupby("site").n_obs.shift(-1)
    a["target_year"] = a.year + 1
    return d, a


def cohort_table():
    """Converted pixels of the Yutian-Minfeng margin, re-expressed in v7 cover units."""
    c = pd.read_csv(os.path.join(SEC, "cohort_converted.csv"))
    ndvi = ND_S_LOC + c.fvc * (ND_V_LOC - ND_S_LOC)
    c["V"] = 100 * np.clip((ndvi - ND_S7) / (ND_V7 - ND_S7), 0, 1)
    c = c[c.tau >= 0]
    g = c.groupby(["window", "t0", "tau"]).V
    t = pd.DataFrame({"V": g.median(), "n": g.count()}).reset_index()
    return t[t.n >= 3]


# ----------------------------------------------------------------------------- B. station fit
def fit_stations(a):
    # Eligibility follows TRAINING growing-season missingness, never held-out scores.
    eligible = a[(a.year <= TRAIN_END) & a.site.isin(VEG)].groupby("site").n_obs.sum()
    eligible = eligible[eligible >= 0.8 * 8 * 4].index
    t = a[a.site.isin(eligible)].dropna(subset=["V", "V_next"])
    tr, te = t[t.year < TRAIN_END], t[t.year >= TRAIN_END]       # target year <= 2022 / >= 2023
    x, x1 = lambda q: (q.V / q.K).values, lambda q: (q.V_next / q.K).values
    pred = lambda th, q: step(x(q), 1.0, 1.0, th[0], th[1])                     # W = 1: irrigated oases
    fit = least_squares(lambda th: pred(th, tr) - x1(tr), [0.5, 0.1], bounds=([0, 0], [3, 1]))
    J = fit.jac
    cov = np.linalg.pinv(J.T @ J) * 2 * fit.cost / (len(tr) - 2)
    sse = 2 * fit.cost
    best = fit.x
    res = {"pooled_r_d": dict(theta=[round(float(v), 4) for v in fit.x],
                              sd=[round(float(v), 4) for v in np.sqrt(np.diag(cov))],
                              cond=float(np.linalg.cond(J.T @ J)),
                              aic=round(float(len(tr) * np.log(sse / len(tr)) + 4), 2),
                              rmse_train=round(rmse(x1(tr), pred(fit.x, tr)), 4),
                              rmse_test=round(rmse(x1(te), pred(fit.x, te)), 4),
                              r2_test=round(r2(x1(te), pred(fit.x, te)), 3))}
    res["baselines"] = dict(
        persistence_rmse_train=round(rmse(x1(tr), x(tr)), 4), persistence_rmse_test=round(rmse(x1(te), x(te)), 4),
        site_mean_rmse_test=round(rmse(x1(te), te.site.map((a[a.year <= TRAIN_END].V / a[a.year <= TRAIN_END].K).groupby(a[a.year <= TRAIN_END].site).mean()).values), 4),
        n_train=int(len(tr)), n_test=int(len(te)), eligible_sites=sorted(t.site.unique()))
    # leave-one-station-out
    loso = {}
    for s in sorted(t.site.unique()):
        q, o = tr[tr.site != s], t[t.site == s]
        f = least_squares(lambda th: step(x(q), 1.0, 1.0, th[0], th[1]) - x1(q), [0.5, 0.1], bounds=([0, 0], [3, 1]))
        loso[s] = dict(r=round(float(f.x[0]), 3), d=round(float(f.x[1]), 3),
                       rmse=round(rmse(x1(o), step(x(o), 1.0, 1.0, *f.x)), 4),
                       persistence=round(rmse(x1(o), x(o)), 4))
    res["leave_one_station_out"] = loso
    return res, best, (tr, te)


# ----------------------------------------------------------------------------- C. cohort transfer
def cohort_check(coh, r, d):
    """Retrospective diagnostic on selected greening pixels, not forecast validation.
    Fit K and initial cover on CON1-3 and score CON4 spatially."""
    cal, val = coh[coh.window != "CON4"], coh[coh.window == "CON4"]

    def traj(K, v0, taus, rr=r, dd=d):
        values, v = [], float(v0)
        for _ in range(int(taus.max()) + 1):
            values.append(v)
            v = float(step(v, K, 1., rr, dd))
        V = np.asarray(values)
        return V[taus.values]

    w = lambda q: np.sqrt(q.n.values)
    f1 = least_squares(lambda th: w(cal) * (traj(th[0], th[1], cal.tau) - cal.V.values), [40, 8],
                       bounds=([10, 1], [100, 30]))
    def free_traj(th, taus):
        rate, plateau, v0 = th
        v, values = v0, []
        for _ in range(int(taus.max()) + 1):
            values.append(v)
            v = v + rate * v * (1 - v / plateau)
        return np.asarray(values)[taus.values]
    f2 = least_squares(lambda th: w(cal) * (free_traj(th, cal.tau) - cal.V.values),
                       [0.5, 36, 8], bounds=([0.001, 10, 1], [1, 100, 30]))
    out = dict(status="retrospective selected-cohort diagnostic, NOT independent forecast validation",
               selection="late-period greening and future years used to select pixels and align t0",
               parameter_warning="free r,d,K structurally non-identifiable; only r-d and r/K identifiable",
               K_cohort=float(f1.x[0]), v0=float(f1.x[1]),
               plateau=float(f1.x[0]*(1-d/r)),
               free_fit=dict(net_rate=float(f2.x[0]), plateau=float(f2.x[1]), v0=float(f2.x[2])))
    for name, q in (("calibration_CON1_3", cal), ("spatial_diagnostic_CON4", val)):
        out[name] = dict(n=int(len(q)),
            transfer_r2=r2(q.V, traj(*f1.x, q.tau)), transfer_rmse=rmse(q.V, traj(*f1.x, q.tau)),
            free_r2=r2(q.V, free_traj(f2.x, q.tau)),
            mean_baseline_r2=r2(q.V, np.full(len(q), cal.V.mean())))
    return out, f1.x, traj


# ----------------------------------------------------------------------------- D. water closure
# ----------------------------------------------------------------------------- entry
if __name__ == "__main__":
    from v7_m1_run import main
    main()
