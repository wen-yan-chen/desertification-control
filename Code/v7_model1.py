# -*- coding: utf-8 -*-
"""
v7_model1.py -- Task 1 rebuilt on the v7 data (2026-11-10).  Offline, ~10 s.

    python Code/v7_model1.py

The backbone is the v7 state equation (Reports/model_v7.tex, Eq. t1), unchanged:

    V[t+1] = V[t] + r V (1 - V/K) W f(T)  -  d V  -  k E (1 - eta V/K) V        (yearly)

What this script changes, and why (each change is backed by a number it prints):

  C1  POOLED calibration.  v7 fits (r, d, k, eta) per station on 8 yearly points:
      89 % of fits end on a bound and the median training R2 is 0.004
      (Results/v7/tab_ablation_summary.csv).  Here one parameter set is shared by
      all vegetated stations; only K is local.  49 training transitions instead of 7.
  C2  NESTED models, keep the smallest one the data support.
      M0: r, d      M1: r, d, k (eta = 1)      M2: r, d, k, eta
  C3  W is no longer the reanalysis index.  GWETROOT has no year-to-year signal at any
      station (it is a site constant) and it has no irrigation, so it cannot be W[t].
      W is closed by a yearly water budget instead:
          W = min(1, A / (c * min(1, 2 fc) * ET0g)),   A = eta_w * I + G
      i.e. usable water / water the canopy would transpire unstressed (FAO-56 Eq. 98
      form).  This is what couples V and effective soil moisture, and it gives Task 2
      the V*(I) curve that v7 replaced by the invented Ks = 0.45 + 0.55 I/60.
  C4  Imputed NDVI months are not scored: yearly V uses observed Jun-Sep months only.
  C5  A second, independent data set checks the station parameters: 217 MODIS pixels
      on the Yutian-Minfeng margin that went from bare sand to vegetation (2003-2021).
      Station (r, d) are transferred to them WITHOUT refitting.

Nothing here prescribes a target fit.  Hold-out scores are printed next to naive
baselines and negative skill is reported as it is.
"""
import json
import os
import sys

import matplotlib
import numpy as np
import pandas as pd
from scipy.optimize import least_squares

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANEL = os.path.join(BASE, "Data", "v7", "processed", "panel_monthly_clean.csv")
SEC = os.path.join(BASE, "Data", "v7", "section_modis")
RES = os.path.join(BASE, "Results", "v7", "model1")
FIG = os.path.join(BASE, "Figures", "v7")
os.makedirs(RES, exist_ok=True)

VEG = ["YT", "MF", "QM", "RQ", "KEL", "YL", "ALE"]      # vegetated (oasis-fringe) stations
BARE = ["XT", "TZ"]                                     # desert stations: rain only
SECTION = ["YT", "MF"]                                  # stations on the modelled section
TRAIN_END = 2022                                        # v7 split: 2015-2022 / 2023-2025

# NDVI end-members.  v7 uses fixed 0.05 / 0.85.  On this section the densest oasis
# pixels reach NDVI 0.583 (Data/v7/section_modis/endmembers.json), so a closed canopy
# reads only V_FULL = 66.6 % in v7 units.  V in v7 units is fine for the dynamics (only
# V/K matters) but must be rescaled before it is used as a ground-cover FRACTION.
ND_S7, ND_V7 = 0.05, 0.85
ND_S_LOC, ND_V_LOC = 0.0505, 0.5827
V_FULL = 100 * (ND_V_LOC - ND_S7) / (ND_V7 - ND_S7)

# Water-budget constants (C3).  Sources: FAO-56 ch. 9 (c), Table 20 / drip practice
# (eta_w); both are assumptions with ranges and are varied in the sensitivity table.
C_KCB = 1.0        # transpiration coefficient of a closed canopy   [0.7, 1.2]
ETA_W = 0.75       # share of gross irrigation that is transpirable  [0.65, 0.85]
#                    (0.9 application efficiency x ~0.85 left after wet-soil evaporation)

PAL = dict(blue="#2a78d6", orange="#eb6834", aqua="#1baf7a", yellow="#eda100", violet="#6250d6", ink="#52514e")
plt.rcParams.update({"figure.dpi": 130, "savefig.dpi": 200, "axes.grid": True, "grid.alpha": 0.25,
                     "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})


# ----------------------------------------------------------------------------- model
def f_temp(t):
    """v7 Eq. fT: trapezoid, 0 below 5 C, 1 above 25 C."""
    return np.clip((np.asarray(t, float) - 5.0) / 20.0, 0.0, 1.0)


def step(v, K, W, E, r, d, k=0.0, eta=1.0):
    """One year of the v7 state equation.  v, K in the same unit; W, E dimensionless.
    f(T) is absorbed in r: the yearly mean temperature differs by < 1.5 C between
    years at a station, so f is a site constant and cannot be separated from r."""
    x = v / K
    return np.maximum(v + r * v * (1 - x) * W - d * v - k * E * (1 - eta * x) * v, 0.0)


def water_factor(v, supply_mm, et0g_mm, c=C_KCB):
    """C3: yearly effective-moisture factor.  v in v7 percent; supply = transpirable water."""
    fc = np.clip(v / V_FULL, 0.0, 1.0)                        # ground-cover fraction
    demand = c * np.minimum(1.0, 2.0 * fc) * et0g_mm          # unstressed transpiration, mm/yr
    return np.where(demand > 1e-9, np.minimum(1.0, supply_mm / np.maximum(demand, 1e-9)),
                    np.where(supply_mm > 0, 1.0, 0.0))


def run(v0, years, K, r, d, k, eta, E=1.0, irrigation=0.0, G=0.0, et0g=1000.0, c=C_KCB, eta_w=ETA_W):
    """Coupled yearly run: V and W together.  Returns arrays V[t], W[t]."""
    v, V, Wt = float(v0), [], []
    irr = np.broadcast_to(irrigation, (years,))
    for t in range(years):
        w = float(water_factor(v, eta_w * irr[t] + G, et0g, c))
        V.append(v)
        Wt.append(w)
        v = float(step(v, K, w, E, r, d, k, eta))
    return np.array(V), np.array(Wt)


def steady(K, r, d, k, eta, irrigation, G, et0g, v0, **kw):
    V, W = run(v0, 200, K, r, d, k, eta, irrigation=irrigation, G=G, et0g=et0g, **kw)
    return float(V[-1]), float(W[-1])


def r2(obs, sim):
    obs, sim = np.asarray(obs, float), np.asarray(sim, float)
    return float(1 - np.sum((obs - sim) ** 2) / np.sum((obs - obs.mean()) ** 2))


def rmse(obs, sim):
    return float(np.sqrt(np.mean((np.asarray(obs, float) - np.asarray(sim, float)) ** 2)))


# ----------------------------------------------------------------------------- data
def yearly_table():
    d = pd.read_csv(PANEL, encoding="utf-8-sig", parse_dates=["date"])
    d["year"], d["m"] = d.date.dt.year, d.date.dt.month
    d["obs"] = d["ndvi_mvc_qa"].notna()                        # False = V was imputed (C4)
    rows = []
    for (s, y), x in d.groupby(["site", "year"]):
        gs = x[x.m.between(6, 9) & x.obs]
        rows.append(dict(site=s, year=y, V=gs.V_pct.mean() if len(gs) >= 2 else np.nan, n_obs=len(gs),
                         E_raw=x.E.mean(), T=x.T2M.mean(), P=x.P_mm.sum(), GWET=x.GWETROOT.mean(),
                         W_v7=x.W.mean(), ET0=x.era_et0_mm.sum(),
                         ET0g=float((f_temp(x.T2M) * x.era_et0_mm).sum())))
    a = pd.DataFrame(rows).sort_values(["site", "year"]).reset_index(drop=True)
    tr = a[a.year <= TRAIN_END]
    a["K"] = a.site.map(1.15 * tr.groupby("site").V.quantile(0.95))          # v7 Eq. K, unchanged
    a["E"] = a.E_raw / a.site.map(tr.groupby("site").E_raw.mean())           # station-normalised
    a["V_next"] = a.groupby("site").V.shift(-1)
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


# ----------------------------------------------------------------------------- A. checks
def check_v7_inputs(d, a):
    """Numbers behind C1, C3, C4."""
    out = {}
    w = a.groupby("site")
    out["W_v7_interannual_sd"] = w.W_v7.std().round(4).to_dict()
    out["W_v7_site_mean"] = w.W_v7.mean().round(3).to_dict()
    out["V_interannual_sd_pct"] = w.V.std().round(2).to_dict()
    # share of W variance that is "which site" rather than "which year"
    tot = a.W_v7.var()
    out["W_v7_between_site_variance_share"] = round(float(a.groupby("site").W_v7.transform("mean").var() / tot), 4)
    veg = a[a.site.isin(VEG)].dropna(subset=["V_next"])
    dv = veg.V_next - veg.V
    out["corr_dV_with_W_v7_pooled"] = round(float(np.corrcoef(dv, veg.W_v7 - veg.site.map(veg.groupby("site").W_v7.mean()))[0, 1]), 3)
    out["corr_dV_with_E_pooled"] = round(float(np.corrcoef(dv, veg.E)[0, 1]), 3)
    out["corr_siteV_with_siteW_veg_sites"] = round(float(np.corrcoef(
        a[a.site.isin(VEG)].groupby("site").V.mean(), a[a.site.isin(VEG)].groupby("site").W_v7.mean())[0, 1]), 3)
    out["f_T_range_within_site"] = round(float((a.groupby("site")["T"].max() - a.groupby("site")["T"].min()).max()), 2)
    out["imputed_month_share"] = (1 - d.groupby("site").obs.mean()).round(3).to_dict()
    abl = pd.read_csv(os.path.join(BASE, "Results", "v7", "tab_ablation_summary.csv"), encoding="utf-8-sig")
    p4 = abl[abl.pipeline == "P4"].iloc[0]
    out["v7_per_station_fit"] = dict(R2_train_median=round(float(p4.R2_train_median), 3),
                                     hit_bound_frac=round(float(p4.hit_bound_frac), 3),
                                     d_median=float(p4.d_median), k_median=round(float(p4.k_median), 3))
    return out


# ----------------------------------------------------------------------------- B. station fit
def fit_stations(a):
    t = a[a.site.isin(VEG)].dropna(subset=["V", "V_next"])
    tr, te = t[t.year < TRAIN_END], t[t.year >= TRAIN_END]       # target year <= 2022 / >= 2023
    x, x1 = lambda q: (q.V / q.K).values, lambda q: (q.V_next / q.K).values
    specs = {"M0 (r,d)": (2, lambda th: (th[0], th[1], 0.0, 1.0)),
             "M1 (r,d,k | eta=1)": (3, lambda th: (th[0], th[1], th[2], 1.0)),
             "M2 (r,d,k,eta)": (4, lambda th: (th[0], th[1], th[2], th[3]))}
    res, best = {}, None
    for name, (n, unpack) in specs.items():
        pred = lambda th, q: step(x(q), 1.0, 1.0, q.E.values, *unpack(th))     # W = 1: irrigated oases
        fit = least_squares(lambda th: pred(th, tr) - x1(tr), [0.5, 0.1, 0.05, 0.5][:n],
                            bounds=([0] * n, [3, 1, 1, 1][:n]))
        J = fit.jac
        dof = len(tr) - n
        cov = np.linalg.pinv(J.T @ J) * 2 * fit.cost / dof
        sse = 2 * fit.cost
        res[name] = dict(theta=[round(float(v), 4) for v in fit.x],
                         sd=[round(float(v), 4) for v in np.sqrt(np.diag(cov))],
                         cond=float(np.linalg.cond(J.T @ J)),
                         aic=round(float(len(tr) * np.log(sse / len(tr)) + 2 * n), 2),
                         rmse_train=round(rmse(x1(tr), pred(fit.x, tr)), 4),
                         rmse_test=round(rmse(x1(te), pred(fit.x, te)), 4),
                         r2_test=round(r2(x1(te), pred(fit.x, te)), 3))
        if name.startswith("M0"):
            best = fit.x
    res["baselines"] = dict(
        persistence_rmse_train=round(rmse(x1(tr), x(tr)), 4), persistence_rmse_test=round(rmse(x1(te), x(te)), 4),
        site_mean_rmse_test=round(rmse(x1(te), te.site.map((tr.V / tr.K).groupby(tr.site).mean()).values), 4),
        n_train=int(len(tr)), n_test=int(len(te)))
    # leave-one-station-out for the adopted model M0
    loso = {}
    for s in VEG:
        q, o = tr[tr.site != s], t[t.site == s]
        f = least_squares(lambda th: step(x(q), 1.0, 1.0, 1.0, th[0], th[1]) - x1(q), [0.5, 0.1], bounds=([0, 0], [3, 1]))
        loso[s] = dict(r=round(float(f.x[0]), 3), d=round(float(f.x[1]), 3),
                       rmse=round(rmse(x1(o), step(x(o), 1.0, 1.0, 1.0, *f.x)), 4),
                       persistence=round(rmse(x1(o), x(o)), 4))
    res["leave_one_station_out_M0"] = loso
    return res, best, (tr, te)


# ----------------------------------------------------------------------------- C. cohort transfer
def cohort_check(coh, r, d):
    """Station (r, d) are FIXED.  Only the local ceiling K and the starting cover are fitted,
    on windows CON1-3; CON4 is never used.  Compared with a free logistic fit."""
    cal, val = coh[coh.window != "CON4"], coh[coh.window == "CON4"]

    def traj(K, v0, taus, rr=r, dd=d):
        V, _ = run(v0, int(taus.max()) + 1, K, rr, dd, 0.0, 1.0, irrigation=1e6)    # water not limiting
        return V[taus.values]

    w = lambda q: np.sqrt(q.n.values)
    f1 = least_squares(lambda th: w(cal) * (traj(th[0], th[1], cal.tau) - cal.V.values), [40, 8],
                       bounds=([10, 1], [100, 30]))
    f2 = least_squares(lambda th: w(cal) * (traj(th[0], th[1], cal.tau, th[2], th[3]) - cal.V.values),
                       [40, 8, 0.6, 0.1], bounds=([10, 1, 0.05, 0], [100, 30, 3, 1]))
    out = dict(K_cohort=round(float(f1.x[0]), 2), v0=round(float(f1.x[1]), 2),
               plateau=round(float(f1.x[0] * (1 - d / r)), 2),
               free_fit=dict(K=round(float(f2.x[0]), 2), v0=round(float(f2.x[1]), 2), r=round(float(f2.x[2]), 3),
                             d=round(float(f2.x[3]), 3), net_rate=round(float(f2.x[2] - f2.x[3]), 3),
                             plateau=round(float(f2.x[0] * (1 - f2.x[3] / f2.x[2])), 2)))
    for name, q in (("calibration_CON1_3", cal), ("holdout_CON4", val)):
        out[name] = dict(n=int(len(q)),
                         transfer_r2=round(r2(q.V, traj(*f1.x, q.tau)), 3), transfer_rmse=round(rmse(q.V, traj(*f1.x, q.tau)), 2),
                         free_r2=round(r2(q.V, traj(f2.x[0], f2.x[1], q.tau, f2.x[2], f2.x[3])), 3),
                         mean_baseline_r2=round(r2(q.V, np.full(len(q), cal.V.mean())), 3))
    return out, f1.x, traj


# ----------------------------------------------------------------------------- D. water closure
def water_analysis(a, r, d, k, eta, K):
    sec = a[a.site.isin(SECTION)]
    et0g, P = float(sec.ET0g.mean()), float(sec.P.mean())
    quotas = np.array([0, 50, 100, 150, 200, 300, 400, 500, 600, 800, 1000])
    rows = []
    for q in quotas:
        lo, wlo = steady(K, r, d, k, eta, q, 0.0, et0g, 2.0)
        hi, whi = steady(K, r, d, k, eta, q, 0.0, et0g, 0.9 * K)
        rows.append(dict(irrigation_mm_yr=int(q), irrigation_m3_ha_yr=int(10 * q), V_steady_pct=round(hi, 2),
                         V_from_planting_pct=round(lo, 2), ground_cover_frac=round(hi / V_FULL, 3), W=round(whi, 3),
                         relative_erosion=round(1 - eta * hi / K, 3)))
    curve = pd.DataFrame(rows)
    out = dict(ET0_mm_yr=round(float(sec.ET0.mean()), 0), ET0g_mm_yr=round(et0g, 0), P_mm_yr=round(P, 1),
               K_pct=round(K, 2), V_full_pct=round(V_FULL, 1),
               saturation_irrigation_mm_yr=None, years_to_90pct_of_steady={})
    # smallest quota at which water stops limiting (W = 1 at steady state)
    for q in np.arange(0, 2001, 10):
        if steady(K, r, d, k, eta, q, 0.0, et0g, 0.9 * K)[1] >= 0.999:
            out["saturation_irrigation_mm_yr"] = int(q)
            break
    for q in (300, 600, 1000):
        V, _ = run(2.0, 60, K, r, d, k, eta, irrigation=q, et0g=et0g)
        target = 0.9 * steady(K, r, d, k, eta, q, 0.0, et0g, 2.0)[0]
        out["years_to_90pct_of_steady"][str(q)] = int(np.argmax(V >= target))
    # stop irrigation after 10 years at 600 mm
    V, _ = run(0.9 * K, 25, K, r, d, k, eta, irrigation=np.r_[np.full(10, 600.0), np.zeros(15)], et0g=et0g)
    out["abandonment_half_life_years"] = round(float(np.log(2) / d), 1)
    out["abandonment_series"] = [round(float(v), 2) for v in V]
    # rain only: v7 desert stations and section desert pixels
    out["rain_only"] = dict(model_steady_pct=steady(K, r, d, k, eta, 0.0, 0.0, et0g, 0.5 * K)[0],
                            observed_XT_pct=round(float(a[a.site == "XT"].V.mean()), 2),
                            observed_TZ_pct=round(float(a[a.site == "TZ"].V.mean()), 2))
    # natural ecotone: groundwater supply G that reproduces its observed cover
    cl = pd.read_csv(os.path.join(SEC, "class_annual_fvc.csv"))
    eco = cl[cl.cls == "ecotone"]["median"].mean()
    eco7 = 100 * (ND_S_LOC + eco * (ND_V_LOC - ND_S_LOC) - ND_S7) / (ND_V7 - ND_S7)
    gs = np.arange(0, 600, 1.0)
    vs = np.array([steady(K, r, d, k, eta, 0.0, g, et0g, 5.0)[0] for g in gs])
    out["ecotone"] = dict(observed_pct=round(float(eco7), 2), implied_G_mm_yr=float(gs[np.argmin(np.abs(vs - eco7))]))
    return curve, out, et0g


def sensitivity(K, r, d, k, eta, et0g):
    base = dict(K=K, r=r, d=d, k=k, eta=eta, et0g=et0g, c=C_KCB, eta_w=ETA_W)
    specs = {"c (canopy coefficient) 0.7-1.2": ("c", 0.7, 1.2), "eta_w 0.65-0.85": ("eta_w", 0.65, 0.85),
             "r +/- 1 sd": ("r", r - SD["r"], r + SD["r"]), "d +/- 1 sd": ("d", d - SD["d"], d + SD["d"]),
             "K +/- 15 %": ("K", 0.85 * K, 1.15 * K), "k 0-0.10": ("k", 0.0, 0.10),
             "ET0g +/- 10 %": ("et0g", 0.9 * et0g, 1.1 * et0g)}

    def v_at(q, **kw):
        p = dict(base, **kw)
        return steady(p["K"], p["r"], p["d"], p["k"], p["eta"], q, 0.0, p["et0g"], 0.9 * p["K"], c=p["c"], eta_w=p["eta_w"])[0]

    rows = [dict(parameter="baseline", low=None, high=None, V300_low=v_at(300), V300_high=v_at(300),
                 V600_low=v_at(600), V600_high=v_at(600))]
    for name, (key, lo, hi) in specs.items():
        rows.append(dict(parameter=name, low=round(lo, 4), high=round(hi, 4), V300_low=v_at(300, **{key: lo}),
                         V300_high=v_at(300, **{key: hi}), V600_low=v_at(600, **{key: lo}), V600_high=v_at(600, **{key: hi})))
    return pd.DataFrame(rows).round(2)


# ----------------------------------------------------------------------------- figures
def figures(a, sets, r, d, coh, cfit, traj, curve, sens):
    tr, te = sets
    fig, ax = plt.subplots(1, 3, figsize=(13.5, 3.9))
    for s, c in zip(VEG + BARE, list(PAL.values()) + ["#e87ba4", "#008300", "#e34948"]):
        q = a[a.site == s]
        ax[0].plot(q.year, q.W_v7, "-", color=c, lw=1.4, label=s)
        ax[1].plot(q.year, q.V, "-o", ms=2.5, color=c, lw=1.2, label=s)
    ax[0].set(title="(a) v7 water index W (from GWETROOT): flat in time", xlabel="year", ylabel="W", ylim=(-0.03, 1.05))
    ax[1].set(title="(b) Observed peak-season cover", xlabel="year", ylabel="V (%, v7 units)")
    ax[1].legend(fontsize=6.5, ncol=3)
    xo = np.r_[(tr.V_next / tr.K).values, (te.V_next / te.K).values]
    xp = np.r_[step((tr.V / tr.K).values, 1, 1, 1, r, d), step((te.V / te.K).values, 1, 1, 1, r, d)]
    n = len(tr)
    ax[2].plot(xo[:n], xp[:n], "o", ms=4, color=PAL["blue"], label="training (to 2022)")
    ax[2].plot(xo[n:], xp[n:], "s", ms=4, color=PAL["orange"], label="hold-out (2023-25)")
    ax[2].plot([0.5, 1.05], [0.5, 1.05], "--", color=PAL["ink"], lw=0.8)
    ax[2].set(title="(c) One-year-ahead, pooled M0 (r, d)", xlabel="observed V/K next year", ylabel="predicted V/K")
    ax[2].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "m1_fig1_station_evidence.png"))
    plt.close(fig)

    fig, ax = plt.subplots(1, 3, figsize=(13.5, 3.9))
    for (w, t0), q in coh.groupby(["window", "t0"]):
        c = PAL["aqua"] if w == "CON4" else PAL["orange"]
        ax[0].plot(q.tau, q.V, "o", ms=3, alpha=0.45, color=c)
    tt = pd.Series(np.arange(0, 22))
    ax[0].plot(tt, traj(cfit[0], cfit[1], tt), "-", color=PAL["ink"], lw=2, label="station r, d transferred (K, V0 fitted)")
    ax[0].plot([], [], "o", color=PAL["orange"], label="CON1-3 (used for K, V0)")
    ax[0].plot([], [], "o", color=PAL["aqua"], label="CON4 (held out)")
    ax[0].set(title="(a) Bare sand -> vegetation, 217 pixels", xlabel="years since establishment", ylabel="V (%, v7 units)")
    ax[0].legend(fontsize=7)
    ref = pd.read_csv(os.path.join(SEC, "daily_model_water_cover_curve.csv"))
    ref7 = 100 * (ND_S_LOC + ref.V_from_high * (ND_V_LOC - ND_S_LOC) - ND_S7) / (ND_V7 - ND_S7)
    ax[1].plot(curve.irrigation_mm_yr, curve.V_steady_pct, "o-", color=PAL["blue"], label="this model (yearly)")
    ax[1].plot(ref.irrigation_mm_yr, ref7, "s--", ms=3, color=PAL["violet"], label="earlier daily model (reference)")
    ax[1].set(title="(b) Water -> steady cover", xlabel="gross irrigation (mm / yr)   [x10 = m3 / ha / yr]", ylabel="V (%, v7 units)")
    ax[1].legend(fontsize=7)
    s = sens.iloc[1:].copy()
    s["span"] = (s.V300_high - s.V300_low).abs()
    s = s.sort_values("span")
    y = np.arange(len(s))
    b = sens.V300_low.iloc[0]
    ax[2].barh(y, s.V300_high - b, left=b, color=PAL["orange"], alpha=0.8, label="high value")
    ax[2].barh(y, s.V300_low - b, left=b, color=PAL["blue"], alpha=0.8, label="low value")
    ax[2].axvline(b, color=PAL["ink"], lw=0.8)
    ax[2].set_yticks(y)
    ax[2].set_yticklabels(s.parameter, fontsize=7)
    ax[2].set(title="(c) Steady cover at 300 mm / yr: sensitivity", xlabel="V (%, v7 units)")
    ax[2].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "m1_fig2_transfer_and_water.png"))
    plt.close(fig)


# ----------------------------------------------------------------------------- main
SD = {}


def main():
    d, a = yearly_table()
    out = {"checks_of_v7_inputs": check_v7_inputs(d, a)}
    fits, th, sets = fit_stations(a)
    out["station_fit"] = fits
    r, dd = float(th[0]), float(th[1])
    SD.update(r=fits["M0 (r,d)"]["sd"][0], d=fits["M0 (r,d)"]["sd"][1])
    # adopted: M0 for (r, d).  k is NOT identified (see M1 sd); it stays in the equation as a
    # scenario parameter with the M1 point estimate, eta = 1 (full shelter at V = K).
    k, eta = fits["M1 (r,d,k | eta=1)"]["theta"][2], 1.0
    coh = cohort_table()
    cres, cfit, traj = cohort_check(coh, r, dd)
    out["cohort_transfer"] = cres
    K = float(a[a.site.isin(SECTION)].drop_duplicates("site").K.mean())
    curve, wres, et0g = water_analysis(a, r, dd, k, eta, K)
    out["water"] = wres
    sens = sensitivity(K, r, dd, k, eta, et0g)
    out["adopted_parameters"] = dict(r=round(r, 4), r_sd=SD["r"], d=round(dd, 4), d_sd=SD["d"], k=k,
                                     k_status="not identified; scenario range 0-0.10", eta=eta,
                                     eta_status="fixed, not identifiable", K_section_pct=round(K, 2),
                                     x_star_no_water_limit=round(1 - dd / r, 3), c=C_KCB, eta_w=ETA_W,
                                     V_full_pct=round(V_FULL, 1))
    a.round(4).to_csv(os.path.join(RES, "yearly_table.csv"), index=False, encoding="utf-8-sig")
    curve.to_csv(os.path.join(RES, "water_cover_curve.csv"), index=False)
    sens.to_csv(os.path.join(RES, "sensitivity.csv"), index=False)
    with open(os.path.join(RES, "model1_results.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=float)
    figures(a, sets, r, dd, coh, cfit, traj, curve, sens)
    print(json.dumps(out, ensure_ascii=False, indent=1, default=float))
    print(curve.to_string(index=False))
    print(sens.to_string(index=False))


if __name__ == "__main__":
    main()
