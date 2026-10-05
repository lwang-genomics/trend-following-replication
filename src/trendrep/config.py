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
