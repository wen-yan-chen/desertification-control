# Practice2 图件

| 用途 | 入口 |
|---|---|
| 正文图 5–16 | [逐图对照册](Paper2026_Polished/figure_comparison_05-16.pdf) · [单图与数据复核](Paper2026_Polished/README.md) |
| 正文图 1–4 | [流程与机制图](Paper2026_Mechanisms/README.md) · [研究区图](Paper2026/README.md) |
| 历史论文图 | [上一轮结果图](Paper2026_Revision/README.md) · [基础图](Paper2026/README.md) · [公共接口补绘](Paper2026_Shared/README.md) |
| 模型分析和写作简报 | [M1 图](M1/README.md) · [M2 图](M2/README.md) · [检验报告](../Reports/model_validation_m1m2.tex)及 [v7_validation](v7_validation/) |
| 数据处理诊断 | [v7_init_test](v7_init_test/) 对应[预处理报告](../Reports/preprocess_v7.tex)中的早期口径 |
| 早期比较和训练变体 | [退役资料](../archive/README.md) |

M1 用反馈环说明日水量与年覆盖的耦合，另用根区水桶和两条响应函数解释水量更新、胁迫和温度作用。保留留出检验、灌溉响应和控制因子图。M2 的批次图并列呈现灌溉阶梯、施工现金流和交给 M3 的末态。月供水图对比五月与年度余量。离散权衡图保留独立光伏准入曲线，另用固定生态目标比较投资敏感性。M3 在风暴敏感性图中加入干旱月的请求量和实供量，同时保留恢复轨迹和数值检验。

M1 弹性候选图将蒸腾需求的覆盖尺度 V_full 标成 K，且脚注与轴标签重叠。正文采用标为 Cover scaling 的 06 图。M3 三维候选图用柱高和颜色表达同一个 RMST，正交数值表与柱体靠得过近。3D 版、落选图及原图注收入历史归档。M1/M2 图中需要单独为写作简报或诊断提供信息的版本仍可沿原路径查阅。

按原渲染器复跑时，请把输出指向新的目录。

2026-11-20 复跑了上一版选用的 6 张基础图和 3 张公共接口图，PNG 与当时选用版本逐像素一致。三张公共接口图的冻结输入 SHA-256 一致，版面检查无提示。该版的 TikZ 示意图和 MATLAB 图见 [Paper/Figure](../Paper/Figure/)。本次修订的验收见[修订图记录](Paper2026_Revision/README.md)。
