# -*- coding: utf-8 -*-
"""make_reports_v2.py —— 生成两份 LaTeX 报告并用 tectonic 编译（用 @TOKEN@ 占位，不做 % 格式化）"""
import json
import os
import subprocess

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, "Results")
DOCS = os.path.join(BASE, "Reports")
os.makedirs(DOCS, exist_ok=True)

qa = json.load(open(os.path.join(RES, "qa_assessment.json"), encoding="utf-8"))
md = json.load(open(os.path.join(RES, "model_v2.json"), encoding="utf-8"))
panel = pd.read_csv(os.path.join(BASE, "Data", "processed", "panel_v2.csv"), encoding="utf-8-sig")
fit = pd.read_csv(os.path.join(RES, "model_fit_by_station.csv"), encoding="utf-8-sig")
TECT = r"C:\Users\zrq20\tectonic\tectonic.exe"

PRE = r"""\documentclass[11pt,a4paper]{ctexart}
\usepackage[margin=2.2cm]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{booktabs,tabularx,array}
\usepackage{graphicx}
\usepackage{float}
\usepackage{hyperref}
\hypersetup{colorlinks=true,linkcolor=blue,urlcolor=blue}
\setlength{\parindent}{2em}
\setlength{\parskip}{0.25em}
\renewcommand{\arraystretch}{1.12}
\newcommand{\src}[1]{\textsuperscript{\scriptsize [#1]}}
\title{@TITLE@}
\author{CQU\_MCM 2026 · B 题《治沙是一项精细活》}
\date{2026-11-09}
\begin{document}
\maketitle
\thispagestyle{empty}
\newpage
"""


def R(tpl, **kw):
    for k, v in kw.items():
        tpl = tpl.replace("@" + k + "@", str(v))
    return tpl


def esc(x):
    t = str(x)
    t = t.replace(chr(92) + "%", "@PCT@").replace("%", chr(92) + "%")
    t = t.replace("@PCT@", chr(92) + "%")
    if "$" not in t:                      # 纯文本单元：转义下划线等
        t = t.replace("_", chr(92) + "_").replace("&", chr(92) + "&")
    return t


def tab(header, rows, widths=None, caption="", font=r"\small"):
    n = len(header)
    widths = widths if widths else ["X"] * n
    spec = "|" + "|".join(widths) + "|"
    body = []
    for i, row in enumerate([header] + list(rows)):
        body.append(" & ".join(esc(x) for x in row) + chr(92) + chr(92))
        if i == 0:
            body.append(chr(92) + "midrule")
    env = "tabularx" if "X" in widths else "tabular"
    if env == "tabularx":
        begin = chr(92) + "begin{tabularx}{" + chr(92) + "textwidth}{" + spec + "}"
        end = chr(92) + "end{tabularx}"
    else:
        begin = chr(92) + "begin{tabular}{" + spec + "}"
        end = chr(92) + "end{tabular}"
    cap = ((chr(92) + "begin{center}" + chr(92) + "small " + caption
            + chr(92) + "end{center}")) if caption else ""
    return chr(10).join([
        chr(92) + "begin{table}[H]" + chr(92) + "centering" + font
        + chr(92) + "setlength{" + chr(92) + "parskip}{1pt}",
        begin,
        chr(92) + "toprule",
        chr(10).join(body),
        chr(92) + "bottomrule",
        end,
        cap,
        chr(92) + "end{table}"])


# ---------------------------------------------------------------- 预处理报告
def build_preprocess():
    st = qa["qa_sampling"]
    rows_qa = [[c, v["composites"], str(round(v["qa_gt1_ratio"] * 100, 2)) + r"\%",
                v["months_with_qa"], v["mean_abs_diff_pp"], v["max_abs_diff_pp"]]
               for c, v in st.items()]
    t_qa = tab(["站点", "合成期数", "QA$>$1 比例", "有效月份", "月均差异(pp)", "最大差异(pp)"],
               rows_qa, widths=["c"] * 6,
               caption="表 1  MOD13Q1 像元可靠性抽样评估（TZ、XT 完整，QM 部分）")
    t_miss = tab(["字段", "缺失数"], [[k, v] for k, v in qa["missing"].items()],
                 widths=["c", "c"], caption="表 2  面板缺失统计")
    t_step = tab(["步骤", "处理", "依据"], [
        ["S1", "气象单一口径", "NASA POWER 月度产品，7 参数一次取齐，附 SHA256"],
        ["S2", "单位换算", "mm/d→mm/月（按当月天数）；kWh/m²/d→MJ/m²/d"],
        ["S3", "NDVI 有效性", "剔除填充值 −3000"],
        ["S4", "替代质控", "相对训练期同月气候态 $|z|>3$ 标记可疑"],
        ["S5", "月最大合成", "同月多期取最大，抑制云与阴影"],
        ["S6", "覆盖度换算", "像元二分，固定端元 0.05 / 0.85"],
        ["S7", "侵蚀指数", "Lettau 单位宽度通量，训练期均值归一"],
        ["S8", "ET$_0$", "Hargreaves 原式，$R_a$ 按纬度与日序计算"],
        ["S9", "湿度归一", "根区湿度按训练期 5%/90% 分位线性归一"],
        ["S10", "时间切分", "训练 2015-01—2022-12；测试 2023-01—2024-12"],
        ["S11", "缺失处理", "站内线性插值（限 3 期）+ 训练期同月气候态"],
        ["S12", "留痕", "面板、特征、统计量、QA 抽样表全部落盘"],
    ], widths=["c", "X", "X"], caption="表 3  预处理流程")
    t_var = tab(["变量", "含义", "单位", "来源"], [
        ["$P_t$", "月降水量", "mm", r"POWER\src{观测}"],
        ["$T_t,T^{\max}_t,T^{\min}_t$", "月均/最高/最低气温", r"$^\circ$C", r"POWER\src{观测}"],
        ["$R_{s,t}$", "短波辐射", r"MJ m$^{-2}$ d$^{-1}$", r"POWER\src{观测}"],
        ["$u_t$", "10 m 风速", r"m s$^{-1}$", r"POWER\src{观测}"],
        ["$W_t$", "根区湿度（0—1）", "—", r"POWER(GWETROOT)\src{观测}"],
        [r"$\mathrm{NDVI}_t$", "归一化植被指数", "—", r"MODIS MOD13Q1\src{观测}"],
        ["$V_t$", "植被覆盖度", r"\%", r"由 NDVI 反演\src{派生}"],
        ["$E_t$", "侵蚀指数（无量纲）", "—", r"由 $u_t$ 计算\src{派生}"],
        [r"$\mathrm{ET}_{0,t}$", "参考蒸散", "mm", r"Hargreaves\src{派生}"],
    ], widths=["c", "X", "c", "X"], caption="表 4  面板变量与来源")

    body = r"""
\section*{摘\quad 要}
本报告说明建模数据的来源、质量控制与预处理流程。与上一版相比有三项结构性修正：
（1）气象统一到 NASA POWER 单一口径并保存原响应哈希，不再混用未指定模型的再分析产品；
（2）不再按文献量级人为设定各站输沙率目标，风蚀改以\textbf{无量纲侵蚀指数} $E$ 进入模型；
（3）插补、截尾、标准化、共线性筛选\textbf{只在训练期拟合}，测试期不参与任何拟合。
NDVI 官方 QA 波段仅在两站完整取得，本报告用它量化了 QA 对月最大合成的影响。

""" + t_step + t_var + t_qa + t_miss + r"""
\section*{一、数据来源}
\subsection*{1.1 气象与地表参数}
全部气象要素取自 NASA POWER 官方 API 月度产品（8 个坐标点 $\times$ 120 个月，2015—2024）：
\texttt{PRECTOTCORR}、\texttt{T2M}/\texttt{T2M\_MAX}/\texttt{T2M\_MIN}、\texttt{WS10M}、
\texttt{ALLSKY\_SFC\_SW\_DWN}、\texttt{GWETROOT}。每个请求的 URL、返回字节数与 SHA256
记录在 \texttt{Data/raw/nasa\_power\_verified/manifest\_v2.json}，可逐请求复核。
\textbf{必须强调}：POWER 是同化/再分析产品，不是地名对应站的仪器观测，正文一律称“再分析产品”。

\subsection*{1.2 遥感植被指数}
NDVI 取自 ORNL DAAC 的 MOD13Q1 子集服务（250 m、16 天合成），单像元（\texttt{kmAboveBelow=0}），
因此覆盖度代表\textbf{站点尺度}而非区段平均；全部合成期的原始响应保存在本地缓存，可重跑复现。

\subsection*{1.3 工程与文献证据}
两份政府/林草部门公开网页（民丰后河坝三期、于田—民丰锁边固沙工程）保存了原文与 SHA256。
提取的 5 条工程参数（芦苇方格 1.5 m；果树密度 66 株/亩 = 990 株/hm$^2$；
成本节约 964 元/亩 = 14\,460 元/hm$^2$；民丰生物治沙 13 万亩；于田工程固沙 10.5 万亩）
记录在 \texttt{parameters.csv}。使用边界很严格：\textbf{节约额不是单价}，\textbf{规划面积不是已完成面积}。

\section*{二、质量控制}
\subsection*{2.1 NDVI 像元可靠性}
表 1 显示：TZ、XT 两站 QA$>$1 的合成期比例均为 0.87\%，过滤前后\textbf{月最大合成几乎不变}
（月均绝对差 0.00 pp，最大 0.55 pp）；QM 站 QA$>$1 比例 15.2\%，过滤后月均差 0.08 pp、最大 2.29 pp。
\textbf{结论}：对“月最大合成”口径，QA 过滤的边际影响很小（最大合成本身倾向选取最清晰观测），
但对单期 NDVI 不可忽略。因此全序列采用替代质控：相对训练期同月气候态 $|z|>3$ 记为可疑，
共标记 @NFLAG@ 个站点-月，按缺失处理并插补。

\subsection*{2.2 缺失与异常}
原始 8 站 $\times$ 120 月 = 960 行的气象字段无缺失；覆盖度经替代质控后缺失 @NQC@ 个。
\textbf{不做事先截尾}：本题需要保留沙尘暴等极端月，一律截尾会削弱风蚀与灾害识别；
异常值只标记、不删除，标准化用中位数/四分位距抗极端值。

\section*{三、派生变量}
\subsection*{3.1 植被覆盖度（像元二分）}
\begin{equation*}
V_t=\mathrm{clip}\!\left(\frac{\mathrm{NDVI}_t-\mathrm{NDVI}_{soil}}
{\mathrm{NDVI}_{veg}-\mathrm{NDVI}_{soil}},0,1\right)\times 100\%,
\qquad \mathrm{NDVI}_{soil}=0.05,\ \mathrm{NDVI}_{veg}=0.85
\end{equation*}
固定端元便于跨站比较；另以各站训练期 5%/95% 分位作动态端元计算 $V^{\mathrm{dyn}}$ 作敏感性口径。
端元取固定值是可检验的假设，取得地表分类与纯端元像元后应替换。

\subsection*{3.2 侵蚀指数（无量纲）}
Lettau 公式给出的 $q$ 是\textbf{单位宽度}质量通量（kg m$^{-1}$ s$^{-1}$）：
\begin{equation*}
q_t=C\frac{\rho}{g}u_{*t}^2\left(u_{*t}-u_{*T}\right),\qquad
u_{*t}=\frac{\kappa u_t}{\ln(10/z_0)}
\end{equation*}
$C=6.7$、$\kappa=0.40$、$z_0=1$ mm、阈值由 10 m 高度 5 m/s 换算；$u_t$ 为月均风速乘阵风代理 1.8
（\src{情景}，敏感 1.5—2.2）。换算面积模数需“宽度/面积/时长”三个额外定义，\textbf{本轮不做}，
以免量纲不闭合；改用站内归一的无量纲指数 $E_t=q_t/\overline{q}_{2015\text{—}2022}$，
只表达相对风蚀强度。

\subsection*{3.3 参考蒸散与水分状态}
\begin{equation*}
\mathrm{ET}_0=0.0023\,R_a\,(T+17.8)\sqrt{T^{\max}-T^{\min}}\;d_m
\end{equation*}
$R_a$ 为天文辐射（按纬度与日序解析计算），$d_m$ 为当月天数。水分状态直接使用 \texttt{GWETROOT}，
按训练期 5%/90% 分位归一为 $W_t\in[0,1]$，避免自造水桶的量纲问题。

\section*{四、面板结构与划分}
平衡面板 @NROWS@ 行，训练期 @NTR@ 行（2015-01—2022-12）、测试期 @NTE@ 行（2023-01—2024-12）。
插补气候态、$W$ 归一化分位、$E$ 归一基准、标准化参数、共线性筛选\textbf{全部只用训练期}估计。

\section*{五、局限}
\begin{itemize}
\item 8 个坐标点是区域点位，不是等距锁边带样带；塔中为腹地背景点，肖塘与塔中直线距离约 36 km，
不能声称“各站均代表边缘”，代表区段边界仍需 GIS 划定。
\item NDVI 为单像元、固定端元，官方 QA 仅两站完整；覆盖度适合时序分析，不宜当作地面实测。
\item 根区湿度为再分析量，土壤有效水、盐分、地下水位未纳入。
\item 输沙量、工程单价、电价、可用水量均为情景假设或部分外部证据，不能当作已测定真值。
\end{itemize}

\end{document}
"""
    txt = R(PRE.replace("@TITLE@", "数据预处理报告（修订版）") + body,
            NFLAG=qa["ndvi_flag_counts"].get("climatology_outlier", 0),
            NQC=qa["missing"]["NDVI_qc"], NROWS=qa["rows"],
            NTR=int((panel["split"] == "train").sum()),
            NTE=int((panel["split"] == "test").sum()))
    p = os.path.join(DOCS, "preprocess.tex")
    open(p, "w", encoding="utf-8").write(txt)
    return p


# ---------------------------------------------------------------- 建模报告
def build_model():
    t1, t2, t3 = md["task1"], md["task2"], md["task3"]
    rows_fit = [[r["站代码"], r["Vcap"], r["R2_h1_train"], r["R2_h1_test"], r["RMSE_h1"],
                 r["RMSE_h12"], r["RMSE_h12_persist"], r["g"], r["m"], r["k"]]
                for _, r in fit.iterrows()]
    t_fit = tab(["站", "$V_{cap}$", "$R^2_1$(训)", "$R^2_1$(测)", "RMSE$_1$", "RMSE$_{12}$",
                 "持续基线", "$g$", "$m$", "$k$"], rows_fit, widths=["c"] * 10,
                font=r"\footnotesize", caption="表 2  任务一逐站标定与检验")
    t_sym = tab(["符号", "含义", "单位", "来源"], [
        ["$V_t$", "植被覆盖度", r"\%", r"MODIS 反演\src{观测}"],
        ["$W_t$", "根区湿度（归一）", "—", r"POWER\src{观测}"],
        ["$E_t$", "侵蚀指数", "—", r"$u_t$ 派生\src{派生}"],
        ["$V_{cap}$", "承载上限（训练期 95% 分位）", r"\%", "由数据确定"],
        ["$g$", "内在增长率", r"月$^{-1}$", "标定"],
        ["$m$", "衰亡率（平衡态锚定）", r"月$^{-1}$", "标定"],
        ["$k$", "风蚀损伤系数", "—", r"标定，约束 $k\ge0$"],
        ["$A_t$", "累计治理面积", r"千 hm$^2$", "决策状态"],
        ["$a_t$", "年新增面积", r"千 hm$^2$/a", "决策变量"],
        ["$I_t$", "年灌溉深度", "mm/a", "决策变量"],
        ["$\\delta$", "贴现因子", "—", r"情景 0.94"],
    ], widths=["c", "X", "c", "X"], caption="表 1  主要符号与来源")
    rows_grid = [[g["build"], g["pv_rev"], g["npv"], g["a1"], g["cum"]] for g in md["task2_grid"]]
    t_grid = tab(["$c_b$(万元/hm$^2$)", "$p_{pv}$(万元/hm$^2$a)", "NPV(万元)", "首年新增", "末年累计"],
                 rows_grid, widths=["c"] * 5, caption="表 4  任务二盈亏网格（其余情景参数不变）")
    rows_g3 = [[c["lam"], c["u_hi"], c["P_end_below_half"], c["end_median"]]
               for row in md["task3_grid"] for c in row]
    t_g3 = tab([r"$\lambda$(次/a)", r"$u_{\max}$", r"$P(V_{2050}<0.5V_{cap})$", r"2050 中位(\%)"],
               rows_g3, widths=["c"] * 4,
               caption="表 5  任务三情景网格（冲击幅度无实测标定）")
    rows_audit = [
        ["输沙率被设为目标", "逐站贴近 400—3200", "取消目标，改无量纲侵蚀指数"],
        ["Lettau 量纲", "kg m$^{-1}$s$^{-1}$ 换成 t km$^{-2}$", "明确为单位宽度通量，仅站内归一"],
        ["水分量纲", "体积含水率与 mm 混用", "改用观测根区湿度 0—1"],
        ["ET$_0$ 名不副实", "线性温度代理", "Hargreaves 原式，$R_a$ 解析"],
        ["训练/测试泄漏", "全期拟合", "训练标定、测试评估，插补归一仅训练期"],
        ["任务二未用任务一", "手设 $V(A)$", "由任务一方程解析求 $V_{eq}$"],
        ["运维单位", "少乘 1000", "单位统一，逐项复核"],
        ["韧性指标", "月滞后当年恢复、$\\lambda$ 硬编码", "$\\lambda$ 由超额频率估计，恢复右删失"],
        ["长期情景", "趋势未进入计算", "气温、风速增量显式进入 $E_t$ 与 $f(T)$"],
        ["验收标准倒置", "以期望 R$^2$、收益作验收", "删除验收指标，改为检验与限定"],
    ]
    t_audit = tab(["审计意见", "原问题", "本版处理"], rows_audit, widths=["c", "X", "X"],
                  font=r"\footnotesize", caption="表 6  审计意见与本版处理对照")

    body = r"""
\section*{摘\quad 要}
本报告给出三问的模型、参数、约束、求解与检验。与上一版相比删除全部时间安排与交付清单，
并按 2026-11-09 审计意见修正四处结构性错误：水分状态改用观测根区湿度；风蚀改无量纲指数、
\textbf{不再宣称}绝对输沙量；拟合只在训练期进行并与两条基线比较；任务二的最优控制
\textbf{真正调用}任务一方程求稳态覆盖度。

三条结论都附适用条件：
\begin{itemize}
\item 任务一一步预测在 8 站中 @NPOS@ 站为正技能（测试期 $R^2_{h=1}$ 中位 @R2MED@），
但 $h\ge6$ 个月后误差超过持续性基线，\textbf{故模型只用于情景比较，不用于多年点预测}；
\item 风蚀项系数在月尺度被标定到边界 0（全部站点），说明月际风蚀变化解释力不足，
该项在结构中保留为待识别项，\textbf{这也是任务二“减蚀效益”只能按情景给出的原因}；
\item 任务二的 NPV 与光伏盈亏点随单价情景显著移动（表 4），报告只给决策规则与区间，
不给“优于对照若干倍”一类结论。
\end{itemize}

""" + t_sym + r"""
\section*{一、假设}
\begin{enumerate}
\item \textbf{尺度}：以站点为控制体，水平均匀；覆盖度由局地水分、温度、风蚀驱动。
\item \textbf{水分}：根区湿度 $W$ 为主要限制因子，可由再分析根区湿度代理（\src{观测}）；
灌溉按有效水容量 $\mathrm{AWC}=1000Z_r(\theta_{fc}-\theta_{wp})$ 换算为 $W$ 的增量（\src{情景}）。
\item \textbf{风蚀}：损伤与侵蚀指数、覆盖度成正比（$kEV$），$k\ge0$。
\item \textbf{经济}：建设、运维、水价、光伏收益、生态价值均为情景参数；预算与水量为约束上限。
\item \textbf{随机性}：事件为泊松过程，强度服从均匀分布（\src{情景}），频率由实测超额频率估计。
\end{enumerate}

\section*{二、任务一：植被—水分耦合动力学}
\subsection*{2.1 方程}
\begin{equation}
\frac{dV}{dt}=gV\left(1-\frac{V}{V_{cap}}\right)W\,f(T)-mV-kEV,
\qquad f(T)=\mathrm{clip}\!\left(\frac{T-5}{20},0,1\right)
\end{equation}
$W$ 已归一，$a$ 与 $g$ 共线，故取 $a=1$。离散化为月步长
\begin{equation}
V_{t+1}=V_t+gV_t\left(1-\frac{V_t}{V_{cap}}\right)W_t-mV_t-kE_tV_t
\end{equation}

\subsection*{2.2 标定：平衡态锚定}
四参数全自由拟合会出现“一步准、长期崩”。令模型年平衡态等于实测多年均值 $\bar V$：
\begin{equation}
m=g\,\overline{Wf(T)}\left(1-\frac{\bar V}{V_{cap}}\right)-k\bar E,\qquad
\overline{Wf(T)}=\frac{1}{12}\sum_{m=1}^{12}W_m f(T_m)
\end{equation}
用\textbf{月气候态乘积}而非年均值乘积：干旱区“湿在冬、暖在夏”反相，用年均会系统性高估生长。
于是只剩 $g,k$ 自由，以一步预测残差最小化为目标、约束 $g>0,k\ge0$，仅用训练期。

\subsection*{2.3 检验}
""" + t_fit + r"""
\begin{figure}[H]\centering
\includegraphics[width=0.95\textwidth]{figs/figM1.png}
\begin{center}\small 图 1  @BEST@ 站的观测与一步递推（左）以及技能随预报步长的衰减（右）\end{center}
\end{figure}

\textbf{解读}：（i）训练与测试的一步技能接近，无明显过拟合；（ii）8 站 $k$ 全部落在下界 0，
月尺度风蚀项不可识别；（iii）$h=12$ 的 RMSE 中位 @RM12@，大于持续性基线 @RMP12@，
\textbf{自由推进一年以上没有技能}，故长期推演一律以情景为条件。

\section*{三、任务二：情景约束下的最优建设路径}
\subsection*{3.1 决策、状态与约束}
\begin{align}
&\text{预算：} c_b\cdot1000a_t+c_m\cdot1000A_t+c_w\frac{I_t}{100}\cdot1000a_t\le B\\
&\text{水量：} \frac{I_t}{1000}\cdot1000a_t\times10^4\le W_{\max}\\
&\text{土地：} A_{t+1}=A_t+a_t,\qquad A_t\le A_{pot}
\end{align}
\subsection*{3.2 稳态响应（由任务一方程给出）}
\begin{equation}
V_{eq}(E,W)=\mathrm{clip}\!\left[V_{cap}\left(1-\frac{m+kE}{g\,\overline{Wf(T)}\,(W/W_0)}\right),0,V_{cap}\right],
\qquad E(A)=E_0\left(1-\beta\frac{A}{A_{pot}}\right)
\end{equation}
灌溉增湿比 $W/W_0$ 由 $\mathrm{AWC}\approx@AWC@$ mm 换算（$Z_r=@ZR@$ m，$\theta_{fc}=@TFC@$、$\theta_{wp}=@TWP@$，\src{情景}）。
\subsection*{3.3 目标与递推}
\begin{equation}
\max_{\{a_t\}}\sum_{t=0}^{T-1}\delta^t\left[p_{pv}s\cdot1000a_t+p_e\frac{V_{eq}}{V_{cap}}\cdot1000A_t-c_b\cdot1000a_t-c_m\cdot1000A_t-c_w\frac{I_t}{100}\cdot1000a_t\right]
\end{equation}
\begin{equation}
J_t(A)=\max_{a\in\{0,0.5,1,1.5,2\}}\left\{r(A,a)+\delta J_{t+1}(A+a)\right\},\qquad J_T=0
\end{equation}
\subsection*{3.4 结果}
基准情景（$c_b=2.0$、$p_{pv}=8$、$s=0.30$、$B=4000$、$T=15$、$\delta=0.94$）：
最优 NPV $=@NPV@$ 万元，均匀扩张对照 $=@NPVU@$ 万元；最优路径首年新增 @A1@ 千 hm$^2$、
末年累计 @CUM@ 千 hm$^2$；光伏占比盈亏点 $s^*\approx@BE@$。
\begin{figure}[H]\centering
\includegraphics[width=0.95\textwidth]{figs/figM3.png}
\begin{center}\small 图 2  情景参数下的最优建设路径（左）与光伏占比敏感性（右）\end{center}
\end{figure}

\textbf{这些数字都是同一情景下的相对比较，不构成投资结论}。表 4 显示 NPV 对单价与光伏收益高度敏感，
网格中存在大片“零新增”区域（NPV$=0$，即不做优于做）——上一版“优于对照 2.2 倍”的结论只在单点情景下成立。

""" + t_grid + r"""
\section*{四、任务三：事件冲击下的韧性}
\subsection*{4.1 事件与冲击}
\begin{equation}
\lambda=\frac{\#\{t:E_t\ge E_{95}\}}{N_{\text{years}}},\qquad
V_{t^+}=V_t(1-U),\quad U\sim\mathcal{U}(0.20,0.55)\ \text{\src{情景}}
\end{equation}
本次 $\lambda=@LAM@$ 次/年（训练期 $E_{95}=@E95@$）。恢复由任务一方程驱动，
恢复时间定义为回到冲击前 90\% 所需月数，未恢复按右删失处理。
\subsection*{4.2 气候情景}
2026—2050：气温每年 $+0.03^\circ$C，风速每年 $+0.2\%$（均\src{情景}），经 $E_t$ 与 $f(T)$ 进入模型。
\subsection*{4.3 结果}
基准情景：模拟期任一时刻跌破 $0.5V_{cap}$ 的概率 @FAIL@，2050 年覆盖度中位 @END@\%
（5\%—95\% 分位 @P05@—@P95@\%），中位恢复时间 @REC@ 个月。
由于冲击幅度无实测标定，表 5 给出网格：$\lambda=0.25$、$u_{\max}=0.30$ 时中位仍达 27\%、
一半情景低于阈值；$\lambda\ge0.75$ 时几乎全部退化。\textbf{故本问只给条件结论}，
不给“失效概率 84\%”这类单点数字。

""" + t_g3 + r"""
\begin{figure}[H]\centering
\includegraphics[width=0.95\textwidth]{figs/figM4.png}
\begin{center}\small 图 3  1000 次模拟的 2050 年覆盖度分布（左）与冲击—恢复轨迹带（右）\end{center}
\end{figure}

\section*{五、检验与稳健性}
\begin{enumerate}
\item 样本外一步预测：@NPOS@/8 站为正技能（表 2）。
\item 基线对照：持续性、季节气候态；$h=12$ 不优于持续性，已在结论中限定使用范围。
\item 情景敏感性：任务二对 $c_b$、$p_{pv}$、$s$ 做网格（表 4）；任务三对 $\lambda$、$u_{\max}$ 做网格（表 5）。
\item 不做的事：不把情景参数当实测值；不在无事件标定时发布概率结论；不用期望结果反向筛选模型。
\end{enumerate}

""" + t_audit + r"""
\section*{六、局限}
\begin{itemize}
\item 代表区段边界未划定，模型为站点尺度；塔中为腹地背景点，不能代表锁边带。
\item 风蚀项月尺度不可识别（$k=0$），任务二减蚀效益纯属情景设定。
\item 经济参数缺本地依据，NPV 只作相对比较；冲击幅度与恢复过程无实测标定。
\item 覆盖度端元固定、单像元取样，绝对水平有系统偏差，时序比较受影响较小。
\end{itemize}

\end{document}
"""
    txt = R(PRE.replace("@TITLE@", "建模报告（修订版）") + body,
            NPOS=t1["n_positive_h1"], R2MED=t1["R2_h1_test_median"],
            RM12=t1["RMSE_h12_median"], RMP12=t1["RMSE_h12_persist_median"],
            AWC=round(float(md["meta"]["AWC_mm"]), 1), ZR=md["meta"]["Zr_m"],
            TFC=md["meta"]["theta_fc"], TWP=md["meta"]["theta_wp"],
            NPV=t2["npv"], NPVU=t2["npv_uniform"], A1=t2["path"][0]["a_khm2"],
            CUM=t2["path"][-1]["cum_khm2"], BE=t2["break_even_pv_share"],
            LAM=t3["lambda_per_year"], E95=t3["E_p95"], FAIL=t3["fail_prob"],
            END=t3["end_median"], P05=t3["end_p05"], P95=t3["end_p95"],
            REC=t3["recov_median_months"], BEST=t2["station"])
    p = os.path.join(DOCS, "model.tex")
    open(p, "w", encoding="utf-8").write(txt)
    return p


def compile_tex(path):
    r = subprocess.run([TECT, "-X", "compile", os.path.basename(path)],
                       cwd=os.path.dirname(path), capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    ok = r.returncode == 0
    print(os.path.basename(path), "→", "ok" if ok else "FAIL")
    if not ok:
        print(r.stderr[-1200:])
    return ok


if __name__ == "__main__":
    a = build_preprocess()
    b = build_model()
    compile_tex(a)
    compile_tex(b)
