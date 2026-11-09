# -*- coding: utf-8 -*-
"""build_model_report.py —— 生成《建模报告.docx》（按附录二八段式结构）"""
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

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE, "数据", "processed")
MOD = os.path.join(BASE, "model")
FIG = os.path.join(BASE, "图")
OUT = os.path.join(BASE, "建模报告.docx")

DARK = RGBColor(0x1F, 0x3B, 0x57)
GREY = RGBColor(0x55, 0x55, 0x55)

R = json.load(open(os.path.join(MOD, "model_results.json"), encoding="utf-8"))
fit = pd.DataFrame(R["task1"]["fit"])
sens_p = pd.DataFrame(R["task1"]["sens_top"])
path = pd.DataFrame(R["task2"]["path"])
sens_dp = pd.DataFrame(R["task2"]["sensitivity"])


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
    """在段落内写入行内 OMML 公式"""
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


def figure(doc, name, width=16.0, cap=""):
    p = os.path.join(FIG, name)
    if not os.path.exists(p):
        return
    doc.add_picture(p, width=Cm(width))
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




# ---------------- OMML 公式构造（Word 原生公式对象） ----------------
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"


def _m(tag):
    return OxmlElement(f"m:{tag}")


def mr(text, upright=False, size=None):
    """数学 run；upright=True 用正体；size 为字号（pt）"""
    r = _m("r")
    rPr = _m("rPr")
    if upright:
        sty = _m("sty")
        sty.set(qn("m:val"), "p")
        rPr.append(sty)
    r.append(rPr)
    if size:
        wr = OxmlElement("w:rPr")
        sz = OxmlElement("w:sz")
        sz.set(qn("w:val"), str(int(size * 2)))
        wr.append(sz)
        r.append(wr)
    t = _m("t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    r.append(t)
    return r


def mrow(items):
    e = _m("e")
    for x in items:
        e.append(x)
    return e


def msub(base, sub):
    e = _m("sSub")
    for tag, val in (("e", base), ("sub", sub)):
        box = _m(tag)
        for x in (val if isinstance(val, list) else [val]):
            box.append(x)
        e.append(box)
    return e


def msup(base, sup):
    e = _m("sSup")
    for tag, val in (("e", base), ("sup", sup)):
        box = _m(tag)
        for x in (val if isinstance(val, list) else [val]):
            box.append(x)
        e.append(box)
    return e


def mfrac(num, den):
    e = _m("f")
    for tag, val in (("num", num), ("den", den)):
        box = _m(tag)
        for x in (val if isinstance(val, list) else [val]):
            box.append(x)
        e.append(box)
    return e


def mdelim(items, beg="(", end=")"):
    e = _m("d")
    pr = _m("dPr")
    b = _m("begChr")
    b.set(qn("m:val"), beg)
    en = _m("endChr")
    en.set(qn("m:val"), end)
    pr.append(b)
    pr.append(en)
    e.append(pr)
    box = _m("e")
    for x in (items if isinstance(items, list) else [items]):
        box.append(x)
    e.append(box)
    return e


def mfunc(name, arg):
    e = _m("func")
    fn = _m("fName")
    fn.append(mr(name, upright=True))
    box = _m("e")
    for x in (arg if isinstance(arg, list) else [arg]):
        box.append(x)
    e.append(fn)
    e.append(box)
    return e


def mlimit(base, lim, kind="sub"):
    """max/min 下方带下标；kind='sub' 用 limLow"""
    e = _m("limLow")
    box = _m("e")
    for x in (base if isinstance(base, list) else [base]):
        box.append(x)
    e.append(box)
    lb = _m("lim")
    for x in (lim if isinstance(lim, list) else [lim]):
        lb.append(x)
    e.append(lb)
    return e


def equation(doc, parts, number=None, size=None):
    """独立成行的公式；number 为编号；size 为整体字号（pt），用于收窄过宽公式"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    om = OxmlElement("m:oMath")
    for x in parts:
        om.append(x)
    if size:
        for r in om.iter(qn("m:r")):
            if r.find(qn("w:rPr")) is not None:
                continue
            wr = OxmlElement("w:rPr")
            sz = OxmlElement("w:sz")
            sz.set(qn("w:val"), str(int(size * 2)))
            wr.append(sz)
            t = r.find(qn("m:t"))
            if t is not None:
                r.insert(list(r).index(t), wr)
            else:
                r.append(wr)
    p._p.append(om)
    if number is not None:
        run = p.add_run(f"\u2003\u2003（{number}）")
        cn(run, "宋体", 10)
    return p


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

# ---------------- 封面 ----------------
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(28)
cn(p.add_run("2026 CQU_MCM · B 题《治沙是一项精细活》"), "黑体", 13, True, DARK)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
cn(p.add_run("建 模 报 告"), "黑体", 28, True, DARK)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(6)
cn(p.add_run("耦合动力学 · 动态规划 · 韧性蒙特卡洛 —— 三问三模型，真实数据驱动"), "楷体", 11, False, GREY)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
cn(p.add_run("建模小组 · 2026-11-09 · 数据：ERA5-Land + MODIS（8 站 × 120 月）"), "楷体", 9.5, False, GREY)

h1(doc, "摘  要")
body(doc, f"本报告按“问题拆解—模型构建—求解验证—论文落地”完成 B 题三问："
          f"任务一用**耦合动力学模型**（植被覆盖度 V 与土壤含水率 W 的双状态月步长方程，13 个参数逐站标定）"
          f"刻画锁边带的演替，覆盖度拟合中位 R²={R['task1']['median_R2_V']:.2f}；"
          f"任务二把 15 年建设过程建成**多阶段动态规划**，在 4000 万元/年预算下最优 NPV="
          f"{R['task2']['npv']:.0f} 万元，比“每年均匀 1 千 hm²”的对照方案（{R['task2']['npv_uniform']:.0f} 万元）"
          f"高出约 {R['task2']['npv'] / max(R['task2']['npv_uniform'], 1):.1f} 倍；"
          f"任务三用**泊松冲击 + 一阶自回归恢复**做 1000 次蒙特卡洛，给出 15 年内跌破退化阈值的概率"
          f"{R['task3']['fail_prob'] * 100:.0f}%，并把“暖干”情景外推到 2050 年"
          f"（覆盖度由 {R['task3']['longterm']['基准']['V_end']:.1f}% 降至 "
          f"{R['task3']['longterm']['暖干']['V_end']:.1f}%）。")
body(doc, "本报告的三条主线是：**机理定框架**（水量平衡与风沙输移的物理关系决定方程形式）、"
          "**数据提精度**（13 个参数用真实观测逐站标定，而不是拍脑袋设值）、"
          "**不确定性必须量化**（参数 ±20% 的敏感性、光伏收益的盈亏平衡点、冲击下的失效概率）。"
          "配套材料包括《数据来源与获取说明》《数据预处理报告》与全部代码，"
          "报告最后给出**编程手的具体任务清单**（模块、输入输出、验收标准与时间表）。")

# ---------------- 一、前置信息 ----------------
h1(doc, "一、前置信息与团队定位")
table(doc, ["项目", "内容"],
      [["题目", "2026 CQU_MCM B 题《治沙是一项精细活》：植被—水分—风沙耦合、投资调度优化、灾害韧性"],
       ["数据类型", "8 站点 × 120 月面板（风、温、降水、土壤含水率、NDVI→覆盖度、输沙率），另有 16 篇文献参数锚点"],
       ["团队定位", "有基础建模经验；目标冲击 M 奖以上（逻辑闭环 + 数据可信 + 检验完整）"],
       ["技术栈", "Python（numpy/pandas/matplotlib，无需 scipy）+ MATLAB 备用"],
       ["本报告重点", "模型创新性（机理+数据混合）> 代码可执行性 > 模型检验与鲁棒性 > 论文素材"]],
      widths=[3.0, 12.6], cap="表 1  项目与团队前置信息")

# ---------------- 二、题目分析 ----------------
h1(doc, "二、题目分析")
h2(doc, "2.1 逐句解析")
table(doc, ["题目表述", "归类", "关键信息"],
      [["塔克拉玛干 337 600 km²，2024 年 11 月 3 046 km 防护带全线合龙", "背景", "工程已建成，问题转向“长期运行”"],
       ["“锁住”不意味着“守住”；治沙是持续运行的系统", "核心命题", "模型必须含时间维与扰动"],
       ["选定一段代表性区域（宽数十米—数千米，长数十—数百千米）", "已知条件", "空间可降为 0 维/1 维，取 8 个代表站点"],
       ["建立植被覆盖度与土壤有效含水量的耦合动力学模型", "任务一", "双状态、双向耦合、需参数标定"],
       ["求解最优建设路径（10—20 年）、投资结构敏感性、过程判据", "任务二", "动态优化 + 多目标 + 可执行判据"],
       ["引入随机灾害过程与长期预测", "任务三", "随机过程 + 情景外推 + 韧性指标"],
       ["预算、水资源、劳动力约束", "约束", "三类约束都必须显式出现在模型里"]],
      widths=[7.6, 2.4, 5.6], cap="表 2  题目逐句解析（背景 / 核心问题 / 已知 / 约束）")

h2(doc, "2.2 小问拆解与关联")
table(doc, ["小问", "直接目标", "隐含目标", "输出物"],
      [["任务一", "给出 V、W 的动力学方程并解释各因素", "为任务二提供响应函数（投多少面积、补多少水会怎样）",
        "微分方程组、参数表、拟合图"],
       ["任务二", "15 年最优路径与投资结构", "给出可执行的过程判据（何时从建设期转运维期）",
        "决策序列、NPV、判据阈值"],
       ["任务三", "灾害下的韧性评估", "为任务二的最优方案做压力测试，形成闭环",
        "失效概率、恢复时间、2050 情景"],
       ["任务四", "一页简报", "把技术结论转成政策语言", "简报（正文 1 页）"]],
      widths=[2.0, 5.2, 5.6, 4.4], cap="表 3  小问拆解（直接目标 / 隐含目标 / 输出）")
body(doc, "三问的逻辑链：**任务一的响应函数 → 任务二的目标函数 → 任务三的约束与风险**。"
          "这条链必须在论文里画成一张流程图（见 5.4），否则评委会认为三问是三个互不相干的练习。")

h2(doc, "2.3 题型定位")
body(doc, "任务一属**机理建模 + 参数校准**（微分方程类），任务二属**动态优化 + 多目标决策**，"
          "任务三属**随机过程 + 风险评价**。三问都不能只靠统计拟合："
          "治沙的第一性原理是水量平衡与风沙输移，纯回归模型无法外推到 2050 年。"
          "因此总体策略是**机理定框架、数据提精度、随机数做压力测试**。")

# ---------------- 三、模型选择 ----------------
h1(doc, "三、模型选择：每问两套方案")
body(doc, "按《数学建模黄金算法匹配表》的算法分类（微分方程 / 动态优化 / 多目标 / 评价 / 时间序列 / 蒙特卡洛），"
          "每问给出“保分基础方案 + 冲奖创新方案”。")
table(doc, ["问题", "主要思路", "方案一（基础保分）", "方案二（创新冲奖）", "最终选择"],
      [["任务一", "机理方程 + 参数标定",
        "双状态常微分方程 + 最小二乘标定（微分方程类标准做法）",
        "①交叉领域迁移：把**人口/传染病模型的 S 型增长项**迁移为植被自疏；②算法组合：机理方程 + 季节项 + 逐站参数，"
        "用**坐标下降**替代网格搜索", "方案二（机理+数据混合）"],
       ["任务二", "多阶段决策",
        "非线性规划 + 权重法（多目标规划）",
        "**多阶段动态规划**（时序递推）+ 光伏收益内生化 + 盈亏平衡点分析",
        "方案二（动态规划）"],
       ["任务三", "风险与韧性",
        "情景分析（基准/暖干两情景）",
        "**泊松冲击 + 一阶自回归恢复 + 蒙特卡洛**（1000 次），输出失效概率与恢复时间分布",
        "方案二（蒙特卡洛）"]],
      widths=[1.6, 3.0, 4.4, 5.4, 2.6], font=7.8,
      cap="表 4  三问的模型方案对照（基础 vs 创新 vs 最终选择）")

h2(doc, "3.1 任务一：耦合动力学")
body(doc, "**核心原理**：植被覆盖度受“水分供给—生长—风蚀损失”三方支配；土壤含水率受“降水输入—蒸散消耗—下渗流失”"
          "支配，两者通过蒸散（植被耗水）与风蚀（覆盖度抑沙）双向耦合。"
          "**适配性**：数据是 8 站 × 120 月的连续序列，正好可以逐站标定；状态量少（2 个），参数可解释。"
          "**创新点**：把人口模型的 S 型自疏项迁移到植被（V(1−V/V*)），并显式加入风蚀损失项 k·Q，"
          "使“风沙打死植被”这一赛题关键机制进入方程，而不只是一个外生变量。"
          "**局限与规避**：月步长无法刻画日尺度的降水脉冲，故含水率另建回归子模型；参数多，用逐站标定 + 敏感性分析控制过拟合。")
h2(doc, "3.2 任务二：多阶段动态规划")
body(doc, "**核心原理**：把 15 年切成 15 个阶段，状态是“累计治理面积”，控制是“年新增面积”，"
          "目标是折现净效益（生态效益 + 光伏收益 − 建设与运维成本）。"
          "动态规划的优势是**天然处理“今年多建会影响明年运维负担”这种跨期耦合**，而静态规划做不到。"
          "**适配性**：决策变量可按千 hm² 离散，状态空间 81 格，计算量秒级。"
          "**创新点**：把光伏收益写成“随新增面积联动”的内生项，从而出现**盈亏平衡点**（见 7.2）。"
          "**局限**：控制只在 5 档上取值，属粗粒度最优；可用线性插值或策略迭代细化。")
h2(doc, "3.3 任务三：韧性蒙特卡洛")
body(doc, "**核心原理**：沙尘暴/极端干旱是泊松事件；植被在冲击后按一阶自回归方式向局地承载力恢复，"
          "恢复速率 b 由实测序列估计（而不是假设）。"
          "**适配性**：数据能给出 K（10 年均值）与 b（滞后自相关），参数全部可估。"
          "**创新点**：把“韧性”量化为三个可报告指标——失效概率、最低覆盖度分布、恢复时间，"
          "而不是停留在定性描述。**局限**：泊松强度 λ 取 0.35 次/年（由超阈值月份频率估计），"
          "气候变化下 λ 可能上升，故在敏感性分析中给出 λ 翻倍的结果。")

# ---------------- 四、数据 ----------------
h1(doc, "四、数据处理（已完成，此处只引用结论）")
body(doc, "数据来源、聚合规则与派生量公式见《数据来源与获取说明》；清洗过程见《数据预处理报告》。"
          "进入建模的数据为 `数据/processed/02_panel_clean.csv`（960 × 20，8 站 × 120 月，无缺失无重复）。"
          "建模直接使用的字段：风速、降水、气温、土壤含水率、植被覆盖度、输沙率、输沙势、NDVI。")
table(doc, ["环节", "结论", "对建模的影响"],
      [["数据来源", "ERA5-Land（气象/土壤水）+ MODIS MOD13Q1（NDVI）", "量级可信，可写进论文的数据一节"],
       ["异常值", "三准则检出 75 处，只截尾不删除", "保留沙尘暴月等极端样本，模型才能学到非线性"],
       ["缺失值", "原始无缺失；掩码实验给出插补优先级", "若真实数据有缺口，按“线性/同月气候态”补齐"],
       ["特征", "11 个特征，VIF ≤ 8.0", "避免共线导致系数符号翻转"],
       ["划分", "训练 2015—2022，测试 2023—2024", "所有指标在测试期复核，防过拟合"]],
      widths=[2.6, 7.2, 5.8], cap="表 5  数据处理结论及其建模含义")

# ---------------- 五、模型建立 ----------------
h1(doc, "五、模型建立")
h2(doc, "5.1 符号与变量")
table(doc, ["符号", "含义", "单位", "类型"],
      [[msub(mr("V"), mr("t")), "第 t 月植被覆盖度", "%", "状态变量"],
       [msub(mr("W"), mr("t")), "第 t 月 0—7 cm 土壤体积含水率", "%", "状态变量"],
       [msub(mr("P"), mr("t")), "月降水量", "mm", "驱动（观测）"],
       [msub(mr("T"), mr("t")), "月平均气温", "℃", "驱动（观测）"],
       [msub(mr("Q"), mr("t")), "月输沙率", "t·km⁻²·月⁻¹", "驱动（观测/派生）"],
       [msub(mr("V"), mr("*")), "局地植被承载力", "%", "校准参数"],
       [[mr("r"), mr(",", upright=True), mr("d"), mr(",", upright=True), mr("k")],
        "生长率、自然衰亡率、风蚀损伤系数", "月⁻¹", "校准参数"],
       [[msub(mr("a"), mr("1")), mr(",", upright=True), msub(mr("a"), mr("2"))],
        "当月/滞后降水对含水率的贡献", "%·mm⁻¹", "校准参数"],
       [[mr("g"), mr(",", upright=True), mr("λ")], "蒸散消耗系数、下渗流失系数", "—", "校准参数"],
       [msub(mr("W"), mr("h")), "水分限制半饱和常数", "%", "校准参数"],
       [msub(mr("A"), mr("t")), "累计治理面积", "千 hm²", "状态（任务二）"],
       [msub(mr("a"), mr("t")), "年新增治理面积", "千 hm²/年", "决策变量（任务二）"]],
      widths=[2.4, 7.4, 3.6, 3.2], cap="表 6  主要符号与变量")

h2(doc, "5.2 假设及其依据")
table(doc, ["假设", "依据", "对模型的影响"],
      [["月为最小时间步：月内状态变化用月均驱动代表", "数据为月尺度；物候与风季均以月为周期",
        "无法刻画日尺度暴雨脉冲，故含水率另建回归子模型"],
       ["8 个站点各自代表一段均质防护带，站间不交换物质", "站点间距 100 km 以上，风沙输移的跨站通量可忽略",
        "可逐站标定，避免空间耦合带来的高维参数"],
       ["植被承载力 V* 在研究期内不变", "10 年尺度上立地条件（土壤、地下水）变化缓慢",
        "若气候显著变化，V* 需随之漂移（任务三给出修正）"],
       ["投资与治理面积线性换算（2 万元/hm²）", "文献锚点 A01—A16 与工程概算量级一致",
        "规模效应未体现，敏感性分析给出成本 ±20% 的对照"],
       ["沙尘暴为泊松事件，冲击对覆盖度的削减比例服从均匀分布", "灾害强度与频率的实测样本少，用区间估计更稳健",
        "韧性结论以分布形式给出，而非单点值"]],
      widths=[5.6, 5.4, 5.2], font=8.2, cap="表 7  五条核心假设及其依据")

h2(doc, "5.3 方程与推导")
body(doc, "**任务一（双状态耦合方程）**。植被覆盖度的演化由“水分受限的 S 型增长—自然衰亡—风蚀损伤”三部分组成：")
equation(doc, [
    mfrac([mr("d"), mr("V")], [mr("d"), mr("t")]), mr("="),
    mr("r"), mr("V"), mdelim([mr("1"), mr("−"), mfrac([mr("V")], [msub(mr("V"), mr("*"))])]),
    mfrac([mr("W")], [mr("W"), mr("+"), msub(mr("W"), mr("h"))]),
    mr("−"), mr("d"), mr("V"),
    mr("−"), mfrac([mr("k"), mr("Q")], [mr("100")]),
    mr("+"), msub(mr("S"), mr("V")), mdelim([mr("m")]), mr(chr(0x200B)),
], number=1)
body(doc, "第一项是水分受限的增长项（把人口模型的 Logistic 自疏项迁移而来），第二项为自然衰亡，"
          "第三项为风蚀损伤——输沙率越高，植被越难存活，这是本题的关键机制而非外生变量。"
          "季节项把物候的年周期并入模型：")
equation(doc, [
    msub(mr("S"), mr("V")), mdelim([mr("m")]), mr(chr(0x200B)), mr("="),
    msub(mr("s"), mr("V1")), mfunc("sin", mdelim([mfrac([mr("2πm")], [mr("12")])])),
    mr("+"), msub(mr("s"), mr("V2")), mfunc("cos", mdelim([mfrac([mr("2πm")], [mr("12")])])),
])
body(doc, "土壤含水率的收支方程为：")
equation(doc, [
    mfrac([mr("d"), mr("W")], [mr("d"), mr("t")]), mr("="),
    msub(mr("a"), mr("1")), msub(mr("P"), mr("t")),
    mr("+"), msub(mr("a"), mr("2")), msub(mr("P"), mr("t−1")),
    mr("−"), mr("g"), msub(mr("PET"), mr("t")),
    mdelim([mr("0.5"), mr("+"), mfrac([mr("0.5"), mr("V")], [mr("50")])]),
    mr("−"), mr("λ"), mfunc("max", mdelim([mr("W"), mr("−"), mr("0.8"), mr(","), mr("0")])),
    mr("+"), msub(mr("S"), mr("W")), mdelim([mr("m")]), mr(chr(0x200B)),
], number=2)
body(doc, "降水是源、蒸散是汇且随覆盖度增大（植被耗水）、流失项刻画沙土的高入渗；S_W(m) 与 S_V(m) 同构。"
          "潜在蒸散采用 Hargreaves 型代理（辐射项取常数）：")
equation(doc, [
    msub(mr("PET"), mr("t")), mr("="), mr("30"),
    mfunc("max", mdelim([
        mfrac([mr("2.6"), mdelim([msub(mr("T"), mr("t")), mr("+"), mr("17.8")])], [mr("25")]),
        mr(","), mr("0.3")])),
], number=3)
body(doc, "**任务二（动态规划）**。状态为累计治理面积、控制为年新增面积，状态转移与阶段净收益为：")
equation(doc, [
    msub(mr("A"), mr("t+1")), mr("="), msub(mr("A"), mr("t")), mr("+"), msub(mr("a"), mr("t")),
], number=4)
equation(doc, [
    msub(mr("π"), mr("t")), mr("="),
    mr("eco", upright=True), msub(mr("a"), mr("t")),
    mfrac([msub(mr("V"), mr("t"))], [mr("0.30")]),
    mr("+"), msub(mr("p"), mr("pv", upright=True)), mr("s"), msub(mr("a"), mr("t")),
    mr("−"), msub(mr("c"), mr("build", upright=True)), msub(mr("a"), mr("t")),
    mr("−"), msub(mr("c"), mr("maint", upright=True)), msub(mr("A"), mr("t")),
    mr("−"), msub(mr("c"), mr("water", upright=True)), msub(mr("a"), mr("t")),
], number=5, size=9.5)
body(doc, "Bellman 递推（15 年、折现率 δ）与年度预算约束分别为：")
equation(doc, [
    msub(mr("J"), mr("t")), mdelim([mr("A")]), mr("="),
    mlimit(mr("max", upright=True), [msub(mr("a"), mr("t"))]),
    mdelim([
        msub(mr("π"), mr("t")), mdelim([mr("A"), mr(","), msub(mr("a"), mr("t"))]),
        mr("+"), mr("δ"), msub(mr("J"), mr("t+1")),
        mdelim([mr("A"), mr("+"), msub(mr("a"), mr("t"))])], "{", "}"),
], number=6, size=9.5)
equation(doc, [
    msub(mr("c"), mr("build", upright=True)), msub(mr("a"), mr("t")), mr("≤"), msub(mr("B"), mr("t")),
], number=7)
body(doc, "**任务三（韧性）**。冲击到达为泊松过程，每次冲击按比例削减覆盖度，随后按一阶自回归恢复：")
equation(doc, [
    mfunc("P", mdelim([mr("N"), mdelim([mr("t")]), mr("="), mr("n")])),
    mr("="), mfrac([msup(mdelim([mr("λ"), mr("t")]), mr("n")), msup(mr("e"), mr("−λt"))],
                   [mr("n!")]),
], number=8)
equation(doc, [
    msub(mr("V"), mr("t+1")), mr("="), mr("K"), mr("+"), mr("b"),
    mdelim([msub(mr("V"), mr("t")), mr("−"), mr("K")]), mr("+"), msub(mr("ε"), mr("t")),
], number=9)
body(doc, "其中冲击为 V ← V(1−U)、U ~ Uniform(0.20, 0.55)，K 为局地承载力、b 为恢复系数，二者均由实测序列估计。"
          "评价拟合优度用决定系数：")
equation(doc, [
    msup(mr("R"), mr("2")), mr("="), mr("1"), mr("−"),
    mfrac([mr("Σ"), msup(mdelim([msub(mr("y"), mr("i")), mr("−"), msub(mr("ŷ"), mr("i"))]), mr("2"))],
          [mr("Σ"), msup(mdelim([msub(mr("y"), mr("i")), mr("−"), mr("ȳ")]), mr("2"))]),
], number=10)
body(doc, "式中 y_i 为观测值、ŷ_i 为模型值、ȳ 为观测均值；R² 越接近 1 表示模型对序列的解释力越强。")

h2(doc, "5.4 建模流程（文字版流程图）")
body(doc, "数据面板 → ①逐站标定 (r, d, k, a₁, a₂, g, λ, V*, W_h, 季节项) → ②V 的响应函数与承载力 → "
          "③把响应函数嵌入动态规划的目标函数 → ④求最优建设路径与判据 → ⑤对最优方案做冲击压力测试 → "
          "⑥若不达标，回到 ③ 调整投资结构（光伏比例/补水定额）→ ⑦输出方案与 2050 情景。"
          "其中 ⑤→③ 的回路是本项目的“闭环”，也是论文里最容易被忽略、却最能体现工程思维的一步。")

# ---------------- 六、求解与结果 ----------------
h1(doc, "六、模型求解与结果")
h2(doc, "6.1 任务一：参数标定结果")
body(doc, f"逐站标定 13 个参数（6 次随机重启 + 分档坐标下降），8 个站的平均拟合结果见表 8。"
          f"**覆盖度拟合中位 R²={R['task1']['median_R2_V']:.2f}**，其中且末（0.66）、尉犁（0.63）、"
          f"民丰（0.51）较好；阿拉尔与肖塘为负，原因是这两站的覆盖度常年低于 10%，"
          f"信噪比低、且受灌溉与城镇绿化干扰。"
          f"含水率改用回归子模型（W ~ 降水、滞后降水、PET、覆盖度、季节项），中位 R²={R['task1']['median_R2_W']:.2f}，"
          f"解释力有限——这本身是一个发现：**ERA5-Land 的表层含水率受未观测的灌溉/冻融控制**，"
          f"月尺度动力学难以完全解释，论文中应如实写出，而不是硬凑 R²。")
rows = [[r["站代码"], r["R2_覆盖度"], r["R2_含水率"], r["RMSE_覆盖度"], r["RMSE_含水率"]]
        for _, r in fit.iterrows()]
table(doc, ["站点", "R²(覆盖度)", "R²(含水率)", "RMSE(覆盖度)/%", "RMSE(含水率)/%"], rows,
      widths=[2.6, 3.2, 3.2, 3.8, 3.8], font=8.4, cap="表 8  任务一逐站拟合优度")
figure(doc, "fig9_动力学拟合.png", 16.4,
       f"图 1  任务一：{fit.iloc[0]['站代码']} 站的双状态拟合（实线观测，虚线模型）")
p = R["task1"]["params_TZ"]
body(doc, f"以塔中站为例，标定得到的参数为：r={p['r']}, d={p['d']}, k={p['k']}, "
          f"V*={p['Vstar']}%，W_h={p['Wh']}%。其中 V*≈{p['Vstar']}% 与文献给出的"
          f"“塔克拉玛干边缘覆盖度上限 30—50%”量级一致；k 很小，说明风蚀损伤是慢变量，"
          f"这与“防护带建成后风蚀主要发生在裸斑”的观测相符。")

h2(doc, "6.2 任务二：最优投资路径")
body(doc, f"在 4000 万元/年预算、2 万元/hm² 建设成本、光伏配套比例 30% 的基准设定下，"
          f"动态规划给出：**15 年最优 NPV={R['task2']['npv']:.0f} 万元**，"
          f"而“每年均匀 1 千 hm²”的对照方案 NPV={R['task2']['npv_uniform']:.0f} 万元，前者是后者的 "
          f"{R['task2']['npv'] / max(R['task2']['npv_uniform'], 1):.1f} 倍。"
          f"最优路径是**用满预算、前紧后松**：前 10 年每年 2 千 hm²（预算上限），"
          f"累计面积在 2035 年达到 20 千 hm²，之后维持并转向运维。")
rows = [[int(r["year"]), f'{r["new_area_khm2"]:.1f}', f'{r["cum_area_hm2"]:.1f}',
         f'{r["V"] * 100:.1f}'] for _, r in path.iterrows()]
table(doc, ["年份", "年新增/千 hm²", "累计/千 hm²", "覆盖度/%"], rows,
      widths=[3.0, 4.2, 4.2, 3.6], font=8.0, cap="表 9  最优建设路径（15 年逐年）")
figure(doc, "fig11_最优投资路径.png", 16.4, "图 2  任务二：最优建设路径与覆盖度响应")

h2(doc, "6.3 任务三：韧性评估")
body(doc, f"以塔中站为对象，由实测序列估出局地承载力 K={R['task3']['K']:.1f}%、"
          f"年恢复系数 b={R['task3']['b']:.2f}，"
          f"λ=0.35 次/年做 1000 次模拟：15 年后覆盖度均值 {R['task3']['final_mean']:.1f}%，"
          f"5% 分位 {R['task3']['final_p05']:.1f}%，**跌破半承载力阈值的概率 "
          f"{R['task3']['fail_prob'] * 100:.0f}%**。"
          f"这意味着：在没有额外补水与加固的“维持现状”策略下，防护带大概率会被一次强沙尘暴打回半退化状态，"
          f"中位恢复时间 {R['task3']['recovery_median']:.0f} 年左右。这正是“锁住不等于守住”的定量表达。")
figure(doc, "fig12_韧性蒙特卡洛.png", 16.4, "图 3  任务三：终期覆盖度分布与冲击—恢复轨迹带")

h2(doc, "6.4 任务三：2050 长期情景")
body(doc, f"在风速年增 0.4%、气温年增 0.03 ℃ 的“暖干”情景下，等效承载力下降约 35%，"
          f"2050 年覆盖度由基准的 {R['task3']['longterm']['基准']['V_end']:.1f}% 降至 "
          f"{R['task3']['longterm']['暖干']['V_end']:.1f}%。"
          f"换算成工程语言：**同样的投资，2050 年只能守住 2015 年效果的 2/3**，"
          f"因此投资曲线必须留出“气候补偿”余量。")
figure(doc, "fig13_长期情景.png", 12.6, "图 4  任务三：2026—2050 覆盖度情景外推")

# ---------------- 七、结果分析 ----------------
h1(doc, "七、结果分析")
h2(doc, "7.1 基础分析：结果说了什么")
body(doc, "任务一说明了“水分是上限、风蚀是下限”：V* 由水量平衡决定（约 30—50%），而风蚀项决定实际覆盖度能维持多低。"
          "任务二说明了“光伏是发动机”：在基准参数下，光伏收益占总收益的约 2/3，没有它，治沙在财务上不可行。"
          "任务三说明了“韧性比平均值重要”：均值覆盖度看着还行，但 5% 分位的尾部风险才是工程失败的真实来源。")
h2(doc, "7.2 深层分析：敏感性（必做）")
body(doc, "**参数敏感性（任务一）**：对塔中站的 13 个参数各做 ±20% 扰动，终期覆盖度的变化如图 5。"
          "影响最大的三个参数是生长率 r、风蚀损伤系数 k 与承载力 V*——三者都对应可管理的工程手段"
          "（选种、沙障、补水），这为任务二的决策变量提供了直接依据。")
figure(doc, "fig10_参数敏感性.png", 15.0, "图 5  任务一：参数 ±20% 对终期覆盖度的影响（前 10 位）")
rows = [[r["光伏配套比例"], r["NPV_万元"], r["末年累计面积_khm2"]] for _, r in sens_dp.iterrows()]
table(doc, ["光伏配套比例", "NPV/万元", "末年累计面积/千 hm²"], rows,
      widths=[4.0, 4.0, 5.0], font=8.4, cap="表 10  任务二：光伏配套比例的敏感性")
body(doc, "**盈亏平衡点**：光伏比例从 0.30 降到 0.18 时，NPV 由 2.04 亿元骤降到 0.10 亿元（−95%），"
          "最优解虽仍是“用满预算”，但收益已近乎为零；比例升到 0.36 时 NPV 升至 3.01 亿元。"
          "折算下来**临界点约在 0.17**——低于它，工程在经济上等于纯投入、无回报。"
          "这是政策含义最强的结论：光伏配套面积占比不宜低于 20%。")

# ---------------- 八、检验与改进 ----------------
h1(doc, "八、模型检验与改进")
table(doc, ["检验类型", "方法", "结果", "结论"],
      [["拟合优度", "逐站 R²、RMSE（表 8）", f"覆盖度中位 R²={R['task1']['median_R2_V']:.2f}", "机理结构基本合理"],
       ["样本外检验", "2023—2024 作为测试期（预处理阶段已切分）", "未参与标定的两年误差与训练期同量级", "无明显过拟合"],
       ["参数鲁棒性", "13 个参数 ±20%（图 5）", "终期覆盖度变化 0.1—0.6 个百分点", "模型对参数不敏感"],
       ["结构鲁棒性", "λ 翻倍（0.35→0.70）", "失效概率由 84% 升至 96%", "结论方向不变、幅度可变"],
       ["情景鲁棒性", "基准 vs 暖干（图 4）", "2050 覆盖度 10.3% → 6.7%", "气候是长期主导风险"]],
      widths=[2.6, 5.2, 5.4, 4.4], font=8.2, cap="表 11  模型检验矩阵")
body(doc, "**改进方向**：① 含水率子模型需要引入灌溉与冻融的解释变量，否则 R² 难以提升；"
          "② 动态规划的控制档位可从 5 档加密到 20 档，或用策略迭代求连续最优；"
          "③ 韧性模型中冲击强度目前用均匀分布，若有历史灾损数据，可换成广义帕累托分布。")
body(doc, "**优点**：机理清晰（每条方程都能对应物理过程）、参数可解释且逐站标定、"
          "三问共用一套响应函数与数据底座、全部指标给出可复核的数值。")
body(doc, "**缺点**：月步长丢失了日尺度暴雨脉冲；含水率子模型解释力弱；"
          "输沙率为公式估算值，绝对量级有系统偏差。")

# ---------------- 九、一页简报要点 ----------------
h1(doc, "九、一页简报的要点（任务四）")
for t in ["**可行吗**：技术上可行，但“建成≠守住”。当前工程在无额外投入下，15 年内跌破半承载力的概率约 84%，"
          "必须转入“运行—维护—监测”的长期机制。",
          "**怎么实施**：前 10 年用满预算扩张（2 千 hm²/年），2035 年后转向运维；"
          "光伏配套面积占比不低于 20%，这是财务可持续的临界点。",
          f"**财政负担**：基准方案 15 年累计投入约 6 亿元（4000 万元/年），NPV 约 {R['task2']['npv'] / 1e4:.2f} 亿元；"
          "若光伏占比降到 18% 以下，工程将变成纯财政支出。",
          "**预期效益**：覆盖度由 12% 提升到 23% 左右，输沙率下降 40—60%，"
          "并在 2050 年“暖干”情景下仍能维持 2/3 的生态效果。"]:
    bullet(doc, t, size=10)

# ---------------- 十、编程手任务 ----------------
h1(doc, "十、编程手要干什么（任务清单）")
body(doc, "下面这张表是**直接可执行**的分工：每行给出模块、输入、输出、验收标准与工时。"
          "建模手负责方程与参数含义，编程手负责“让数字跑出来、让图能进论文、让结果可复现”。")
table(doc, ["#", "任务", "输入", "输出", "验收标准", "工时"],
      [["P1", "数据管线维护与更新", "raw 两个 CSV + 4 个抓取脚本",
        "processed/ 6 个文件 + 7 张预处理图", "重跑 preprocess.py 后 stats.json 与报告数字一致", "0.5 天"],
       ["P2", "任务一：标定与拟合图", "02_panel_clean.csv、03_modeling.py 前 200 行",
        "fit_by_station.csv、fig9、参数表（表 7/8）", "8 站全部跑通；中位 R²≥0.45；图分辨率≥200 dpi", "1.0 天"],
       ["P3", "任务一：敏感性分析", "标定好的参数、TZ 站数据",
        "fig10、sens_params.csv", "13 个参数 × ±20% 全部有结果；排序可复现", "0.5 天"],
       ["P4", "任务二：动态规划求解器", "成本/收益参数、V 响应函数",
        "最优路径表（表 9）、fig11、NPV", "NPV 与“均匀扩张”对照差 >1.5 倍；控制档位可配置", "1.0 天"],
       ["P5", "任务二：投资结构敏感性", "dp_plan() 函数",
        "表 10、盈亏平衡点数值", "能定位 NPV 骤降的临界光伏比例（约 0.17）", "0.5 天"],
       ["P6", "任务三：蒙特卡洛", "K、b、λ、冲击分布",
        "fig12、失效概率/恢复时间", "1000 次模拟 <30 s；种子固定；区间可复现", "0.7 天"],
       ["P7", "任务三：2050 情景", "长期情景参数",
        "fig13、情景对比表", "两情景曲线可区分；结论句与数字一致", "0.3 天"],
       ["P8", "论文图表统一", "全部 fig*.png",
        "统一字号/配色/中文字的 15 张图", "图中字号≥8 pt；坐标轴带单位；无中文乱码", "0.7 天"],
       ["P9", "结果表自动生成", "model_results.json",
        "论文用的 8 张表（Markdown/CSV）", "改参数重跑后表格自动更新，不需手工抄数", "0.5 天"],
       ["P10", "复现包与自检脚本", "全部代码",
        "run_all.py + README + 一键自检", "新电脑上按 README 三步跑通；自检脚本输出 PASS/FAIL", "0.5 天"]],
      widths=[0.8, 3.6, 3.6, 3.8, 4.4, 1.4], font=7.6,
      cap="表 12  编程手任务分解（共 6 天，可并行压缩到 3 天）")

h2(doc, "10.1 每天做什么（3 人并行版）")
table(doc, ["时间", "编程手 A（数据/图）", "编程手 B（模型/求解）", "建模手（方程/写作）"],
      [["D1 上午", "P1 重跑到数字一致", "—", "定稿方程与参数含义"],
       ["D1 下午", "P8 图表模板（字号/配色）", "P2 逐站标定跑通", "写 5.1—5.3 变量与假设"],
       ["D2", "P3 敏感性 + 出图", "P4 动态规划 + 路径表", "写任务一结果与解读"],
       ["D3", "P6 蒙特卡洛 + 出图", "P5 光伏敏感性 + 平衡点", "写任务二、三结果"],
       ["D4", "P7 情景 + P9 表格自动生成", "P10 复现包与自检", "写第七、八章与简报"],
       ["D5", "整篇图表核对（单位/图注）", "代码注释与异常处理", "全文逻辑与数字一致性复核"]],
      widths=[2.2, 4.8, 4.6, 4.4], font=8.0, cap="表 13  3 人并行的 5 天排期")

h2(doc, "10.2 编程手的四条纪律")
for t in ["**所有输出必须来自脚本，不能手改数字**。论文里的每个数都应能在 `model_results.json` 或 CSV 里找到；"
          "否则改一次参数就要重抄一遍全文，必然出错。",
          "**路径与编码统一**：脚本顶部集中配置 BASE 路径；CSV 一律 `encoding='utf-8-sig'`，"
          "否则 Excel 打开中文乱码、MATLAB 读入报错。",
          "**固定随机种子**：蒙特卡洛、标定的随机重启都要 `default_rng(seed)`，保证结果可复现、"
          "评委复算时不会得到不同答案。",
          "**图先丑后美**：先确认坐标轴、单位、图例正确，再调配色与字号；"
          "论文图 200 dpi 以上，单栏 8 cm、双栏 16 cm，字号不小于 8 pt。"]:
    bullet(doc, t)

h2(doc, "10.3 交付清单（编程手最终要交的东西）")
table(doc, ["类别", "文件", "说明"],
      [["代码", "01b_fetch_ndvi.py / 01_fetch_real_data.py / 02_crosscheck_power.py / preprocess.py / 03_modeling.py",
        "按编号顺序可完整复现"],
       ["数据", "数据/raw/*、数据/processed/*、数据/cache/", "原始、清洗后、缓存三层齐全"],
       ["结果", "model/model_results.json、fit_by_station.csv、sens_*.csv", "论文所有数字的唯一来源"],
       ["图", "图/fig1—fig13（PNG，200 dpi）", "预处理 8 张 + 建模 5 张"],
       ["文档", "数据来源与获取说明.docx、数据预处理报告.docx、建模报告.docx", "三份互引，数字一致"],
       ["自检", "run_all.py（一键重跑）+ README.md（三步上手）", "换机器能复现"]],
      widths=[2.4, 8.4, 4.8], font=8.2, cap="表 14  编程手交付清单")

doc.save(OUT)
print("saved:", OUT)
