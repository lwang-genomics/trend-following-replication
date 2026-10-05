"""Universe, data sources and parameters for the replication.

The universe mirrors Lempérière et al. (2014), "Two centuries of trend following":
stock indices, 10-year government bonds and currencies for seven countries, plus
seven commodities, on monthly data. The paper uses Global Financial Data (paid);
here every series comes from a free public source (FRED / OECD, World Bank, Shiller).
"""

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
FIG_DIR = ROOT / "figures"
RES_DIR = ROOT / "results"
REPORT_DIR = ROOT / "report"

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
WORLD_BANK_URL = (
    "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/"
    "CMO-Historical-Data-Monthly.xlsx"
)
SHILLER_URL = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"


@dataclass(frozen=True)
class Asset:
    name: str
    sector: str  # Indices | Bonds | Currencies | Commodities
    source: str  # human-readable description of the series
    start: str | None = None  # first month used (None = first available)
    note: str = ""


COUNTRIES = {"US": "United States", "GB": "United Kingdom", "DE": "Germany", "JP": "Japan",
             "CA": "Canada", "AU": "Australia", "CH": "Switzerland"}

ASSETS = (
    [Asset(f"EQ_{c}", "Indices", f"OECD total share price index, {n} (FRED SPASTT01{c}M661N)")
     for c, n in COUNTRIES.items()]
    + [Asset(f"BD_{c}", "Bonds", f"10y bond price from OECD long-term yield, {n} (FRED IRLTLT01{c}M156N)")
       for c, n in COUNTRIES.items()]
    + [
        Asset("FX_GBP", "Currencies", "USD per GBP (FRED EXUSUK)", "1973-03"),
        Asset("FX_JPY", "Currencies", "USD per JPY (FRED 1/EXJPUS)", "1973-03"),
        Asset("FX_EUR", "Currencies", "USD per DEM to 1998, per EUR from 1999 (FRED EXGEUS, EXUSEU)", "1973-03"),
        Asset("FX_CAD", "Currencies", "USD per CAD (FRED 1/EXCAUS)", "1973-03"),
        Asset("FX_CHF", "Currencies", "USD per CHF (FRED 1/EXSZUS)", "1973-03"),
        Asset("FX_AUD", "Currencies", "USD per AUD (FRED EXUSAL)", "1973-03"),
        Asset("CRUDE", "Commodities", "WTI crude (FRED WTISPLC)", "1982-01",
              "US crude price controls until January 1981 (price flat in 63 of 96 months, 1974-81)"),
        Asset("NATGAS", "Commodities", "US natural gas (World Bank; IMF via FRED after)", "1985-01",
              "regulated wellhead prices before decontrol in the mid-1980s"),
        Asset("CORN", "Commodities", "Maize (World Bank; IMF via FRED after)"),
        Asset("WHEAT", "Commodities", "Wheat, US HRW (World Bank; IMF via FRED after)"),
        Asset("SUGAR", "Commodities", "Sugar, world (World Bank; IMF via FRED after)"),
        Asset("CATTLE", "Commodities", "Beef (World Bank; IMF via FRED after); proxy for live cattle"),
        Asset("COPPER", "Commodities", "Copper (World Bank; IMF via FRED after)"),
    ]
)
SECTORS = ["Commodities", "Currencies", "Bonds", "Indices"]

# World Bank Pink Sheet column -> (asset, FRED/IMF series used to extend it after the Pink Sheet ends)
WORLD_BANK_COLUMNS = {
    "Natural gas, US": ("NATGAS", "MHHNGSP"),
    "Maize": ("CORN", "PMAIZMTUSDM"),
    "Wheat, US HRW": ("WHEAT", "PWHEAMTUSDM"),
    "Sugar, world": ("SUGAR", "PSUGAISAUSDM"),
    "Beef **": ("CATTLE", "PBEEFUSDM"),
    "Copper": ("COPPER", "PCOPPUSDM"),
}

# Signal (Lempérière et al. 2014, eqs. 1-2)
MAIN_N = 5  # EMA decay, months
N_GRID = [2, 3, 5, 7, 10, 15, 20]  # Table 1 of the paper
LAG = 1  # eq. 2 as printed: signal from p(t-1), P&L over p(t) -> p(t+1)

# Periods
SAMPLE_START = "1960-01"
PUBLICATION_END = "2013-12"  # last full year before the paper (arXiv, April 2014)
OOS_START = "2014-01"
DECADES = [("1960s", "1960", "1969"), ("1970s", "1970", "1979"), ("1980s", "1980", "1989"),
           ("1990s", "1990", "1999"), ("2000–13", "2000", "2013"), ("2014–26", "2014", "2026")]

# Saturation fit
RUNNING_AVG_POINTS = 1000
BOOT_BLOCK = 12  # months, for the out-of-sample comparison
BOOT_N = 5000

# Published values (Lempérière et al. 2014, futures since 1960, n = 5 unless stated), for side-by-side tables
PAPER_TABLE1 = {2: (0.80, 5.9, 5.5), 3: (0.83, 6.1, 5.5), 5: (0.78, 5.7, 5.0), 7: (0.80, 5.9, 5.0),
                10: (0.76, 5.6, 5.1), 15: (0.65, 4.8, 4.5), 20: (0.57, 4.2, 3.3)}  # SR, t, t*
PAPER_TABLE2 = {"Currencies": (0.57, 3.6, 3.4, "05/1973"), "Commodities": (0.80, 5.9, 5.0, "01/1960"),
                "Bonds": (0.49, 2.8, 1.6, "05/1982"), "Indices": (0.41, 2.3, 2.1, "01/1982")}
PAPER_TABLE3 = {"1960s": (0.66, 2.1, 1.8), "1970s": (1.15, 3.64, 2.5), "1980s": (1.05, 3.3, 2.85),
                "1990s": (1.12, 3.5, 3.03), "2000–13": (0.75, 2.8, 1.9)}
PAPER_FIT = {"lin_a": 0.018, "lin_b": 0.038, "tanh_b": 0.075, "tanh_s_star": 0.89}
LONG_US_BLOCKS = [("1873–1899", "1873", "1899"), ("1900–1949", "1900", "1949"),
                  ("1950–1999", "1950", "1999"), ("2000–2023", "2000", "2023")]


# ====================================================================== Part II: practitioner rules, daily futures
#
# Daily back-adjusted futures prices from the pysystemtrade project (R. Carver, GPL-3), pinned to one commit
# so that every run sees the same data. Prices are in points, Panama back-adjusted across rolls, so price
# differences include roll yield (carry). Costs come from the same project's instrument configuration.

FUTURES_COMMIT = "4420802541a561b8de1b95ef3b43ccc708b2e987"  # 2024-05-01, data to 2024-03-28
FUTURES_URL = "https://raw.githubusercontent.com/pst-group/pysystemtrade/{}/data/futures/{}"
FUTURES_DIR = RAW_DIR / "futures"

# One contract per underlying (no minis or micros), every sector Clenow trades.
FUTURES = {
    "Equities": ["SP500", "NASDAQ", "DOW", "FTSE100", "DAX", "CAC", "AEX", "IBEX", "EUROSTX", "SMI", "HANG",
                 "NIKKEI", "KOSPI"],
    "Rates": ["US2", "US5", "US10", "US20", "US30", "BUND", "BOBL", "SHATZ", "GILT", "JGB", "CAD10", "BTP", "OAT",
              "EURIBOR"],
    "Currencies": ["EUR", "JPY", "GBP", "CHF", "AUD", "CAD", "NZD", "MXP"],
    "Energy": ["CRUDE_W", "CRUDE_ICE", "HEATOIL", "GASOILINE", "GASOIL", "GAS_US"],
    "Metals": ["GOLD", "SILVER", "COPPER", "PLAT", "PALLAD"],
    "Agriculturals": ["CORN", "WHEAT", "REDWHEAT", "SOYBEAN", "SOYMEAL", "SOYOIL", "SUGAR11", "COFFEE", "COCOA",
                      "COTTON2", "OJ", "RICE", "OATIES", "LIVECOW", "FEEDCOW", "LEANHOG"],
}
DAILY_SECTORS = list(FUTURES)
FUTURES_SECTOR = {m: sec for sec, ms in FUTURES.items() for m in ms}


@dataclass(frozen=True)
class ClenowRules:
    """The core trend model of A. Clenow, *Following the Trend* (2013), as parameters.

    Trend filter: trade long only while EMA(fast) > EMA(slow), short only while below.
    Entry: a close at the highest (lowest) close of the last `breakout` days.
    Exit: a trailing stop `stop_atr` ATRs from the best close since entry.
    Size: `risk` of capital per ATR(atr_window), fixed at entry (no rebalancing).
    ATR is the average true range, as in the book (see TRUE_RANGE_RATIO).
    """

    fast: int = 50
    slow: int = 100
    breakout: int = 50
    atr_window: int = 100
    stop_atr: float = 3.0
    risk: float = 0.002  # 20 bp of capital per daily ATR


CLENOW = ClenowRules()
# The data have closes only. The book's ATR is the average *true range* (high/low based), about twice the mean
# absolute close-to-close change (a Brownian motion gives 2.0). Measured on 31 front-month futures with daily
# OHLC from Yahoo Finance, 2000-2024: median ratio of 100-day means 1.89 (see futures.true_range_ratio).
# Stops and sizes in true ATRs are therefore converted with this ratio.
TRUE_RANGE_RATIO = 1.9
OHLC_TICKERS = ["ES=F", "NQ=F", "YM=F", "ZF=F", "ZN=F", "ZB=F", "6E=F", "6J=F", "6B=F", "6A=F", "6C=F", "6S=F",
                "CL=F", "NG=F", "HO=F", "RB=F", "GC=F", "SI=F", "HG=F", "PL=F", "ZC=F", "ZW=F", "ZS=F", "ZM=F",
                "ZL=F", "SB=F", "KC=F", "CC=F", "CT=F", "LE=F", "HE=F"]
DAILY_START = "1990-01-01"  # results from here; earlier data only warm the indicators up
DAILY_SPLIT = "2014-01-01"  # book (2013) and paper (2014) published: same split as Part I
EXEC_LAG = 1  # decide on the close of day t, trade on the close of day t+1 (the book trades the next open)
EMA_DAYS = [20, 50, 100, 200]  # paper's signal on daily data; 100 days ≈ 5 months, the paper's main n
MAIN_EMA_DAYS = 100
GRID_BREAKOUT = [20, 50, 100, 150, 200]
GRID_STOP = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
COST_RECENT = "2019-01-01"  # costs are converted to ATR units with each market's mean |Δp| from here on
# The spread file gives EURIBOR 0.26 points (≈ 50 ticks, 8 daily ATRs): an evident error. Use one tick.
SPREAD_OVERRIDES = {"EURIBOR": 0.005}
COST_STRESS = 3.0  # costs are today's; history was dearer, so also report costs ×3
DAILY_BOOT_BLOCK = 63  # trading days
DAILY_BOOT_N = 2000
VOL_DISPLAY = 0.10  # equity curves and drawdowns shown at 10% annual volatility (ex post scaling)

# Managed-futures benchmark: a public trend-following mutual fund (daily NAV with distributions).
BENCHMARK = "AQMIX"
BENCHMARK_NAME = "AQR Managed Futures Strategy (AQMIX)"

# Phase-I spot commodity -> futures with the same underlying (Part I's spot-vs-futures question)
SPOT_TO_FUTURES = {"CRUDE": "CRUDE_W", "NATGAS": "GAS_US", "CORN": "CORN", "WHEAT": "REDWHEAT",
                   "SUGAR": "SUGAR11", "CATTLE": "LIVECOW", "COPPER": "COPPER"}
