# Two centuries of trend following: replication and out-of-sample test

[![CI](https://github.com/lwang-genomics/trend-following-replication/actions/workflows/ci.yml/badge.svg)](https://github.com/lwang-genomics/trend-following-replication/actions/workflows/ci.yml)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

A replication of **Lempérière, Deremble, Seager, Potters & Bouchaud (2014), "Two centuries of trend following"**
([arXiv:1404.3274](https://arxiv.org/abs/1404.3274)) using only **free public data** (FRED/OECD, World Bank, Shiller).
It is followed by the test a published result invites: **did it hold in the twelve years after publication?**

📄 **Report:** [`report/trend_following_replication.pdf`](report/trend_following_replication.pdf)

---

## Findings

| | Result |
|---|---|
| **Replicates** | 1960–2013, 27 markets, n = 5 months: Sharpe **0.74** (paper 0.78), t = **5.4** (5.7), drift-removed t\* = **4.5** (5.0). Correlation with the long-only drift is 0.18 (paper 0.15). |
| **Sectors** | Currencies (0.53 vs 0.57) and bonds (0.45 vs 0.49) match. Commodities are much weaker on spot prices (0.17 vs 0.80), because spot data miss the futures' carry, as the paper notes. |
| **Saturation** | A tanh fit of the next move on the signal saturates at s\* = 1.01 (paper 0.89) and beats the linear fit (F = 11). The cubic term is negative, as reported. |
| **After publication** | 2014–2026: Sharpe **0.27** (t = 1.0). That's weaker, but a bootstrap of the in-sample history gives a 9% chance of a period this weak, so the effect is not statistically rejected. |
| **150 years of US data** | Trend on US equities (from 1873) and bonds (from 1953): Sharpe 0.45, t = 5.5, positive in every 50-year block. |

<p align="center">
  <img src="figures/fig01_aggregate_pnl.png" width="80%"><br>
  <em>Aggregate trend P&L (n = 5, σ units) vs the long-only drift; shaded: after publication.</em>
</p>

<p align="center">
  <img src="figures/fig03_sharpe_by_n.png" width="80%"><br>
  <em>Sharpe ratio by EMA time scale: paper (futures), replication (1960–2013) and after publication.</em>
</p>

## Three data traps, and how they are handled

1. **Monthly averages fake a trend.** Most free series are monthly averages of daily prices. Averaging a random walk
   gives its monthly changes a lag-1 autocorrelation of 0.25 (Working, 1960), and the data show 0.25–0.35.
   - Trading the very next month on such data *doubles* the Sharpe ratio (0.55 vs 0.22) without any real edge.
   - The paper's eq. (2), read literally, holds the position one month later. That removes the artefact, and on
     markets with free month-end data it matches the realistic month-end result exactly (0.22 vs 0.22).
2. **Administered prices.** Grain support programmes and US oil price controls produce long stretches of unchanged
   prices, so σ shrinks to zero.
   - A single corn observation (January 1972, −467σ) cuts the 1960–2013 Sharpe ratio from 0.82 to 0.34.
   - Fix: a stale-price filter that trades only if the price moved in ≥ 10 of the last 12 months. It uses past data
     only, and the result is robust to the threshold.
3. **Interpolated history.** Shiller's long rate before 1953 is annual data interpolated to monthly (lag-1
   autocorrelation 0.92), which gave a fake bond-trend Sharpe of 2.0. The long-history bond starts in 1953.

<p align="center">
  <img src="figures/fig07_averaging_check.png" width="65%"><br>
  <em>Mean Sharpe ratio on 6 currencies + US 10y: monthly averages vs month-end closes, lag 0 vs lag 1.</em>
</p>

## Method

The signal and P&L follow the paper's eqs. (1)–(2):

```
s_n(t) = (p(t-1) − EMA_n[p](t-1)) / σ_n(t-1)         σ_n = EMA_n of |monthly price change|
Q_n(t) = Σ sign[s_n(t')] · (p(t'+1) − p(t')) / σ_n(t'-1)
```

- **Universe.** Stock indices, 10-year bonds and currencies for 7 countries (US, UK, Germany, Japan, Canada,
  Australia, Switzerland), plus 7 commodities: crude, natural gas, corn, wheat, sugar, cattle (beef proxy) and copper.
- **Statistics.** Sharpe and t = Sharpe·√years are computed as in the paper. The drift-removed t\* is the alpha
  t-stat from regressing the trend P&L on the long-only P&L. The out-of-sample test uses a block bootstrap.

## Reproduce

```bash
uv sync                   # Python 3.12 environment from uv.lock
uv run trendrep           # download data once (data/raw/), run everything, write results/ and figures/
uv run trendrep-report    # compile the PDF report (Typst)
uv run pytest             # 12 tests, synthetic data only
```

The tests check the EMA and P&L against hand calculations and verify that there is **no look-ahead**. They also
check that random walks give t-stats centred on zero with unit spread, that **monthly averaging fakes a trend at
lag 0 but not at lag 1**, that trending series are profitable, that stale prices are not traded, and that the
saturation fit and de-biasing recover known parameters.

## Code

```
src/trendrep/
  config.py    universe, sources, start dates (with reasons), parameters, the paper's published values
  data.py      FRED / World Bank / Shiller download and cache, bond prices from yields, month-end panel
  signal.py    the paper's signal and P&L, stale-price filter
  analysis.py  Sharpe, t, de-biased t*, saturation (tanh) fit, out-of-sample test
  study.py     every table and figure of the report
  plots.py     figures
```

## Limitations and next steps

- **Limitations:** spot and index proxies instead of futures (no carry), monthly averages for most series, no
  costs, and 27 markets rather than a full CTA universe.
- **Next:**
  1. Daily futures and the practitioner's rules from A. Clenow's *Following the Trend*: moving-average filter,
     breakouts, ATR sizing.
  2. Trend following as a convex overlay for a long-only book (Dao et al., 2016), connected to
     [inverse-vol-futures-overlay](https://github.com/lwang-genomics/inverse-vol-futures-overlay).

## Context

An independent replication by Liangxi Wang, computational scientist (Genomics PhD), not affiliated with any employer
or with the paper's authors. Implemented with AI-assisted coding (Claude Code). Research questions, design decisions,
data checks and interpretation are my own; all results are reproducible from the code. Research code, **not
investment advice**. Licence: MIT. Data remain subject to their providers' terms.
