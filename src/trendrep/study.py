"""Replication of Lempérière et al. (2014) on free data, and an out-of-sample test after publication.

Run:  uv run trendrep           (downloads raw data once into data/raw/)
"""

import argparse
import json

import numpy as np
import pandas as pd

from . import plots
from .analysis import oos_comparison, running_average, saturation_fit, sharpe, summary, t_stat
from .config import (
    ASSETS,
    DECADES,
    LAG,
    LONG_US_BLOCKS,
    MAIN_N,
    N_GRID,
    OOS_START,
    PAPER_FIT,
    PAPER_TABLE1,
    PAPER_TABLE2,
    PAPER_TABLE3,
    PUBLICATION_END,
    RES_DIR,
    RUNNING_AVG_POINTS,
    SAMPLE_START,
    SECTORS,
)
from .data import build_month_end_panel, build_panel, build_us_long
from .signal import panel_pnl, pooled_signal_moves

SECTOR_OF = {a.name: a.sector for a in ASSETS}


def fmt(x: float, digits: int = 2) -> str:
    return "–" if x is None or not np.isfinite(x) else f"{x:.{digits}f}".replace("-", "−")


def agg(pnl: pd.DataFrame, cols: list[str] | None = None) -> pd.Series:
    """Paper's aggregate: sum of the risk-normalised P&L over the assets alive that month."""
    sub = pnl if cols is None else pnl[cols]
    return sub.sum(axis=1, min_count=1).loc[SAMPLE_START:].dropna()


class Study:
    def __init__(self) -> None:
        self.panel = build_panel()
        self.facts: dict = {}
        self.tables: dict = {}
        self.trend = panel_pnl(self.panel, MAIN_N, LAG)
        self.long = panel_pnl(self.panel, MAIN_N, LAG, long_only=True)
        self.T, self.L = agg(self.trend), agg(self.long)
        self.facts["sample"] = f"{self.T.index.min():%Y-%m} → {self.T.index.max():%Y-%m}"
        self.facts["n_assets"] = int(self.trend.notna().any().sum())

    def run(self) -> None:
        self.headline()
        self.horizons()
        self.sectors()
        self.decades()
        self.out_of_sample()
        self.saturation()
        self.rolling()
        self.averaging_check()
        self.long_us()

    def _upto(self, s: pd.Series, end: str = PUBLICATION_END) -> pd.Series:
        return s.loc[:end]

    # ------------------------------------------------------------------ replication

    def headline(self) -> None:
        s = summary(self._upto(self.T), self._upto(self.L))
        corr = float(self._upto(self.T).corr(self._upto(self.L)))
        self.facts["headline"] = s | {"corr_trend_long": corr}
        plots.cumulative(self.T, self.L, OOS_START, "fig01_aggregate_pnl.png")
        plots.sector_cumulative({sec: agg(self.trend, self._cols(sec)) for sec in SECTORS}, OOS_START,
                                "fig02_sector_pnl.png")

    def _cols(self, sector: str) -> list[str]:
        return [c for c in self.trend if SECTOR_OF[c] == sector]

    def horizons(self) -> None:
        rows, sr_in, sr_out = [], {}, {}
        for n in N_GRID:
            T, L = agg(panel_pnl(self.panel, n, LAG)), agg(panel_pnl(self.panel, n, LAG, long_only=True))
            s = summary(self._upto(T), self._upto(L))
            oos = T.loc[OOS_START:]
            sr_in[n], sr_out[n] = s["sr"], sharpe(oos)
            p = PAPER_TABLE1[n]
            rows.append([str(n), fmt(p[0]), fmt(s["sr"]), fmt(p[1], 1), fmt(s["t"], 1), fmt(p[2], 1),
                         fmt(s["t_debiased"], 1), fmt(sr_out[n]), fmt(t_stat(oos), 1)])
        self.tables["horizons"] = {
            "header": ["n (months)", "SR paper", "SR ours", "t paper", "t ours", "t* paper", "t* ours",
                       "SR 2014–26", "t 2014–26"],
            "rows": rows,
        }
        self.facts["horizon_sr"] = {"in": sr_in, "out": sr_out}
        plots.sharpe_by_horizon(sr_in, sr_out, {n: v[0] for n, v in PAPER_TABLE1.items()}, "fig03_sharpe_by_n.png")

    def sectors(self) -> None:
        rows = []
        self.facts["sectors"] = {}
        for sec in SECTORS:
            cols = self._cols(sec)
            T, L = agg(self.trend, cols), agg(self.long, cols)
            s = summary(self._upto(T), self._upto(L))
            oos = T.loc[OOS_START:]
            p = PAPER_TABLE2[sec]
            self.facts["sectors"][sec] = s | {"sr_oos": sharpe(oos), "t_oos": t_stat(oos), "n_assets": len(cols)}
            rows.append([sec, fmt(p[0]), fmt(s["sr"]), fmt(p[1], 1), fmt(s["t"], 1), fmt(p[2], 1),
                         fmt(s["t_debiased"], 1), fmt(s["sr_mu"]), p[3], s["start"], fmt(sharpe(oos)),
                         fmt(t_stat(oos), 1)])
        self.tables["sectors"] = {
            "header": ["Sector", "SR paper", "SR ours", "t paper", "t ours", "t* paper", "t* ours", "SR(μ) ours",
                       "Start paper", "Start ours", "SR 2014–26", "t 2014–26"],
            "rows": rows,
        }

    def decades(self) -> None:
        rows, sr = [], {}
        for name, start, end in DECADES:
            T, L = self.T.loc[start:end], self.L.loc[start:end]
            s = summary(T, L)
            p = PAPER_TABLE3.get(name, (np.nan, np.nan, np.nan))
            sr[name] = (p[0], s["sr"])
            rows.append([name, fmt(p[0]), fmt(s["sr"]), fmt(p[1], 1), fmt(s["t"], 1), fmt(p[2], 1),
                         fmt(s["t_debiased"], 1), fmt(s["sr_mu"]), fmt(s["t_mu"], 1)])
        self.tables["decades"] = {
            "header": ["Period", "SR paper", "SR ours", "t paper", "t ours", "t* paper", "t* ours", "SR(μ) ours",
                       "t(μ) ours"],
            "rows": rows,
        }
        self.facts["decade_sr"] = sr
        plots.sharpe_by_decade(sr, "fig04_sharpe_by_decade.png")

    # ------------------------------------------------------------------ after publication

    def out_of_sample(self) -> None:
        res = oos_comparison(self.T, OOS_START)
        lres = oos_comparison(self.L, OOS_START)
        self.facts["oos"] = res | {"long_sr_in": lres["sr_in"], "long_sr_out": lres["sr_out"]}
        yearly = self.per_asset().groupby(self.T.index.year).sum()  # σ units per asset per year
        self.facts["oos_years_negative"] = int((yearly.loc[2014:] < 0).sum())
        self.facts["oos_years"] = int(len(yearly.loc[2014:]))
        self.facts["oos_yearly"] = {int(k): float(v) for k, v in yearly.loc[2014:].items()}

    # ------------------------------------------------------------------ the signal

    def saturation(self) -> None:
        pts = pooled_signal_moves(self.panel, MAIN_N, LAG)
        pts = pts[pts.index >= pd.Timestamp(SAMPLE_START)]
        x, y = pts["signal"].to_numpy(), pts["move"].to_numpy()
        fit = saturation_fit(x, y)
        self.facts["saturation"] = fit | {"paper": PAPER_FIT}
        plots.saturation(running_average(x, y, RUNNING_AVG_POINTS), fit, "fig05_saturation.png")

    def per_asset(self) -> pd.Series:
        """Aggregate P&L divided by the number of assets alive, so periods with fewer markets compare fairly."""
        return self.T / self.trend.notna().sum(axis=1).reindex(self.T.index)

    def rolling(self) -> None:
        roll = self.per_asset().rolling(120).mean() * 12
        self.facts["rolling10_min"] = float(roll.min())
        self.facts["rolling10_min_date"] = f"{roll.idxmin():%Y-%m}"
        self.facts["rolling10_last"] = float(roll.dropna().iloc[-1])
        plots.rolling_10y(roll.dropna(), OOS_START, "fig06_rolling_10y.png")

    # ------------------------------------------------------------------ data checks and long history

    def averaging_check(self) -> None:
        eom = build_month_end_panel()
        rows, means = [], {k: [] for k in ("avg0", "avg1", "eom0", "eom1")}
        for c in eom:
            e = eom[c].dropna()
            a = self.panel[c].dropna()
            a = a[a.index >= e.index[0]]
            res = {
                "avg0": sharpe(panel_pnl(a.to_frame(), MAIN_N, 0)[c]),
                "avg1": sharpe(panel_pnl(a.to_frame(), MAIN_N, 1)[c]),
                "eom0": sharpe(panel_pnl(e.to_frame(), MAIN_N, 0)[c]),
                "eom1": sharpe(panel_pnl(e.to_frame(), MAIN_N, 1)[c]),
            }
            for k, v in res.items():
                means[k].append(v)
            ac_a = float(np.log(a).diff().autocorr(1))
            ac_e = float(np.log(e).diff().autocorr(1))
            rows.append([c, f"{e.index[0]:%Y}", fmt(ac_a), fmt(ac_e)] + [fmt(res[k]) for k in res])
        mean = {k: float(np.mean(v)) for k, v in means.items()}
        rows.append(["Mean", "", "", ""] + [fmt(mean[k]) for k in ("avg0", "avg1", "eom0", "eom1")])
        self.tables["averaging"] = {
            "header": ["Market", "From", "AC(1) avg", "AC(1) month-end", "SR avg, lag 0", "SR avg, lag 1",
                       "SR month-end, lag 0", "SR month-end, lag 1"],
            "rows": rows,
        }
        self.facts["averaging"] = mean
        plots.averaging(mean, "fig07_averaging_check.png")

    def long_us(self) -> None:
        us = build_us_long()
        T, L = panel_pnl(us, MAIN_N, LAG), panel_pnl(us, MAIN_N, LAG, long_only=True)
        tot, ltot = T.sum(axis=1, min_count=1).dropna(), L.sum(axis=1, min_count=1).dropna()
        rows = []
        for name, start, end in [("Full", "1800", "2100"), *LONG_US_BLOCKS]:
            s = summary(tot.loc[start:end], ltot.loc[start:end])
            per = {c: sharpe(T[c].loc[start:end]) for c in T}
            rows.append([name if name != "Full" else f"{tot.index.min():%Y}–{tot.index.max():%Y}", fmt(s["sr"]),
                         fmt(s["t"], 1), fmt(s["t_debiased"], 1), fmt(per["EQ_US_1871"]), fmt(per["BD_US_1871"])])
        self.tables["long_us"] = {
            "header": ["Period", "SR (2 assets)", "t", "t*", "SR equity", "SR bond"],
            "rows": rows,
        }
        self.facts["long_us"] = summary(tot, ltot)
        plots.long_us(T.cumsum(), "fig08_us_since_1871.png")


def _clean(x):
    """JSON-safe copy: numpy scalars to Python, NaN/inf to None, int keys kept as strings."""
    if isinstance(x, dict):
        return {str(k): _clean(v) for k, v in x.items()}
    if isinstance(x, list | tuple):
        return [_clean(v) for v in x]
    if isinstance(x, np.generic):
        x = x.item()
    if isinstance(x, float) and not np.isfinite(x):
        return None
    return x


def write_results(study: Study) -> None:
    RES_DIR.mkdir(exist_ok=True)
    with open(RES_DIR / "results.json", "w", encoding="utf-8") as f:
        json.dump(_clean({"facts": study.facts, "tables": study.tables}), f, indent=1, allow_nan=False)
    md = ["# Results", "", f"Monthly data, n = {MAIN_N} months, lag = {LAG}; sample {study.facts['sample']}.", ""]
    for name, t in study.tables.items():
        md += [f"## {name}", "", "| " + " | ".join(t["header"]) + " |", "|" + " --- |" * len(t["header"])]
        md += ["| " + " | ".join(r) + " |" for r in t["rows"]] + [""]
    (RES_DIR / "results.md").write_text("\n".join(md), encoding="utf-8")


def main() -> None:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    study = Study()
    study.run()
    write_results(study)
    print(f"Saved {RES_DIR.name}/results.json and {RES_DIR.name}/results.md")


if __name__ == "__main__":
    main()
