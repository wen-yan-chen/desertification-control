# Practice2 · Desertification Control

团队练习题：**2026 CQU_MCM Problem B — Sand Control is Meticulous Work**。2027 MCM/ICM备赛练习，不是2027正式赛题。

仓库：<https://github.com/wen-yan-chen/desertification-control>。本机唯一项目工作目录为 `C:\ModelingProgram\Practice2`；其他电脑克隆到各自固定目录即可，路径不必相同。

## 从哪里开始

1. [英文题目PDF](Problems/2026_CQU_MCM_Problem_B.pdf) / [Word原题](Problems/2026_CQU_MCM_Problem_B.docx)
2. [读题与约束登记](Docs/2026_CQU_MCM_B题_读题文档.md)（已纠正推荐年限、报告页数等口径）
3. [已有文献覆盖、缺口与建模接口](Docs/文献覆盖审计与建模接口.md)
4. [组员原有32项资料导航](Reference/00_阅读导航与资料清单.md)
5. [新增16项英文文献/报告](Reference/05_英文补充与来源核验/README.md)、[参数摘录与7项数据源说明](Reference/05_英文补充与来源核验/参数与数据源.md)
6. [三机协作与同步](Docs/协作同步.md)

## 目录约定

| 目录 | 内容 |
|---|---|
| `Problems/` | 原始赛题，保持源文件不改 |
| `Reference/01–04` | 组员已有PDF、CAJ及网页资料，保留原路径 |
| `Reference/05_英文补充与来源核验/` | 英文补充原文、阅读卡、DOI/哈希索引、BibTeX和数据说明 |
| `Docs/` | 读题、文献审计、协作约定 |
| `Archive/FigureStyleDemos/` | 前期两批图表风格演示及生成脚本；**合成数据演示，不是本题研究结果** |
| `Tools/` | 同步与文献完整性核验工具 |

后续代码、数据和论文按实际需要添加。大体量遥感/再分析数据不直接塞进Git：保留下载脚本、清单、版本、校验和与处理后必要小样本；私钥、API令牌和个人配置不提交。

## 当前状态（2026-11-08）

已接收远程资料、纳入本地题目和读题文档，新增英文资料并完成主要方法/关键页核验。已有32项与新增16项合计48项资料记录，另有数据源操作说明；不是48份已精读全文。新增16项中12份本地PDF，4项尚无本地全文。16份CAJ的正文参数仍需有阅读器的组员核验。

**尚未确定代表区段、下载区段时间序列、校准模型或求解最优方案。** 下一步优先确定沙漠边缘区段，补齐供水、覆盖度/水分、建设/运维/人工与电价资料，再实现统一模型。

开始工作前运行 `git pull --ff-only`，或在PowerShell中使用 `.\Tools\sync.ps1`。完成一项工作后明确选择文件、提交、推送，再通知队友拉取。远程推送不会自动刷新另外两台电脑。
