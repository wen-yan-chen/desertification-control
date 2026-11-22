# 给队友或 AI 的绘图任务单

```text
目标图 / 正文要支持的一句话：[……]
数据来源：[冻结文件、列、连接键、单位、缺失值及阈值口径]
参考图：[练习图编号；有 O 奖示例时给论文页码和图号]

先读工作区 AGENTS.md、_shared/README.md 和 _shared/mcm_library/CATALOG.md。
首选公共接口：[模块.函数；不知道时先按目录选择，并说清为什么]
出图脚本：项目内只做读表、对齐、单位换算和图注；
          复用 mcm_style 的字体、配色、分图和导出，整图复用 mcm_library。
输出：[目录和图号]，按实际插入宽度生成 PDF + 300 dpi PNG。
先预览一张，核对普通值、推荐解或阈值、字号、重叠、灰阶和图注，再批量导出。
交接：列出实际用的公共接口、冻结来源、抽查数值和输出路径。
```

单图重绘示例：重绘联合敏感性图，调用
`mcm_library.charts.annotated_heatmap` 和 `colorbar`。从情景配置与冻结结果
按 `case` 连接，再按参数值分行列；色条用年，未求解格显示 NA。先复跑
`python -B .\_shared\replay.py --only p2_13_stress --out .\tmp\figure-reference`，
再迁移到当届数据。

每次训练结束按[回流记录](../TRAINING.md)完成交接。单题特有布局留在项目；
能用另一组输入验证的部件再进入公共包，附来源、最短示例和复跑结果。
