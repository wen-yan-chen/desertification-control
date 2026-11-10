"""Model 1 driver: data study, calibration, hold-out validation, model analysis.  Offline.

    .venv/bin/python Code/m1_run.py

Reads Data/processed/model1/, writes Results/model1/ (numbers) and Figures/model1/ (PNG).
Sections
  A  what the data say (trends and drivers of cover, water and wind, 2001-2024)
  B  calibration with hold-out:  B1 irrigated establishment (converted pixels)
                                 B2 natural ecotone (groundwater subsidy)
                                 B3 bare desert (qualitative check)
  C  what the model says:  water -> cover curve, establishment time, abandonment,
     sand-transport reduction, one-at-a-time sensitivity, water-balance closure

Rules kept from the audit
  * parameters are estimated on the calibration subset only; hold-out data never enter a fit;
  * every skill score is the prediction R2 = 1 - SSE/SST of the coupled model itself,
    reported next to naive baselines; negative values are printed as they are;
  * no target value is prescribed in advance for any fit or benefit.
"""
import json
import warnings

import matplotlib
import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from scipy.stats import kendalltau, spearmanr, theilslopes

import m1_config as C
from m1_model import Params, annual_means, annual_sums, irrigation_schedule, simulate

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams.update({"figure.dpi": 130, "savefig.dpi": 200, "axes.grid": True, "grid.alpha": 0.25,
                     "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

# categorical colours in fixed order (colour-blind-checked default palette); one y-axis per panel
PAL = dict(blue="#2a78d6", orange="#eb6834", aqua="#1baf7a", yellow="#eda100", violet="#6250d6", ink="#52514e")

DP_SOURCE = "mean"          # hourly wind that drives DP.  "mean" = ERA5 hourly-mean 10 m wind: 450-590 h/yr
#                             >= 6 m/s on the section, same order as the 550-800 h/yr measured at Tazhong
#                             (Zhang et al. 2016 p.5).  "gust" = hourly 3-s gust: ~3000 h/yr, not a sustained
#                             wind, kept only as an upper bound.  See Docs, assumption A10.
CAL_END = 2016              # temporal hold-out: fit on <= 2016, test on 2017-2024


# ------------------------------------------------------------------------------ helpers
def load_forcing(site, dp_source=DP_SOURCE, y0=None, y1=None, scale=None):
    """Daily forcing dict for simulate().  scale: optional {'P':1.2,'ET0':0.9,'DP':1.5} factors."""
    df = pd.read_csv(C.PROC / f"forcing_{site}.csv", parse_dates=["date"])
    if y0:
        df = df[df.date.dt.year >= y0]
    if y1:
        df = df[df.date.dt.year <= y1]
    df = df.reset_index(drop=True)
    cols = [c for c in df.columns if c.startswith(f"DP_{dp_source}_")]
    mult = np.array([float(c.rsplit("_", 1)[1]) for c in cols])
    sc = scale or {}
    dp_tab = df[cols].values * sc.get("DP", 1.0)
    dp = dp_tab[:, 0]
    f = dict(date=df.date.values.astype("datetime64[D]"), year=df.date.dt.year.values,
             month=df.date.dt.month.values, P=df.P.values * sc.get("P", 1.0),
             ET0=df.ET0.values * sc.get("ET0", 1.0), Tsm=df.Tsm.values + sc.get("dT", 0.0),
             DP=dp, dp_tab=dp_tab, dp_mult=mult,
             DPbar=pd.Series(dp).rolling(365, min_periods=30).mean().bfill().values)
    return f


def cycle_forcing(f, n_years):
    """Repeat the observed record to get a long stationary run (for steady states)."""
    reps = int(np.ceil(n_years * 365.25 / len(f["P"])))
    g = {k: (np.tile(v, (reps, 1)) if v.ndim == 2 else np.tile(v, reps)) for k, v in f.items()
         if k not in ("dp_mult", "date", "year")}
    g["dp_mult"] = f["dp_mult"]
    span = int(f["year"].max() - f["year"].min() + 1)
    g["year"] = np.concatenate([f["year"] + i * span for i in range(reps)])
    g["date"] = f["date"][0] + np.arange(len(g["P"]))
    return g


def r2(obs, sim):
    obs, sim = np.asarray(obs, float), np.asarray(sim, float)
    return float(1.0 - np.sum((obs - sim) ** 2) / np.sum((obs - obs.mean()) ** 2))


def rmse(obs, sim):
    return float(np.sqrt(np.mean((np.asarray(obs) - np.asarray(sim)) ** 2)))


def mk_trend(years, y):
    """Theil-Sen slope per decade and Mann-Kendall (Kendall tau) p-value."""
    ok = np.isfinite(y)
    slope = theilslopes(y[ok], years[ok])[0]
    tau, p = kendalltau(years[ok], y[ok])
    return dict(slope_per_decade=round(float(slope * 10), 5), kendall_tau=round(float(tau), 3),
                p_value=round(float(p), 4), mean=round(float(np.nanmean(y)), 4))


# ------------------------------------------------------------------------------ A. data study
def data_study(win):
    cls = pd.read_csv(C.PROC / "class_annual_fvc.csv")
    out = {"cover_trends": {}, "driver_trends": {}, "ecotone_drivers": {}}
    years = np.arange(C.Y0, C.Y1 + 1)
    for k in ("desert", "ecotone", "converted", "oasis"):
        s = cls[cls.cls == k].set_index("year")["median"].reindex(years).values
        out["cover_trends"][k] = mk_trend(years, s)
    drivers = {}
    for site in C.FORCING_SITES:
        df = pd.read_csv(C.PROC / f"forcing_{site}.csv", parse_dates=["date"])
        g = df.groupby(df.date.dt.year)
        d = pd.DataFrame({"P_mm": g["P"].sum(), "ET0_mm": g["ET0"].sum(), "T_C": g["T"].mean(),
                          "u10_ms": g["wind_speed_10m_mean"].mean(), "DP_mean_VU": g["DP_mean_1.0"].mean(),
                          "DP_gust_VU": g["DP_gust_1.0"].mean(),
                          "aridity_P_over_ET0": g["P"].sum() / g["ET0"].sum(),
                          "sm_0_7": g["soil_moisture_0_to_7cm_mean"].mean(),
                          "sm_28_100": g["soil_moisture_28_to_100cm_mean"].mean()})
        drivers[site] = d
        out["driver_trends"][site] = {c: mk_trend(years, d[c].reindex(years).values) for c in d.columns}
    # which drivers co-vary with natural ecotone cover (year-to-year, detrended ranks)?
    eco = cls[cls.cls == "ecotone"].set_index("year")["median"].reindex(years)
    d = drivers["E_minfeng"].reindex(years)
    for c in ("P_mm", "ET0_mm", "T_C", "DP_gust_VU", "sm_0_7"):
        for lag in (0, 1):
            x = d[c].shift(lag)
            ok = x.notna() & eco.notna()
            rho, p = spearmanr(np.diff(x[ok]), np.diff(eco[ok]))     # first differences remove trend
            out["ecotone_drivers"][f"{c}_lag{lag}"] = dict(spearman_rho=round(float(rho), 3), p=round(float(p), 3))
    pd.concat(drivers, names=["site", "year"]).round(4).to_csv(C.RES / "annual_drivers.csv")
    return out, drivers, cls


# ------------------------------------------------------------------------------ B1. establishment
def cohort_table(win):
    """Median cover of converted pixels by (forcing site, establishment year t0, year)."""
    coh = pd.read_csv(C.PROC / "cohort_converted.csv").merge(win[["window", "forcing_site"]], on="window")
    coh = coh[coh.tau >= 0]
    g = coh.groupby(["forcing_site", "window", "t0", "year"])["fvc"]
    tab = pd.DataFrame({"fvc": g.median(), "n": g.count()}).reset_index()
    npx = coh.drop_duplicates(["window", "pixel"]).groupby(["window", "t0"]).size().rename("n_pixels")
    tab = tab.merge(npx.reset_index(), on=["window", "t0"])
    return tab[tab.n_pixels >= 3], coh                      # groups with >= 3 pixels only


def sim_cohort(p, v0, site, t0, forcings):
    f = forcings[(site, t0)]
    out = simulate(p, f, v0, demand_irrigation=True, m_init=1.0)
    yrs, v = annual_means(out, f, "V")
    _, irr = annual_sums(out, f, "I")
    return yrs, v, irr


def fit_establishment(tab, base):
    """Fit r, v_max and the initial cover v0 on the calibration groups.

    Water is NOT limiting in these runs (demand irrigation): the converted pixels are
    irrigated land of unknown regime, so what they identify is the potential growth
    rate r and the cover ceiling v_max - not a water response.
    """
    groups = tab.drop_duplicates(["forcing_site", "window", "t0"])[["forcing_site", "window", "t0", "n_pixels"]]
    forcings = {(s, t0): load_forcing(s, y0=int(t0)) for s, t0 in set(zip(groups.forcing_site, groups.t0))}
    cal = tab[tab.window.isin(CAL_WINDOWS)]
    val = tab[~tab.window.isin(CAL_WINDOWS)]

    def predict(theta, sub):
        r_, vmax_, v0_ = theta
        p = base.with_(r=r_, v_max=vmax_)
        pred = np.empty(len(sub))
        for (site, t0), idx in sub.groupby(["forcing_site", "t0"]).indices.items():
            yrs, v, _ = sim_cohort(p, v0_, site, t0, forcings)
            pred[idx] = pd.Series(v, index=yrs).reindex(sub.iloc[idx].year.values).values
        return pred

    def resid(theta, sub):
        return np.sqrt(sub.n_pixels.values) * (predict(theta, sub) - sub.fvc.values)

    fit = least_squares(resid, x0=[0.004, 0.7, 0.08], bounds=([5e-4, 0.3, 0.01], [0.05, 1.0, 0.3]),
                        args=(cal,), x_scale=[1e-3, 0.1, 0.02], diff_step=1e-2)
    theta = fit.x
    # approximate 1-sigma from the Jacobian (weighted least squares, Gauss-Newton covariance)
    dof = max(len(cal) - 3, 1)
    cov = np.linalg.pinv(fit.jac.T @ fit.jac) * (2 * fit.cost / dof)
    sd = np.sqrt(np.diag(cov))
    res = dict(r_per_day=float(theta[0]), r_per_year=float(theta[0] * 365.25), v_max=float(theta[1]),
               v0=float(theta[2]), sd=dict(r_per_day=float(sd[0]), v_max=float(sd[1]), v0=float(sd[2])),
               param_corr_r_vmax=float(cov[0, 1] / (sd[0] * sd[1])),
               calibration_windows=sorted(CAL_WINDOWS), n_cal=int(len(cal)), n_val=int(len(val)))
    for name, sub in (("calibration", cal), ("holdout_windows", val)):
        if len(sub) == 0:
            continue
        pr = predict(theta, sub)
        # baselines: (a) mean of calibration data, (b) data-only logistic curve in tau (no climate)
        res[name] = dict(n=int(len(sub)), rmse=rmse(sub.fvc, pr), r2=r2(sub.fvc, pr),
                         bias=float(np.mean(pr - sub.fvc.values)),
                         baseline_mean_rmse=rmse(sub.fvc, np.full(len(sub), cal.fvc.mean())),
                         baseline_mean_r2=r2(sub.fvc, np.full(len(sub), cal.fvc.mean())))
    # baseline (b): plain logistic in years-since-establishment fitted on the calibration set
    tau_c, tau_v = (cal.year - cal.t0).values, (val.year - val.t0).values
    lg = lambda th, tau: th[1] / (1 + (th[1] / th[2] - 1) * np.exp(-th[0] * tau))
    lfit = least_squares(lambda th: np.sqrt(cal.n_pixels.values) * (lg(th, tau_c) - cal.fvc.values),
                         x0=[0.5, 0.7, 0.1], bounds=([0.01, 0.2, 0.01], [5, 1, 0.4]))
    res["baseline_logistic"] = dict(rate_per_year=float(lfit.x[0]), plateau=float(lfit.x[1]), v0=float(lfit.x[2]),
                                    calibration_rmse=rmse(cal.fvc, lg(lfit.x, tau_c)),
                                    calibration_r2=r2(cal.fvc, lg(lfit.x, tau_c)))
    if len(val):
        res["baseline_logistic"].update(holdout_rmse=rmse(val.fvc, lg(lfit.x, tau_v)),
                                        holdout_r2=r2(val.fvc, lg(lfit.x, tau_v)))
    return res, theta, forcings, predict


# ------------------------------------------------------------------------------ B2. ecotone
def fit_ecotone(cls, base, site="E_minfeng"):
    """Natural sparse vegetation: no irrigation.  One free parameter, the groundwater /
    flood subsidy g_cap (mm/day), fitted on 2001-CAL_END; 2017-2024 is a free-running test."""
    years = np.arange(C.Y0, C.Y1 + 1)
    obs = cls[cls.cls == "ecotone"].set_index("year")["median"].reindex(years).values
    f = load_forcing(site)
    cal = years <= CAL_END

    def run(g):
        out = simulate(base.with_(g_cap=float(g)), f, obs[0], m_init=0.5)
        return annual_means(out, f, "V")[1], out

    fit = least_squares(lambda th: (run(th[0])[0] - obs)[cal], x0=[0.3], bounds=([0.0], [3.0]), diff_step=1e-2)
    sim, out = run(fit.x[0])
    res = dict(g_cap_mm_day=float(fit.x[0]), g_cap_mm_year=float(fit.x[0] * 365.25),
               rain_only_cover_2024=float(annual_means(simulate(base, f, obs[0]), f, "V")[1][-1]),
               obs_mean=float(np.nanmean(obs)), sim_mean=float(sim.mean()))
    for name, m in (("calibration", cal), ("holdout_2017_2024", ~cal)):
        clim = np.full(m.sum(), obs[cal].mean())                 # baseline 1: calibration mean
        pers = np.r_[obs[0], obs[:-1]][m]                        # baseline 2: last year's value
        res[name] = dict(rmse=rmse(obs[m], sim[m]), r2=r2(obs[m], sim[m]),
                         baseline_mean_rmse=rmse(obs[m], clim), baseline_persistence_rmse=rmse(obs[m], pers))
    res["anomaly_corr_all_years"] = float(np.corrcoef(obs - obs.mean(), sim - sim.mean())[0, 1])
    return res, years, obs, sim, out, f


# ------------------------------------------------------------------------------ C. model analysis
def steady_cover(p, f_long, w_mm, v0, n_last=10):
    """Cover after a long run under a fixed yearly irrigation quota (mean of last n_last years)."""
    irr = irrigation_schedule(f_long["date"], w_mm)
    out = simulate(p, f_long, v0, irrigation=irr, m_init=0.5)
    yrs, v = annual_means(out, f_long, "V")
    return float(v[-n_last:].mean()), out, irr


def water_cover_curve(p, f, quotas, n_years=72):
    f_long = cycle_forcing(f, n_years)
    rows = []
    for w in quotas:
        lo, out_lo, _ = steady_cover(p, f_long, w, 0.05)        # newly planted
        hi, out_hi, _ = steady_cover(p, f_long, w, 0.60)        # established stand
        yrs = np.unique(f_long["year"])[-10:]
        sel = np.isin(f_long["year"], yrs)
        nyr = sel.sum() / 365.25
        rows.append(dict(irrigation_mm_yr=w, irrigation_m3_ha_yr=10 * w, V_from_low=lo, V_from_high=hi,
                         M_growing_season=float(out_hi["M"][sel & (f_long["month"] >= 4) & (f_long["month"] <= 10)].mean()),
                         T_mm_yr=float(out_hi["T"][sel].sum() / nyr), E_mm_yr=float(out_hi["E"][sel].sum() / nyr),
                         perc_mm_yr=float(out_hi["perc"][sel].sum() / nyr),
                         sand_rel=float(out_hi["sand"][sel].mean() / max(f_long["DP"][sel].mean(), 1e-9)),
                         DP_VU=float(f_long["DP"][sel].mean())))
    return pd.DataFrame(rows)


def min_quota_for(curve, target, col="V_from_high"):
    """Smallest irrigation quota whose steady cover reaches the target (linear interpolation)."""
    v, w = curve[col].values, curve["irrigation_mm_yr"].values
    if v.max() < target:
        return None
    i = int(np.argmax(v >= target))
    if i == 0:
        return float(w[0])
    return float(w[i - 1] + (target - v[i - 1]) * (w[i] - w[i - 1]) / (v[i] - v[i - 1]))


def establishment_time(p, f, w_mm, v_plant=0.05, target=None, n_years=40):
    target = p.v_c if target is None else target
    f_long = cycle_forcing(f, n_years)
    out = simulate(p, f_long, v_plant, irrigation=irrigation_schedule(f_long["date"], w_mm), m_init=1.0)
    yrs, v = annual_means(out, f_long, "V")
    hit = np.where(v >= target)[0]
    return (int(hit[0]) + 1 if len(hit) else None), v


def abandonment(p, f, w_mm, v_start, stop_after=10, n_years=30):
    """Irrigate for `stop_after` years, then stop: how fast is the stand lost?"""
    f_long = cycle_forcing(f, n_years)
    y0 = int(f_long["year"].min())
    quota = {y0 + i: (w_mm if i < stop_after else 0.0) for i in range(n_years + 30)}
    out = simulate(p, f_long, v_start, irrigation=irrigation_schedule(f_long["date"], quota), m_init=0.8)
    return annual_means(out, f_long, "V")[1][:n_years]


SENS = {  # one-at-a-time ranges (low, high): literature range where one exists, else +-30 %
    "theta_fc - theta_wp (FAO-56 sand 0.05-0.11)": (dict(theta_fc=0.095), dict(theta_fc=0.155)),
    "z_root 0.6-2.0 m": (dict(z_root=0.6), dict(z_root=2.0)),
    "p_stress 0.4-0.7": (dict(p_stress=0.4), dict(p_stress=0.7)),
    "kcb_full 0.7-1.2": (dict(kcb_full=0.7), dict(kcb_full=1.2)),
    "f_wet 0.2-0.5": (dict(f_wet=0.2), dict(f_wet=0.5)),
    "eta_irr 0.8-0.95": (dict(eta_irr=0.8), dict(eta_irr=0.95)),
    "r -/+30 %": ("r*0.7", "r*1.3"),
    "v_max -/+0.1": ("v_max-0.1", "v_max+0.1"),
    "m_w 0.3-3 /yr": (dict(m_w=0.3 / 365.25), dict(m_w=3.0 / 365.25)),
    "eps x0.3-x3": ("eps*0.3", "eps*3"),
    "v_c 0.15-0.40": (dict(v_c=0.15), dict(v_c=0.40)),
    "t_base 5-12 C": (dict(t_base=5.0), dict(t_base=12.0)),
    "ET0 -/+10 %": ({"__scale__": {"ET0": 0.9}}, {"__scale__": {"ET0": 1.1}}),
    "P x0.5-x2": ({"__scale__": {"P": 0.5}}, {"__scale__": {"P": 2.0}}),
    "DP x0.5-x4": ({"__scale__": {"DP": 0.5}}, {"__scale__": {"DP": 4.0}}),
    "warming +2 C (Tsm only)": ({"__scale__": {"dT": 0.0}}, {"__scale__": {"dT": 2.0}}),
}


def perturb(p, spec):
    if isinstance(spec, str):
        for op in ("*", "+", "-"):
            if op in spec:
                name, val = spec.split(op)
                cur = getattr(p, name)
                return p.with_(**{name: cur * float(val) if op == "*" else cur + float(val) * (1 if op == "+" else -1)}), None
    if "__scale__" in spec:
        return p, spec["__scale__"]
    return p.with_(**spec), None


def sensitivity(p, site, quotas, target):
    rows = []
    for name, (lo, hi) in SENS.items():
        vals = []
        for spec in (lo, hi):
            q, scale = perturb(p, spec)
            curve = water_cover_curve(q, load_forcing(site, scale=scale), quotas, n_years=48)
            vals.append((min_quota_for(curve, target), float(np.interp(300, curve.irrigation_mm_yr, curve.V_from_high))))
        rows.append(dict(parameter=name, Wmin_low=vals[0][0], Wmin_high=vals[1][0],
                         V300_low=vals[0][1], V300_high=vals[1][1]))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------ figures
def fig_study_area(win):
    z = np.load(C.PROC / "area_ndvi_epochs.npz")
    fig, ax = plt.subplots(2, 1, figsize=(9, 7.2), sharex=True)
    for a, k, t in ((ax[0], "early", "Mean summer NDVI 2001-2003"), (ax[1], "late", "Mean summer NDVI 2022-2024")):
        m = a.pcolormesh(z["lon"], z["lat"], z[k], vmin=0, vmax=0.6, cmap="YlGn", shading="auto", rasterized=True)
        plt.colorbar(m, ax=a, pad=0.01, label="NDVI")
        col = {"converted": PAL["orange"], "ecotone": PAL["blue"], "desert": PAL["ink"], "oasis": PAL["violet"]}
        for r in win.itertuples():
            a.plot(r.lon, r.lat, "s", mfc="none", mec=col[r.cls], ms=8, mew=1.5)
            a.annotate(r.window, (r.lon, r.lat), xytext=(4, 4), textcoords="offset points", fontsize=7, color=col[r.cls])
        for s, (la, lo) in C.FORCING_SITES.items():
            a.plot(lo, la, "*", color=PAL["yellow"], ms=10, mec="k", mew=0.5)
        a.set_title(t, loc="left")
        a.set_ylabel("Latitude (deg N)")
        a.grid(False)
    ax[1].set_xlabel("Longitude (deg E)   [squares: 9x9-pixel MODIS windows; stars: forcing sites]")
    fig.tight_layout()
    fig.savefig(C.FIG / "fig1_study_area.png")
    plt.close(fig)


def fig_data(cls, drivers):
    fig, ax = plt.subplots(2, 2, figsize=(10, 6.2))
    col = {"converted": PAL["orange"], "ecotone": PAL["blue"], "desert": PAL["ink"], "oasis": PAL["violet"]}
    for k, c in col.items():
        s = cls[cls.cls == k]
        ax[0, 0].fill_between(s.year, s.q25, s.q75, color=c, alpha=0.15, lw=0)
        ax[0, 0].plot(s.year, s["median"], "-o", ms=3, color=c, label=f"{k} (n={int(s.n.median())} px)")
    ax[0, 0].set(title="(a) Peak-season cover by land class (median, IQR)", ylabel="FVC")
    ax[0, 0].legend(fontsize=7)
    for (site, d), c in zip(drivers.items(), ("blue", "orange", "aqua")):
        ax[0, 1].plot(d.index, d.P_mm, "-o", ms=3, color=PAL[c], label=site)
        ax[1, 0].plot(d.index, d.ET0_mm, "-o", ms=3, color=PAL[c], label=site)
        ax[1, 1].plot(d.index, d.DP_mean_VU, "-o", ms=3, color=PAL[c], label=site)
    ax[0, 1].set(title="(b) Annual precipitation", ylabel="mm / yr")
    ax[1, 0].set(title="(c) Reference evapotranspiration (FAO-56 PM)", ylabel="mm / yr")
    ax[1, 1].set(title="(d) Drift potential, hourly mean wind", ylabel="VU", ylim=(0, None))
    for a in ax.flat[1:]:
        a.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(C.FIG / "fig2_data_overview.png")
    plt.close(fig)


def fig_calibration(tab, theta, predict, eco, base):
    years, obs, sim, out, f = eco
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.9))
    pred = predict(theta, tab)
    for (w, t0), s in tab.assign(pred=pred).groupby(["window", "t0"]):
        cal = w in CAL_WINDOWS
        ax[0].plot(s.year - t0, s.fvc, "o", ms=3, alpha=0.5, color=PAL["orange"] if cal else PAL["aqua"])
        ax[0].plot(s.year - t0, s.pred, "-", lw=0.8, alpha=0.6, color=PAL["orange"] if cal else PAL["aqua"])
    ax[0].plot([], [], "o-", color=PAL["orange"], label="calibration windows (obs / model)")
    ax[0].plot([], [], "o-", color=PAL["aqua"], label="hold-out window (obs / model)")
    ax[0].set(title="(a) Irrigated establishment (converted pixels)", xlabel="years since establishment", ylabel="peak-season cover V")
    ax[0].legend(fontsize=7)
    ax[1].plot(tab.fvc, pred, ".", ms=4, color="0.3")
    ax[1].plot([0, 1], [0, 1], "k--", lw=0.8)
    ax[1].set(title="(b) Observed vs modelled, all cohort-years", xlabel="observed", ylabel="modelled", xlim=(0, 1), ylim=(0, 1))
    ax[2].plot(years, obs, "o-", color=PAL["blue"], ms=3, label="observed ecotone median")
    ax[2].plot(years, sim, "-", color="k", label="model (g_cap fitted <= %d)" % CAL_END)
    ax[2].axvspan(CAL_END + 0.5, years[-1] + 0.5, color="0.9", zorder=0, label="hold-out")
    ax[2].set(title="(c) Natural ecotone, no irrigation", xlabel="year", ylabel="peak-season cover V",
              ylim=(0, max(0.2, 1.3 * np.nanmax(obs))))
    ax[2].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(C.FIG / "fig3_calibration_validation.png")
    plt.close(fig)


def fig_model(curve, est, aband, p, out_demo, f_demo):
    fig, ax = plt.subplots(2, 3, figsize=(14.5, 7))
    a = ax[0, 0]
    a.plot(curve.irrigation_mm_yr, curve.V_from_high, "o-", color=PAL["aqua"], label="established stand (start V=0.60)")
    a.plot(curve.irrigation_mm_yr, curve.V_from_low, "s--", color=PAL["yellow"], ms=3, label="new planting (start V=0.05)")
    a.axhline(p.v_c, color=PAL["ink"], lw=0.8, ls=":")
    a.text(curve.irrigation_mm_yr.max(), p.v_c + 0.01, "critical cover v_c", ha="right", color=PAL["ink"], fontsize=7)
    a.set(title="(a) Water -> steady cover", xlabel="gross irrigation (mm / yr)   [x10 = m3 / ha / yr]", ylabel="cover V")
    a.legend(fontsize=7)
    a = ax[1, 2]
    a.plot(curve.irrigation_mm_yr, curve.sand_rel, "o-", color=PAL["violet"])
    a.set(title="(f) Water -> sand transport (established stand)", xlabel="gross irrigation (mm / yr)",
          ylabel="sand transport / bare-surface potential", ylim=(0, 1.05))
    a = ax[0, 2]
    a.stackplot(curve.irrigation_mm_yr, curve.T_mm_yr, curve.E_mm_yr, curve.perc_mm_yr,
                labels=["transpiration", "soil evaporation", "deep percolation"],
                colors=[PAL["aqua"], PAL["yellow"], PAL["blue"]], alpha=0.85)
    a.set(title="(c) Where the water goes (steady state)", xlabel="gross irrigation (mm / yr)", ylabel="mm / yr")
    a.legend(fontsize=7, loc="upper left")
    a = ax[0, 1]
    for (w, (yrs_to, v)), c in zip(est.items(), ("blue", "orange", "aqua", "violet")):
        a.plot(np.arange(1, len(v) + 1), v, color=PAL[c], label=f"{w} mm/yr" + (f" (v_c in {yrs_to} yr)" if yrs_to else " (v_c never)"))
    a.axhline(p.v_c, color=PAL["ink"], lw=0.8, ls=":")
    a.set(title="(b) Establishment from planting (V0 = 0.05)", xlabel="years after planting", ylabel="cover V", xlim=(1, 25))
    a.legend(fontsize=7)
    a = ax[1, 0]
    for (lab, v), c in zip(aband.items(), ("blue", "orange")):
        a.plot(np.arange(1, len(v) + 1), v, color=PAL[c], label=lab)
    a.axvline(10.5, color="0.5", lw=0.8, ls="--")
    a.axhline(p.v_c, color=PAL["ink"], lw=0.8, ls=":")
    a.set(title="(d) Irrigation stopped after year 10", xlabel="year", ylabel="cover V")
    a.legend(fontsize=7)
    a = ax[1, 1]
    n = 3 * 365
    t = f_demo["date"][:n]
    a.plot(t, out_demo["M"][:n], color=PAL["blue"], lw=0.8, label="effective soil moisture M")
    a.plot(t, out_demo["V"][:n], color=PAL["aqua"], lw=1.6, label="cover V")
    a.set(title="(e) Daily states, first 3 years after planting (300 mm/yr)", ylabel="-")
    a.legend(fontsize=7)
    a.tick_params(axis="x", labelrotation=30)
    fig.tight_layout()
    fig.savefig(C.FIG / "fig4_model_behaviour.png")
    plt.close(fig)


def fig_sensitivity(sens, base_w, base_v):
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.6))
    s = sens.copy()
    s["span"] = (s.Wmin_high.fillna(900) - s.Wmin_low.fillna(900)).abs()
    s = s.sort_values("span")
    y = np.arange(len(s))
    ax[0].barh(y, s.Wmin_high.fillna(900) - base_w, left=base_w, color=PAL["orange"], alpha=0.7, label="high value")
    ax[0].barh(y, s.Wmin_low.fillna(900) - base_w, left=base_w, color=PAL["blue"], alpha=0.7, label="low value")
    ax[0].set_yticks(y)
    ax[0].set_yticklabels(s.parameter, fontsize=7)
    ax[0].axvline(base_w, color="k", lw=0.8)
    ax[0].set(title="(a) Minimum irrigation to hold V >= v_c", xlabel="mm / yr (bars at 900 = target not reachable)")
    ax[0].legend(fontsize=7)
    s2 = sens.assign(span=(sens.V300_high - sens.V300_low).abs()).sort_values("span")
    ax[1].barh(y, s2.V300_high - base_v, left=base_v, color=PAL["orange"], alpha=0.7)
    ax[1].barh(y, s2.V300_low - base_v, left=base_v, color=PAL["blue"], alpha=0.7)
    ax[1].set_yticks(y)
    ax[1].set_yticklabels(s2.parameter, fontsize=7)
    ax[1].axvline(base_v, color="k", lw=0.8)
    ax[1].set(title="(b) Steady cover at 300 mm / yr", xlabel="cover V")
    fig.tight_layout()
    fig.savefig(C.FIG / "fig5_sensitivity.png")
    plt.close(fig)


# ------------------------------------------------------------------------------ main
CAL_WINDOWS = set()


def main():
    global CAL_WINDOWS
    C.RES.mkdir(parents=True, exist_ok=True)
    C.FIG.mkdir(parents=True, exist_ok=True)
    win = pd.read_csv(C.PROC / "windows.csv")
    results = {"dp_source": DP_SOURCE, "calibration_end_year": CAL_END}
    base = Params()

    # ---- A ------------------------------------------------------------------------------
    study, drivers, cls = data_study(win)
    results["data_study"] = study
    fig_study_area(win)
    fig_data(cls, drivers)

    # ---- B1 -----------------------------------------------------------------------------
    tab, coh = cohort_table(win)
    con = sorted(tab.window.unique())
    # spatial hold-out: the easternmost converted window is never used for fitting
    holdout = win[win.window.isin(con)].sort_values("lon").window.iloc[-1]
    CAL_WINDOWS = set(con) - {holdout}
    est_res, theta, forcings, predict = fit_establishment(tab, base)
    est_res["holdout_window"] = holdout
    results["establishment_fit"] = est_res
    p = base.with_(r=float(theta[0]), v_max=float(theta[1]))
    # implied irrigation demand of the non-limited cohort runs (mm/yr, by cover level)
    dem = []
    for (site, t0) in forcings:
        yrs, v, irr = sim_cohort(p, float(theta[2]), site, t0, forcings)
        dem += [(site, t0, y, vv, ii) for y, vv, ii in zip(yrs, v, irr)]
    dem = pd.DataFrame(dem, columns=["site", "t0", "year", "V", "irrigation_mm"])
    dem.round(4).to_csv(C.RES / "demand_irrigation_runs.csv", index=False)
    results["nonlimiting_irrigation_mm_yr_at_V_ge_0p5"] = float(dem[dem.V >= 0.5].irrigation_mm.mean())

    # ---- B2 / B3 --------------------------------------------------------------------------
    eco_res, years, obs, sim, out_eco, f_eco = fit_ecotone(cls, p)
    results["ecotone_fit"] = eco_res
    f_des = load_forcing("M_gap")
    out_des = simulate(p, f_des, 0.05)
    results["desert_check"] = dict(
        start_cover=0.05, cover_after_5yr=float(annual_means(out_des, f_des, "V")[1][4]),
        cover_2024=float(annual_means(out_des, f_des, "V")[1][-1]),
        observed_desert_fvc_median=float(cls[cls.cls == "desert"]["median"].median()),
        mean_M=float(out_des["M"].mean()),
        ledger=out_des["ledger"])
    fig_calibration(tab, theta, predict, (years, obs, sim, out_eco, f_eco), p)

    # ---- C ----------------------------------------------------------------------------------
    site = "M_gap"                                   # mid-section forcing for the design curves
    f = load_forcing(site)
    quotas = [0, 50, 100, 150, 200, 250, 300, 350, 400, 500, 600, 800]
    curve = water_cover_curve(p, f, quotas)
    curve.round(4).to_csv(C.RES / "water_cover_curve.csv", index=False)
    w_min = min_quota_for(curve, p.v_c)
    results["water_constraint"] = dict(
        forcing_site=site, target_cover=p.v_c,
        min_irrigation_mm_yr_hold=w_min, min_irrigation_m3_ha_yr_hold=None if w_min is None else 10 * w_min,
        min_irrigation_mm_yr_from_planting=min_quota_for(curve, p.v_c, "V_from_low"),
        section_volume_Mm3_yr=None if w_min is None else 10 * w_min * C.SECTION["area_ha"] / 1e6,
        cover_at_300mm=float(np.interp(300, curve.irrigation_mm_yr, curve.V_from_high)))
    est = {w: establishment_time(p, f, w) for w in (200, 300, 400, 600)}
    results["years_to_critical_cover"] = {str(w): e[0] for w, e in est.items()}
    v_hold = float(np.interp(400, curve.irrigation_mm_yr, curve.V_from_high))
    aband = {"400 mm/yr, then 0": abandonment(p, f, 400, v_hold),
             "400 mm/yr, then 0, barriers halve DP": abandonment(p.with_(shelter=0.5), f, 400, v_hold)}
    results["abandonment_years_to_lose_half"] = {
        k: int(np.argmax(v[10:] < 0.5 * v[9]) + 1) if np.any(v[10:] < 0.5 * v[9]) else None for k, v in aband.items()}
    f_long = cycle_forcing(f, 24)
    out_demo = simulate(p, f_long, 0.05, irrigation=irrigation_schedule(f_long["date"], 300), m_init=1.0)
    results["ledger_irrigated_300mm_24yr"] = out_demo["ledger"]
    # wet-surface effect on sand: bare cell, with vs without the Fecan threshold correction
    dry = dict(f_des)
    dry.pop("dp_tab")
    o_wet, o_dry = simulate(p, f_des, 0.0), simulate(p, dry, 0.0)
    results["wet_surface_reduction_of_DP_percent"] = float(100 * (1 - o_wet["DPeff"].sum() / o_dry["DPeff"].sum()))
    fig_model(curve, est, aband, p, out_demo, f_long)

    sens = sensitivity(p, site, [0, 100, 200, 300, 400, 500, 600, 800], p.v_c)
    sens.round(4).to_csv(C.RES / "sensitivity_oat.csv", index=False)
    fig_sensitivity(sens, w_min if w_min is not None else 900, results["water_constraint"]["cover_at_300mm"])

    results["parameters"] = p.as_dict()
    (C.RES / "model1_results.json").write_text(json.dumps(results, indent=1, default=float))
    print(json.dumps({k: v for k, v in results.items() if k not in ("parameters", "data_study")}, indent=1, default=float))


if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        main()
