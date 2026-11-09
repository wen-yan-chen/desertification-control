# Practice2 · Desertification Control

团队练习题：**2026 CQU_MCM Problem B — Sand Control is Meticulous Work**。2027 MCM/ICM 备赛练习，不是 2027 正式赛题。

仓库：<https://github.com/wen-yan-chen/desertification-control>。本机唯一项目工作目录为 `C:\ModelingProgram\Practice2`；其他电脑克隆到各自固定目录即可，路径不必相同。

## 从哪里开始

1. [英文题目 PDF](Problem/2026_CQU_MCM_Problem_B.pdf) / Word 原题
2. [读题与约束登记](Docs/2026_CQU_MCM_B题_读题文档.md)（已纠正推荐年限、报告页数等口径）
3. [已有文献覆盖、缺口与建模接口](Docs/文献覆盖审计与建模接口.md)
4. [组员原有 32 项资料导航](Reference/00_阅读导航与资料清单.md)
5. [新增 16 项英文文献/报告](Reference/05_英文补充与来源核验/README.md)、[参数摘录与 7 项数据源说明](Reference/05_英文补充与来源核验/参数与数据源.md)
6. [三机协作与同步](Docs/协作同步.md)

## 目录约定

| 目录 | 内容 |
|---|---|
| `Problem/` | 原始赛题，保持源文件不改 |
| `Reference/01–04` | 组员已有 PDF、CAJ 及网页资料，保留原路径 |
| `Reference/05_英文补充与来源核验/` | 英文补充原文、阅读卡、DOI/哈希索引、BibTeX 和数据说明 |
| `Docs/` | 读题、文献审计、协作约定 |
| `Plan/` | 甘特图、时间计划与组员分工 |
| `Code/` | 数据抓取、预处理、建模与报告生成脚本；脚本以 `Code` 的上一级（项目根）为 BASE 定位同级目录 |
| `Data/` | 数据三层：`raw/`（原始）、`processed/`（清洗与特征）、`cache/`（接口缓存）；数据字典见 `Data/数据字典.md` |
| `Figures/` | 分析流水线生成的图（fig1–fig13，PNG） |
| `Results/` | 模型结果（model_results.json、逐站拟合、敏感性 CSV） |
| `Reports/` | 三份支撑报告（data_source/preprocess/model 的 tex+pdf）及 `figs/` |
| `Paper/` | 最终 LaTeX 论文：`main.tex` 入口，章节在 `Section/`，图在 `Figure/`，文献在 `bibliography/` |
| `archive/` | 全部合成样张与排版风格实验；**合成数据，不是本题研究结果**，见 [archive 说明](archive/README.md) |
| `Tools/` | 同步与文献完整性核验工具 |

大体量遥感/再分析数据不直接塞进 Git：保留下载脚本、清单、版本、校验和与处理后必要小样本；私钥、API 令牌和个人配置不提交。

## 当前状态（2026-11-09）

已接收远程资料、纳入本地题目和读题文档，新增英文资料并完成主要方法/关键页核验。已有 32 项与新增 16 项合计 48 项资料记录；不是 48 份已精读全文。16 份 CAJ 的正文参数仍需有阅读器的组员核验。目录已按 Practice1 风格平铺为英文根目录，并实际运行 `Code/03_modeling.py` 验证路径有效。

**尚未确定代表区段、下载区段时间序列、校准最终模型或求解最优方案。** 下一步优先确定沙漠边缘区段，补齐供水、覆盖度/水分、建设/运维/人工与电价资料，再实现统一模型。

开始工作前运行 `git pull --ff-only`，或在 PowerShell 中使用 `.\Tools\sync.ps1`。完成一项工作后明确选择文件、提交、推送，再通知队友拉取。远程推送不会自动刷新另外两台电脑。
