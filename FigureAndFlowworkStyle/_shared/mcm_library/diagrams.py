"""Paper workflows that explain stages and the outputs handed between them."""

from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch
from matplotlib.path import Path as MplPath

from mcm_style import palette as P
from mcm_style.components import arrow, box, canvas, label, panel, sheet, stage
from mcm_style.typography import PAGE_WIDTH


@dataclass(frozen=True)
class Stage:
    title: str
    detail: str
    evidence_title: str
    evidence_detail: str
    color: str


@dataclass(frozen=True)
class CardStage:
    """One model column in :func:`research_framework_cards`.

    Keep ``name`` and ``kicker`` short. Each step is a
    ``(heading, description)`` pair with a one-line description. This formal
    layout uses exactly three steps so the card columns stay equally filled.
    """

    name: str
    kicker: str
    steps: tuple
    color: str = P.BLUE
    pale: str = "#EDF3F7"


def research_framework(stages, *, handoffs, deliverable, contributors, height=3.0):
    """Evidence → 2–3 stages → named handoffs → a single deliverable.

    Pass a Stage per column, a short string per adjacent arrow, and zero-based
    contributor indices. Use explicit line breaks for longer English phrases.
    """
    stages, handoffs, contributors = tuple(stages), tuple(handoffs), tuple(contributors)
    n = len(stages)
    if (n not in (2, 3) or len(handoffs) != n-1 or not all(handoffs) or
            not contributors or len(set(contributors)) != len(contributors) or
            any(not isinstance(i, int) or not 0 <= i < n for i in contributors)):
        raise ValueError("Expected 2–3 stages, named adjacent handoffs, and valid contributors")
    title, detail = deliverable
    gap, margin = .055, .024
    w = (1 - 2*margin - (n-1)*gap) / n
    x = [margin + i*(w+gap) for i in range(n)]
    mid = [a+w/2 for a in x]
    fig, ax = sheet(height)
    for i, stage in enumerate(stages):
        box(ax, x[i], .754, w, .207, stage.evidence_title, stage.evidence_detail, stage.color)
        box(ax, x[i], .395, w, .232, stage.title, stage.detail, stage.color, P.LIGHT)
        arrow(ax, (mid[i], .754), (mid[i], .63), head=8)
    for i, text in enumerate(handoffs):
        center = (x[i]+w+x[i+1])/2
        arrow(ax, (x[i]+w, .515), (x[i+1], .515), head=8)
        label(ax, center, .335, text, ha="center", size=8.4)
    positions = sorted(mid[i] for i in contributors)
    center = (positions[0]+positions[-1])/2
    for xpos in positions:
        ax.plot([xpos, xpos], [.39, .255], color=P.MUTED, lw=.8, zorder=1)
    ax.plot([positions[0], positions[-1]], [.255, .255], color=P.MUTED, lw=.8, zorder=1)
    arrow(ax, (center, .255), (center, .222), head=8)
    card_w = .59
    left = min(1-margin-card_w, max(margin, center-card_w/2))
    box(ax, left, .035, card_w, .184, title, detail, P.INK)
    return fig


def research_framework_cards(stages, *, title, subtitle, inputs, handoffs,
                             deliverable, height=5.0, width=PAGE_WIDTH):
    """Detailed, data-driven evidence → model steps → deliverable diagram.

    Parameters
    ----------
    stages : sequence of CardStage
        Two or three ordered columns. Each has exactly three concrete steps.
    inputs : pair of strings
        Heading and concise description for the shared evidence strip.
    handoffs : sequence of strings
        The output passed from each stage to the next, in stage order.
    deliverable : pair
        Heading and one or two ``(short label, detail)`` rows. No task or
        data is hardcoded; callers provide only results they can justify.

    This is an optional richer layout. The compact ``research_framework``
    remains available and its rendering is unchanged. All text is English
    and should be prewrapped where necessary.
    """
    stages = tuple(stages)
    handoffs = tuple(handoffs)
    if not isinstance(title, str) or not title or not isinstance(subtitle, str):
        raise ValueError("title and subtitle must be strings, with a nonempty title")
    if len(stages) not in (2, 3) or len(handoffs) != len(stages) - 1:
        raise ValueError("Expected two or three stages and one handoff per gap")
    if any(not isinstance(s, CardStage) or len(s.steps) != 3 or
           not s.name or not s.kicker or
           any(not isinstance(step, (tuple, list)) or len(step) != 2 or
               not all(isinstance(part, str) and part for part in step)
               for step in s.steps)
           for s in stages):
        raise ValueError("Each CardStage needs a name, kicker and three step pairs")
    if any(not isinstance(h, str) or not h for h in handoffs):
        raise ValueError("Every handoff must name a real output")
    if (not isinstance(inputs, (tuple, list)) or len(inputs) != 2 or
            not all(isinstance(part, str) and part for part in inputs)):
        raise ValueError("inputs must be a heading and description")
    if (not isinstance(deliverable, (tuple, list)) or len(deliverable) != 2 or
            not isinstance(deliverable[0], str) or not deliverable[0]):
        raise ValueError("deliverable must be a heading and detail rows")
    rows = tuple(deliverable[1])
    if not 1 <= len(rows) <= 2 or any(
            not isinstance(row, (tuple, list)) or len(row) != 2 or
            not all(isinstance(part, str) and part for part in row)
            for row in rows):
        raise ValueError("deliverable needs one or two (label, detail) rows")
    if height < 4.5 or width < 6.0:
        raise ValueError("rich framework needs at least 6.0 in width and 4.5 in height")

    fig, ax = canvas(title, subtitle, figsize=(width, height))
    margin, gap = .045, .041 if len(stages) == 3 else .07
    card_w = (1 - 2*margin - (len(stages)-1)*gap) / len(stages)
    xs = [margin+i*(card_w+gap) for i in range(len(stages))]
    centers = [x+card_w/2 for x in xs]

    # A single source strip makes the shared evidence visible without
    # pretending that each stage has a separate data origin.
    panel(ax, margin, .781, 1-2*margin, .095, P.LIGHT, "#C6CFD5",
          radius=.011, lw=.8)
    label(ax, margin+.018, .846, inputs[0], size=8.4,
          color=P.BLUE, weight="bold")
    label(ax, margin+.018, .809, inputs[1], size=8.5, color=P.INK)
    arrow(ax, (centers[0], .781), (centers[0], .748), color=P.MUTED,
          width=.9, head=8)

    for i, (x, spec) in enumerate(zip(xs, stages)):
        stage(ax, x, card_w, spec.color, spec.pale, f"{i+1:02d}",
              spec.name, spec.kicker, spec.steps, y=.299, h=.449)
    for i, handoff in enumerate(handoffs):
        arrow(ax, (xs[i]+card_w, .531), (xs[i+1], .531),
              color=P.INK, width=1.0, head=9)
        label(ax, centers[i], .268, f"Passes: {handoff}", size=8.0,
              color=P.MUTED, ha="center")

    # The final stage produces the deliverable. A short connector preserves
    # this relation even if earlier stages have differently named handoffs.
    arrow(ax, (centers[-1], .299), (centers[-1], .221),
          color=stages[-1].color, width=1.0, head=9)
    panel(ax, margin, .035, 1-2*margin, .186, "#FFFFFF", "#BFD0CA",
          radius=.011, lw=.8)
    panel(ax, margin, .164, 1-2*margin, .057, P.TEAL, P.TEAL,
          radius=.011, lw=.8)
    label(ax, margin+.018, .192, deliverable[0], size=11.5,
          color="#FFFFFF", weight="bold")
    for i, (row_label, detail) in enumerate(rows):
        y = .129-i*.050 if len(rows) == 2 else .108
        label(ax, margin+.020, y, row_label, size=8.5,
              color=P.TEAL, weight="bold")
        label(ax, margin+.17, y, detail, size=8.4, color=P.INK)
    return fig


# ---------------------------------------------------------------------------
# Promoted from FigureTraining concept03 (1.4.0): a circular feedback loop
# with directional arrows, signed interactions and caller-supplied labels.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LoopStage:
    """One node on a :func:`feedback_loop` ring.

    ``label`` and ``detail`` keep the node readable; ``color`` should follow
    the semantic encoding used elsewhere in the paper (e.g. vegetation green,
    water blue). Nodes are placed clockwise from the top.
    """

    label: str
    detail: str
    color: str = P.BLUE


def feedback_loop(stages, *, title, subtitle, center=None, signs=None,
                  footer=None, height=3.8):
    """Circular feedback loop for concept diagrams (balances, state cycles).

    ``stages`` are the nodes around the ring in causal order; the arrows
    follow the ring between adjacent nodes and are colored by the segment.
    ``signs`` optionally marks each arrow with "+" or "−" at the segment
    midpoint; ``center`` is a short label inside the loop. Pass all text as
    prewrapped English strings.
    """
    stages = tuple(stages)
    if not 3 <= len(stages) <= 6:
        raise ValueError("Feedback loop needs 3–6 stages")
    if any(not isinstance(s, LoopStage) or not s.label or not s.detail
           for s in stages):
        raise ValueError("Every LoopStage needs a label and a detail")
    if signs is not None and (len(signs) != len(stages)
                              or any(not isinstance(s, str) or not s for s in signs)):
        raise ValueError("signs, when used, needs one symbol per stage")
    if not title or not subtitle:
        raise ValueError("title and subtitle must be nonempty")

    width = PAGE_WIDTH
    fig = plt.figure(figsize=(width, height), facecolor="white")
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set(xlim=(0, width), ylim=(0, height))
    ax.set_aspect("equal")
    ax.axis("off")
    label(ax, .045, .95, title, size=10.8, weight="bold", color=P.INK, va="top")
    label(ax, .045, .88, subtitle, size=8.0, color=P.MUTED, va="top")
    ax.plot([width*.045, width*.955], [height*.815]*2, color=P.GRID, lw=.65)

    cx, cy = width*.38, height*.50
    radius = min(width, height)*.24
    outer = radius*1.55
    angles = np.linspace(90, 90-360, len(stages)+1, endpoint=True)  # clockwise
    mid_angles = (angles[:-1] + angles[1:]) / 2

    def arc(start, end, color, lw=1.15):
        a = np.deg2rad(np.linspace(start, end, 40))
        xy = np.column_stack((cx + radius*np.cos(a), cy + radius*np.sin(a)))
        path = MplPath(xy, [MplPath.MOVETO] + [MplPath.LINETO]*(len(xy)-1))
        ax.add_patch(FancyArrowPatch(path=path, arrowstyle="-|>", mutation_scale=7.5,
                                     lw=lw, color=color))

    for i, (a, b) in enumerate(zip(angles[:-1], angles[1:])):
        arc(a-10, b+10, stages[i].color)

    for i, (angle, s) in enumerate(zip(angles[:-1], stages)):
        theta = np.deg2rad(angle)
        ca, sa = np.cos(theta), np.sin(theta)
        ax.plot(cx + radius*ca, cy + radius*sa, "o", ms=3.1, mfc="white",
                mec=s.color, mew=.85, zorder=3)
        tx, ty = cx + outer*ca, cy + outer*sa
        ha = "center" if abs(ca) < .30 else ("left" if ca > 0 else "right")
        va = "bottom" if sa > .35 else ("top" if sa < -.35 else "center")
        ax.text(tx, ty, s.label, fontsize=8.0, weight="bold", color=s.color,
                ha=ha, va=va)
        ax.text(tx, ty - .17, s.detail, fontsize=8.0, color=P.MUTED, ha=ha, va=va)

    if signs is not None:
        for angle, symbol in zip(mid_angles, signs):
            theta = np.deg2rad(angle)
            ax.text(cx + radius*np.cos(theta), cy + radius*np.sin(theta), symbol,
                    fontsize=8.0, color=P.INK, ha="center", va="center",
                    bbox=dict(facecolor="white", edgecolor="none", pad=.09))

    if center:
        ax.text(cx, cy, center, fontsize=9, color=P.INK, ha="center", va="center")
    if footer:
        ax.text(width*.045, height*.07, footer, fontsize=8.0, color=P.MUTED,
                va="bottom")
    return fig
