"""Daily trading rules on back-adjusted futures (Part II): Clenow's core model, its parts, and the paper's signal.

Every rule maps one market's daily closes to a *decision*: the signed position, in units of capital
per price point, wanted after the close of day t, using closes up to t only. It is traded EXEC_LAG
days later at that day's close. Positions are risk-sized, so a market's P&L is in fractions of capital:

    P&L(t+1) = units held after close t × (p(t+1) − p(t))

All volatility estimates use closes only (the data have no highs and lows). The book's average true
range is estimated as TRUE_RANGE_RATIO × the mean absolute daily close-to-close change, the ratio being
measured on futures with daily highs and lows (config.TRUE_RANGE_RATIO).
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import CLENOW, EXEC_LAG, TRUE_RANGE_RATIO, ClenowRules
from .futures import zero_safe
from .signal import ema

VARIANTS = ["Filter only", "Breakout only", "Filter + breakout", "Clenow core"]


def ema_span(x: pd.Series, days: int) -> pd.Series:
    """The trading-platform EMA of a `days`-day moving average: weight 2 / (days + 1) on the newest close."""
    return x.ewm(span=days, adjust=False).mean()


def atr(p: pd.Series, window: int) -> pd.Series:
    """Average true range estimated from closes: TRUE_RANGE_RATIO × rolling mean of |Δp| (points)."""
    return TRUE_RANGE_RATIO * zero_safe(p.diff().abs().rolling(window).mean())


def clenow_decisions(p: pd.Series, rules: ClenowRules = CLENOW, variant: str = "Clenow core") -> pd.Series:
    """Signed position (units of capital per point) decided at each close.

    Variants, each adding one component of the core model:
      Filter only        always positioned with the EMA filter; reverses when it flips
      Breakout only      long after a `breakout`-day high close, short after a low close (stop and reverse)
      Filter + breakout  enters on a breakout in the filter's direction, exits when the filter flips
      Clenow core        enters on a breakout in the filter's direction, exits on the ATR trailing stop
    The position size is fixed at entry (risk / ATR on the entry day) and kept until exit.
    """
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant!r}")
    filt = np.sign(ema_span(p, rules.fast) - ema_span(p, rules.slow))
    filt.iloc[: rules.slow] = np.nan  # EMAs need `slow` days of history
    hi = p.rolling(rules.breakout).max()
    lo = p.rolling(rules.breakout).min()
    a = atr(p, rules.atr_window)

    px, f, h, lw, av = (x.to_numpy(dtype=float) for x in (p, filt, hi, lo, a))
    out = np.zeros(len(px))
    state, units, best = 0, 0.0, np.nan
    use_filter = variant != "Breakout only"
    for t in range(len(px)):
        if not (np.isfinite(av[t]) and np.isfinite(h[t]) and np.isfinite(f[t])):
            out[t] = state * units
            continue
        up, down = px[t] >= h[t], px[t] <= lw[t]
        want = 0
        if variant == "Filter only":
            want = int(f[t])
        elif variant == "Breakout only":
            want = 1 if up else -1 if down else state
        else:
            if state != 0:
                if variant == "Clenow core":
                    best = max(best, px[t]) if state > 0 else min(best, px[t])
                    stopped = (px[t] <= best - rules.stop_atr * av[t]) if state > 0 else (
                        px[t] >= best + rules.stop_atr * av[t])
                    want = 0 if stopped else state
                else:  # filter + breakout: hold until the filter turns against the position
                    want = state if f[t] == state else 0
            if want == 0 and use_filter:
                if f[t] > 0 and up:
                    want = 1
                elif f[t] < 0 and down:
                    want = -1
        if want != state:
            state = want
            units = rules.risk / av[t] if state != 0 else 0.0
            best = px[t]
        out[t] = state * units
    return pd.Series(out, index=p.index)


def ema_decisions(p: pd.Series, n: int, risk: float = CLENOW.risk) -> pd.Series:
    """The paper's signal on daily data: sign(p − EMA_n[p]) / σ_n, σ_n = EMA_n of |Δp|, rebalanced daily.

    EMA_n uses the paper's convention (weight 1/n on the newest value), so n = 100 days ≈ 5 months.
    Positions carry the same risk per market as Clenow's (risk per true-range ATR ≈ TRUE_RANGE_RATIO σ_n).
    """
    sigma = zero_safe(ema(p.diff().abs(), n))
    pos = np.sign(p - ema(p, n)) * risk / (TRUE_RANGE_RATIO * sigma)
    pos.iloc[: 2 * n] = np.nan  # warm-up
    return pos.fillna(0.0)


@dataclass
class MarketResult:
    gross: pd.Series  # P&L before costs, fraction of capital
    cost: pd.Series  # trading and roll costs, fraction of capital (positive number)
    held: pd.Series  # units held after each close


def run_market(p: pd.Series, decisions: pd.Series, cost: pd.Series, lag: int = EXEC_LAG) -> MarketResult:
    """P&L and costs of trading `decisions` on market `p` with an execution lag of `lag` days.

    cost: one row of futures.trading_costs(). A trade of Δu units costs |Δu| × c points, with c the
    market's cost per side in ATR units times the current ATR; holding u units costs 2 × |u| × c per
    roll, spread over the year.
    """
    p = p.dropna()
    held = decisions.reindex(p.index).shift(lag).fillna(0.0)
    gross = held.shift(1).fillna(0.0) * p.diff().fillna(0.0)
    per_side = cost["cost_atr"] * p.diff().abs().rolling(CLENOW.atr_window, min_periods=20).mean().bfill()
    trade = held.diff().abs().fillna(held.abs())
    roll = held.abs() * 2 * per_side * cost["rolls_per_year"] / 252
    return MarketResult(gross, trade * per_side + roll, held)


@dataclass
class PanelResult:
    gross: pd.DataFrame
    cost: pd.DataFrame
    held: pd.DataFrame

    def net(self, cost_mult: float = 1.0) -> pd.DataFrame:
        return self.gross - cost_mult * self.cost

    def daily(self, cost_mult: float = 1.0, cols: list[str] | None = None) -> pd.Series:
        """Portfolio P&L per day (fraction of capital): the sum over markets."""
        x = self.net(cost_mult)
        return (x if cols is None else x[cols]).sum(axis=1)


def run_panel(panel: pd.DataFrame, rule, costs: pd.DataFrame, lag: int = EXEC_LAG) -> PanelResult:
    """Apply `rule` (closes -> decisions) to every market of `panel` and collect the results."""
    res = {}
    for m in panel:
        p = panel[m].dropna()
        res[m] = run_market(p, rule(p), costs.loc[m], lag)
    frame = {k: pd.DataFrame({m: getattr(r, k) for m, r in res.items()}).reindex(panel.index).fillna(0.0)
             for k in ("gross", "cost", "held")}
    return PanelResult(**frame)
