# 当前可运行入口

在仓库根目录执行（Python 3；依赖见 `requirements-audit.txt`）：

```powershell
python Code/fetch_power_verified.py
python Code/fetch_project_evidence.py
python Code/audit_pipeline.py
```

前两个脚本获取NASA POWER官方月数据与政府工程网页，已有原响应时复用，失败不以模拟值补齐。原响应已入库，因此审计脚本可以完全离线复核哈希、单位、记录、旧截尾改动和同高度产品一致性，并重建探索面板与诊断图。

`03_modeling.py`、`preprocess.py`目前明确以非零状态退出，防止误用旧流程。旧抓取、模型、报告生成、MATLAB预处理及硬编码本机路径的转换工具保存在 `archive/invalidated_20261109/Code/`。包括旧建模报告生成器在内，这些都不再是当前运行入口；不能重新生成被撤销的报告。

当前 `Reports/model.tex` 是人工维护的模型规范；可用XeLaTeX编译。实现选择不由建模文档限定。此轮代码是数据补充与审计工具，不是任务三所说的正式模型求解。
