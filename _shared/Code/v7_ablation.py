# -*- coding: utf-8 -*-
"""
v7_ablation.py —— 预处理方案消融实验

目的：把"数据预处理对建模结果的影响"从定性说法变成可复算的数字。
做法：构造 5 套递进的预处理方案 P0→P4，对同一份原始数据分别处理，
      再用 model_v6 给出的三问公式（任务一标定、任务二动态规划、任务三吸收马尔可夫链）
      各跑一遍，比较输出的差异。

P0 原始直用      不换单位、不做质控、不插补、用全样本统计量
P1 量纲/口径统一  mm/d→mm/月；km/h→m/s；m³/m³→0-1 归一；剔除年度汇总行
P2 +缺失插补      站内线性(≤2 月)+同月气候态
P3 +遥感质控      MODIS QA 过滤 + 月最大合成 + 物理范围检查
P4 +训练期隔离    所有统计量只在 2015—2022 拟合，测试期 2023—2025 不参与

评价：
  任务一 训练期 R²、一年外推 RMSE、标定参数
  任务二 基准情景 NPV（万元）
  任务三 λ=0.3 时 30 年内退化概率
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "Data", "v7", "processed")
RES = os.path.join(BASE, "Results", "v7")
os.makedirs(RES, exist_ok=True)

PNL = os.path.join(OUT, "panel_monthly_raw.csv")
CODES = ["YT", "MF", "QM", "RQ", "KEL", "YL", "ALE", "XT", "TZ"]
TRAIN = (2015, 2022)
TEST = (2023, 2025)
Z0, KAPPA, C_L, RHO, G = 0.001, 0.40, 6.7, 1.225, 9.81
U_T = 5.0
RNG = np.random.default_rng(20261110)


# --------------------------------------------------------------- 任务一：标定
def sim(theta, V0, W, E, T, K):
    r, d, k, eta = theta
    n = len(V0)
    out = np.empty(n)
    out[0] = V0[0]
    for t in range(n - 1):
        f = min(1.0, max(0.0, (T[t] - 5.0) / 20.0))
        Eeff = E[t] * (1 - eta * out[t] / K)
        out[t + 1] = (out[t] + r * out[t] * (1 - out[t] / K) * W[t] * f
                      - d * out[t] - k * Eeff * out[t])
        out[t + 1] = max(out[t + 1], 0.0)
    return out


def sse(theta, V, W, E, T, K):
    vm = sim(theta, V, W, E, T, K)
    return float(np.mean((vm[1:] - V[1:]) ** 2))


BOUNDS = np.array([[0.02, 1.5], [0.0, 0.3], [0.0, 0.5], [0.0, 0.95]])


def fit(V, W, E, T, K, n_start=25, seed=0):
    rng = np.random.default_rng(seed)
    best, best_f = None, np.inf
    steps = [0.30, 0.15, 0.08, 0.04, 0.02, 0.01, 0.008]
    for _ in range(n_start):
        th = rng.uniform(BOUNDS[:, 0], BOUNDS[:, 1])
        f = sse(th, V, W, E, T, K)
        for st in steps:
            improved = True
            it = 0
            while improved and it < 60:
                improved = False
                it += 1
                for j in range(4):
                    for sgn in (1, -1):
                        cand = th.copy()
                        cand[j] = np.clip(cand[j] + sgn * st, *BOUNDS[j])
                        fc = sse(cand, V, W, E, T, K)
                        if fc < f - 1e-12:
                            th, f, improved = cand, fc, True
        if f < best_f:
            best, best_f = th, f
    return best, best_f


def r2(y, yhat):
    y, yhat = np.asarray(y, float), np.asarray(yhat, float)
    ss = np.sum((y - y.mean()) ** 2)
    return float(1 - np.sum((y - yhat) ** 2) / ss) if ss > 0 else np.nan


# --------------------------------------------------------------- 任务二：DP
def steady_v(params, K, I):
    r, d, k, eta = params
    Ks = 0.45 + 0.55 * I / 60.0
    num = r * Ks - d - k
    den = r * Ks - k * eta
    if den <= 1e-9:
        return 0.0
    x = num / den
    return float(np.clip(x, 0, 1) * K)


def task2_npv(params, K, scen=None):
    s = {"cb": 2.0, "cm": 0.12, "ppv": 8.0, "pe": 0.15, "cw": 1.0,
         "B": 4000.0, "Wmax": 500.0, "Amax": 20.0, "delta": 0.94, "T": 15}
    s.update(scen or {})
    A = np.linspace(0, s["Amax"], 81)
    a_opts = np.array([0, 0.5, 1.0, 1.5, 2.0])
    I_opts = np.array([0, 20, 40, 60])
    s_opts = np.array([0.2, 0.3, 0.4, 0.5])
    Vstar = {I: steady_v(params, K, I) for I in I_opts}
    J = np.zeros_like(A)
    for t in range(s["T"] - 1, -1, -1):
        Jn = np.full_like(A, -1e18)
        for i, At in enumerate(A):
            for a in a_opts:
                if At + a > s["Amax"] + 1e-9:
                    continue
                if s["cb"] * 1000 * a + s["cm"] * 1000 * At > s["B"]:
                    continue
                for I in I_opts:
                    vol = I * a / 1000.0
                    if vol > s["Wmax"] + 1e-9:
                        continue
                    if s["cw"] * vol + s["cb"] * 1000 * a + s["cm"] * 1000 * At > s["B"]:
                        continue
                    for sv in s_opts:
                        rew = (s["ppv"] * sv * 1000 * a
                               + s["pe"] * (Vstar[I] / K) * 1000 * At
                               - s["cb"] * 1000 * a - s["cm"] * 1000 * At
                               - s["cw"] * vol)
                        j2 = A.searchsorted(At + a)
                        val = rew + s["delta"] * J[min(j2, len(A) - 1)]
                        if val > Jn[i]:
                            Jn[i] = val
        J = Jn
    return float(J[0])


# --------------------------------------------------------------- 任务三：吸收链
def task3_pdeg(params, K, lam=0.30, horizon=30, n=120):
    r, d, k, eta = params
    Vmax = 1.5 * K
    st = np.linspace(0, Vmax, n)
    crit = 0.3 * K
    w_bar, t_bar = 0.55, 12.0
    f = min(1.0, max(0.0, (t_bar - 5) / 20))
    idx = lambda v: int(np.clip(np.searchsorted(st, v), 0, n - 1))
    absorb = st < crit
    uq = np.linspace(0.2, 0.55, 15)
    P = np.zeros((n, n))
    for i, v in enumerate(st):
        if absorb[i]:
            P[i, i] = 1.0
            continue
        vd = v + r * v * (1 - v / K) * w_bar * f - d * v - k * 1.0 * (1 - eta * v / K) * v
        P[i, idx(max(vd, 0))] += (1 - lam)
        for u in uq:
            P[i, idx(max(v * (1 - u), 0))] += lam / len(uq)
    keep = ~absorb
    Q = P[np.ix_(keep, keep)]
    p0 = np.zeros(len(st))
    p0[idx(K)] = 1.0
    p0 = p0[keep]
    p = p0 @ np.linalg.matrix_power(Q, horizon)
    return float(1 - p.sum())


# --------------------------------------------------------------- 面板构造
def annual(df, cols):
    d = df.copy()
    d["year"] = d["date"].dt.year
    g = d.groupby(["site", "year"])[list(cols)].mean()
    return g.reset_index()


def erosion(u, base):
    us = KAPPA * u / np.log(10 / Z0)
    ust = KAPPA * U_T / np.log(10 / Z0)
    q = np.clip(C_L * RHO / G * us ** 2 * (us - ust), 0, None)
    return q / base if base > 0 else q


def build(pipeline: str, raw: pd.DataFrame):
    """返回 {site: DataFrame[year, V, W, E, T]}"""
    x = raw.copy()
    last_train = x["date"].dt.year <= TRAIN[1]
    full = np.ones(len(x), bool)

    # ---------- 水分状态 W
    if pipeline == "P0":
        x["W_use"] = x["era_sm_root"]                       # m³/m³，未归一
    elif pipeline == "P1":
        lo, hi = np.nanpercentile(x["GWETROOT"], [5, 95])   # 全样本 → 泄漏
        x["W_use"] = np.clip((x["GWETROOT"] - lo) / (hi - lo), 0, 1)
    else:
        lo, hi = np.nanpercentile(x.loc[last_train, "GWETROOT"], [5, 95]) if pipeline == "P4" \
            else np.nanpercentile(x["GWETROOT"], [5, 95])
        x["W_use"] = np.clip((x["GWETROOT"] - lo) / (hi - lo), 0, 1)

    # ---------- 侵蚀指数 E
    if pipeline == "P0":
        # 典型错误：把 Open-Meteo/ERA5 交付的 km/h 直接当 m/s 代入 Lettau 公式
        u_bad = x["era_ws_max"] * 3.6   # ERA5 交付 km/h
        x["E_use"] = erosion(u_bad, np.nanmean(erosion(u_bad, 1.0)))
    else:
        x["E_use"] = erosion(x["WS10M_MAX"], np.nanmean(erosion(x["WS10M_MAX"], 1.0)))

    # ---------- 气温
    x["T_use"] = x["era_T"] if pipeline == "P0" else x["T2M"]

    # ---------- 植被覆盖度 V
    if pipeline in ("P0", "P1", "P2"):
        x["V_use"] = x["ndvi_mean"] * 100.0                 # 未做 QA / MVC / 像元二分
    else:
        x["V_use"] = np.clip((x["ndvi_mvc_qa"] - 0.05) / 0.80, 0, 1) * 100.0

    # ---------- 缺失处理
    if pipeline in ("P0", "P1"):
        pass                                                # 不插补：年度均值按可用月份
    else:
        for c in ("W_use", "E_use", "T_use", "V_use"):
            x[c] = (x.groupby("site", group_keys=False)[c]
                    .apply(lambda s: s.interpolate(limit=2, limit_direction="both")))
        if pipeline == "P4":
            clim = (x[x["date"].dt.year.between(*TRAIN)]
                    .groupby(["site", x["date"].dt.month])[["W_use", "E_use", "T_use", "V_use"]]
                    .transform("mean"))
        else:
            clim = (x.groupby(["site", x["date"].dt.month])[["W_use", "E_use", "T_use", "V_use"]]
                    .transform("mean"))
        for c in ("W_use", "E_use", "T_use", "V_use"):
            x[c] = x[c].fillna(clim[c])

    # ---------- 物理范围检查（仅 P3/P4）
    if pipeline in ("P3", "P4"):
        x.loc[(x["V_use"] < 0) | (x["V_use"] > 100), "V_use"] = np.nan
        x.loc[(x["W_use"] < 0) | (x["W_use"] > 1), "W_use"] = np.nan
        x.loc[x["E_use"] > 50, "E_use"] = np.nan

    out = annual(x, ["V_use", "W_use", "E_use", "T_use"])
    out = out.rename(columns={"V_use": "V", "W_use": "W", "E_use": "E", "T_use": "T"})
    res = {}
    for c in CODES:
        s = out[out["site"] == c].sort_values("year")
        res[c] = s.dropna(subset=["V", "W", "E", "T"]).reset_index(drop=True)
    return res


def evaluate(pipeline: str, raw: pd.DataFrame, data=None):
    if data is None:
        data = build(pipeline, raw)
    rows = []
    for c in CODES:
        s = data[c]
        tr = s[s["year"].between(*TRAIN)]
        te = s[s["year"].between(*TEST)]
        if len(tr) < 5:
            continue
        V, W, E, T = (tr[k].to_numpy() for k in ("V", "W", "E", "T"))
        K = 1.15 * np.percentile(V, 95)
        theta, f = fit(V, W, E, T, K, n_start=25, seed=hash(c) % 1000)
        Vm = sim(theta, V, W, E, T, K)
        rr = r2(V[1:], Vm[1:])
        # 一年外推：以当年实测为初值，只推一年
        errs = []
        for _, row in te.iterrows():
            y = int(row["year"])
            prev = s[s["year"] == y - 1]
            if len(prev) == 0:
                continue
            v0 = float(prev["V"].iloc[0])
            pred = sim(theta, np.array([v0, v0]), np.array([row["W"], row["W"]]),
                       np.array([row["E"], row["E"]]), np.array([row["T"], row["T"]]), K)[1]
            errs.append(pred - float(row["V"]))
        rows.append({"pipeline": pipeline, "site": c, "K": K, "Vstar": steady_v(theta, K, 60),
                     "r": theta[0], "d": theta[1], "k": theta[2], "eta": theta[3],
                     "R2_train": rr, "RMSE_one_year": float(np.sqrt(np.mean(np.square(errs)))) if errs else np.nan,
                     "NPV": task2_npv(theta, K),
                     "P_deg_30y_lam03": task3_pdeg(theta, K)})
    return pd.DataFrame(rows)


def main():
    raw = pd.read_csv(PNL, parse_dates=["date"])
    # 统一列名（raw 面板里可能缺 qa 列）
    if "ndvi_mvc_qa" not in raw:
        raw["ndvi_mvc_qa"] = raw["ndvi_mvc"]

    print("== 消融：5 套预处理方案 ==", flush=True)
    data_all = {p: build(p, raw) for p in ["P0", "P1", "P2", "P3", "P4"]}
    ref = data_all["P4"]
    frames, verr = [], []
    for p in ["P0", "P1", "P2", "P3", "P4"]:
        df = evaluate(p, raw, data_all[p])
        frames.append(df)
        # 相对"全流程"的覆盖度重建误差（这才是预处理直接造成的状态偏差）
        errs = []
        for c in CODES:
            a = data_all[p][c].set_index("year")["V"]
            b = ref[c].set_index("year")["V"]
            j = pd.concat([a, b], axis=1, keys=["a", "b"]).dropna()
            if len(j):
                errs.append((j["a"] - j["b"]).to_numpy())
        e = np.concatenate(errs) if errs else np.array([np.nan])
        verr.append({"pipeline": p, "V_MAE_pp": float(np.mean(np.abs(e))),
                     "V_RMSE_pp": float(np.sqrt(np.mean(e ** 2))),
                     "V_max_pp": float(np.max(np.abs(e))),
                     "V_bias_pp": float(np.mean(e))})
        print(f"  {p}: R²中位={df['R2_train'].median():.3f}  "
              f"一年RMSE中位={df['RMSE_one_year'].median():.2f}  "
              f"V偏差MAE={verr[-1]['V_MAE_pp']:.2f}pp  "
              f"NPV中位={df['NPV'].median():.0f}  "
              f"退化概率中位={df['P_deg_30y_lam03'].median():.3f}", flush=True)
    allr = pd.concat(frames, ignore_index=True)
    allr["hit_bound"] = ((allr["r"] >= 1.49) | (allr["d"] <= 1e-6)
                         | (allr["k"] <= 1e-6) | (allr["eta"] >= 0.949)).astype(int)
    allr.to_csv(os.path.join(RES, "tab_ablation_by_site.csv"), index=False, encoding="utf-8-sig")

    sum2 = allr.groupby("pipeline").agg(hit_bound_frac=("hit_bound", "mean"),
                                        Vstar_median=("Vstar", "median")).reset_index()
    summ = (allr.groupby("pipeline")
            .agg(R2_train_median=("R2_train", "median"),
                 R2_train_mean=("R2_train", "mean"),
                 RMSE_one_year_median=("RMSE_one_year", "median"),
                 r_median=("r", "median"), d_median=("d", "median"),
                 k_median=("k", "median"), eta_median=("eta", "median"),
                 K_median=("K", "median"),
                 NPV_median=("NPV", "median"),
                 Pdeg_median=("P_deg_30y_lam03", "median"))
            .reindex(["P0", "P1", "P2", "P3", "P4"]).reset_index()
            .merge(pd.DataFrame(verr), on="pipeline")
            .merge(sum2, on="pipeline"))
    refrow = summ[summ["pipeline"] == "P4"].iloc[0]
    for c in ["R2_train_median", "RMSE_one_year_median", "NPV_median", "Pdeg_median",
              "r_median", "k_median", "eta_median", "Vstar_median"]:
        summ[c + "_vs_P4"] = (summ[c] / refrow[c] - 1) if refrow[c] not in (0, np.nan) else np.nan
    summ.to_csv(os.path.join(RES, "tab_ablation_summary.csv"), index=False, encoding="utf-8-sig")

    with open(os.path.join(RES, "ablation.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": summ.round(4).to_dict("records"),
                   "by_site": allr.round(4).to_dict("records"),
                   "note": "任务二/三按 model_v6 §4、§5 公式复算，仅替换输入数据与预处理方案"},
                  f, ensure_ascii=False, indent=1)
    print(summ.round(3).to_string(index=False), flush=True)
    print("完成 ablation.json / tab_ablation_*.csv", flush=True)


if __name__ == "__main__":
    main()



