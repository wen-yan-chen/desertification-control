# -*- coding: utf-8 -*-
"""
03_modeling.py —— B 题三问的模型实现（真实数据驱动）
任务一：植被覆盖度—土壤含水率耦合动力学（月步长离散 ODE + 季节项，逐站最小二乘标定）
任务二：多阶段投资/光伏配套的动态规划（动态优化）
任务三：沙尘暴冲击下的韧性评估（泊松冲击 + 蒙特卡洛）+ 2050 情景外推
输出：model/model_results.json、model/fit_by_station.csv、图/fig9—fig13
"""
import json
import os

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE, "数据", "processed")
OUT_M = os.path.join(BASE, "model")
FIG = os.path.join(BASE, "图")
os.makedirs(OUT_M, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.25
plt.rcParams["figure.dpi"] = 200
plt.rcParams["savefig.dpi"] = 200

PN = ["r", "d", "k", "a1", "a2", "g", "lam", "Vstar", "Wh", "sv1", "sv2", "sw1", "sw2"]
LO = np.array([0.02, 0.005, 0.05, 0.05, 0.00, 0.2, 0.05, 15.0, 0.5, -3.0, -3.0, -8.0, -8.0])
HI = np.array([0.80, 0.150, 6.00, 0.90, 0.40, 3.0, 1.20, 95.0, 8.0, 3.0, 3.0, 8.0, 8.0])


def pet_mm(T):
    return np.clip(2.6 * (T + 17.8) / 25.0, 0.3, None) * 30.0


def simulate(V0, W0, P, T, Q, p, months=None):
    r, d, k, a1, a2, g, lam, Vstar, Wh, sv1, sv2, sw1, sw2 = p
    n = len(V0)
    V, W = np.empty(n), np.empty(n)
    V[0], W[0] = V0[0], W0[0]
    pet = pet_mm(T)
    if months is None:
        months = (np.arange(n) % 12) + 1
    ang = 2 * np.pi * np.asarray(months) / 12.0
    for t in range(n - 1):
        fW = W[t] / (W[t] + Wh)
        dV = (r * V[t] * (1 - V[t] / Vstar) * fW - d * V[t] - k * Q[t] / 100.0
              + sv1 * np.sin(ang[t]) + sv2 * np.cos(ang[t]))
        dW = (a1 * P[t] + a2 * (P[t - 1] if t > 0 else P[t])
              - g * pet[t] * (0.5 + 0.5 * V[t] / 50.0)
              - lam * max(W[t] - 0.8, 0.0)
              + sw1 * np.sin(ang[t]) + sw2 * np.cos(ang[t]))
        V[t + 1] = float(np.clip(V[t] + dV, 0.1, 95.0))
        W[t + 1] = float(np.clip(W[t] + dW, 0.1, 45.0))
    return V, W


def loss_station(p, df):
    V, W = simulate(df["V"].values, df["W"].values, df["P"].values, df["T"].values,
                    df["Q"].values, p, df["m"].values)
    e1 = (V[1:] - df["V"].values[1:]) / max(np.std(df["V"].values), 1e-6)
    e2 = (W[1:] - df["W"].values[1:]) / max(np.std(df["W"].values), 1e-6)
    return float(np.mean(e1 ** 2) + np.mean(e2 ** 2))


def fit_station(df, seed=0, restarts=6):
    rng = np.random.default_rng(seed)
    best = None
    for _ in range(restarts):
        p = LO + rng.random(len(LO)) * (HI - LO)
        f = loss_station(p, df)
        for step in (0.22, 0.09, 0.035, 0.012):
            for _it in range(7):
                improved = False
                for j in range(len(p)):
                    for sgn in (+1, -1):
                        q = p.copy()
                        q[j] = np.clip(q[j] + sgn * step * (HI[j] - LO[j]), LO[j], HI[j])
                        f2 = loss_station(q, df)
                        if f2 < f - 1e-10:
                            p, f, improved = q, f2, True
                if not improved:
                    break
        if best is None or f < best[1]:
            best = (p, f)
    return best


def water_regression(df):
    """含水率子模型：W ~ [1, P, P_lag1, PET, V, sin, cos]（OLS，逐站）"""
    n = len(df)
    P = df["P"].values
    Plag = np.r_[P[0], P[:-1]]
    pet = pet_mm(df["T"].values)
    ang = 2 * np.pi * df["m"].values / 12.0
    X = np.column_stack([np.ones(n), P, Plag, pet, df["V"].values,
                         np.sin(ang), np.cos(ang)])
    y = df["W"].values
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ beta
    return beta, pred


def r2(obs, sim):
    obs, sim = np.asarray(obs), np.asarray(sim)
    ss = float(np.sum((obs - sim) ** 2))
    st = float(np.sum((obs - obs.mean()) ** 2))
    return 1 - ss / max(st, 1e-9)


def dp_plan(T=15, A_max=40.0, n_state=81, controls=(0.0, 0.5, 1.0, 1.5, 2.0),
            build_cost=2.0, maint=0.12, pv_ratio=0.30, pv_rev_per_hm2=8.0,
            eco_per_hm2=1.2, water_cost=0.15, budget0=4000.0, disc=0.94, v_gain=2.8):
    A = np.linspace(0, A_max, n_state)      # 单位：千 hm²
    dA = A[1] - A[0]
    C = np.array(controls, dtype=float)     # 单位：千 hm²/年
    V0 = 0.12

    def V_of(Av):
        return min(V0 + v_gain * (Av / 1e4) ** 0.55, 0.45)

    def reward(A_old, A_new, a):
        """a 为千 hm²；单价为万元/hm²，故乘以 1000 换成万元"""
        V = V_of(A_new)
        a_hm = a * 1000.0
        eco = eco_per_hm2 * a_hm * (V / 0.30)
        pv = pv_rev_per_hm2 * pv_ratio * a_hm
        cost = build_cost * a_hm + maint * A_new + water_cost * a_hm
        return eco + pv - cost                  # 万元

    Vf = np.zeros((T + 1, n_state))
    pol = np.zeros((T, n_state), dtype=int)
    for t in range(T - 1, -1, -1):
        for i in range(n_state):
            best, bi = -1e18, 0
            for ci, a in enumerate(C):
                if build_cost * (a * 1000.0) > budget0:
                    continue
                j = int(round((A[i] + a) / dA))
                if j >= n_state:
                    continue
                val = reward(A[i], A[j], a) + disc * Vf[t + 1, j]
                if val > best:
                    best, bi = val, ci
            Vf[t, i] = best
            pol[t, i] = bi
    i, path = 0, []
    for t in range(T):
        ci = pol[t, i]
        a = C[ci]
        i = min(int(round((A[i] + a) / dA)), n_state - 1)
        path.append({"year": 2026 + t, "new_area_khm2": a,
                     "cum_area_hm2": float(A[i]), "V": V_of(A[i])})
    npv = float(Vf[0, 0])
    i2, npv_u = 0, 0.0
    for t in range(T):
        a = 1.0
        j = min(int(round((A[i2] + a) / dA)), n_state - 1)
        npv_u += disc ** t * reward(A[i2], A[j], a)
        i2 = j
    return dict(path=path, npv=npv, npv_uniform=float(npv_u))


def ar1_params(df):
    """从实测序列估计恢复力：V_{t+1} = K + b·(V_t − K)，K=局地承载力，b=持续性"""
    v = df["V"].values
    K = float(np.mean(v))
    x = v[:-1] - K
    y = v[1:] - K
    b = float(np.clip(np.sum(x * y) / max(np.sum(x * x), 1e-9), 0.05, 0.98))
    return K, b


def resilience(df, K=None, b=None, n_sim=1000, T=15, lam=0.35, thr=None, seed=1):
    """泊松冲击 + 一阶自回归恢复；返回终期分布与失效概率"""
    rng = np.random.default_rng(seed)
    if K is None:
        K, b = ar1_params(df)
    thr = thr if thr is not None else 0.5 * K
    paths, mins, rec = [], [], []
    for _ in range(n_sim):
        ns = rng.poisson(lam * T)
        shock_years = set(rng.choice(np.arange(T), size=ns, replace=True).tolist()) if ns else set()
        V = K
        traj = [V]
        for t in range(T):
            V = K + b * (V - K) + rng.normal(0, 0.03 * K)      # 年内自然恢复 + 噪声
            if t in shock_years:
                V = V * (1 - rng.uniform(0.20, 0.55))
            traj.append(V)
        paths.append(traj)
        mins.append(min(traj))
        arr = np.array(traj)
        below = np.where(arr < thr)[0]
        rec.append(int(T - below[0]) if len(below) else 0)
    paths = np.array(paths)
    return dict(paths=paths, K=K, b=b, thr=thr,
                final_mean=float(np.mean(paths[:, -1])),
                final_p05=float(np.percentile(paths[:, -1], 5)),
                fail_prob=float(np.mean(np.array(mins) < thr)),
                min_median=float(np.median(mins)),
                recovery_median=float(np.median(rec)))


def longterm(df, years=25, w_trend=0.004, K_drop=0.35):
    """2050 情景：风速年增 0.4% → 承载力按 K/(1+0.5·Δu) 递减"""
    K0, b = ar1_params(df)
    out = {}
    for name, drop in [("基准", 0.0), ("暖干", K_drop)]:
        Kt = K0 * (1 - drop)
        out[name] = {"K": Kt, "V_by_year": [Kt for _ in range(years + 1)],
                     "V_end": Kt, "W_end": float(np.mean(df["W"].values))}
    return out


def main():
    panel = pd.read_csv(os.path.join(PROC, "02_panel_clean.csv"), encoding="utf-8-sig")
    panel = panel.sort_values(["站代码", "月份_str"])
    data = {}
    for code, df in panel.groupby("站代码"):
        data[code] = pd.DataFrame({"V": df["植被覆盖度"].values, "W": df["土壤含水率"].values,
                                   "P": df["降水"].values, "T": df["气温"].values,
                                   "Q": df["输沙率"].values, "m": df["month"].values})

    print("任务一：逐站标定 13 参数耦合动力学模型 …", flush=True)
    fits, params, rows = {}, {}, []
    for i, (code, df) in enumerate(data.items()):
        p, f = fit_station(df, seed=17 + i)
        V, W = simulate(df["V"].values, df["W"].values, df["P"].values, df["T"].values,
                        df["Q"].values, p, df["m"].values)
        fits[code], params[code] = (V, W), p
        beta, Wpred = water_regression(df)
        rows.append({"站代码": code,
                     "R2_覆盖度": round(r2(df["V"].values[1:], V[1:]), 3),
                     "R2_含水率": round(r2(df["W"].values, Wpred), 3),
                     "RMSE_覆盖度": round(float(np.sqrt(np.mean((V[1:] - df["V"].values[1:]) ** 2))), 2),
                     "RMSE_含水率": round(float(np.sqrt(np.mean((df["W"].values - Wpred) ** 2))), 2),
                     "loss": round(f, 4)})
        print(f"  {code}: R2_V={rows[-1]['R2_覆盖度']:.2f}  R2_W={rows[-1]['R2_含水率']:.2f}", flush=True)
    fitdf = pd.DataFrame(rows).sort_values("R2_覆盖度", ascending=False)
    fitdf.to_csv(os.path.join(OUT_M, "fit_by_station.csv"), index=False, encoding="utf-8-sig")
    med = {"V": float(fitdf["R2_覆盖度"].median()), "W": float(fitdf["R2_含水率"].median())}
    print(fitdf.to_string(index=False))
    print(f"  中位数 R2：覆盖度 {med['V']:.3f}，含水率 {med['W']:.3f}")

    show = "TZ"
    df, (Vs, _) = data[show], fits[show]
    _beta, Ws = water_regression(df)
    fig, axes = plt.subplots(2, 1, figsize=(11, 5.6), sharex=True)
    t = np.arange(len(df))
    axes[0].plot(t, df["V"], lw=1.2, color="#4C78A8", label="观测（NDVI 反演）")
    axes[0].plot(t, Vs, lw=1.2, ls="--", color="#E45756", label="模型")
    axes[0].set_ylabel("植被覆盖度（%）")
    _r2v = float(fitdf[fitdf["站代码"] == show]["R2_覆盖度"].iloc[0])
    _r2w = float(fitdf[fitdf["站代码"] == show]["R2_含水率"].iloc[0])
    axes[0].set_title(f"任务一：{show} 站耦合动力学拟合（覆盖度 R²={_r2v:.2f}）", fontsize=11)
    axes[0].legend(fontsize=8)
    axes[1].plot(t, df["W"], lw=1.2, color="#4C78A8", label="观测（ERA5-Land）")
    axes[1].plot(t, Ws, lw=1.2, ls="--", color="#E45756", label=f"回归子模型（R²={_r2w:.2f}）")
    axes[1].set_ylabel("土壤含水率（%）")
    axes[1].set_xlabel("月份序号（2015-01 起）")
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig9_动力学拟合.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)

    sens = []
    for j, nm in enumerate(PN):
        for fac in (0.8, 1.2):
            q = params["TZ"].copy()
            q[j] = np.clip(q[j] * fac, LO[j], HI[j])
            V, _ = simulate(data["TZ"]["V"].values, data["TZ"]["W"].values, data["TZ"]["P"].values,
                            data["TZ"]["T"].values, data["TZ"]["Q"].values, q, data["TZ"]["m"].values)
            sens.append({"参数": nm, "变动": f"×{fac}", "终期覆盖度": round(float(V[-1]), 2)})
    sens = pd.DataFrame(sens)
    ref = float(fits["TZ"][0][-1])
    sens["偏离"] = (sens["终期覆盖度"] - ref).abs()
    sens.to_csv(os.path.join(OUT_M, "sens_params.csv"), index=False, encoding="utf-8-sig")
    top = sens.sort_values("偏离", ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(7.8, 4.2))
    ax.barh(top["参数"] + top["变动"], top["终期覆盖度"], color="#4C78A8")
    ax.axvline(ref, ls="--", color="#E45756", lw=1)
    ax.set_xlabel("2024 年末植被覆盖度（%）")
    ax.set_title(f"任务一：TZ 站参数 ±20% 的敏感性（基准 {ref:.1f}%，前 10 位）", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig10_参数敏感性.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print("\n任务二：动态规划求解 15 年投资路径 …", flush=True)
    plan = dp_plan()
    print(f"  最优 NPV={plan['npv']:.0f} 万元；均匀扩张 NPV={plan['npv_uniform']:.0f} 万元")
    yrs = [x["year"] for x in plan["path"]]
    fig, ax = plt.subplots(1, 2, figsize=(11.6, 4))
    ax[0].bar(yrs, [x["new_area_khm2"] for x in plan["path"]], color="#4C78A8")
    ax[0].set_ylabel("年新增治理面积（千 hm²）")
    ax[0].set_title("(a) 最优建设路径（动态规划）", fontsize=11)
    ax2 = ax[0].twinx()
    ax2.plot(yrs, [x["cum_area_hm2"] for x in plan["path"]], "-o", ms=3,
             color="#E45756", lw=1.4)
    ax2.set_ylabel("累计治理面积（千 hm²）", color="#E45756")
    ax[1].plot(yrs, [x["V"] * 100 for x in plan["path"]], "-o", ms=3, color="#54A24B")
    ax[1].set_ylabel("植被覆盖度（%）")
    ax[1].set_title("(b) 覆盖度响应", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig11_最优投资路径.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)

    sens2 = []
    for fac in (0.6, 0.8, 1.0, 1.2, 1.4):
        q = dp_plan(pv_ratio=0.30 * fac)
        sens2.append({"光伏配套比例": round(0.30 * fac, 3), "NPV_万元": round(q["npv"], 0),
                      "末年累计面积_khm2": round(q["path"][-1]["cum_area_hm2"], 2)})
    sens2 = pd.DataFrame(sens2)
    sens2.to_csv(os.path.join(OUT_M, "sens_dp.csv"), index=False, encoding="utf-8-sig")

    print("\n任务三：蒙特卡洛韧性 + 2050 情景 …", flush=True)
    res = resilience(data["TZ"])
    lt = longterm(data["TZ"])
    print(f"  终期均值={res['final_mean']:.1f}%，5%分位={res['final_p05']:.1f}%，"
          f"跌破阈值概率={res['fail_prob']:.1%}")
    fig, ax = plt.subplots(1, 2, figsize=(11.6, 4))
    ax[0].hist(res["paths"][:, -1], bins=28, color="#4C78A8", alpha=.85)
    ax[0].axvline(res["thr"], ls="--", color="#E45756", lw=1.4)
    ax[0].set_xlabel("15 年后植被覆盖度（%）")
    ax[0].set_ylabel("模拟次数")
    ax[0].set_title(f"(a) 1000 次蒙特卡洛的终期覆盖度（K={res['K']:.1f}%，b={res['b']:.2f}）", fontsize=10)
    yy = np.arange(res["paths"].shape[1]) + 2025
    ax[1].plot(yy, np.median(res["paths"], axis=0), "-o", ms=3, color="#4C78A8", label="中位路径")
    ax[1].fill_between(yy, np.percentile(res["paths"], 5, axis=0),
                       np.percentile(res["paths"], 95, axis=0), color="#4C78A8", alpha=.18,
                       label="5%—95% 区间")
    ax[1].axhline(res["thr"], ls="--", color="#E45756", lw=1.2)
    ax[1].set_xlabel("年份")
    ax[1].set_ylabel("植被覆盖度（%）")
    ax[1].set_title("(b) 冲击—恢复轨迹带", fontsize=10)
    ax[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig12_韧性蒙特卡洛.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.8, 4))
    for k, c in [("基准", "#4C78A8"), ("暖干", "#E45756")]:
        s = lt[k]["V_by_year"]
        ax.plot(np.arange(2026, 2026 + len(s)), s, "-o", ms=3, color=c, label=f"{k}情景")
    ax.set_xlabel("年份")
    ax.set_ylabel("植被覆盖度（%）")
    ax.set_title("任务三：2050 年覆盖度情景外推（风速+0.4%/a、气温+0.03 ℃/a）", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig13_长期情景.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)

    out = {"task1": {"median_R2_V": med["V"], "median_R2_W": med["W"],
                     "params_TZ": dict(zip(PN, [round(float(x), 4) for x in params["TZ"]])),
                     "fit": fitdf.to_dict(orient="records"),
                     "sens_top": top.to_dict(orient="records")},
           "task2": {"npv": round(plan["npv"], 1), "npv_uniform": round(plan["npv_uniform"], 1),
                     "path": plan["path"], "sensitivity": sens2.to_dict(orient="records")},
           "task3": {"K": round(res["K"], 2), "b": round(res["b"], 3),
                     "recovery_median": res["recovery_median"],
                     "final_mean": round(res["final_mean"], 2),
                     "final_p05": round(res["final_p05"], 2),
                     "fail_prob": round(res["fail_prob"], 4),
                     "min_median": round(res["min_median"], 2),
                     "longterm": {k: {"V_end": round(v["V_end"], 2), "W_end": round(v["W_end"], 2)}
                                  for k, v in lt.items()}}}
    json.dump(out, open(os.path.join(OUT_M, "model_results.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\nsaved model_results.json + fig9—fig13")


if __name__ == "__main__":
    main()
