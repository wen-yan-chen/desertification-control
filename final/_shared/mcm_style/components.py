"""Reusable diagram components on a 0-1 axes coordinate system.

Two levels of structure are available:

* primitives -- :func:`sheet`, :func:`panel`, :func:`box`, :func:`arrow`
  (simple boxes, the style the Practice2 paper figures used).
* rich components -- :func:`canvas` (bold title + subtitle) and :func:`stage`
  (a white card with a solid-color header bar and nested pale sub-cards),
  ported from the FigureTraining ``workflow01`` drill.

All coordinates are axes fractions (0-1), so the same layout code works at any
physical size. Figures default to the 6.5-inch MCM text width.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from . import palette as P
from .typography import PAGE_WIDTH


def sheet(height, width=PAGE_WIDTH):
    """Create a borderless full-bleed canvas with a 0-1 axes for diagrams."""
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_axes([0, 0, 1, 1], xlim=(0, 1), ylim=(0, 1))
    ax.set_axis_off()
    return fig, ax


def panel(ax, x, y, w, h, fill, edge=None, radius=0.012, lw=0.8, zorder=2):
    """Draw a rounded rectangle."""
    if edge is None:
        edge = fill
    patch = FancyBboxPatch(
        (x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radius}",
        fc=fill, ec=edge, lw=lw, transform=ax.transAxes,
        clip_on=False, zorder=zorder)
    ax.add_patch(patch)
    return patch


def label(ax, x, y, text, size=9, color=None, weight="normal",
          ha="left", va="center", fontfamily=None, zorder=3):
    """Place text in axes-fraction coordinates."""
    kwargs = dict(transform=ax.transAxes, fontsize=size, color=color or P.INK,
                  weight=weight, ha=ha, va=va, linespacing=1.18, zorder=zorder)
    if fontfamily is not None:
        kwargs["fontfamily"] = fontfamily
    return ax.text(x, y, text, **kwargs)


def arrow(ax, start, end, color=None, width=1.0, head=10, **kwargs):
    """Draw a block arrow between two axes-fraction points."""
    patch = FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=head,
        lw=width, color=color or P.MUTED, shrinkA=0, shrinkB=0,
        transform=ax.transAxes, **kwargs)
    ax.add_patch(patch)
    return patch


def box(ax, x, y, w, h, title, detail, color, fill="white",
        title_size=10, detail_size=8.6):
    """Simple titled box (Practice2 style): colored title on a filled card."""
    panel(ax, x, y, w, h, fill, color, radius=0.012, lw=0.9)
    label(ax, x + w / 2, y + h * 0.70, title, size=title_size,
          color=color, weight="bold", ha="center")
    label(ax, x + w / 2, y + h * 0.32, detail, size=detail_size,
          ha="center", va="center")


def canvas(title, subtitle, figsize, title_color=None):
    """Create a diagram canvas pre-fitted with a bold title and a muted subtitle."""
    fig = plt.figure(figsize=figsize, facecolor="white")
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    label(ax, 0.045, 0.985, title, size=15.5, weight="bold",
          color=title_color or P.INK, va="top")
    label(ax, 0.045, 0.917, subtitle, size=8.7, color=P.MUTED, va="top")
    return fig, ax


def stage(ax, x, w, color, pale, number, name, kicker, steps,
          y=0.315, h=0.445, edge="#C6CFD5"):
    """Rich model card: white frame, solid header bar, nested pale sub-cards.

    ``steps`` contains one to three ``(heading, description)`` pairs. Wrap
    text before passing it; use a second stage for longer chains.
    """
    steps = tuple(steps)
    if not 1 <= len(steps) <= 3 or w <= .065 or h <= 0:
        raise ValueError("stage requires a positive card size and one to three steps")
    panel(ax, x, y, w, h, "#FFFFFF", edge, radius=0.012)
    scale = h / .445
    header_h = .087 * scale
    panel(ax, x, y + h - header_h, w, header_h, color, color, radius=0.012)
    label(ax, x + 0.017, y + h - 0.044 * scale, number, size=14,
          color="#FFFFFF", weight="bold")
    label(ax, x + 0.065, y + h - 0.044 * scale, name, size=10.5,
          color="#FFFFFF", weight="bold")
    label(ax, x + 0.017, y + h - 0.119 * scale, kicker, size=8,
          color=color, weight="bold")
    for i, (heading, desc) in enumerate(steps):
        cy = y + (.22 - .10 * i) * scale
        panel(ax, x + 0.016, cy, w - 0.032, 0.082 * scale, pale, pale,
              radius=0.007, lw=0.5)
        label(ax, x + 0.028, cy + 0.061 * scale, heading, size=8.75,
              color=P.INK, weight="bold")
        label(ax, x + 0.028, cy + 0.020 * scale, desc, size=8, color=P.MUTED)
        if i < len(steps) - 1:
            arrow(ax, (x + w / 2, cy - 0.001 * scale), (x + w / 2, cy - 0.020 * scale),
                  color=color, width=0.8, head=6)
