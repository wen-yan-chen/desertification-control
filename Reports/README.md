# 建模与预处理报告

| 文件 | 内容与使用入口 |
|---|---|
| [model_v7/model_v7.pdf](model_v7/model_v7.pdf) / [model_v7.tex](model_v7/model_v7.tex) | 建模公式、参数与约束；任务一已并入复核更正（年度植被＋年内有效储水），任务二采用原章节位置的新批次动态模型 |
| [model_v7/m2_correction.tex](model_v7/m2_correction.tex) | M2 批次状态、三类资金、总预算/月水量/劳动约束与条件最优性范围 |
| [model_v7/m3_correction.tex](model_v7/m3_correction.tex) | 已并入总报告的M3更正：复合Poisson、二维储水状态、非平稳情景、首达/恢复/删失及证据边界 |
| [preprocess_v7.pdf](preprocess_v7.pdf) / [preprocess_v7.tex](preprocess_v7.tex) | 预处理和方法对比，阅读时结合文中的更正提示 |
| [M1/M1_writing_brief.pdf](M1/M1_writing_brief.pdf) | 英文写作简报：M1 目标与完成情况、结构图、公式含义、参数值、结果数表、可/不可声称内容、图清单 |
| [M2/M2_writing_brief.pdf](M2/M2_writing_brief.pdf) | 英文写作简报：M2 目标与完成情况、结构图、公式含义、参数值、基准方案、权衡与敏感性、可执行判据、图清单 |
| [M3/M3_writing_brief.pdf](M3/M3_writing_brief.pdf) / [中文导航](M3/README.md) | 英文写作简报：M3成果、M1/M2接口、灾害与水量公式、算法、参数证据、27情景结果、验证、论文思路与Claude绘图计划；图片待绘制 |
| [model_validation_m1m2.pdf](model_validation_m1m2.pdf) / [.tex](model_validation_m1m2.tex) | **模型检验报告（2026-11-12）**：25 项检验（必要性判断、方法选择、代码、逐项结果、改进方案）。只读 `Results/v7/model1|model2` 的结果表，不改动实现；数值源为 `Results/v7_validation/validation_m1m2.json` |

当前数值、输入和结果解释分别见
[M1 审计与实现](../Docs/20261110_m1_audit_and_implementation.md)、
[经复核输入](../Data/v7/m1_audited/README.md)和
[结果说明](../Results/v7/model1/README.md)。

M2 的问题更正、计算证据与参数缺口见 [M2 审计](../Docs/20261111_m2_audit_and_implementation.md)，
数表及图交接见 [M2 结果](../Results/v7/model2/README.md)。
M3于2026-11-13完成实现：[复核说明](../Docs/20261113_m3_audit_and_implementation.md)、
[数表](../Results/v7/model3/README.md)、[Claude绘图交接](../Docs/20261113_m3_figure_handoff.md)。

模型检验（[model_validation_m1m2.tex](model_validation_m1m2.tex)）的结论：M2 全部通过；
M1 数值可复现、水量账闭合，但留出期预测不如持续性基线，参数区间宽达 150%。
该报告同时给出 M3 的四项"设计检验"（矩阵性质、解析 vs 蒙特卡洛、离散化收敛、λ=0 极限），
是历史设计记录；其中“λ=0必不退化”等结论已在当前M3章节纠正，不能直接复用。

在各报告所在目录运行两遍编译：`model_v7/` 与根目录的 `preprocess_v7` 用 XeLaTeX，`M1/`、`M2/` 的写作简报用 pdfLaTeX，`M3/` 用 XeLaTeX。M3先在仓库根目录运行`python Reports/M3/build_tables.py`核验并提取结果表，详见[M3导航](M3/README.md)。代码入口与依赖见 [Code](../Code/README.md)，
数据版本与来源见 [Data/v7](../Data/v7/README.md)。


