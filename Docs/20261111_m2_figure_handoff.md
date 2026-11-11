# 给 Claude 的 M2 制图交接

本轮只提供模型、代码和数表，未生成图片。当前数据入口 `Results/v7/model2/`，不要使用 `v7_ablation.py` 的历史 Task2 NPV 或 `Figures/v7_init_test/` 反推新结果。M1图片已完成，无需为了M2重画。

## 建议表达的内容（图形结构由绘图手决定）

| 内容 | 数据文件及字段 | 需要保留的含义 |
|---|---|---|
| 15年建设与养护进程 | `annual.csv`：new_area_ha、eco_area_ha、new_pv_kw、pv_operating_kw、三类fund_share | 新增面积为流量，累计面积/装机为存量；资金比例不是光伏占地比例；PV次年才发电 |
| 逐批植被恢复与补水 | `cohorts.csv`：cohort_id、year、V_start/end_pct、M_start/end_mm、irrigation_mm_yr、area_ha | 项目年和林龄不同；年内收益使用V_start；小批次不可和大批次等权当项目均值 |
| 年/月水资源压力 | `monthly.csv`或`scenario_monthly.csv`：gross_water_m3/cap_m3、slack_m3 | 包含所有存量面积及PV清洗，均为人工毛取水；上限本身是情景，不能标“当地许可量” |
| 生态—经济权衡 | `scenario_summary.csv`筛选group=frontier：ecological_ha_year、net_present_cost_cny、mip_gap | 6个离散可行点，基准60%已包含，不重复画；不平滑成已求得的连续完整前沿；净现成本越低越好 |
| 投资结构敏感性 | `scenario_summary.csv`的base、no_pv、pv_price_low/high、pv_capex_low/high、om_low/high、pv_share_min_*；配合scenario_annual | 固定相同的绝对生态目标；价格变动情景不能被解释成真实概率或置信区间 |
| 关键假设与策略空间检验 | initial_cover_low/high、storage_low/high、water_low、finer_area_grid、constant_irrigation_only | 初始植被影响很大；面积细化约0.22%的净成本变化与约0.20%求解容差同量级，不能据此宣称收敛 |
| 光伏独立立项筛查 | `pv_screening.csv`：start_year、break_even_price_cny_kwh | 只能筛查单项目财务，不是系统最优占比/收益保证；还要看水、地、劳动和预算机会成本 |

## 统一口径

- 面积ha（hm²）；1 mm×1 ha=10 m³。金额原表CNY，画万元除1e4，百万元除1e6；PV kW转MW除1000。人日不能写人数。
- 生态积分为覆盖代理达成率面积时间积分，不是观测生态价值、因果新增面积或减蚀吨数。长期曲线标 **scenario**，不用 **forecast**。
- 基准300 ha与9.5 MW只适用于参数登记中的情景，不能写成本地推荐实施规模。最大生态参考不是拟合优度，也不是M1的K。
- 95%置信带不存在；敏感性区间标“assumption scenarios”。MIP gap为数值最优性界，不是统计误差棒。
- 无支出年的资金比例为空是合理数据；不能用插值创造投资。不可行情景不应补造路径，本次29次计算均可行。
- 图中可用短标题保持简洁，以上限制应进入对应论文图注/正文；继承M1图形的颜色角色时，新增建设、存量养护、PV资本、用水尽量保持一致。

作图前可比对 `model2_results.json` 的输入哈希，版本不同不要混接。详见 [复核与实现](20261111_m2_audit_and_implementation.md)、[参数证据登记](../Data/v7/m2_inputs/README.md)。
