# -*- coding: utf-8 -*-
"""
model_v6.py —— 植被—水分—风沙耦合（年尺度，保守且参数可解释）+ 优化 + 韧性
--------------------------------------------------------------------------
任务一：V_{y+1} = V_y + r·V_y(1−V_y/K)·W_y·fT(T_y) − d·V_y − k·E_eff,y·V_y
        E_eff,y = E_y·(1 − η·V_y/K)          （植被遮蔽降低风蚀：双向耦合的第二步）
        K 由观测 95% 分位确定；标定 r, d, k, η 四个参数（物理含义明确）
任务二：15 年动态规划（面积 / 补水 / 光伏占比；预算·水量·土地·劳动力约束）
任务三：吸收马尔可夫链（年步长）+ 蒙特卡洛交叉验证
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

LAM = 0.6      # 事件频率（次/年）：由侵蚀指数 95% 超额频率估计


def fT(T):
    """温度响应因子（0—1）"""
    return float(np.clip((T - 5.0) / 20.0, 0.0, 1.0))


def build_annual(panel):
    p = panel.copy()
    p["年"] = p["月份"].str[:4].astype(int)
    a = p.groupby(["站代码", "年"]).agg(
        V=("FVC_fixed", "mean"), P=("P_mm", "sum"), ET0=("ET0_mm", "sum"),
        T=("T2M", "mean"), E=("E_index", "mean"), W=("GWETROOT", "mean")).reset_index()
    a["split"] = np.where(a["年"] <= 2022, "train", "test")
    a["Wn"] = np.nan
    a["Em"] = a["E"]
    for code, sub in a.groupby("站代码"):
        lo, hi = np.percentile(sub[sub["split"] == "train"]["W"], [5, 90])
        a.loc[sub.index, "Wn"] = np.clip((sub["W"] - lo) / max(hi - lo, 1e-6), 0, 1)
    return a


def step(V, W, E, T, p):
    r, K, d, k, eta = p
    ks = float(np.clip(W, 0, 1))
    E_eff = E * (1 - eta * min(V / max(K, 1e-6), 1.0))
    V1 = V + r * V * (1 - V / K) * ks * fT(T) - d * V - k * E_eff * V
    return float(np.clip(V1, 0.02, 100.0))


def simulate(df, p):
    V = np.empty(len(df))
    V[0] = float(df["V"].values[0])
    W = df["Wn"].values; E = df["Em"].values; T = df["T"].values
    for t in range(len(df) - 1):
        V[t + 1] = step(V[t], W[t], E[t], T[t], p)
    return V


def fit(df, K_fix, seed=0, restarts=25):
    rng = np.random.default_rng(seed)
    obs = df["V"].values.astype(float)
    lo = np.array([0.02, 0.000, 0.000, 0.000])
    hi = np.array([1.50, 0.300, 0.500, 0.950])

    def f(q):
        p = (q[0], K_fix, q[1], q[2], q[3])
        return float(np.mean((simulate(df, p) - obs) ** 2))

    best = (lo + (hi - lo) * 0.3, np.inf)
    for _ in range(restarts):
        q = lo + rng.random(4) * (hi - lo)
        val = f(q)
        for st in (0.3, 0.12, 0.05, 0.02, 0.008):
            for _it in range(10):
                imp = False
                for j in range(4):
                    for sg in (1, -1):
                        qq = q.copy()
                        qq[j] = np.clip(q[j] + sg * st * (hi[j] - lo[j]), lo[j], hi[j])
                        v2 = f(qq)
                        if v2 < val * (1 - 1e-5):
                            q, val, imp = qq, v2, True
                if not imp:
                    break
        if val < best[1]:
            best = (q, val)
    q = best[0]
    return (float(q[0]), float(K_fix), float(q[1]), float(q[2]), float(q[3]))


def r2(o, s):
    o, s = np.asarray(o, float), np.asarray(s, float)
    return 1 - float(np.sum((o - s) ** 2)) / max(float(np.sum((o - o.mean()) ** 2)), 1e-9)


# ---------------- 任务二 ----------------
SC = dict(A_max=20.0, T=15, build=2.0, maint=0.12, pv=8.0, pv_share_max=0.5,
          p_e=0.15, water_cost=0.5, B=4000.0, W_max=500.0, L_max=600.0,
          labor_per_hm2=0.02, disc=0.94)


def v_ss(K, d, r, k, eta, ks_val=1.0, E=1.0):
    """解 r(1−x)ks = d + k·E(1−ηx)（x=V/K），取 [0,1] 内解"""
    A = -r * ks_val + k * E * eta
    Bc = r * ks_val - d - k * E
    x = -Bc / A if abs(A) > 1e-12 else (1.0 if Bc <= 0 else 0.0)
    x = float(np.clip(x, 0, 1))
    if r * (1 - x) * ks_val - (d + k * E * (1 - eta * x)) > 1e-9:
        x = 0.0
    return float(np.clip(K * x, 0, K))


def dp(sc=SC, K=25.0, d=0.005, r=1.0, k=0.05, eta=0.7,
       a_ctrl=(0, 0.5, 1.0, 1.5, 2.0), s_ctrl=(0.2, 0.3, 0.4, 0.5),
       i_ctrl=(0, 20, 40, 60)):
    A_max, T = sc["A_max"], sc["T"]
    nS = 81
    A = np.linspace(0, A_max, nS); dA = A[1] - A[0]

    def reward(A_new, a, s, I):
        a_hm = a * 1000.0
        if a_hm <= 0:
            return 0.0, 0.0, 0.0
        ks_val = float(np.clip(0.45 + 0.55 * I / 60.0, 0, 1))
        Vss = v_ss(K, d, r, k, eta, ks_val=ks_val)
        eco = sc["p_e"] * (Vss / max(K, 1e-6)) * A_new * 1000.0
        pvr = sc["pv"] * s * a_hm
        cost = sc["build"] * a_hm + sc["maint"] * A_new * 1000.0 + sc["water_cost"] * (I * a / 1000.0)
        return eco + pvr - cost, Vss, I * a / 1000.0

    Vf = np.zeros((T + 1, nS)); pol = {}
    for t in range(T - 1, -1, -1):
        for i in range(nS):
            best, ch = -1e18, None
            for a in a_ctrl:
                if A[i] + a > A_max + 1e-9:
                    continue
                j = min(int(round((A[i] + a) / dA)), nS - 1)
                for s in s_ctrl:
                    if s > sc["pv_share_max"]:
                        continue
                    for I in i_ctrl:
                        if I * a / 1000.0 > sc["W_max"]:
                            continue
                        if sc["build"] * a * 1000.0 > sc["B"]:
                            continue
                        if sc["labor_per_hm2"] * a * 1000.0 > sc["L_max"]:
                            continue
                        rw, Vss, w = reward(A[j], a, s, I)
                        val = rw + sc["disc"] * Vf[t + 1, j]
                        if val > best:
                            best, ch = val, (a, s, I, j, rw, Vss, w)
            Vf[t, i] = best; pol[(t, i)] = ch
    i, path = 0, []
    for t in range(T):
        ch = pol[(t, i)]
        if ch is None:
            path.append(dict(year=2026 + t, a=0.0, s=0.0, I=0.0, A=round(float(A[i]), 2),
                             net=0.0, Vss=0.0, water=0.0))
            continue
        a, s, I, j, rw, Vss, w = ch
        path.append(dict(year=2026 + t, a=a, s=s, I=I, A=round(float(A[j]), 2),
                         net=round(rw, 1), Vss=round(Vss, 2), water=round(w, 1)))
        i = j
    return dict(npv=float(Vf[0, 0]), path=path, A_end=path[-1]["A"])


# ---------------- 任务三（年步长吸收链） ----------------
def markov(K, d, r, k, eta, ks_val=0.55, n_state=120, T_year=25,
           lam_year=LAM, u_lo=0.2, u_hi=0.55, v_crit=0.4, nq=41):
    edges = np.linspace(0, K, n_state + 1); h = edges[1] - edges[0]
    n_abs = max(1, int(np.floor(v_crit * K / h)))

    def drift(v):
        return r * v * (1 - v / K) * ks_val - d * v - k * (1 - eta * v / K) * v

    P = np.zeros((n_state, n_state))
    for i in range(n_state):
        v = 0.5 * (edges[i] + edges[i + 1])
        v1 = float(np.clip(v + drift(v), 0, K))
        x = v1 / h
        j = int(np.clip(np.floor(x), 0, n_state - 2)); fr = x - j
        P[i, j] += (1 - lam_year) * (1 - fr); P[i, j + 1] += (1 - lam_year) * fr
        for u in np.linspace(u_lo, u_hi, nq):
            v2 = v * (1 - u)
            x2 = v2 / h
            j2 = int(np.clip(np.floor(x2), 0, n_state - 2)); f2 = x2 - j2
            P[i, j2] += lam_year / nq * (1 - f2); P[i, j2 + 1] += lam_year / nq * f2
    P /= P.sum(axis=1, keepdims=True)
    tr = np.arange(n_abs, n_state)
    Q = P[np.ix_(tr, tr)]
    N = np.linalg.inv(np.eye(len(tr)) - Q)
    tau = N.sum(axis=1)                       # 期望首达时间（年）
    hitT = 1 - np.linalg.matrix_power(Q, T_year).sum(axis=1)
    start = int(np.clip(round(0.8 * K / h) - n_abs, 0, len(tr) - 1))
    return dict(tau=tau, hitT=hitT, tau_at=float(tau[start]), hit_at=float(hitT[start]),
                v_crit=v_crit * K, lam=lam_year)


def mc(K, d, r, k, eta, ks_val=0.55, lam_year=LAM, u_lo=0.2, u_hi=0.55,
       v0=0.8, v_crit=0.4, T_year=25, n=20000, seed=7):
    rng = np.random.default_rng(seed)
    hit, taus = 0, []
    for _ in range(n):
        v = v0 * K
        for t in range(1, T_year + 1):
            v = v + r * v * (1 - v / K) * ks_val - d * v - k * v
            if rng.random() < lam_year:
                v *= 1 - rng.uniform(u_lo, u_hi)
            if v < v_crit * K:
                hit += 1; taus.append(t); break
    return dict(hit_prob=hit / n, tau_median=float(np.median(taus)) if taus else float("nan"))


def main():
    panel = pd.read_csv(os.path.join(PROC, "panel_v2.csv"), encoding="utf-8-sig")
    panel["FVC_fixed"] = panel.groupby("站代码")["FVC_fixed"].transform(
        lambda x: x.interpolate(limit=3, limit_direction="both"))
    panel = panel.dropna(subset=["FVC_fixed"])
    ann = build_annual(panel)

    out = {"meta": {"stations": int(ann["站代码"].nunique()),
                    "years": [int(ann["年"].min()), int(ann["年"].max())],
                    "train": "2015—2022", "test": "2023—2024", "lam": LAM}}

    rows, fits = [], {}
    print("[任务一] 年尺度标定 …", flush=True)
    for code, sub in ann.groupby("站代码"):
        sub = sub.sort_values("年").reset_index(drop=True)
        tr = sub[sub["split"] == "train"].reset_index(drop=True)
        te = sub[sub["split"] == "test"].reset_index(drop=True)
        K_fix = float(np.clip(np.percentile(tr["V"], 95) * 1.15, 8, 70))
        p = fit(tr, K_fix, seed=sum(ord(c) for c in code) % 991)
        Vtr = simulate(tr, p)
        # 一年外推（用上一年实测作初值）
        pred = []
        for k_ in range(len(te)):
            prev = sub[sub["年"] == te["年"].values[k_] - 1].iloc[0]
            pred.append(step(prev["V"], prev["Wn"], prev["Em"], prev["T"], p))
        pred = np.array(pred)
        obs_te = te["V"].values
        base = np.array([sub[sub["年"] == y - 1]["V"].values[0] for y in te["年"].values])
        rows.append({"站代码": code, "r": round(p[0], 3), "K": round(p[1], 1),
                     "d": round(p[2], 4), "k": round(p[3], 4), "eta": round(p[4], 2),
                     "R2_train": round(r2(tr["V"].values, Vtr), 3),
                     "RMSE_1y": round(float(np.sqrt(np.mean((obs_te - pred) ** 2))), 2),
                     "RMSE_persist": round(float(np.sqrt(np.mean((obs_te - base) ** 2))), 2)})
        fits[code] = (tr, te, p, Vtr, pred)
        print(f"  {code}: r={p[0]:.2f} K={p[1]:.1f} d={p[2]:.3f} k={p[3]:.3f} eta={p[4]:.2f} "
              f"R2tr={rows[-1]['R2_train']:+.3f} 1y={rows[-1]['RMSE_1y']}(持续 {rows[-1]['RMSE_persist']})",
              flush=True)
    fdf = pd.DataFrame(rows)
    fdf.to_csv(os.path.join(RES, "model_v6_fit.csv"), index=False, encoding="utf-8-sig")
    out["task1"] = {"fit": fdf.to_dict(orient="records"),
                    "R2_train_median": float(fdf["R2_train"].median()),
                    "n_beat_persist": int((fdf["RMSE_1y"] < fdf["RMSE_persist"]).sum()),
                    "k_median": float(fdf["k"].median()),
                    "eta_median": float(fdf["eta"].median()),
                    "rep": {c: round(float(fdf[c].median()), 4) for c in ["r", "K", "d", "k", "eta"]}}

    best = fdf.sort_values("R2_train", ascending=False).iloc[0]["站代码"]
    tr, te, p_b, Vtr, pred = fits[best]
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    yrs = tr["年"].tolist() + te["年"].tolist()
    ax.plot(yrs[:len(tr)], tr["V"].values, "o-", ms=4, color="#4C78A8", label="观测")
    ax.plot(yrs[:len(tr)], Vtr, "s--", ms=4, color="#E45756", label="模型")
    ax.plot(yrs[len(tr):], te["V"].values, "o-", ms=4, color="#4C78A8")
    ax.plot(yrs[len(tr):], pred, "s--", ms=4, color="#54A24B", label="一年外推")
    ax.axvline(2022.5, color="#888", ls=":", lw=1)
    ax.set_xlabel("年份"); ax.set_ylabel("年均覆盖度（%）")
    ax.set_title(f"任务一：{best} 站（r={p_b[0]:.2f}, K={p_b[1]:.1f}, k={p_b[3]:.3f}）", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "figS1_拟合.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print("[任务二] 动态规划 …", flush=True)
    rep = out["task1"]["rep"]
    base = dp(K=rep["K"], d=rep["d"], r=rep["r"], k=rep["k"], eta=rep["eta"])
    share_sweep, maint_sweep, sens = [], [], []
    for sv in (0.1, 0.2, 0.3, 0.4, 0.5):
        rr = dp(K=rep["K"], d=rep["d"], r=rep["r"], k=rep["k"], eta=rep["eta"], s_ctrl=(sv,))
        share_sweep.append({"pv_share": sv, "npv": round(rr["npv"], 1), "A_end": rr["A_end"]})
    for mv in (0.08, 0.12, 0.16, 0.20):
        sc = dict(SC); sc["maint"] = mv
        rr = dp(sc=sc, K=rep["K"], d=rep["d"], r=rep["r"], k=rep["k"], eta=rep["eta"])
        maint_sweep.append({"maint": mv, "npv": round(rr["npv"], 1), "A_end": rr["A_end"]})
    for key, vals in [("build", (1.5, 2.0, 2.5)), ("pv", (5.0, 8.0, 11.0)),
                      ("B", (3000, 4000, 5000)), ("W_max", (300, 500, 700))]:
        for v in vals:
            sc = dict(SC); sc[key] = v
            rr = dp(sc=sc, K=rep["K"], d=rep["d"], r=rep["r"], k=rep["k"], eta=rep["eta"])
            sens.append({"param": key, "value": v, "npv": round(rr["npv"], 1)})
    out["task2"] = {"npv": round(base["npv"], 1), "path": base["path"], "scen": SC,
                    "share_sweep": share_sweep, "maint_sweep": maint_sweep, "sens": sens,
                    "A_end": base["A_end"]}

    print("[任务三] 吸收链 + MC …", flush=True)
    sweep = []
    for vc in (0.2, 0.3, 0.4, 0.5):
        mk_ = markov(rep["K"], rep["d"], rep["r"], rep["k"], rep["eta"], v_crit=vc)
        mc_ = mc(rep["K"], rep["d"], rep["r"], rep["k"], rep["eta"], v_crit=vc)
        sweep.append({"v_crit_ratio": vc, "thr": round(vc * rep["K"], 2),
                      "hit_markov": round(mk_["hit_at"], 3), "hit_mc": round(mc_["hit_prob"], 3),
                      "tau_markov": round(mk_["tau_at"], 1), "tau_mc": round(mc_["tau_median"], 1)})
    lam_sweep = []
    for lm in (0.15, 0.30, 0.45, 0.60, 0.80):
        mk_ = markov(rep["K"], rep["d"], rep["r"], rep["k"], rep["eta"],
                     v_crit=0.3, lam_year=lm)
        mc_ = mc(rep["K"], rep["d"], rep["r"], rep["k"], rep["eta"],
                 v_crit=0.3, lam_year=lm, n=8000)
        lam_sweep.append({"lam": lm, "hit_markov": round(mk_["hit_at"], 3),
                          "hit_mc": round(mc_["hit_prob"], 3),
                          "tau_markov": round(mk_["tau_at"], 1),
                          "tau_mc": round(mc_["tau_median"], 1)})
    out["task3"] = {"K": rep["K"], "lam": LAM, "sweep": sweep, "lam_sweep": lam_sweep}

    json.dump(out, open(os.path.join(RES, "model_v6.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=float)
    print("R2 中位:", out["task1"]["R2_train_median"], "| 1 年胜持续性:",
          out["task1"]["n_beat_persist"], "/8 | k 中位:", out["task1"]["k_median"],
          "| NPV:", out["task2"]["npv"], flush=True)
    print("韧性扫描:", [(s["v_crit_ratio"], s["hit_markov"], s["hit_mc"]) for s in sweep], flush=True)


if __name__ == "__main__":
    main()
