# v7 代码入口

## M1 计算

Python 要求为 3.11 及以上，依赖版本见 `requirements-m1.txt`。在仓库根目录运行。

```sh
python -m pip install -r Code/requirements-m1.txt
python Code/v7_model1.py
python -m unittest discover -s Code -p test_v7_m1.py -v
```

| 文件 | 用途 |
|---|---|
| `v7_model1.py` | 条件合并标定、模型比较与空间诊断 |
| `v7_m1_water.py` | 有效储水动态、植被更新与情景计算 |
| `v7_m1_run.py` | 统一导出当前 M1 数表 |
| `test_v7_m1.py` | QA、时间隔离、可识别性、守恒与状态边界测试 |

输入见 [m1_audited](../Data/v7/m1_audited/README.md)，数值输出见
[结果说明](../Results/v7/model1/README.md)，模型依据见
[M1 审计与实现](../Docs/20261110_m1_audit_and_implementation.md)。

## 重建 M1 输入

```sh
python Code/v7_replay_m1.py
python Code/v7_prepare_m1.py
```

前者重放来源请求并记录原、新哈希，后者执行逐像元 QA 和当前 M1 数据整理。
日常计算可直接使用已提交的输入表。

## M2 计算（不生成图片）

使用同一份 `requirements-m1.txt` 的 NumPy、Pandas、SciPy 环境，无需联网。

```sh
python Code/v7_model2.py
python -m unittest discover -s Code -p test_v7_m2.py -v
```

`v7_m2_core.py` 按建植批次调用 M1 的 `(V,M)` 轨迹，将有限灌溉路径、面积块及PV资产
组成混合整数优化；`v7_model2.py` 导出基准、成本生态前沿、投资结构与资源敏感性，
并逐批回放检查；`test_v7_m2.py` 包括水量/现金流/预算/劳动及穷举对照测试。

输入和假设见 [m2_inputs](../Data/v7/m2_inputs/README.md)，
数表见 [model2](../Results/v7/model2/README.md)，
图交接见 [说明](../Docs/20261111_m2_figure_handoff.md)。
快速检查可运行 `python Code/v7_model2.py --base-only --output tmp/m2_smoke`。
`formal_model_ready=false`，最优界只适用于给定网格与策略库。

## M1/M2 出图

```sh
python Code/v7_m1_figures.py
python Code/v7_m2_figures.py
```

两个脚本只读 `Results/v7/model1/`、`Results/v7/model2/` 的数表，不重跑模型，分别写入
`Figures/M1/`、`Figures/M2/`（PDF 与 PNG）。需要 Matplotlib（未列入 `requirements-m1.txt`）。
`v7_m2_figures.py` 复用 M1 脚本的字体与配色设置，并在出图前核对 `model2_results.json`
记录的输入哈希；改动 M2 输入或源码后须先重跑 `v7_model2.py`。图注须写入的限制见
[Figures/M2](../Figures/M2/README.md)。

### 论文图（MATLAB）

```sh
cd Code/figures_matlab && matlab -batch make_paper_figures
cd Paper/Figure && for f in m1_structure m1_two_clocks m1_bucket; do pdflatex $f.tex; done
```

`Code/figures_matlab/` 只读 `Data/v7/` 与 `Results/v7/model1/`，把论文用数据图（`data_stations`、
`m1_cover_series`、`m1_scenarios`、`m1_water_curve`、`m1_sensitivity`）写入 `Paper/Figure/`（矢量 PDF + 400 dpi PNG）。
配色取自 mycolor.space（基色 #1E5F74），坐标轴按知乎专栏“阿昆的科研日常”的 MATLAB 模板，见 `paper_style.m`。
TikZ 示意图共用 `Paper/Figure/paper_palette.tex`，颜色角色与 `paper_style.m` 相同：水＝青蓝，植被＝绿，风沙＝棕，突出＝橙，界限＝红色虚线。

## 预处理与对比工具

下列程序支撑 v7 面板预处理、诊断和方法对比。窗口 QA、ET0 温差口径及插值方式的适用限制
记录在 M1 审计说明中，运行时应按研究用途核对。

| 文件 | 用途 | 主要产物 |
|---|---|---|
| `v7_fetch.py` | 获取 POWER、MODIS、Open-Meteo、SoilGrids 响应 | `Data/v7/raw/` |
| `v7_finalize_fetch.py` | 合并 MODIS 分块、生成响应清单 | `Data/v7/raw/manifest.json` |
| `v7_clean.py` | 预处理、派生和训练期归一化 | `Data/v7/processed/` |
| `v7_missing.py` | 缺失检查与插补对比 | `Results/v7/missing.json` 等 |
| `v7_ablation.py` | 预处理方案消融比较 | `Results/v7/ablation.json` 等 |
| `v7_figures.py`、`v7_fig_pre.py` | 预处理与对比出图 | `Figures/v7_init_test/` |
| `preprocess_v7.py` | Python 逐步预处理和校验 | CSV、XLSX、JSON |
| `preprocess_v7.m` | MATLAB 预处理实现 | MATLAB 面板 CSV |

这些工具使用 NumPy、Pandas、SciPy、Matplotlib、OpenPyXL。
`v7_ablation.py` 内历史 `task2_npv` 不是当前 M2 求解器，存在水量单位和静态收益口径问题；
只保留作旧消融对照，不应用其 Task2 数值出论文图或结论。
MATLAB 程序面向 R2020b 及以上，执行结果仍需在 MATLAB 环境验证。
原始响应与缓存通过请求清单重建，数据范围见 [Data/v7](../Data/v7/README.md)。
