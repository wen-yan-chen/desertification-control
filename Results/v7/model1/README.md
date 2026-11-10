# 当前 M1 数值结果（无新图片）

入口：`python Code/v7_model1.py`。输入为 `Data/v7/m1_audited/`。

`input_text_sha256_lf` 对文本输入先统一为 LF 再计算，避免三台电脑的 Git 换行转换造成伪差异；原始响应清单的哈希仍严格按原始字节计算。

| 文件 | 含义与 Claude 制图用途 |
|---|---|
| `model1_results.json` | 参数、训练/留出指标、数据哈希、运行环境、限制条件 |
| `yearly_table.csv` | 年度覆盖代理、局地 K、风指数、每年有效月份数 |
| `prediction_pairs.csv` | 训练与留出逐对观测/预测/持续性基线；覆盖指标 x=V/K |
| `holdout_by_site.csv` | 各站误差及相对持续性基线技能，负值必须保留 |
| `free_running_holdout.csv` | 从 2022 出发连续推演 2023—2025，不逐年读入真值 |
| `parameter_cluster_bootstrap.csv` | 300 次站点整簇重采样；只有 7 簇，不作高精度置信承诺 |
| `cohort_diagnostic_pairs.csv` | 回溯性筛选像元的空间诊断，不能标“独立预测验证” |
| `section_forcing_climatology.csv` | 2015—2022 于田/民丰气象季节气候态 |
| `water_cover_curve.csv` | 假设水分参数下的周期稳态，双初值与收敛残差 |
| `scenario_annual.csv` | 14 个情景的 2026—2050 年植被与水分状态、灌溉 |
| `scenario_monthly_water.csv` | 每月储水、入水、蒸腾、深层排水与守恒残差 |
| `sensitivity.csv` | 水分容量、有效降水、效率、端元等假设及风损伤情景 |

`V` 单位是旧端元定义的 NDVI 覆盖代理百分点，不是直接观测的地面覆盖度；`local_endmember_cover_proxy` 仍是遥感端元假设。`relative_erosion_scenario` 只是遮蔽函数，不是实证减蚀率。

`M` 单位 mm，为高于凋萎点的有效储水；`W` 是年度实际/潜在蒸腾比，**不能把 W 当成土壤含水量**。灌溉 mm 为处理面积上的水深，乘 10 得 m³/ha；未提供真实区段面积，不自动换算全项目水量。

基准年度气象重复用于未来情景，不是未来天气预报。14 个情景包括 13 档恒定灌溉，以及前 10 年 600 mm/年、随后停灌。实际储水和灌溉数据不足，`formal_model_ready=false`。

原 `Figures/v7/m1_fig*.png` 与 `Reports/M1/model1_v7_*` 的旧数字已失效；本轮不重绘，Claude 应从以上新表制作图片。
