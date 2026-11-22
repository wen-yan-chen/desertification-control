# Practice2 公共接口补绘

上一版正文从公共绘图包 1.3.0 的七张训练回放中选入以下三张。当前稿沿用 08a 和 14，13 改用[含干旱月交付的修订图](../Paper2026_Revision/m3_storm_and_delivery.pdf)。每张均为 6.5 英寸、矢量 PDF 与 300 dpi PNG。原七图记录收入[退役资料](../../archive/README.md)。

结果路径相对于 [Results/v7](../../Results/v7)。三张共享 `paper_context`、`panels`、`head`、`palette` 和 `save_paper`。

| 图 / 正文论点 | 实际接口 | 结果表、连接键与单位 | 逐图参考 |
|---|---|---|---|
| [08a 月度供水压力](08a_m2_water_pressure.pdf) · 年供水余量掩盖五月的月度瓶颈 | `annotated_heatmap`、`colorbar`、`scenario_trends`、`callout` | `model2/monthly.csv` 按 `year, month`，`model2/annual.csv` 按 `year`。毛取水 m³ 分别除月上限与 `Data/v7/m2_inputs/scenario.json` 的年上限，显示百分比。 | 旧 08a–b、selected `2509557_p18_x477` 的连续色阶与矩阵 |
| [13 风暴与管理敏感性](13_m3_storm_sensitivity.pdf) · 联合风暴情景与管理对照对首达时间的影响 | `annotated_heatmap`、`colorbar`、`comparison_dots` | `model3/summary.csv` 取 `entity=project` 并与 `scenario_configs.json` 通过 `case` 对齐。RMST 单位 yr，风暴初始率为 1/yr。 | 旧 13a–b、selected `2509557_p18_x477` 的逐格数值 |
| [14 数值检验](14_m3_numerical_check.pdf) · 比较两套网格与独立 Monte Carlo 的差值 | `comparison_intervals(row_separation=.40)`、`grouped_bars` | `model3/markov_mc_comparison.csv` 按 `nv, cohort_id, post_year`，`grid_validation.csv` 按 `cohort_id, comparison`。概率差乘 100 得百分点。批次 A/B/C 沿 `initial_cohorts.csv` 的原论文排序，并核对 `validation_summary.json`。 | 旧 14、selected `2503268_p21_x237` 的横条结构 |
|---|---|

## 核验与复跑

- 08a 的第 8 年五月用率 94.94%，全年用率 70.01%。分母分别为当月和年度上限。
- 13 逐格标出九组风暴假设的 50 年限制平均首达时间。基准 7.13 年与无灌溉 2.96 年来自管理情景，同均值的联合网格列使用不同损失范围。
- 14 以百分点刻度显示区间和差值。最细 321 × 41 网格的 9 个点均在 Monte Carlo 区间内。中等网格的批次 B 第 30 年略低于对应区间。加密冲击积分引起的最大改变约 0.202 个百分点。
- [输入哈希与版面检查记录](qa-all.json)与当前 v7 输入逐项一致。

[渲染入口](../../Code/paper_figures/render_shared.py)只读冻结输入。从 Practice2 根目录运行。

~~~powershell
$env:PYTHONPATH = (Resolve-Path ../_shared).Path
python -B Code/paper_figures/render_shared.py --out ../tmp/practice2-shared-preview
~~~
