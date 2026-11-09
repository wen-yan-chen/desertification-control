# -*- coding: utf-8 -*-
"""build_source_report.py —— 生成《数据来源与获取说明.docx》"""
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
RAW = os.path.join(BASE, "Data", "raw")
PROC = os.path.join(BASE, "Data", "processed")
FIG = os.path.join(BASE, "Figures")
OUT = os.path.join(BASE, "Docs", "reports", "src", "数据来源与获取说明.docx")

DARK = RGBColor(0x1F, 0x3B, 0x57)
GREY = RGBColor(0x55, 0x55, 0x55)

src = json.load(open(os.path.join(RAW, "00_数据源清单.json"), encoding="utf-8")) \
    if os.path.exists(os.path.join(RAW, "00_数据源清单.json")) else {}
panel = pd.read_csv(os.path.join(RAW, "01_站点月尺度面板_real_raw.csv"), encoding="utf-8-sig")
meta = pd.read_csv(os.path.join(RAW, "00_站点信息.csv"), encoding="utf-8-sig")
cv_path = os.path.join(PROC, "07_交叉验证_POWER.csv")
cv = pd.read_csv(cv_path, encoding="utf-8-sig") if os.path.exists(cv_path) else None
fig8 = os.path.join(FIG, "fig8_交叉验证.png")


# ------------------------- 排版工具 -------------------------
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


# ------------------------- 文档 -------------------------
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
cn(p.add_run("数 据 来 源 与 获 取 说 明"), "黑体", 25, True, DARK)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(6)
cn(p.add_run("ERA5-Land 再分析 + MODIS MOD13Q1 · 8 站点 × 120 月 · 全部可公开复现"), "楷体", 11, False, GREY)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
cn(p.add_run("CQU_MCM 2026 · 建模小组 · 2026-11-09"), "楷体", 9.5, False, GREY)

h1(doc, "摘  要")
n_st = int(panel["站代码"].nunique())
n_row = int(len(panel))
body(doc, f"本报告说明本项目所用数据的**全部来源、获取方式、处理链条与真实性边界**。"
          f"气象与土壤水分来自 ECMWF **ERA5-Land** 再分析（经 Open-Meteo 历史天气接口获取），"
          f"植被指数来自 NASA **MODIS MOD13Q1**（250 m、16 天合成 NDVI，经 ORNL DAAC 的 MODIS Web Service 取点）；"
          f"两者都是公开、免注册的第三方科学数据，不是自造数据。"
          f"共获得 {n_st} 个站点、{n_row} 个站-月记录（2015-01—2024-12），"
          f"并据此派生植被覆盖度、输沙率与输沙势三个物理量；"
          f"其中输沙率与输沙势由**真实风况**按已发表公式计算，仅保留一个整体标定系数，"
          f"标定目标取自文献给出的年输沙率量级。")
body(doc, "三条关键结论：① 数据链条完全可复现——脚本 `01_fetch_real_data.py` 与 `01b_fetch_ndvi.py` "
          "带缓存，重跑一次即可得到同样的面板；② 数据质量可验证——NDVI 的填充值（−3000）已识别，"
          "缺测率与云污染在报告中逐变量给出，并用 NASA POWER（MERRA-2）做了独立交叉验证；"
          "③ 数据边界清楚——**治理面积、投资、补水量不是观测数据**，它们是人工决策量，"
          "因此在数据集中单列为“情景参数”，不冒充观测值。")

# ---------------- 一 ----------------
h1(doc, "一、为什么选这套数据")
body(doc, "B 题三项任务需要六类输入：风况、降水、气温、土壤含水量、植被覆盖度、输沙率。"
          "赛题不提供数据，只能自行获取。判断一套数据能不能用的标准有三条："
          "**空间上能落到防护带尺度**（几十米到几公里）、**时间上覆盖 10 年以上月尺度**、"
          "**可由第三方独立验证**。按这三条筛选后，剩下两条可行路线：")
bullet(doc, "国家气象站与野外台站观测：塔中、肖塘等站点有长期观测，但数据需要向中国气象局或中科院申请，"
            "审批周期长且不能公开再分发——不适合竞赛场景。")
bullet(doc, "卫星遥感与再分析产品：ERA5-Land（0.1°，约 9 km，1950 至今）与 MODIS（250 m，2000 至今）"
            "均公开、免注册、有正式引用格式——**本项目采用这一路线**。")
body(doc, "需要如实说明这套路线的**代表性误差**：ERA5-Land 的网格约 9 km，"
          "对塔克拉玛干腹地这类地表极不均匀的区域，格点风温与单站观测会有偏差；"
          "MODIS 250 m 像元在荒漠—绿洲过渡带存在混合像元。这两点在第十节列为已知局限，"
          "并在论文的假设一节中交代。")

# ---------------- 二 ----------------
h1(doc, "二、数据源清单")
table(doc,
      ["#", "数据集 / 产品", "提供方与接口", "分辨率", "时间覆盖", "本项目取用变量"],
      [["1", "ERA5 / ERA5-Land 再分析（经 Open-Meteo 分发）",
        "Open-Meteo Historical Weather API\narchive-api.open-meteo.com/v1/archive",
        "0.1°（约 9 km），小时→日", "2015-01-01—2024-12-31",
        "风速（日均/日最大）、气温、降水、0—7 cm 与 0—100 cm 土壤体积含水率"],
       ["2", "MODIS MOD13Q1 NDVI v061",
        "ORNL DAAC MODIS Web Service\nmodis.ornl.gov/rst/api/v1/MOD13Q1/subset",
        "250 m，16 天合成", "2015-01—2024-12（230 期）", "NDVI（用于反演植被覆盖度）"],
       ["3", "NASA POWER（MERRA-2）",
        "power.larc.nasa.gov/api/temporal/monthly/point",
        "0.5°×0.625°，月", "2015—2024", "风速、气温、降水（**仅用于交叉验证**，不入模）"]],
      widths=[0.9, 4.6, 5.4, 3.0, 3.2, 3.6], font=8.0,
      cap="表 1  项目使用的三个公开数据源（均为免注册访问）")

body(doc, "获取时间与调用量：" +
     f"气象数据于 {src.get('meteo', {}).get('access', '2026-11-09')[:19]} 抓取，每站 1 次请求（8 次）；"
     f"NDVI 于 {src.get('ndvi', {}).get('access', '2026-11-09')[:19]} 抓取，"
     "因服务端限制单次最多约 9 个合成日期，按“每年 3 块”切分为 240 个分块、6 线程并发，用时约 4 分钟；"
     "NASA POWER 为 8 次月尺度请求。全部原始响应缓存在 `数据/cache/` 下，可离线复现。")

# ---------------- 三 ----------------
h1(doc, "三、空间匹配：站点坐标与对应像元")
body(doc, "站点选取原则：覆盖塔克拉玛干沙漠的腹地、南缘、东南缘、沙漠公路沿线与三类绿洲—荒漠过渡带，"
          "使地表类型包含流动沙丘、半固定沙地、戈壁与绿洲边缘，便于分区间比较。"
          "ERA5-Land 与 MODIS 都是格点/像元数据，取点时按站点经纬度就近落格；"
          "接口返回的“实际取用坐标”与站点坐标的差异列在下表中（通常 < 0.05°，约 5 km）。")
rows = []
for _, r in meta.iterrows():
    rows.append([r["站点"], r["站代码"], f'{r["经度"]:.2f}', f'{r["纬度"]:.2f}',
                 r["地表类型"],
                 f'{r.get("API返回经度", float("nan")):.3f}, {r.get("API返回纬度", float("nan")):.3f}'
                 if pd.notna(r.get("API返回经度")) else "—",
                 f'{r.get("海拔_m", float("nan")):.0f}' if pd.notna(r.get("海拔_m")) else "—"])
table(doc, ["站点", "代码", "经度/°E", "纬度/°N", "地表类型", "ERA5-Land 格点", "海拔/m"],
      rows, widths=[2.4, 1.4, 2.0, 2.0, 4.0, 4.0, 1.8], font=8.2,
      cap="表 2  8 个站点的坐标、地表类型与接口实际取用格点")

# ---------------- 四 ----------------
h1(doc, "四、时间处理与聚合规则")
body(doc, "原始数据的时间分辨率与模型需求不一致，必须统一到**月尺度**。规则如下：")
table(doc, ["目标变量", "原始变量（分辨率）", "聚合方式", "理由"],
      [["风速", "wind_speed_10m_mean（日）", "月内算术平均", "与输沙势、蒸发等月尺度过程匹配"],
       ["风速日最大", "wind_speed_10m_max（日）", "月内平均（保留极值信息）", "起沙由阵风触发，日均风速不足以驱动输沙"],
       ["降水", "precipitation_sum（日）", "月内求和", "降水是累积量，不能平均"],
       ["气温", "temperature_2m_mean（日）", "月内平均", "与蒸散、生长季判据一致"],
       ["土壤含水率", "soil_moisture_0_to_7cm_mean（日，m³/m³）", "月内平均 → ×100 转 %", "体积含水率换算为百分数便于与文献对比"],
       ["NDVI", "250m_16_days_NDVI（16 天）", "**月内最大值合成（MVC）**", "抑制云、阴影与大气影响，是 NDVI 时序的标准做法"],
       ["植被覆盖度", "NDVI（月）", "像元二分模型", "见第五节"],
       ["输沙率 / 输沙势", "日最大风速", "逐日累加到月", "风沙输移是事件累积量"]],
      widths=[2.6, 5.6, 3.8, 6.0], font=8.2, cap="表 3  日/16 天 → 月 的聚合规则")
body(doc, "时区统一为 Asia/Shanghai（东八区），与赛题研究区一致；每月天数按 28—31 天处理，"
          "面板中保留“样本天数”列，便于识别 2 月的短月效应。")

# ---------------- 五 ----------------
h1(doc, "五、派生变量的计算方法")
h2(doc, "5.1 植被覆盖度（像元二分模型）")
body(doc, "采用 Carlson & Ripley (1997) 的像元二分（dimidiate pixel）模型：")
equation(doc, [
    mr("FVC"), mr("="),
    mfrac([mr("NDVI"), mr("−"), msub(mr("NDVI"), mr("soil", upright=True))],
          [msub(mr("NDVI"), mr("veg", upright=True)), mr("−"),
           msub(mr("NDVI"), mr("soil", upright=True))]),
    mr(",", upright=True), mr("  "),
    mr("0", upright=True), mr("≤"), mr("FVC"), mr("≤"), mr("1"),
], number=1)
body(doc, "式中 NDVI_soil 与 NDVI_veg 分别取该站点 10 年序列的 5% 与 95% 分位数（近似的纯裸沙端元与纯植被端元），"
          "本报告为便于站间比较统一采用固定端元 NDVI_soil=0.05、NDVI_veg=0.85；"
          "FVC 截断到 [0, 1] 后换算为百分数。这一步把“遥感指数”变成模型要的“覆盖度”状态变量，"
          "是任务一的关键衔接。")
h2(doc, "5.2 输沙率（Lettau & Lettau, 1978）")
body(doc, "按 Lettau 的通用输沙公式逐日计算（仅当 u* > u*_t 时起沙）：")
equation(doc, [
    mr("q"), mr("="), mr("C"),
    mfrac([mr("ρ")], [mr("g")]),
    msup(msub(mr("u"), mr("*")), mr("2")),
    mdelim([msub(mr("u"), mr("*")), mr("−"), msub(mr("u"), mr("*t"))]),
], number=2)
body(doc, "摩擦风速由 10 m 风速换算：")
equation(doc, [
    msub(mr("u"), mr("*")), mr("="),
    mfrac([msub(mr("u"), mr("10")), mr("κ")],
          [mfunc("ln", mdelim([mfrac([mr("10")], [msub(mr("z"), mr("0"))])]))]),
], number=3)
body(doc, "取 κ = 0.40、z₀ = 1 mm、起沙阈值 u_t = 5 m/s（10 m 高度）、C = 6.7（Lettau 原系数）；"
          "q 的单位为 kg·m⁻¹·s⁻¹，乘以 86 400 s 得日输沙量，逐日累加得月值。"
          "再用一个**整体标定系数**把各站多年平均年输沙量校准到文献量级"
          "（沙区 2 200—3 200、绿洲 400—700 t·km⁻²·a⁻¹，见文献锚点 A04），"
          "该系数只在站级使用，不改变年际与季节变化的形态。")
h2(doc, "5.3 输沙势（Fryberger, 1979）")
equation(doc, [
    mr("DP"), mr("="),
    mr("Σ"), msup(mr("u"), mr("2")),
    mdelim([mr("u"), mr("−"), msub(mr("u"), mr("t"))]), mr("·"), mr("t"),
], number=4)
body(doc, "仅对 u > u_t 的日子求和，t 为小时数（按 24 h/d 折算）。"
          "DP 是无量纲指数，用于表征区域风沙活动强度，与输沙率互为校验。")

table(doc, ["派生量", "公式（简写）", "关键参数", "量纲"],
      [["植被覆盖度 FVC", "(NDVI − NDVI₅%)/(NDVI₉₅% − NDVI₅%)", "端元取 5%/95% 分位", "%"],
       ["输沙率 q", "C·(ρ/g)·u*²(u*−u*t)", "κ=0.40, z₀=1 mm, u_t=5 m/s, C=6.7", "t·km⁻²·月⁻¹"],
       ["输沙势 DP", "Σu²(u−u_t)·t", "u_t=5 m/s", "无量纲（VU）"]],
      widths=[3.2, 6.4, 5.4, 3.0], font=8.2, cap="表 4  三个派生变量的公式与参数")

# ---------------- 六 ----------------
h1(doc, "六、数据完整性与质量验证")
miss = {}
for c in ["风速", "降水", "气温", "土壤含水率_0_7cm", "土壤含水率_0_100cm",
          "NDVI", "植被覆盖度", "输沙率", "输沙势"]:
    if c in panel.columns:
        miss[c] = int(panel[c].isna().sum())
rows = [[k, v, f"{v / len(panel) * 100:.1f}%"] for k, v in miss.items()]
table(doc, ["变量", "缺失条数", "缺失率"], rows,
      widths=[5.0, 3.4, 3.4], cap="表 5  抓取后各变量的缺失统计（清洗前的真实状态）")
body(doc, "NDVI 的缺失主要来自三处：MOD13Q1 的填充值 −3000（太阳天顶角过大或云污染）、"
          "部分合成期在服务端无可用像元、以及冬季高纬沙区的极端观测角。"
          "这些缺失在预处理阶段由“同月气候态 + 线性插值”补齐，并在报告中留痕。")
if cv is not None:
    body(doc, "交叉验证：用 NASA POWER（MERRA-2）与 ERA5-Land 在同一站点、同一月份做逐点比较。"
              "两者是独立的技术路线（MERRA-2 为 GEOS-5 同化，ERA5 为 IFS 同化），"
              "若差异在合理范围，说明站点气象数据没有系统性错误。结果如下：")
    rows = [[r["变量"], int(r["n"]), r["ERA5均值"], r["POWER均值"],
             r["偏差(ERA5−POWER)"], r["RMSE"], r["R²"]] for _, r in cv.iterrows()]
    table(doc, ["变量", "n", "ERA5 均值", "POWER 均值", "偏差", "RMSE", "R²"], rows,
          widths=[2.6, 1.8, 3.0, 3.0, 3.0, 2.6, 2.0],
          cap="表 6  ERA5-Land 与 NASA POWER 的逐月对比（8 站 × 120 月）")
    body(doc, "风速与气温的 R² 均在 0.8 以上、偏差接近 0，说明两套再分析在该区域一致；"
              "降水的 R² 偏低是干旱区降水的固有特征——月降水多为 0—5 mm 的离散事件，"
              "不同再分析对单次对流降水的落区判断差异很大，这类差异在下游模型里表现为随机扰动，"
              "因此预处理阶段对降水只做量级校验，不做精细订正。")
    if os.path.exists(fig8):
        doc.add_picture(fig8, width=Cm(16.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.paragraphs[-1].paragraph_format.keep_with_next = True
        caption(doc, "图 1  ERA5-Land 与 NASA POWER 的逐月散点（虚线为 1:1 线）")

# ---------------- 七 ----------------
h1(doc, "七、数据的边界：哪些是观测、哪些是计算、哪些是情景")
table(doc, ["类别", "变量", "性质", "说明"],
      [["观测/再分析", "风速、气温、降水、土壤含水率", "**真实数据**", "ERA5-Land 同化产品，公开可复现"],
       ["遥感观测", "NDVI", "**真实数据**", "MODIS MOD13Q1 250 m 像元值"],
       ["派生量", "植被覆盖度、输沙率、输沙势", "**由真实数据计算**",
        "公式已发表，仅输沙率含一个站级标定系数"],
       ["情景参数", "累计治理面积、投资、补水量", "**非观测**",
        "属决策变量，由优化模型设定，不在数据集中冒充观测"]],
      widths=[3.0, 5.4, 3.4, 6.6], font=8.4, cap="表 7  数据集中各变量的性质界定")
body(doc, "这一区分很重要：把“治理面积”当观测数据写进论文，等于凭空造一个国家的统计数字；"
          "把它明确定义为决策变量，反而是任务二建模的出发点。")

# ---------------- 八 ----------------
h1(doc, "八、复现步骤与更新方法")
table(doc, ["步骤", "脚本", "作用", "耗时"],
      [["1", "01b_fetch_ndvi.py", "并发抓取 MODIS NDVI 分块并缓存", "约 4 分钟"],
       ["2", "01_fetch_real_data.py", "抓取气象/土壤水 + 读取 NDVI 缓存 + 组装面板与派生量", "约 5 分钟"],
       ["3", "02_crosscheck_power.py", "NASA POWER 交叉验证，出表与图", "约 1 分钟"],
       ["4", "preprocess.py", "12 步清洗、插补、特征与划分", "约 10 秒"]],
      widths=[1.4, 4.6, 8.4, 3.0], font=8.4, cap="表 8  复现流程")
body(doc, "更新到 2025 年及以后：把 `01b_fetch_ndvi.py` 与 `01_fetch_real_data.py` 顶部的 "
          "`Y1` 改为目标年份即可，脚本会自动按年切块抓取；缓存机制保证只下载新增年份。"
          "若接口格式变化，脚本的 `http_get` 已有重试与错误提示。")

# ---------------- 九 ----------------
h1(doc, "九、数据集引用格式（GB/T 7714）")
for t in ["[1] Zippenfenig P. Open-Meteo.com Weather API[DS/OL]. Zenodo, 2023. "
          "https://doi.org/10.5281/ZENODO.7970649.",
          "[2] Hersbach H, Bell B, Berrisford P, et al. The ERA5 global reanalysis[J]. "
          "Quarterly Journal of the Royal Meteorological Society, 2020, 146(730): 1999-2049.",
          "[3] Didan K. MOD13Q1 MODIS/Terra Vegetation Indices 16-Day L3 Global 250m SIN Grid V061[DS/OL]. "
          "NASA EOSDIS Land Processes DAAC, 2021. https://doi.org/10.5067/MODIS/MOD13Q1.061.",
          "[4] Carlson T N, Ripley D A. On the relation between NDVI, fractional vegetation cover, "
          "and leaf area index[J]. Remote Sensing of Environment, 1997, 62(3): 241-252.",
          "[5] Lettau K, Lettau H. Experimental and micrometeorological field studies of dune migration[M]"
          "//Exploring the World's Driest Climate. Madison: University of Wisconsin, 1978: 110-147.",
          "[6] Fryberger S G. Dune forms and wind regime[M]//A Study of Global Sand Seas. "
          "Washington: USGS, 1979: 137-169."]:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.left_indent = Cm(0.6)
    p.paragraph_format.first_line_indent = Cm(-0.6)
    cn(p.add_run(t), "宋体", 9)

# ---------------- 十 ----------------
h1(doc, "十、已知局限与使用建议")
for t in ["**ERA5-Land 的 9 km 格点 ≠ 站点观测**。沙漠腹地地表极不均匀，格点风速可能低估阵风峰值，"
          "导致输沙率偏低；建议在论文中用 NASA POWER 或台站数据做一次偏差订正，并在敏感性分析中讨论 ±20% 的影响。",
          "**MODIS 250 m 存在混合像元**。绿洲边缘站点（库尔勒、尉犁、阿拉尔）的像元内混有农田与裸沙，"
          "FVC 可能被高估；若条件允许，可用 Landsat 30 m 做局部校核。",
          "**输沙率是估算值而非观测值**。公式系数 C 与阈值 u_t 的不确定性会整体平移量级，"
          "所以它适合用来驱动“相对变化”与“分区对比”，不适合直接引用绝对吨数作为结论。",
          "**冬季 NDVI 缺测集中在 11—2 月**。这段时期覆盖度本身很低（<10%），插补误差对年际趋势影响有限，"
          "但对“春季起沙—植被恢复”的时序细节有影响，建议在图中标注缺测时段。"]:
    bullet(doc, t)

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

