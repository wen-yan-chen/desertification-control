# M1 图（v7 数值实现）

由 `python Code/v7_m1_figures.py` 生成（仓库 `.venv`，matplotlib 3.9）。只读 `Results/v7/model1/` 的表格与 `model1_results.json`，不重跑模型。每张图有 PDF（LaTeX 引用）和 PNG（预览）。英文标注，Times 字体，宽度按 MCM 正文 6.3 in。

| 文件 | 内容 | 数据来源 |
|---|---|---|
| `m1_f01_station_series` | 7 站覆盖代理 V（2015—2025）、一步预测、2022 起自由推演、持续性基线、局地 K | `yearly_table`, `prediction_pairs`, `free_running_holdout` |
| `m1_f02_holdout_skill` | (a) 训练/留出观测—预测散点；(b) 各站留出 RMSE 与持续性对比，含负技能 | `prediction_pairs`, `holdout_by_site`, json |
| `m1_f03_parameter_bootstrap` | r–d 站点整簇 bootstrap、留一站估计、合并拟合与 95% 分位 | `parameter_cluster_bootstrap`, json |
| `m1_f04_cohort_diagnostic` | 区段像元回溯诊断：CON1–3 标定窗、CON4 空间诊断与迁移曲线 | `cohort_diagnostic_pairs`, json |
| `m1_f05_forcing_climatology` | 2015—2022 月降水、ET0/ET0g、风指数 E | `section_forcing_climatology` |
| `m1_f06_water_cover_curve` | 灌溉—稳态 V、W、M、相对侵蚀（mm/yr 与 m³/ha/yr 双刻度） | `water_cover_curve` |
| `m1_f07_scenario_trajectories` | 2026—2050 情景 V、M、W（6 档恒定灌溉 + 600 mm 十年后停灌） | `scenario_annual` |
| `m1_f08_monthly_water_balance` | 300 mm/yr 下 2050 年逐月收支、蒸腾供需；三情景逐月储水 | `scenario_monthly_water` |
| `m1_f09_sensitivity` | 300/600 mm/yr 下水分参数龙卷风图；风损伤 k 情景 | `sensitivity`, `water_cover_curve` |

界限线统一为红色虚线（与 M2 图共用 `LIMIT` 样式）：各站局地 K（图 1）、迁移曲线平台值（图 4）、
W = 1 与储水容量 75 mm（图 6b、6c）、储水容量（图 8c）。红色只用于界限，不用于数据系列。
留出期灰色底纹（图 1）、bootstrap 95% 分位线（图 3）、E = 1 参考线（图 5）、停灌时刻竖线（图 7、8）
是时段、区间或事件标记，不是界限，保持灰色。图 2、3、5、7、9 未改动。

使用注意（图中已去掉脚注，请写进论文图注）：

- V 是 NDVI 端元覆盖代理，不是实测地面覆盖度；W 是蒸腾满足率，不是土壤含水量。
- 模型留出 RMSE 0.0635 未优于持续性 0.0536，图 2 保留负技能值，正文不得写成“优于基线”。
- 图 4 为回溯选择的像元，不是独立预测验证。
- 水分参数、k、相对侵蚀均为情景假设，`formal_model_ready=false`。
- 灌溉 mm 为处理面积水深，未换算全项目水量。
