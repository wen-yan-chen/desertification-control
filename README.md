# Practice2 · Desertification Control

团队练习题：**2026 CQU_MCM Problem B — Sand Control is Meticulous Work**。2027 MCM/ICM 备赛练习，不是 2027 正式赛题。

仓库：<https://github.com/wen-yan-chen/desertification-control>。本机唯一项目工作目录为 `C:\ModelingProgram\Practice2`；其他电脑克隆到各自固定目录即可，路径不必相同。

## 从哪里开始

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

## 文档目录（2026-11-10 更新）

| 位置 | 内容 | 说明 |
|---|---|---|
| `Reports/model_v6.pdf` | **建模报告（当前版，11 页，逐步讲解）** | 任务一植被—水分—风沙耦合（含风蚀项与遮蔽修正）、任务二动态规划、任务三吸收马尔可夫链 |
| `Reports/model_v6.tex` | 同上 LaTeX 源码 | `tectonic -X compile model_v6.tex` 可重编 |
| `Reports/model_v4.pdf` | 旧版建模报告（7 页） | 保留作对照，数字以 v6 为准 |
| `Reports/model.pdf` / `.tex` | 建模报告（11-09 版） | 保留作历史对照，勿引用其中数字 |
| `Reports/preprocess.pdf` / `.tex` | 数据预处理报告（5 页） | 数据来源、QA 抽样、派生变量、训练测试划分 |
| `Docs/20261109_模型与数据审计.md` | 编程手审计 + 我方逐条修订状态 | 已解决的写“已解决”，未解决的写原因 |
| `Docs/20261109_修订交接说明.md` | 交接要点 | 三件必须说清的事 + 全部改动清单 |
| `Docs/2026_CQU_MCM_B题_读题文档.md` | 读题与约束登记 | 题面口径 |
| `Code/model_v4.py` | 当前建模代码 | 任务一标定、任务二 DP、任务三吸收链 |
| `Code/make_report_v4.py` | 报告生成 | 数字全部取自 `Results/model_v4.json` |
| `Code/build_panel_v2.py` | 面板组装 | 由缓存重算，不发网络请求 |
| `Data/processed/panel_v2.csv` | 分析面板 | 8 站 × 120 月 |
| `Results/model_v4.json` | 建模结果 | 报告所有数字的唯一来源 |
| `Results/model_v4_fit.csv` | 逐站标定结果 | r、K、d、R²、一年外推 RMSE |
| `Figures/figQ1—figQ3.png` | 建模图 | 拟合、最优路径、韧性 |

### 建模路线（为什么这样选）

B 题重逻辑闭环，不追求方程复杂度，因此按“保守—保守—创新”配置：

1. **任务一（保守）**：年尺度水量平衡 + 水分限制 Logistic，承载上限 $K$ 由观测 95% 分位确定，
   只标定生长率 $r$ 与衰亡率 $d$。8 站 $R^2$ 中位 0.21、一年外推 2/8 站优于持续性——
   据此明确：**该模型只提供稳态关系 $V^*(K_s)$ 与参数区间，不作短期预测**。
2. **任务二（保守，重点）**：15 年动态规划，决策为年新增面积、补水深度、光伏占比，
   约束为预算、水量、土地、劳动力；控制档位 60 个/状态，**全局最优且可复现**。
   基准情景 NPV 约 3.31 亿元，路径“前 10 年按上限推进、其后运维”。附 5 条可执行过程判据。
3. **任务三（创新）**：把冲击—恢复写成**吸收马尔可夫链**，用 $(I-Q)^{-1}$ 闭式给出期望首达时间，
   与 6000 次蒙特卡洛交叉验证（差异 <5 个百分点）；阈值扫描说明结论对“退化”定义高度敏感。

### 本次上传内容（提交说明）

- 新增建模报告 `Reports/model_v4.{tex,pdf}`（7 页）与旧版并列存放，避免误用。
- 新增 `Code/model_v4.py`、`Code/make_report_v4.py`：任务一标定、任务二 DP、任务三吸收链、报告生成。
- 新增 `Results/model_v4.json`、`Results/model_v4_fit.csv`：报告全部数字的来源。
- 新增 `Figures/figQ1—figQ3.png`：拟合、最优路径、韧性交叉验证图。
- README 增补本节“文档目录”，明确各文件用途与版本关系。

## 当前状态（2026-11-09）

**模型与预处理未通过正式计算前审计。** 旧代码存在无逐站来源支持的输沙目标、量纲问题、留出验证缺失，以及预算/运维/灾害恢复错误。旧拟合、NPV、失效概率及2050预测已撤回。50个历史文件原样保存并带哈希，见 [失效快照](archive/invalidated_20261109/README.md)。

本轮已补NASA POWER官方8点×120月共960条记录及原响应，并补 [地方工程官方资料](Data/raw/local_project_evidence/README.md)。已重写建模说明，只规定模型、参数和约束；编程方式由编程手决定。修正结构不代表模型已验证。区段边界、NDVI质量、水土/水权、成本和灾害恢复证据仍未齐，**未进入正式最优控制与风险求解**。

在仓库根目录运行 `python Code/audit_pipeline.py` 可离线复核当前数据并重建审计结果；依赖和下载入口见 [Code说明](Code/README.md)。原有32项及16项英文资料仍保留，不代表48项均已精读或全部参数已核验。

开始工作前运行 `git pull --ff-only`，或在 PowerShell 中使用 `.\Tools\sync.ps1`。完成一项工作后明确选择文件、提交、推送，再通知队友拉取。远程推送不会自动刷新另外两台电脑。
