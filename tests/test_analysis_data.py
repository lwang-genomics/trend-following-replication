import numpy as np
import pandas as pd
import pytest

from trendrep.analysis import debiased_t_stat, oos_comparison, saturation_fit, sharpe, t_stat, tanh_model
from trendrep.data import bond_price_from_yield

IDX = pd.date_range("1960-01-01", periods=720, freq="MS")


def test_t_stat_is_sharpe_times_sqrt_years():
    rng = np.random.default_rng(0)
    m = pd.Series(rng.normal(0.1, 1, 720), index=IDX)
    assert t_stat(m) == pytest.approx(sharpe(m) * np.sqrt(60))


def test_debiasing_removes_pure_beta():
    rng = np.random.default_rng(1)
    long = pd.Series(rng.normal(0.4, 1, 720), index=IDX)
    trend = 0.5 * long + pd.Series(rng.normal(0, 1, 720), index=IDX)  # no alpha, only beta to the drift
    res = debiased_t_stat(trend, long)
    assert res["beta"] == pytest.approx(0.5, abs=0.1)
    assert abs(res["alpha_t"]) < 2.5
    assert t_stat(trend) > 2.5  # the raw t-stat is flattered by the drift


def test_saturation_fit_recovers_known_parameters():
    rng = np.random.default_rng(2)
    s = rng.normal(0, 1.5, 50_000)
    y = tanh_model(s, 0.02, 0.08, 0.9) + rng.normal(0, 0.3, len(s))
    fit = saturation_fit(s, y)
    assert fit["tanh_s_star"] == pytest.approx(0.9, rel=0.15)
    assert fit["tanh_b"] == pytest.approx(0.08, rel=0.15)
    assert fit["f_stat"] > 10  # tanh clearly preferred to the linear fit
    assert fit["cubic_s3"] < 0


def test_oos_comparison_flags_a_collapse():
    rng = np.random.default_rng(3)
    m = pd.Series(np.r_[rng.normal(0.3, 1, 600), rng.normal(-0.3, 1, 120)], index=IDX)
    res = oos_comparison(m, "2010-01-01")
    assert res["sr_in"] > 0.7 and res["sr_out"] < 0
    assert res["z_diff"] < -2 and res["p_oos_le_observed"] < 0.05


def test_bond_price_from_yield():
    flat = bond_price_from_yield(pd.Series([5.0] * 4, index=IDX[:4]))
    np.testing.assert_allclose(flat.to_numpy(), 1.0)
    up = bond_price_from_yield(pd.Series([5.0, 6.0], index=IDX[:2]))
    duration = (1 - 1.06**-10) / 0.06 * 1.06 / 1.06  # modified duration of a 10y par bond, roughly
    assert up.iloc[1] < 1.0
    assert (1 - up.iloc[1]) / 0.01 == pytest.approx(duration, rel=0.1)
