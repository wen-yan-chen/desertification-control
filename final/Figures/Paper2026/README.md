# Practice2 论文基础图

以下六张按 6.5 英寸正文宽度选入上一版论文，各有 PDF 和 300 dpi PNG。当前稿沿用 02、04、05、06、12，09 改用[修订图](../Paper2026_Revision/m2_tradeoff_revision.pdf)。原 15 图的图注和落选图在[退役资料](../../archive/README.md)中。图号沿用训练编号。

| 图 | 冻结来源、连接键和单位 |
|---|---|
| [02 研究区和站点覆盖](02_study_area.pdf) | [站点面板](../../Data/v7/m1_audited/README.md)按站点、年和月选 6–9 月，至少两个有效月。覆盖用 MODIS 代理百分数，误差线为年间标准差。地图使用缓存 Esri 瓦片及 v7 代表样带。 |
| [04 留出检验](04_m1_holdout.pdf) | `holdout_by_site.csv`、`prediction_pairs.csv`、`yearly_table.csv`、`free_running_holdout.csv`，按站点和年对齐。RMSE 基于 `V/K`，下排为覆盖代理百分数。 |
| [05 剂量响应与停灌](05_m1_irrigation_response.pdf) | `water_cover_curve.csv` 按灌溉深度 mm/yr，`scenario_annual.csv` 按 `scenario, calendar_year`。覆盖用代理百分数，年末根区储水用 mm。 |
| [06 控制因子](06_m1_drivers.pdf) | `section_forcing_climatology.csv` 按月，`wind_channel.csv` 和 `sensitivity.csv` 按灌溉量、参数及取值。季节需求为 mm/月，覆盖差为百分点。 |
| [09 权衡和光伏准入](09_m2_tradeoff_pv.pdf) | `scenario_summary.csv` 取六个 `frontier_*` 已求解点，比较有效 ha·yr、百万 CNY 和 MW。`pv_screening.csv` 按建设年读取 CNY/kWh 的独立保本电价。 |
| [12 韧性与恢复](12_m3_resilience.pdf) | `project_annual.csv`、`cohort_annual.csv`、`summary.csv`，按情景、后评估年和批次对齐。概率与覆盖为百分数，面积为 ha，累计效益为有效 ha·yr。 |

输入字段见 [M1](../../Results/v7/model1/README.md)、[M2](../../Results/v7/model2/README.md)和 [M3](../../Results/v7/model3/README.md)。[渲染入口](../../Code/paper_figures/render.py)沿用该批的项目样式与本地瓦片。逐图取舍见[图件入口](../README.md)。

从 Practice2 根目录复跑。依赖 Matplotlib 3.8+、NumPy、pandas 和 Pillow。

~~~powershell
python -B Code/paper_figures/render.py --out ../tmp/practice2-paper-preview
~~~
