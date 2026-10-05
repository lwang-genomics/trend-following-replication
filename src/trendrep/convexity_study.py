"""Part III: trend convexity (Dao et al., 2016) and trend as a tail hedge for the inverse-vol book.

Run:  uv run trendrep-convexity     (after uv run trendrep-daily has cached the futures data)
"""

import argparse
import json

import numpy as np
import pandas as pd

from . import plots
from .analysis import max_drawdown, sharpe_daily
from .book import inverse_vol_book, vol_scaled
from .config import (
    BOOK_ASSETS,
    CONVEX_TAU,
    FUTURES,
    OVERLAY_SIZES,
    OVERLAY_TAUS,
    PAPER_CTA,
    PAPER_CTA_START,
    RES_DIR,
    SP_SAMPLE,
    STRESS,
    TAU_GRID,
)
from .convexity import (
    GAMMA,
    L,
    binned,
    calibrate_gamma,
    identity_rhs,
    normalised_returns,
    quad_fit,
    tau_prime,
    theory_linear,
    theory_sign,
    trend_frame,
    upsilon,
)
from .futures import (
    benchmark_daily,
    build_daily_panel,
    percent_returns,
    protective_put,
    sp500_total_return,
    tbill_daily,
    trading_costs,
    vix,
)
from .rules import run_market
from .study import _clean, fmt

TAU = CONVEX_TAU
LAM = 0.01 / np.sqrt(TAU)  # daily P&L of a single-asset linear trend ≈ 1% (paper, Fig. 4)
START = "1990-01-01"
OVERLAY_START = "1991-01-01"  # the volatility-scaled combinations need a year of history


def normalised_panel(panel: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """R_k (eq. 9) for each market on its own trading days, zero on days it does not trade."""
    out = {}
    for c in cols:
        p = panel[c].dropna()
        out[c] = normalised_returns(p.diff().iloc[1:])
    return pd.DataFrame(out).reindex(panel.index).fillna(0.0)


def portfolio_trend(R: pd.DataFrame, tau: float, weights: pd.DataFrame | None = None,
                    lam: float = LAM) -> pd.Series:
    """Σ_k w_k λτ L_τ[R_k]_{t-1} R_k,t (eqs. 16-17); w_k = 1/N by default."""
    ema = R.apply(lambda x: pd.Series(L(x.to_numpy(), tau), index=R.index))
    w = weights if weights is not None else pd.DataFrame(1.0 / R.shape[1], index=R.index, columns=R.columns)
    return (w.shift(1) * lam * tau * ema.shift(1) * R).sum(axis=1)


def monthly(d: pd.Series) -> pd.Series:
    return d.resample("MS").sum()


def quarter_stats(daily: pd.Series) -> dict:
    """Annual return, volatility, Sharpe, max drawdown and quarterly tail measures of daily simple returns."""
    q = (1 + daily).resample("QS").prod() - 1
    tail = q.nsmallest(max(1, int(round(0.05 * len(q)))))
    return {"ret": float(daily.mean() * 252), "vol": float(daily.std() * np.sqrt(252)),
            "sr": sharpe_daily(daily), "maxdd": float(np.expm1(max_drawdown(np.log1p(daily)))),
            "worst_q": float(q.min()),
            "cvar_q": float(tail.mean()), "skew_q": float(q.skew())}


def period_return(daily: pd.Series, a: str, b: str) -> float:
    return float((1 + daily.loc[a:b]).prod() - 1)


class ConvexityStudy:
    def __init__(self) -> None:
        self.panel = build_daily_panel()
        self.facts: dict = {"tau": TAU, "tau_prime": tau_prime(TAU), "gamma_paper": GAMMA}
        self.tables: dict = {}

    def run(self) -> None:
        self.single_asset()
        self.horizons()
        self.replicator()
        self.fund_convexity()
        self.rp_bound()
        self.overlay()
        self.options()

    # ------------------------------------------------------------------ section 2 of the paper

    def single_asset(self) -> None:
        """S&P 500 futures, the paper's sample: identity, parabola (linear) and V (sign)."""
        d = self.panel["SP500"].dropna().diff().loc[SP_SAMPLE[0] : SP_SAMPLE[1]]
        r = normalised_returns(d)
        burn = 2 * TAU
        lin = trend_frame(r, TAU, LAM, "linear")
        sgn = trend_frame(r, TAU, 0.01, "sign")
        err = np.abs(L(lin["G"].to_numpy(), tau_prime(TAU)) - identity_rhs(r, TAU, LAM)).max()
        x, y = lin["T"].iloc[burn:].to_numpy(), lin["Gbar"].iloc[burn:].to_numpy()
        fit = quad_fit(x, y)
        xs, ys = sgn["T"].iloc[burn:].to_numpy(), sgn["Gbar"].iloc[burn:].to_numpy()
        A = np.column_stack([np.ones_like(xs), np.abs(xs)])
        (sa, sb), *_ = np.linalg.lstsq(A, ys, rcond=None)
        s_r2 = 1 - (ys - A @ [sa, sb]).var() / ys.var()
        # the naive view: monthly trend P&L against the contemporaneous monthly S&P 500 move
        m = pd.DataFrame({"g": lin["G"], "r": d / d.loc[d.index[burn] :].std()}).iloc[burn:].resample("MS").sum()
        naive = quad_fit(m["r"].to_numpy(), m["g"].to_numpy())
        self.facts["sp"] = {
            "gamma": calibrate_gamma(d), "var_R": float((r.iloc[30:] ** 2).mean()), "identity_err": float(err),
            "lin": fit, "lin_theory_c": upsilon(TAU, LAM), "sign_a": float(sa), "sign_b": float(sb),
            "sign_r2": float(s_r2), "sign_theory_b": 0.01 * np.sqrt(TAU), "naive_monthly": naive,
            "start": f"{d.index[burn]:%Y-%m}", "end": f"{d.index[-1]:%Y-%m}",
        }
        edges = np.linspace(-3.5, 3.5, 29)
        v = self.facts["sp"]["var_R"]
        self.facts["sp"] |= {"lin_theory_a": -upsilon(TAU, LAM) * v,
                             "sign_theory_a": -0.01 * np.sqrt(TAU) * np.sqrt(2 * v / np.pi)}
        plots.smile(binned(x, y, edges), binned(xs, ys, edges), (x, y), (xs, ys),
                    lambda t: theory_linear(t, TAU, LAM, v), lambda t: theory_sign(t, TAU, 0.01, v),
                    "fig15_sp500_smile.png")

    def horizons(self) -> None:
        """Convexity of the S&P 500 trend against the S&P 500 move, by aggregation horizon (non-overlapping)."""
        d = self.panel["SP500"].dropna().diff().loc["1983":]
        r = normalised_returns(d)
        lin = trend_frame(r, TAU, LAM, "linear").iloc[2 * TAU :]
        rows, out = [], {}
        for h in [1, 5, 21, 63, 126, 252]:
            k = np.arange(len(lin)) // h
            g = lin["G"].groupby(k).sum()
            mv = lin["R"].groupby(k).sum() / np.sqrt(h)
            n = lin["R"].groupby(k).size()
            g, mv = g[n == h], mv[n == h]
            f = quad_fit(mv.to_numpy(), g.to_numpy())
            out[h] = f
            rows.append([f"{h}", str(f["n"]), fmt(f["c"] * 100, 2), fmt(f["r2"])])
        self.facts["sp_horizons"] = out
        self.tables["sp_horizons"] = {"header": ["Horizon (days)", "Periods", "Curvature c (×100)", "R²"],
                                      "rows": rows}

    # ------------------------------------------------------------------ section 3 of the paper

    def replicator(self) -> None:
        """Correlation of a simple trend replicator with a managed-futures fund, by time scale τ."""
        fund = monthly(benchmark_daily())
        R16 = normalised_panel(self.panel, PAPER_CTA).loc[PAPER_CTA_START:]
        all_m = [m for ms in FUTURES.values() for m in ms]
        R62 = normalised_panel(self.panel, all_m)
        alive = self.panel[all_m].notna().astype(float)
        w62 = alive.div(alive.sum(axis=1), axis=0).fillna(0.0)
        corr = {"16": {}, "62": {}}
        for tau in TAU_GRID:
            for key, R, w in (("16", R16, None), ("62", R62, w62)):
                rep = monthly(portfolio_trend(R, tau, w if w is None else w.reindex(R.index)))
                df = pd.concat([rep, fund], axis=1).dropna()
                corr[key][tau] = float(df.iloc[:, 0].corr(df.iloc[:, 1]))
        best = max(corr["16"], key=corr["16"].get)
        self.facts["replicator"] = {"corr": corr, "best_tau_16": best, "best_tau_62": max(corr["62"],
                                                                                       key=corr["62"].get)}
        self.R16, self.R62, self.w62 = R16, R62, w62
        plots.corr_by_tau(corr, "fig16_corr_by_tau.png")

    def fund_convexity(self) -> None:
        """The fund's P&L against the S&P 500: naive monthly view vs the paper's aggregated view (Fig. 9)."""
        fund = benchmark_daily()
        sp_d = self.panel["SP500"].dropna().diff()
        T_sp = trend_frame(normalised_returns(sp_d.iloc[1:]), TAU, LAM)["T"]
        g = pd.Series(tau_prime(TAU) * L(fund.to_numpy(), tau_prime(TAU)), index=fund.index)
        df = pd.concat([g, T_sp], axis=1, keys=["Gbar", "T"]).dropna().iloc[TAU:]
        agg = quad_fit(df["T"].to_numpy(), df["Gbar"].to_numpy())
        sp_m = monthly(percent_returns("SP500"))
        mm = pd.concat([monthly(fund), sp_m], axis=1, keys=["f", "s"]).dropna()
        naive = quad_fit(mm["s"].to_numpy(), mm["f"].to_numpy())
        # the same two views for the replicator over a longer sample
        rep = portfolio_trend(self.R16, TAU)
        rg = pd.Series(tau_prime(TAU) * L(rep.to_numpy(), tau_prime(TAU)), index=rep.index)
        rdf = pd.concat([rg, T_sp], axis=1, keys=["Gbar", "T"]).dropna().iloc[2 * TAU :]
        rep_agg = quad_fit(rdf["T"].to_numpy(), rdf["Gbar"].to_numpy())
        rm = pd.concat([monthly(rep), sp_m], axis=1, keys=["f", "s"]).dropna().loc["2003":]
        rep_naive = quad_fit(rm["s"].to_numpy(), rm["f"].to_numpy())
        self.facts["fund_convexity"] = {"naive": naive, "agg": agg, "rep_naive": rep_naive, "rep_agg": rep_agg,
                                        "start": f"{df.index[0]:%Y-%m}", "end": f"{df.index[-1]:%Y-%m}"}
        view_m = "Monthly return vs S&P 500 monthly return"
        view_a = f"P&L over τ' ≈ {tau_prime(TAU):.0f} d vs S&P 500 trend (τ = {TAU} d)"
        self.tables["fund_convexity"] = {
            "header": ["Series", "View", "Sample", "R² (quadratic fit)"],
            "rows": [["Managed-futures fund", view_m, f"{mm.index[0]:%Y}–{mm.index[-1]:%Y}", fmt(naive["r2"])],
                     ["Managed-futures fund", view_a, f"{df.index[0]:%Y}–{df.index[-1]:%Y}", fmt(agg["r2"])],
                     ["Replicator (16 futures)", view_m, f"{rm.index[0]:%Y}–{rm.index[-1]:%Y}", fmt(rep_naive["r2"])],
                     ["Replicator (16 futures)", view_a, f"{rdf.index[0]:%Y}–{rdf.index[-1]:%Y}", fmt(rep_agg["r2"])]],
        }
        plots.fund_convexity(mm, naive, df, agg, "fig17_fund_convexity.png")

    def rp_bound(self) -> None:
        """Eq. (24): the diversified trend's aggregated P&L is bounded below by a parabola in the risk-parity trend."""
        R = self.R16
        N = R.shape[1]
        rep = portfolio_trend(R, TAU)
        gbar = tau_prime(TAU) * L(rep.to_numpy(), tau_prime(TAU))
        g_rp = R.mean(axis=1).to_numpy()
        t_rp = np.sqrt(TAU) * L(g_rp, TAU)
        short = np.mean([L(R[c].to_numpy() ** 2, tau_prime(TAU)) for c in R], axis=0)
        ups = upsilon(TAU, LAM)
        bound = ups * (t_rp**2 - short)
        burn = 2 * TAU
        gap = (gbar - bound)[burn:]
        approx = ups * (t_rp**2 - 1.0)
        self.facts["rp_bound"] = {"share_above_exact": float((gap >= -1e-12).mean()),
                                  "share_above_parabola": float((gbar[burn:] >= approx[burn:]).mean()),
                                  "n": int(len(gap)), "markets": N, "start": f"{R.index[burn]:%Y-%m}"}
        plots.rp_bound(t_rp[burn:], gbar[burn:], ups, "fig18_rp_bound.png")

    # ------------------------------------------------------------------ application: the inverse-vol book

    def overlay_pnl(self, markets: list[str], tau: float, costs: pd.DataFrame) -> pd.Series:
        """Linear trend (eq. 12) on `markets`, equal risk over the markets alive, next-close execution, net of costs."""
        alive = self.panel[markets].notna().sum(axis=1)
        out = {}
        for m in markets:
            p = self.panel[m].dropna()
            d = p.diff()
            sigma = GAMMA * np.sqrt(L(d.fillna(0.0).to_numpy() ** 2, 10))
            sigma[sigma == 0] = np.nan  # before the first price change: no position
            r = normalised_returns(d.iloc[1:]).reindex(p.index).fillna(0.0)
            ema = L(r.to_numpy(), tau)
            dec = pd.Series(LAM * tau * ema / sigma, index=p.index).replace([np.inf, -np.inf], 0.0).fillna(0.0)
            dec = dec / alive.reindex(p.index)
            res = run_market(p, dec, costs.loc[m])
            out[m] = res.gross - res.cost
        return pd.DataFrame(out).reindex(self.panel.index).fillna(0.0).sum(axis=1)

    def overlay(self) -> None:
        costs = trading_costs(self.panel)
        rets = pd.concat([percent_returns(m) for m in BOOK_ASSETS], axis=1).dropna()
        book = inverse_vol_book(rets).loc[START:]
        all_m = [m for ms in FUTURES.values() for m in ms]
        ov = {
            "div_slow": vol_scaled(self.overlay_pnl(all_m, OVERLAY_TAUS["slow"], costs)),
            "div_fast": vol_scaled(self.overlay_pnl(all_m, OVERLAY_TAUS["fast"], costs)),
            "book_slow": vol_scaled(self.overlay_pnl(BOOK_ASSETS, OVERLAY_TAUS["slow"], costs)),
        }
        ov = {k: v.reindex(book.index).fillna(0.0) for k, v in ov.items()}
        labels = {"div_slow": f"diversified trend τ={OVERLAY_TAUS['slow']}",
                  "div_fast": f"diversified trend τ={OVERLAY_TAUS['fast']}",
                  "book_slow": f"3-asset trend τ={OVERLAY_TAUS['slow']}"}
        self.facts["overlay_labels"] = labels
        # every combination is rescaled to the book's 10% ex-ante volatility, so that risks compare
        combos = {"Book alone": book}
        for k in OVERLAY_SIZES[1:]:
            combos[f"Book + {k:g} × {labels['div_slow']}"] = vol_scaled(book + k * ov["div_slow"]).reindex(
                book.index).fillna(0.0)
        combos[f"Book + 1 × {labels['div_fast']}"] = vol_scaled(book + ov["div_fast"]).reindex(book.index).fillna(0.0)
        combos[f"Book + 1 × {labels['book_slow']}"] = vol_scaled(book + ov["book_slow"]).reindex(book.index).fillna(0.0)
        self.combo_main = combos[f"Book + 1 × {labels['div_slow']}"]
        combos = {k: v.loc[OVERLAY_START:] for k, v in combos.items()}
        self.combo_main = self.combo_main.loc[OVERLAY_START:]
        book = book.loc[OVERLAY_START:]
        ov = {k: v.loc[OVERLAY_START:] for k, v in ov.items()}
        st = {k: quarter_stats(v) for k, v in combos.items()}
        st |= {f"Overlay alone, {labels[k]}": quarter_stats(v) for k, v in ov.items()}
        self.facts["overlay"] = {"stats": st, "corr_book": {k: float(monthly(v).corr(monthly(book)))
                                                            for k, v in ov.items()},
                                 "start": f"{book.index[0]:%Y-%m}", "end": f"{book.index[-1]:%Y-%m}"}
        self.tables["overlay"] = {
            "header": ["Portfolio", "Return p.a.", "Vol", "Sharpe", "Max DD", "Worst quarter", "CVaR 5% (quarter)",
                       "Skew (quarter)"],
            "rows": [[k, f"{fmt(v['ret'] * 100, 1)}%", f"{fmt(v['vol'] * 100, 1)}%", fmt(v["sr"]),
                      f"{fmt(v['maxdd'] * 100, 0)}%", f"{fmt(v['worst_q'] * 100, 1)}%",
                      f"{fmt(v['cvar_q'] * 100, 1)}%", fmt(v["skew_q"])] for k, v in st.items()],
        }
        rows, stress = [], {}
        for name, (a, b) in STRESS.items():
            s = {"book": period_return(book, a, b)} | {k: period_return(v, a, b) for k, v in ov.items()}
            stress[name] = s
            rows.append([name, f"{fmt(s['book'] * 100, 1)}%", f"{fmt(s['div_slow'] * 100, 1)}%",
                         f"{fmt(s['div_fast'] * 100, 1)}%", f"{fmt(s['book_slow'] * 100, 1)}%"])
        self.facts["stress"] = stress
        self.tables["stress"] = {"header": ["Episode", "Book", f"Diversified, τ = {OVERLAY_TAUS['slow']}",
                                            f"Diversified, τ = {OVERLAY_TAUS['fast']}",
                                            f"Book's assets, τ = {OVERLAY_TAUS['slow']}"], "rows": rows}
        # conditional view: the overlay's mean return by quintile of the book's return, at two horizons
        cond = {}
        for h, freq in (("1 month", "MS"), ("3 months", "QS")):
            b = (1 + book).resample(freq).prod() - 1
            q = pd.qcut(b, 5, labels=False)
            cond[h] = {k: [float(((1 + v).resample(freq).prod() - 1)[q == i].mean()) for i in range(5)]
                       for k, v in ov.items() if k != "book_slow"}
        self.facts["conditional"] = cond
        plots.overlay_quintiles(cond, labels, "fig19_overlay_quintiles.png")
        plots.overlay_drawdowns(book, self.combo_main, labels["div_slow"], "fig20_overlay_drawdowns.png")

    # ------------------------------------------------------------------ section 4 of the paper: options

    def options(self) -> None:
        spx = sp500_total_return()
        pput = protective_put()
        df = pd.concat([spx, pput], axis=1, keys=["spx", "pput"]).dropna().loc[START:"2024-03-28"]
        r = df.pct_change().dropna()
        rf = tbill_daily(r.index)
        ex = r.sub(rf, axis=0)
        # implied vs realised variance: VIX² against the next 21 trading days' realised variance
        v = vix().reindex(r.index).ffill()
        rv = r["spx"].rolling(21).var().shift(-21) * 252
        vr = pd.concat([v / 100, np.sqrt(rv)], axis=1, keys=["iv", "rv"]).dropna()
        self.facts["vrp"] = {"iv": float(np.sqrt((vr["iv"] ** 2).mean())), "rv": float(np.sqrt((vr["rv"] ** 2).mean())),
                             "share_iv_above": float((vr["iv"] > vr["rv"]).mean()),
                             "var_ratio": float((vr["iv"] ** 2).mean() / (vr["rv"] ** 2).mean())}
        costs = trading_costs(self.panel)
        all_m = [m for ms in FUTURES.values() for m in ms]
        ov_sp = vol_scaled(self.overlay_pnl(["SP500"], CONVEX_TAU, costs)).reindex(r.index).fillna(0.0)
        ov_div = vol_scaled(self.overlay_pnl(all_m, CONVEX_TAU, costs)).reindex(r.index).fillna(0.0)
        strat = {"S&P 500": ex["spx"], "S&P 500 + 5% puts (CBOE PPUT)": ex["pput"],
                 "S&P 500 + trend on the S&P 500": ex["spx"] + ov_sp,
                 "S&P 500 + diversified trend": ex["spx"] + ov_div}
        st = {k: quarter_stats(v) for k, v in strat.items()}
        rows = []
        for k, v in st.items():
            row = [k, f"{fmt(v['ret'] * 100, 1)}%", f"{fmt(v['vol'] * 100, 1)}%", fmt(v["sr"]),
                   f"{fmt(v['maxdd'] * 100, 0)}%"]
            row += [f"{fmt(period_return(strat[k], *STRESS[e]) * 100, 0)}%" for e in
                    ("2007–09 financial crisis", "2020 COVID crash", "2022 rate shock")]
            rows.append(row)
        put_cost = st["S&P 500"]["ret"] - st["S&P 500 + 5% puts (CBOE PPUT)"]["ret"]
        self.facts["options"] = {"stats": st, "put_cost": put_cost}
        self.tables["options"] = {"header": ["Excess return over T-bills", "Return p.a.", "Vol", "Sharpe", "Max DD",
                                             "2007–09", "COVID 2020", "2022"], "rows": rows}
        plots.protection(strat, "fig21_protection.png")


def write_results(study: ConvexityStudy) -> None:
    RES_DIR.mkdir(exist_ok=True)
    with open(RES_DIR / "results_convexity.json", "w", encoding="utf-8") as f:
        json.dump(_clean({"facts": study.facts, "tables": study.tables}), f, indent=1, allow_nan=False)
    md = ["# Results, Part III", ""]
    for name, t in study.tables.items():
        md += [f"## {name}", "", "| " + " | ".join(t["header"]) + " |", "|" + " --- |" * len(t["header"])]
        md += ["| " + " | ".join(r) + " |" for r in t["rows"]] + [""]
    (RES_DIR / "results_convexity.md").write_text("\n".join(md), encoding="utf-8")


def main() -> None:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    study = ConvexityStudy()
    study.run()
    write_results(study)
    print(f"Saved {RES_DIR.name}/results_convexity.json and {RES_DIR.name}/results_convexity.md")


if __name__ == "__main__":
    main()
