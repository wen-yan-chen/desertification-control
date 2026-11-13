# M3 数表（2026-11-13）

这是条件灾害情景的数值交付，**不含新图片**。生成入口 `Code/v7_model3.py`，追加离散检验 `Code/v7_m3_grid_check.py`。
[模型复核](../../../Docs/20261113_m3_audit_and_implementation.md)、[参数与证据](../../../Data/v7/m3_inputs/README.md)、[Claude交接](../../../Docs/20261113_m3_figure_handoff.md)。

| 文件 | 粒度及用途 |
|---|---|
| `model3_results.json` | 所有输入/源码的LF规范化哈希、当前M1参数、环境、接口回放及每情景水量误差、限制 |
| `initial_cohorts.csv` | M2第15年末实际各批次状态；本表`year`仍是项目年 |
| `scenario_configs.json` | 27情景的完整参数，用`case`连接 |
| `cohort_annual.csv` | 情景×批次×后评估年：V均值/5、50、95分位，M均值，曾越界/当前越界概率，前者的Wilson区间 |
| `project_annual.csv` | 情景×后评估年：同时低覆盖面积触发的首次项目事件概率、期望曾失败面积/当前低覆盖面积、覆盖面积与累计积分 |
| `summary.csv` | 情景×实体（3批次及project）：50年首达概率、Wilson区间、RMST及其MC标准误、删失数、终年覆盖均值 |
| `first_passage_counts.csv` | 首次越界年份频数；0表示初始就不达标，51为超过50年仍未命中的**删失编码**，不能当第51年发生 |
| `sample_paths.csv` | 每情景固定前12条路径×批次×年度，供示意；不是随机过程全集，不能用它重新估计风险 |
| `resources.csv` | 每情景×年×正常/干旱×月：毛取水/能力/余量、生态申请及实际供水、P和ET0g、风速倍率。两种旱情是条件资源表，不是每年都发生两次供水 |
| `markov_survival.csv` | 平稳子模型3套网格下各批次首达概率；不能当非平稳基准或项目联合概率 |
| `markov_diagnostics.json` | 状态数、矩阵非零项、行和、条件无限期首达均值/方差、线性系统残差、泊松尾和分位积分误差 |
| `markov_mc_comparison.csv` | 平稳链与独立物理MC在10/30/50年的对照，保留未进入MC区间的点 |
| `markov_cross_grid.csv` | 161×21网格配96冲击节点的附加曲线，用于隔离误差来源 |
| `grid_validation.csv`,`validation_summary.json` | 单独加密状态网格/冲击积分的误差、MC对照与已导出数表核验 |

除初态表外，`post_year=0`为M2完工时；`post_year=1`为项目第16年。V单位为百分数（17表示17%），M为有效储水mm，水量m³，面积ha，积分有效ha·年。`failure_cover_fraction_K=.3`是K的30%，不等于30%绝对覆盖。

`failure_probability`为首次年度低于阈值的累计概率，必随时间不减；`current_below_threshold_probability`可因恢复下降。project是**同年**至少50%面积低于阈值的首次事件，不是批次概率的独立乘积。

RMST=E[min(τ,50)]，不是无条件平均寿命。`censored_count`记录未在期限内失败的路径，95%Wilson区间即使样本全部失败也不退化为单点。5–95%路径分位带不是均值95%置信区间。

`cumulative_cover_ha_year_*`延续M2线性覆盖代理积分，未宣称实测减蚀效益。项目平均V应按面积加权，不能等权平均三批次。水量余量约−4e−11 m³属于浮点舍入，计算断言容差1e−7 m³。
