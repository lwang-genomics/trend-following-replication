import numpy as np
import pandas as pd
import pytest

from trendrep.book import inverse_vol_book, vol_scaled
from trendrep.convexity import (
    L,
    identity_rhs,
    normalised_returns,
    quad_fit,
    tau_prime,
    trend_frame,
    upsilon,
)

TAU = 60
LAM = 0.01 / np.sqrt(TAU)


def test_trend_identity_is_exact():
    """Eq. (13): L_τ'[G] = λτ/(τ−1) (τ L_τ[R]² − L_τ'[R²]) holds exactly, whatever the returns."""
    rng = np.random.default_rng(0)
    r = pd.Series(rng.standard_t(3, 5000) + 0.05)  # fat tails and a drift: no assumption needed
    f = trend_frame(r, TAU, LAM)
    np.testing.assert_allclose(L(f["G"].to_numpy(), tau_prime(TAU)), identity_rhs(r, TAU, LAM), atol=1e-15)


def test_linear_trend_parabola_on_random_walk():
    """⟨Ḡ | T⟩ = Υ (T² − 1) for uncorrelated unit-variance returns (eq. 14).

    Approximate: the short-term term L_τ'[R²] is slightly correlated with T², which flattens the
    fitted curvature by a few percent at this τ.
    """
    rng = np.random.default_rng(1)
    f = trend_frame(pd.Series(rng.normal(0, 1, 300_000)), TAU, LAM).iloc[1000:]
    fit = quad_fit(f["T"].to_numpy(), f["Gbar"].to_numpy())
    assert fit["c"] == pytest.approx(upsilon(TAU, LAM), rel=0.05)
    assert fit["a"] == pytest.approx(-upsilon(TAU, LAM), rel=0.05)
    assert abs(fit["b"]) < 0.05 * upsilon(TAU, LAM)


def test_sign_trend_v_shape_on_random_walk():
    """⟨Ḡ | T⟩ ≈ λ√τ (|T| − √(2/π)) for the sign rule (appendix 6.2.3, continuous-time approximation)."""
    rng = np.random.default_rng(2)
    f = trend_frame(pd.Series(rng.normal(0, 1, 300_000)), TAU, 0.01, "sign").iloc[1000:]
    t, y = f["T"].to_numpy(), f["Gbar"].to_numpy()
    (a, b), *_ = np.linalg.lstsq(np.column_stack([np.ones_like(t), np.abs(t)]), y, rcond=None)
    assert b == pytest.approx(0.01 * np.sqrt(TAU), rel=0.1)
    assert a == pytest.approx(-0.01 * np.sqrt(TAU) * np.sqrt(2 / np.pi), rel=0.1)


def test_risk_parity_bound_holds_pointwise():
    """Eq. (24): Σ w Ḡ_k ≥ Υ (T_RP² − Σ w L_τ'[R_k²]) on every day, for any correlated returns."""
    rng = np.random.default_rng(3)
    n, k = 4000, 5
    common = rng.normal(0, 1, (n, 1))
    R = 0.6 * common + 0.8 * rng.standard_t(4, (n, k))
    gbar = np.mean([trend_frame(pd.Series(R[:, i]), TAU, LAM)["Gbar"].to_numpy() for i in range(k)], axis=0)
    t_rp = np.sqrt(TAU) * L(R.mean(axis=1), TAU)
    short = np.mean([L(R[:, i] ** 2, tau_prime(TAU)) for i in range(k)], axis=0)
    assert (gbar - upsilon(TAU, LAM) * (t_rp**2 - short) >= -1e-12).all()


def test_normalised_returns_use_past_risk_only():
    rng = np.random.default_rng(4)
    d = pd.Series(rng.normal(0, 1, 500))
    e = d.copy()
    e.iloc[301:] *= 10
    pd.testing.assert_series_equal(normalised_returns(d).iloc[:301], normalised_returns(e).iloc[:301])


def test_inverse_vol_book_hits_its_volatility_target():
    rng = np.random.default_rng(5)
    idx = pd.bdate_range("2000-01-03", periods=3000)
    rets = pd.DataFrame(rng.normal(0, 1, (3000, 3)) * [0.01, 0.004, 0.012], index=idx, columns=list("abc"))
    book = inverse_vol_book(rets, cost_bps=0.0)
    assert book.std() * np.sqrt(252) == pytest.approx(0.10, rel=0.1)


def test_vol_scaling_uses_past_only():
    rng = np.random.default_rng(6)
    x = pd.Series(rng.normal(0, 0.01, 1000), index=pd.bdate_range("2000-01-03", periods=1000))
    y = x.copy()
    y.iloc[601:] *= 5
    pd.testing.assert_series_equal(vol_scaled(x).loc[: x.index[600]], vol_scaled(y).loc[: x.index[600]])
    assert vol_scaled(x).std() * np.sqrt(252) == pytest.approx(0.10, rel=0.1)
