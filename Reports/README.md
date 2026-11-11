# 建模与预处理报告

| 文件 | 内容与使用入口 |
|---|---|
| [model_v7.pdf](model_v7.pdf) / [model_v7.tex](model_v7.tex) | 建模公式、参数与约束；任务一已并入复核更正（年度植被＋年内有效储水），任务二采用原章节位置的新批次动态模型 |
| [m2_correction.tex](m2_correction.tex) | M2 批次状态、三类资金、总预算/月水量/劳动约束与条件最优性范围 |
| [preprocess_v7.pdf](preprocess_v7.pdf) / [preprocess_v7.tex](preprocess_v7.tex) | 预处理和方法对比，阅读时结合文中的更正提示 |
| `M1/model1_v7_zh.*`、`M1/model1_v7_en.*` | 带历史提示的早期重建稿，参数口径按当前 M1 审计说明核对 |

当前数值、输入和结果解释分别见
[M1 审计与实现](../Docs/20261110_m1_audit_and_implementation.md)、
[经复核输入](../Data/v7/m1_audited/README.md)和
[结果说明](../Results/v7/model1/README.md)。

M2 的问题更正、计算证据与参数缺口见 [M2 审计](../Docs/20261111_m2_audit_and_implementation.md)，
数表及图交接见 [M2 结果](../Results/v7/model2/README.md)。M3 仍待核验。

在 `Reports/` 中对报告运行两遍 XeLaTeX。代码入口与依赖见 [Code](../Code/README.md)，
数据版本与来源见 [Data/v7](../Data/v7/README.md)。
