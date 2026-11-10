"""Reproducible M1 calculation/export orchestration; deliberately no plotting."""
from dataclasses import asdict, replace
from pathlib import Path
import hashlib
import json
import platform
import numpy as np
import pandas as pd
import scipy
from scipy.optimize import least_squares
import v7_model1 as model
from v7_m1_water import WaterParameters, trajectory, equilibrium

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Results/v7/model1"

def save(frame, name):
    frame.to_csv(OUT / name, index=False, float_format="%.10g")

def prediction_pairs(a, th):
    _, _, (train, test) = model.fit_stations(a)
    records = []
    for split, data in (("train", train), ("test", test)):
        q = data[["site", "year", "target_year", "V", "V_next", "K", "n_obs", "n_obs_next"]].copy()
        q["split"] = split
        q["observed_x"] = q.V_next/q.K
        q["predicted_x"] = model.step(q.V/q.K, 1., 1., 1., *th)
        q["persistence_x"] = q.V/q.K
        records.append(q)
    return pd.concat(records, ignore_index=True)

def bootstrap(train, repetitions=300):
    """Station-cluster resampling; small number of clusters remains a limitation."""
    rng = np.random.default_rng(20261110)
    sites, rows = train.site.unique(), []
    for i in range(repetitions):
        selected = rng.choice(sites, len(sites), replace=True)
        q = pd.concat([train[train.site == site] for site in selected])
        x, y = (q.V/q.K).to_numpy(), (q.V_next/q.K).to_numpy()
        fit = least_squares(lambda th: model.step(x, 1., 1., 1., *th)-y,
                            [0.5, 0.1], bounds=([0, 0], [3, 1]))
        rows.append(dict(replicate=i, r=fit.x[0], d=fit.x[1]))
    return pd.DataFrame(rows)

def forcing_table(panel):
    sec = panel[panel.site.isin(model.SECTION) & (panel.date.dt.year <= model.TRAIN_END)].copy()
    sec["month"] = sec.date.dt.month
    sec["ET0g_mm"] = model.f_temp(sec.era_T)*sec.era_et0_mm
    f = sec.groupby("month").agg(P_mm=("era_P_mm", "mean"), ET0g_mm=("ET0g_mm", "mean"),
        ET0_mm=("era_et0_mm", "mean"), E=("E", "mean"))
    f["days"] = [31,28,31,30,31,30,31,31,30,31,30,31]
    # Historical climatology repeats, not future climate prediction.
    return f.reset_index()

def main():
    OUT.mkdir(exist_ok=True)
    panel, annual = model.yearly_table()
    fits, th, (train, test) = model.fit_stations(annual)
    r, d = map(float, th)
    K = float(annual[annual.site.isin(model.SECTION)].drop_duplicates("site").K.mean())
    pars = WaterParameters()
    ftab = forcing_table(panel)
    forcing = ftab[["days", "P_mm", "ET0g_mm"]].to_numpy()
    coh = model.cohort_table()
    cohort_result, cfit, traj = model.cohort_check(coh, r, d)
    coh["predicted_transfer_pct"] = traj(*cfit, coh.tau)
    coh["diagnostic_split"] = np.where(coh.window == "CON4", "spatial_diagnostic", "fit")
    save(coh, "cohort_diagnostic_pairs.csv")
    pairs = prediction_pairs(annual, th)
    save(pairs, "prediction_pairs.csv")
    boot = bootstrap(train)
    save(boot, "parameter_cluster_bootstrap.csv")
    metrics = []
    for site, q in pairs[pairs.split == "test"].groupby("site"):
        mse = np.mean((q.observed_x-q.predicted_x)**2)
        base = np.mean((q.observed_x-q.persistence_x)**2)
        metrics.append(dict(site=site, n=len(q), rmse=np.sqrt(mse), persistence_rmse=np.sqrt(base),
                            mse_skill_vs_persistence=1-mse/base if base > 0 else None))
    save(pd.DataFrame(metrics), "holdout_by_site.csv")
    # Free-running holdout starts only from 2022; no assimilation of 2023/2024 targets.
    free = []
    for site in train.site.unique():
        q = annual[annual.site == site].set_index("year")
        v, ceiling = float(q.loc[2022, "V"]), float(q.loc[2022, "K"])
        for year in (2023, 2024, 2025):
            v = float(model.step(v, ceiling, 1., 1., r, d))
            free.append(dict(site=site, year=year, predicted_pct=v, observed_pct=q.loc[year, "V"],
                             persistence_2022_pct=q.loc[2022, "V"]))
    save(pd.DataFrame(free), "free_running_holdout.csv")
    curves, yearly, monthly = [], [], []
    for quota in (0, 50, 100, 150, 200, 300, 400, 500, 600, 800, 1000, 1500, 2000):
        low = equilibrium(2., pars.capacity_mm/2, K, r, d, forcing, quota, pars)
        high = equilibrium(0.9*K, pars.capacity_mm/2, K, r, d, forcing, quota, pars)
        curves.append(dict(irrigation_mm_yr=quota, irrigation_m3_ha_yr=10*quota,
            V_steady_pct=high["V_pct"], V_from_planting_pct=low["V_pct"], M_periodic_end_mm=high["M_mm"],
            W=high["W"], local_endmember_cover_proxy=high["V_pct"]/pars.v_full_pct,
            relative_erosion_scenario=1-high["V_pct"]/K,
            converged_both=low["converged"] and high["converged"],
            max_fixed_point_residual=max(low["residual"], high["residual"])))
        a, m = trajectory(2., pars.capacity_mm/2, 25, K, r, d, forcing, quota, pars)
        yearly.append(a.assign(scenario=f"I{quota}", calendar_year=a.year+2025))
        monthly.append(m.assign(scenario=f"I{quota}", calendar_year=m.year+2025))
    # Stop-irrigation scenario; calendar endpoint explicitly 2050, not 2051.
    a, m = trajectory(2., pars.capacity_mm/2, 25, K, r, d, forcing, [600.]*10+[0.]*15, pars)
    yearly.append(a.assign(scenario="stop_after_10", calendar_year=a.year+2025))
    monthly.append(m.assign(scenario="stop_after_10", calendar_year=m.year+2025))
    sensitivity = []
    specs = dict(capacity_mm=[30.,150.], rain_fraction=[0.,1.], c=[0.7,1.2],
                 eta_w=[0.65,0.85], depletion_fraction=[0.3,0.7], v_full_pct=[64.85,69.4])
    for key, values in specs.items():
        for value in values:
            for quota in (300,600):
                z = equilibrium(2., min(37.5, replace(pars, **{key:value}).capacity_mm), K, r, d,
                    forcing, quota, replace(pars, **{key:value}))
                sensitivity.append(dict(parameter=key, value=value, irrigation_mm_yr=quota, **z))
    for wind_k in (0.,0.02,0.05,0.10):
        z = equilibrium(2.,37.5,K,r,d,forcing,300,pars,k=wind_k)
        sensitivity.append(dict(parameter="k_scenario", value=wind_k, irrigation_mm_yr=300, **z))
    qa75 = panel.copy()
    qa75["V_pct"] = qa75.V_pct_qa75
    qa75["year"] = qa75.date.dt.year
    qa75["month"] = qa75.date.dt.month
    tmp = qa75[qa75.month.between(6,9)].groupby(["site","year"]).V_pct.agg(["mean","count"]).reset_index()
    alternate = annual.drop(columns=["V", "n_obs", "K", "V_next"]).merge(
        tmp.rename(columns={"mean":"V","count":"n_obs"}), on=["site","year"])
    alternate.loc[alternate.n_obs < 2,"V"] = np.nan
    alternate["K"] = alternate.site.map(1.15*alternate[alternate.year<=2022].groupby("site").V.quantile(.95))
    alternate["V_next"] = alternate.groupby("site").V.shift(-1)
    fit75, _, _ = model.fit_stations(alternate)
    inputs = [ROOT/"Data/v7/m1_audited/panel_m1.csv", ROOT/"Data/v7/m1_audited/replay_manifest.json",
              ROOT/"Data/v7/section_modis/cohort_converted.csv", ROOT/"Data/v7/m1_audited/section_definition.json",
              ROOT/"Data/v7/section_modis/endmembers.json"]
    out = dict(status="implemented; scenario-ready; NOT field-calibrated water or erosion forecast",
        formal_model_ready=False, station_fit=fits,
        uncertainty=dict(method="local least-squares sd is conditional IID approximation; cluster bootstrap separately",
            cluster_count=int(train.site.nunique()), bootstrap_seed=20261110,
            bootstrap_percentiles=boot[["r","d"]].quantile([.025,.5,.975]).to_dict()),
        adopted_parameters=dict(r=r,d=d,K_section_pct=K,k=0.,eta=1.,water=asdict(pars)),
        qa75_sensitivity=fit75, cohort_transfer=cohort_result,
        water=dict(forcing="2015-2022 YT/MF Open-Meteo archive monthly climatology; provider model unspecified",
            annual_rain_mm=float(forcing[:,1].sum()),annual_ET0g_mm=float(forcing[:,2].sum()),
            maximum_balance_residual_mm=float(pd.concat(monthly).balance_residual_mm.abs().max()),
            discrete_no_water_half_life_years=float(np.log(.5)/np.log1p(-d))),
        limitations=["W=1 for oasis parameter fitting is an unverified calibration assumption",
            "annual June-September cover proxy, not measured ground cover or year-end cover",
            "no field water-storage/irrigation pairs; bucket parameters are scenarios",
            "selected cohort is retrospective, not independent prospective validation",
            "site windows are not an engineering belt polygon; no verified section area",
            "wind index from daily maximum is a proxy, not actual erosion or hazard counts"],
        input_sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        runtime=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__))
    save(annual, "yearly_table.csv")
    save(ftab, "section_forcing_climatology.csv")
    save(pd.DataFrame(curves), "water_cover_curve.csv")
    save(pd.concat(yearly, ignore_index=True), "scenario_annual.csv")
    save(pd.concat(monthly, ignore_index=True), "scenario_monthly_water.csv")
    save(pd.DataFrame(sensitivity), "sensitivity.csv")
    (OUT/"model1_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False),encoding="utf-8")
    print(json.dumps(dict(station=fits["M0 (r,d)"],baselines=fits["baselines"],water=out["water"]),indent=2))

if __name__ == "__main__":
    main()
