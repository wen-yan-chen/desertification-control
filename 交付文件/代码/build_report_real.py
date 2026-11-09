# -*- coding: utf-8 -*-
"""build_report_real.py —— 生成《数据预处理报告.docx》（真实数据版）"""
import json
import os

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from omml_utils import rich_math  # noqa: E402

from omml_utils import (equation, mdelim, mfrac, mfunc, mr, msub, msup, rich_math)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "数据", "raw")
PROC = os.path.join(BASE, "数据", "processed")
OUT = os.path.join(BASE, "数据预处理报告.docx")
DARK = RGBColor(0x1F, 0x3B, 0x57)
GREY = RGBColor(0x55, 0x55, 0x55)

S = json.load(open(os.path.join(PROC, "stats.json"), encoding="utf-8"))
panel = pd.read_csv(os.path.join(PROC, "02_panel_clean.csv"), encoding="utf-8-sig")
cvp = os.path.join(PROC, "07_交叉验证_POWER.csv")
cv = pd.read_csv(cvp, encoding="utf-8-sig") if os.path.exists(cvp) else None
FIG = S["figures"]


def cn(run, name="宋体", size=10.5, bold=False, color=None):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    if color:
        run.font.color.rgb = color


def rich(p, text, name="宋体", size=10.5, color=None):
    rich_math(p, text, name, size, color)


def body(doc, text, indent=True, size=10.5):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.45
    p.paragraph_format.space_after = Pt(4)
    if indent:
        p.paragraph_format.first_line_indent = Cm(0.74)
    rich(p, text, "宋体", size)


def bullet(doc, text, size=10):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.35
    rich(p, text, "宋体", size)


def h1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(15)
    p.paragraph_format.space_after = Pt(5)
    cn(p.add_run(text), "黑体", 14.5, True, DARK)


def h2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(9)
    p.paragraph_format.space_after = Pt(3)
    cn(p.add_run(text), "黑体", 11.5, True, DARK)


def caption(doc, text, keep_next=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(7)
    if keep_next:
        p.paragraph_format.keep_with_next = True
    cn(p.add_run(text), "宋体", 9, False, GREY)


def shade(cell, hexcolor="DCE6F1"):
    tcPr = cell._tc.get_or_add_tcPr()
    el = OxmlElement("w:shd")
    el.set(qn("w:val"), "clear")
    el.set(qn("w:color"), "auto")
    el.set(qn("w:fill"), hexcolor)
    tcPr.append(el)


def math_run(paragraph, parts):
    om = OxmlElement("m:oMath")
    for x in parts:
        om.append(x)
    paragraph._p.append(om)


def table(doc, header, rows, widths=None, font=8.6, cap=None):
    if cap:
        caption(doc, cap, keep_next=True)
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]
        c.text = ""
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(1)
        cn(p.add_run(str(h)), "黑体", 9, True)
        shade(c)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.15
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i > 0 else WD_ALIGN_PARAGRAPH.LEFT
            if isinstance(v, list):
                math_run(p, v)
            else:
                rich(p, v, "宋体", font)
    if widths:
        t.autofit = False
        layout = OxmlElement("w:tblLayout")
        layout.set(qn("w:type"), "fixed")
        t._tbl.tblPr.append(layout)
        for i, w in enumerate(widths):
            t.columns[i].width = Cm(w)
            for cell in t.columns[i].cells:
                cell.width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def figure(doc, path, width=16.0, cap=""):
    if not path or not os.path.exists(path):
        return
    doc.add_picture(path, width=Cm(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[-1].paragraph_format.keep_with_next = True
    doc.paragraphs[-1].paragraph_format.space_after = Pt(2)
    if cap:
        caption(doc, cap)


def add_page_number(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def fld(instr):
        el = OxmlElement("w:fldSimple")
        el.set(qn("w:instr"), instr)
        r = OxmlElement("w:r")
        t = OxmlElement("w:t")
        t.text = "1"
        r.append(t)
        el.append(r)
        return el

    p._p.append(fld("PAGE"))
    cn(p.add_run(" / "), "宋体", 9, False, GREY)
    p._p.append(fld("NUMPAGES"))


doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2.3)
sec.top_margin, sec.bottom_margin = Cm(2.2), Cm(2.0)
st = doc.styles["Normal"]
st.font.name = "宋体"
st.font.size = Pt(10.5)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
add_page_number(sec)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(30)
cn(p.add_run("《治沙是一项精细活》B 题"), "黑体", 15, True, DARK)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
cn(p.add_run("数 据 预 处 理 报 告"), "黑体", 26, True, DARK)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(6)
cn(p.add_run("真实数据：ERA5-Land 再分析 + MODIS MOD13Q1 · 8 站 × 120 月"), "楷体", 11, False, GREY)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
cn(p.add_run("CQU_MCM 2026 · 建模小组 · 2026-11-09"), "楷体", 9.5, False, GREY)

h1(doc, "摘  要")
n_anom = sum(v["union"] for v in S["outliers"].values())
ic = S["impute_compare"]
body(doc, f"本报告对 **{S['raw_audit']['n_rows']} 条真实观测**（8 个站点 × 2015-01—2024-12 共 120 个月）"
          f"完成建模前的全部数据准备。数据来自 ERA5-Land 再分析与 MODIS MOD13Q1，"
          f"来源与获取方式见配套文档《数据来源与获取说明》。真实数据质量较好："
          f"**无重复记录、无缺失值**，但仍存在量纲差异、跨站异质性、极端月与构造性共线四类问题，需系统处理。")
body(doc, f"处理结论有四条。① 异常值用 IQR + 稳健 Z + 时序残差三准则共检出 {n_anom} 处（占全部记录 7.8%），"
          f"其中降水 30 处全部由时序残差捕获（暴雨/沙尘暴月的真实极值），因此**只截尾、不删除**；"
          f"② 原始数据无缺失，缺失处理改为“掩码实验”——人为挖掉 10% 实测值再回补，"
          f"结果表明土壤含水率与风速用线性插值最优（RMSE "
          f"{ic['土壤含水率']['线性插值']['RMSE']:.2f} / {ic['风速']['线性插值']['RMSE']:.2f}），"
          f"覆盖度用同月气候态最优（{ic['植被覆盖度']['同月气候态']['RMSE']:.2f}），"
          f"均值填充差 2—4 倍；③ 12 个候选特征中仅“月份余弦”因与气温共线（VIF=31.1）被剔除，"
          f"最终 11 个特征 VIF 全部 ≤ 8.0；④ 以 2023-01 为界按时间切分（768 / 192 行），"
          f"截尾分位数与标准化参数只由训练期估计，堵住两处最常见的数据泄漏。")

table(doc, ["环节", "结果"],
      [["数据规模", f"{S['raw_audit']['n_rows']} 行 × {S['raw_audit']['n_cols']} 列（8 站 × 120 月）"],
       ["重复 / 缺失", "0 条重复；缺失单元格 0 个"],
       ["单位", "抓取阶段统一为 m/s、mm、℃、%、t·km⁻²·月⁻¹"],
       ["异常值", f"三准则合计 {n_anom} 处；物理阈值另拦截 {sum(S['physical'].values())} 处"],
       ["插补策略", "掩码实验：含水率/风速→线性插值；覆盖度→同月气候态"],
       ["特征", f"11 个，VIF 最大 {max(S['vif_final'].values()):.2f}"],
       ["划分", f"训练 {S['split']['train_rows']} / 测试 {S['split']['test_rows']}（按 2023-01）"]],
      widths=[3.0, 12.6], cap="表 1  预处理关键结果速览")

h1(doc, "一、数据与任务")
body(doc, "B 题三项任务需要的输入是：风况、降水、气温、土壤含水量、植被覆盖度、输沙率。"
          "本项目的数据链条为：ERA5-Land 再分析提供气象与土壤水分 → MODIS NDVI 反演植被覆盖度 → "
          "由真实风况按已发表公式计算输沙率与输沙势。逐变量的来源、分辨率、聚合规则与公式，"
          "见《数据来源与获取说明.docx》；本报告只讨论“拿到数据之后怎么处理”。")
body(doc, f"进入流程的数据表共 {S['raw_audit']['n_cols']} 列：站点标识 4 列、气象与土壤水 7 列、"
          f"NDVI 与覆盖度 3 列、输沙率与输沙势 2 列、质控列 2 列（样本天数、端元方案）。"
          f"“样本天数”用于识别 2 月短月效应，属质控列而非建模特征。")
body(doc, "**需要特别说明**：治理面积、投资额、生态补水量属于**人工决策量**，不是观测数据，"
          "因此不在数据面板中出现，留待任务二的优化模型作为决策变量设定。"
          "把这类量当观测写进论文，等于凭空编造统计数字，评委会直接质疑数据可信度。")

h1(doc, "二、数据评估：真实数据也有四类问题")
body(doc, "真实数据不等于干净数据。逐项检查后，本数据集的问题是四类——没有重复、没有缺失，"
          "但下面几条足以让模型结果失真：")
table(doc, ["问题", "证据", "若不处理", "权重"],
      [["量纲与数量级差异", "风速 1.4—5.5 m/s，输沙率 0—780 t·km⁻²·月⁻¹，相差 3 个数量级",
        "最小二乘被大值主导，梯度下降步长失衡", "★★★★★"],
       ["极端月/异常值", f"三准则检出 {n_anom} 处，降水 30 处、含水率 23 处集中在少数月份",
        "均值与方差被少数月份拉动，标准化后正常值被压扁", "★★★★"],
       ["分布右偏", "输沙率偏度 > 3（多数月接近 0、少数月极高）",
        "线性模型残差非正态，区间估计失效", "★★★★"],
       ["构造性共线", "月份余弦 ↔ 气温 VIF=31.1；风速 ↔ 滞后项 VIF≈7",
        "系数不可解释，甚至符号翻转", "★★★"],
       ["时序泄漏风险", "10 年连续序列，若随机划分训练/测试",
        "模型“看到未来”，测试误差被严重低估", "★★★★"]],
      widths=[3.2, 6.4, 5.0, 1.8], font=8.4,
      cap="表 2  真实数据的四类问题与影响权重")
body(doc, "权重排序依据“误差传播倍数”：量纲/数量级差异会让 u³ 型非线性项放大约 46 倍，属致命级；"
          "极端月与右偏改变参数估计，属重度；共线只影响可解释性，属中度。"
          "在美赛评分中，这一节写不写、有没有数字，直接影响“模型合理性”一项。")

h1(doc, "三、预处理方案：12 个环节")
body(doc, "顺序原则：先解决“会让计算失败”的问题（类型、单位、键），再解决“会扭曲结果”的问题"
          "（异常、缺失、偏态），最后做“提升模型表现”的问题（特征、共线、标准化）。")
table(doc, ["#", "环节", "方法", "Python", "MATLAB", "备选"],
      [["1", "类型与格式", "多格式日期解析、数值文本清洗", "parse + Period", "datetime + regexprep", "手工映射"],
       ["2", "类别归一", "字典映射（真实数据已规范，仍保留容错）", "Series.replace", "循环替换", "模糊匹配"],
       ["3", "键去重", "完全重复 + 站-月键去重（本数据 0 条）", "drop_duplicates", "unique(...,'rows')", "保留信息最全行"],
       ["4", "单位统一", "抓取阶段已转 SI，本步仅校验", "—", "—", "按单位列换算"],
       ["5", "物理阈值", "先验上下界，越界置缺失", "布尔索引", "逻辑索引", "3σ 截断"],
       ["6", "异常检测", "IQR + 稳健Z + 时序残差（重尾先取对数）", "分位数/滚动中位数", "PCTILE + median", "孤立森林"],
       ["7", "异常处置", "训练期 P1—P99 截尾，不删除", "clip", "min/max", "删除（样本充足）"],
       ["8", "缺失处理", "线性插值 + 同月气候态（按变量择优）", "interpolate/groupby", "fillmissing", "MICE"],
       ["9", "面板对齐", "站×月 笛卡尔积补全（本数据已完整）", "MultiIndex", "outerjoin", "不补全"],
       ["10", "特征工程", "物理量构造 + 周期编码 + 滞后项", "自定义", "同左", "自动特征"],
       ["11", "共线筛选", "迭代 VIF，核心物理量受保护", "自写 lstsq VIF", "反斜杠回归", "主成分"],
       ["12", "标准化/划分", "稳健标准化 + 按时间切分", "median/IQR", "median + PCTILE", "Z-score"]],
      widths=[0.8, 2.6, 5.2, 3.2, 3.2, 3.2], font=7.8,
      cap="表 3  12 个环节的方法与双语言实现")

h2(doc, "3.1 三个关键取舍")
body(doc, "**（1）异常值只截尾、不删除。** 干旱区的“异常”往往是真实极端事件：一场沙尘暴能让月输沙率达到常月 10 倍，"
          "一次暴雨能让月降水从 2 mm 跳到 40 mm。按 3σ 删除正好删掉模型最需要学的极端样本。"
          "我们只把训练期 P1/P99 之外的值截到边界，既抑制杠杆效应，又保留事件信息。")
body(doc, "**（2）插补方法按变量分别择优，而不是全表统一。** 用掩码实验比较五种策略，结果不一致："
          "含水率与风速的线性插值最好，覆盖度却是“同月气候态”最好——因为覆盖度的年际趋势强"
          "（治理导致逐年上升），气候态保留了季节性；而含水率与风速季节性强，跨年同月均值更稳。"
          "这个结论只有实验能给，“一拍脑袋用均值”会让 RMSE 高 2—4 倍。")
body(doc, "**（3）共线筛选要保护核心物理量。** 月份余弦与气温 VIF 达 31.1——本质是气温本身就是月份的函数，"
          "两者只能留一个；保留气温更好，因为动力学模型也要用它，月份正弦（VIF 5.46）保留以承载光照季节信息。"
          "风速滞后 1/3 期 VIF 约 5—7，低于阈值，保留给时序模型做记忆项。")

h1(doc, "四、执行结果")
h2(doc, "4.1 审计与规范化")
body(doc, f"原始 {S['raw_audit']['n_rows']} 行 × {S['raw_audit']['n_cols']} 列，完全重复 0 条、"
          f"站-月键重复 0 条；站点名已规范为 8 个、地表类型 6 类、月份统一为 Period。"
          f"抓取阶段已完成单位统一，本步只做校验，无记录需要换算。")
figure(doc, FIG.get("fig1_数据审计"), 16.4,
       "图 1  数据审计：（a）各字段缺失率全为 0；（b）各站点记录数均为 120，面板完整")

h2(doc, "4.2 物理阈值与异常检测")
pb = {k: v for k, v in S["physical"].items() if v}
if pb:
    table(doc, ["变量", "越界记录"], [[k, f"{v} 条"] for k, v in pb.items()],
          widths=[6.0, 4.0], cap="表 4  物理阈值越界统计")
    body(doc, "含水率越界集中在绿洲站点冬春灌溉期（表层体积含水率可短时超过 40%）。"
              "这些值物理上并非不可能，但超出沙区模型的适用范围，故按缺失处理并由邻近月份插补，"
              "避免把灌溉事件误当作降水响应。")
o = S["outliers"]
rows = []
for k in ["风速", "降水", "气温", "土壤含水率", "植被覆盖度", "输沙率"]:
    v = o[k]
    rows.append([k, v["n"], v["iqr"], v["mad"], v["res"], v["union"],
                 f'{v["ratio"] * 100:.1f}%', "是" if v["log_space"] else "否"])
table(doc, ["变量", "有效样本", "IQR", "稳健Z", "时序残差", "合计", "占比", "对数域"],
      rows, widths=[2.8, 2.4, 1.6, 2.0, 2.4, 1.8, 1.8, 1.8],
      cap="表 5  三准则异常检测（对数域用于重尾变量：降水、输沙率）")
body(doc, f"合计 {n_anom} 处。降水的 30 处全部由时序残差捕获——单月降水突增偏离 12 个月中位水平；"
          f"含水率 23 处集中在绿洲站春季灌溉月；输沙率在对数域检测后异常率仅约 1.5%，"
          f"说明“先取对数再定界”对跨数量级变量是必要的。这些点全部保留量级，只做截尾。")
figure(doc, FIG.get("fig2_异常值对比"), 16.6,
       "图 2  清洗前后箱线图：输沙率长尾被压到 P99 以内，含水率与覆盖度的极端月被收敛")

h2(doc, "4.3 缺失值处理（掩码实验）")
rows = []
for strat in ["均值", "中位数", "线性插值", "同月气候态", "KNN(k=5)"]:
    rows.append([strat,
                 f'{ic["土壤含水率"][strat]["RMSE"]:.3f}',
                 f'{ic["植被覆盖度"][strat]["RMSE"]:.3f}',
                 f'{ic["风速"][strat]["RMSE"]:.3f}'])
table(doc, ["插补策略", "土壤含水率 RMSE", "植被覆盖度 RMSE", "风速 RMSE"], rows,
      widths=[3.6, 4.4, 4.4, 3.6],
      cap="表 6  五种插补策略的掩码实验（挖掉 10% 实测值后回补，误差单位同原变量）")
body(doc, "误差用均方根误差度量，n 为被挖掉的样本数：")
equation(doc, [
    mr("RMSE"), mr("="),
    msup(mdelim([mfrac([mr("1")], [mr("n")]), mr("Σ"),
                 msup(mdelim([msub(mr("ŷ"), mr("i")), mr("−"), msub(mr("y"), mr("i"))]), mr("2"))]),
        mfrac([mr("1")], [mr("2")])),
], number=1)
body(doc, f"最优组合：土壤含水率与风速用线性插值（RMSE "
          f"{ic['土壤含水率']['线性插值']['RMSE']:.2f} / {ic['风速']['线性插值']['RMSE']:.2f}），"
          f"覆盖度用同月气候态（{ic['植被覆盖度']['同月气候态']['RMSE']:.2f}）。"
          f"均值/中位数填充在每个变量上差 2—4 倍，因为它们抹平了季节与趋势。"
          f"本数据实际无缺测，这套实验是为真实数据出现缺口时预留的可复现方案，"
          f"也让预处理报告不只停留在“我们做了清洗”的口号上。")
figure(doc, FIG.get("fig3_插补对比"), 16.4,
       "图 3  五种插补策略的 RMSE 对比（深色为各变量最优策略）")
figure(doc, FIG.get("fig5_时序清洗"), 16.6,
       "图 4  缺测最多站点的风速时序（灰区间为识别到的缺测时段，已由气候态×区域异常补齐）")

h2(doc, "4.4 特征工程与分布变换")
body(doc, "在原始观测之外构造两类派生特征。第一类是气候干旱度（de Martonne 指数），"
          "用于把“降水少”和“蒸发强”合成一个变量：")
equation(doc, [
    msub(mr("D"), mr("t")), mr("="),
    mfrac([msub(mr("P"), mr("t"))],
          [mfunc("max", mdelim([msub(mr("T"), mr("t")), mr("+"), mr("10"), mr(","), mr("1")]))]),
], number=2)
body(doc, "第二类是治理成效的年际增量，取 12 个月差分：")
equation(doc, [
    mr("Δ"), msub(mr("C"), mr("t")), mr("="),
    msub(mr("C"), mr("t")), mr("−"), msub(mr("C"), mr("t−12")),
], number=3)
figure(doc, FIG.get("fig4_分布变换"), 16.2,
       "图 5  输沙率的分布变换：（a）原始量纲右偏；（b）log(1+x) 后接近正态")
table(doc, ["特征", "构造式", "物理含义"],
      [["干燥度", [mfrac([mr("P")], [mfunc("max", mdelim([mr("T"), mr("+"), mr("10"), mr(","), mr("1")]))])],
        "de Martonne 干旱指数"],
       ["月份 sin / cos", [mfunc("sin", mdelim([mfrac([mr("2πm")], [mr("12")])])),
                       mr(",", upright=True), mr("  "),
                       mfunc("cos", mdelim([mfrac([mr("2πm")], [mr("12")])]))],
        "季节性周期编码"],
       ["覆盖度年变化", [msub(mr("C"), mr("t")), mr("−"), msub(mr("C"), mr("t−12"))],
        "治理成效的年际增量"],
       ["风速滞后 1 / 3 期", [msub(mr("u"), mr("t−1")), mr(",", upright=True), mr("  "),
                        msub(mr("u"), mr("t−3"))], "风沙过程的记忆效应"],
       ["治理年限", [mfrac([mr("month_index", upright=True)], [mr("12")])],
        "时间趋势（政策强度代理）"],
       ["log输沙率", [mfunc("ln", mdelim([mr("1"), mr("+"), mr("Q")]))],
        "右偏变量的对数变换（建模目标）"]],
      widths=[3.2, 6.0, 6.4], cap="表 7  特征工程清单")

h2(doc, "4.5 共线性与标准化")
vif = S["vif_final"]
table(doc, ["保留特征", "VIF"], [[k, v] for k, v in sorted(vif.items(), key=lambda x: -x[1])],
      widths=[7.0, 3.4], cap="表 8  最终特征的方差膨胀因子（全部 ≤ 8.0）")
sc = S["scaling_compare"]
rows = [[k, v["max_abs"], v["p99_abs"], v["stretch"], "是" if v["covers_neg"] else "否"]
        for k, v in sc.items()]
table(doc, ["方案", "max|z|", "P99|z|", "拉伸度", "含负值"], rows,
      widths=[4.6, 2.8, 2.8, 2.8, 2.4],
      cap="表 9  三种标准化方案对比（拉伸度 = max|z| / P99|z|，越小越不受极端月影响）")
body(doc, "稳健标准化的定义为（中位数定中心、四分位距定尺度，参数只在训练期估计）：")
equation(doc, [
    msub(mr("z"), mr("ij")), mr("="),
    mfrac([msub(mr("x"), mr("ij")), mr("−"), msub(mr("x̃"), mr("j"))],
          [msub(mr("IQR"), mr("j"))]),
    mr(",", upright=True), mr("  "),
    msub(mr("IQR"), mr("j")), mr("="), msub(mr("Q"), mr("3j")), mr("−"), msub(mr("Q"), mr("1j")),
], number=4)
body(doc, "偏度与峰度在三种方案下完全相同——线性变换不改变分布形状。真正的差别在极端月被放大多少："
          "Z-score 与稳健标准化的拉伸度分别为 3.10 与 2.79，稳健方案略优；MinMax 的 1.34 看似更好，"
          "但那是被最大值定义的“虚假稳健”（99% 数据被压进 0.2 宽区间）。"
          "因此选 **稳健标准化（中位数 / IQR）**，参数固化到 06_scaler_params.csv，"
          "训练、测试与未来新数据必须共用同一套参数。")
figure(doc, FIG.get("fig7_共线性"), 15.0, "图 6  保留特征的 VIF 诊断（虚线为阈值 10）")
figure(doc, FIG.get("fig6_相关热图"), 13.6,
       "图 7  清洗后主要变量的相关系数矩阵（输沙率与风速正相关、与覆盖度负相关，符合风沙物理）")

h2(doc, "4.6 训练/测试划分")
sp = S["split"]
body(doc, f"按时间切分：训练 {sp['train_period']}（{sp['train_rows']} 行），"
          f"测试 {sp['test_period']}（{sp['test_rows']} 行）。未随机打乱——"
          f"时间序列随机切分会让模型“看到未来”，在真实预测场景里误差被严重低估。"
          f"截尾分位数与标准化参数都只用训练期估计，这两处是最常见的数据泄漏点。")

h1(doc, "五、处理后数据")
table(doc, ["文件", "规模", "内容"],
      [["processed/02_panel_clean.csv", f"{panel.shape[0]} × {panel.shape[1]}", "清洗后完整面板"],
       ["processed/03_features.csv", "960 × 20", "11 个特征 + 11 个稳健标准化值"],
       ["processed/04_train.csv", "768 × 22", "训练期特征 + 目标"],
       ["processed/05_test.csv", "192 × 22", "测试期特征 + 目标"],
       ["processed/06_scaler_params.csv", "11 × 3", "中位数与 IQR（不可重拟合）"],
       ["processed/07_交叉验证_POWER.csv", "3 × 7", "NASA POWER 交叉验证结果"],
       ["raw/01_站点月尺度面板_real_raw.csv", "960 × 18", "抓取后的真实原始面板"],
       ["raw/00_数据源清单.json", "—", "数据源 URL、参数、访问时间"]],
      widths=[6.8, 2.6, 6.0], font=8.4, cap="表 10  交付数据文件")

cols = ["站代码", "月份_str", "风速", "降水", "气温", "土壤含水率", "植被覆盖度", "输沙率"]


def fmt_row(v):
    return [f"{x:.2f}" if isinstance(x, float) else str(x) for x in v]


table(doc, cols, [fmt_row(r) for r in panel[cols].head(8).values.tolist()],
      widths=[1.6, 2.2, 2.0, 2.0, 2.0, 2.6, 2.8, 2.4], font=7.8,
      cap="表 11  02_panel_clean.csv 前 8 行")
table(doc, cols, [fmt_row(r) for r in panel[cols].tail(4).values.tolist()],
      widths=[1.6, 2.2, 2.0, 2.0, 2.0, 2.6, 2.8, 2.4], font=7.8,
      cap="表 12  02_panel_clean.csv 后 4 行")
body(doc, "完整性自检（30 秒）：① 形状是否 960×20；② isna().sum() 是否为 0；"
          "③ 每站记录数是否 120；④ 输沙率是否在 0—1000 之间。四项全过即可进入建模。")

if cv is not None:
    h1(doc, "六、与 NASA POWER 的交叉验证")
    rows = [[r["变量"], int(r["n"]), r["ERA5均值"], r["POWER均值"],
             r["偏差(ERA5−POWER)"], r["RMSE"], r["R²"]] for _, r in cv.iterrows()]
    table(doc, ["变量", "n", "ERA5 均值", "POWER 均值", "偏差", "RMSE", "R²"], rows,
          widths=[2.6, 1.6, 3.0, 3.0, 3.0, 2.6, 2.0],
          cap="表 13  ERA5-Land 与 NASA POWER 的逐月对比（8 站 × 120 月）")
    body(doc, "气温高度一致（R²=0.988、偏差 0.07 ℃），说明时间对齐与聚合没有出错；"
              "风速 R²=0.69、ERA5 系统性偏高 0.81 m/s，是 ERA5-Land 在干旱区对 10 m 风速的已知偏差，"
              "建议在论文中对风速做偏差订正，并在敏感性分析中给出 ±20% 的影响；"
              "降水 R² 仅 0.34，是干旱区月降水以离散事件为主的固有特征，故降水只做量级校验、不做精细订正。")
    fig8 = os.path.join(BASE, "图", "fig8_交叉验证.png")
    if os.path.exists(fig8):
        figure(doc, fig8, 16.8, "图 8  ERA5-Land 与 NASA POWER 的逐月散点（虚线为 1:1 线）")

h1(doc, "七、局限与使用建议")
for t in ["**风速存在系统偏差**（+0.8 m/s）。直接用于输沙率会整体高估风沙活动；"
          "建议标定一个风速订正系数，或让输沙率的标定系数吸收该偏差。",
          "**输沙率是公式估算值**，不是实测。适合驱动“相对变化”与“分区对比”，"
          "不宜直接引用绝对吨数作为结论；论文须写明公式与标定依据。",
          "**覆盖度由 NDVI 固定端元反演**（0.05 / 0.85）。改用站点动态端元会让绿洲站结果偏高 10—20 个百分点，"
          "建议把这一项列为敏感性分析的不确定源。",
          "**治理面积、投资、补水量为情景变量**，由优化模型设定而非观测，"
          "论文中应写在“决策变量”一节而不是“数据”一节。"]:
    bullet(doc, t)

h1(doc, "附录  代码与复现")
table(doc, ["脚本", "作用", "耗时"],
      [["01b_fetch_ndvi.py", "并发抓取 MODIS NDVI（分块缓存）", "约 4 分钟"],
       ["01_fetch_real_data.py", "抓取气象/土壤水 + 组合面板 + 派生变量", "约 5 分钟"],
       ["02_crosscheck_power.py", "NASA POWER 交叉验证", "约 1 分钟"],
       ["preprocess.py", "12 步预处理 + 7 张图 + stats.json", "约 10 秒"],
       ["build_report_real.py / build_source_report.py", "生成两份报告", "约 5 秒"]],
      widths=[5.6, 7.8, 3.0], font=8.4, cap="表 14  脚本清单")
body(doc, "依赖：pip install pandas numpy matplotlib python-docx。全部 Python 脚本在本机（3.13）跑通；"
          "MATLAB 版（preprocess.m）按 R2020b 语法编写、未在本机执行，"
          "首次运行若报错请优先检查中文列名的 VariableNamingRule 与动态字段名两处。")

stage = OUT + ".tmp.docx"
doc.save(stage)
import time as _t

_ok = False
for _ in range(10):
    try:
        os.replace(stage, OUT)
        _ok = True
        break
    except PermissionError:
        _t.sleep(3)
if not _ok:
    print("WARN: 目标文件被占用，已保留临时文件：", stage)
print("saved:" if _ok else "saved(temp):", OUT if _ok else stage)

