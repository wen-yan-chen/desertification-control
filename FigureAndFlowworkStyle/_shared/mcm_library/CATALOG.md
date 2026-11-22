# 按论文问题选图

## 正式绘图接口 · 直接换成当届数据

下表函数不读取项目文件，不重跑模型。绘前用 [`paper_context`、`panels`，绘后用 `save_paper`](../README.md)；要查完整输入和调用过程，到 [复跑示例](../replay.py) 按图号找。

| 论文要回答的问题 | 首选公共接口 | 训练证据 / 输入要点 |
|---|---|---|
| 数据、模型、交付如何衔接？ | `diagrams.research_framework` | Practice2 01；2–3 个阶段，每相邻阶段给一个交接产物，并指定谁贡献给交付。更多分支可用 [TikZ](latex/STYLE_GUIDE.md) 或 `mcm_style.components`。 |
| 两到三段模型链需要展示阶段内部步骤吗？ | `diagrams.research_framework_cards` + `diagrams.CardStage` | FigureTraining 01；传 2–3 个阶段、每阶段 3 个步骤、共同输入与相邻交接，较简图更接近训练卡片层级。建议 `paper_context("modern_sans")`，长文案先换行并按版宽复核。 |
| 站点和路线在哪里？ | `maps.cached_tiles` + `maps.study_map` | Practice2 02；离线 XYZ 影像，明确投影、原始经纬度、站点类型和比例尺。 |
| 离散情景怎样改变指标？ | `charts.annotated_heatmap` + `charts.colorbar` | Practice2 13a / FigureTraining 08；未算传 NaN，色尺写单位；共用量程时显式传 `limits`。 |
| 方案相对基准差多少？ | `charts.comparison_dots` | Practice2 13b 值标签统一放一侧，基准线带名称；两个方案还可用哑铃连线。 |
| 数值解落在参考区间内吗？ | `charts.comparison_intervals` | Practice2 14a；上下限和各估计按类别对齐。估计接近时可传 `row_separation=.4`，只沿类别轴错开符号，保留量轴位置和区间端点。 |
| 已求解的目标怎样权衡？ | `charts.target_tradeoff` | Practice2 09；按目标顺序对齐，零容量单列写 0，未求解传 NaN；阈值可另有筛选小图。 |
| 情景曲线和区间分开比较吗？ | `charts.scenario_trends` + `charts.Series` | Practice2 12b / 13c；严格递增共同 x；颜色搭配线型，同指标同量程。区间和阈值由数据提供，图例要说明它们。 |
| 真实的前沿样本和选择点在哪里？ | `charts.pareto_cloud` | Practice1 M1P_02/03；接收已计算的候选或前沿，不计算支配、不拟曲面；两轴能讲清就先用二维。 |
| 多维画像的差别在哪一项？ | `charts.radar_profile` | Practice1 M4P_04 / FigureTraining 06；各维方向一致且已归一化至 [0, 1]，图注说明参考区间；大量维度用点图。 |
| 各方案内部的百分比构成如何变化？ | `bars.composition_bars` | FigureTraining 11 的横向五级构成与纵向 100% 堆叠；传 `labels × segments` 百分数矩阵，各行合计 100%，不自动归一化。 |
| 基准与方案、多个期次的数值如何并列比较？ | `bars.grouped_bars` + `bars.BarSeries` | FigureTraining 11 与 Practice1 M1P_01；共同零基线、同一单位，默认中深色实色，最多 5 个系列。 |
| 柱/面积需要突出一个结果吗？ | `mcm_style.accents.gradient_bar` / `gradient_area` / `callout` | Practice1 M1P_01、M3P_01、M1P_04 / Practice2 13c；对比图优先实色，浅渐变可作重点，说明性引线锚定真实点。 |
| 如何选择尚未抽取的图型？ | 下方历史索引 | 找最接近的样图；优先复用共享轴、图例、色条、引线或卡片，再以当届数据封装。 |

## 历史索引 · 找样式、查思路、复现练习

以下 **19 个历史模块**源自 FigureTraining 与 Practice2 样图。按需访问
  `lib.templates` 或 `lib.get("templates")` 才加载对应原文件；普通
`import mcm_library` 不把历史目录插入 `sys.path`，也不加载潜在的写文件模块。
旧脚本可能在加载时切换后端、改全局样式或准备目录。需要原貌时用单独进程；
在同一个定稿脚本中使用上方正式绘图 API。

## 快速使用

```python
import mcm_library as lib
# 方式一：模块.函数（推荐，命名空间清晰）
fig = lib.templates.pareto_plot(...)
# 方式二：先取模块再调用
m = lib.get("concept03")
fig = m.water_cover()
# 查看任意函数的参数
import inspect; print(inspect.signature(lib.templates.sweep_heatmap))
```

部分函数接收参数，另一些使用项目固定文件、合成数据或自行写盘。先核对源码或
用 `inspect.signature` 查签名，再决定如何复用。下面的适配层只统一已有输出形态。

## 接口模式速查（Interface Styles）

训练脚本历史上有三种接口，统一用适配层 `adapters` 调用即可始终拿到 Figure：

| 模式 | 模块 | 行为 |
|---|---|---|
| `fig` | templates、workflow01、concept03、heatmap08、feasible09、seasonal04、three_d07_style | 直接返回 Figure |
| `tuple` | tradeoff05、radar06、three_d07 | 部分函数返回 `(Figure, ...)`，取首个 |
| `selfwrite` | sensitivity10、bars11、demo_figures、demo_figures2、mcm_figures | 内部直接写文件、返回 None，按整库入口运行 |

```python
from mcm_library.adapters import call_figure, interface_of
fig = call_figure("radar06", "three_axis")   # 自动解包 tuple，始终得到 fig
print(interface_of("bars11"))                # 'selfwrite'
```

- `fig` / `tuple`：数据图首选，用 `call_figure` 统一拿 Figure 后自由控制输出。
- `selfwrite`：直接调用即在其原始位置产出文件；11 类柱条图改用正式 `bars` 接口接收自有数据、自由定输出；其他图型优先选上方正式接口，不要强行适配。
- 新结构 `generate_structures.n01(pdf)` 等需传入 `PdfPages` 对象，见 `__main__`。

---

## 一、按图型选择函数（11 类 + 高级冷门）

### 1. 框架 / 流程图（Flowchart / Our Work）
| 函数 | 特点 |
|---|---|
| `diagrams.research_framework_cards` / `CardStage` | 正式数据驱动分层卡片：共同证据、阶段内三步骤、显式交接、综合交付 |
| `workflow01.overview` | 大标题 + 三色 stage 卡片（实色标题条、嵌套子卡片），最精致 |
| `workflow01.decision_map` | 决策映射图 |
| `templates.workflow` | 三阶段 × 三步骤，含底部交付条 |
| `mcm_figures.fig_flowchart` | 单函数流水线框 |
| `demo_figures.fig_workflow` | 流程演示 |

### 2. GIS 地图（Map）
| 函数 | 特点 |
|---|---|
| `gis02.overview` / `gis02.focus` | 完整地图，含底图、指北针、比例尺、站点标记、卡片 |
| `gis02.basemap`（联网取瓦片）、`north`、`scale_bar`、`site_marks` | 可单独调用的地图元件 |
| `demo_figures.fig_map` | 地图演示 |

### 3. 概念循环 / 反馈环（Concept Loop）
| 函数 | 特点 |
|---|---|
| **`diagrams.feedback_loop` / `LoopStage`（正式 1.4.0）** | 3–6 节点圆环、带符号箭头、中心标签与脚注；标签/细节/颜色全参数化 |
| `concept03.water_cover` | 水-覆盖双反馈环（含生境图标、正负号标注） |
| `concept03.annual_resilience` | 年韧性状态循环 |
| 元件：`arc_arrow`、`ring`、`node`、`signs`、`habitat` | 圆形反馈组件 |

### 4. 时间序列 / 季节（Time Series）
| 函数 | 特点 |
|---|---|
| `seasonal04.natural_figure` / `policy_figure` | 自然/政策季节曲线，含上下限与边界 |
| `templates.paired_trends` | 双面板对齐趋势，共享坐标与图例 |

### 5. 双轴 / 交叉 / 盈亏平衡（Trade-off）
| 函数 | 特点 |
|---|---|
| **`charts.break_even_points` / `break_even_curves`（正式 1.4.0）** | 盈亏交叉点计算与绘制；可行带、交点星标、净收益最大点独立标注 |
| **`charts.dual_axis_lines`（正式 1.4.0）** | 双轴双单位，轴色随序列；要求脚注说明"交叉 ≠ 最优" |
| `tradeoff05.common_scale` / `dual_axis` / `paired_axis` | 同尺度、双轴、配对三种画法 |
| `tradeoff05.break_even_points`、`aligned_series`、`tax_series` | 盈亏点与序列工具 |

### 6. 雷达图（Radar）
| 函数 | 特点 |
|---|---|
| `radar06.three_axis` / `five_axis` | 三/五轴极坐标雷达 |
| `radar06.radar_axes`、`draw_series`、`normalize` | polar 元件 |
| `demo_figures.fig_radar` | 雷达演示 |

### 7. 3D 图（3D）
| 函数 | 特点 |
|---|---|
| **`charts.three_d_columns`（正式 1.4.0）** | 离散网格 3D 柱面 + 正交数值表；单指标单单位，颜色仅重复高度，绝不推断曲面 |
| `three_d07.bars_figure` | 3D 柱状 |
| `three_d07_style.columns_figure` / `radial_figure` / `ramp_figure` | 离散柱、径向发散、渐变序列风格 |
| `mcm_figures.fig_pareto_3d`、`demo_figures.fig_pareto_3d` | 3D Pareto 面 |

### 8. 热力图（Heatmap）
| 函数 | 特点 |
|---|---|
| `templates.sweep_heatmap` | 智能文字配色、NA 标注、colorbar，最通用 |
| `heatmap08.annotated_grid` | 带数值标注网格（YlGnBu） |
| `heatmap08.palette_transfer` / `shared_scale_fields` / `correlation_matrix` | 调色迁移、共享尺度、相关矩阵 |
| `heatmap08.ink_on`、`relative_luminance` | 文字对比度工具 |
| `mcm_figures.fig_sensitivity_heat` | 双参数敏感性热力 |

### 9. 可行域 / Pareto 散点（Feasible Region）
| 函数 | 特点 |
|---|---|
| **`charts.feasible_band`（正式 1.4.0）** | 约束定义的可行带 + 可选样本点与星标观测；禁止凸包/插值填充 |
| `templates.pareto_plot`（+ `pareto_indices` 非支配排序） | Pareto 前沿、选中点高亮 |
| `feasible09.band_figure` / `irregular_figure` / `palette_comparison` | 曲线可行带、非凸区域、配色对比 |
| `mcm_figures.fig_pareto_2d` | 二维 Pareto |

### 10. 敏感性分析（Sensitivity）
| 函数 | 特点 |
|---|---|
| **`charts.signed_bars`（正式 1.4.0）** | 符号弹性横条：按绝对值排序、正负分色、零基线；筛选视图，符号仅表方向 |
| **`charts.tornado`（正式 1.4.0）** | 单参数龙卷风：按跨幅排序、基线虚线、端点数值标注 |
| `sensitivity10.oat_figure` | 单参数（one-at-a-time） |
| `sensitivity10.local_figure` / `morris_figure` / `sobol_figure` | 局部弹性、Morris μ-σ、Sobol 指数 |
| `sensitivity10.log_*` | 对数尺度配色版本 |
| `mcm_figures.fig_sensitivity_lines` / `fig_tornado` | 小多面曲线、龙卷风图 |
| `demo_figures.fig_tornado` / `fig_uncertainty` | 龙卷风/不确定性演示 |
| 算法：`morris_effects`、`exact_sobol`、`local_elasticity` | 可复用计算（非仅绘图） |

### 11. 柱状 / 条形 / 构成（Bars & Composition）
| 函数 | 特点 |
|---|---|
| `bars.composition_bars` / `grouped_bars` / `BarSeries` | 正式接口；数据参数化、零基线及百分比合计检查，复用 FigureTraining 11 的中深色实色配色 |
| `bars11.likert` / `stack_100` / `paired_scores` / `multi_year` | 李克特、100% 堆叠、配对、多年分组（ReportLab 直绘 PDF） |
| `mcm_figures.fig_bar_trend` / `fig_composition` | 带标签柱、环形占比 |
| `seasonal04` 等亦可处理构成 | — |

### 12. 高级 / 冷门图型（`demo_figures2`，出彩点）
`fig_alluvial`（冲积桑基）、`fig_ridge`（山脊）、`fig_bump`（凸起排名）、
`fig_raincloud`（雨云）、`fig_network`（网络）、`fig_waterfall`（瀑布）、
`fig_streamgraph`（流图）、`fig_hexbin`（六角箱）、`fig_sunburst`（旭日）、
`fig_phase`（相位）、`fig_dumbbell`（哑铃）、`fig_clustermap`（聚类热图）。

### 13. 新结构样张（`generate_structures` n01–n12）
12 个面向新题型的结构图，每个含独立 `nXX` 函数；需要整组时运行其 `main()`。

---

## 二、模块完整清单（19）

| 模块 | 来源 | 后端 | 职责 |
|---|---|---|---|
| `templates` | FigureTraining | matplotlib | 通用高级函数（pareto/heatmap/gradient/workflow） |
| `workflow01` | FigureTraining | matplotlib | 精致框架卡片 |
| `concept03` | FigureTraining | matplotlib | 圆形反馈循环（→ `diagrams.feedback_loop` 已晋升） |
| `gis02` | FigureTraining | matplotlib | GIS 地图 |
| `seasonal04` | FigureTraining | matplotlib | 季节时间序列 |
| `tradeoff05` | FigureTraining | matplotlib | 双轴/盈亏（→ `charts.break_even_*`、`dual_axis_lines` 已晋升） |
| `radar06` | FigureTraining | matplotlib | 雷达 |
| `three_d07` / `three_d07_style` | FigureTraining | matplotlib | 3D（→ `charts.three_d_columns` 已晋升） |
| `heatmap08` | FigureTraining | matplotlib | 热力图 |
| `feasible09` | FigureTraining | matplotlib | 可行域（→ `charts.feasible_band` 已晋升） |
| `sensitivity10` | FigureTraining | ReportLab | 敏感性（直绘 PDF）（→ `charts.signed_bars`、`tornado` 已晋升） |
| `bars11` | FigureTraining | ReportLab | 柱状/条形（直绘 PDF） |
| `render_training` | FigureTraining | matplotlib | 训练渲染入口 |
| `mcm_figures` | FigureAndFlowworkStyle | matplotlib | 一函数一图型模板 |
| `demo_figures` / `demo_figures2` | FigureAndFlowworkStyle | matplotlib | 常规/高级演示 |
| `figure_paths` | FigureAndFlowworkStyle | — | 输出路径工具 |
| `generate_structures` | FigureAndFlowworkStyle | matplotlib | 12 个新结构 |

## 三、批量脚本与 LaTeX 资产（不自动导入）

- 批量整库脚本：`BATCH_SCRIPTS["generate_gallery"]`（无 `__main__` guard，
  import 会执行全流程）。需要整套画廊时直接运行：
  `py -3.13 "<路径>/generate_gallery.py"`，不要 import。
- LaTeX/TikZ 工作流：`LATEX_WORKFLOW["sty"]`（[公共副本](latex/mcmworkflow.sty)，含
  problem grid / rounded outline / fishbone 三种布局与 4 主题），用法见
  `LATEX_WORKFLOW["style_guide"]`。适合用纯 LaTeX 画"Our Work"流程图。

## 四、复用红线

- [ ] 优先调用正式图接口。没有匹配的整图时，复用公共部件；一次性适配留在项目。
- [ ] 数据作为参数传入；整图返回 Figure，部件在传入 Axes 上绘制并返回 Axes／artist；不重跑模型、不改数值
- [ ] 先预览一张，核对数据/单位/版宽后再批量保存 PDF（可编辑）+ 300 dpi PNG
- [ ] 新增能力沉淀进对应模块并更新本索引，不把一次性脚本塞进公共库

## 从治沙论文提炼的机制图和数据图（1.5.0）

| 论文要回答的问题 | 入口 | 输入与读法 |
|---|---|---|
| 多时间尺度、存量、分批投入或状态跃迁怎样运行？ | [四张可编辑的 TikZ 示意图](latex/mechanisms/README.md) | 每张附编译预览、适用情形和换题时需改的内容。 |
| 全年有余量，哪个月仍可能受限？ | `charts.quota_pressure` | 输入按年 × 期对齐的用量、分期配额和年度配额。图中依次显示年总量、最紧年份的分期曲线、各年利用率。并列峰值取最早输入位置。 |
| 曾经越线的对象里，目前有多少已恢复？ | `charts.recovery_gap` | 固定同一批对象，时间递增。历史累计越线量与当前越线量同单位；两线之间为曾越线且当前已恢复的量。末个配对时刻的差值自动标注。 |

[论文结果表示例](../examples/desertification.py) · [配额图预览](../examples/quota_pressure.png) · [恢复图预览](../examples/recovery_gap.png)

要将真实图片和数据结合，可查[实景、影像与数据案例](../examples/image_data/README.md)。其中照片取样线图可用自己的图片与像素坐标重新生成。
