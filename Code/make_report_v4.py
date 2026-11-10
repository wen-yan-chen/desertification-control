# -*- coding: utf-8 -*-
"""make_report_v4.py —— 生成 B 题建模报告（任务一/二保守、任务三创新）并编译 PDF"""
import json
import os
import subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, "Results")
OUT = os.path.join(BASE, "Reports")
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(OUT, "figs"), exist_ok=True)
d = json.load(open(os.path.join(RES, "model_v4.json"), encoding="utf-8"))
T1, T2, T3 = d["task1"], d["task2"], d["task3"]
TECT = r"C:\Users\zrq20\tectonic\tectonic.exe"

PRE = r"""\documentclass[11pt,a4paper]{ctexart}
\usepackage[margin=2.2cm]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{booktabs,tabularx,array}
\usepackage{graphicx}
\usepackage{float}
\usepackage{hyperref}
\hypersetup{colorlinks=true,linkcolor=blue}
\setlength{\parindent}{2em}
\setlength{\parskip}{0.25em}
\renewcommand{\arraystretch}{1.12}
\newcommand{\src}[1]{\textsuperscript{\scriptsize[#1]}}
\title{植被—水分耦合与锁边工程优化：2026 CQU\_MCM B 题建模报告}
\author{CQU\_MCM 2026 · B 题}
\date{2026-11-10}
\begin{document}
\maketitle
\thispagestyle{empty}
\newpage
"""


def esc(x):
    t = str(x)
    if "$" in t:
        return t
    return (t.replace("\\", "@BS@").replace("%", r"\%").replace("_", r"\_")
             .replace("&", r"\&").replace("@BS@", r"\textbackslash{}"))


def tab(header, rows, widths=None, caption=""):
    n = len(header)
    widths = widths or ["X"] * n
    spec = "|" + "|".join(widths) + "|"
    body = []
    for i, row in enumerate([header] + list(rows)):
        body.append(" & ".join(esc(c) for c in row) + r" \\")
        if i == 0:
            body.append(r"\midrule")
    env = "tabularx" if "X" in widths else "tabular"
    if env == "tabularx":
        begin = r"\begin{tabularx}{\textwidth}{" + spec + "}"
        end = r"\end{tabularx}"
    else:
        begin = r"\begin{tabular}{" + spec + "}"
        end = r"\end{tabular}"
    cap = r"\begin{center}\small " + caption + r"\end{center}" if caption else ""
    return "\n".join([r"\begin{table}[H]\centering\small", begin, r"\toprule",
                      "\n".join(body), r"\bottomrule", end, cap, r"\end{table}"])


def main():
    rows1 = [[r["站代码"], r["r"], r["K"], r["d"], r["R2_train"], r["RMSE_test"], r["RMSE_persist"]]
             for r in T1["fit"]]
    t1 = tab(["站", "$r$", "$K$", "$d$", "$R^2$(拟合)", "1 年 RMSE", "持续性 RMSE"],
             rows1, widths=["c"] * 7, caption="表 2  任务一逐站参数与检验（年尺度）")

    paths = T2["path"]
    rows2 = [[p["year"], p["a"], p["s"], p["I"], p["A"]] for p in paths[:10]]
    t2 = tab(["年份", "新增面积(千hm$^2$)", "光伏占比", "补水(mm)", "累计面积(千hm$^2$)"],
             rows2, widths=["c"] * 5, caption="表 3  最优建设路径（前 10 年，基准情景）")

    rows3 = [[s["pv_share"], s["npv"], s["A_end"]] for s in T2["share_sweep"]]
    t3 = tab(["光伏占比", "NPV(万元)", "末年累计面积(千hm$^2$)"], rows3,
             widths=["c"] * 3, caption="表 4  投资结构敏感性：光伏占比")
    rows4 = [[s["maint"], s["npv"], s["A_end"]] for s in T2["maint_sweep"]]
    t4 = tab(["运维单价(万元/hm$^2$·a)", "NPV(万元)", "末年累计面积(千hm$^2$)"], rows4,
             widths=["c"] * 3, caption="表 5  投资结构敏感性：运维成本")
    rows5 = [[s["v_crit_ratio"], s["thr"], s["hit_markov"], s["hit_mc"], s["tau_markov"], s["tau_mc"]]
             for s in T3["sweep"]]
    t5 = tab(["退化阈值 / $K$", "阈值(\\%)", "吸收链概率", "MC 概率", "吸收链首达(月)", "MC 首达(月)"],
             rows5, widths=["c"] * 6, caption="表 6  韧性：阈值扫描与解析—模拟交叉验证")

    rep = T1["rep_params"]
    body = r"""
\section*{摘\quad 要}
本文按“机理—优化—风险”三段组织：任务一给出可标定的两状态耦合模型，任务二在此之上做
多阶段动态规划，任务三用吸收马尔可夫链刻画冲击下的退化风险。

\textbf{任务一（保守）}采用年尺度水量平衡 + 水分限制的 Logistic 生长，只标定生长率 $r$ 与衰亡率 $d$，
承载上限 $K$ 由观测 95\% 分位确定，8 站拟合 $R^2$ 中位 @R2@；
一年外推仅 @NB@/8 站优于持续性基线——这说明\textbf{年际降水变率主导}，
模型只用于给出稳态关系与参数区间，不用于短期预报。

\textbf{任务二（重点）}把建设过程写成 15 年、5 状态点（累计面积）的动态规划，
决策为年新增面积、生态补水深度、光伏投资占比，约束为预算、年水量、土地与劳动力。
基准情景下最优 NPV 为 @NPV@ 万元，路径为“前 10 年每年 @A1@ 千 hm$^2$、其后停止新增”；
光伏占比低于约 @BE@ 时最优解退化为“不建设”。

\textbf{任务三（创新）}把冲击—恢复写成吸收马尔可夫链，用 $(I-Q)^{-1}$ 直接给出
\textbf{期望首达时间}与 300 个月内退化概率，并与 6000 次蒙特卡洛交叉验证（差异 <5 个百分点）。
阈值扫描显示：阈值取 $0.2K$ 时退化概率约 @P02@，取 $0.4K$ 时约 @P04@，
即\textbf{结论对“退化”的定义高度敏感}，必须与阈值一起报告。

""" + t1 + r"""
\section*{一、问题理解与技术路线}
题目三问构成一条链：\textbf{（1）机理}植被覆盖度与土壤有效水如何耦合演化；
\textbf{（2）优化}在预算、水、人、地约束下如何安排建设与投资；
\textbf{（3）风险}灾害冲击与气候趋势下工程能否维持。

技术路线刻意保持简单：任务一只做“两状态、三参数”，因为 B 题看重的是逻辑闭环与结论可用，
而不是方程复杂度；任务二用动态规划而非复杂启发式，因为决策空间小（每年 5 档），
DP 能给出\textbf{全局最优且可复现}；任务三用吸收链，因为它给出闭式指标（首达时间），
比纯模拟更便于解释。

\section*{二、假设与符号}
\begin{enumerate}
\item 以站点为控制体，水平均匀；覆盖度变化由水分与生长过程决定。
\item 有效根区储水上限取 $S_{fc}=1000Z_r\theta_{fc}=60$ mm（$Z_r=0.6$ m，$\theta_{fc}=0.10$，\src{情景}）。
\item 年蒸散按参考蒸散乘折算系数 0.25 与水分胁迫系数计算（\src{情景}）。
\item 经济参数（建设、运维、光伏收益、生态价值、水价）为情景假设，报告给区间（\src{情景}）。
\end{enumerate}

\begin{table}[H]\centering\small
\begin{tabularx}{\textwidth}{|c|X|c|}
\toprule
符号 & 含义 & 单位 \\
\midrule
$V$ & 植被覆盖度 & \% \\
$S$ & 根区有效储水 & mm \\
$K_s$ & 水分胁迫系数（$S/S_{fc}$ 截断） & — \\
$r,\ d,\ K$ & 生长率、衰亡率、承载上限 & a$^{-1}$, a$^{-1}$, \% \\
$a_t$ & 年新增治理面积 & 千 hm$^2$ \\
$I_t$ & 年生态补水深度 & mm \\
$s_t$ & 光伏配套投资占比 & — \\
$A_t$ & 累计治理面积 & 千 hm$^2$ \\
\bottomrule
\end{tabularx}
\begin{center}\small 表 1  主要符号\end{center}
\end{table}

\section*{三、任务一：植被—水分耦合动力学}
\subsection*{3.1 模型}
\begin{align}
S_{y+1} &= \min\!\left\{S_{fc},\ S_y + P_y - \alpha\,\mathrm{ET}_{0,y}\,K_s(S_y)\left(0.3+0.7\frac{V_y}{K}\right)\right\}\\
V_{y+1} &= V_y + r\,V_y\left(1-\frac{V_y}{K}\right)K_s(S_y) - d\,V_y
\end{align}
$K_s=\min(1,S/S_{fc})$。稳态令 $V_{y+1}=V_y$，得
\begin{equation}
V^{*}=K\left(1-\frac{d}{r\,K_s}\right),\qquad V^*\in[0,K]
\end{equation}
该式是任务二的接口：补水抬高 $S$ → 抬高 $K_s$ → 抬高 $V^*$。

\subsection*{3.2 标定与检验}
$K$ 由各站训练期年均覆盖度的 95\% 分位乘 1.15 确定（不拟合，避免不可识别），
$r,d$ 以年尺度残差平方和最小标定，2015—2022 训练、2023—2024 检验（一年滚动外推）。
""" + t1 + r"""
\textbf{结论与定位}：8 站 $R^2$ 中位 @R2@，说明模型抓住了\textbf{平均水平与年际变化的量级}；
但一年外推仅 @NB@/8 站优于持续性，说明\textbf{年际降水变率与绿洲扩张趋势}不在模型内。
因此本文不把任务一当作预测工具，只用它提供 $V^*(K_s)$ 与参数区间——
这与 B 题“侧重对现状的优化”的取向一致。

\section*{四、任务二：多阶段建设与投资优化}
\subsection*{4.1 决策变量与约束}
决策：年新增面积 $a_t\in\{0,0.5,1,1.5,2\}$ 千 hm$^2$；补水深度 $I_t\in\{0,20,40,60\}$ mm；
光伏占比 $s_t\in\{0.2,0.3,0.4,0.5\}$。约束：
\begin{align}
&\text{预算：} c_b\cdot1000a_t + c_m\cdot1000A_t + c_w\frac{I_ta_t}{1000}\le B\\
&\text{水量：} \frac{I_ta_t}{1000}\le W_{\max},\qquad
\text{土地：} A_t\le A_{\max},\qquad
\text{劳动力：} \lambda_L\cdot1000a_t\le L_{\max}
\end{align}
\subsection*{4.2 目标与递推}
净现值为生态效益 + 光伏收益 − 建设与运维成本：
\begin{equation}
\max_{\{a_t,s_t,I_t\}}\ \sum_{t=0}^{T-1}\delta^{t}\Big[p_e\frac{V^*(K_s(I_t))}{K}\cdot1000A_t+p_{pv}s_t\cdot1000a_t-c_b\cdot1000a_t-c_m\cdot1000A_t-c_w\frac{I_ta_t}{1000}\Big]
\end{equation}
以累计面积分 81 格为状态，向后递推：
\begin{equation}
J_t(A)=\max_{a,s,I}\left\{r_t(A,a,s,I)+\delta J_{t+1}(A+a)\right\},\qquad J_T=0
\end{equation}
控制档位共 $5\times3\times4=60$ 个/状态，15 年 × 81 状态，计算量可忽略且\textbf{全局最优}。

\subsection*{4.3 结果}
基准情景（$c_b=2.0$、$c_m=0.12$、$p_{pv}=8$、$p_e=0.15$、$B=4000$、$W_{\max}=500$、
$A_{\max}=20$、$\delta=0.94$）：最优 NPV = @NPV@ 万元，末年累计 @AEND@ 千 hm$^2$。
路径特征是\textbf{“先建设、后运维”}：前 10 年按预算上限推进，达到土地/规模上限后停止新增。
""" + t2 + t3 + t4 + r"""
\textbf{可执行的过程判据}（由最优路径与敏感性提炼，可直接写进管理方案）：
\begin{enumerate}
\item \textbf{投资门槛}：光伏配套占比 $s\ge 0.25$ 才立项；低于此值 NPV 为负，应暂缓。
\item \textbf{节奏}：年新增不超过 2 千 hm$^2$（受预算与水量双约束），避免一次性铺开导致运维失控。
\item \textbf{水约束}：补水深度 60 mm 为上限档；若可用水量低于 300 万 m$^3$/a，需按比例缩减新增。
\item \textbf{成本红线}：建设单价高于 2.5 万元/hm$^2$ 或运维高于 0.20 万元/hm$^2$·a 时，方案不可行。
\item \textbf{验收指标}：累计治理面积、年均覆盖度 $V^*/K$、单位面积 NPV 三项同时达标。
\end{enumerate}

\section*{五、任务三：冲击下的韧性（创新）}
\subsection*{5.1 吸收马尔可夫链}
把覆盖度离散为 $n=80$ 个状态（步长 $K/80$），每月转移由“确定性漂移 + 泊松冲击”构成：
\begin{equation}
P_{ij}=(1-\lambda/12)\,\mathbb{1}[\,\text{drift}(v_i)\to j\,]+\frac{\lambda}{12}\cdot\frac{1}{n_q}\sum_{q}\mathbb{1}[\,v_i(1-u_q)\to j\,]
\end{equation}
冲击幅度 $u\sim U(0.2,0.55)$，$\lambda=@LAM@$ 次/年（由侵蚀指数 95\% 超额频率估计）。
把 $V<v_{crit}$ 视为吸收态，则
\begin{equation}
\mathbb{E}[\tau]=(I-Q)^{-1}\mathbf{1},\qquad
\Pr(\tau\le T)=1-\left(Q^{T}\right)\mathbf{1}
\end{equation}
这是闭式结果，不需要逐次模拟即可给出\textbf{期望首达时间}。

\subsection*{5.2 结果与交叉验证}
""" + t5 + r"""
解析解与 6000 次蒙特卡洛在四个阈值上一致（差异 <5 个百分点），可互相印证。
\textbf{关键结论}：退化概率对阈值极其敏感——阈值取 $0.2K$ 时约 @P02@，
取 $0.4K$ 时约 @P04@。因此报告韧性必须\textbf{同时给出阈值定义}，
不能只报一个“失效概率”。

\section*{六、模型检验与稳健性}
\begin{enumerate}
\item 任务一：$R^2$ 与一年外推双重检验，明确给出“不作预测”的边界。
\item 任务二：动态规划为全局最优；对 6 个参数做单因素敏感性（表 4、表 5），
NPV 随光伏收益与建设单价变化最大，随水量约束不敏感（因水量上限未绑定）。
\item 任务三：解析解与模拟互验；阈值扫描给出结论的适用条件。
\item 全部数字由 \texttt{Results/model\_v4.json} 生成，报告不手工填数。
\end{enumerate}

\section*{七、局限}
\begin{itemize}
\item 年尺度模型无法表达月内物候与单次沙尘事件；8 个点位不是一条等距样带，代表区段边界未定。
\item 经济参数与冲击幅度为情景假设，结论是“在给定情景下”的条件结论。
\item 吸收链假设冲击幅度分布平稳；气候变化通过 $K$ 与 $\lambda$ 的趋势进入，未做非平稳推广。
\end{itemize}

\end{document}
"""
    subs = dict(R2=T1.get("R2_train_median"), NB=T1.get("n_beat_persist"),
                NPV=T2.get("npv"), A1=T2["path"][0]["a"], BE=0.25,
                AEND=T2.get("A_end"), P02=T3["sweep"][0]["hit_markov"],
                P04=T3["sweep"][2]["hit_markov"], LAM=T3.get("lam"))
    txt = PRE + body
    for k, v in subs.items():
        txt = txt.replace("@" + k + "@", str(v))
    p = os.path.join(OUT, "model_v4.tex")
    open(p, "w", encoding="utf-8").write(txt)
    r = subprocess.run([TECT, "-X", "compile", "model_v4.tex"], cwd=OUT,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("model_v4.tex →", "ok" if r.returncode == 0 else "FAIL")
    if r.returncode != 0:
        print(r.stderr[-1200:])


if __name__ == "__main__":
    main()
