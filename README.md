# Practice2 · Desertification Control

团队练习题：**2026 CQU_MCM Problem B — Sand Control is Meticulous Work**。2027 MCM/ICM 备赛练习，不是 2027 正式赛题。

仓库：<https://github.com/wen-yan-chen/desertification-control>。本机唯一项目工作目录为 `C:\ModelingProgram\Practice2`；其他电脑克隆到各自固定目录即可，路径不必相同。

## 从哪里开始

0. **[2026-11-10 审计复核与模型一（英文）](Docs/20261110_audit_check_and_model1.md)**、[给 Astra 的交接说明](Docs/HANDOFF_to_Astra.md)：模型一第一版已可运行（`Code/m1_*.py`），下面的11-09审计结论仍保留供追溯。

1. **[2026-11-09模型与数据审计](Docs/20261109_模型与数据审计.md)**、[修正模型规范](Reports/model.pdf)、[数据字典](Data/data_dictionary.md)
2. [英文题目 PDF](Problem/2026_CQU_MCM_Problem_B.pdf) / Word 原题
3. [读题与约束登记](Docs/2026_CQU_MCM_B题_读题文档.md)（已纠正推荐年限、报告页数等口径）
4. [已有文献覆盖、缺口与建模接口](Docs/文献覆盖审计与建模接口.md)
5. [组员原有 32 项资料导航](Reference/00_阅读导航与资料清单.md)
6. [新增 16 项英文文献/报告](Reference/05_英文补充与来源核验/README.md)、[参数摘录与 7 项数据源说明](Reference/05_英文补充与来源核验/参数与数据源.md)
7. [三机协作与同步](Docs/协作同步.md)

## 目录约定

| 目录 | 内容 |
|---|---|
| `Problem/` | 原始赛题，保持源文件不改 |
| `Reference/01–04` | 组员已有 PDF、CAJ 及网页资料，保留原路径 |
| `Reference/05_英文补充与来源核验/` | 英文补充原文、阅读卡、DOI/哈希索引、BibTeX 和数据说明 |
| `Docs/` | 读题、文献审计、协作约定 |
| `Plan/` | 甘特图、时间计划与组员分工 |
| `Code/` | 当前真实数据获取与审计工具，见目录README；旧正式模型入口已停用 |
| `Data/` | `raw/`保留原响应和来源状态；`processed/audited/`为来源诊断与探索数据；见数据字典 |
| `Figures/audit/` | 同高度再分析产品对比，非现场真值验证 |
| `Results/audit/` | 审计表及未关闭条件，不包含正式模型结论 |
| `Reports/` | 修正模型规范（tex+pdf），尚未校准 |
| `Paper/` | 最终 LaTeX 论文：`main.tex` 入口，章节在 `Section/`，图在 `Figure/`，文献在 `bibliography/` |
| `archive/` | 合成风格样张及单独标记的失效历史快照`invalidated_20261109/`；均不可作为当前实证结果 |
| `Tools/` | 同步与文献完整性核验工具 |

大体量遥感/再分析数据不直接塞进 Git：保留下载脚本、清单、版本、校验和与处理后必要小样本；私钥、API 令牌和个人配置不提交。

## 当前状态（2026-11-10 更新）

模型一（植被—水—沙耦合）第一版已建立：代表区段为于田—民丰南缘，数据为 MOD13Q1（含QA）、ERA5/ERA5-Land（固定模型）与 NASA POWER，2001–2024；结果与局限见上面第0项文档。任务二、三尚未开始。

## 11-09 状态（保留）

**模型与预处理未通过正式计算前审计。** 旧代码存在无逐站来源支持的输沙目标、量纲问题、留出验证缺失，以及预算/运维/灾害恢复错误。旧拟合、NPV、失效概率及2050预测已撤回。50个历史文件原样保存并带哈希，见 [失效快照](archive/invalidated_20261109/README.md)。

本轮已补NASA POWER官方8点×120月共960条记录及原响应，并补 [地方工程官方资料](Data/raw/local_project_evidence/README.md)。已重写建模说明，只规定模型、参数和约束；编程方式由编程手决定。修正结构不代表模型已验证。区段边界、NDVI质量、水土/水权、成本和灾害恢复证据仍未齐，**未进入正式最优控制与风险求解**。

在仓库根目录运行 `python Code/audit_pipeline.py` 可离线复核当前数据并重建审计结果；依赖和下载入口见 [Code说明](Code/README.md)。原有32项及16项英文资料仍保留，不代表48项均已精读或全部参数已核验。

开始工作前运行 `git pull --ff-only`，或在 PowerShell 中使用 `.\Tools\sync.ps1`。完成一项工作后明确选择文件、提交、推送，再通知队友拉取。远程推送不会自动刷新另外两台电脑。
