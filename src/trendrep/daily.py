"""Part II: Clenow's practitioner rules against the paper's signal, on daily back-adjusted futures.

Run:  uv run trendrep-daily     (downloads the futures data once into data/raw/futures/)
"""

import argparse
import json

import numpy as np
import pandas as pd

from . import plots
from .analysis import max_drawdown, ols, sharpe, sharpe_daily, sharpe_diff_bootstrap
from .config import (
    BENCHMARK,
    BENCHMARK_NAME,
    CLENOW,
    COST_STRESS,
    DAILY_BOOT_BLOCK,
    DAILY_BOOT_N,
    DAILY_SECTORS,
    DAILY_SPLIT,
    DAILY_START,
    EMA_DAYS,
    FUTURES,
    FUTURES_COMMIT,
    GRID_BREAKOUT,
    GRID_STOP,
    LAG,
    MAIN_EMA_DAYS,
    MAIN_N,
    PUBLICATION_END,
    RES_DIR,
    SPOT_TO_FUTURES,
    TRUE_RANGE_RATIO,
    VOL_DISPLAY,
    ClenowRules,
)
from .futures import benchmark_monthly, build_daily_panel, month_end_points, trading_costs, true_range_ratio
from .rules import VARIANTS, clenow_decisions, ema_decisions, run_panel
from .signal import panel_pnl
from .study import _clean, fmt

PAPER = f"Paper EMA, {MAIN_EMA_DAYS} d"
CORE = "Clenow core"
IN_END = (pd.Timestamp(DAILY_SPLIT) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")


def monthly(daily: pd.Series) -> pd.Series:
    return daily.resample("MS").sum()


def scaled(daily: pd.Series) -> pd.Series:
    """The same P&L at VOL_DISPLAY annual volatility (ex post, over the whole sample): display only."""
    return daily * VOL_DISPLAY / (daily.std() * np.sqrt(252))


class DailyStudy:
    def __init__(self) -> None:
        self.panel = build_daily_panel()
        self.costs = trading_costs(self.panel)
        self.alive = self.panel.notna().loc[DAILY_START:]
        self.facts: dict = {"futures_commit": FUTURES_COMMIT, "rules": CLENOW.__dict__}
        self.tables: dict = {}
        self.res = {v: run_panel(self.panel, lambda p, v=v: clenow_decisions(p, variant=v), self.costs)
                    for v in VARIANTS}
        self.ema = {n: run_panel(self.panel, lambda p, n=n: ema_decisions(p, n), self.costs) for n in EMA_DAYS}
        self.res[PAPER] = self.ema[MAIN_EMA_DAYS]
        net = self.daily(PAPER)
        self.facts["sample"] = f"{net.index.min():%Y-%m-%d} → {net.index.max():%Y-%m-%d}"
        self.facts["n_markets"] = int(self.panel.shape[1])

    def daily(self, name: str, cost_mult: float = 1.0, cols: list[str] | None = None) -> pd.Series:
        return self.res[name].daily(cost_mult, cols).loc[DAILY_START:]

    def run(self) -> None:
        self.universe()
        self.rule_ladder()
        self.horizons()
        self.sectors()
        self.spanning()
        self.robustness()
        self.yearly()
        self.benchmark()
        self.spot_vs_futures()

    # ------------------------------------------------------------------ data

    def universe(self) -> None:
        rows = []
        for sec, ms in FUTURES.items():
            first = [self.panel[m].first_valid_index() for m in ms]
            rows.append([sec, str(len(ms)), f"{min(first):%Y}", f"{max(first):%Y}",
                         fmt(self.costs.loc[ms, "cost_atr"].median() * 100, 1), ", ".join(ms)])
        self.tables["universe"] = {"header": ["Sector", "Markets", "First data", "Last start", "Cost (% ATR)",
                                              "Markets (pysystemtrade names)"], "rows": rows}
        self.facts["cost_atr_median"] = float(self.costs["cost_atr"].median())
        self.facts["cost_atr_max"] = {m: float(v) for m, v in self.costs["cost_atr"].nlargest(3).items()}
        self.facts["markets_alive_1990"] = int(self.alive.iloc[0].sum())
        tr = true_range_ratio()
        self.facts["true_range"] = {"used": TRUE_RANGE_RATIO, "median": float(np.median(list(tr.values()))),
                                    "min": float(min(tr.values())), "max": float(max(tr.values())), "n": len(tr)}

    # ------------------------------------------------------------------ the rules

    def behaviour(self, name: str) -> dict:
        held = self.res[name].held.loc[DAILY_START:]
        in_mkt = (held != 0) & self.alive
        changes = (np.sign(held).diff().fillna(0) != 0) & self.alive
        market_years = self.alive.to_numpy().sum() / 252
        return {"in_market": float(in_mkt.to_numpy().sum() / self.alive.to_numpy().sum()),
                "changes_per_market_year": float(changes.to_numpy().sum() / market_years),
                "avg_positions": float(in_mkt.sum(axis=1).mean())}

    def rule_stats(self, name: str) -> dict:
        g, n, s = (self.daily(name, c) for c in (0.0, 1.0, COST_STRESS))
        return {
            "sr_gross_in": sharpe_daily(g.loc[:IN_END]), "sr_net_in": sharpe_daily(n.loc[:IN_END]),
            "sr_stress_in": sharpe_daily(s.loc[:IN_END]), "sr_net_post": sharpe_daily(n.loc[DAILY_SPLIT:]),
            "sr_gross_post": sharpe_daily(g.loc[DAILY_SPLIT:]), "sr_net_full": sharpe_daily(n),
            "vol": float(n.std() * np.sqrt(252)), "maxdd_10": max_drawdown(scaled(n)),
            "skew_m": float(monthly(n).skew()),
            "corr_paper": float(monthly(n).corr(monthly(self.daily(PAPER)))),
            "corr_core": float(monthly(n).corr(monthly(self.daily(CORE)))),
        } | self.behaviour(name)

    def rule_ladder(self) -> None:
        names = [*VARIANTS, PAPER]
        st = {k: self.rule_stats(k) for k in names}
        self.facts["rules_stats"] = st
        self.tables["ladder"] = {
            "header": ["Rule", "SR gross", "SR net", f"SR net, costs ×{COST_STRESS:.0f}", "SR net 2014–24",
                       "Max DD (10% vol)", "Skew (monthly)"],
            "rows": [[k, fmt(v["sr_gross_in"]), fmt(v["sr_net_in"]), fmt(v["sr_stress_in"]), fmt(v["sr_net_post"]),
                      f"{fmt(v['maxdd_10'] * 100, 0)}%", fmt(v["skew_m"])] for k, v in st.items()],
        }
        self.tables["behaviour"] = {
            "header": ["Rule", "Vol (risk 0.2%)", "Time in market", "Changes per market-year", "Open positions",
                       "Corr. with paper EMA", "Corr. with Clenow"],
            "rows": [[k, f"{fmt(v['vol'] * 100, 0)}%", f"{fmt(v['in_market'] * 100, 0)}%",
                      fmt(v["changes_per_market_year"], 1), fmt(v["avg_positions"], 0), fmt(v["corr_paper"]),
                      fmt(v["corr_core"])] for k, v in st.items()],
        }
        plots.daily_equity({k: scaled(self.daily(k)) for k in (PAPER, CORE, "Filter only")}, DAILY_SPLIT,
                           "fig09_daily_equity.png")
        plots.rule_ladder({k: (v["sr_net_in"], v["sr_net_post"]) for k, v in st.items()}, "fig10_rule_ladder.png")

    def horizons(self) -> None:
        rows, out = [], {}
        core = monthly(self.daily(CORE))
        for n in EMA_DAYS:
            g = self.ema[n].daily(0.0).loc[DAILY_START:]
            d = self.ema[n].daily(1.0).loc[DAILY_START:]
            out[n] = {"sr_gross_in": sharpe_daily(g.loc[:IN_END]), "sr_net_in": sharpe_daily(d.loc[:IN_END]),
                      "sr_net_post": sharpe_daily(d.loc[DAILY_SPLIT:]), "corr_core": float(monthly(d).corr(core))}
            rows.append([f"{n} ({n / 21:.0f} months)" if n >= 42 else f"{n} (1 month)", fmt(out[n]["sr_gross_in"]),
                         fmt(out[n]["sr_net_in"]), fmt(out[n]["sr_net_post"]), fmt(out[n]["corr_core"])])
        self.facts["ema_horizons"] = out
        self.tables["ema_horizons"] = {"header": ["EMA n (days)", "SR gross", "SR net", "SR net 2014–24",
                                                  f"Corr. with {CORE}"], "rows": rows}

    def sectors(self) -> None:
        rows, out = [], {}
        for sec in DAILY_SECTORS:
            cols = FUTURES[sec]
            r = {}
            for k in (CORE, PAPER):
                d = self.daily(k, 1.0, cols)
                r[k] = (sharpe_daily(d.loc[:IN_END]), sharpe_daily(d.loc[DAILY_SPLIT:]))
            out[sec] = r
            rows.append([sec, str(len(cols)), fmt(r[CORE][0]), fmt(r[CORE][1]), fmt(r[PAPER][0]), fmt(r[PAPER][1])])
        self.facts["daily_sectors"] = out
        self.tables["daily_sectors"] = {
            "header": ["Sector", "Markets", "Clenow 1990–2013", "Clenow 2014–24", "Paper EMA 1990–2013",
                       "Paper EMA 2014–24"], "rows": rows}
        plots.daily_sectors(out, CORE, PAPER, "fig14_daily_sectors.png")

    # ------------------------------------------------------------------ does the practitioner add anything?

    def spanning(self) -> None:
        core, paper = monthly(self.daily(CORE)), monthly(self.daily(PAPER))
        emas = pd.DataFrame({f"EMA{n}": monthly(self.ema[n].daily(1.0).loc[DAILY_START:]) for n in EMA_DAYS})
        rows, out = [], {}
        cases = [(f"{CORE} on paper EMA (100 d)", core, paper.rename("paper").to_frame()),
                 (f"{CORE} on 4 EMA horizons", core, emas),
                 (f"Paper EMA (100 d) on {CORE}", paper, core.rename("core").to_frame())]
        for label, y, X in cases:
            for per, (a, b) in {"1990–2013": (DAILY_START, IN_END), "1990–2024": (DAILY_START, None)}.items():
                r = ols(y.loc[a:b], X.loc[a:b])
                appraisal = r["coef"]["alpha"] / r["resid_sd"] * np.sqrt(12)  # Sharpe of the unexplained part
                out[f"{label} | {per}"] = {"alpha_t": r["t"]["alpha"], "appraisal": float(appraisal), "r2": r["r2"]}
                rows.append([label, per, fmt(r["t"]["alpha"], 1), fmt(appraisal), fmt(r["r2"])])
        self.facts["spanning"] = out
        self.tables["spanning"] = {"header": ["Regression (monthly, net)", "Period", "t(alpha)", "Appraisal ratio",
                                              "R²"], "rows": rows}
        boot = {}
        for per, (a, b) in {"in": (DAILY_START, IN_END), "post": (DAILY_SPLIT, None)}.items():
            boot[per] = sharpe_diff_bootstrap(self.daily(CORE).loc[a:b], self.daily(PAPER).loc[a:b],
                                              DAILY_BOOT_BLOCK, DAILY_BOOT_N)
        self.facts["sr_diff_core_minus_paper"] = boot

    def robustness(self) -> None:
        grid = {"in": np.full((len(GRID_BREAKOUT), len(GRID_STOP)), np.nan)}
        grid["post"] = grid["in"].copy()
        for i, b in enumerate(GRID_BREAKOUT):
            for j, s in enumerate(GRID_STOP):
                rules = ClenowRules(breakout=b, stop_atr=s)
                r = run_panel(self.panel, lambda p, rules=rules: clenow_decisions(p, rules), self.costs)
                d = r.daily(1.0).loc[DAILY_START:]
                grid["in"][i, j], grid["post"][i, j] = sharpe_daily(d.loc[:IN_END]), sharpe_daily(d.loc[DAILY_SPLIT:])
        self.facts["grid"] = {"breakout": GRID_BREAKOUT, "stop_atr": GRID_STOP,
                              "in": grid["in"].tolist(), "post": grid["post"].tolist(),
                              "in_min": float(grid["in"].min()), "in_max": float(grid["in"].max()),
                              "post_min": float(grid["post"].min()), "post_max": float(grid["post"].max()),
                              "rank_corr": float(pd.Series(grid["in"].ravel()).corr(pd.Series(grid["post"].ravel()),
                                                                                      method="spearman"))}
        plots.robustness(grid, GRID_BREAKOUT, GRID_STOP, "fig11_robustness.png", (CLENOW.breakout, CLENOW.stop_atr))

    def yearly(self) -> None:
        y = {k: scaled(self.daily(k)).groupby(lambda d: d.year).sum() for k in (CORE, PAPER)}
        y = pd.DataFrame(y).loc[:2023]  # 2024 has one quarter only
        self.facts["yearly"] = {k: {int(i): float(v) for i, v in y[k].items()} for k in y}
        self.facts["yearly_losing"] = {k: int((y[k] < 0).sum()) for k in y}
        self.facts["yearly_corr"] = float(y[CORE].corr(y[PAPER]))
        plots.yearly(y, DAILY_SPLIT, "fig12_yearly.png")

    def benchmark(self) -> None:
        fund = benchmark_monthly()
        m = pd.DataFrame({k: monthly(self.daily(k)) for k in [*VARIANTS, PAPER]}).loc[fund.index.min():]
        df = pd.concat([fund, m], axis=1).dropna()
        out = {"start": f"{df.index.min():%Y-%m}", "end": f"{df.index.max():%Y-%m}", "months": len(df),
               "sr_fund": sharpe(df[BENCHMARK])}
        out["corr"] = {k: float(df[BENCHMARK].corr(df[k])) for k in m}
        out["sr"] = {k: sharpe(df[k]) for k in m}
        out["r2_paper_and_core"] = ols(df[BENCHMARK], df[[PAPER, CORE]])["r2"]
        self.facts["benchmark"] = out | {"name": BENCHMARK_NAME}
        vol = df[BENCHMARK].std()
        plots.benchmark(df[BENCHMARK], {k: df[k] * vol / df[k].std() for k in (PAPER, CORE)}, BENCHMARK_NAME,
                        "fig13_benchmark.png")

    # ------------------------------------------------------------------ back to Part I: spot vs futures

    def spot_vs_futures(self) -> None:
        """Part I's monthly rule (n = 5, lag 1) on spot commodity prices vs month-end futures, same months."""
        try:
            from .data import build_panel

            spot = build_panel()
        except OSError:  # Part I data unavailable (offline)
            return
        fut = month_end_points(self.panel[list(SPOT_TO_FUTURES.values())])
        rows, agg = [], {"spot": [], "fut": [], "fut0": [], "spot_mu": [], "fut_mu": []}
        out = {}
        for s_name, f_name in SPOT_TO_FUTURES.items():
            pair = pd.concat([spot[s_name], fut[f_name]], axis=1, keys=["spot", "fut"]).dropna()
            res = {}
            for k in ("spot", "fut"):
                p = pair[[k]]
                res[k] = panel_pnl(p, MAIN_N, LAG)[k]
                res[k + "_mu"] = panel_pnl(p, MAIN_N, LAG, long_only=True)[k]
            # month-end data have no averaging artefact: lag 0 is the like-for-like of averaged data at lag 1
            res["fut0"] = panel_pnl(pair[["fut"]], MAIN_N, 0)["fut"]
            both = pd.DataFrame(res).dropna().loc[DAILY_START:PUBLICATION_END]
            for k in agg:
                agg[k].append(both[k])
            out[s_name] = {k: sharpe(both[k]) for k in res} | {"from": f"{both.index.min():%Y}"}
            o = out[s_name]
            rows.append([s_name.title(), f_name, f"{both.index.min():%Y}", fmt(o["spot"]), fmt(o["fut"]),
                         fmt(o["fut0"]), fmt(o["spot_mu"]), fmt(o["fut_mu"])])
        tot = {k: sharpe(pd.concat(v, axis=1).sum(axis=1, min_count=1).dropna()) for k, v in agg.items()}
        rows.append(["All seven", "", "", *(fmt(tot[k]) for k in ("spot", "fut", "fut0", "spot_mu", "fut_mu"))])
        self.facts["spot_vs_futures"] = out | {"all": tot}
        self.tables["spot_vs_futures"] = {
            "header": ["Commodity", "Futures", "From", "Trend SR, spot (avg., lag 1)", "Trend SR, futures (lag 1)",
                       "Trend SR, futures (lag 0)", "Long-only SR, spot", "Long-only SR, futures"], "rows": rows}


def write_results(study: DailyStudy) -> None:
    RES_DIR.mkdir(exist_ok=True)
    with open(RES_DIR / "results_daily.json", "w", encoding="utf-8") as f:
        json.dump(_clean({"facts": study.facts, "tables": study.tables}), f, indent=1, allow_nan=False)
    md = ["# Results, Part II", "", f"Daily futures, sample {study.facts['sample']}; in-sample to {IN_END}.", ""]
    for name, t in study.tables.items():
        md += [f"## {name}", "", "| " + " | ".join(t["header"]) + " |", "|" + " --- |" * len(t["header"])]
        md += ["| " + " | ".join(r) + " |" for r in t["rows"]] + [""]
    (RES_DIR / "results_daily.md").write_text("\n".join(md), encoding="utf-8")


def main() -> None:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    study = DailyStudy()
    study.run()
    write_results(study)
    print(f"Saved {RES_DIR.name}/results_daily.json and {RES_DIR.name}/results_daily.md")


if __name__ == "__main__":
    main()
