# Practice2 机制图与流程图修订

图注采用 2025 年 B 题 O 奖样稿的短标题做法，参考 2501687 图 2、2502617 图 2、2503268 图 1 和 2504448 图 2。数据口径和统计区间说明写入相邻正文。图号对应当前英文稿。

| 正文图 | 参考与复用 | 数据与复核 |
|---|---|---|
| [1 全局流程](workflow_cards.pdf) | FigureTraining 01 的 01 Overview，公共 `palette` 与 `components` | 深蓝、紫、赭、绿区分三个模型和政策交付。箭头对应 M1 的增长和水量模型、M2 的批次末态 |
| [3 水与覆盖反馈](m1_water_feedback.pdf) | FigureTraining 03 的 01 Water Cover Feedback，复用 `components.arrow/panel/label` | 从年覆盖、日需水、实际吸水到全年需求满足率，符号按 M1 公式 |
| [4 根区水桶](m1_root_zone.pdf) | 上一轮归档的原图 5，复用公共示意部件 | 入流和溢流后得到可用水，实际蒸腾后才结转。示意水位不按比例 |
| [5 胁迫与温度开关](m1_stress_switches.pdf) | 上一轮归档的原图 6，复用 `panels` 与 `head` | M1 基准容量 75 mm，水分胁迫阈值 37.5 mm。按月汇总 [panel_m1.csv](../../Data/v7/m1_audited/panel_m1.csv) 中 YT、MF 的 2015–2022 年 `era_T`，单位 °C。季节需求总量在现图 8 展示 |
| [9 M2 两步求解](m2_two_stage.pdf) | FigureTraining 01 的 02 Model2 Detail，复用公共示意部件 | 先求生态上限，再对给定目标求最低净现成本。目标份额采用正文符号 `φ` |

五张图均按 6.5 英寸出矢量 PDF 和 300 dpi PNG。版面检查和冻结输入哈希见[流程与示意图记录](qa-all.json)及[胁迫开关记录](qa-m1_stress_switches.json)。项目[渲染入口](../../Code/paper_figures/render_mechanisms.py)沿用公共包 1.4.0 的 `paper_context` 与 `save_paper`。从 Practice2 根目录将复跑输出指向新的预览目录。

~~~powershell
$env:PYTHONPATH = (Resolve-Path ../_shared).Path
python -B Code/paper_figures/render_mechanisms.py --out ../tmp/practice2-mechanisms-preview
~~~
