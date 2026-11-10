# Model 1 rebuilt on v7 (2026-11-10) · 模型一 v7 重建

Code: `Code/v7_model1.py` (offline, about 10 s). Numbers: `Results/v7/model1/`. Figures: `Figures/v7/m1_fig1_*.png`, `m1_fig2_*.png`.
中文摘要见文末。

## 1. The model

The v7 state equation is kept exactly (`Reports/model_v7.tex`, Eq. t1), yearly step:

```
V[t+1] = V[t] + r·V·(1 − V/K)·W  −  d·V  −  k·E·(1 − η·V/K)·V
```

One relation is added so that water is actually coupled to cover:

```
W = min(1, A / (c · min(1, 2·fc) · ET0g))        A = η_w·I + G,   fc = V / V_full
```

W is usable water divided by what the canopy would transpire unstressed. I is gross irrigation (mm/yr), G groundwater supply, ET0g the temperature-weighted reference evapotranspiration Σ f(T)·ET0 = 1163 mm/yr on the section, fc the ground-cover fraction. Root-zone storage (about 75 mm) is small against yearly fluxes of hundreds of mm, so at a yearly step effective moisture follows supply and demand without a storage equation.

| Parameter | Value | Status |
|---|---|---|
| r | 0.584 ± 0.180 per year | fitted, pooled over 7 stations |
| d | 0.117 ± 0.035 per year | fitted, pooled over 7 stations |
| K | 1.15 × 95th percentile of training-period V, per site; 38.1 % for the section (YT, MF mean) | v7 rule, unchanged |
| k | 0 (estimate 0.00 ± 0.27) | **not identified**; scenario range 0–0.10 |
| η | 1 | fixed; not identifiable |
| c | 1.0 | assumption, range 0.7–1.2 (FAO-56 ch. 9) |
| η_w | 0.75 | assumption, range 0.65–0.85 |
| V_full | 66.6 % (v7 units) | from section oasis pixels, see C6 |

Without a water limit the steady state is x* = 1 − d/r = 0.80, the same closed form as v7 Eq. xstar with k = 0.

## 2. Check of the v7 Task 1, and the changes made

| # | Finding in v7 | Evidence | Change |
|---|---|---|---|
| C1 | Per-station fit of four parameters on 8 yearly points does not work | v7's own ablation: median training R² 0.004, 89 % of fits end on a bound, median d = 0 (`Results/v7/tab_ablation_summary.csv`) | One parameter set shared by all vegetated stations, K local: 49 training transitions |
| C2 | k and η cannot be estimated | Adding k: AIC −282.4 → −280.4, k = 0.00 ± 0.27. Adding η: condition number 2.6×10⁸, η = 0 ± 112 | Keep the smallest supported model (r, d). k and η stay in the equation as scenario parameters for Task 3 |
| C3 | W (normalised GWETROOT) carries no time signal | 99.94 % of its variance is between stations; within a station its yearly s.d. is 0.003–0.013 while V varies by 1.5–3.6 points. Across vegetated stations cover is unrelated to it (r = 0.10): YT has W = 0.23 and KEL W = 1.00 with the same cover. Reanalysis has no irrigation | W is closed by the water budget above; for the irrigated oasis stations W = 1 in calibration |
| C4 | f(T) cannot be separated from r at a yearly step | Yearly mean temperature varies by at most 1.8 °C within a station | f(T) absorbed into r; it still enters through ET0g |
| C5 | Imputed NDVI months were scored like observations | 9.3 % of station-months are imputed, 31 % at KEL | Yearly V uses observed June–September months only |
| C6 | Fixed end-members 0.05/0.85 understate ground cover | The densest oasis pixels on the section reach NDVI 0.583, i.e. 66.6 % in v7 units | V stays in v7 units for the dynamics; it is divided by V_full where a ground-cover fraction is needed |
| C7 | Task 2 used an invented water response, Ks = 0.45 + 0.55·I/60 | `Code/v7_ablation.py::steady_v` | Replaced by the V*(I) curve in §4 |

## 3. Data support

**Stations (v7 panel).** Seven vegetated stations, target years to 2022 for fitting, 2023–2025 held out.

| | Training RMSE (V/K) | Hold-out RMSE | Hold-out R² |
|---|---|---|---|
| Model (r, d) | 0.054 | 0.068 | 0.40 |
| Persistence (next year = this year) | 0.060 | 0.058 | – |
| Station mean | – | 0.079 | – |

The model beats the station mean but **not persistence** on the hold-out years. These series sit near their steady state, so they fix the ratio d/r and a relaxation rate, not much more. Leaving one station out moves r only between 0.51 and 0.58, except when YT is removed (0.99): YT is the one station with a clear decline.

**Independent check on the section.** 217 MODIS pixels on the Yutian–Minfeng margin went from bare sand to vegetation between 2003 and 2021 (`Data/v7/section_modis/`). The station r and d were applied to them without refitting; only the local ceiling K and starting cover were fitted, on three windows.

| | CON1–3 (K, V₀ fitted) | CON4 (never used) |
|---|---|---|
| Station r, d transferred | R² 0.40 | R² 0.31 |
| All four parameters fitted freely | R² 0.40 | R² 0.29 |
| Mean baseline | 0.00 | −0.02 |

A free fit to these pixels gives r = 0.64, d = 0.10, against 0.58 and 0.12 from the stations. Two data sets with different sites, years and dynamics agree, which is the main support for r and d. The fitted plateau is 36 % against K = 34–49 % at the stations.

**What has no data behind it.** The water-limited part of the curve (W < 1). The only anchors are the two ends: rain only gives zero cover (XT station 1.2 %, section desert pixels 0.2 %), and irrigated oases sit at x* ≈ 0.8. Between them the curve depends on c and η_w.

## 4. Output for Task 2: water → steady cover

Section forcing (YT, MF), `Results/v7/model1/water_cover_curve.csv`:

| Gross irrigation (mm/yr) | 0 | 100 | 200 | 300 | 400 | 600 | 800 | 1000 |
|---|---|---|---|---|---|---|---|---|
| Steady V (%, v7 units) | 0 | 8.3 | 13.7 | 17.4 | 20.1 | 23.9 | 26.3 | 28.1 |
| Ground-cover fraction | 0 | 0.13 | 0.21 | 0.26 | 0.30 | 0.36 | 0.40 | 0.42 |
| W | 0 | 0.26 | 0.31 | 0.37 | 0.43 | 0.54 | 0.65 | 0.77 |

- Water stops limiting at about 1420 mm/yr.
- A new planting reaches 90 % of its steady cover in 10–11 years.
- Steady cover at 300 mm/yr ranges from 14 to 21 % across the sensitivity cases; r, d and c matter most, then k.
- The natural ecotone (8.9 % in v7 units) corresponds to about 81 mm/yr of groundwater supply.
- The earlier daily model gives a similar curve, lower at small quotas because it charges soil evaporation first (11 % against 17 % at 300 mm/yr).

## 5. Limits

1. No skill over persistence for year-to-year change at the stations.
2. When irrigation stops the model loses cover at rate d only (half-life 5.9 years). d was measured on watered vegetation, so real loss without water is probably faster; the earlier daily model, with an assumed drought mortality, gave 2 years. Task 3 should treat this as a scenario.
3. k is not identified. Wind enters Task 3 only as a scenario.
4. Stations are town coordinates inside oases. They describe irrigated fringe vegetation, not shrub belts on dunes. TZ (9 %) is likely irrigated greenery at the oil base, not natural desert.
5. Rain is ignored as a water source for plants (daily amounts are almost always below what evaporates the same day). The two reanalyses disagree on its size anyway: 73 mm/yr in POWER, 31 mm/yr in ERA5.
6. `Reports/model_v7.tex` was not edited. The changes above should be carried into §3 of that report by whoever owns it.

---

## 中文摘要

**模型。** 保留 v7 的年尺度状态方程不变，只加一条水量关系把水分真正耦合进来：W = min(1, 可用水量 / 冠层不受胁迫时的蒸腾需水量)，可用水量 A = η_w·I + G。

**对 v7 任务一的复核与修改。**

1. 逐站用 8 个年值拟合 4 个参数不可行：v7 自己的消融结果是训练 R² 中位数 0.004，89 % 的拟合顶到边界。改为 7 个有植被站点**共用一组参数**，K 仍逐站确定。
2. k、η 不可识别（k = 0.00 ± 0.27；加入 η 后条件数 2.6×10⁸）。数据只支持 (r, d) 两个参数：r = 0.584 ± 0.180，d = 0.117 ± 0.035。k、η 留在方程里，作为任务三的情景参数。
3. v7 的 W（GWETROOT 归一化）没有时间信号：99.94 % 的方差来自站点之间，站内年际标准差只有 0.003–0.013；再分析产品也不含灌溉。因此不能当作 W_t，改用上面的水量关系；标定时灌溉绿洲站点取 W = 1。
4. 年尺度上 f(T) 与 r 无法区分（站内年均温变幅不超过 1.8 °C），并入 r。
5. 插补出来的 NDVI 月份不再参与评分（全体 9.3 %，库尔勒 31 %）。
6. 固定端元 0.05/0.85 低估地面覆盖：本区段最密的绿洲像元 NDVI 为 0.583，在 v7 单位下只有 66.6 %。动力学仍用 v7 单位，需要地面覆盖比例时除以 66.6 %。
7. 任务二里的 Ks = 0.45 + 0.55·I/60 没有依据，改用第 4 节的 V*(I) 曲线。

**数据支持。** 站点留出期（2023–2025）RMSE 0.068，优于站点均值（0.079），但**不如持续性基线**（0.058）。独立检验：把站点的 r、d 不加修改地用到于田—民丰南缘 217 个“裸沙变植被”的 MODIS 像元上，从未参与拟合的窗口 R² = 0.31；对这些像元自由拟合得到 r = 0.64、d = 0.10，与站点结果一致。

**给任务二的结果。** 300 mm/年 → 稳态 17.4 %（地面覆盖 0.26）；600 mm/年 → 23.9 %（0.36）；约 1420 mm/年以上水分不再受限；新植 10–11 年达到稳态的 90 %。

**局限。** 年际变化预测不优于持续性基线；停灌后模型只按 d 衰减（半衰期 5.9 年），实际应更快；k 未识别；站点是绿洲内的城镇坐标；水分受限区间没有实测数据，取决于 c 与 η_w 两个假设。`Reports/model_v7.tex` 未改动。
