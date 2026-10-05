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


# ------------------------------------------------------------------ Part II: daily strategies


def sharpe_daily(daily: pd.Series) -> float:
    """Annualised Sharpe ratio of a daily excess-return series (252 days a year)."""
    d = daily.dropna()
    return float(d.mean() / d.std(ddof=1) * np.sqrt(252))


def max_drawdown(daily: pd.Series) -> float:
    """Largest peak-to-trough fall of the cumulative (non-compounded) P&L, in the series' units."""
    cum = daily.fillna(0.0).cumsum()
    return float((cum - cum.cummax()).min())


def ols(y: pd.Series, X: pd.DataFrame) -> dict:
    """OLS of y on X with an intercept: coefficients, t-stats, R² and residual standard deviation."""
    df = pd.concat([y.rename("_y"), X], axis=1).dropna()
    A = np.column_stack([np.ones(len(df)), df[X.columns].to_numpy()])
    b = df["_y"].to_numpy()
    coef, *_ = np.linalg.lstsq(A, b, rcond=None)
    resid = b - A @ coef
    s2 = resid @ resid / (len(b) - A.shape[1])
    se = np.sqrt(np.diag(s2 * np.linalg.inv(A.T @ A)))
    names = ["alpha", *X.columns]
    return {"coef": dict(zip(names, coef.tolist())), "t": dict(zip(names, (coef / se).tolist())),
            "r2": float(1 - resid @ resid / ((b - b.mean()) @ (b - b.mean()))), "n": len(b),
            "resid_sd": float(np.sqrt(s2))}


def sharpe_diff_bootstrap(a: pd.Series, b: pd.Series, block: int, n_boot: int, seed: int = 0) -> dict:
    """Moving-block bootstrap of SR(a) − SR(b) on paired daily returns.

    Resampling the same blocks for both series keeps their correlation. Returns the observed
    difference, a 95% percentile interval and the share of resamples with a difference ≤ 0.
    """
    df = pd.concat([a, b], axis=1).dropna().to_numpy()
    n = len(df)
    rng = np.random.default_rng(seed)
    diff = []
    for _ in range(0, n_boot, 200):  # chunks keep memory small
        starts = rng.integers(0, n - block, size=(200, n // block + 1))
        idx = (starts[:, :, None] + np.arange(block)).reshape(200, -1)[:, :n]
        x = df[idx]  # 200 × n × 2
        sr = x.mean(axis=1) / x.std(axis=1, ddof=1) * np.sqrt(252)
        diff.append(sr[:, 0] - sr[:, 1])
    diff = np.concatenate(diff)[:n_boot]
    obs = sharpe_daily(pd.Series(df[:, 0])) - sharpe_daily(pd.Series(df[:, 1]))
    return {"diff": float(obs), "lo": float(np.percentile(diff, 2.5)), "hi": float(np.percentile(diff, 97.5)),
            "p_le_0": float((diff <= 0).mean())}
