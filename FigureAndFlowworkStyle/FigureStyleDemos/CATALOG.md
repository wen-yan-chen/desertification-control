# 图表分类索引

[返回目录说明](README.md)。全部图片集中在 [Images/](Images/)，按用途分类。相同图形的不同风格均保留，带 PDF 的条目可用于矢量出图参考。

## 流程与空间布局

| 图形 | 风格来源 | 预览／矢量图 | 绘图函数 | 适合表达 |
| --- | --- | --- | --- | --- |
| 建模流程图 | batch1 | [PNG](Images/01_流程与空间布局/batch1_Fig01_workflow.png) | [`fig_workflow`](Scripts/demo_figures.py) | 总体技术路线 |
| 区域布局示意图 | batch1 | [PNG](Images/01_流程与空间布局/batch1_Fig03_schematic_map.png) | [`fig_map`](Scripts/demo_figures.py) | 区段与节点关系；非真实地图 |
| 网络图 | batch2 | [PNG](Images/01_流程与空间布局/batch2_B5_network.png) | [`fig_network`](Scripts/demo_figures2.py) | 节点联系与群组 |
| 分栏流程图 | template | [PNG](Images/01_流程与空间布局/template_flowchart.png) · [PDF](Images/01_流程与空间布局/template_flowchart.pdf) | [`fig_flowchart`](Scripts/mcm_figures.py) | Our work 技术路线 |

## 数据探索与分布

| 图形 | 风格来源 | 预览／矢量图 | 绘图函数 | 适合表达 |
| --- | --- | --- | --- | --- |
| 探索分析面板 | batch1 | [PNG](Images/02_数据探索与分布/batch1_Fig02_eda_dashboard.png) | [`fig_eda`](Scripts/demo_figures.py) | 时间变化、构成与指标概览 |
| 相关性热力图 | batch1 | [PNG](Images/02_数据探索与分布/batch1_Fig04_corr_heatmap.png) | [`fig_heatmap`](Scripts/demo_figures.py) | 变量关系探索 |
| 小提琴图 | batch1 | [PNG](Images/02_数据探索与分布/batch1_Fig09_violin.png) | [`fig_violin`](Scripts/demo_figures.py) | 约束裕量或指标分布 |
| 山峦图 | batch2 | [PNG](Images/02_数据探索与分布/batch2_B2_ridge.png) | [`fig_ridge`](Scripts/demo_figures2.py) | 多组分布对比 |
| 雨云图 | batch2 | [PNG](Images/02_数据探索与分布/batch2_B4_raincloud.png) | [`fig_raincloud`](Scripts/demo_figures2.py) | 分布、箱线与样本点 |
| 六边形密度与边际分布 | batch2 | [PNG](Images/02_数据探索与分布/batch2_B8_hexbin_joint.png) | [`fig_hexbin`](Scripts/demo_figures2.py) | 大量二维样本 |
| 聚类热力图 | batch2 | [PNG](Images/02_数据探索与分布/batch2_B12_clustermap.png) | [`fig_clustermap`](Scripts/demo_figures2.py) | 指标与样本聚类 |
| 拟合与残差图 | template | [PNG](Images/02_数据探索与分布/template_fit.png) · [PDF](Images/02_数据探索与分布/template_fit.pdf) | [`fig_fit`](Scripts/mcm_figures.py) | 参数拟合诊断 |

## 优化与算法

| 图形 | 风格来源 | 预览／矢量图 | 绘图函数 | 适合表达 |
| --- | --- | --- | --- | --- |
| 三维 Pareto 图 | batch1 | [PNG](Images/03_优化与算法/batch1_Fig05_pareto_3d.png) | [`fig_pareto_3d`](Scripts/demo_figures.py) | 多目标权衡 |
| 平行坐标图 | batch1 | [PNG](Images/03_优化与算法/batch1_Fig06_parallel_coords.png) | [`fig_parallel`](Scripts/demo_figures.py) | 多指标候选方案比较 |
| 相平面图 | batch2 | [PNG](Images/03_优化与算法/batch2_B10_phase_plane.png) | [`fig_phase`](Scripts/demo_figures2.py) | 状态轨迹、向量场与零增长线 |
| 二维 Pareto 图 | template | [PNG](Images/03_优化与算法/template_pareto_2d.png) · [PDF](Images/03_优化与算法/template_pareto_2d.pdf) | [`fig_pareto_2d`](Scripts/mcm_figures.py) | 双目标与推荐方案 |
| 三维 Pareto 图 | template | [PNG](Images/03_优化与算法/template_pareto_3d.png) · [PDF](Images/03_优化与算法/template_pareto_3d.pdf) | [`fig_pareto_3d`](Scripts/mcm_figures.py) | 三目标曲面与选点 |
| 收敛曲线 | template | [PNG](Images/03_优化与算法/template_convergence.png) · [PDF](Images/03_优化与算法/template_convergence.pdf) | [`fig_convergence`](Scripts/mcm_figures.py) | 算法表现与波动 |

## 敏感性与不确定性

| 图形 | 风格来源 | 预览／矢量图 | 绘图函数 | 适合表达 |
| --- | --- | --- | --- | --- |
| 龙卷风图 | batch1 | [PNG](Images/04_敏感性与不确定性/batch1_Fig07_tornado.png) | [`fig_tornado`](Scripts/demo_figures.py) | 单因素敏感性排序 |
| 分布与不确定性扇形带 | batch1 | [PNG](Images/04_敏感性与不确定性/batch1_Fig08_uncertainty.png) | [`fig_uncertainty`](Scripts/demo_figures.py) | 区间与分布展示 |
| 投资响应曲线 | batch1 | [PNG](Images/04_敏感性与不确定性/batch1_Fig10_response_curves.png) | [`fig_response`](Scripts/demo_figures.py) | 边际效应与饱和 |
| 策略响应与容量线 | template | [PNG](Images/04_敏感性与不确定性/template_policy_curve.png) · [PDF](Images/04_敏感性与不确定性/template_policy_curve.pdf) | [`fig_policy_curve`](Scripts/mcm_figures.py) | 实际响应与约束比较 |
| 多面板敏感性曲线 | template | [PNG](Images/04_敏感性与不确定性/template_sensitivity_lines.png) · [PDF](Images/04_敏感性与不确定性/template_sensitivity_lines.pdf) | [`fig_sensitivity_lines`](Scripts/mcm_figures.py) | 多个目标的单因素变化 |
| 龙卷风图 | template | [PNG](Images/04_敏感性与不确定性/template_tornado.png) · [PDF](Images/04_敏感性与不确定性/template_tornado.pdf) | [`fig_tornado`](Scripts/mcm_figures.py) | 参数影响排序 |
| 双参数敏感性热图 | template | [PNG](Images/04_敏感性与不确定性/template_sensitivity_heat.png) · [PDF](Images/04_敏感性与不确定性/template_sensitivity_heat.pdf) | [`fig_sensitivity_heat`](Scripts/mcm_figures.py) | 交互效应 |

## 构成与方案比较

| 图形 | 风格来源 | 预览／矢量图 | 绘图函数 | 适合表达 |
| --- | --- | --- | --- | --- |
| 雷达图 | batch1 | [PNG](Images/05_构成与方案比较/batch1_Fig11_radar.png) | [`fig_radar`](Scripts/demo_figures.py) | 多维方案表现 |
| 情景堆叠柱图 | batch1 | [PNG](Images/05_构成与方案比较/batch1_Fig12_scenario_bars.png) | [`fig_scenario`](Scripts/demo_figures.py) | 投资结构与情景比较 |
| 桑基／流向图 | batch2 | [PNG](Images/05_构成与方案比较/batch2_B1_alluvial.png) | [`fig_alluvial`](Scripts/demo_figures2.py) | 资金来源与去向 |
| 排名变化图 | batch2 | [PNG](Images/05_构成与方案比较/batch2_B3_bump.png) | [`fig_bump`](Scripts/demo_figures2.py) | 方案排名随时间变化 |
| 瀑布图 | batch2 | [PNG](Images/05_构成与方案比较/batch2_B6_waterfall.png) | [`fig_waterfall`](Scripts/demo_figures2.py) | 收益或预算增减分解 |
| 流图 | batch2 | [PNG](Images/05_构成与方案比较/batch2_B7_streamgraph.png) | [`fig_streamgraph`](Scripts/demo_figures2.py) | 各分量的时间变化 |
| 旭日图 | batch2 | [PNG](Images/05_构成与方案比较/batch2_B9_sunburst.png) | [`fig_sunburst`](Scripts/demo_figures2.py) | 层级构成 |
| 哑铃图 | batch2 | [PNG](Images/05_构成与方案比较/batch2_B11_dumbbell.png) | [`fig_dumbbell`](Scripts/demo_figures2.py) | 干预前后对比 |
| 年度柱状图 | template | [PNG](Images/05_构成与方案比较/template_bar_trend.png) · [PDF](Images/05_构成与方案比较/template_bar_trend.pdf) | [`fig_bar_trend`](Scripts/mcm_figures.py) | 年度规模与缺失值 |
| 环形图与排序条图 | template | [PNG](Images/05_构成与方案比较/template_composition.png) · [PDF](Images/05_构成与方案比较/template_composition.pdf) | [`fig_composition`](Scripts/mcm_figures.py) | 投资或成本构成 |

