"""Trend signal and fictitious P&L of Lempérière et al. (2014), eqs. (1)-(2).

For a monthly price series p and EMA decay n (months):

    <p>_n(t)  = EMA of past prices, excluding p(t)
    sigma_n(t) = EMA of absolute monthly price changes |p(t) - p(t-1)|
    s_n(t)    = (p(t-1) - <p>_n(t-1)) / sigma_n(t-1)                   (1)
    Q_n(t)    = sum_{t'<t} sign[s_n(t')] (p(t'+1) - p(t')) / sigma_n(t'-1)  (2)

As printed, eq. (2) pairs the signal built from p(t'-1) with the price change
p(t') -> p(t'+1): the position is held one month after the information date
(`lag=1`). `lag=0` trades the very next month instead. With monthly-average data
(OECD, World Bank), `lag=0` inherits the spurious lag-1 autocorrelation of
averaged prices (Working, 1960); see tests/test_signal.py.

EMA convention: weight 1/n on the newest observation, i.e. x_ema(t) = (1-1/n) x_ema(t-1) + x(t)/n.

Stale-price filter: a market is traded in month i only if its price changed in at least
STALE_MIN_MOVES of the trailing STALE_WINDOW months. Administered prices (grain support
programmes, oil price controls) otherwise shrink sigma towards zero, and the first real
move then produces a P&L of hundreds of sigmas (corn, January 1972: −467σ). The paper
requires "prices actually moving (no gaps)" for the same reason.
"""

import numpy as np
import pandas as pd

WARMUP = 24  # months of history before the first position
STALE_WINDOW = 12
STALE_MIN_MOVES = 10


def ema(x: pd.Series, n: float) -> pd.Series:
    """Exponential moving average with weight 1/n on the newest value, started at the first value."""
    return x.ewm(alpha=1.0 / n, adjust=False).mean()


def trend_signal(p: pd.Series, n: float) -> pd.DataFrame:
    """Signal x(i) = (p(i) - <p>(i)) / sigma(i) known at the close of month i.

    <p>(i) averages prices strictly before i; sigma(i) averages |Δp| up to and including i.
    Returns columns: signal, sigma (both NaN during the warm-up, when sigma == 0, or when the
    price is stale; see the module docstring).
    """
    p = p.dropna()
    ref = ema(p, n).shift(1)  # EMA of p(<i)
    sigma = ema(p.diff().abs(), n)
    sigma = sigma.where(sigma > 0)
    x = (p - ref) / sigma
    moving = (p.diff() != 0).rolling(STALE_WINDOW).sum() >= STALE_MIN_MOVES
    valid = (np.arange(len(p)) >= WARMUP) & moving.to_numpy()
    return pd.DataFrame({"signal": x.where(valid), "sigma": sigma.where(valid)})


def trend_pnl(p: pd.Series, n: float, lag: int = 1, long_only: bool = False) -> pd.DataFrame:
    """Monthly fictitious P&L of the risk-managed trend (or long-only) strategy.

    Position sign[x(i)] (or +1 if `long_only`) of size 1/sigma(i), held over the price
    change from month i+lag to i+lag+1; the P&L is labelled by the month it is realised.
    Returns columns: pnl, signal, move (= normalised price change used for the P&L).
    """
    p = p.dropna()
    sig = trend_signal(p, n)
    move = (p.shift(-(lag + 1)) - p.shift(-lag)) / sig["sigma"]  # (p(i+lag+1) - p(i+lag)) / sigma(i)
    pos = pd.Series(1.0, index=p.index) if long_only else np.sign(sig["signal"])
    pnl = pos * move
    out = pd.DataFrame({"pnl": pnl, "signal": sig["signal"], "move": move})
    out.index = p.index.to_series().shift(-(lag + 1)).to_numpy()  # realisation month
    return out.dropna()


def panel_pnl(panel: pd.DataFrame, n: float, lag: int = 1, long_only: bool = False) -> pd.DataFrame:
    """Per-asset monthly P&L (assets as columns), each from its own first valid month."""
    return pd.DataFrame({c: trend_pnl(panel[c], n, lag, long_only)["pnl"] for c in panel.columns})


def pooled_signal_moves(panel: pd.DataFrame, n: float, lag: int = 1) -> pd.DataFrame:
    """All (signal, next normalised move) pairs across assets, for the saturation fit."""
    parts = [trend_pnl(panel[c], n, lag)[["signal", "move"]].assign(asset=c) for c in panel.columns]
    return pd.concat(parts)
