# -*- coding: utf-8 -*-
"""
v7_missing.py —— 缺失值专项排查（《数据预处理》第 3 章）

五件事：
  1) 缺失图谱：按站点、按日历月、按连续缺失长度统计；
  2) 缺失机制：比较"缺失月"与"观测月"的气象分布（KS / Welch t 检验），判断是否 MCAR；
  3) 缺失成因：与沙尘事件频率、MODIS 合成期有效性的关系；
  4) 插补方法对比：5 种方法 × 2 种缺失机制（随机缺失 / 沙尘型缺失）的还原误差；
  5) 真实缺失月份的插补敏感度：气候态 vs 线性插值对覆盖度的影响。

输出：Results/v7/missing.json、tab_missing_detail.csv、tab_impute_compare.csv
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "Data", "v7", "processed")
RAW = os.path.join(BASE, "Data", "v7", "raw")
RES = os.path.join(BASE, "Results", "v7")
os.makedirs(RES, exist_ok=True)

CODES = ["YT", "MF", "QM", "RQ", "KEL", "YL", "ALE", "XT", "TZ"]
NAME = {"YT": "于田", "MF": "民丰", "QM": "且末", "RQ": "若羌", "KEL": "库尔勒",
        "YL": "尉犁", "ALE": "阿拉尔", "XT": "肖塘", "TZ": "塔中"}
TRAIN = (2015, 2022)
TARGET = "ndvi_mvc_qa"
RNG = np.random.default_rng(20261110)


def runs(mask: np.ndarray) -> list[int]:
    out, cur = [], 0
    for v in mask:
        if v:
            cur += 1
        elif cur:
            out.append(cur)
            cur = 0
    if cur:
        out.append(cur)
    return out


def impute(arr, mask, method, mon):
    """arr: 参照序列；mask: 被遮住的布尔数组；返回补齐后的序列"""
    x = arr.copy()
    x[mask] = np.nan
    s = pd.Series(x)
    if method == "mean":
        return s.fillna(np.nanmean(x)).to_numpy()
    if method == "median":
        return s.fillna(np.nanmedian(x)).to_numpy()
    if method == "linear":
        return s.interpolate(limit=3, limit_direction="both").to_numpy()
    if method == "clim":
        cl = {m: float(np.nanmean(x[mon == m])) for m in np.unique(mon)}
        out = x.copy()
        for i in np.where(mask)[0]:
            out[i] = cl[mon[i]]
        return pd.Series(out).interpolate(limit_direction="both").to_numpy()
    if method == "persistence":
        out = x.copy()
        for i in np.where(mask)[0]:
            j = i - 12
            out[i] = x[j] if j >= 0 and np.isfinite(x[j]) else np.nanmean(x)
        return pd.Series(out).interpolate(limit_direction="both").to_numpy()
    raise ValueError(method)


def main():
    p = pd.read_csv(os.path.join(OUT, "panel_monthly_raw.csv"), parse_dates=["date"])
    p = p.sort_values(["site", "date"]).reset_index(drop=True)
    if "P_mm" not in p and "PRECTOTCORR" in p:
        p["P_mm"] = p["PRECTOTCORR"] * p["days_in_month"]
    res: dict = {}

    # ---------------------------------------------------------------- 1 图谱
    miss_rows = []
    for c in CODES:
        s = p[p.site == c].sort_values("date")
        m = s[TARGET].isna().to_numpy()
        rl = runs(m)
        miss_rows.append({
            "site": c, "name": NAME[c], "n_months": int(len(s)), "n_missing": int(m.sum()),
            "missing_pct": round(100 * m.mean(), 2),
            "max_run": max(rl) if rl else 0,
            "n_runs": len(rl),
            "run_dist": {int(k): int(v) for k, v in
                         pd.Series(rl).value_counts().sort_index().items()} if rl else {},
            "first_missing": str(s.loc[m, "date"].min().date()) if m.any() else "",
            "last_missing": str(s.loc[m, "date"].max().date()) if m.any() else "",
        })
    pd.DataFrame(miss_rows).to_csv(os.path.join(RES, "tab_missing_detail.csv"),
                                   index=False, encoding="utf-8-sig")
    res["by_site"] = miss_rows

    mm = p.assign(missing=p[TARGET].isna())
    by_month = mm.groupby(mm["date"].dt.month)["missing"].agg(["sum", "mean"])
    res["by_calendar_month"] = {int(k): {"n_missing": int(v["sum"]),
                                         "pct": round(100 * float(v["mean"]), 2)}
                                for k, v in by_month.iterrows()}
    by_year = mm.groupby(mm["date"].dt.year)["missing"].agg(["sum", "mean"])
    res["by_year"] = {int(k): {"n_missing": int(v["sum"]), "pct": round(100 * float(v["mean"]), 2)}
                      for k, v in by_year.iterrows()}

    all_runs = []
    for c in CODES:
        all_runs += runs(p[p.site == c].sort_values("date")[TARGET].isna().to_numpy())
    res["run_length_dist"] = {int(k): int(v) for k, v in
                              pd.Series(all_runs).value_counts().sort_index().items()}
    res["overall"] = {"n_missing": int(p[TARGET].isna().sum()), "n_total": int(len(p)),
                      "pct": round(100 * float(p[TARGET].isna().mean()), 2),
                      "max_run": int(max(all_runs)) if all_runs else 0}

    # ---------------------------------------------------------------- 2 机制
    p["missing"] = p[TARGET].isna()
    tests = {}
    for v in ["WS10M_MAX", "T2M", "P_mm", "RH2M"]:
        a = p.loc[p.missing, v].dropna()
        b = p.loc[~p.missing, v].dropna()
        if len(a) < 5:
            continue
        ks = stats.ks_2samp(a, b)
        tt = stats.ttest_ind(a, b, equal_var=False)
        tests[v] = {"mean_missing": round(float(a.mean()), 3), "mean_obs": round(float(b.mean()), 3),
                    "ks_stat": round(float(ks.statistic), 3), "ks_p": f"{ks.pvalue:.3g}",
                    "t_p": f"{tt.pvalue:.3g}", "n_missing": int(len(a))}
    res["mcar_tests"] = tests

    if "dust_days_12" in p:
        res["corr_missing_dust12"] = round(float(np.corrcoef(
            p["missing"].astype(float), p["dust_days_12"].fillna(0))[0, 1]), 3)

    # ---------------------------------------------------------------- 3 成因
    comp = []
    for c in CODES:
        recs = json.load(open(os.path.join(RAW, f"modis_{c}_NDVI.json"), encoding="utf-8"))
        n_empty = sum(1 for r in recs if not r.get("data") or
                      sum(1 for v in r["data"] if v > -2900) == 0)
        comp.append({"site": c, "n_composites": len(recs), "n_all_invalid": n_empty})
    res["composite_level"] = comp

    # ---------------------------------------------------------------- 4 插补对比
    truth, dates = {}, {}
    for c in CODES:
        s = p[p.site == c].sort_values("date")
        # 参照序列：未做 QA 过滤的月最大合成反演的覆盖度（完整，且保留真实季节变差）
        truth[c] = np.clip((s["ndvi_mvc"].to_numpy(dtype=float) - 0.05) / 0.80, 0, 1) * 100
        dates[c] = s["date"].to_numpy()

    mcar = {c: (RNG.random(len(truth[c])) < 0.10) for c in CODES}
    dust = {}
    for c in CODES:
        s = p[p.site == c].sort_values("date")
        thr = np.nanpercentile(s["WS10M_MAX"], 90)
        dust[c] = (s["WS10M_MAX"].to_numpy() >= thr)

    methods = ["mean", "median", "linear", "clim", "persistence"]
    out_rows = []
    for scheme, masks in (("MCAR_10pct", mcar), ("dust_10pct", dust)):
        for meth in methods:
            errs = []
            for c in CODES:
                mon = pd.DatetimeIndex(dates[c]).month
                pred = impute(truth[c], masks[c], meth, mon)
                errs.append(pred[masks[c]] - truth[c][masks[c]])
            e = np.concatenate(errs)
            out_rows.append({"method": meth, "scheme": scheme,
                             "RMSE_pp": round(float(np.sqrt(np.mean(e ** 2))), 3),
                             "MAE_pp": round(float(np.mean(np.abs(e))), 3),
                             "bias_pp": round(float(np.mean(e)), 3), "n": int(e.size)})
    res["impute_compare"] = out_rows
    pd.DataFrame(out_rows).to_csv(os.path.join(RES, "tab_impute_compare.csv"),
                                  index=False, encoding="utf-8-sig")

    # ---------------------------------------------------------------- 5 真实缺失敏感度
    sens = []
    for c in CODES:
        s = p[p.site == c].sort_values("date")
        v = s[TARGET].to_numpy(dtype=float)
        mon = s["date"].dt.month.to_numpy()
        yr = s["date"].dt.year.to_numpy()
        miss = ~np.isfinite(v)
        if not miss.any():
            continue
        lin = pd.Series(v).interpolate(limit=2, limit_direction="both").to_numpy()
        cl = {}
        for m in np.unique(mon):
            sel = (mon == m) & (yr <= TRAIN[1]) & np.isfinite(v)
            cl[m] = float(np.nanmean(v[sel])) if sel.any() else float(np.nanmean(v))
        cli = v.copy()
        cli[miss] = [cl[mon[i]] for i in np.where(miss)[0]]
        cli = pd.Series(cli).interpolate(limit_direction="both").to_numpy()
        for y in np.unique(yr):
            sel = (yr == y) & miss
            if not sel.any():
                continue
            sens.append({"site": c, "year": int(y), "n_missing": int(sel.sum()),
                         "diff_pp": round(float(np.nanmean(cli[sel] - lin[sel])), 3)})
    d = np.array([x["diff_pp"] for x in sens])
    res["real_missing_sensitivity"] = sens
    res["real_missing_sensitivity_summary"] = {
        "n_site_years": int(len(d)),
        "mean_abs_diff_pp": round(float(np.mean(np.abs(d))), 3) if len(d) else None,
        "max_abs_diff_pp": round(float(np.max(np.abs(d))), 3) if len(d) else None}

    with open(os.path.join(RES, "missing.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1,
                  default=lambda o: int(o) if isinstance(o, np.integer) else float(o))

    print(json.dumps(res["overall"], ensure_ascii=False))
    print("按日历月：", json.dumps(res["by_calendar_month"], ensure_ascii=False))
    print("连续长度：", json.dumps(res["run_length_dist"], ensure_ascii=False))
    print("敏感度：", json.dumps(res["real_missing_sensitivity_summary"], ensure_ascii=False))
    print(pd.DataFrame(out_rows).to_string(index=False))


if __name__ == "__main__":
    main()
