# 图表风格素材库

全部图片集中到 `Images/`，按图形用途分类，不再按生成批次分目录。共有 **35 个图表实例、46 个图片文件**（35 PNG + 11 PDF）。同一图形的不同风格用 `batch1_`、`batch2_`、`template_` 前缀区分；同一实例的 PNG 与 PDF 放在一起。

## 看图入口

- [完整分类索引](CATALOG.md)：按用途查找图片、PDF、对应函数及适用场景。
- [流程与空间布局](Images/01_流程与空间布局/)：流程图、区段示意图、网络图。
- [数据探索与分布](Images/02_数据探索与分布/)：相关性、分布、拟合与残差。
- [优化与算法](Images/03_优化与算法/)：Pareto、平行坐标、相平面、收敛曲线。
- [敏感性与不确定性](Images/04_敏感性与不确定性/)：龙卷风、响应曲线、区间带、双参数热图。
- [构成与方案比较](Images/05_构成与方案比较/)：柱状、环形、桑基、雷达、哑铃等图形。

## 目录结构

```text
FigureStyleDemos/
├── Images/
│   ├── 01_流程与空间布局/
│   ├── 02_数据探索与分布/
│   ├── 03_优化与算法/
│   ├── 04_敏感性与不确定性/
│   └── 05_构成与方案比较/
├── Scripts/
│   ├── demo_figures.py
│   ├── demo_figures2.py
│   ├── mcm_figures.py
│   └── figure_paths.py
├── README.md
├── CATALOG.md
├── catalog.json         # 图形、函数、分类、路径与迁移时的哈希
└── requirements.txt
```

## 重新生成

在仓库根目录运行（只查看现有图片无需安装依赖）：

```sh
python3 -m pip install -r Archive/FigureStyleDemos/requirements.txt
python3 Archive/FigureStyleDemos/Scripts/demo_figures.py
python3 Archive/FigureStyleDemos/Scripts/demo_figures2.py
python3 Archive/FigureStyleDemos/Scripts/mcm_figures.py
```

脚本通过 `figure_paths.py` 按 `catalog.json` 中的类别输出到 `Images/`，不依赖终端的当前目录。运行会覆盖对应的同名演示图。改变函数的 `name` 参数后，新图会进入 `Images/06_自定义输出/`；如需纳入现有分类，可更新 `catalog.json`。

`demo_figures.py` 为基础演示（12 PNG），`demo_figures2.py` 为扩展演示（12 PNG），`mcm_figures.py` 为参数化论文模板（11 PNG + 11 PDF）。后者上方的 `PALETTE`、`FULL_W`、`HALF_W` 控制配色与尺寸，各 `fig_*` 函数接收数据。依赖未锁定版本，重生成细节可能随绘图库版本变化。

## 用于论文

这里全部为合成／示例数据，部分沿用旧旅游题变量与标签，不是本次治沙题结果。选定图形后替换实际数据、变量、单位、图例与来源，将正式结果另存到 `Main/Figure/`；LaTeX 优先引用 PDF。

2026-11-09 整合：取消 Batch1、Batch2、PaperTemplate 三个物理目录，全部图片按用途合并，脚本集中到 Scripts。46 个原图按 SHA-256 校验内容一致，未重新生成图片。
