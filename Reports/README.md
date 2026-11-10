# 当前报告（2026-11-10，v7）

| 文件 | 内容 | 页数 |
|---|---|---|
| `preprocess_v7.tex` / `.pdf` | **数据预处理**：七项体检、缺失值专项排查（缺失图谱 / MCAR 检验 / 五种插补对比）、环节与优先级、Python 与 MATLAB 双语言方法对比与代码、处理后数据与校验、评分权重 | 16 |
| `model_v7.tex` / `.pdf` | **建模说明**：题目解读、假设、任务一至三的公式逐项解释、参数与约束、三个算法与伪代码、公式速查表；**只含建模部分，不含数据结果** | 21 |

编译方式：`xelatex` 跑两遍（需 ctex 与中文字体）；本仓库的 PDF 由 XeLaTeX 生成。

配套数据与代码：
- 数据：[Data/v7/README.md](../Data/v7/README.md)
- 代码：[Code/README.md](../Code/README.md)
- 审计与消融结果：`Results/v7/`

> 旧版 `model`、`model_v4`、`model_v6`、`preprocess` 报告已删除，其数字来自已被替换的数据面板，不可再引用。
> 历史留档见 `archive/invalidated_20261109/`。
