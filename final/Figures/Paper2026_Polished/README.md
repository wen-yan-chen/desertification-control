# Practice2 图 5–16 绘图优化

[逐图对照册](figure_comparison_05-16.pdf)左侧为替换前用图，右侧为批量优化版。[图 11 的现稿版](fig11_water_use_smooth.pdf)随后改用了平滑色阶。单图各有 6.5 英寸宽的矢量 PDF 和 300 dpi PNG。

| 正文图号与改动 | 训练参考及公共接口 | 冻结来源与单位 |
|---|---|---|
| [5 胁迫与温度](fig05_stress_switches.pdf) · 突出 37.5 mm 折点及胁迫区，温度图保留站点月均点 | FigureTraining 04-02 阈值标法，`panels`、`head` | M1 基准参数及 `panel_m1.csv`，筛 YT/MF 2015–2022 年按月取温度均值，mm、°C |
| [6 留出检验](fig06_holdout.pdf) · 按站点配对误差，单列总体误差，三站轨迹共用尺度 | 11-03 配对比较，`comparison_dots`、`scenario_trends` | M1 `holdout_by_site` 按站，`prediction_pairs` 取 test，`yearly_table`、`free_running_holdout` 按站与年，RMSE 基于 V/K，轨迹为覆盖代理百分数 |
| [7 灌溉响应](fig07_irrigation_response.pdf) · 标出停灌首年，统一同指标纵轴 | 04-02 阈值及情景区间，`scenario_trends` | M1 `water_cover_curve` 按灌溉量，`scenario_annual` 按情景与年，`model1_results.json` 提供容量和无水分限制覆盖，mm/yr、覆盖代理百分数、mm |
| [8 控制因子](fig08_drivers.pdf) · 强化端点符号和零线，统一两档灌溉下的敏感性范围 | 04-01 季节曲线、10-01 小多图，`panels`、`scenario_trends` | M1 `section_forcing_climatology` 按月，`wind_channel` 按配额和风速，`sensitivity` 按配额、参数及取值，`water_cover_curve` 提供配额基线。mm/月、覆盖百分数、百分点 |
| [9 两步求解](fig09_two_stage_optimisation.pdf) · 实色标题分开输入、生态上限和最小成本 | 01-02 Model2 Detail，`sheet`、`panel`、`arrow`、`label` | 按 M2 的共用约束、目标份额和求解顺序绘制的示意 |
| [10 施工批次](fig10_cohort_plan.pdf) · 标明灌溉阶梯分界，现金流叠柱增加纹理 | 11-02 年度构成、11-04 分组柱，`panels`、`head` | M2 `cohorts` 按批次、项目年，第 15 年按批次对 M3 `initial_cohorts`；`annual` 按年，`scenario.json` 给年度预算。面积 ha、配额 mm/yr、覆盖 %、储水 mm、未折现百万 CNY |
| [11 月供水](fig11_water_use_smooth.pdf) · 平滑色阶与年度曲线共用年份位置，标出第 8 年的两个比例 | [08-03 共用色阶](../../../FigureTraining/output/08_热力图/03_shared_scale_fields.png)，公共 `panels`、`colorbar`、`scenario_trends`、`callout` | M2 `monthly` 按年月，`annual` 按年。毛取水量除相应月上限或 `scenario.json` 年上限，单位 % |
| [12 方案权衡](fig12_tradeoff.pdf) · 标清斜率单位，区分 60% 方案和 100% 目标下的零 PV | 05-01 参考线与决策标注，`target_tradeoff`、`callout` | M2 `scenario_summary` 的六个 `frontier_*` 按生态目标排序，`pv_screening` 按投建年。有效 ha·yr、百万 CNY、MW、CNY/kWh |
| [13 投资敏感性](fig13_investment_sensitivity.pdf) · 零基线展示新增成本，右列保留各方案总成本 | 10-02 有方向的横条、11-03 数值标法，`panels`、公共色板 | M2 `scenario_summary` 按 case 对照 base，只比较同一绝对生态目标下的可行解，百万 CNY |
| [14 马尔可夫检验](fig14_markov_validation.pdf) · 分开 A/B/C，区间、点型和加密柱纹理可用灰阶识读 | 11-04 分组柱，`comparison_intervals`、`grouped_bars` | M3 `markov_mc_comparison` 按网格、批次和后评估年，`grid_validation` 按批次和加密类型；`initial_cohorts` 定批次顺序，`validation_summary.json` 核对区间覆盖数。概率差乘 100 得百分点 |
| [15 韧性与恢复](fig15_resilience.pdf) · 分开两类区间、直标面积轨迹，标出第 50 年恢复和累计收益比例 | 04-01 趋势与区域，`scenario_trends`、`callout` | M3 `project_annual`、`cohort_annual`、`summary` 按情景、后评估年、批次或实体对齐，M1 参数与 M3 配置给预警阈值。概率和覆盖 %、面积 ha、收益为有效 ha·yr |
| [16 联合风暴与供水](fig16_storm_and_delivery.pdf) · 突出管理基准和两方案共同的实供水平 | 08-02 九格注值、11-03 成对柱，`annotated_heatmap`、`comparison_dots`、`grouped_bars` | M3 `summary` 与 `scenario_configs.json` 按 case，`resources` 取后评估第 1 年五月干旱行。50 年限制平均首达时间用 yr，生态请求与实供用千 m³ |

图型参考来自 [FigureTraining 成图](../../../FigureTraining/output/) 和[训练手册](../../../FigureTraining/2027绘图训练手册.md)。图 16 的九格逐格标注沿用训练手册记录的 2025 年 B 题 O 奖 2509557 图 9。样图用于选版式，数值来自 Practice2。

图 11(a) 使用从浅绿到深蓝的 GnBu 色带和双线性插值，0–100% 色标及原始年月网格点数值一致。插值仅用于相邻网格点之间的显示，图 11(b) 直接绘制原值。[方格版](fig11_water_use.pdf)可供对照，[平滑版记录](qa-fig11_water_use_smooth.json)保存相同的冻结输入哈希。

抽查了图 6 的 21 个留出样本（M1 0.0635，持续性基准 0.0536）、图 7 的 2036 年停灌、图 11 第 8 年的五月 94.94% 与全年 70.01%、图 13 初始覆盖减半增加约 7.39 百万 CNY、图 14 最细网格的 9/9 覆盖，以及图 16 两种请求量对应约 126 千 m³ 的共同实供。图 15 的 A 与 C 首达概率曲线接近重合。

使用公共包 1.4.0 的 `paper_context` 和 `save_paper`。全部图已按正文宽度复核彩色和灰阶，检查标签、图例、轴范围和纹理。逐图输入哈希和自动版面检查见 [qa-all.json](qa-all.json)。[项目适配脚本](../../Code/paper_figures/render_polished.py)从 Practice2 根目录复跑到新目录。

~~~powershell
$env:PYTHONPATH = (Resolve-Path ../_shared).Path
python -B Code/paper_figures/render_polished.py --out ../tmp/practice2-polished-replay
python -B Code/paper_figures/render_polished.py --only fig11_water_use_smooth --out ../tmp/practice2-polished-replay
~~~
