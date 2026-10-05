"""
Dale Wang — Visualization Style Guide (Python / Matplotlib / Seaborn)
Mirror of visualization_style.R

Usage:
    from visualization_style import *
    # or
    import visualization_style as ds

Slide-ready theme is applied automatically on import.
Call set_theme_report() at the top of a script for written reports.
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

try:
    import seaborn as sns
    _HAS_SEABORN = True
except ImportError:
    _HAS_SEABORN = False


# ============================================================
# 1. CORE THEME
# ============================================================
# L-shaped axes (top/right spines off), no grid, white background.
# DEFAULT: slide-ready (base_fontsize = 14).
# Switch to set_theme_report() for written reports / journals.

def _rcparams(base_fontsize: int) -> dict:
    """Base rcParams dict — shared between slide and report themes."""
    return {
        # Font
        "font.family":            "sans-serif",
        "font.sans-serif":        ["Arial", "Helvetica Neue", "Helvetica",
                                   "DejaVu Sans"],
        "font.size":              base_fontsize,
        "axes.titlesize":         base_fontsize + 2,
        "axes.labelsize":         base_fontsize + 1,
        "xtick.labelsize":        base_fontsize,
        "ytick.labelsize":        base_fontsize,
        "legend.fontsize":        base_fontsize - 1,
        "legend.title_fontsize":  base_fontsize,
        # L-shaped axes — remove top and right spines
        "axes.spines.top":        False,
        "axes.spines.right":      False,
        "axes.linewidth":         0.9,
        # No grid
        "axes.grid":              False,
        # White backgrounds
        "axes.facecolor":         "white",
        "figure.facecolor":       "white",
        # Ticks — outward, matched to R style
        "xtick.major.size":       4.0,
        "ytick.major.size":       4.0,
        "xtick.major.width":      0.7,
        "ytick.major.width":      0.7,
        "xtick.minor.size":       2.0,
        "ytick.minor.size":       2.0,
        "xtick.direction":        "out",
        "ytick.direction":        "out",
        "xtick.color":            "black",
        "ytick.color":            "black",
        # Legend — no box
        "legend.frameon":         False,
        "legend.borderpad":       0.4,
        "legend.handlelength":    1.5,
        # Lines and markers
        "lines.linewidth":        1.5,
        "lines.markersize":       7.0,
        "patch.linewidth":        0.7,
        # Save settings
        "figure.dpi":             150,   # screen preview
        "savefig.dpi":            300,
        "savefig.bbox":           "tight",
        "savefig.facecolor":      "white",
        "savefig.edgecolor":      "none",
    }


def set_theme_slide():
    """
    Apply slide-ready theme (base_fontsize=14).
    Called automatically on import — no action needed for slides.
    """
    rc = _rcparams(14)
    mpl.rcParams.update(rc)
    if _HAS_SEABORN:
        sns.set_theme(style="ticks", rc=rc)


def set_theme_report():
    """
    Apply report / journal theme (base_fontsize=11).
    Call at the top of a script when preparing written report figures.
    Remember to also use save_report() or save_pdf() instead of save_slide().
    """
    rc = _rcparams(11)
    mpl.rcParams.update(rc)
    if _HAS_SEABORN:
        sns.set_theme(style="ticks", rc=rc)


# Apply slide theme by default on import
set_theme_slide()


def despine(ax=None):
    """Remove top and right spines. Apply after any seaborn call that re-adds them."""
    if ax is None:
        ax = plt.gca()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    return ax


# ============================================================
# 2. SIZE CONSTANTS
# ============================================================
# Font sizes are in points (pt), matching the R guide.
# Marker sizes for ax.scatter() are in points² (s=).
# Marker sizes for ax.plot() are in points (markersize=).
# Line widths are in points (linewidth=).

# Geometry
DALE_POINT_SIZE   = 40      # ax.scatter(s=...) — standard scatter / PCA
DALE_JITTER_SIZE  = 25      # ax.scatter(s=...) — dense / jitter
DALE_LINE_WIDTH   = 1.5     # ax.plot(linewidth=...) — regular lines
DALE_LINE_EMPH    = 2.5     # ax.plot(linewidth=...) — regression / trend / primary method
DALE_ERRBAR_WIDTH = 1.2     # ax.errorbar(linewidth=...) — ≥ 1.0 for print visibility
DALE_BAR_WIDTH    = 0.65    # ax.bar(width=...)
DALE_VIOLIN_WIDTH = 0.7     # violinplot widths

# Text annotation sizes (pt) — separate slide and report constants
DALE_FONT_ANNOT        = 14   # ax.text(fontsize=...) / ax.annotate — SLIDES (default)
DALE_FONT_ANNOT_REPORT = 11   # ax.text(fontsize=...) / ax.annotate — reports

# Usage:
#   ax.text(x, y, "label", fontsize=DALE_FONT_ANNOT)          # slides
#   ax.text(x, y, "label", fontsize=DALE_FONT_ANNOT_REPORT)   # reports


# ============================================================
# 3. COLOR PALETTES
# ============================================================

# ── 3a. Two-group (control vs treatment / CD vs HFD) ────────
# ⚠ GRAYSCALE WARNING: #66C2A5 and #FC8D62 have similar luminance.
#   Always double-encode with marker shape or linestyle for B&W print.
DALE_2GROUP = {
    "CD":      "#66C2A5",   # teal-green    (Set2 #1) — control
    "HFD":     "#FC8D62",   # salmon-orange (Set2 #2) — treatment
    "control": "#66C2A5",
    "treat":   "#FC8D62",
}
DALE_2GROUP_LIST = ["#66C2A5", "#FC8D62"]   # [control, treatment]


# ── 3b. Qualitative 6-color (Set2) ──────────────────────────
# Slot 6 (#FFD92F muted yellow) is low-contrast on white — use last.
DALE_QUAL6 = [
    "#66C2A5",   # teal-green
    "#FC8D62",   # salmon-orange
    "#8DA0CB",   # muted periwinkle-blue
    "#E78AC3",   # soft pink
    "#A6D854",   # light green
    "#FFD92F",   # muted yellow (low contrast — last resort)
]


# ── 3c. TE subfamily categories ─────────────────────────────
DALE_TE_COLORS = {
    "SINE":  "#FC8D62",   # salmon
    "LINE":  "#66C2A5",   # teal
    "LTR":   "#E78AC3",   # soft pink
    "DNA":   "#8DA0CB",   # muted periwinkle-blue
    "Other": "#A6D854",   # light green
}


# ── 3d. GO term categories ───────────────────────────────────
DALE_GO_COLORS = {
    "BP": "#8DA0CB",   # muted steel-blue (Biological Process)
    "MF": "#66C2A5",   # seafoam/teal (Molecular Function)
    "CC": "#BC80BD",   # soft lavender (Cellular Component)
}


# ── 3e. Highlight vs background ─────────────────────────────
DALE_SIG       = "#D95F02"   # warm orange-brown — significant / enriched
DALE_NONSIG    = "#BDBDBD"   # neutral mid-gray  — not enriched (data points)
DALE_REGLINE   = "#2166AC"   # steel blue        — regression / trend lines
DALE_GREYLIGHT = "#D9D9D9"   # light gray        — background spaghetti lines


# ── 3f. KO vs WT / perturbation violin fills ────────────────
# Use #969696 (mid-gray), NOT #BDBDBD — too light on white slides.
DALE_KO_COLORS = {
    "WT":      "#969696",   # mid-gray — clearly visible on white
    "KO":      "#FC8D62",   # salmon-orange
    "control": "#969696",
    "treat":   "#FC8D62",
}


# ── 3g. scRNA-seq cell-type palette ─────────────────────────
# ⚠ COLORBLIND WARNING: Delta (red #E05C5C) and Beta (green #59A14F)
#   are indistinguishable for ~8% of male viewers.
#   Use DALE_OKABE_ITO for public-facing talks and conference posters.
DALE_SCRNA_CELLTYPES = {
    "Progenitor":  "#4C9BE8",   # cornflower blue
    "Cycling":     "#F28E2B",   # warm orange
    "Beta":        "#59A14F",   # medium green       ⚠ red-green conflict
    "Alpha":       "#9467BD",   # muted purple
    "Delta":       "#E05C5C",   # muted red          ⚠ red-green conflict
    "Epsilon":     "#B07AA1",   # dusty rose-purple
    "Ductal":      "#76B7B2",   # steel teal
    "Acinar":      "#EDC948",   # golden yellow (use sparingly — low contrast on white)
    "Erythroid":   "#D62728",   # strong red
    "Neutrophil":  "#1F4E79",   # dark navy
    "Other":       "#BDBDBD",   # gray
}

# Cell cycle phases
DALE_CELLCYCLE = {
    "G1":  "#66C2A5",
    "S":   "#FC8D62",
    "G2M": "#8DA0CB",
}


# ── 3h. Method comparison (scRNA benchmarking) ──────────────
# Primary method always gets solid line + most prominent color.
DALE_METHOD_COLORS = {
    "RegVelo":  "#377EB8",   # Set1 blue  — primary
    "veloVI":   "#FC8D62",   # salmon-orange
    "scVelo":   "#4DAF4A",   # Set1 green
    "UniTVelo": "#984EA3",   # Set1 purple
}
DALE_METHOD_LSTYLES = {
    "RegVelo":  "solid",
    "veloVI":   "dashed",
    "scVelo":   "dotted",
    "UniTVelo": "dashdot",
}


# ── 3i. Network / regulatory graph node colors ──────────────
DALE_NETWORK_NODES = {
    "TF":           "#FC8D62",   # salmon-orange — transcription factor
    "Target":       "#8DA0CB",   # periwinkle-blue — target gene
    "SharedTarget": "#66C2A5",   # teal — shared target across lineages
}


# ── 3j. Colorblind-safe palette (Okabe-Ito) ─────────────────
# Use for public talks and any figure with > 4 color categories.
DALE_OKABE_ITO = [
    "#E69F00",   # warm yellow-orange
    "#56B4E9",   # sky blue
    "#009E73",   # green
    "#F0E442",   # yellow (low contrast — use last)
    "#0072B2",   # deep blue
    "#D55E00",   # vermillion
    "#CC79A7",   # mauve-pink
    "#000000",   # black
]

# Earth tones — multi-species / multi-condition panels
DALE_EARTH = ["#A6611A", "#DFC27D", "#80CDC1", "#018571"]


# ============================================================
# 4. COLORMAP HELPERS
# ============================================================

def dale_div_cmap():
    """
    Diverging colormap: blue (#2166AC) — white — warm red (#D6604D).
    Equivalent to scale_fill_dale_div() in R.
    Usage: im = ax.imshow(data, cmap=dale_div_cmap(), vmin=-v, vmax=v)
    """
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list(
        "dale_div", ["#2166AC", "white", "#D6604D"]
    )


# Recommended colormap strings
# ⚠ SEQUENTIAL: prefer these over YlGn/YlOrBr — they start at a visible
#   color, not near-white yellow that disappears on white backgrounds.
DALE_PSEUDOTIME_CMAP  = "viridis_r"   # purple=early (visible in legend), yellow=late
DALE_EXPRESSION_CMAP  = "magma_r"     # light=low expression, dark=high
DALE_SEQ_BLUE         = "Blues"       # light→dark blue — safe in B&W
DALE_SEQ_WARM         = "rocket_r"    # white → dark red-brown
DALE_SEQ_COOL         = "mako_r"      # white → dark blue-green

# Usage examples:
#   sc = ax.scatter(x, y, c=pseudotime, cmap=DALE_PSEUDOTIME_CMAP)
#   plt.colorbar(sc, ax=ax, label="Pseudotime")
#   sns.heatmap(df, cmap=dale_div_cmap(), center=0, vmin=-3, vmax=3)


# ============================================================
# 5. FIGURE HELPERS
# ============================================================

def ax_embedding(ax=None, xlabel="UMAP1", ylabel="UMAP2"):
    """
    Format a UMAP / PHATE / FLE axis:
      - Remove tick marks and tick labels (unitless space)
      - Keep L-shaped axis lines and axis labels
    Call after plotting the scatter.

    Usage:
        fig, ax = plt.subplots()
        ax.scatter(umap1, umap2, c=colors, s=DALE_JITTER_SIZE)
        ax_embedding(ax)
    """
    if ax is None:
        ax = plt.gca()
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.spines["left"].set_visible(True)
    ax.spines["bottom"].set_visible(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    return ax


def add_significance(ax, x1, x2, y, p_value, h=0.02, fontsize=None):
    """
    Draw a significance bracket between two groups.

    Parameters
    ----------
    ax       : matplotlib Axes
    x1, x2  : x-positions of the two groups (e.g. 0 and 1)
    y        : y-position of the bracket (in data coordinates)
    p_value  : float — determines star label
    h        : float — height of the bracket tick marks (data units)
    fontsize : int — defaults to DALE_FONT_ANNOT (slides)
    """
    if fontsize is None:
        fontsize = DALE_FONT_ANNOT

    if p_value < 0.001:
        label = "***"
    elif p_value < 0.01:
        label = "**"
    elif p_value < 0.05:
        label = "*"
    else:
        label = "n.s."

    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y],
            lw=0.9, color="black")
    ax.text((x1 + x2) / 2, y + h, label,
            ha="center", va="bottom", fontsize=fontsize)
    return ax


# ============================================================
# 6. FIGURE SAVING
# ============================================================
# Slide dimensions are the DEFAULT. Use report / pdf variants
# when preparing written reports or journal submissions.
# Remember: switch to set_theme_report() before saving report figures.

def save_slide(filename, fig=None, width=6.5, height=5.0, dpi=300):
    """
    Save a slide-ready PNG (6.5 × 5 in, 300 dpi). DEFAULT output format.
    Equivalent to save_dale_slide() in R.
    """
    if fig is None:
        fig = plt.gcf()
    fig.set_size_inches(width, height)
    fig.savefig(filename, dpi=dpi, bbox_inches="tight", facecolor="white")
    return filename


def save_slide_wide(filename, fig=None, width=10.0, height=5.0, dpi=300):
    """Save a wide multi-panel slide figure (10 × 5 in, 300 dpi)."""
    return save_slide(filename, fig=fig, width=width, height=height, dpi=dpi)


def save_report(filename, fig=None, width=3.5, height=3.0, dpi=300):
    """
    Save a single-column report PNG (3.5 × 3 in, 300 dpi).
    Call set_theme_report() before plotting.
    Equivalent to save_dale_report() in R.
    """
    if fig is None:
        fig = plt.gcf()
    fig.set_size_inches(width, height)
    fig.savefig(filename, dpi=dpi, bbox_inches="tight", facecolor="white")
    return filename


def save_report_double(filename, fig=None, width=7.0, height=5.0, dpi=300):
    """Save a double-column report PNG (7 × 5 in, 300 dpi)."""
    return save_report(filename, fig=fig, width=width, height=height, dpi=dpi)


def save_pdf(filename, fig=None, width=7.0, height=5.0):
    """
    Save a vector PDF for journal submission (7 × 5 in).
    PDF is required by most journals — do not substitute PNG.
    Call set_theme_report() before plotting.
    Equivalent to save_dale_pdf() in R.
    """
    if fig is None:
        fig = plt.gcf()
    fig.set_size_inches(width, height)
    fig.savefig(filename, format="pdf", bbox_inches="tight",
                facecolor="white", backend="pdf")
    return filename


# ============================================================
# 7. QUICK-REFERENCE CHEAT SHEET
# ============================================================
#
#  THEME  (slide-ready by default — no action needed)
#  ─────
#  set_theme_slide()          14pt base — applied on import
#  set_theme_report()         11pt base — call for written reports
#
#  SWITCHING TO REPORT MODE (do this at top of script)
#  ─────────────────────────
#  set_theme_report()
#  # ... make your plot ...
#  save_report("fig.png")   or   save_pdf("fig.pdf")
#
#  GEOMETRY CONSTANTS
#  ──────────────────
#  ax.scatter(x, y, s=DALE_POINT_SIZE)          40 — standard scatter
#  ax.scatter(x, y, s=DALE_JITTER_SIZE)          25 — dense / jitter
#  ax.plot(x, y, linewidth=DALE_LINE_WIDTH)      1.5 — regular line
#  ax.plot(x, y, linewidth=DALE_LINE_EMPH)       2.5 — trend / regression
#  ax.errorbar(..., linewidth=DALE_ERRBAR_WIDTH) 1.2 — error bars
#  ax.bar(..., width=DALE_BAR_WIDTH)             0.65
#
#  ANNOTATION TEXT
#  ───────────────
#  ax.text(x, y, s, fontsize=DALE_FONT_ANNOT)        14pt — slides
#  ax.text(x, y, s, fontsize=DALE_FONT_ANNOT_REPORT) 11pt — reports
#  add_significance(ax, x1, x2, y, p_value)           auto star label
#
#  COLORS
#  ──────
#  DALE_2GROUP_LIST            ['#66C2A5', '#FC8D62'] control / treat
#    ⚠ similar luminance — add marker shape for B&W print
#  DALE_KO_COLORS              {'WT': '#969696', 'KO': '#FC8D62'}
#  DALE_SIG / DALE_NONSIG      '#D95F02' / '#BDBDBD'
#  DALE_TE_COLORS              dict — SINE LINE LTR DNA Other
#  DALE_GO_COLORS              dict — BP MF CC
#  DALE_SCRNA_CELLTYPES        dict — 11 cell types ⚠ red-green conflict
#  DALE_OKABE_ITO              colorblind-safe 8-color list
#  DALE_METHOD_COLORS          dict — RegVelo veloVI scVelo UniTVelo
#  DALE_METHOD_LSTYLES         dict — matching line styles
#
#  COLORMAPS
#  ─────────
#  dale_div_cmap()             diverging blue–white–red object
#  DALE_PSEUDOTIME_CMAP        'viridis_r'  (purple=early — visible in legend)
#  DALE_EXPRESSION_CMAP        'magma_r'    (light=low)
#  DALE_SEQ_BLUE               'Blues'      (B&W safe)
#  DALE_SEQ_WARM               'rocket_r'
#  DALE_SEQ_COOL               'mako_r'
#
#  SAVING
#  ──────
#  save_slide("fig.png")                 6.5 × 5.0 in, PNG [DEFAULT]
#  save_slide_wide("fig.png")           10.0 × 5.0 in, PNG [multi-panel]
#  save_report("fig.png")               3.5 × 3.0 in, PNG [single col]
#  save_report_double("fig.png")         7.0 × 5.0 in, PNG [double col]
#  save_pdf("fig.pdf")                   7.0 × 5.0 in, PDF [journals]
#
#  EMBEDDING HELPER
#  ────────────────
#  ax_embedding(ax)     removes ticks, keeps L-axes + labels
#
# ============================================================
# END OF STYLE GUIDE
# ============================================================
