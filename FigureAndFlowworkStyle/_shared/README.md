# 美赛论文绘图公共包 · 1.5.0

本包是三人协作的**唯一公共同步单元**：队友只需拿到这个目录即可出图，不必拿到 `Practice1`、`Practice2`、`FigureTraining` 的原始素材。整体复制到任意路径都能用（2026-11-18 实测：独立副本导入成功、实绘成功、12 项测试全过）。同步边界与命令见根目录 [SYNC.md](../SYNC.md)。

先按论文要回答的问题去[选图目录](mcm_library/CATALOG.md)找已经做好的一张，再用当届冻结结果替换输入。正式图共用字体、配色、分图和导出；旧训练素材按原位置查阅。Practice1 和 Practice2 的原图、渲染器与数据均保留。本轮从 [FigureTraining 11 柱条训练](../FigureTraining/11_柱状条形图_训练记录.md)提炼了可直接传数据的构成与分组柱接口，另增加分层流程卡片；[对照图与验收记录](../FigureTraining/公共绘图包_20261117_训练记录.md)保留了出图证据。

| 我需要 | 从这里开始 |
|---|---|
| 找已验证的整图和部件 | [选图目录](mcm_library/CATALOG.md) · [能力清单](mcm_style/CAPABILITY.md) |
| 看训练成图怎么迁移成正式接口 | [复跑示例](replay.py) · [来源与取舍](TRAINING.md#本轮回流基线) |
| 给队友或 AI 布置一张图 | [绘图任务模板](mcm_style/prompt_template.md) |
| 更新团队共用成果、判断图能否进正文 | [回流与验收](TRAINING.md) |
| 用 LaTeX/TikZ 画流程 | [共享宏包](mcm_library/latex/mcmworkflow.sty) · [角色与版式说明](mcm_library/latex/STYLE_GUIDE.md) |

**治沙论文的绘图资产（1.5.0）**

[实景图片与数据案例集](examples/image_data/README.md) · [四张模型机制图的预览和可编辑源码](mcm_library/latex/mechanisms/README.md) · [年内配额瓶颈图](examples/quota_pressure.png) · [累计与当前越线差值图](examples/recovery_gap.png)

在本包目录下，用可导入本包的 Python 3.10+ 环境运行 `python -m examples.desertification <论文仓库路径> <新输出目录>`，可读论文冻结表生成两张 PDF 和 PNG。复用到其他题目时，直接给 `charts.quota_pressure` 和 `charts.recovery_gap` 传数据。

历史样张按原 Practice2 布局、相邻 FigureAndFlowworkStyle 或本机 Documents/GitHub/desertification-control 下的同名目录查找。其他位置可用环境变量 `MCM_FIGURE_STYLE_DIR` 显式指定指向 FigureAndFlowworkStyle 的路径。FigureTraining 的旧模块仍从原训练目录读取。

**在比赛或训练项目中使用**

下面从工作区根目录运行。若本机已能导入两个包，可以跳过环境变量设置。核心依赖 Python 3.10+、Matplotlib 3.8+、NumPy、Pillow。跨机器共享时复制整个 `_shared`，也可选用 `python -m pip install -e .\_shared`；历史索引和真实数据回放仍需要原训练目录。

```powershell
$env:PYTHONPATH = (Resolve-Path .\_shared).Path +
    [IO.Path]::PathSeparator + $env:PYTHONPATH
python -B -c "import mcm_style, mcm_library; print(mcm_style.__version__, mcm_style.__file__)"
```

```python
import matplotlib.pyplot as plt
from mcm_library.charts import annotated_heatmap, colorbar
from mcm_style import panels, paper_context, save_paper

# 示例：values 矩阵已按 rate_labels × loss_labels 对齐，单位是年。
# 使用真实冻结结果替换这些示例值；None/NaN 表示未算，不是 0。
values = [[41.8, 16.6], [20.7, float("nan")]]
with paper_context():
    fig, axes = panels(3.0)
    ax = axes[0, 0]
    image = annotated_heatmap(
        ax, values, rows=["0.10", "0.25"], cols=["15%", "30%"],
        unit="Restricted mean (yr)", cmap="academic_plum", limits=(0, 50),
    )
    colorbar(fig, image, ax=ax)
    ax.set(xlabel="Loss per storm", ylabel="Storm rate (1/yr)")
    paths, issues = save_paper(fig, "figures/03_storm_sensitivity")
    for issue in issues:
        print(issue.severity, issue.detail)
    plt.close(fig)
```

`panels(width=...)` 和 `save_paper(width=...)` 可用不同的目标宽度，例如需要直接生成 3.25 英寸的半栏图。若导出 6.5 英寸后会缩小插入，给 `save_paper` 传 `placed_width=3.25` 检查缩放后的字号；按失败项重排。导出默认不覆盖同名结果。PDF 默认嵌入 TrueType 字体；渐变和影像底图是栅格层，地图描边文字可作为矢量轮廓。SVG 可选 `svg=True`，编辑文字需要相同字体。

构成图和分组柱可直接传入结果表列，旧 `bars11` 仅作图形参考：

```python
from mcm_library.bars import BarSeries, grouped_bars
with paper_context():
    fig, axes = panels(3.2)
    grouped_bars(axes[0, 0], ["Plan A", "Plan B"], [
        BarSeries("Baseline", [0.54, 0.63]),
        BarSeries("Revised", [0.70, 0.72]),
    ], value_label="Score (0–1)", maximum=1, legend=False)
    fig.legend(*axes[0, 0].get_legend_handles_labels(),
               loc="outside upper center", ncols=2)
    paths, issues = save_paper(fig, "figures/score_comparison")
```

当数值检验的多个估计落在同一位置附近时，给 `charts.comparison_intervals(..., row_separation=.4)` 传入可选的类别内间距。原有调用默认沿用中心线布局。实测对照见 [Practice2 图集](../Practice2/Figures/Paper2026_Shared/README.md)。

1.4.0 起，训练图型晋升为正式接口：`charts.three_d_columns`（3D 柱面 + 正交数值表）、`charts.break_even_curves` / `dual_axis_lines`（盈亏/双轴）、`charts.signed_bars` / `tornado`（敏感性）、`charts.feasible_band`（约束可行域）、`diagrams.feedback_loop`（概念循环）。全部只收数据、不读任何项目文件，选型见 [mcm_library/CATALOG.md](mcm_library/CATALOG.md)。

**在工作区复跑基准**

回放额外使用 pandas 和 pypdf；在新环境可用 `python -m pip install -e ".\_shared[replay]"` 一并安装。回放只读原 CSV/JSON/瓦片，输出目录要在历史训练目录之外：

```powershell
python -B .\_shared\replay.py --only p2_13_stress --out .\tmp\figure-first-look
python -B .\_shared\replay.py --out .\tmp\figure-review-v1.3.0 --overwrite --against .\_shared\baselines\v1.2.0.json
python -B -m unittest discover -s .\_shared\tests
```

`baselines/previews_v1.2.0/` 保存了该基线的 11 张成图与逐图 QA（由 `tmp\figure-review-v1.2.0` 归档而来），没跑回放的队友可直接目检比对。`qa-all.json` 记录样图来源、输入 SHA-256、字体、分辨率和布局提示；`--against` 用[本轮已审基线](baselines/v1.2.0.json)确认冻结输入没有漂移。图的结论、引线指向、重叠线能否分辨，以及打印效果仍需人看。复跑用于验证公共函数，不能代替比赛数据，也不代表图的奖项等级。
