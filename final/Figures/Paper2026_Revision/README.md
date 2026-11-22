# Practice2 正文修订图

下表沿用 24 页修订稿的图号。最新正文的流程和机制图见[机制图与流程图修订](../Paper2026_Mechanisms/README.md)。其余结果图沿用下表中的文件。各图复用公共绘图包 1.4.0 的配色、排版和导出接口，均有 6.5 英寸宽的矢量 PDF 和 300 dpi PNG。[渲染脚本](../../Code/paper_figures/render_revision.py)调用 `render_shared` 的数据读取和 `paper_context`、`save_paper` 导出流程。

| 正文图与论点 | 复用接口及参考图 | 冻结输入、连接键与单位 |
|---|---|---|
| [1 工作全流程](workflow_revision.pdf) · 三个模型如何交接 | `diagrams.research_framework`，Practice2 原 01 | 示意图，按正文章节标注输入、交接和交付 |
| [3 M1 时间尺度](m1_daily_annual.pdf) · 日水分平衡如何驱动年覆盖 | `components.sheet/panel/arrow/label`，原时间尺度与根区水桶图 | 示意图，符号对应正文的日需水量、根区储水和全年蒸腾满足率 |
| [7 M2 求解步骤](m2_milp_workflow.pdf) · 同一组约束下先求生态上限，再求目标成本 | `components.sheet/box/arrow`，原 M2 结构图 | 示意图，按正文的预计算、离散决策和两步 MILP |
| [8 M2 基准方案与交接](m2_cohort_handoff.pdf) · 三批林带如何补水、何时投资、以什么状态进入 M3 | `panels`、`head`，原 M2 方案图与 M2 训练图 01–02 | `model2/cohorts.csv` 按 `cohort_id, year`，以第 15 年状态按 `cohort_id` 对照 `model3/initial_cohorts.csv`。面积 ha、补水 mm/yr、覆盖 %、储水 mm。`model2/annual.csv` 按 `year` 加总支出，年上限来自 M2 情景配置，金额用未折现百万 CNY |
| [10 M2 生态、成本与光伏](m2_tradeoff_revision.pdf) · 追求更高生态目标的增量成本 | `charts.target_tradeoff`、`callout`，基础图 09 | `model2/scenario_summary.csv` 取六个 `frontier_*`，按目标排序。增量成本由相邻解的净现成本之差除以有效 ha·yr 之差。光伏容量由 kW 转 MW，`model2/pv_screening.csv` 按 `start_year` 读取独立保本电价 |
| [11 M2 投资敏感性](m2_investment_sensitivity.pdf) · 固定生态目标时哪些假设影响成本 | `charts.comparison_dots`，M2 训练图 05 | `model2/scenario_summary.csv` 按 `case` 比较同一绝对生态目标下的五个可行情景和基准，金额用百万 CNY |
| [14 M3 风暴与供水](m3_storm_and_delivery.pdf) · 风暴如何改变预警时间，以及供水上限如何影响增灌 | `annotated_heatmap`、`comparison_dots`、`bars.grouped_bars`，公共接口图 13 | `model3/summary.csv` 与 `scenario_configs.json` 按 `case` 匹配。50 年限制平均首达时间用 yr。供水取 `model3/resources.csv` 的第 1 个后评估年、五月、干旱条件，按 `case` 对照请求和实供，m³ 除以 1,000 |

结果路径相对于 [Results/v7](../../Results/v7/)，M2 配置在 [Data/v7/m2_inputs](../../Data/v7/m2_inputs/)。[验收记录](qa-all.json)保存逐图输入哈希和版面检查。抽查核对了 M2 三批末态与 M3 初值、相邻目标成本 36.7 千和 57.1 千 CNY/有效 ha·yr、固定目标基准 25.35 百万 CNY，以及干旱五月约 171 和 205 千 m³ 的请求与共同的 126 千 m³ 实供。七张图均已预览灰阶，并以正文实际比例检查图例、标签和图注。沿用已有公共接口，项目适配留在 Practice2。

七张修订图的 PNG 和验收记录均与独立复跑一致。公共接口补绘的旧图 13 用默认参数复跑，PNG 与原文件逐像素一致。

从 Practice2 根目录复跑到单独的预览目录。

~~~powershell
$env:PYTHONPATH = (Resolve-Path ../_shared).Path
python -B Code/paper_figures/render_revision.py --out ../tmp/practice2-paper-revision-preview
~~~
