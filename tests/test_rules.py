import numpy as np
import pandas as pd
import pytest

from trendrep.analysis import sharpe_daily
from trendrep.config import TRUE_RANGE_RATIO, ClenowRules
from trendrep.rules import VARIANTS, atr, clenow_decisions, ema_decisions, ema_span, run_market

RULES = ClenowRules(fast=5, slow=10, breakout=10, atr_window=10, stop_atr=3.0, risk=0.002)
DAYS = pd.bdate_range("2000-01-03", periods=3000)
COST = pd.Series({"cost_atr": 0.0, "rolls_per_year": 4})


def walk(seed: int, n: int = 3000, drift: float = 0.0) -> pd.Series:
    rng = np.random.default_rng(seed)
    return pd.Series(1000 + np.cumsum(rng.normal(drift, 1.0, n)), index=DAYS[:n])


def test_clenow_entries_exits_and_sizes_follow_the_rules():
    """Check every entry, exit and holding day of the core model against the rules, one by one."""
    p = walk(0, drift=0.02)
    pos = clenow_decisions(p, RULES)
    filt = np.sign(ema_span(p, RULES.fast) - ema_span(p, RULES.slow))
    hi, lo = p.rolling(RULES.breakout).max(), p.rolling(RULES.breakout).min()
    a = atr(p, RULES.atr_window)
    n_entries = n_exits = 0
    best = np.nan
    for t in range(1, len(p)):
        prev, now = pos.iloc[t - 1], pos.iloc[t]
        if prev != 0 and np.sign(now) != np.sign(prev):  # exit: close beyond the trailing stop
            n_exits += 1
            best = max(best, p.iloc[t]) if prev > 0 else min(best, p.iloc[t])
            gap = (best - p.iloc[t]) if prev > 0 else (p.iloc[t] - best)
            assert gap >= RULES.stop_atr * a.iloc[t]
        elif prev != 0:  # holding: size fixed at entry, stop not yet hit
            assert now == prev
            best = max(best, p.iloc[t]) if prev > 0 else min(best, p.iloc[t])
            gap = (best - p.iloc[t]) if prev > 0 else (p.iloc[t] - best)
            assert gap < RULES.stop_atr * a.iloc[t]
        if now != 0 and np.sign(now) != np.sign(prev):  # entry (possibly the day of an exit): breakout with filter
            n_entries += 1
            assert np.sign(now) == filt.iloc[t]
            assert p.iloc[t] == (hi.iloc[t] if now > 0 else lo.iloc[t])
            assert abs(now) == pytest.approx(RULES.risk / a.iloc[t])
            best = p.iloc[t]
    assert n_entries > 20 and n_exits > 20


def test_filter_blocks_trades_against_the_trend():
    """A breakout to a new low while the filter is long must not open a short."""
    up = np.linspace(100, 200, 200)
    dip = up[-1] - np.linspace(0, 6, 8)  # a sharp dip to a 10-day low; the 5/10 EMAs barely turn
    p = pd.Series(np.concatenate([up, dip]), index=DAYS[:208])
    pos = clenow_decisions(p, ClenowRules(fast=5, slow=50, breakout=10, atr_window=10, stop_atr=100.0))
    assert (pos.iloc[-8:] >= 0).all()


def test_atr_is_true_range_estimate_from_closes():
    p = walk(1, 300)
    expected = TRUE_RANGE_RATIO * p.diff().abs().rolling(20).mean()
    pd.testing.assert_series_equal(atr(p, 20), expected)


@pytest.mark.parametrize("variant", VARIANTS)
def test_no_look_ahead(variant):
    """Changing prices after day k changes no decision up to k."""
    p = walk(2)
    q = p.copy()
    k = 1500
    q.iloc[k + 1 :] = q.iloc[k + 1 :] * 1.5 - 300
    a, b = clenow_decisions(p, RULES, variant), clenow_decisions(q, RULES, variant)
    pd.testing.assert_series_equal(a.iloc[: k + 1], b.iloc[: k + 1])
    pd.testing.assert_series_equal(ema_decisions(p, 50).iloc[: k + 1], ema_decisions(q, 50).iloc[: k + 1])


def test_execution_lag_and_pnl():
    """Decisions made at close t are held from close t+lag; P&L(t+1) = held(t) × Δp(t+1)."""
    p = walk(3, 400)
    dec = clenow_decisions(p, RULES)
    r = run_market(p, dec, COST, lag=1)
    pd.testing.assert_series_equal(r.held, dec.shift(1).fillna(0.0), check_names=False)
    expected = dec.shift(2).fillna(0.0) * p.diff().fillna(0.0)
    np.testing.assert_allclose(r.gross.to_numpy(), expected.to_numpy())


def test_costs_are_charged_on_trades_and_rolls():
    p = pd.Series(100.0 + np.arange(300) % 2, index=DAYS[:300])  # |Δp| = 1 every day, ATR(close) = 1
    dec = pd.Series(0.0, index=p.index)
    dec.iloc[100:200] = 2.0  # buy 2 units, hold 100 days, sell
    cost = pd.Series({"cost_atr": 0.05, "rolls_per_year": 4})
    r = run_market(p, dec, cost, lag=0)
    trades = 2 * 2 * 0.05  # two trades of 2 units at 0.05 points
    rolls = 100 * 2 * 2 * 0.05 * 4 / 252  # 100 days holding 2 units, 4 rolls a year, two sides each
    assert r.cost.sum() == pytest.approx(trades + rolls)


def test_random_walk_has_no_edge():
    """Without trends, the core model and the paper's signal earn nothing on average (gross)."""
    sr_core, sr_ema = [], []
    for seed in range(40):
        p = walk(100 + seed)
        sr_core.append(sharpe_daily(run_market(p, clenow_decisions(p, RULES), COST).gross.iloc[100:]))
        sr_ema.append(sharpe_daily(run_market(p, ema_decisions(p, 20), COST).gross.iloc[100:]))
    se = 1 / np.sqrt(len(DAYS) / 252) / np.sqrt(40)  # standard error of the mean Sharpe ratio
    assert abs(np.mean(sr_core)) < 3 * se
    assert abs(np.mean(sr_ema)) < 3 * se


def test_trending_series_is_profitable():
    """With a slowly wandering drift (persistent trends), every rule and the paper's signal make money."""
    rng = np.random.default_rng(0)
    mu = np.zeros(3000)
    for i in range(1, 3000):
        mu[i] = 0.99 * mu[i - 1] + 0.03 * rng.normal()  # trends lasting ~100 days
    p = pd.Series(1000 + np.cumsum(mu + rng.normal(0, 1, 3000)), index=DAYS)
    for variant in VARIANTS:
        assert sharpe_daily(run_market(p, clenow_decisions(p, RULES, variant), COST).gross) > 1.0
    assert sharpe_daily(run_market(p, ema_decisions(p, 20), COST).gross) > 1.0
