"""Trend convexity (Part III): Dao, Nguyen, Deremble, Lempérière, Bouchaud & Potters (2016).

Notation follows the paper. For one market with daily price changes D_t (points):

    σ_t   = γ sqrt(L_τσ[D²_t])                 risk estimate, τσ = 10, γ ≈ 1.05       (9)
    R_t   = D_t / σ_{t-1}                       normalised return, unit variance
    L_τ   EMA with α = 1 − 2/(τ+1), started from zero:  L_τ[X]_t = α L_τ[X]_{t-1} + (1−α) X_t
    Π_t   = λ τ L_τ[R_t] / σ_t                  linear trend position                    (12)
    G_t   = Π_{t-1} D_t = λ τ L_τ[R]_{t-1} R_t  daily P&L
    τ'    = τ/2 + 1/(2τ)                        (the EMA with α²)

and the paper's exact identity (13), (42):

    L_τ'[G_t] = λτ/(τ−1) · (τ L_τ[R_t]² − L_τ'[R²_t])

so the P&L aggregated over ≈ τ' days, Ḡ_t = τ' L_τ'[G_t], is a long-term variance (T² with
T = √τ L_τ[R]) minus a short-term one: Ḡ = Υ(τ) (T² − L_τ'[R²]), Υ = λττ'/(τ−1).  (14)
"""

import numpy as np
import pandas as pd
from scipy.signal import lfilter

SIGMA_TAU = 10  # τσ of eq. (9)
GAMMA = 1.05  # the paper's calibration for τσ = 10
WARMUP = 20  # days before the first normalised return


def alpha(tau: float) -> float:
    return 1.0 - 2.0 / (tau + 1.0)


def tau_prime(tau: float) -> float:
    return tau / 2.0 + 1.0 / (2.0 * tau)


def L(x, tau: float) -> np.ndarray:
    """The paper's EMA operator L_τ, started from zero (exact recursion, no NaNs allowed)."""
    a = alpha(tau)
    return lfilter([1.0 - a], [1.0, -a], np.asarray(x, dtype=float))


def upsilon(tau: float, lam: float) -> float:
    return lam * tau * tau_prime(tau) / (tau - 1.0)


def normalised_returns(d: pd.Series, gamma: float = GAMMA) -> pd.Series:
    """R_t = D_t / σ_{t-1}, with σ from eq. (9); zero during the warm-up."""
    d = d.fillna(0.0)
    sigma = gamma * np.sqrt(L(d.to_numpy() ** 2, SIGMA_TAU))
    prev = np.r_[np.nan, sigma[:-1]]
    prev[prev == 0] = np.nan
    r = d.to_numpy() / prev
    r[: WARMUP + 1] = 0.0
    r[~np.isfinite(r)] = 0.0
    return pd.Series(r, index=d.index)


def calibrate_gamma(d: pd.Series) -> float:
    """γ such that the normalised returns have unit variance (the paper finds 1.05 for τσ = 10)."""
    r = normalised_returns(d, gamma=1.0).iloc[WARMUP + 1 :]
    return float(np.sqrt((r**2).mean()))


def trend_frame(r: pd.Series, tau: float, lam: float, kind: str = "linear") -> pd.DataFrame:
    """Daily P&L G, aggregated P&L Ḡ and trend indicator T for one normalised return series.

    linear: G_t = λτ L_τ[R]_{t-1} R_t          (eq. 12)
    sign:   G_t = λ sign(L_τ[R]_{t-1}) R_t     (section 2.4)
    Ḡ = τ' L_τ'[G], the P&L aggregated over ≈ τ/2 days (eq. 14). For the sign rule the paper's
    continuous-time result (appendix 6.2.3) is matched by this discrete aggregation (checked on
    simulated random walks in the tests).
    T_t = √τ L_τ[R]_t (unit variance for uncorrelated R).
    """
    x = r.to_numpy()
    ema = L(x, tau)
    prev = np.r_[0.0, ema[:-1]]
    if kind == "linear":
        g = lam * tau * prev * x
    elif kind == "sign":
        g = lam * np.sign(prev) * x
    else:
        raise ValueError(kind)
    agg = tau_prime(tau) * L(g, tau_prime(tau))
    return pd.DataFrame({"G": g, "Gbar": agg, "T": np.sqrt(tau) * ema, "R": x}, index=r.index)


def identity_rhs(r: pd.Series, tau: float, lam: float) -> np.ndarray:
    """Right-hand side of eq. (13): λτ/(τ−1) (τ L_τ[R]² − L_τ'[R²])."""
    x = r.to_numpy()
    return lam * tau / (tau - 1.0) * (tau * L(x, tau) ** 2 - L(x**2, tau_prime(tau)))


def theory_linear(t: np.ndarray, tau: float, lam: float, v: float = 1.0) -> np.ndarray:
    """⟨Ḡ | T⟩ = Υ(τ) (T² − v), eq. (14); v = ⟨R²⟩ = 1 when the risk estimate is unbiased."""
    return upsilon(tau, lam) * (t**2 - v)


def theory_sign(t: np.ndarray, tau: float, lam: float, v: float = 1.0) -> np.ndarray:
    """⟨Ḡ | T⟩ = λ √τ (|T| − √(2v/π)) for G = λ sign(trend) R (appendix 6.2.3, our normalisation)."""
    return lam * np.sqrt(tau) * (np.abs(t) - np.sqrt(2.0 * v / np.pi))


def quad_fit(x: np.ndarray, y: np.ndarray) -> dict:
    """y = a + b x + c x²: coefficients and R²."""
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    c2, b, a = np.polyfit(x, y, 2)
    resid = y - (a + b * x + c2 * x**2)
    return {"a": float(a), "b": float(b), "c": float(c2), "r2": float(1 - resid.var() / y.var()), "n": int(len(x))}


def binned(x: np.ndarray, y: np.ndarray, edges: np.ndarray) -> pd.DataFrame:
    """Mean of y in bins of x, for display."""
    ok = np.isfinite(x) & np.isfinite(y)
    b = pd.cut(pd.Series(x[ok]), edges)
    g = pd.Series(y[ok]).groupby(b, observed=True)
    return pd.DataFrame({"x": pd.Series(x[ok]).groupby(b, observed=True).mean(), "y": g.mean(), "n": g.size()})
