# -*- coding: utf-8 -*-
"""
model_v4.py —— B 题取向：逻辑清楚优先；任务一/二保守，任务三保留创新点

任务一（保守）：年尺度两状态耦合（覆盖度 V、根区有效储水 S），3 个参数 r, K, d
任务二（保守，重点）：15 年多阶段动态规划（面积/补水/光伏占比，预算·水量·土地·劳动力约束）
任务三（创新）：冲击—恢复的吸收马尔可夫链（解析首达时间）+ 蒙特卡洛交叉验证
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
S_FC = 1000 * ZR * TH_FC          # 60 mm
ET_FRAC = 0.25                    # 年尺度蒸散折算系数（情景）


def annual_panel(panel):
    p = panel.copy()
    p["年"] = p["月份"].str[:4].astype(int)
    return p.groupby(["站代码", "年"]).agg(
        V=("FVC_fixed", "mean"), P=("P_mm", "sum"), ET0=("ET0_mm", "sum"),
        T=("T2M", "mean")).reset_index()


def ks_of(S, Scap=S_FC):
    return float(np.clip(S / max(Scap, 1e-6), 0, 1))


def sim_annual(rows, p):
    r, K, d = p
    n = len(rows)
    V = np.empty(n); S = np.empty(n)
    V[0] = rows["V"].values[0]; S[0] = 0.8 * S_FC
    for i in range(n - 1):
        ks = ks_of(S[i])
        et = ET_FRAC * ET0_i(rows, i) * ks * (0.3 + 0.7 * min(V[i] / max(K, 1e-6), 1.0))
        S[i + 1] = float(np.clip(S[i] + rows["P"].values[i] - et, 0, S_FC))
        V[i + 1] = float(np.clip(V[i] + r * V[i] * (1 - V[i] / K) * ks - d * V[i], 0.05, 100))
    return V, S


def ET0_i(rows, i):
    return float(rows["ET0"].values[i])


def fit_annual(rows, K_fix, seed=0, restarts=30):
    """K 由观测分位给出（不拟合），只标定生长率 r 与衰亡率 d"""
    rng = np.random.default_rng(seed)
    lo = np.array([0.02, 0.005]); hi = np.array([1.20, 0.30])
    obs = rows["V"].values

    def f(q):
        p = (q[0], K_fix, q[1])
        V, _ = sim_annual(rows, p)
        return float(np.mean((V - obs) ** 2))

    best = (lo + (hi - lo) * 0.3, np.inf)
    for _ in range(restarts):
        q = lo + rng.random(2) * (hi - lo)
        val = f(q)
        for step in (0.3, 0.12, 0.05, 0.02, 0.008):
            for _it in range(10):
                imp = False
                for j in range(2):
                    for sg in (1, -1):
                        qq = q.copy()
                        qq[j] = np.clip(q[j] + sg * step * (hi[j] - lo[j]), lo[j], hi[j])
                        v2 = f(qq)
                        if v2 < val * (1 - 1e-5):
                            q, val, imp = qq, v2, True
                if not imp:
                    break
        if val < best[1]:
            best = (q, val)
    return (float(best[0][0]), float(K_fix), float(best[0][1]))


def r2(o, s):
    o, s = np.asarray(o, float), np.asarray(s, float)
    return 1 - float(np.sum((o - s) ** 2)) / max(float(np.sum((o - o.mean()) ** 2)), 1e-9)


# ---------------- 任务二 ----------------
SC = dict(A_max=20.0, T=15, build=2.0, maint=0.12, pv=8.0, pv_share_max=0.5,
          p_e=0.15, water_cost=0.5, B=4000.0, W_max=500.0, L_max=600.0,
          labor_per_hm2=0.02, disc=0.94)


def v_ss(K, d, r, ks_val):
    if ks_val <= 1e-6:
        return 0.0
    return float(np.clip(K * (1 - d / max(r * ks_val, 1e-9)), 0.0, K))


def dp(sc=SC, K=30.0, d=0.03, r=0.4,
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
        Vss = v_ss(K, d, r, ks_val)
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
    return dict(npv=float(Vf[0, 0]), path=path, A_end=path[-1]["A"], scen=sc)


# ---------------- 任务三 ----------------
def markov_resilience(K, d, r, ks_val=0.55, n_state=80, T_month=300,
                      lam_year=0.6, u_lo=0.2, u_hi=0.55, v_crit=0.4, nq=41):
    edges = np.linspace(0, K, n_state + 1)
    h = edges[1] - edges[0]
    pj = lam_year / 12.0

    def drift(v):
        return r * v * (1 - v / K) * ks_val - d * v

    n_abs = max(1, int(np.floor(v_crit * K / h)))
    P = np.zeros((n_state, n_state))
    for i in range(n_state):
        v = 0.5 * (edges[i] + edges[i + 1])
        v1 = float(np.clip(v + drift(v), 0, K))
        x = v1 / h
        j = int(np.clip(np.floor(x), 0, n_state - 2)); fr = x - j
        P[i, j] += (1 - pj) * (1 - fr); P[i, j + 1] += (1 - pj) * fr
        for frac in np.linspace(u_lo, u_hi, nq):
            v2 = v * (1 - frac)
            x2 = v2 / h
            j2 = int(np.clip(np.floor(x2), 0, n_state - 2)); f2 = x2 - j2
            P[i, j2] += pj / nq * (1 - f2); P[i, j2 + 1] += pj / nq * f2
    P /= P.sum(axis=1, keepdims=True)
    tr = np.arange(n_abs, n_state)
    Q = P[np.ix_(tr, tr)]
    N = np.linalg.inv(np.eye(len(tr)) - Q)
    tau = N.sum(axis=1)
    hitT = 1 - np.linalg.matrix_power(Q, T_month).sum(axis=1)
    start = int(np.clip(round(0.8 * K / h) - n_abs, 0, len(tr) - 1))
    return dict(tau=tau, hitT=hitT, tau_at=float(tau[start]), hit_at=float(hitT[start]),
                v_crit=v_crit * K, lam=lam_year, n_abs=n_abs)


def mc_resilience(K, d, r, ks_val=0.55, lam_year=0.6, u_lo=0.2, u_hi=0.55,
                  v0=0.8, v_crit=0.4, T_month=300, n=6000, seed=3):
    rng = np.random.default_rng(seed)
    hit, taus = 0, []
    for _ in range(n):
        v = v0 * K
        for t in range(1, T_month + 1):
            v = v + r * v * (1 - v / K) * ks_val - d * v
            if rng.random() < lam_year / 12.0:
                v *= 1 - rng.uniform(u_lo, u_hi)
            if v < v_crit * K:
                hit += 1; taus.append(t); break
    return dict(hit_prob=hit / n, tau_median=float(np.median(taus)) if taus else float("nan"))


def main():
    panel = pd.read_csv(os.path.join(PROC, "panel_v2.csv"), encoding="utf-8-sig")
    panel["FVC_fixed"] = panel.groupby("站代码")["FVC_fixed"].transform(
        lambda x: x.interpolate(limit=3, limit_direction="both"))
    panel = panel.dropna(subset=["FVC_fixed"])
    ann = annual_panel(panel)

    out = {"meta": {"stations": int(ann["站代码"].nunique()),
                    "years": [int(ann["年"].min()), int(ann["年"].max())],
                    "train": "2015—2022", "test": "2023—2024",
                    "Zr_m": ZR, "theta_fc": TH_FC, "S_fc_mm": S_FC,
                    "et_fraction": ET_FRAC}}

    rows, fits = [], {}
    print("[任务一] 年尺度标定 …", flush=True)
    for code, sub in ann.groupby("站代码"):
        sub = sub.sort_values("年").reset_index(drop=True)
        tr = sub[sub["年"] <= 2022].reset_index(drop=True)
        te = sub[sub["年"] >= 2023].reset_index(drop=True)
        K_fix = float(min(max(np.percentile(tr["V"].values, 95) * 1.15, 8.0), 70.0))
        p = fit_annual(tr, K_fix, seed=sum(ord(c) for c in code) % 977)
        Vtr, _ = sim_annual(tr, p)
        Vfull, _ = sim_annual(sub, p)
        pred_te = Vfull[len(tr):]
        obs_tr, obs_te = tr["V"].values, te["V"].values
        base = np.repeat(obs_tr[-1], len(obs_te))
        rows.append({"站代码": code, "r": round(float(p[0]), 3), "K": round(float(p[1]), 2),
                     "d": round(float(p[2]), 4),
                     "R2_train": round(r2(obs_tr, Vtr), 3),
                     "RMSE_test": round(float(np.sqrt(np.mean((obs_te - pred_te) ** 2))), 2),
                     "RMSE_persist": round(float(np.sqrt(np.mean((obs_te - base) ** 2))), 2)})
        fits[code] = (tr, te, p, Vtr, pred_te, sub)
        print(f"  {code}: r={p[0]:.2f} K={p[1]:.1f} d={p[2]:.3f} R2tr={rows[-1]['R2_train']:+.3f} "
              f"1年RMSE={rows[-1]['RMSE_test']}(持续 {rows[-1]['RMSE_persist']})", flush=True)
    fdf = pd.DataFrame(rows)
    fdf.to_csv(os.path.join(RES, "model_v4_fit.csv"), index=False, encoding="utf-8-sig")
    t1 = {"fit": fdf.to_dict(orient="records"),
          "R2_train_median": float(fdf["R2_train"].median()),
          "n_beat_persist": int((fdf["RMSE_test"] < fdf["RMSE_persist"]).sum())}
    out["task1"] = t1

    best = fdf.sort_values("R2_train", ascending=False).iloc[0]["站代码"]
    tr, te, p_b, Vtr, pred_te, sub = fits[best]
    p_med = (float(fdf["r"].median()), float(fdf["K"].median()), float(fdf["d"].median()))
    fig, ax = plt.subplots(figsize=(7.4, 3.5))
    yrs = sub["年"].values
    ax.plot(yrs, sub["V"].values, "o-", ms=4, lw=1.2, color="#4C78A8", label="观测（年均）")
    ax.plot(yrs[:len(Vtr)], Vtr, "s--", ms=4, lw=1.1, color="#E45756", label="模型拟合")
    ax.plot(yrs[len(Vtr):], pred_te, "s--", ms=4, lw=1.1, color="#54A24B", label="模型外推")
    ax.axvline(2022.5, color="#888888", ls=":", lw=1)
    ax.set_xlabel("年份"); ax.set_ylabel("年均覆盖度（%）")
    ax.set_title(f"任务一：{best} 站（r={p_b[0]:.2f}, K={p_b[1]:.1f}, d={p_b[2]:.3f}）", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "figQ1_年尺度拟合.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print("[任务二] 动态规划 …", flush=True)
    r_b, K_b, d_b = p_med            # 代表区段参数 = 8 站中位数
    out["task1"]["rep_params"] = {"r": round(r_b, 3), "K": round(K_b, 2), "d": round(d_b, 4),
                                 "note": "任务二/三用 8 站标定参数的中位数作为代表区段参数"}
    base = dp(K=K_b, d=d_b, r=r_b)
    sens = []
    for key, vals in [("build", (1.5, 2.0, 2.5)), ("pv", (5.0, 8.0, 11.0)),
                      ("p_e", (0.10, 0.15, 0.25)), ("B", (3000, 4000, 5000)),
                      ("W_max", (300, 500, 700)), ("disc", (0.90, 0.94, 0.97))]:
        for v in vals:
            sc = dict(SC); sc[key] = v
            rr = dp(sc=sc, K=K_b, d=d_b, r=r_b)
            sens.append({"param": key, "value": v, "npv": round(rr["npv"], 1), "A_end": rr["A_end"]})
    # 投资结构敏感性：固定光伏占比/运维单价，重新优化面积与补水
    share_sweep = []
    for sv in (0.1, 0.2, 0.3, 0.4, 0.5):
        rr = dp(K=K_b, d=d_b, r=r_b, s_ctrl=(sv,))
        share_sweep.append({"pv_share": sv, "npv": round(rr["npv"], 1), "A_end": rr["A_end"]})
    maint_sweep = []
    for mv in (0.08, 0.12, 0.16, 0.20):
        sc = dict(SC); sc["maint"] = mv
        rr = dp(sc=sc, K=K_b, d=d_b, r=r_b)
        maint_sweep.append({"maint": mv, "npv": round(rr["npv"], 1), "A_end": rr["A_end"]})
    out["task2"] = {"station": best, "npv": round(base["npv"], 1), "path": base["path"],
                    "scen": SC, "sens": sens, "A_end": base["A_end"],
                    "share_sweep": share_sweep, "maint_sweep": maint_sweep}
    yrs = [x["year"] for x in base["path"]]
    fig, ax = plt.subplots(1, 2, figsize=(11.6, 3.6))
    ax[0].bar(yrs, [x["a"] for x in base["path"]], color="#4C78A8")
    ax[0].set_ylabel("年新增（千 hm²）"); ax[0].set_title("(a) 最优建设路径", fontsize=10)
    axb = ax[0].twinx(); axb.plot(yrs, [x["A"] for x in base["path"]], "-o", ms=3, color="#E45756")
    axb.set_ylabel("累计面积（千 hm²）", color="#E45756")
    for prm, mk in [("build", "o"), ("pv", "s"), ("p_e", "^")]:
        ys = [s["npv"] / 1e4 for s in sens if s["param"] == prm]
        ax[1].plot(range(3), ys, "-" + mk, ms=4, label=prm)
    ax[1].set_xticks(range(3)); ax[1].set_xticklabels(["低", "基准", "高"])
    ax[1].set_ylabel("NPV（亿元）"); ax[1].set_title("(b) 单因素敏感性", fontsize=10)
    ax[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "figQ2_路径.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print("[任务三] 吸收链 + 蒙特卡洛 …", flush=True)
    sweep = []
    for vc in (0.2, 0.3, 0.4, 0.5):
        mk_ = markov_resilience(K_b, d_b, r_b, v_crit=vc)
        mc_ = mc_resilience(K_b, d_b, r_b, v_crit=vc)
        sweep.append({"v_crit_ratio": vc, "thr": round(vc * K_b, 2),
                      "hit_markov": round(mk_["hit_at"], 3),
                      "hit_mc": round(mc_["hit_prob"], 3),
                      "tau_markov": round(mk_["tau_at"], 1),
                      "tau_mc": round(mc_["tau_median"], 1)})
    mk = markov_resilience(K_b, d_b, r_b, v_crit=0.4)
    mc = mc_resilience(K_b, d_b, r_b, v_crit=0.4)
    out["task3"] = {"K": K_b, "v_crit": mk["v_crit"], "lam": mk["lam"],
                    "tau_at": mk["tau_at"], "hit_markov": round(mk["hit_at"], 3),
                    "hit_mc": round(mc["hit_prob"], 3), "tau_mc": mc["tau_median"],
                    "sweep": sweep}
    fig, ax = plt.subplots(1, 2, figsize=(11.6, 3.6))
    ax[0].plot(mk["tau"], lw=1.2, color="#4C78A8")
    ax[0].set_xlabel("初始覆盖度分箱（由低到高）"); ax[0].set_ylabel("期望首达时间（月）")
    ax[0].set_title("(a) 吸收链期望首达时间", fontsize=10)
    ax[1].plot(mk["hitT"], lw=1.2, color="#54A24B", label="吸收链解析")
    ax[1].axhline(mc["hit_prob"], ls="--", color="#E45756", label=f"蒙特卡洛 {mc['hit_prob']:.2f}")
    ax[1].set_xlabel("初始覆盖度分箱"); ax[1].set_ylabel("300 月内退化概率")
    ax[1].set_title("(b) 解析解与 MC 交叉验证", fontsize=10); ax[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "figQ3_韧性.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)

    json.dump(out, open(os.path.join(RES, "model_v4.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=float)
    print("R2_train 中位:", t1["R2_train_median"], "| 胜过持续性:", t1["n_beat_persist"], "/8",
          "| NPV:", out["task2"]["npv"],
          "| P(解析):", out["task3"]["hit_markov"], " P(MC):", out["task3"]["hit_mc"], flush=True)


if __name__ == "__main__":
    main()
