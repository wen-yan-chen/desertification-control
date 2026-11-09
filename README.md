# Practice2 · Desertification Control

团队练习题：**2026 CQU_MCM Problem B — Sand Control is Meticulous Work**。2027 MCM/ICM备赛练习，不是2027正式赛题。

仓库：<https://github.com/wen-yan-chen/desertification-control>。本机唯一项目工作目录为 `C:\ModelingProgram\Practice2`；其他电脑克隆到各自固定目录即可，路径不必相同。

## 从哪里开始

1. [英文题目PDF](Problems/2026_CQU_MCM_Problem_B.pdf) / [Word原题](Problems/2026_CQU_MCM_Problem_B.docx)
2. [读题与约束登记](Docs/2026_CQU_MCM_B题_读题文档.md)（已纠正推荐年限、报告页数等口径）
3. [已有文献覆盖、缺口与建模接口](Docs/文献覆盖审计与建模接口.md)
4. [组员原有32项资料导航](Reference/00_阅读导航与资料清单.md)
5. [新增16项英文文献/报告](Reference/05_英文补充与来源核验/README.md)、[参数摘录与7项数据源说明](Reference/05_英文补充与来源核验/参数与数据源.md)
6. [三机协作与同步](Docs/协作同步.md)

## 目录约定

| 目录 | 内容 |
|---|---|
| `Problems/` | 原始赛题，保持源文件不改 |
| `Reference/01–04` | 组员已有PDF、CAJ及网页资料，保留原路径 |
| `Reference/05_英文补充与来源核验/` | 英文补充原文、阅读卡、DOI/哈希索引、BibTeX和数据说明 |
| `Docs/` | 读题、文献审计、协作约定 |
| `Archive/FigureStyleDemos/` | 前期两批图表风格演示及生成脚本；**合成数据演示，不是本题研究结果** |
| `Tools/` | 同步与文献完整性核验工具 |
| `Code/` | 抓取、预处理、建模与报告生成脚本（Python / MATLAB） |
| `Data/` | `raw/` 真实面板与数据源清单；`processed/` 清洗后数据、特征、训练/测试集；字段字典见 `data_dictionary.md` |
| `Figures/` | 论文与报告用图 fig1—fig13（200 dpi PNG） |
| `Results/` | 模型输出：标定参数、逐站拟合、敏感性、NPV 等 |
| `Docs/reports/` | 三份工作报告的 LaTeX 源码与编译 PDF（含 `figs/`） |

后续代码、数据和论文按实际需要添加。大体量遥感/再分析数据不直接塞进Git：保留下载脚本、清单、版本、校验和与处理后必要小样本；私钥、API令牌和个人配置不提交。


## 目录结构

```
desertification-control/
├── Problems/                    赛题原文（PDF + DOCX）
├── Docs/
│   ├── 2026_CQU_MCM_B题_读题文档.md
│   ├── 文献覆盖审计与建模接口.md
│   ├── 协作同步.md
│   └── reports/                 ★ 三份工作报告（LaTeX 源码 + PDF）
│       ├── data_source.tex / .pdf     数据来源与获取说明（6 页）
│       ├── preprocess.tex / .pdf      数据预处理报告（12 页）
│       ├── model.tex / .pdf           建模报告（18 页）
│       └── figs/                      报告插图
├── Main/                        MCM 论文正文（mcmthesis 模板）
├── Code/                        ★ 脚本
│   ├── 01b_fetch_ndvi.py              MODIS NDVI 并发抓取（分块缓存）
│   ├── 01_fetch_real_data.py          ERA5-Land 气象/土壤水 + 面板组装 + 派生量
│   ├── 02_crosscheck_power.py         NASA POWER 交叉验证
│   ├── preprocess.py / preprocess.m   12 步预处理（Python / MATLAB）
│   ├── 03_modeling.py                 三问模型：耦合动力学 / 动态规划 / 蒙特卡洛
│   ├── build_model_report.py 等        三份报告生成（docx）
│   ├── docx2tex.py                    docx → LaTeX 转换
│   └── omml_utils.py                  Word 原生公式（OMML）工具
├── Data/
│   ├── raw/                     真实面板、数据源清单、站点信息、文献参数锚点
│   ├── processed/               清洗后面板、特征、训练/测试集、交叉验证
│   └── data_dictionary.md       字段字典与 30 秒自检
├── Figures/                     fig1—fig13（预处理 8 张 + 建模 5 张）
├── Results/                     模型输出（参数、拟合、敏感性）
├── Reference/                   文献 01—05（含 16 篇 .caj）
├── Archive/                     早期图表风格演示（合成数据，非本题结果）
├── GanntChart&Plan/             进度与计划
└── Tools/                       同步与文献核验脚本
```

### 三份报告

| 报告 | 主要内容 | 页数 |
|---|---|---|
| [数据来源与获取说明](Docs/reports/data_source.pdf) | ERA5-Land + MODIS MOD13Q1 的来源、时空匹配、聚合规则、派生量公式、NASA POWER 交叉验证 | 6 |
| [数据预处理报告](Docs/reports/preprocess.pdf) | 8 站 × 120 月：异常值、掩码插补实验、特征工程、共线性、稳健标准化、时序划分 | 12 |
| [建模报告](Docs/reports/model.pdf) | 任务一耦合动力学、任务二动态规划、任务三韧性蒙特卡洛，含敏感性与检验，末章为编程手任务清单 | 18 |

均为 **LaTeX 源码 + 编译 PDF**；改动后重编：`tectonic -X compile Docs/reports/model.tex`。

### 复现

```powershell
python Code\01b_fetch_ndvi.py        # MODIS NDVI，分块缓存到 Data/cache
python Code\01_fetch_real_data.py    # ERA5-Land 气象/土壤水 → Data/raw 面板
python Code\02_crosscheck_power.py   # 与 NASA POWER 交叉验证
python Code\preprocess.py            # 12 步预处理 → Data/processed + Figures
python Code\03_modeling.py           # 三问模型 → Results
```

依赖：`pip install pandas numpy matplotlib python-docx`；LaTeX 用 `tectonic`（或 xelatex + ctex）。
`Data/cache/`（API 原始响应，约 1.8 MB）与 `Docs/reports/src/`（报告 docx 中间产物）已列入 `.gitignore`，由脚本重新生成。

## 当前状态（2026-11-08）

已接收远程资料、纳入本地题目和读题文档，新增英文资料并完成主要方法/关键页核验。已有32项与新增16项合计48项资料记录，另有数据源操作说明；不是48份已精读全文。新增16项中12份本地PDF，4项尚无本地全文。16份CAJ的正文参数仍需有阅读器的组员核验。

**尚未确定代表区段、下载区段时间序列、校准模型或求解最优方案。** 下一步优先确定沙漠边缘区段，补齐供水、覆盖度/水分、建设/运维/人工与电价资料，再实现统一模型。

开始工作前运行 `git pull --ff-only`，或在PowerShell中使用 `.\Tools\sync.ps1`。完成一项工作后明确选择文件、提交、推送，再通知队友拉取。远程推送不会自动刷新另外两台电脑。
