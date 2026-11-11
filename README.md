# Desertification Control

2026 CQU_MCM Problem B — Sand Control is Meticulous Work，团队数学建模练习项目。

## 项目入口

| 内容 | 位置 |
|---|---|
| 赛题 | [Problem/](Problem/) |
| 最终论文 | [Paper/main.tex](Paper/main.tex) |
| M1 公式、数据审计与证据边界 | [M1 审计与实现](Docs/20261110_m1_audit_and_implementation.md) |
| M1 输入 | [Data/v7/m1_audited/](Data/v7/m1_audited/README.md) |
| M1 计算结果 | [Results/v7/model1/](Results/v7/model1/README.md) |
| M2 复核与实现 | [M2 审计说明](Docs/20261111_m2_audit_and_implementation.md) |
| M2 情景输入与数表 | [参数登记](Data/v7/m2_inputs/README.md) / [结果说明](Results/v7/model2/README.md) |
| M2 制图交接 | [给 Claude 的数表说明](Docs/20261111_m2_figure_handoff.md) |
| M2 图 | [Figures/M2/](Figures/M2/README.md) |
| 代码与运行方法 | [Code/](Code/README.md) |
| 建模与预处理报告 | [Reports/](Reports/README.md) |
| 文献与来源 | [Reference/](Reference/00_阅读导航与资料清单.md) |
| 图表和流程图样式 | [FigureAndFlowworkStyle/](FigureAndFlowworkStyle/README.md) |
| 团队协作 | [协作同步](Docs/协作同步.md) |

## 当前模型

M1 已实现条件合并标定、有效储水动态、逐像元 QA、水量闭合和情景计算。数据入口为
`Data/v7/m1_audited/`，数值出口为 `Results/v7/model1/`。公式参考
`Reports/model_v7/model_v7.tex` 第 3 节（任务一，已并入复核更正）。

当前结果保留 `formal_model_ready=false`。水分和风损伤参数仍需现场证据，区段工程边界、
可用水量、成本和劳动力约束仍待补充。M2 已完成批次动态优化、预算/水量/劳动约束、
光伏资产现金流、成本—生态权衡及敏感性数表，仅作条件情景；7 张图已由数表生成，见 `Figures/M2/`。
任务三的韧性计算尚待实现验证。

在仓库根目录运行。

```sh
python -m pip install -r Code/requirements-m1.txt
python Code/v7_model1.py
python -m unittest discover -s Code -p test_v7_m1.py -v
python Code/v7_model2.py
python -m unittest discover -s Code -p test_v7_m2.py -v
python Tools/check_references.py
```

Python 版本要求为 3.11 及以上。已提交的小表支持离线运行 M1。
重建数据时依次运行 `Code/v7_replay_m1.py`、`Code/v7_prepare_m1.py`。

## 数据与文献

v7 月面板覆盖 9 个点位和 2015—2025 年，共 1188 行。来源包括 NASA POWER、
MODIS MOD13Q1、Open-Meteo 历史归档和 SoilGrids。原始请求与哈希保存在
`Data/v7/raw/manifest.json`，数据结构与处理口径见 [数据说明](Data/v7/README.md)。

`Data/v7/processed/` 保存预处理对比材料。经复核的 M1 输入和 QA 记录位于
`Data/v7/m1_audited/`，模型运行方法见 [代码说明](Code/README.md)。

参考资料按水盐灌溉、风沙韧性、经济优化、工程背景和英文补充组织。
原有索引为 `Reference/资料索引.json`，英文补充索引为
`Reference/05_英文补充与来源核验/sources.json`。

## 目录用途

| 目录 | 用途 |
|---|---|
| `Problem/` | 赛题原文件 |
| `Reference/` | 文献、网页存档、题录与来源核验 |
| `Docs/` | 读题、当前模型审计、文献接口与协作说明 |
| `Plan/` | 计划与分工 |
| `Code/` | M1/M2 实现、输入重建、预处理与对比工具 |
| `Data/v7/` | 请求清单、面板和经复核输入 |
| `Results/v7/` | 审计、对比材料及 M1/M2 数值结果 |
| `Figures/M1/` | 当前 M1 数表生成的图片 |
| `Figures/M2/` | 当前 M2 数表生成的图片（`python Code/v7_m2_figures.py`） |
| `Figures/v7_init_test/` | 初版预处理与模型图，使用时核对对应数据版本 |
| `Reports/` | 建模与预处理报告 |
| `Paper/` | 论文源码、章节、图片与文献库 |
| `FigureAndFlowworkStyle/` | 图表样张、生成脚本和流程图样式 |
| `Tools/` | 同步和完整性核验工具 |

开始工作前按 [协作说明](Docs/协作同步.md) 同步仓库。完成修改后选择实际文件提交、推送。
原始响应、个人环境和编译缓存按 `.gitignore` 管理。
