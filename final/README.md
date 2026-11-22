# Practice2 最终成果

本目录汇集 2026-11-22 本地交付的 Practice2 英文成稿、定稿图件及复跑材料。成果按项目目录结构保存，供队友审阅和复现。

| 内容 | 入口 |
|---|---|
| 25 页英文论文，含图 11(a) 平滑热力图 | [成稿 PDF](Paper/main.pdf) · [LaTeX 主文件](Paper/main.tex) |
| 中文参考稿，对应队友主线 67bb38b 的较早英文版 | [论文中文版](Paper/论文中文版.docx) |
| 正文图与逐图数据依据 | [优化图件](Figures/Paper2026_Polished/README.md) · [图 5–16 对照册](Figures/Paper2026_Polished/figure_comparison_05-16.pdf) · [图 11 平滑版](Figures/Paper2026_Polished/fig11_water_use_smooth.pdf) |
| 机制图、建模分析图和组图压缩包 | [Figures](Figures/) |
| 求解与出图代码 | [代码说明](Code/README.md) · [出图入口](Code/paper_figures/render_polished.py) |
| 冻结输入、输出与核验 | [输入](Data/v7/) · [输出](Results/v7/) · [报告](Reports/README.md) · [模型与绘图说明](Docs/) |

从 final/ 运行以下命令可重编英文稿，文献后端为 BibTeX。

~~~sh
latexmk -cd -xelatex Paper/main.tex
~~~

图件复跑使用随包保存的 _shared 1.4.0 接口和冻结表。安装 Python 绘图库 Matplotlib、NumPy、pandas、Pillow，在 final/ 执行下列命令。

~~~powershell
$env:PYTHONPATH = (Resolve-Path ./_shared).Path
python -B Code/paper_figures/render_polished.py --out ../tmp/practice2-final-replay
python -B Code/paper_figures/render_polished.py --only fig11_water_use_smooth --out ../tmp/practice2-final-replay
~~~

正文 PDF 和图件可直接查看。历史底图练习所需的本机瓦片缓存、第三方参考文献文件、旧稿及编译缓存保存在原有位置。
