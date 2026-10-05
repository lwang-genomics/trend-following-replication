"""Statistics used in the paper (Sharpe, t-stat, de-biased t-stat, saturation fit) and the out-of-sample test."""

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from .config import BOOT_BLOCK, BOOT_N


def sharpe(monthly: pd.Series) -> float:
    """Annualised Sharpe ratio of a monthly P&L. Futures-style P&L is self-financed, so no rf."""
    m = monthly.dropna()
    return float(m.mean() / m.std(ddof=1) * np.sqrt(12))


def t_stat(monthly: pd.Series) -> float:
    """t-stat of the mean as defined in the paper: Sharpe × sqrt(number of years)."""
    m = monthly.dropna()
    return sharpe(m) * np.sqrt(len(m) / 12)


def debiased_t_stat(trend: pd.Series, long_only: pd.Series) -> dict[str, float]:
    """t-stat of the intercept in trend = alpha + beta × long_only + e (OLS).

    This is the paper's "de-biased" trend (T*): the trend P&L once its exposure to the
    long-only drift mu has been factored out.
    """
    df = pd.concat([trend, long_only], axis=1, keys=["y", "x"]).dropna()
    X = np.column_stack([np.ones(len(df)), df["x"].to_numpy()])
    y = df["y"].to_numpy()
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
    s2 = resid @ resid / (len(y) - 2)
    se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
    return {"alpha_t": float(coef[0] / se[0]), "beta": float(coef[1]), "corr": float(df.corr().iloc[0, 1])}


def summary(trend: pd.Series, long_only: pd.Series) -> dict[str, float]:
    """The columns of the paper's tables: SR(T), t(T), t(T*), SR(mu), t(mu)."""
    return {
        "sr": sharpe(trend),
        "t": t_stat(trend),
        "t_debiased": debiased_t_stat(trend, long_only)["alpha_t"],
        "sr_mu": sharpe(long_only),
        "t_mu": t_stat(long_only),
        "years": len(trend.dropna()) / 12,
        "start": f"{trend.dropna().index.min():%m/%Y}",
    }


# ------------------------------------------------------------------ saturation (paper Fig. 5)


def tanh_model(s, a, b, s_star):
    return a + b * s_star * np.tanh(s / s_star)


def saturation_fit(signal: np.ndarray, move: np.ndarray) -> dict[str, float]:
    """Linear fit move = a + b s and the paper's saturating fit move = a + b s* tanh(s/s*).

    Also reports the residual sum of squares of each, and a cubic fit's coefficients
    (the paper notes a small s^2 and clearly negative s^3 term).
    """
    lin = np.polyfit(signal, move, 1)
    rss_lin = float(((move - np.polyval(lin, signal)) ** 2).sum())
    (a, b, s_star), cov = curve_fit(tanh_model, signal, move, p0=[0.0, 0.05, 1.0], maxfev=20000)
    rss_tanh = float(((move - tanh_model(signal, a, b, s_star)) ** 2).sum())
    cubic = np.polyfit(signal, move, 3)
    n = len(signal)
    return {
        "n_points": n,
        "lin_a": float(lin[1]), "lin_b": float(lin[0]),
        "tanh_a": float(a), "tanh_b": float(b), "tanh_s_star": float(abs(s_star)),
        "tanh_s_star_se": float(np.sqrt(cov[2, 2])),
        "cubic_s2": float(cubic[1]), "cubic_s3": float(cubic[0]),
        "rss_lin": rss_lin, "rss_tanh": rss_tanh,
        # F-test of the extra parameter s* (tanh nests the linear model as s* -> inf)
        "f_stat": float((rss_lin - rss_tanh) / (rss_tanh / (n - 3))),
    }


def running_average(x: np.ndarray, y: np.ndarray, window: int) -> pd.DataFrame:
    """Running average of y over `window` consecutive points ordered by x (paper Fig. 5 display)."""
    order = np.argsort(x)
    xs = pd.Series(x[order]).rolling(window, center=True).mean()
    ys = pd.Series(y[order]).rolling(window, center=True).mean()
    return pd.DataFrame({"x": xs, "y": ys}).dropna()


# ------------------------------------------------------------------ out-of-sample


def oos_comparison(monthly: pd.Series, split: str, seed: int = 0) -> dict[str, float]:
    """Compare the Sharpe ratio before and after `split`.

    z: difference of Sharpe ratios over its approximate standard error sqrt(1/Y1 + 1/Y2)
    (the Sharpe of an i.i.d. series has SE ≈ 1/sqrt(years)).
    p_oos_le_observed: under a stationary-block bootstrap of the in-sample months, the
    probability of an out-of-sample-length Sharpe at or below the one observed.
    """
    m = monthly.dropna()
    ins, oos = m[m.index < pd.Timestamp(split)], m[m.index >= pd.Timestamp(split)]
    sr_in, sr_out = sharpe(ins), sharpe(oos)
    y_in, y_out = len(ins) / 12, len(oos) / 12
    z = (sr_out - sr_in) / np.sqrt(1 / y_in + 1 / y_out)

    rng = np.random.default_rng(seed)
    x, n_out = ins.to_numpy(), len(oos)
    starts = rng.integers(0, len(x) - BOOT_BLOCK, size=(BOOT_N, n_out // BOOT_BLOCK + 1))
    idx = (starts[:, :, None] + np.arange(BOOT_BLOCK)).reshape(BOOT_N, -1)[:, :n_out]
    sims = x[idx]
    sr_sims = sims.mean(axis=1) / sims.std(axis=1, ddof=1) * np.sqrt(12)
    return {
        "sr_in": sr_in, "sr_out": sr_out, "years_in": y_in, "years_out": y_out,
        "t_in": t_stat(ins), "t_out": t_stat(oos), "z_diff": float(z),
        "p_oos_le_observed": float((sr_sims <= sr_out).mean()),
        "sr_sim_5": float(np.percentile(sr_sims, 5)), "sr_sim_95": float(np.percentile(sr_sims, 95)),
    }
