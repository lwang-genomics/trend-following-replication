"""Daily back-adjusted futures prices, trading costs and the managed-futures benchmark (Part II).

Prices come from the pysystemtrade data set at a pinned commit (config.FUTURES_COMMIT) and are
cached under data/raw/futures/. They are Panama back-adjusted: each roll shifts the history by the
roll gap, so price *differences* are those of the contract held, roll yield included, and the price
*level* is not a real price (it can be negative). Everything here therefore works in price points.
"""

import io

import numpy as np
import pandas as pd

from .config import (
    BENCHMARK,
    CBOE_PPUT_URL,
    COST_RECENT,
    FRED_URL,
    FUTURES,
    FUTURES_COMMIT,
    FUTURES_DIR,
    FUTURES_URL,
    OHLC_TICKERS,
    SPREAD_OVERRIDES,
)
from .data import _fetch, fred


def _futures_file(path: str) -> bytes:
    local = FUTURES_DIR / path.replace("/", "_")
    FUTURES_DIR.mkdir(parents=True, exist_ok=True)
    return _fetch(FUTURES_URL.format(FUTURES_COMMIT, path), local)


def daily_close(market: str) -> pd.Series:
    """Last price of each weekday for one market (the raw file has several stamps on recent days)."""
    raw = _futures_file(f"adjusted_prices_csv/{market}.csv")
    x = pd.read_csv(io.BytesIO(raw), parse_dates=["DATETIME"])
    s = x.set_index("DATETIME")["price"].astype(float).dropna()
    d = s.groupby(s.index.normalize()).last()
    return d[d.index.dayofweek < 5].rename(market)


def build_daily_panel() -> pd.DataFrame:
    """Daily closes (points) for every market in config.FUTURES, on the union of trading days.

    A market's missing days (holidays, before listing) stay NaN; signals are computed on each
    market's own trading days.
    """
    cols = [daily_close(m) for ms in FUTURES.values() for m in ms]
    return pd.concat(cols, axis=1).sort_index()


def trading_costs(panel: pd.DataFrame) -> pd.DataFrame:
    """Cost per contract and side in units of daily ATR, and rolls per year, for each market.

    Cost in points = half the bid-ask spread (SpreadCost) + commission per contract converted to points
    (PerBlock / Pointsize) + any percentage commission × the recent price level. These are today's costs;
    they are divided by each market's recent ATR (mean |Δp| since COST_RECENT) so that, applied to the
    ATR at the time of each trade, costs scale with volatility and price level through history. Trading
    was dearer in the 1990s, hence the cost stress test (config.COST_STRESS).
    Rolls per year = number of contract months held (HoldRollCycle); each roll trades twice.
    """
    inst = pd.read_csv(io.BytesIO(_futures_file("csvconfig/instrumentconfig.csv"))).set_index("Instrument")
    spread = pd.read_csv(io.BytesIO(_futures_file("csvconfig/spreadcosts.csv"))).set_index("Instrument")
    roll = pd.read_csv(io.BytesIO(_futures_file("csvconfig/rollconfig.csv"))).set_index("Instrument")
    markets = list(panel.columns)
    out = pd.DataFrame(index=markets)
    out["spread_points"] = spread["SpreadCost"].reindex(markets)
    # a few full-size contracts have no spread estimate: the mini quotes the same index points
    mini = spread["SpreadCost"].reindex([f"{m}_mini" for m in markets]).to_numpy()
    out["spread_points"] = out["spread_points"].fillna(pd.Series(mini, index=markets))
    for m, v in SPREAD_OVERRIDES.items():
        if m in out.index:
            out.loc[m, "spread_points"] = v
    out["commission_points"] = (inst["PerBlock"] / inst["Pointsize"]).reindex(markets)
    out["commission_pct"] = inst["Percentage"].reindex(markets)
    out["rolls_per_year"] = roll["HoldRollCycle"].reindex(markets).str.len()
    out["description"] = inst["Description"].reindex(markets)
    missing = out[["spread_points", "commission_points", "rolls_per_year"]].isna().any(axis=1)
    if missing.any():
        raise ValueError(f"no cost data for {list(out.index[missing])}")
    recent = panel.loc[COST_RECENT:]
    out["recent_atr"] = [recent[m].dropna().diff().abs().mean() for m in markets]
    level = [recent[m].dropna().abs().mean() for m in markets]
    points = out["spread_points"] + out["commission_points"] + out["commission_pct"] * level
    out["cost_atr"] = points / out["recent_atr"]
    return out


def benchmark_monthly() -> pd.Series:
    """Monthly excess return of the managed-futures benchmark fund over 3-month T-bills.

    Total return from the fund's adjusted close (distributions reinvested), via Yahoo Finance,
    minus the 3-month T-bill rate (FRED TB3MS) over the month: the fund is fully funded, while
    the futures strategies earn excess returns.
    """
    path = FUTURES_DIR / f"yahoo_{BENCHMARK}.csv"
    if not path.exists():
        import yfinance as yf

        FUTURES_DIR.mkdir(parents=True, exist_ok=True)
        px = yf.download(BENCHMARK, start="2000-01-01", end="2024-04-01", auto_adjust=True, progress=False)
        px["Close"].squeeze().rename("close").to_csv(path)
    px = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    ret = px.resample("MS").last().pct_change().dropna()
    tbill = fred("TB3MS").reindex(ret.index) / 100 / 12
    return (ret - tbill).dropna().rename(BENCHMARK)


def percent_returns(market: str) -> pd.Series:
    """Daily simple returns of the contract held: back-adjusted price change over the previous actual price.

    The actual price of the contract held (PRICE in pysystemtrade's multiple prices) gives the
    denominator; on a roll day the change is that of the new contract, so roll yield is included.
    """
    raw = _futures_file(f"multiple_prices_csv/{market}.csv")
    x = pd.read_csv(io.BytesIO(raw), parse_dates=["DATETIME"]).set_index("DATETIME")["PRICE"].astype(float)
    actual = x.groupby(x.index.normalize()).last()
    actual = actual[actual.index.dayofweek < 5]
    adj = daily_close(market)
    both = pd.concat([adj, actual], axis=1, keys=["adj", "px"]).dropna()
    return (both["adj"].diff() / both["px"].shift(1)).dropna().rename(market)


def _yahoo_daily(ticker: str, name: str) -> pd.Series:
    path = FUTURES_DIR / f"yahoo_{name}.csv"
    if not path.exists():
        import yfinance as yf

        FUTURES_DIR.mkdir(parents=True, exist_ok=True)
        px = yf.download(ticker, start="1985-01-01", end="2024-04-01", auto_adjust=True, progress=False)
        px["Close"].squeeze().rename("close").to_csv(path)
    return pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0].dropna()


def tbill_daily(index: pd.DatetimeIndex) -> pd.Series:
    """3-month T-bill rate (FRED TB3MS) as a daily simple return on `index`."""
    tb = fred("TB3MS") / 100 / 252
    return tb.reindex(index.union(tb.index)).ffill().reindex(index)


def benchmark_daily() -> pd.Series:
    """Daily excess return of the managed-futures benchmark fund (adjusted close, minus T-bills)."""
    ret = _yahoo_daily(BENCHMARK, BENCHMARK).pct_change().dropna()
    return (ret - tbill_daily(ret.index)).dropna().rename(BENCHMARK)


def sp500_total_return() -> pd.Series:
    """S&P 500 total-return index level (Yahoo ^SP500TR, from 1988)."""
    return _yahoo_daily("^SP500TR", "SP500TR").rename("SP500TR")


def protective_put() -> pd.Series:
    """CBOE S&P 500 5% Put Protection Index (PPUT): S&P 500 plus a monthly 5% out-of-the-money put."""
    raw = _fetch(CBOE_PPUT_URL, FUTURES_DIR / "cboe_PPUT.csv")
    x = pd.read_csv(io.BytesIO(raw))
    return pd.Series(x["PPUT"].to_numpy(float), index=pd.to_datetime(x["DATE"], format="%m/%d/%Y"), name="PPUT")


def vix() -> pd.Series:
    """VIX (FRED VIXCLS), the 30-day implied volatility of the S&P 500, in % p.a."""
    raw = _fetch(FRED_URL.format("VIXCLS"), FUTURES_DIR / "fred_VIXCLS_daily.csv")
    df = pd.read_csv(io.BytesIO(raw), na_values=".")
    return pd.Series(df.iloc[:, 1].to_numpy(float), index=pd.to_datetime(df.iloc[:, 0]), name="VIX").dropna()


def true_range_ratio() -> dict[str, float]:
    """Ratio of the 100-day average true range to the 100-day mean |close-to-close change|.

    Measured on Yahoo Finance front-month futures with daily highs and lows (2000 to March 2024);
    bars with high <= low are dropped. Returns the median ratio over time for each ticker.
    """
    path = FUTURES_DIR / "yahoo_ohlc.csv"
    if not path.exists():
        import yfinance as yf

        FUTURES_DIR.mkdir(parents=True, exist_ok=True)
        d = yf.download(OHLC_TICKERS, start="2000-01-01", end="2024-04-01", auto_adjust=False, progress=False)
        d[["High", "Low", "Close"]].to_csv(path)
    d = pd.read_csv(path, header=[0, 1], index_col=0, parse_dates=True)
    out = {}
    for k in d["Close"].columns:
        x = pd.DataFrame({"h": d["High"][k], "l": d["Low"][k], "c": d["Close"][k]}).dropna()
        x = x[x["h"] > x["l"]]
        if len(x) < 500:
            continue
        pc = x["c"].shift(1)
        tr = pd.concat([x["h"] - x["l"], (x["h"] - pc).abs(), (x["l"] - pc).abs()], axis=1).max(axis=1)
        ratio = tr.rolling(100).mean() / (x["c"] - pc).abs().rolling(100).mean()
        out[k] = float(ratio.median())
    return out


def month_end_points(panel: pd.DataFrame) -> pd.DataFrame:
    """Last close of each month, labelled by month start (the layout of the Part I panel)."""
    return panel.resample("MS").last()


def zero_safe(x: pd.Series) -> pd.Series:
    """Replace non-positive or non-finite volatility estimates by NaN so that no position is opened."""
    return x.where(np.isfinite(x) & (x > 0))
