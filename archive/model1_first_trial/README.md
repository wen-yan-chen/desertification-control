# archive/model1_first_trial — 模型一初版（日尺度），已归档

First-trial Model 1 (daily FAO-56 water balance, hourly-wind drift potential). Superseded by the
v7 rebuild (`Code/v7_model1.py`, `Docs/20261110_model1_v7_rebuild.md`, `Reports/M1/model1_v7_*.pdf`).

| File | Content |
|---|---|
| `20261110_audit_check_and_model1.md` | check of the 2026-11-09 audit, data, model, results, limits |
| `model1_en.pdf` / `model1_zh.pdf` (+ `.tex`) | description of the first-trial model, English and Chinese |

Its code (`Code/m1_*.py`), raw and processed data, results and figures are not in `main`; they are on
branch `model1-first-version`. The `.tex` files cannot be recompiled here because their figures are there.
Still worth reading for: the 2017 source switch in the legacy weather series, the daily water accounting,
and the faster cover loss after irrigation stops (about 2 years) used as a Task 3 scenario.
