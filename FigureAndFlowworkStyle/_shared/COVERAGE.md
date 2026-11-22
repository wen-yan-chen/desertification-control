# 公共包覆盖审计（COVERAGE）

> 最后更新：2026-11-19（公共包 1.4.0）。
> 回答两个问题：`_shared` 现在能画什么；四个训练源里有哪些成果还没进包。
> 覆盖状态定义：**正式** = 开箱即用、只收数据、有测试与版面审查；**历史索引** = 懒加载，
> 需要原训练目录在场（`FigureTraining\toolkit`、`Practice2\FigureAndFlowworkStyle`）；
> **未收录** = 连索引都没有。

## 一、正式接口全清单（1.4.0）

| 模块 | 能力 |
|---|---|
| `charts` | `annotated_heatmap`（标注热力）、`colorbar`、`comparison_dots` / `comparison_intervals`（点估计/区间对比）、`target_tradeoff`（目标-成本-容量权衡）、`scenario_trends`（多情景趋势）、`pareto_cloud`（2D/3D Pareto 散点）、`radar_profile`（雷达）、`signed_bars`（符号弹性条）、`tornado`（龙卷风）、`break_even_points` / `break_even_curves`（盈亏交叉）、`dual_axis_lines`（双轴）、`feasible_band`（约束可行域带）、`three_d_columns`（3D 柱面 + 正交数值表） |
| `bars` | `BarSeries`、`composition_bars`（构成）、`grouped_bars`（分组，含零基线/百分比合计检查） |
| `diagrams` | `research_framework` / `research_framework_cards`（Our Work 框架）、`feedback_loop` / `LoopStage`（概念循环） |
| `maps` | `mercator`、`cached_tiles`、`Site`、`study_map`（离线底图研究区） |
| `mcm_style` | 四套配色（MORANDI/AWARD/PAPER/DEFAULT + BAR_*）、语义色、colormaps、衬线/无衬线字体、`components`（sheet/panel/label/arrow/box/stage/canvas）、`accents`、`panels/head/grid/save_paper`（含 ≥8pt 与出界自动审查） |
| `latex` | `mcmworkflow.sty`（problem grid / rounded outline / fishbone 三种 TikZ 流程布局） |

## 二、四个训练源覆盖矩阵

### FigureTraining（11 类主线）

| 训练类 | 状态 |
|---|---|
| 01 框架流程图 | 正式 `diagrams.research_framework*` |
| 02 GIS 地图 | 正式 `maps.study_map` |
| 03 概念循环 | 正式 `diagrams.feedback_loop`（1.4.0 晋升） |
| 04 季节序列 | 正式 `charts.scenario_trends`；natural/policy 双曲线留历史 |
| 05 双轴/盈亏 | 正式 `break_even_*`、`dual_axis_lines`（1.4.0 晋升） |
| 06 雷达 | 正式 `radar_profile` |
| 07 3D | 正式 `three_d_columns`（1.4.0 晋升）+ `pareto_cloud` 3D；径向/渐变 3D 留历史 |
| 08 热力 | 正式 `annotated_heatmap`；相关矩阵/调色迁移留历史 |
| 09 可行域 | 正式 `feasible_band`（1.4.0 晋升）+ `pareto_cloud` |
| 10 敏感性 | 正式 `signed_bars`、`tornado`（1.4.0 晋升）；Morris/Sobol 算法与图留历史 |
| 11 柱状 | 正式 `composition_bars`、`grouped_bars`；likert/stack_100/paired/multi_year（ReportLab 直绘）留历史 |

### Practice2\FigureAndFlowworkStyle（样张库）

| 部分 | 状态 |
|---|---|
| `mcm_figures`（13） | 与正式接口等效：bar_trend≈grouped_bars、flowchart≈research_framework、pareto_2d/3d≈pareto_cloud、tornado≈tornado、composition≈composition_bars、sensitivity_heat≈annotated_heatmap 组合；**未覆盖**：`fig_fit`（拟合展示）、`fig_policy_curve`（政策曲线）、`fig_convergence`（收敛）、`fig_sensitivity_lines`（小多面敏感性） |
| `demo_figures`（13 常规） | workflow/eda/map/heatmap/pareto_3d/tornado/uncertainty/radar/scenario ≈ 正式等效；**未覆盖**：`fig_violin`、`fig_parallel`、`fig_response` |
| `demo_figures2`（12 冷门） | **全部仅历史索引**：alluvial、ridge、bump、raincloud、network、waterfall、streamgraph、hexbin、sunburst、phase、dumbbell、clustermap |
| `generate_structures`（n01–n12） | **全部仅历史索引**（12 个新结构样张） |
| `WorkFlowStyle` | 已沉淀为 `latex/mcmworkflow.sty`（正式资产） |

### Practice1\Figures_polished（16 张精修图）

| 状态 | 内容 |
|---|---|
| 已保留 | Morandi 配色 → `palette.MORANDI` / `MORANDI_CYCLE` |
| 正式等效 | 帕累托 2D/3D → `pareto_cloud`；热力 → `annotated_heatmap`；雷达 → `radar_profile`；渐变可行区 → `feasible_band`（近似）；分组柱 → `grouped_bars` |
| **未收录**（连历史索引都没有） | **donut**（M2P_01 经费环形）、**TOPSIS 双面板排名**（M4P_02）、**双轴台阶线+柱**（M4P_03）、**KPI 仪表盘**（OVP_01）、**概念分布示意**（OVP_02）、**发散渐变条**（M3P_01 敏感性排名）、**PCHIP 渐变可行曲线**（M1P_04） |

### Practice2\Figures（项目成图）

- 定位：当届数据成图，**不是公共库素材**；留在项目符合 TRAINING.md 第 4 步原则。
- `Paper2026\render.py`、`Paper2026_Shared\render_shared.py` 为适配脚本（读冻结表 → 调公共接口），正确留在项目。
- `Paper2026_Shared` 7 张已全部走正式接口；`Paper2026` 15 张部分是 1.3.0 前直写，改造时换正式接口。

## 三、缺口清单（未晋升候选，按需求可能性排序）

| 优先级 | 图型 | 来源 | 校赛/正式赛用途 |
|---|---|---|---|
| 高 | donut 构成环 | Practice1 M2P_01 | M2 经费构成，现成数据 |
| 高 | waterfall 瀑布 | demo_figures2 | 资金/成本流分解，治沙经费直接可用 |
| 高 | dumbbell 哑铃前后对比 | demo_figures2 | M5P 前后对比思路、政策效果对比 |
| 高 | sensitivity_heat 双参热力 | mcm_figures | 双参数敏感性网格 |
| 中 | violin / ridge 分布 | demo_figures2 | 情景分布对比 |
| 中 | policy_curve / fit / convergence | mcm_figures | 政策曲线、拟合展示、算法收敛 |
| 中 | likert / stack_100（ReportLab） | bars11 | 问卷类数据 |
| 低 | Morris/Sobol 算法与图 | sensitivity10 | 正式赛若做全局敏感性 |
| 低 | radial 3D、log 尺度敏感性 | three_d07_style / sensitivity10 | 罕见 |
| 保持懒加载 | alluvial/ridge/bump/raincloud/network/streamgraph/hexbin/sunburst/phase/clustermap、n01–n12 | demo_figures2 / generate_structures | 赛时真有需要再升，避免公共包膨胀 |

## 四、结论

- 11 类训练主线 + 样张库核心图型已全部成为正式接口；**常用图 100% 覆盖**。
- "所有最好成果"**没有全包**：缺口集中在 ①Practice1 精修图的 7 个专类（完全未收录），
  ②demo_figures2 的 12 个冷门图型与 generate_structures 的 12 个新结构（仅历史索引）。
- 晋升原则不变：**有真实需求再升**。下一批建议只升 donut、waterfall、dumbbell、
  sensitivity_heat 四个高频项；冷门图型保持懒加载即可。

## 1.5.0 治沙论文补录

正文图 4、5、11 及状态网格备选图已收入 TikZ 机制图目录。图 14b 的累计与当前越线量差值、候选图 m2_water 的年内配额瓶颈已提供独立数据接口。[选图与预览](mcm_library/CATALOG.md#从治沙论文提炼的机制图和数据图150)
