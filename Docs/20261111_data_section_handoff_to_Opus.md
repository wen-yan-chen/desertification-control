# Handoff to Opus — 数据节（2026-11-11）

## 1. 已完成

- `Paper/main.tex` 第 3 节已从 6 页压缩为 **1 页**（当前 PDF 第 5 页）。
- 按**站点**分类，而不是按变量类型：
  - **Category I**：绿洲边缘 7 站（YT、MF、QM、RQ、KEL、YL、ALE），用于校准；
  - **Category II**：沙漠公路走廊 XT，仅作 context；
  - **Category III**：塔中 TZ，仅作 interior control。
- 新图 `Paper/Figure/data_stations.pdf`：左图为 9 站位置，右图为各站 2015–2025 生长季平均覆盖度。
- 正文只保留 Sources 一句 + Result 三条：
  - 1,188 station–months = 9 stations × 132 months；
  - 395/396 growing-season cover values valid, no interpolation；
  - training 2015–2022, hold-out 2023–2025。
- 新增 `REF17`–`REF20` 到 `Paper/bibliography/references.bib`；当前正文只引用 REF17/18/19/EN09，PDF References 只有 4 条。
- `Paper/main.pdf` 编译通过，共 11 页；数据节正好 1 页。

## 2. 我差了什么 / 需要你判断或修

1. **四要素不完整。** 用户最初要求：1) what data/source；2) how to categorize；3) each category's attribution；4) standard data structure/algorithm。现在 1/2/3 有，4 基本没有——因为用户后来说“leave all the process, just list the result”，我把算法/结构段落删了。请确认是否要在 1 页内补一行 canonical structure，或放到 appendix。
2. **没有明确写数据组织。** 建议补一句：`one row per station–month; key = (site, date); fields = P, T, ET0, u10max, V, E; flags; split`。这样花 1 行，能回答第 4 点，也不会超页。
3. **图不可复现。** `data_stations.pdf/png` 是我用临时 Python 脚本生成的，没有提交生成脚本；`Code/` 里没有对应文件。建议加 `Code/v7_data_section_figure.py`，或并入 `v7_m1_figures.py`，从 `Data/v7/m1_audited/panel_m1.csv` 重画。
4. **图注统计口径。** 柱状图是 2015–2025 所有生长季**月值**的均值 ± 月值 SD，不是年值；caption 写“±1 SD”可能被读成年际 SD。建议改成“monthly values”，或先按年聚合再画。
5. **地图精度。** 椭圆是示意图，不是真实沙漠边界；站点是点坐标，没有投影/比例尺。若评委看重 GIS，可换真实边界或明确标注“schematic”（当前已标）。
6. **KEL 缺 1 个月。** 图中 KEL 是 43/44，正文只写 395/396；建议在图注或正文明确“Korla missing one month”。现在可接受，但不够显式。
7. **编译警告未清。** `main.log` 仍有：
   - `LaTeX Warning: There were undefined references`
   - `biblatex Warning: Please (re)run BibTeX`
   
   但 PDF 引用 [1]–[4] 正常，`main.bbl` 与 `main.aux` 的 md5 一致（4 条 entry）。我试过 clean rebuild、去掉 `\printbibliography` 外层 group、改用 `\thetotalpages`，都没消掉；`\thetotalpages` 还会显示错误的“Page 5 of 5”，已回退。需要你用最小例子定位，或确认是 TeX Live 2025 + biblatex/bibtex 后端的假警告。
8. **版面还有约 1.5 in 空白。** 如果补第 2 条的 structure 一行，正好填上。若不想补，可把图再放大一点，但不要超过 1 页。
9. **与 Notations 脱节。** 数据节用了 `V`、`E`、`r`、`d`、`K_s`，但 `Notations` 还是 placeholder。你写 Notations 时请统一定义；尤其 `V` 是 cover proxy，不是实测地面覆盖度。
10. **Category 语义待确认。** 我把“category”理解为 station group（I/II/III）。如果用户原意是“每个 station 一个 category”，需要改成 9 行 station list；当前 3 组是压缩版。
11. **标题用词。** 当前用 “Data Collection and Preprocessing”；原 placeholder 是 “Data procession”。如果组里统一用词，请改回或统一。
12. **图号顺延。** 数据节新增 Figure 1，后文 M1/M2 图号会顺延；插图时注意 `\ref` 和图号。
13. **未使用的 bib 条目。** `REF20`（于田项目报道）和 `EN06`（PV degradation）现在没在正文引用；M2 节要用可直接引用；不用也不会出现在 References（biblatex 只打 cited）。
14. **数据来源表述。** Open-Meteo 不能写成纯 ERA5-Land（原请求未指定 models）；当前只写 Open-Meteo，OK。NASA POWER 月度产品是日均值，正文没展开；若审稿人问，需在 appendix 说明。
15. **“no interpolation” 的口径。** 这是 M1 audited 口径；旧 `Reports/preprocess_v7.tex` 有插补，别混用。引用旧报告数字时注意版本。

## 3. 优先级建议

- **P0**：决定是否补 standard structure（1 行）；补图生成脚本；定位或确认编译警告。
- **P1**：明确图注统计口径；KEL 缺测说明；Notations 与数据节符号对齐。
- **P2**：地图精度、图号/引用、标题用词。

## 4. 不要破坏

- 数据节必须 **≤ 1 页**；不要恢复长算法/参数表。
- 分类按**站点**，不是按变量。
- `Paper/Figure/data_stations.pdf` 是当前图；改图时保留同名或同步改 `\includegraphics`。
- 数据节前有 `\clearpage`，保证从整页开始；节后也有 `\clearpage`。
- 当前 PDF 数据节在第 5 页。

## 5. 复现 / 检查

```sh
cd Paper
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
pdfinfo main.pdf | grep Pages
```

或：

```sh
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error Paper/main.tex
```

图数据：`Data/v7/m1_audited/panel_m1.csv`；取 `month in {6,7,8,9}` 的 `V_pct`。

## 6. 关键文件

- `Paper/main.tex` §3，当前约 lines 157–188
- `Paper/Figure/data_stations.pdf` / `.png`
- `Paper/bibliography/references.bib`（REF17–REF20）
- `Data/v7/m1_audited/panel_m1.csv`
- `Paper/main.pdf`
