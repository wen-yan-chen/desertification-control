# Code/ · v7 数据流水线与预处理

本目录只保留 **2026-11-10 重新采集** 的流水线。旧版抓取/组装/建模/报告脚本已删除，
历史实现见 `archive/invalidated_20261109/`（不可作为当前结果）。

## 数据流水线（按顺序运行）

| 顺序 | 脚本 | 作用 | 产物 |
|---|---|---|---|
| 1 | `v7_fetch.py` | 抓取 NASA POWER（月/日）、MODIS MOD13Q1、Open-Meteo ERA5、SoilGrids | `Data/v7/raw/*.json`、`raw/_cache/modis/` |
| 2 | `v7_finalize_fetch.py` | 合并 MODIS 分块、按文件重建 SHA256 清单 | `raw/modis_{站}_{NDVI,QA}.json`、`raw/manifest.json` |
| 3 | `v7_clean.py` | 七项体检（缺失/异常/重复/类型/量纲/不平衡/时序）+ 派生 + 训练期隔离 | `Data/v7/processed/panel_monthly_{raw,clean}.csv`、`Results/v7/qc_report.json` |
| 4 | `v7_missing.py` | 缺失专项：图谱、MCAR 检验、五种插补对比、真实缺失敏感度 | `Results/v7/missing.json`、`tab_impute_compare.csv` |
| 5 | `v7_ablation.py` | 五套预处理方案消融（任务一/二/三复算） | `Results/v7/ablation.json`、`tab_ablation_*.csv` |
| 6 | `v7_figures.py`、`v7_fig_pre.py` | 生成报告用图 | `Figures/v7/*.png` |

## 双语言预处理脚本（面向使用者）

| 文件 | 说明 |
|---|---|
| `preprocess_v7.py` | Python 主程序：路径提示、异常处理、逐步中间结果、前后可视化、完整性断言；输出 CSV/XLSX/JSON |
| `preprocess_v7.m` | MATLAB R2020b+ 等价实现，只用内置函数；输出 `panel_monthly_clean_matlab.csv` |

两者输入都是 `Data/v7/processed/panel_monthly_raw.csv`，输出可逐列比对。
MATLAB 版**尚未在真实 MATLAB 环境运行过**，首次使用请自行校验（脚本内含断言）。

## 依赖

```bash
pip install pandas numpy matplotlib openpyxl scipy
```

- Python 3.8–3.11
- MATLAB R2020b 及以上（无需工具箱）

## 说明

- 原始响应体积较大（约 14 MB，672 个文件），**不入库**；`Data/v7/raw/manifest.json` 保存了每个请求的
  URL、字节数与 SHA256，可用 `v7_fetch.py` 完整重放。
- 仓库内 `Data/v7/processed/` 保留了处理后的面板与元数据，可直接用于建模，不必重新抓取。
