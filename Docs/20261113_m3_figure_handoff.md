# 给 Claude 的 M3 绘图交接（2026-11-13）

M3计算已完成，不需重做M1/M2。本轮没有生成图片。数据只读 `Results/v7/model3/`；作图前核对 `model3_results.json` 的输入哈希。颜色与排版继续由绘图手决定，可沿用目前论文MATLAB图风格。

| 建议表达内容 | 文件与选择 | 关键口径 |
|---|---|---|
| 继承M2后各批次覆盖演化 | `cohort_annual`，case=base_nonstationary；V_mean/p05/p95，初值见initial_cohorts | 3批次面积不同；post_year=0是项目第15年末；绘制约11.423%退化参考线，不能画成30% |
| 首次退化与当前状态的区别 | `cohort_annual`的failure_probability/current_below_threshold_probability；或project_annual的两类面积 | 曾退化曲线单调不减，当前低覆盖可恢复；不能把累计首达写成永久毁坏 |
| 非平稳与平稳风险/效益 | `project_annual`，base_nonstationary、stationary_reference、no_random_disasters | 基准与平稳都含灾害；no_random_disasters仍含气候趋势。覆盖积分可展示随机分位带，不标统计置信带 |
| λ—平均损失的联合敏感性 | `summary`筛选joint_rate_*且entity=project；读configs中的λ与U上下界 | 3×3仅9个假设点；可画方格，不外推成精细实测连续曲面。50年概率易饱和，可同时画RMST或10年风险 |
| 资源与事件机制对照 | summary、project_annual：water_80pct/120pct、no_irrigation、storm_at_year_start、independent_cohort_storms、no_drought_storm_association | 多申请水量可能被月供水能力限住；独立/共同灾害是关联情景，不能预设谁总更安全 |
| 供水配给与干湿背景 | `resources`的申请/实际、gross_water_m3/cap_m3、P/ET0g、wind_speed_scale | 每个年有正常/旱年两组条件数据，不可直接相加作一年取水；湿润代理用全年ΣP/ΣET0g，冬季月ET0g可能为零 |
| 数值验证 | `markov_mc_comparison`、`grid_validation`、`markov_cross_grid` | 仅平稳子模型；最细网格9个检查点进入MC区间，不能标“实测验证”；中等网格未进区间的点保留 |
| 示例灾后恢复轨迹 | `sample_paths`固定前12条，选取前说明规则 | 数据是示意子集，不可从12条路径估计概率；首次退化后物理状态继续更新 |

## 图注必须交代

- 这是未标定灾害参数与未来趋势下的 **scenario / stress test**；不是塔克拉玛干实际灾害预报。不要把基准高风险写成“工程必然失败”。
- 27组情景；基准与平稳各6000条路径，其余3000。所有概率区间只反映MC误差；不含M1参数、事件率、气候和结构不确定性。
- 项目事件：同一年至少50%治理面积低于0.30K（约11.423%覆盖代理）。不是平均覆盖下降50%，也不是M2讨论过的防护达标门槛。
- RMST是50年窗口内的受限平均首达时间；不写成工程寿命。删失编码51不得画成第51年实际失败。
- 默认年末冲击；先年初冲击的情景单独标注。风沙冲击合并磨蚀、沙埋，干旱通过土壤水量和供水能力进入。
- 相同天气和风沙冲击可同时作用多个批次；不能将三个边际生存概率相乘生成项目图。
- 基准第50年项目事件命中率为100%，Wilson下限约99.936%；不能画零宽置信区间。当前低覆盖期望面积约200.22 ha，与曾越界面积约299.45 ha不同。
- 未计算未来PV收益、设施更换和养护融资，不用M3数表制造长期NPV图。效益积分是覆盖代理有效ha·年，不是实际防沙面积、固碳量或减蚀吨数。

更新模型公式以 `Reports/model_v7/m3_correction.tex` 为准；旧检验报告里的M3设计公式已在本轮纠正。当前结果与说明见 [复核文档](20261113_m3_audit_and_implementation.md)。
