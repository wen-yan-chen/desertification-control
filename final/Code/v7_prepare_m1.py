"""Build observed-only M1 inputs from replayed public responses. No interpolation.

Retains v7 panel as a reference snapshot; writes Data/v7/m1_audited only.
"""
import hashlib
import json
import numpy as np
import pandas as pd
from v7_replay_m1 import ROOT, CACHE

OUT = ROOT / "Data/v7/m1_audited"
SITES = ["YT", "MF", "QM", "RQ", "KEL", "YL", "ALE", "XT", "TZ"]

def pixel_mean(ndvi, qa, minimum_fraction=0.5):
    a, q = np.asarray(ndvi, float), np.asarray(qa, float)
    if a.shape != q.shape or a.size == 0:
        raise ValueError("NDVI and QA pixels must align")
    good = (a >= -2000) & (a <= 10000) & np.isin(q, [0, 1])
    n = int(good.sum())
    return (float(a[good].mean() * 1e-4) if n >= np.ceil(a.size * minimum_fraction) else np.nan), n

def records(site, band):
    found = {}
    for path in sorted((CACHE / "_cache/modis" / site).glob(f"250m_16_days_{band}_A*161.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for row in data["subset"]:
            row["_grid"] = tuple(data[k] for k in ("nrows", "ncols", "xllcorner", "yllcorner", "cellsize"))
            key = row["modis_date"]
            if key in found and found[key]["data"] != row["data"]:
                raise ValueError(f"Conflicting MODIS duplicate: {site} {key}")
            found[key] = row
    expected = {f"A{year}{day:03d}" for year in range(2015,2026) for day in range(161,306,16)}
    if set(found) != expected:
        raise ValueError(f"Incomplete M1 growing-season series: {site} {band}")
    return found

def main():
    OUT.mkdir(exist_ok=True)
    replay = json.loads((OUT / "replay_manifest.json").read_text())
    if replay["errors"]:
        raise ValueError("Raw replay incomplete")
    for rec in replay["requests"]:
        if hashlib.sha256((CACHE / rec["file"]).read_bytes()).hexdigest() != rec["replay_sha256"]:
            raise ValueError(f"Cache hash changed: {rec['file']}")
    old = pd.read_csv(ROOT / "Data/v7/processed/panel_monthly_clean.csv", parse_dates=["date"])
    rows, composite_rows, diagnostics = [], [], []
    for site in SITES:
        nd, qa = records(site, "NDVI"), records(site, "pixel_reliability")
        if nd.keys() != qa.keys():
            raise ValueError("NDVI/QA composite dates differ")
        for key in sorted(nd):
            r, q = nd[key], qa[key]
            if r["calendar_date"] != q["calendar_date"] or r["_grid"] != q["_grid"]:
                raise ValueError("NDVI/QA spatial or temporal alignment mismatch")
            v, n = pixel_mean(r["data"], q["data"])
            v75, _ = pixel_mean(r["data"], q["data"], 0.75)
            raw_values = np.asarray(r["data"], float)
            valid_raw = raw_values[(raw_values >= -2000) & (raw_values <= 10000)]
            composite_rows.append(dict(site=site, date=r["calendar_date"], ndvi_qa=v,
                ndvi_qa75=v75, ndvi_unqa=float(valid_raw.mean()*1e-4) if len(valid_raw) else np.nan,
                n_good=n, n_pixels=len(r["data"])))
        raw = json.loads((CACHE / f"power_daily_{site}.json").read_text())
        daily = pd.DataFrame(raw["properties"]["parameter"]).replace(-999, np.nan)
        daily.index = pd.to_datetime(daily.index, format="%Y%m%d")
        if len(daily) != 4018 or daily.isna().any().any():
            raise ValueError(f"Incomplete daily POWER: {site}")
        # Nonlinear transport proxy first, aggregate second. Not measured sand flux.
        u = daily.WS10M_MAX
        daily["q_proxy"] = u ** 2 * np.maximum(u - 5.0, 0)
        baseline = daily.loc[daily.index.year <= 2022, "q_proxy"].mean()
        if baseline <= 0:
            raise ValueError(f"Zero wind proxy normalization: {site}")
        daily["E_daily"] = daily.q_proxy / baseline
        mon = daily.resample("MS").agg(E=("E_daily", "mean"),
            Tmax_daily_mean=("T2M_MAX", "mean"), Tmin_daily_mean=("T2M_MIN", "mean"),
            daily_windmax_monthmean=("WS10M_MAX", "mean"))
        mon["site"] = site
        mon.index.name = "date"
        rows.append(mon.reset_index())
    comp = pd.DataFrame(composite_rows)
    comp["date"] = pd.to_datetime(comp.date)
    comp = comp[comp.date.dt.month.between(6,9)].copy()
    comp["composite_date"] = comp.date
    comp["date"] = comp.date.dt.to_period("M").dt.to_timestamp()
    monthly = comp.groupby(["site", "date"]).agg(
        ndvi_mvc_qa=("ndvi_qa", "max"), ndvi_mvc_qa75=("ndvi_qa75", "max"),
        ndvi_unqa_replayed=("ndvi_unqa", "max"),
        n_comp_ok=("ndvi_qa", "count"), valid_pixel_fraction_mean=("n_good", lambda x: x.mean()/81))
    panel = old.drop(columns=["E", "ndvi_mvc_qa", "n_comp_ok"], errors="ignore").merge(
        pd.concat(rows), on=["site", "date"], validate="one_to_one").merge(
        monthly, on=["site", "date"], how="left", validate="one_to_one")
    panel["V_pct"] = ((panel.ndvi_mvc_qa - 0.05) / 0.8).clip(0, 1) * 100
    panel["V_pct_qa75"] = ((panel.ndvi_mvc_qa75 - 0.05) / 0.8).clip(0, 1) * 100
    unqa_difference = (panel.ndvi_unqa_replayed-panel.ndvi_mvc).abs().max()
    # Explicitly exclude flawed Hargreaves/extrema and all imputed legacy NDVI fields.
    columns = ["site", "date", "T2M", "P_mm", "GWETROOT", "W", "era_et0_mm", "era_T",
               "era_P_mm", "era_sm_root", "E", "ndvi_mvc_qa", "V_pct", "V_pct_qa75",
               "n_comp_ok", "valid_pixel_fraction_mean", "Tmax_daily_mean", "Tmin_daily_mean"]
    panel = panel[columns].sort_values(["site", "date"]).reset_index(drop=True)
    assert len(panel) == 1188 and not panel.duplicated(["site", "date"]).any()
    for site, g in panel.groupby("site"):
        prev = old[old.site == site].set_index("date")
        joined = g.set_index("date").join(prev[["V_pct", "WS10M_MAX"]], rsuffix="_old")
        train = g[g.date.dt.year <= 2022]
        summer = train[train.date.dt.month.between(6, 9)]
        diagnostics.append(dict(site=site, missing_JunSep_months=int(g.loc[g.date.dt.month.between(6,9),'V_pct'].isna().sum()),
            months_outside_M1_season=int((~g.date.dt.month.between(6,9)).sum()),
            train_summer_missing_fraction=float(summer.V_pct.isna().mean()),
            V_mean_abs_change_pp=float((joined.V_pct-joined.V_pct_old).abs().mean()),
            monthly_WSMAX_mean=float(prev.WS10M_MAX.mean())))
    panel.to_csv(OUT / "panel_m1.csv", index=False, float_format="%.10g")
    comp.to_csv(OUT / "modis_composite_qc.csv", index=False, float_format="%.10g")
    pd.DataFrame(diagnostics).to_csv(OUT / "audit_by_site.csv", index=False)
    report = dict(rows=len(panel), expected_JunSep_months=396,
        missing_JunSep_V=int(panel.loc[panel.date.dt.month.between(6,9),'V_pct'].isna().sum()),
        nonseason_V_intentionally_absent=792,
        raw_replay_exact_hashes=sum(x["exact_match"] for x in replay["requests"]),
        raw_replay_responses=len(replay["requests"]),
        unqa_replay_max_abs_difference_from_old_panel=float(unqa_difference),
        qa="pixel reliability 0 or 1, >=50% valid pixels per composite; 75% sensitivity",
        interpolation="none; missing targets never scored; only Jun-Sep downloaded for M1",
        era_source="existing v7 Open-Meteo archive, models unspecified; do not label pure ERA5",
        soil_moisture_status="reanalysis context only, not observed plantation available water",
        legacy_panel_sha256=hashlib.sha256((ROOT/'Data/v7/processed/panel_monthly_clean.csv').read_bytes()).hexdigest())
    (OUT / "audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    windows = pd.read_csv(ROOT / 'Data/v7/section_modis/windows.csv')
    line = windows[windows.window.isin(['CON1','CON2','CON3','CON4'])].sort_values('window')
    coords = np.radians(line[['lat','lon']].to_numpy())
    delta = np.diff(coords,axis=0)
    hav = np.sin(delta[:,0]/2)**2 + np.cos(coords[:-1,0])*np.cos(coords[1:,0])*np.sin(delta[:,1]/2)**2
    length = float((2*6371.0088*np.arcsin(np.sqrt(hav))).sum())
    section = dict(name='Yutian-Minfeng study transect', centerline=line[['window','lat','lon']].to_dict('records'),
        polyline_length_km=length, assumed_width_km=1.0,
        status='representative research scenario, not a surveyed engineering boundary',
        area_usage='do not infer actual treated area or project water totals from this line')
    (OUT/'section_definition.json').write_text(json.dumps(section,indent=2),encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
