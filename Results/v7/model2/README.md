# M2 数值结果（不含图片）

生成器：`python Code/v7_model2.py`。模型、证据与局限见 [复核说明](../../../Docs/20261111_m2_audit_and_implementation.md)；[制图交接](../../../Docs/20261111_m2_figure_handoff.md)。所有量为情景计算，`formal_model_ready=false`。

| 文件 | 内容与单位 |
|---|---|
| `model2_results.json` | 输入/源码哈希、实际版本、求解记录、限制、基准回放误差 |
| `annual.csv` | 基准逐年新增/存量ha、PV kW、三类支出/收入CNY、人日、m³、有效ha、资源余量、资金比例、贴现净成本 |
| `monthly.csv` | 基准年×月人工毛取水m³、月供水上限与余量；包括PV清洗 |
| `decisions.csv` | 基准所选建植/光伏批次、策略、整数块数、面积或装机 |
| `cohorts.csv` | 生态批次×年，V百分数、M毫米、实际/潜在蒸腾比、灌溉深度/单位面积水量 |
| `cohort_water.csv` | 生态批次×年×月，完整M1土壤水量账；`*_mm`为面积归一化深度，乘`area_ha*10`才是m³ |
| `policy_library.csv` | 18种候选年补水路径的M1逐龄轨迹，年份为**林龄**而非项目日历年 |
| `pv_screening.csv` | 各建设年独立PV保本电价元/kWh、独立NPV元/kW；不含稀缺资源机会成本 |
| `scenario_summary.csv` | 33次优化状态、目标、界/gap、生态积分、净现成本、全期支出和最终规模；`group=threshold`为最低覆盖规则对照；`feasible=False`的行没有方案，其余表中也没有对应`case` |
| `scenario_annual.csv` | 各情景逐年方案，`case`为连接键 |
| `scenario_decisions.csv` | 各情景所选批次，`case`连接对应配置 |
| `scenario_monthly.csv` | 各情景逐月供水量、上限和余量 |
| `scenario_configs.json` | 每个`case`实际使用的参数、M1参数和策略名称 |

**最低覆盖规则（2026-11-11起）。** 生态积分只统计达标批次：`annual.csv`的`counted_effective_ha`是计分量，`effective_ha`仍是全部批次的物理量；`cohorts.csv`的`counts_toward_score`、`policy_library.csv`的`meets_min_cover`标明批次/路径是否达标（基准为林龄10年末V≥20%）。`scenario_summary.csv`的`ecological_ha_year`与目标值均按计分量。本次`initial_cover_low`在同一绝对目标下不可行，属于正常记录，不得补造路径。

`year`从1开始；资本发生于该年年初，运维与发电收入发生于年末；PV建设年没有发电，次年投产收益。生态`V_start_pct`决定当年`effective_ha`，`V_end_pct`为年末状态；不能混用。V与M均跨年继承。

`effective_ha=sum(area_ha*V_start_pct/K)`，逐年相加才是生态目标“有效ha·年”；不是裸地消失面积，也不是实测防沙面积。`relative_erosion_scenario`从M1原样带出，不能将它转为M2的已识别减蚀效益。

三类资金比例为建设/运维（含水）/PV设施资本费除当年总支出，0支出年留空。总预算余额扣未贴现毛支出，不加发电收入。净现成本可以为负（零生态要求的纯PV情景），负数不意味着治理可以无预算实施。

`dual_bound_scaled`：成本最小化时单位为**百万元**，是净现成本下界；最大生态时优化的是`-H/1000`，故取`-1000*dual_bound_scaled`得到生态上界。`mip_gap`为比例，乘100显示百分数。无可行解时不得连接或补齐曲线；本次记录均可行。
