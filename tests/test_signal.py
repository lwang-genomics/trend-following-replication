import numpy as np
import pandas as pd
import pytest

from trendrep.analysis import t_stat
from trendrep.signal import WARMUP, ema, trend_pnl, trend_signal

MONTHS = pd.date_range("1960-01-01", periods=600, freq="MS")


def random_walk(rng, n=600, drift=0.0) -> pd.Series:
    return pd.Series(100 + np.cumsum(rng.normal(drift, 1.0, n)), index=MONTHS[:n])


def test_ema_matches_explicit_recursion():
    x = pd.Series([1.0, 3.0, 2.0, 5.0, 4.0])
    n = 3
    expected = [1.0]
    for v in x.iloc[1:]:
        expected.append((1 - 1 / n) * expected[-1] + v / n)
    np.testing.assert_allclose(ema(x, n).to_numpy(), expected)


def test_pnl_matches_hand_calculation():
    rng = np.random.default_rng(0)
    p = random_walk(rng, 60)
    n, lag = 5, 1
    sig = trend_signal(p, n)
    out = trend_pnl(p, n, lag)
    i = WARMUP + 3  # an arbitrary information month
    expected = np.sign(sig["signal"].iloc[i]) * (p.iloc[i + 2] - p.iloc[i + 1]) / sig["sigma"].iloc[i]
    assert out.loc[p.index[i + 2], "pnl"] == pytest.approx(expected)


def test_no_look_ahead():
    """Changing prices after month k must not change any signal up to k or any P&L realised up to k."""
    rng = np.random.default_rng(1)
    p = random_walk(rng)
    k = 300
    q = p.copy()
    q.iloc[k + 1 :] = q.iloc[k + 1 :] * 3 + 50
    for lag in (0, 1):
        a, b = trend_pnl(p, 5, lag), trend_pnl(q, 5, lag)
        cut = p.index[k]
        pd.testing.assert_frame_equal(a.loc[:cut], b.loc[:cut])
    pd.testing.assert_frame_equal(trend_signal(p, 5).iloc[: k + 1], trend_signal(q, 5).iloc[: k + 1])


def test_random_walk_has_no_trend_edge():
    rng = np.random.default_rng(2)
    t = [t_stat(trend_pnl(random_walk(rng), 5, lag=1)["pnl"]) for _ in range(300)]
    assert abs(np.mean(t)) < 0.2  # unbiased...
    assert 0.8 < np.std(t) < 1.2  # ...and the paper's t-stat is correctly scaled


def test_monthly_averaging_fakes_a_trend_at_lag_0_but_not_lag_1():
    """Working (1960): averaging a random walk induces lag-1 autocorrelation of 0.25 in its changes.

    A trend follower trading the very next month (lag 0) on monthly averages earns a spurious
    profit; holding one month later (lag 1, eq. 2 as printed) removes it.
    """
    rng = np.random.default_rng(3)
    t0, t1 = [], []
    for _ in range(200):
        daily = np.cumsum(rng.normal(0, 1, 600 * 21)) + 1000
        monthly_avg = pd.Series(daily.reshape(600, 21).mean(axis=1), index=MONTHS)
        t0.append(t_stat(trend_pnl(monthly_avg, 5, lag=0)["pnl"]))
        t1.append(t_stat(trend_pnl(monthly_avg, 5, lag=1)["pnl"]))
    assert np.mean(t0) > 1.5  # ≈ 2 on average: a pure artefact of averaging
    assert abs(np.mean(t1)) < 0.3


def test_trending_series_is_profitable():
    rng = np.random.default_rng(4)
    t = []
    for _ in range(50):
        r = np.zeros(600)
        eps = rng.normal(0, 1, 600)
        for i in range(1, 600):
            r[i] = 0.6 * r[i - 1] + eps[i]  # persistent monthly changes
        t.append(t_stat(trend_pnl(pd.Series(100 + np.cumsum(r), index=MONTHS), 5, lag=1)["pnl"]))
    assert np.mean(t) > 2.0


def test_stale_prices_are_not_traded():
    rng = np.random.default_rng(5)
    p = random_walk(rng, 120)
    p.iloc[60:84] = p.iloc[60]  # two years of administered, unchanged prices
    sig = trend_signal(p, 5)
    assert sig["signal"].iloc[62:63].notna().all()  # two flat months: still 10 moves in the last 12
    assert sig["signal"].iloc[63:84].isna().all()  # from the third flat month on: not traded
    assert sig["signal"].iloc[84:93].isna().all()  # nor until 10 of the last 12 months moved again
    assert sig["signal"].iloc[94:].notna().all()
