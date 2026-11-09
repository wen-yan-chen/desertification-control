# 当前数据字典与使用边界（2026-11-09）

## 1. 已取得的NASA POWER月数据

`raw/nasa_power_verified/monthly.csv`：960行，8点各120月，2015-01至2024-12。每点原JSON与`manifest.json`记录请求、返回元数据和SHA256。经API格点提取，不是现场测量。

|字段|单位|解释|
|---|---|---|
|station|代码|对应旧站点表的请求坐标，不代表NASA地面站|
|month|YYYY-MM|仅保留月份01--12，排除接口年度汇总项13|
|WS10M|m/s|10米风速月平均，不能用于直接计算小时阈值输沙|
|T2M|°C|2米气温月平均|
|PRECTOTCORR|mm/day|当月日均降水率，不是整月累计量|
|ALLSKY_SFC_SW_DWN|kWh/m²/day|水平面短波辐照日均值，不是装机发电量|

`processed/audited/nasa_power_monthly.csv`额外包含`days`（公历当月天数）与`precip_mm_month=PRECTOTCORR*days`（mm/月）。闰年2月按29天计。数据未截尾、未插补，不向未来外推。

## 2. 旧原始面板及新探索面板

旧原始表 `raw/01_站点月尺度面板_real_raw.csv` 960×18，未更改。旧源模型未固定、原API缓存缺失；不能断言全部气象字段是ERA5-Land。旧`输沙率`并非实测，`植被覆盖度`是未经QA核验的固定端元派生量。旧字典已留在失效历史目录。

`processed/audited/exploratory_panel.csv`仅供诊断，移除了`输沙率、输沙势、植被覆盖度、端元方案`。其余字段：

|字段|单位/类型|限制|
|---|---|---|
|月份、站点、站代码|文本|按站/月唯一|
|经度、纬度|角度|请求点而非研究区边界|
|地表类型|文本|旧人工标签，待GIS核验|
|风速、风速日最大_月均|m/s|旧API派生，来源模型未明确；后者是日最大值的月均|
|降水|mm/月|旧API日降水累加|
|气温|°C|旧API日平均气温的月均|
|土壤含水率_0_7cm、土壤含水率_0_100cm|体积百分数|旧API层值/组合，非实测根区有效水；换为体积分数需除100|
|NDVI|无量纲|旧MODIS月最大合成，缺QA及原响应；不自动换为覆盖度|
|样本天数|天|旧日数据计数，不等于晴空遥感有效样本数|
|ndvi_quality_status|文本|明确QA缺失，仅探索|
|meteorology_source_status|文本|明确旧模型未固定且非站测|
|elapsed_years_since_2015|年|时间索引，不是真实治理年限|
|split|train/test|2015--2022 / 2023--2024；并不代表已完成无泄漏模型训练|

## 3. 来源诊断与失效结果

`processed/audited/anchor_verification.csv`登记A01--A16逐项核验状态，当前全部`pending_source_verification`，`model_parameter_eligible=False`。原锚点数值保持原样，不能自动用于标定。

`Results/audit/matched_height_source_comparison.csv`含总体及8点的风、温、雨对比：n、单位、旧值减POWER的均偏差、RMSE、Pearson r、相对POWER的agreement R²。两套产品的比较不能证明谁接近地面真值；负R²保留。

`Results/audit/legacy_sand_targets.csv`揭示旧输沙目标缩放，不是新数据；`Results/audit/audit.json`记录审计状态及未关闭条件。

旧清洗、特征、训练/测试集、缩放参数、模型结果及论文图均归档至 `archive/invalidated_20261109/`。当前没有可声明已经校准的正式模型数据集。
