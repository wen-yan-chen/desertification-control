# 公共绘图能力 · 1.4.0

| 能力 | 接口 | 来源与边界 |
|---|---|---|
| 学术衬线、现代无衬线 | `paper_context("academic_serif")` / `paper_context("modern_sans")` | Practice2 / Practice1；用局部作用域，默认 Times New Roman，缺少时用 DejaVu Serif；尽量整册一致。现有 `configure` 仍可用于独立脚本。 |
| 可比较的配色 | `palette.PAPER`（默认）、`AWARD`、`MORANDI`、`SEMANTIC`，`BAR_PAIR/LIKERT/COMPONENTS/PERIODS` | 学术或低饱和主题。经济蓝、环境青绿、社会赭橙；11 类柱条图另用有序、构成、期次的中深色配色。没有这些语义时按情景固定颜色与线型。 |
| 9 种色带 | `get_colormap`；`academic_teal`、`academic_blue`、`academic_plum`；`morandi_teal/coral/gold/rose/heat/diverge` | Practice1 / Practice2 13a。单调量用顺序色带，偏离共同基准用有含义的发散中心。 |
| 正文分图、画布 | `panels`、`head`、`grid`；`components.sheet/canvas` | Practice2；默认 6.5 英寸，明确分图对照关系。 |
| 流程图形和批注 | `components.panel/label/arrow/box/stage`；`accents.callout` | Practice2 01/13 与 FigureTraining 01。“框有角色、箭头有含义”；`stage` 支持 1–3 步，用于内容足够的模型卡片。 |
| 分层流程整图 | `mcm_library.diagrams.research_framework_cards`、`CardStage` | FigureTraining 01；共同输入、2–3 阶段各三步、相邻交接和交付。适合需要展开方法链的论文全局图。 |
| 梯度装饰 | `accents.gradient_bar`、`gradient_area` | Practice1 M1P_01 / M3P_01 / M1P_04；处理正负条和多边形裁切，不内插样本。 |
| 正式柱条图 | `mcm_library.bars.composition_bars`、`grouped_bars`、`BarSeries` | FigureTraining 11 与 Practice1 M1P_01；百分比合计、缺失和零基线明确检查。类别长时选横向，5 个以上系列改分面。 |
| 审稿与保存 | `page.audit`、`save_paper` | 按插入尺寸检查字号（默认 ≥8 pt）、出界及疑似文字重叠；默认固定画布、PDF + 300 dpi PNG，可选 SVG。误报或数据遮挡由人看；`qa-all.json` 是回放结果。 |
| 正式整图与历史入口 | [图型目录](../mcm_library/CATALOG.md)、[可移植 TikZ 样式](../mcm_library/latex/STYLE_GUIDE.md) | 选真实数据已回放的公共函数；FigureTraining 11 类和 Practice2 样张可用于尚未抽取的类型。 |

新增能力按[回流与验收](../TRAINING.md)保留真实输入的迁移证据、输入边界和旧基准。公共包扩展时同步版本、索引和最短调用示例。

- **1.4.0（2026-11-19）**：训练图型晋升正式接口，全部"只收数据、不读文件"：`charts.signed_bars`（符号弹性条）、`charts.tornado`（单参数龙卷风）、`charts.break_even_points` / `break_even_curves`（盈亏交叉）、`charts.dual_axis_lines`（双轴）、`charts.feasible_band`（约束可行域带）、`charts.three_d_columns`（3D 柱面 + 正交数值表）；`diagrams.feedback_loop`（概念循环图，3–6 节点、带符号箭头）。全部 ≥ 8 pt 过 `save_paper` 版面审查，新增 19 项契约测试；7 张旧基线回放哈希一致。
- **1.3.0（2026-11-18）**：`charts.comparison_intervals` 增加可选 `row_separation`，解决重复或接近估计的符号遮挡。数值位置和区间端点保留，原调用默认继续用中心线。使用 Practice2 真实结果和一份含重复估计的独立测试复核。
- **1.2.0（2026-11-17）**：根据 [公共包对照训练](../../FigureTraining/公共绘图包_20261117_训练记录.md)新增正式柱条与分层流程卡片接口和较深默认轮换色；修复点图数值与基准线冲突、雷达内部刻度压线问题；保留历史渐变，并追加同一冻结投资数据的实色对照。
- **1.1.0（2026-11-17）**：抽取 Paper2026 的分图、框架、离线地图、目标权衡、热力、情景趋势和校验区间，以及 Practice1 的渐变、Pareto 点云和雷达。补固定宽度导出、自动版面检查、10 个历史回放和训练回流入口；把旧图型模块改为按需引用。
- **1.0.0（2026-11-17）**：汇总 Practice1 Morandi 配色、FigureTraining 卡片/衬线和 Practice2 论文版宽约定。

1.5.0 增加多时间尺度、存量守恒、批次年龄和状态转移四张 [TikZ 源码与预览](../mcm_library/latex/mechanisms/README.md)。年度与分期约束诊断使用 `charts.quota_pressure`，累计与当前越线量对照使用 `charts.recovery_gap`。[输入与回放示例](../examples/desertification.py)
