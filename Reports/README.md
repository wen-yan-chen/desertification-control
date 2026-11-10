# 当前报告（2026-11-10，v7）

> **复核后读法**：`model_v7.pdf` 末尾“复核更正”节为当前任务一公式、参数与约束。
> `preprocess_v7.pdf` 已加入更正提示，其原图与原数字保留作历史记录。
> `M1/model1_v7_zh.pdf`、`M1/model1_v7_en.pdf` 是加了历史提示的旧重建稿，不能引用旧参数、验证结论和图片。
> 当前数值见 [M1 复核说明](../Docs/20261110_m1_audit_and_implementation.md)、[结果说明](../Results/v7/model1/README.md)。

| 文件 | 内容 | 页数 |
|---|---|---|
| `preprocess_v7.tex` / `.pdf` | **数据预处理**：七项体检、缺失值专项排查（缺失图谱 / MCAR 检验 / 五种插补对比）、环节与优先级、Python 与 MATLAB 双语言方法对比与代码、处理后数据与校验、评分权重 | 16 |
| `model_v7.tex` / `.pdf` | **建模说明**：题目解读、假设、任务一至三的公式逐项解释、参数与约束、三个算法与伪代码、公式速查表及任务一复核更正；**只含建模部分，不含数据结果** | 23 |

编译方式：`xelatex` 跑两遍（需 ctex 与中文字体）；本仓库的 PDF 由 XeLaTeX 生成。

配套数据与代码：
- 数据：[Data/v7/README.md](../Data/v7/README.md)
- 代码：[Code/README.md](../Code/README.md)
- 审计与消融结果：`Results/v7/`

> 旧版 `model`、`model_v4`、`model_v6`、`preprocess` 报告已删除，其数字来自已被替换的数据面板，不可再引用。
> 历史留档见 `archive/invalidated_20261109/`。
