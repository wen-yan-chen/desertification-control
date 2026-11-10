# Data/v7 —— 2026 CQU_MCM B 题数据（重新采集版）

> **M1 当前数据入口是 [m1_audited/](m1_audited/README.md)**。
> 以下 `processed/` 是原 v7 快照，含已确认的窗口 QA 和派生变量口径问题，不能直接作为当前 M1 输入。
> 重放清单及逐像元修正另存；本轮不将历史表静默覆盖。

> **仓库版说明**：原始响应（`raw/*.json`、`_cache/`）体积约 14 MB，**不入库**；
> 仓库内保留 `raw/manifest.json`（672 个请求的 URL + SHA256）与 `processed/` 全部处理后数据。
> 需要原始响应时运行 `Code/v7_fetch.py` 重放，哈希可逐一核对。


生成时间：2026-11-10　　全部数据由 `Code/v7_*.py` 重新抓取，未引用工作区任何既有 CSV。

## 目录

| 路径 | 内容 |
|---|---|
| `raw/power_monthly_{CODE}.json` | NASA POWER 月度产品，16 参数，2015-01—2025-12 |
| `raw/power_daily_{CODE}.json` | NASA POWER 日值，10 参数，4018 天 |
| `raw/modis_{CODE}_NDVI.json` | MOD13Q1 NDVI，9×9 像元窗口，253 期/站（已按 modis_date 去重） |
| `raw/modis_{CODE}_QA.json` | MOD13Q1 像元可靠性（0—3 级） |
| `raw/era5land_{CODE}.json` | Open-Meteo ERA5/ERA5-Land 日值，14 变量 |
| `raw/soil/*.json` | SoilGrids 逐属性/逐深度请求：81 项中成功 62 项（库尔勒全缺、若羌/尉犁/阿拉尔部分缺），覆盖不完整，未纳入面板 |
| `raw/manifest.json` | 672 个响应的 URL / 字节数 / SHA256 / 抓取时间 |
| `_cache/modis/` | MODIS 分块原始响应（断点续跑用，与 raw 中合并结果一致） |
| `processed/panel_monthly_raw.csv` | 合并后未清洗面板（1188 行 × 45 列），供审计复现 |
| `processed/panel_monthly_clean.csv` | 清洗 + 派生后面板（1188 行 × 62 列），建模输入 |
| `processed/features_train.csv` / `features_test.csv` | 2015—2022 / 2023—2025 特征表 |
| `processed/norm_params.json` | 仅用训练期拟合的归一化与标准化参数 |
| `processed/qc_summary.json` | 本次预处理的审计与填补记录 |
| `processed/panel_monthly_clean.xlsx` | 同内容 Excel（不入库，由脚本生成） |
| `processed/soil_profile.csv` | 土壤剖面（本轮为空：SoilGrids 仅 62/81 成功，覆盖不完整故未纳入） |

## 站点

| 代码 | 名称 | 纬度 | 经度 | 角色 |
|---|---|---|---|---|
| YT | 于田 | 36.85 | 81.67 | 南缘锁边区段 |
| MF | 民丰 | 37.06 | 82.68 | 南缘锁边区段 |
| QM | 且末 | 38.13 | 85.53 | 南缘锁边区段 |
| RQ | 若羌 | 39.02 | 88.17 | 东南缘锁边区段 |
| KEL | 库尔勒 | 41.76 | 86.15 | 北缘 |
| YL | 尉犁 | 41.34 | 86.26 | 北缘 |
| ALE | 阿拉尔 | 40.55 | 81.28 | 西北缘 |
| XT | 肖塘 | 38.83 | 84.02 | 沙漠公路走廊 |
| TZ | 塔中 | 38.97 | 83.65 | 腹地对照 |

注：肖塘与塔中落入同一个 MERRA-2 格点，气温序列逐月完全相同（气象独立样本 8 个，不是 9 个）。

## 已知口径（预处理时必须遵守）

1. POWER 月度 `PRECTOTCORR`、`EVLAND`、`ALLSKY_SFC_SW_DWN` 是**日均值**：月总量 = 原值 × 当月天数。
2. POWER 月度返回的 `YYYY13` 是**年均行**，不是 13 月，必须剔除（本数据每站 11 条）。
3. MODIS NDVI 为 int16，×10⁻⁴；填充值 −3000（缩放后 −0.3）。
4. Open-Meteo 交付风速为 **km/h**，需 ÷3.6；土壤含水量为 m³/m³，与 POWER 的 GWETROOT（0—1 饱和度）**不可混用**。
5. Hargreaves 公式中的 Ra 需 ×0.408 由 MJ m⁻² d⁻¹ 换算为 mm/d。
6. 缺失值：`ndvi_mvc_qa` 有 110 个站—月（9.26%），其余字段为 0。

## 复现

```powershell
python Code/v7_fetch.py            # 抓取（断点续跑）
python Code/v7_finalize_fetch.py   # 合并 MODIS + 重建 manifest
python Code/v7_clean.py            # 体检 + 预处理 + QC 报告
python Code/v7_ablation.py         # 五套方案消融
python Code/v7_figures.py          # 图 1—7
python Code/v7_report.py           # 生成 Word 报告
```

