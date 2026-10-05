"""Figures. Styling comes from viz_style (slide-ready theme on import)."""

from .viz_style import *  # noqa: I001  (must load first: sets the theme)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.dates import DateFormatter, YearLocator

from .analysis import tanh_model
from .config import FIG_DIR, ROOT, SECTORS

TREND_C = DALE_METHOD_COLORS["RegVelo"]  # primary series: Set1 blue
PAPER_C = DALE_NONSIG
OOS_C = DALE_SIG
SECTOR_COLORS = dict(zip(SECTORS, [DALE_OKABE_ITO[i] for i in (0, 2, 4, 6)]))
SECTOR_LSTYLES = dict(zip(SECTORS, ["solid", "dashed", "dotted", "dashdot"]))


def finish(fig, name: str, size: tuple[float, float] | None = None) -> None:
    FIG_DIR.mkdir(exist_ok=True)
    path = FIG_DIR / name
    if size is None:
        save_slide_wide(path, fig)
    else:
        save_slide_wide(path, fig, width=size[0], height=size[1])
    plt.close(fig)
    print(f"Saved {path.relative_to(ROOT)}")


def style_dates(ax, idx: pd.DatetimeIndex, base: int = 5) -> None:
    ax.xaxis.set_major_locator(YearLocator(base=base))
    ax.xaxis.set_major_formatter(DateFormatter("%Y"))
    ax.set_xlim(idx[0], idx[-1])


def shade_oos(ax, start: str, end) -> None:
    ax.axvspan(pd.Timestamp(start), end, color=OOS_C, alpha=0.08, linewidth=0)
    ax.text(pd.Timestamp(start), 1.0, " after publication", transform=ax.get_xaxis_transform(), color=OOS_C,
            fontsize=DALE_FONT_ANNOT, va="top", ha="left")


def legend_top(ax, ncol: int) -> None:
    ax.legend(ncol=ncol, loc="lower left", bbox_to_anchor=(0.0, 1.0), borderaxespad=0.2)


def panel_label(ax, letter: str) -> None:
    ax.text(-0.12, 1.12, letter, transform=ax.transAxes, fontsize=16, fontweight="bold", va="top")


def cumulative(trend: pd.Series, long_only: pd.Series, oos_start: str, name: str) -> None:
    fig, ax = plt.subplots()
    ax.plot(long_only.index, long_only.cumsum(), color=DALE_NONSIG, linewidth=DALE_LINE_WIDTH,
            label="Long-only (drift μ)")
    ax.plot(trend.index, trend.cumsum(), color=TREND_C, linewidth=DALE_LINE_EMPH, label="Trend, n = 5 months")
    shade_oos(ax, oos_start, trend.index[-1])
    ax.set_ylabel("Cumulative P&L (σ units)")
    legend_top(ax, ncol=2)
    style_dates(ax, trend.index)
    finish(fig, name)


def sector_cumulative(series: dict[str, pd.Series], oos_start: str, name: str) -> None:
    fig, ax = plt.subplots()
    for sec, s in series.items():
        ax.plot(s.index, s.cumsum(), color=SECTOR_COLORS[sec], linestyle=SECTOR_LSTYLES[sec],
                linewidth=DALE_LINE_WIDTH, label=sec)
    end = max(s.index[-1] for s in series.values())
    shade_oos(ax, oos_start, end)
    ax.set_ylabel("Cumulative P&L (σ units)")
    legend_top(ax, ncol=4)
    style_dates(ax, pd.DatetimeIndex([min(s.index[0] for s in series.values()), end]))
    finish(fig, name)


def sharpe_by_horizon(sr_in: dict, sr_out: dict, sr_paper: dict, name: str) -> None:
    fig, ax = plt.subplots()
    ns = list(sr_in)
    x = np.arange(len(ns))
    w = 0.27
    ax.bar(x - w, [sr_paper[n] for n in ns], width=w, color=PAPER_C, edgecolor="#4D4D4D", linewidth=0.7,
           label="Paper, futures 1960–2013")
    ax.bar(x, [sr_in[n] for n in ns], width=w, color=TREND_C, label="Ours, 1960–2013")
    ax.bar(x + w, [sr_out[n] for n in ns], width=w, color=OOS_C, label="Ours, 2014–2026")
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_xticks(x, [str(n) for n in ns])
    ax.set_xlabel("EMA time scale n (months)")
    ax.set_ylabel("Sharpe ratio")
    legend_top(ax, ncol=3)
    finish(fig, name)


def sharpe_by_decade(sr: dict[str, tuple[float, float]], name: str) -> None:
    fig, ax = plt.subplots()
    names = list(sr)
    x = np.arange(len(names))
    w = 0.38
    ax.bar(x - w / 2, [sr[k][0] for k in names], width=w, color=PAPER_C, edgecolor="#4D4D4D", linewidth=0.7,
           label="Paper, futures")
    colors = [OOS_C if k.startswith("2014") else TREND_C for k in names]
    ax.bar(x + w / 2, [sr[k][1] for k in names], width=w, color=colors, label="Ours")
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_xticks(x, names)
    ax.set_ylabel("Sharpe ratio")
    legend_top(ax, ncol=2)
    finish(fig, name)


def saturation(ravg: pd.DataFrame, fit: dict, name: str) -> None:
    fig, ax = plt.subplots()
    s = np.linspace(ravg["x"].min(), ravg["x"].max(), 300)
    ax.plot(ravg["x"], ravg["y"], color=DALE_GREYLIGHT, linewidth=DALE_LINE_WIDTH, label="Data (running average)")
    ax.plot(s, fit["lin_a"] + fit["lin_b"] * s, color=DALE_NONSIG, linestyle="dashed", linewidth=DALE_LINE_WIDTH,
            label="Linear fit")
    ax.plot(s, tanh_model(s, fit["tanh_a"], fit["tanh_b"], fit["tanh_s_star"]), color=TREND_C,
            linewidth=DALE_LINE_EMPH, label=f"tanh fit, s* = {fit['tanh_s_star']:.2f}")
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.axvline(0.0, color="black", linewidth=0.8)
    ax.set_xlabel("Signal s")
    ax.set_ylabel("Next move / σ")
    ax.legend(loc="upper left", fontsize=12)
    finish(fig, name)


def rolling_10y(roll: pd.Series, oos_start: str, name: str) -> None:
    fig, ax = plt.subplots()
    ax.plot(roll.index, roll, color=TREND_C, linewidth=DALE_LINE_EMPH)
    ax.axhline(roll.mean(), color=DALE_NONSIG, linestyle="dashed", linewidth=DALE_LINE_WIDTH, label="Average")
    ax.axhline(0.0, color="black", linewidth=0.8)
    shade_oos(ax, oos_start, roll.index[-1])
    ax.set_ylabel("10y average P&L per asset\n(σ units per year)")
    legend_top(ax, ncol=1)
    style_dates(ax, roll.index)
    finish(fig, name)


def averaging(mean: dict[str, float], name: str) -> None:
    fig, ax = plt.subplots()
    labels = ["Monthly average\nlag 0", "Monthly average\nlag 1 (as printed)", "Month-end\nlag 0",
              "Month-end\nlag 1"]
    vals = [mean["avg0"], mean["avg1"], mean["eom0"], mean["eom1"]]
    colors = [OOS_C, TREND_C, DALE_NONSIG, DALE_GREYLIGHT]
    ax.bar(range(4), vals, color=colors, edgecolor="#4D4D4D", linewidth=0.7, width=DALE_BAR_WIDTH)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.01, f"{v:.2f}", ha="center", va="bottom", fontsize=DALE_FONT_ANNOT)
    ax.set_xticks(range(4), labels)
    ax.set_ylabel("Mean Sharpe ratio\n(6 FX + US 10y)")
    ax.set_ylim(0, max(vals) * 1.2)
    finish(fig, name)


def long_us(cum: pd.DataFrame, name: str) -> None:
    fig, ax = plt.subplots()
    for c, color, ls, label in [("EQ_US_1871", SECTOR_COLORS["Indices"], "solid", "S&P composite"),
                                ("BD_US_1871", SECTOR_COLORS["Bonds"], "dashed", "US 10y bond")]:
        s = cum[c].dropna()
        ax.plot(s.index, s, color=color, linestyle=ls, linewidth=DALE_LINE_WIDTH, label=label)
    tot = cum.sum(axis=1)
    ax.plot(tot.index, tot, color=TREND_C, linewidth=DALE_LINE_EMPH, label="Both")
    ax.set_ylabel("Cumulative trend P&L (σ units)")
    legend_top(ax, ncol=3)
    style_dates(ax, cum.dropna(how="all").index, base=20)
    finish(fig, name)
