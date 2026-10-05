"""The long-only book of the companion study inverse-vol-futures-overlay (Part III).

Same rules as https://github.com/lwang-genomics/inverse-vol-futures-overlay (backtest.py there):
inverse-volatility weights from the trailing 252 days, quarter-end rebalancing, drifting weights
in between, 10 bp per unit traded, scaled to an ex-ante 10% volatility from the trailing
covariance with leverage capped at 3. Here it runs on back-adjusted futures from 1990.
"""

import numpy as np
import pandas as pd

LOOKBACK_DAYS = 252
MIN_TRAIN_DAYS = 200
COST_BPS = 10.0
EVERY_MONTHS = 3
VOL_TARGET = 0.10
MAX_LEVERAGE = 3.0


def inverse_vol_weights(log_returns: pd.DataFrame) -> pd.Series:
    """w_i ∝ 1/σ_i, normalised to sum to one."""
    inv = 1.0 / log_returns.std()
    return inv / inv.sum()


def rebalance_dates(index: pd.DatetimeIndex, every_months: int) -> pd.DatetimeIndex:
    """Last trading day of every `every_months`-th month (Mar/Jun/Sep/Dec for 3)."""
    last = pd.Series(index, index=index).groupby(index.to_period("M")).last()
    return pd.DatetimeIndex([d for p, d in last.items() if p.month % every_months == 0])


def inverse_vol_book(rets: pd.DataFrame, every_months: int = EVERY_MONTHS, cost_bps: float = COST_BPS,
                     vol_target: float | None = VOL_TARGET, lookback: int = LOOKBACK_DAYS,
                     min_train: int = MIN_TRAIN_DAYS, max_leverage: float = MAX_LEVERAGE) -> pd.Series:
    """Daily simple returns (after costs) of the walk-forward inverse-vol book on daily simple returns."""
    log_r = np.log1p(rets)
    idx = rets.index
    targets: dict[int, np.ndarray] = {}
    for d in rebalance_dates(idx, every_months):
        i = idx.get_loc(d)
        train = log_r.iloc[max(0, i - lookback + 1) : i + 1]
        if len(train) < min_train:
            continue
        w = inverse_vol_weights(train).to_numpy()
        if vol_target is not None:
            ex_ante = float(np.sqrt(w @ train.cov().to_numpy() @ w * 252))
            w = w * min(max_leverage, vol_target / ex_ante)
        targets[i] = w
    R = rets.to_numpy()
    port = np.full(len(idx), np.nan)
    w = None
    for i in range(len(idx)):
        if w is not None:
            r_p = float(w @ R[i])
            w = w * (1.0 + R[i]) / (1.0 + r_p)
            port[i] = r_p
        if i in targets:
            tgt = targets[i]
            if w is not None:
                port[i] = (1.0 + port[i]) * (1.0 - cost_bps / 1e4 * float(np.abs(tgt - w).sum())) - 1.0
            w = tgt.copy()
    return pd.Series(port, index=idx).iloc[min(targets) + 1 :]


def vol_scaled(pnl: pd.Series, target: float = VOL_TARGET, window: int = LOOKBACK_DAYS,
               max_scale: float = 10.0) -> pd.Series:
    """Scale a daily P&L stream to an ex-ante volatility `target`, from its trailing realised volatility.

    The scale for day t uses P&L up to day t-1 only.
    """
    vol = pnl.rolling(window, min_periods=min(window, MIN_TRAIN_DAYS)).std().shift(1) * np.sqrt(252)
    return (pnl * (target / vol).clip(upper=max_scale)).dropna()
