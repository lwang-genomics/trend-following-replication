"""Download, cache and assemble the monthly price panel.

All raw files are cached under data/raw/ (not committed). The panel has one
column per asset (see config.ASSETS), monthly, indexed by month start.
"""

import io
import time
import urllib.request

import numpy as np
import pandas as pd

from .config import (
    ASSETS,
    COUNTRIES,
    FRED_URL,
    RAW_DIR,
    SHILLER_URL,
    WORLD_BANK_COLUMNS,
    WORLD_BANK_URL,
)


def _fetch(url: str, path, retries: int = 3) -> bytes:
    """Download `url` to `path` once; later calls read the cached file."""
    if not path.exists():
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        for attempt in range(retries):
            try:
                # default Python-urllib client: FRED rejects unrecognised custom user agents
                with urllib.request.urlopen(url, timeout=60) as r:
                    path.write_bytes(r.read())
                break
            except OSError:
                if attempt == retries - 1:
                    raise
                time.sleep(2 * (attempt + 1))
    return path.read_bytes()


def fred(series_id: str) -> pd.Series:
    """Monthly FRED series indexed by month start ('.' = missing)."""
    raw = _fetch(FRED_URL.format(series_id), RAW_DIR / f"fred_{series_id}.csv")
    df = pd.read_csv(io.BytesIO(raw), na_values=".")
    s = pd.Series(df.iloc[:, 1].to_numpy(dtype=float), index=pd.to_datetime(df.iloc[:, 0]), name=series_id)
    return s.dropna()


def world_bank() -> pd.DataFrame:
    """World Bank Commodity Price Data ('Pink Sheet'), monthly averages from 1960."""
    raw = _fetch(WORLD_BANK_URL, RAW_DIR / "world_bank_pink_sheet.xlsx")
    x = pd.read_excel(io.BytesIO(raw), sheet_name="Monthly Prices", header=4)
    x = x.rename(columns={x.columns[0]: "date"}).iloc[1:]  # first row holds units
    x = x[x["date"].astype(str).str.match(r"^\d{4}M\d{2}$")]
    x.index = pd.to_datetime(x["date"].str.replace("M", "-") + "-01")
    return x[list(WORLD_BANK_COLUMNS)].apply(pd.to_numeric, errors="coerce")


def shiller() -> pd.DataFrame:
    """Shiller's monthly S&P composite price and long-term interest rate (GS10), from 1871."""
    raw = _fetch(SHILLER_URL, RAW_DIR / "shiller_ie_data.xls")
    x = pd.read_excel(io.BytesIO(raw), sheet_name="Data", header=7)
    x = x[pd.to_numeric(x["Date"], errors="coerce").notna()]
    d = x["Date"].astype(float)
    year = d.astype(int)
    month = ((d - year) * 100).round().astype(int)  # 1871.1 is October
    idx = pd.to_datetime({"year": year, "month": month, "day": 1})
    out = pd.DataFrame({"P": pd.to_numeric(x["P"], errors="coerce").to_numpy(),
                        "GS10": pd.to_numeric(x["Rate GS10"], errors="coerce").to_numpy()}, index=idx)
    return out.dropna()


def bond_price_from_yield(yield_pct: pd.Series, maturity: int = 10) -> pd.Series:
    """Price index of a constant-maturity bond, repriced each month at the new yield.

    Each month, a par bond with coupon y(t-1) and `maturity` years is repriced at y(t):
    the exact price change (duration and convexity), without coupon carry, which is
    the spot analogue of a bond-futures price change.
    """
    y = yield_pct.dropna() / 100.0
    y_prev, y_new = y.shift(1).iloc[1:], y.iloc[1:]
    t = np.arange(1, maturity + 1)
    coupon = y_prev.to_numpy()[:, None]
    disc = (1.0 + y_new.to_numpy()[:, None]) ** -t
    price = (coupon * disc).sum(axis=1) + disc[:, -1]  # per unit face, par = 1 at y_prev
    rel = pd.Series(price, index=y_new.index)
    return pd.concat([pd.Series([1.0], index=y.index[:1]), rel.cumprod()])


def _chain(base: pd.Series, extension: pd.Series) -> pd.Series:
    """Extend `base` after its last date with the returns of `extension`."""
    base = base.dropna()
    ext = extension.dropna()
    ext = ext[ext.index >= base.index[-1]]
    if len(ext) < 2:
        return base
    tail = base.iloc[-1] * ext / ext.iloc[0]
    return pd.concat([base, tail.iloc[1:]])


def build_panel() -> pd.DataFrame:
    """Monthly prices for every asset in config.ASSETS, each from its stated start date."""
    cols: dict[str, pd.Series] = {}
    for c in COUNTRIES:
        cols[f"EQ_{c}"] = fred(f"SPASTT01{c}M661N")
        cols[f"BD_{c}"] = bond_price_from_yield(fred(f"IRLTLT01{c}M156N"))

    cols["FX_GBP"] = fred("EXUSUK")
    cols["FX_AUD"] = fred("EXUSAL")
    for code, sid in [("JPY", "EXJPUS"), ("CAD", "EXCAUS"), ("CHF", "EXSZUS")]:
        cols[f"FX_{code}"] = 1.0 / fred(sid)
    dem = 1.0 / fred("EXGEUS")  # USD per DEM, to 2001
    eur = fred("EXUSEU")  # USD per EUR, from 1999
    cols["FX_EUR"] = _chain(dem[dem.index <= "1999-01-01"], eur)

    cols["CRUDE"] = fred("WTISPLC")
    wb = world_bank()
    for col, (name, ext_id) in WORLD_BANK_COLUMNS.items():
        cols[name] = _chain(wb[col], fred(ext_id))

    panel = pd.DataFrame(cols)
    for a in ASSETS:
        if a.start is not None:
            panel.loc[panel.index < pd.Timestamp(a.start), a.name] = np.nan
    return panel[[a.name for a in ASSETS]].sort_index()


LONG_BOND_START = "1953-04"  # Shiller's GS10 before this is annual data interpolated to monthly


def build_us_long() -> pd.DataFrame:
    """US equity (S&P composite, from 1871) and 10y bond price (from 1953), monthly (Shiller).

    Before April 1953 Shiller's long rate is interpolated from annual observations: its
    monthly changes have a lag-1 autocorrelation of 0.92 (0.31 afterwards), which would
    hand a trend follower spurious profits. The bond therefore starts in 1953.
    """
    sh = shiller()
    gs10 = sh["GS10"][sh.index >= LONG_BOND_START]
    return pd.DataFrame({"EQ_US_1871": sh["P"], "BD_US_1871": bond_price_from_yield(gs10)})


def month_end(series_id: str) -> pd.Series:
    """Last daily observation of each month from a daily FRED series, labelled by month start."""
    return fred(series_id).resample("MS").last()


def build_month_end_panel() -> pd.DataFrame:
    """Month-end closes for the markets where free daily data exists (FX from 1973, US 10y from 1962).

    Used to measure how monthly averaging changes the trend results. There is no free
    daily Deutsche mark series, so FX_EUR starts with the euro in 1999.
    """
    cols = {
        "FX_GBP": month_end("DEXUSUK"),
        "FX_JPY": 1.0 / month_end("DEXJPUS"),
        "FX_CAD": 1.0 / month_end("DEXCAUS"),
        "FX_CHF": 1.0 / month_end("DEXSZUS"),
        "FX_AUD": month_end("DEXUSAL"),
        "FX_EUR": month_end("DEXUSEU"),
        "BD_US": bond_price_from_yield(month_end("DGS10")),
    }
    panel = pd.DataFrame(cols)
    fx = [c for c in panel if c.startswith("FX")]
    panel.loc[panel.index < "1973-03-01", fx] = np.nan
    return panel
