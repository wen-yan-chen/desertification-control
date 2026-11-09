# -*- coding: utf-8 -*-
"""
omml_utils.py —— 生成 Word 原生公式（OMML）
提供两类能力：
  1) 结构化拼装：mr / msub / msup / mfrac / mdelim / mfunc / mlimit + equation()
  2) 行内公式：在正文里用 $...$ 包裹简化的 LaTeX 片段（支持 _ ^ \\frac \\max \\sum
     希腊字母、\\Delta、\\cdot、\\times、\\le、\\ge、\\pm、\\bar、\\hat、\\text 等），
     rich_math() 会自动切成“文字—公式—文字”渲染。
"""
import re

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt


def _m(tag):
    return OxmlElement(f"m:{tag}")


def mr(text, upright=False, size=None):
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


def mlimit(base, lim):
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


# ------------------------------------------------------------------
# 简化的 LaTeX 子集 → OMML
# ------------------------------------------------------------------
GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε",
    "zeta": "ζ", "eta": "η", "theta": "θ", "lambda": "λ", "mu": "μ",
    "nu": "ν", "xi": "ξ", "pi": "π", "rho": "ρ", "sigma": "σ", "tau": "τ",
    "phi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω",
    "Delta": "Δ", "Sigma": "Σ", "Omega": "Ω", "Phi": "Φ",
}
SYMBOL = {
    "cdot": "·", "times": "×", "pm": "±", "le": "≤", "ge": "≥", "ne": "≠",
    "approx": "≈", "to": "→", "infty": "∞", "sum": "Σ", "prod": "∏",
    "partial": "∂", "prime": "′", "ldots": "…", "quad": "\u2003",
    "lbrace": "{", "rbrace": "}", "textasciitilde": "~",
}
FUNCS = {"max", "min", "ln", "lg", "sin", "cos", "tan", "exp", "lim"}


class _Parser:
    def __init__(self, s):
        self.s = s
        self.i = 0

    def peek(self):
        return self.s[self.i] if self.i < len(self.s) else ""

    def parse(self, stop=None):
        """解析直到遇到 stop 字符（不消耗）"""
        items = []
        while self.i < len(self.s):
            c = self.s[self.i]
            if stop and c == stop:
                break
            if c == "\\":
                node = self.command()
            elif c in "_^":
                self.i += 1
                arg = self.atom()
                if items:
                    base = items.pop()
                else:
                    base = mr("□")
                items.append(msub(base, arg) if c == "_" else msup(base, arg))
                continue
            elif c == "{":
                self.i += 1
                sub = self.parse("}")
                self.i += 1
                items.append(mdelim(sub, "", ""))
                continue
            elif c == " ":
                self.i += 1
                if items:
                    items.append(mr(" "))
                continue
            else:
                node = mr(c)
                self.i += 1
            items.append(node)
        return items

    def atom(self):
        """取一个“原子”作为上下标的内容：{...} 或单字符/命令"""
        c = self.peek()
        if c == "{":
            self.i += 1
            sub = self.parse("}")
            self.i += 1
            return mdelim(sub, "", "")
        if c == "\\":
            return [self.command()]
        self.i += 1
        return mr(c)

    def command(self):
        self.i += 1  # 跳过反斜杠
        m = re.match(r"[A-Za-z]+", self.s[self.i:])
        name = m.group(0) if m else ""
        self.i += len(name)
        if name in ("frac", "dfrac", "tfrac"):
            num = self.brace()
            den = self.brace()
            return mfrac(num, den)
        if name == "text":
            return mr("".join(self.brace_text()), upright=True)
        if name in GREEK:
            return mr(GREEK[name])
        if name in SYMBOL:
            return mr(SYMBOL[name], upright=(name in ("sum", "prod")))
        if name in FUNCS:
            arg = self.brace()
            return mfunc(name, arg)
        if name == "bar":
            return mr("̄")   # 组合上划线，附在前一字符上
        if name == "hat":
            return mr("̂")
        if name in ("left", "right"):
            return mr("")
        if name == ",":
            return mr("\u2009")
        if name == "%":
            return mr("%")
        return mr(name)

    def brace(self):
        while self.peek() == " ":
            self.i += 1
        if self.peek() == "{":
            self.i += 1
            body = self.parse("}")
            self.i += 1
            return body
        return self.atom()

    def brace_text(self):
        if self.peek() == "{":
            self.i += 1
            start = self.i
            depth = 1
            while self.i < len(self.s):
                if self.s[self.i] == "{":
                    depth += 1
                elif self.s[self.i] == "}":
                    depth -= 1
                    if depth == 0:
                        txt = self.s[start:self.i]
                        self.i += 1
                        return [txt]
                self.i += 1
        return [""]


def parse_math(expr):
    """把 $...$ 内的简化 LaTeX 转成 OMML 元素列表"""
    return _Parser(expr).parse()


def math_run(paragraph, parts):
    om = OxmlElement("m:oMath")
    for x in (parts if isinstance(parts, list) else [parts]):
        om.append(x)
    paragraph._p.append(om)


# ------------------------------------------------------------------
# 文本里的常见符号 → 行内公式（自动包裹 $..$）
# ------------------------------------------------------------------
SYMBOLS = [
    (re.compile(r"V\*"), lambda m: "$V^*$"),
    (re.compile(r"R²"), lambda m: "$R^2$"),
    (re.compile(r"W_h"), lambda m: "$W_h$"),
    (re.compile(r"(?<![A-Za-z0-9])([VWTPQA])_t(?![A-Za-z0-9])"),
     lambda m: "$%s_t$" % m.group(1)),
    (re.compile(r"a₁"), lambda m: "$a_1$"),
    (re.compile(r"a₂"), lambda m: "$a_2$"),
    (re.compile(r"(s_[VW][12])"), lambda m: "$%s$" % m.group(1)),
    (re.compile(r"u\*"), lambda m: "$u_*$"),
    (re.compile(r"FVC"), lambda m: "$" + chr(92) + "mathrm{FVC}$"),
    (re.compile(r"NDVI_soil"), lambda m: "$" + chr(92) + "mathrm{NDVI}_{soil}$"),
    (re.compile(r"NDVI_veg"), lambda m: "$" + chr(92) + "mathrm{NDVI}_{veg}$"),
    (re.compile(r"S_[VW]" + r"\(m\)"), lambda m: "{%s}(m)$" % m.group(0)[2]),
    (re.compile(r"S_[VW]"), lambda m: "{%s}$" % m.group(0)[2]),
    (re.compile("λ"), lambda m: "$" + chr(92) + "lambda$"),
    (re.compile("κ"), lambda m: "$" + chr(92) + "kappa$"),
    (re.compile("ρ"), lambda m: "$" + chr(92) + "rho$"),
    (re.compile("ε"), lambda m: "$" + chr(92) + "varepsilon$"),
]

_PH = "\uFFF0"


def symbolize(text):
    """把常见符号包成 $..$；已有 $..$ 片段先保护起来，避免嵌套"""
    text = str(text)
    parts = MATH_RE.split(text)
    out = []
    for i, seg in enumerate(parts):
        if i % 2 == 1:                 # 原本就是公式
            out.append("$" + seg + "$")
            continue
        for pat, fn in SYMBOLS:
            seg = pat.sub(fn, seg)
        out.append(seg)
    return "".join(out)


MATH_RE = re.compile(r"\$(.+?)\$", re.S)
BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.S)


def rich_math(paragraph, text, font_name="宋体", size=10.5, color=None, bold_all=False):
    """把含 $..$ 与 **加粗** 的文本渲染到段落：$..$ 走 OMML，**..** 走粗体"""
    text = str(text).replace("`", "")
    text = symbolize(text)
    # 先按 $..$ 切，保留公式段
    pos = 0
    for m in MATH_RE.finditer(text):
        _emit_text(paragraph, text[pos:m.start()], font_name, size, color, bold_all)
        try:
            parts = parse_math(m.group(1))
            math_run(paragraph, parts)
        except Exception:
            _emit_text(paragraph, m.group(1), font_name, size, color, bold_all)
        pos = m.end()
    _emit_text(paragraph, text[pos:], font_name, size, color, bold_all)


def _emit_text(paragraph, text, font_name, size, color, bold_all):
    if not text:
        return
    # 处理 ** 粗体
    for i, seg in enumerate(text.split("**")):
        if not seg:
            continue
        run = paragraph.add_run(seg)
        run.font.size = Pt(size)
        run.font.bold = bold_all or (i % 2 == 1)
        run.font.name = font_name
        run._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)
        if color:
            run.font.color.rgb = color


def equation(doc, parts, number=None, size=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    math_run(p, parts)
    if size:
        for r in p._p.iter(qn("m:r")):
            if r.find(qn("w:rPr")) is not None:
                continue
            wr = OxmlElement("w:rPr")
            sz = OxmlElement("w:sz")
            sz.set(qn("w:val"), str(int(size * 2)))
            wr.append(sz)
            t = r.find(qn("m:t"))
            if t is not None:
                r.insert(list(r).index(t), wr)
    if number is not None:
        run = p.add_run(f"\u2003\u2003（{number}）")
        run.font.size = Pt(10)
        run.font.name = "宋体"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    return p
