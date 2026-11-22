# 图表与流程图样式

本目录提供合成数据图表、配色和流程图排版示例，可据此选择表达形式并替换实际研究数据。

| 子目录 | 内容 |
|---|---|
| [_shared 1.5.0](_shared/README.md) | [真实图片与数据](_shared/examples/image_data/README.md)、[可编辑机制图](_shared/mcm_library/latex/mechanisms/README.md)、配额与恢复图接口 |
| [FigureStyleDemos](FigureStyleDemos/README.md) | 35 个图表实例，按用途分类，含生成脚本与分类索引 |
| [MCM_B图表样张](MCM_B图表样张/README.md) | 28 张图型与配色样张，含 PDF 图集、SVG、PNG 与生成脚本 |
| [MCM_B新结构样张](MCM_B新结构样张/README.md) | 12 张复合结构图、PDF 图集和落地说明 |
| [WorkFlowStyle](WorkFlowStyle/STYLE_GUIDE.md) | 工作流样式、LaTeX 宏包和布局示例 |

正式论文图放在 `Paper/Figure/`。使用样式时填写实际变量、单位、数据来源与图注，
并将生成图与对应的模型输出表关联。

项目内的 `_shared` 可以直接使用。若要把本次增量合并到同一基线的桌面共享包，从本仓库根目录运行以下命令。补丁按原文件上下文校验，保留原有工作区改动。

```sh
shared_dir="$HOME/Desktop/MCM:ICM/_shared"
patch_file="$PWD/FigureAndFlowworkStyle/shared-1.5.0.patch"
git -C "$shared_dir" apply --check "$patch_file" && git -C "$shared_dir" apply "$patch_file"
```
