# -*- coding: utf-8 -*-
"""
modeling_v2.py —— 修订版建模（2026-11-09 审计后重写）

任务一（耦合动力学，月步长）
    dV/dt = g·V·(1 − V/V_cap)·W^a·f(T) − m·V − k·E·V ,   W∈[0,1] 为根区湿度（观测）,
    E 为无量纲侵蚀指数，k≥0 强制“风蚀只减不增”。
    · 标定：约束最小二乘（g,m,k≥0，a=1）在**一步预测**残差上最小化，仅用训练期；
    · 验证：测试期一步预测 R²，以及 h=1/3/6/12 的滚动多步技能衰减；
    · 结论：多步自由推进不具备显著技能时，长期推演只做情景，不做点预测。

任务二（情景动态规划）：稳态覆盖度由任务一方程解析求得
    V_eq = V_cap·[1 − (m + kE)/(g·W_eff)]，灌溉经有效水容量 AWC 换算进 W_eff。
    目标函数、约束、情景参数显式列出；结果以区间/敏感性给出。

任务三（韧性）：泊松事件强度 λ 由实测 E 的超额频率估计；冲击恢复按“回到冲击前 90%”
    定义并右删失；2026—2050 情景含显式气候增量。
"""
import json
import os

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE, "Data", "processed")
RES = os.path.join(BASE, "Results")
FIG = os.path.join(BASE, "Figures")
os.makedirs(RES, exist_ok=True); os.makedirs(FIG, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.25
plt.rcParams["figure.dpi"] = 200
plt.rcParams["savefig.dpi"] = 200

ZR, TH_FC, TH_WP = 0.6, 0.10, 0.03
AWC = 1000 * ZR * (TH_FC - TH_WP)            # 有效水容量 mm ≈ 42


def fT(T):
    return np.clip((T - 5.0) / 20.0, 0.0, 1.0)


def w_norm(gwet, lo, hi):
    return np.clip((gwet - lo) / max(hi - lo, 1e-6), 0.0, 1.0)


def fit_station(df, Vcap, seed=0, restarts=12):
    """约束标定（平衡态锚定）：只自由拟合 g, k≥0；衰亡率 m 由
         m = g·W̄·f(T̄)·(1 − V̄/V_cap) − k·Ē  反解，使模型长期平衡态等于实测均值 V̄。
       目标函数仍为一步预测均方误差（只用训练期）。"""
    rng = np.random.default_rng(seed)
    V = df["FVC_fixed"].values.astype(float)
    W = df["W_norm"].values.astype(float)
    T = df["T2M"].values.astype(float)
    E = df["E_index"].values.astype(float)
    Wb, Tb, Eb, Vb = float(W.mean()), float(T.mean()), float(E.mean()), float(V.mean())
    mo = df["月份"].str[5:].astype(int).values
    Wc = {m: float(W[mo == m].mean()) for m in range(1, 13)}
    Tc = {m: float(T[mo == m].mean()) for m in range(1, 13)}
    WfT_bar = float(np.mean([Wc[m] * fT(Tc[m]) for m in range(1, 13)]))
    y = np.diff(V)
    g_lo, g_hi = 0.02, 3.0
    k_lo, k_hi = 0.0, 0.30

    def m_of(g, k):
        m = g * WfT_bar * (1 - Vb / Vcap) - k * Eb
        return max(m, 0.0)

    def f1(par):
        g, k = par
        m = m_of(g, k)
        pred = (g * V[:-1] * (1 - V[:-1] / Vcap) * W[:-1] * fT(T[:-1])
                - m * V[:-1] - k * E[:-1] * V[:-1])
        return float(np.mean((pred - y) ** 2))

    best = (np.array([0.3, 0.02]), np.inf)
    for _ in range(restarts):
        q = np.array([g_lo + rng.random() * (g_hi - g_lo), k_lo + rng.random() * (k_hi - k_lo)])
        f = f1(q)
        for step in (0.2, 0.08, 0.03, 0.01, 0.004):
            for _it in range(10):
                imp = False
                for j, (lo, hi) in enumerate([(g_lo, g_hi), (k_lo, k_hi)]):
                    for sg in (1, -1):
                        qq = q.copy()
                        qq[j] = np.clip(q[j] + sg * step * (hi - lo), lo, hi)
                        f2 = f1(qq)
                        if f2 < f * (1 - 1e-5):
                            q, f, imp = qq, f2, True
                if not imp:
                    break
        if f < best[1]:
            best = (q, f)
    g, k = best[0]
    return np.array([g, m_of(g, k), k]), {"WfT_bar": WfT_bar, "Wb": Wb, "Tb": Tb,
                                          "Eb": Eb, "Vb": Vb}


def v_next(V, W, T, E, p, Vcap):
    g, m, k = p
    return float(np.clip(V + g * V * (1 - V / Vcap) * W * fT(T) - m * V - k * E * V,
                         0.02, 100.0))


def r2(o, s):
    o, s = np.asarray(o, float), np.asarray(s, float)
    return 1 - float(np.sum((o - s) ** 2)) / max(float(np.sum((o - o.mean()) ** 2)), 1e-9)


def skill_decay(df, p, Vcap, horizons=(1, 3, 6, 12)):
    """滚动起点自由推进 h 步，返回各 h 的 RMSE 与季节基线 RMSE"""
    V = df["FVC_fixed"].values.astype(float)
    W = df["W_norm"].values.astype(float)
    T = df["T2M"].values.astype(float)
    E = df["E_index"].values.astype(float)
    out = {}
    for h in horizons:
        err, errb = [], []
        for i in range(len(df) - h):
            v = V[i]
            for t in range(i, i + h):
                v = v_next(v, W[t], T[t], E[t], p, Vcap)
            err.append((v - V[i + h]) ** 2)
            errb.append((V[i] - V[i + h]) ** 2)      # 持续性基线
        out[h] = {"rmse": float(np.sqrt(np.mean(err))),
                  "rmse_persist": float(np.sqrt(np.mean(errb)))}
    return out


def v_eq(E, p, Vcap, W_ratio, WfT_bar):
    """W_ratio = W_eff / W_bar；有效生长项用月气候态乘积 WfT_bar"""
    g, m, k = p
    s = (m + k * E) / max(g * WfT_bar * W_ratio, 1e-9)
    return float(np.clip(Vcap * (1 - s), 0.0, Vcap))


SCEN = dict(A_pot=40.0, T=15, build=2.0, maint=0.12, pv_rev=8.0, pv_share=0.30,
            eco=1.2, water_cost=0.5, B=4000.0, W_max=500.0, disc=0.94, beta=0.5)


def dp_plan(p, Vcap, Wbar, Tbar, scen=SCEN, controls=(0.0, 0.5, 1.0, 1.5, 2.0), WfT_bar=None):
    A_pot, T = scen["A_pot"], scen["T"]
    nS = 81
    A = np.linspace(0, A_pot, nS); dA = A[1] - A[0]

    def reward(A_new, a):
        if a <= 0:
            return 0.0
        a_hm = a * 1000.0
        E = max(1.0 * (1 - scen["beta"] * A_new / A_pot), 0.10)
        I_mm = min(scen["W_max"] / max(a, 1e-9) * 1e4 / a_hm, 60.0)
        W_eff = float(np.clip(Wbar + I_mm / AWC, 0.0, 1.0))
        Veq = v_eq(E, p, Vcap, W_eff / max(Wbar, 1e-6), WfT_bar)
        return (scen["pv_rev"] * scen["pv_share"] * a_hm
                + scen["eco"] * (Veq / max(Vcap, 1e-6)) * a_hm
                - scen["build"] * a_hm - scen["maint"] * A_new * 1000.0
                - scen["water_cost"] * (I_mm / 100.0) * a_hm)

    Vf = np.zeros((T + 1, nS)); pol = np.zeros((T, nS), dtype=int)
    for t in range(T - 1, -1, -1):
        for i in range(nS):
            best, bi = -1e18, 0
            for ci, a in enumerate(controls):
                if scen["build"] * a * 1000.0 > scen["B"]:
                    continue
                j = min(int(round((A[i] + a) / dA)), nS - 1)
                val = reward(A[j], a) + scen["disc"] * Vf[t + 1, j]
                if val > best:
                    best, bi = val, ci
            Vf[t, i], pol[t, i] = best, bi
    i, path = 0, []
    for t in range(T):
        a = controls[pol[t, i]]
        j = min(int(round((A[i] + a) / dA)), nS - 1)
        E = max(1.0 * (1 - scen["beta"] * A[j] / A_pot), 0.10)
        I_mm = min(scen["W_max"] / max(a, 1e-9) * 1e4 / (a * 1000.0), 60.0) if a > 0 else 0.0
        W_eff = float(np.clip(Wbar + I_mm / AWC, 0.0, 1.0))
        path.append({"year": 2026 + t, "a_khm2": float(a), "cum_khm2": float(A[j]),
                     "V_eq": round(v_eq(E, p, Vcap, W_eff / max(Wbar, 1e-6), WfT_bar), 2),
                     "I_mm": round(float(I_mm), 1)})
        i = j
    npv_u, i2 = 0.0, 0
    for t in range(T):
        j = min(int(round((A[i2] + 1.0) / dA)), nS - 1)
        npv_u += scen["disc"] ** t * reward(A[j], 1.0)
        i2 = j
    return dict(path=path, npv=float(Vf[0, 0]), npv_uniform=float(npv_u))


def resilience(df, p, Vcap, lam, n_sim=800, years=25, seed=7, dT=0.03, dW=0.002,
               u_lo=0.20, u_hi=0.55):
    rng = np.random.default_rng(seed)
    tr = df[df["split"] == "train"]
    clim = tr.groupby(tr["月份"].str[5:].astype(int))[["W_norm", "T2M", "E_index"]].mean()
    V0 = float(tr["FVC_fixed"].mean()); thr = 0.5 * Vcap
    paths = np.empty((n_sim, years * 12 + 1))
    fails, recov = 0, []
    for s in range(n_sim):
        V = V0; traj = [V]
        for t in range(years * 12):
            mo, yr = t % 12 + 1, t // 12
            W = float(np.clip(clim.loc[mo, "W_norm"], 0, 1))
            T = float(clim.loc[mo, "T2M"] + dT * yr)
            E = float(clim.loc[mo, "E_index"] * (1 + dW * yr) ** 2)
            V = v_next(V, W, T, E, p, Vcap)
            if rng.random() < lam / 12.0:
                V = max(V * (1 - rng.uniform(u_lo, u_hi)), 0.05)
            traj.append(V)
        traj = np.array(traj); paths[s] = traj
        if (traj < thr).any():
            fails += 1
            f0 = int(np.where(traj < thr)[0][0])
            back = np.where(traj[f0:] >= 0.9 * V0)[0]
            recov.append(int(back[0]) if len(back) else (years * 12 - f0))
    return dict(paths=paths, V0=V0, thr=float(thr), Vcap=float(Vcap), lam=float(lam),
                fail_prob=fails / n_sim,
                recov_median=float(np.median(recov)) if recov else 0.0,
                recov_n=len(recov),
                end_median=float(np.median(paths[:, -1])),
                end_p05=float(np.percentile(paths[:, -1], 5)),
                end_p95=float(np.percentile(paths[:, -1], 95)))


def main():
    panel = pd.read_csv(os.path.join(PROC, "panel_v2.csv"), encoding="utf-8-sig")
    panel = panel.sort_values(["站代码", "月份"]).reset_index(drop=True)
    n_imp = int(panel["FVC_fixed"].isna().sum())
    panel["FVC_fixed"] = panel.groupby("站代码")["FVC_fixed"].transform(
        lambda x: x.interpolate(limit=3, limit_direction="both"))
    panel = panel.dropna(subset=["FVC_fixed"]).reset_index(drop=True)
    panel["GWETROOT"] = panel["GWETROOT"].clip(0, 1)

    for code, sub in panel.groupby("站代码"):
        tr = sub[sub["split"] == "train"]["GWETROOT"]
        lo, hi = np.percentile(tr, [5, 90])
        panel.loc[sub.index, "W_norm"] = w_norm(sub["GWETROOT"].values, lo, hi)
        panel.loc[sub.index, "W_lo"] = lo
        panel.loc[sub.index, "W_hi"] = hi
        panel.loc[sub.index, "Vcap_s"] = float(min(np.percentile(
            sub[sub["split"] == "train"]["FVC_fixed"], 95), 80.0))

    out = {"meta": {"stations": int(panel["站代码"].nunique()), "rows": int(len(panel)),
                    "train": "2015-01—2022-12", "test": "2023-01—2024-12",
                    "n_fvc_imputed": n_imp,
                    "AWC_mm": AWC, "Zr_m": ZR, "theta_fc": TH_FC, "theta_wp": TH_WP}}

    rows, fits = [], {}
    print("[任务一] 约束标定（一步预测）…", flush=True)
    for code, sub in panel.groupby("站代码"):
        sub = sub.reset_index(drop=True)
        tr = sub[sub["split"] == "train"].reset_index(drop=True)
        te = sub[sub["split"] == "test"].reset_index(drop=True)
        Vcap = float(sub["Vcap_s"].iloc[0])
        p, ctx = fit_station(tr, Vcap, seed=abs(hash(code)) % 997)
        # 一步预测 R²（训练期用拟合值，测试期为外推）
        def one_step(d):
            V = d["FVC_fixed"].values
            pred = [v_next(V[i], d["W_norm"].values[i], d["T2M"].values[i],
                           d["E_index"].values[i], p, Vcap) for i in range(len(d) - 1)]
            return r2(V[1:], pred)
        sd = skill_decay(te, p, Vcap, horizons=(1, 3, 6, 12))
        rows.append({"站代码": code, "Vcap": round(Vcap, 2),
                     "W_lo": round(float(sub["W_lo"].iloc[0]), 3),
                     "W_hi": round(float(sub["W_hi"].iloc[0]), 3),
                     "R2_h1_train": round(one_step(tr), 3),
                     "R2_h1_test": round(one_step(te), 3),
                     "RMSE_h1": round(sd[1]["rmse"], 2),
                     "RMSE_h1_persist": round(sd[1]["rmse_persist"], 2),
                     "RMSE_h3": round(sd[3]["rmse"], 2),
                     "RMSE_h6": round(sd[6]["rmse"], 2),
                     "RMSE_h12": round(sd[12]["rmse"], 2),
                     "RMSE_h12_persist": round(sd[12]["rmse_persist"], 2),
                     "g": round(float(p[0]), 4), "m": round(float(p[1]), 5),
                     "k": round(float(p[2]), 5),
                     "V_anchor": round(float(tr["FVC_fixed"].mean()), 2),
                     "WfT_bar": round(float(ctx["WfT_bar"]), 4)})
        fits[code] = (tr, te, p, Vcap, ctx)
        print(f"  {code}: R2(h1,te)={rows[-1]['R2_h1_test']:+.3f}  h12RMSE={rows[-1]['RMSE_h12']} "
              f"(持续 {rows[-1]['RMSE_h12_persist']})  g={rows[-1]['g']} m={rows[-1]['m']} k={rows[-1]['k']}",
              flush=True)
    fdf = pd.DataFrame(rows)
    fdf.to_csv(os.path.join(RES, "model_fit_by_station.csv"), index=False, encoding="utf-8-sig")
    out["task1"] = {"fit": fdf.to_dict(orient="records"),
                    "R2_h1_test_median": float(fdf["R2_h1_test"].median()),
                    "n_positive_h1": int((fdf["R2_h1_test"] > 0).sum()),
                    "RMSE_h1_median": float(fdf["RMSE_h1"].median()),
                    "RMSE_h12_median": float(fdf["RMSE_h12"].median()),
                    "RMSE_h12_persist_median": float(fdf["RMSE_h12_persist"].median()),
                    "skill_note": "h 步为滚动起点自由推进；h≥6 时误差接近或超过持续性基线"}

    # figM1：最优站点的拟合与技能衰减
    best = fdf.sort_values("R2_h1_test", ascending=False).iloc[0]["站代码"]
    tr, te, p_b, cap_b, ctx_b = fits[best]
    sub = panel[panel["站代码"] == best].reset_index(drop=True)
    Vhat = [float(sub["FVC_fixed"].iloc[0])]
    for i in range(len(sub) - 1):
        Vhat.append(v_next(Vhat[-1], sub["W_norm"].values[i], sub["T2M"].values[i],
                           sub["E_index"].values[i], p_b, cap_b))
    fig, ax = plt.subplots(1, 2, figsize=(11.6, 3.9))
    ax[0].plot(sub["FVC_fixed"].values, lw=1.1, color="#4C78A8", label="观测")
    ax[0].plot(Vhat, lw=1.1, ls="--", color="#E45756", label="一步递推（自由推进仅作对照）")
    ax[0].axvline(len(tr), color="#888888", ls=":", lw=1)
    ax[0].set_xlabel("月份序号"); ax[0].set_ylabel("覆盖度（%）")
    ax[0].set_title(f"(a) {best} 站：观测与一步递推", fontsize=10)
    ax[0].legend(fontsize=8)
    hs = [1, 3, 6, 12]
    sd = skill_decay(te, p_b, cap_b, horizons=(1, 3, 6, 12))
    ax[1].plot(hs, [sd[h]["rmse"] for h in hs], "-o", ms=4, color="#54A24B", label="模型")
    ax[1].plot(hs, [sd[h]["rmse_persist"] for h in hs], "-s", ms=4, color="#999999", label="持续性基线")
    ax[1].set_xlabel("预报步长 h（月）"); ax[1].set_ylabel("RMSE（百分点）")
    ax[1].set_title("(b) 技能随步长衰减（测试期）", fontsize=10)
    ax[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "figM1_耦合拟合.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print("[任务二] 情景动态规划 …", flush=True)
    code2 = best
    tr2 = fits[code2][0]
    p2, cap2 = fits[code2][2], fits[code2][3]
    ctx2 = fits[code2][4]
    Wbar = float(tr2["W_norm"].mean()); Tbar = float(tr2["T2M"].mean())
    WFT = ctx2["WfT_bar"]
    plan = dp_plan(p2, cap2, Wbar, Tbar, WfT_bar=WFT)
    sens = []
    for share in (0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45):
        r = dp_plan(p2, cap2, Wbar, Tbar, dict(SCEN, pv_share=share), WfT_bar=WFT)
        sens.append({"pv_share": share, "npv": round(r["npv"], 1),
                     "end_cum_khm2": r["path"][-1]["cum_khm2"]})
    be = next((s["pv_share"] for s in sens if s["npv"] > 0), None)
    grid = []
    for build in (1.5, 2.0, 2.5):
        for pv in (6.0, 8.0, 10.0):
            r = dp_plan(p2, cap2, Wbar, Tbar, dict(SCEN, build=build, pv_rev=pv), WfT_bar=WFT)
            grid.append({"build": build, "pv_rev": pv, "npv": round(r["npv"], 1),
                         "a1": r["path"][0]["a_khm2"],
                         "cum": r["path"][-1]["cum_khm2"]})
    out["task2_grid"] = grid
    out["task2"] = {"station": code2, "npv": round(plan["npv"], 1),
                    "npv_uniform": round(plan["npv_uniform"], 1),
                    "path": plan["path"], "scenario": SCEN,
                    "break_even_pv_share": be, "sens": sens,
                    "note": "全部经济参数为情景假设，结果只作相对比较，不作投资结论"}
    fig, ax = plt.subplots(1, 2, figsize=(11.6, 3.9))
    yrs = [x["year"] for x in plan["path"]]
    ax[0].bar(yrs, [x["a_khm2"] for x in plan["path"]], color="#4C78A8")
    ax[0].set_ylabel("年新增（千 hm²）"); ax[0].set_title("(a) 情景最优建设路径", fontsize=10)
    axb = ax[0].twinx()
    axb.plot(yrs, [x["cum_khm2"] for x in plan["path"]], "-o", ms=3, color="#E45756")
    axb.set_ylabel("累计面积（千 hm²）", color="#E45756")
    ax[1].plot([s["pv_share"] for s in sens], [s["npv"] / 1e4 for s in sens], "-o", ms=4, color="#54A24B")
    ax[1].axhline(0, color="#333", lw=1)
    ax[1].set_xlabel("光伏配套面积占比"); ax[1].set_ylabel("NPV（亿元）")
    ax[1].set_title("(b) 光伏占比敏感性", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "figM3_最优路径.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print("[任务三] 韧性 …", flush=True)
    tr3 = panel[(panel["站代码"] == code2) & (panel["split"] == "train")]
    thrE = float(np.percentile(tr3["E_index"], 95))
    n_ev = int((tr3["E_index"] >= thrE).sum())
    lam = n_ev / (len(tr3) / 12.0)
    res = resilience(panel[panel["站代码"] == code2].reset_index(drop=True), p2, cap2, lam)
    out["task3"] = {"station": code2, "lambda_per_year": round(lam, 3), "n_events": n_ev,
                    "E_p95": round(thrE, 2), "fail_prob": round(res["fail_prob"], 3),
                    "recov_median_months": res["recov_median"], "n_recovered": res["recov_n"],
                    "end_median": round(res["end_median"], 2),
                    "end_p05": round(res["end_p05"], 2), "end_p95": round(res["end_p95"], 2),
                    "V0": round(res["V0"], 2), "thr": round(res["thr"], 2),
                    "clim_deltas": {"dT_C_per_year": 0.03, "wind_factor_per_year": 0.002},
                    "note": "λ 由实测超额频率估计；冲击幅度 U~U(0.20,0.55) 为情景假设"}
    fig, ax = plt.subplots(1, 2, figsize=(11.6, 3.9))
    ax[0].hist(res["paths"][:, -1], bins=28, color="#4C78A8", alpha=.85)
    ax[0].axvline(res["thr"], ls="--", color="#E45756", lw=1.3)
    ax[0].set_xlabel("2050 覆盖度（%）"); ax[0].set_ylabel("模拟次数")
    ax[0].set_title(f"(a) 2050 分布（阈值 {res['thr']:.1f}%）", fontsize=10)
    yy = np.arange(res["paths"].shape[1]) / 12.0 + 2026
    ax[1].plot(yy, np.median(res["paths"], axis=0), color="#4C78A8")
    ax[1].fill_between(yy, np.percentile(res["paths"], 5, axis=0),
                       np.percentile(res["paths"], 95, axis=0), color="#4C78A8", alpha=.18)
    ax[1].axhline(res["thr"], ls="--", color="#E45756", lw=1.2)
    ax[1].set_xlabel("年份"); ax[1].set_ylabel("覆盖度（%）")
    ax[1].set_title("(b) 冲击—恢复带", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "figM4_韧性.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)

    grid3 = []
    for lam_g in (0.25, 0.50, 0.75, 1.00):
        row = []
        for u_hi in (0.30, 0.45, 0.60):
            rg = resilience(panel[panel["站代码"] == code2].reset_index(drop=True),
                            p2, cap2, lam_g, n_sim=400, years=25, seed=11,
                            u_lo=0.15, u_hi=u_hi)
            row.append({"lam": lam_g, "u_hi": u_hi,
                        "P_end_below_half": round(float((rg["paths"][:, -1] < 0.5 * cap2).mean()), 3),
                        "end_median": round(rg["end_median"], 2)})
        grid3.append(row)
    out["task3_grid"] = grid3

    curves = []
    endp = res["paths"][:, -1]
    for x in (0.3, 0.4, 0.5, 0.6, 0.7):
        curves.append({"ratio": x, "thr": round(x * cap2, 2),
                       "P_below_end": round(float((endp < x * cap2).mean()), 3),
                       "P_below_any": round(float((res["paths"] < x * cap2).any(axis=1).mean()), 3)})
    out["task3_curves"] = curves

    json.dump(out, open(os.path.join(RES, "model_v2.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("NPV=", round(plan["npv"], 1), "对照=", round(plan["npv_uniform"], 1),
          "P(fail)=", round(res["fail_prob"], 3), "λ=", round(lam, 3), flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
