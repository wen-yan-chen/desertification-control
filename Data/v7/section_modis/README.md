# Data/v7/section_modis — 于田—民丰区段 MODIS 派生小表

> 复核更正：converted 像元按后期变绿筛选，建植年份使用未来观测。
> 这里只作回溯空间诊断，不能作严格独立预测验证；下文 independent check 是旧版表述。
> 裁剪后的 FVC 在端元外反算不回原始 NDVI，局地端元也不是地面覆盖真值。

Copied unchanged from branch `model1-first-version` (commit 270e468); produced there by
`Code/m1_fetch_data.py` + `Code/m1_build_dataset.py` from MOD13Q1 v061 (ORNL DAAC), 2001–2024,
with `pixel_reliability` 0/1 only. Used by `Code/v7_model1.py` as an independent check.

| File | Content |
|---|---|
| `cohort_converted.csv` | 217 pixels that went from bare sand to vegetation; cover by year since establishment (`tau`) |
| `class_annual_fvc.csv` | yearly peak-season cover by land class (converted / ecotone / desert / oasis) |
| `windows.csv` | the eleven 9×9-pixel windows and their coordinates |
| `endmembers.json` | NDVI of bare sand (0.0505) and dense oasis (0.5827) on this section |
| `daily_model_water_cover_curve.csv` | water–cover curve of the earlier daily model, reference only |

`fvc` here uses the local end-members above. `v7_model1.py` converts it to v7 units
(end-members 0.05 / 0.85) before use.
