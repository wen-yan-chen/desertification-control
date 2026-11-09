# -*- coding: utf-8 -*-
"""docx2tex.py —— 三份 docx 报告 → ctex/xelatex 可编译的 LaTeX"""
import os
import re
import shutil
import zipfile

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXDIR = os.path.join(BASE, "Reports")
FIGDIR = os.path.join(TEXDIR, "figs")

DOCS = [
    ("数据来源与获取说明.docx", "data_source", "数据来源与获取说明"),
    ("数据预处理报告.docx", "preprocess", "数据预处理报告"),
    ("建模报告.docx", "model", "建模报告"),
]

NS_M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
NS_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

MATH_SYM = {
    "π": r"{\pi}", "δ": r"{\delta}", "λ": r"{\lambda}", "κ": r"{\kappa}",
    "ρ": r"{\rho}", "ε": r"{\varepsilon}", "σ": r"{\sigma}", "θ": r"{\theta}",
    "α": r"{\alpha}", "β": r"{\beta}", "γ": r"{\gamma}", "μ": r"{\mu}",
    "Δ": r"{\Delta}", "Σ": r"{\sum}", "Ω": r"{\Omega}", "Φ": r"{\Phi}",
    "≤": r"{\le}", "≥": r"{\ge}", "×": r"{\times}", "±": r"{\pm}",
    "·": r"{\cdot}", "−": "-", "≈": r"{\approx}", "→": r"{\to}",
    "∞": r"{\infty}", "′": "'",
}
TEXT_SYM = {
    "²": r"$^{2}$", "³": r"$^{3}$", "⁻¹": r"$^{-1}$", "⁻²": r"$^{-2}$",
    "⁻³": r"$^{-3}$", "≤": r"$\le$", "≥": r"$\ge$", "×": r"$\times$",
    "·": r"$\cdot$", "≈": r"$\approx$", "→": r"$\to$", "±": r"$\pm$",
    "℃": r"$^{\circ}$C", "\u2003": " ", "\u2002": " ", "\u00a0": " ",
}


def _esc(s):
    out = []
    i = 0
    while i < len(s):
        pair = s[i:i + 2]
        if pair in TEXT_SYM:
            out.append(TEXT_SYM[pair])
            i += 2
            continue
        ch = s[i]
        i += 1
        if ch in TEXT_SYM:
            out.append(TEXT_SYM[ch])
        elif ch == "\\":
            out.append(r"\textbackslash{}")
        elif ch in "{}%&#_$":
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def _math_text(t):
    out = []
    for ch in t:
        if ch in MATH_SYM:
            out.append(MATH_SYM[ch])
        elif ch in "_%&#{}":
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def _child(el, tag):
    e = el.find(qn("m:" + tag))
    return e if e is not None else el


def _wrap(s):
    return "{" + s + "}" if (len(s) > 1 or re.search(r"[\\\s]", s)) else s


def omml_to_latex(el):
    tag = el.tag.split("}")[-1]
    if tag == "r":
        t = el.find(qn("m:t"))
        return _math_text(t.text or "") if t is not None else ""
    if tag == "t":
        return _math_text(el.text or "")
    if tag == "sSub":
        return _wrap(omml_to_latex(_child(el, "e"))) + "_{" + omml_to_latex(_child(el, "sub")) + "}"
    if tag == "sSup":
        return _wrap(omml_to_latex(_child(el, "e"))) + "^{" + omml_to_latex(_child(el, "sup")) + "}"
    if tag == "f":
        return "\\frac{" + omml_to_latex(_child(el, "num")) + "}{" + omml_to_latex(_child(el, "den")) + "}"
    if tag == "d":
        inner = "".join(omml_to_latex(c) for c in _child(el, "e"))
        pr = el.find(qn("m:dPr"))
        beg, end = "(", ")"
        if pr is not None:
            b, e = pr.find(qn("m:begChr")), pr.find(qn("m:endChr"))
            if b is not None:
                beg = b.get(qn("m:val"))
            if e is not None:
                end = e.get(qn("m:val"))
        if beg == "" and end == "":
            return inner
        bmap = {"{": r"\{", "}": r"\}", "|": "|"}
        return "\\left" + bmap.get(beg, beg) + inner + "\\right" + bmap.get(end, end)
    if tag == "func":
        name = omml_to_latex(_child(el, "fName")).strip()
        arg = omml_to_latex(_child(el, "e"))
        if name in ("max", "min", "ln", "lg", "exp", "sin", "cos", "tan"):
            return "\\" + name + "\\left(" + arg + "\\right)"
        return name + arg
    if tag == "limLow":
        return "\\underset{" + omml_to_latex(_child(el, "lim")) + "}{" + omml_to_latex(_child(el, "e")) + "}"
    return "".join(omml_to_latex(c) for c in el)


def para_inline(p_el):
    out = []
    for node in p_el.iterchildren():
        tag = node.tag
        if tag == NS_W + "r":
            txt = "".join(t.text or "" for t in node.iter(NS_W + "t"))
            if not txt:
                continue
            bEl = node.find(NS_W + "rPr/" + NS_W + "b")
            bold = bEl is not None and (bEl.get(NS_W + "val") not in ("0", "false"))
            t2 = _esc(txt)
            out.append("\\textbf{" + t2 + "}" if bold else t2)
        elif tag == NS_M + "oMath":
            out.append("$" + omml_to_latex(node) + "$")
        elif tag == NS_M + "oMathPara":
            out.append("$" + "".join(omml_to_latex(o) for o in node) + "$")
    return "".join(out)


def cell_text(cell):
    parts = [para_inline(p._p).strip() for p in cell.paragraphs]
    return " ".join(x for x in parts if x)


def table_latex(tbl):
    ncol = len(tbl.columns)
    rows = [[cell_text(c) for c in row.cells] for row in tbl.rows]
    if not rows:
        return ""
    spec = "|" + "|".join(["X"] * ncol) + "|"
    body = []
    for i, r in enumerate(rows):
        body.append(" & ".join(r) + r" \\\\")
        if i == 0:
            body.append("\\midrule")
    return ("\\begin{table}[H]\\centering\\small\\setlength{\\parskip}{2pt}\n"
            "\\begin{tabularx}{\\textwidth}{" + spec + "}\n\\toprule\n"
            + "\n".join(body) + "\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n")


def convert(docx_path):
    doc = Document(docx_path)
    media = []
    with zipfile.ZipFile(docx_path) as z:
        for n in sorted(z.namelist()):
            if n.startswith("word/media/"):
                dst = os.path.join(FIGDIR, os.path.basename(n))
                with z.open(n) as src, open(dst, "wb") as f:
                    shutil.copyfileobj(src, f)
                media.append(os.path.basename(n))
    mi = 0
    lines, started = [], False

    for child in doc.element.body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            p = Paragraph(child, doc)
            if child.findall(".//" + qn("a:blip")) and mi < len(media):
                lines.append("\\begin{figure}[H]\\centering\n"
                             "\\includegraphics[width=0.90\\textwidth]{figs/" + media[mi] + "}\n"
                             "\\end{figure}\n")
                mi += 1
                txt = para_inline(child).strip()
                if txt.startswith("图"):
                    lines.append("\\begin{center}\\small " + txt + "\\end{center}\n")
                continue

            sizes = [r.font.size.pt for r in p.runs if r.font.size]
            size = max(sizes) if sizes else 10.5
            bolds = [r.font.bold for r in p.runs if (r.text or "").strip()]
            inline = para_inline(child).strip()

            if not started:
                if "摘" in inline and size >= 13.5:
                    started = True
                else:
                    continue
            if not inline:
                continue

            plain = re.sub(r"\\textbf\{([^{}]*)\}", r"\1", inline)
            if size >= 20:
                continue
            if size >= 13.5:
                lines.append("\n\\section*{" + plain + "}\n")
            elif size >= 11.0 and bolds and all(bolds):
                lines.append("\n\\subsection*{" + plain + "}\n")
            else:
                lines.append(inline + "\n\n")
        elif tag == "tbl":
            lines.append("\n" + table_latex(Table(child, doc)))
    return "".join(lines)


PREAMBLE = r"""\documentclass[11pt,a4paper]{ctexart}
\usepackage[margin=2.2cm]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs,tabularx}
\usepackage{float}
\usepackage{caption}
\usepackage{hyperref}
\hypersetup{colorlinks=true,linkcolor=blue,urlcolor=blue}
\setlength{\parindent}{2em}
\setlength{\parskip}{0.3em}
\renewcommand{\arraystretch}{1.12}
\captionsetup{font=small}
\title{%s}
\author{CQU\_MCM 2026 · 建模小组}
\date{2026-11-09}
\begin{document}
\maketitle
\thispagestyle{empty}
\newpage
"""


def main():
    os.makedirs(FIGDIR, exist_ok=True)
    for name, stem, title in DOCS:
        src = os.path.join(TEXDIR, name)
        if not os.path.exists(src):
            print("missing:", src)
            continue
        content = convert(src)
        tex = PREAMBLE % title + content + "\n\\end{document}\n"
        with open(os.path.join(TEXDIR, stem + ".tex"), "w", encoding="utf-8") as f:
            f.write(tex)
        print("wrote", stem + ".tex", len(tex))


if __name__ == "__main__":
    main()
