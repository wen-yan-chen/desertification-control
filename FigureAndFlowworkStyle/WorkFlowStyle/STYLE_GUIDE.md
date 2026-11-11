# Workflow figure style guide

How to turn modeling content into a figure that matches the PowerPoint templates
in this folder (`数学建模论文流程图1–6.pptx`). Everything is TikZ, defined in
[mcmworkflow.sty](mcmworkflow.sty). Working reproductions are in [examples/](examples/).

| Template | Look | Example |
|---|---|---|
| 1, 3, 5, 6 | Problem grid: dashed panels, flat boxes, bold-italic Times | [problem_grid.tex](examples/problem_grid.tex) |
| 2 | Rounded outline: white rounded boxes, green accents, block arrows | [rounded_outline.tex](examples/rounded_outline.tex) |
| 4 | Fishbone: causes feeding stages that lead to a result | [fishbone.tex](examples/fishbone.tex) |

## 1. Choose the layout from the content

- **Several sub-problems that feed each other** → problem grid (default for "Our work").
  2×2 for four problems; 1×3 or 2×2 with one wide panel for three.
- **One evaluation pipeline with stages and a final strategy list** → rounded outline.
- **Factors converging on one outcome** (e.g. drivers of desertification) → fishbone.

## 2. Problem grid rules (`wf ...` styles)

**Panels.** One panel per problem, `\wfpanelat[above|below]{slot}{name}{(x0,y0)}{(x1,y1)}{Problem1:}`.
Each problem gets its own slot A–D so the panels differ slightly in hue. Top-row
titles go above, bottom-row titles go below. Panels 8 cm × ~4.9 cm, 1.2 cm gaps,
so the whole figure is ~17 cm wide and fits `\linewidth`.

**Box roles.** Every box gets exactly one role. Color carries meaning, so do not
mix roles for decoration.

| Content | Style | Look |
|---|---|---|
| Named model (ARIMA, LSTM, AHP) | `wf model` | strong theme color, white text |
| Headline result of a problem | `wf key` | darkest color, white text — one per panel at most |
| Result of a panel | `wf output=X` | slot dark, white text |
| Secondary result | `wf aux` | grey `#767171`, white text |
| Method step / intermediate | `wf mid=X` | slot mid tint, black text |
| Input data, factors | `wf input=X` | slot light tint, black text |
| Small attribute tags | `wf chip=X`, wrapped in `wf group` | tiny light boxes in a dashed set |
| Free label | `wf plain` | text only |
| Method name or remark without a box | `wf note=X` | italic text in slot color |

**Connectors.**

| Meaning | Style |
|---|---|
| Main flow inside a panel | `wf arrow` (thin black, triangle head) |
| Flow within a slot's colored family | `wf link=X` |
| Weak or derived relation | `wf soft=X` (dashed, colored) |
| One-to-many / many-to-one split | `wf branch` / `wf branch c=X` (no head) |
| Panel to panel | `wf pass` (theme link color); last step into the final panel `wf thick arrow` |

**Text.** Bold italic Times. Box text `\small`, model names `\normalsize`,
panel titles `\Large`. Use `text width=` for anything over ~4 words; wrapping is
on and hyphenation is off. Write short phrases, not sentences.

**Themes.** `\wftheme{green|slate|vivid|indigo}` (templates 1/3/5/6). Default
green. Slate or indigo print best in grayscale; vivid is loud — avoid for the paper.

## 3. Rounded outline rules (`wfo ...` styles)

- Group stages in `wfo container` (grey dashed, rounded); wrap all in `wfo frame`.
- Section header: `wfo head` overlapping the container's top edge.
- Plain items: `wfo box`. The one key method per section: `wfo method` (green text).
- Between sections: `wfo big arrow` (solid green) for the main path,
  `wfo hollow arrow` for the secondary path.
- Ordered lists of strategies: a `wfo gradient` panel. Put labels on it in
  `wfoTextDark`, never `wfoText`, so they stay readable on the green.

## 4. Fishbone rules (`wf bone`, `wf rib`, `wf joint`)

Each stage is a joint circle with up to four ribs (two above, two below). Keep
rib labels to 1–3 words. Space joints ≥ 4 cm apart so labels clear the bones.
Joint fills go dark → light (`wfJointA`, `B`, `C`) toward the result.

## 5. Clarity checks before delivering

1. Render to PNG (`pdftoppm -png -r 110 -singlefile fig.pdf fig`) and look at it.
2. No text leaves its box; no two boxes overlap; no label sits on a line.
3. White text only on `model`, `key`, `output`, `aux`. Black text on everything lighter.
4. Every arrow means "feeds into". Remove decorative arrows.
5. Panels align on one grid; equal gaps.

## 6. Making a figure for the paper

```latex
% Paper/Figure/workflow.tex
\documentclass[tikz,border=2pt]{standalone}
\usepackage{newtxtext}
\usepackage{../../FigureAndFlowworkStyle/WorkFlowStyle/mcmworkflow}
\begin{document}
\wftheme{green}
\begin{tikzpicture}
  ... nodes at explicit coordinates, then \wfpanelat ..., then \wfpagebg
\end{tikzpicture}
\end{document}
```

Build with `pdflatex workflow.tex` inside `Paper/Figure/`, then in `main.tex`:
`\includegraphics[width=\linewidth]{Figure/workflow.pdf}`.
