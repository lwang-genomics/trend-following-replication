// Replication of "Two centuries of trend following" on free data.
// Build from the repository root: uv run trendrep && uv run trendrep-report
#let res = json("../results/results.json")
#let T = res.tables
#let F = res.facts
#let num(x, d: 2) = {
  if x == none { return "–" }
  let neg = x < 0
  let parts = str(calc.round(calc.abs(x), digits: d)).split(".")
  let dec = if parts.len() > 1 { parts.at(1) } else { "" }
  (if neg { "−" } else { "" }) + parts.at(0) + (if d > 0 { "." + dec + "0" * (d - dec.len()) } else { "" })
}

#set document(title: "Trend Following: Replication and Out-of-Sample Test", author: "Liangxi Wang")
#set page(paper: "a4", margin: (x: 2.2cm, y: 2.2cm), numbering: "1")
#set text(font: ("Arial", "Helvetica Neue", "Helvetica"), size: 10pt)
#set par(justify: true, leading: 0.62em)
#set heading(numbering: "1.1")
#show heading.where(level: 1): it => block(above: 1.6em, below: 0.9em, text(size: 14pt, it))
#show heading.where(level: 2): it => block(above: 1.3em, below: 0.7em, text(size: 11.5pt, it))
#show figure.caption: set text(size: 9pt)
#show figure: set block(breakable: false, above: 1.2em, below: 1.2em)
#set figure(gap: 0.6em)

#let fig(path, caption) = figure(image("../figures/" + path, width: 100%), caption: caption)
#let mtable(t, caption, size: 9pt, left-cols: 1) = figure(
  text(size: size)[#set par(justify: false); #table(
    columns: t.header.len(),
    align: (x, y) => if x < left-cols { left } else { right },
    stroke: none,
    inset: (x: 4pt, y: 3pt),
    table.hline(stroke: 0.8pt),
    table.header(..t.header.map(h => text(weight: "bold", h))),
    table.hline(stroke: 0.5pt),
    ..t.rows.flatten().map(c => [#c]),
    table.hline(stroke: 0.8pt),
  )],
  caption: caption,
  kind: table,
)

#align(center)[
  #text(size: 19pt)[Trend Following: Replication and Out-of-Sample Test] \
  #v(0.3em)
  #text(size: 12pt)[Lempérière, Deremble, Seager, Potters & Bouchaud (2014), "Two centuries of trend following", \
    reproduced on free data and tested on the twelve years after publication] \
  #v(0.3em)
  #text(size: 10pt, fill: luma(110))[Liangxi Wang · monthly data #F.sample · October 2026 \
    #link("https://github.com/lwang-genomics/trend-following-replication")[github.com/lwang-genomics/trend-following-replication]]
]
#v(1em)
#outline(depth: 1, indent: auto)
#pagebreak()

= Summary

Lempérière et al. (2014, Capital Fund Management) show that a minimal trend-following rule earns significant
excess returns across commodities, currencies, stock indices and bonds: a t-statistic of about 5.9 on futures since
1960, and about 10 on spot data back to 1800. This note re-runs their rule on the same 27-market universe using only
free public data, checks how the data affect the result, and then asks the question a published result invites:
*did it hold after publication?*

- *The result replicates.* For 1960–2013 the aggregate Sharpe ratio is #num(F.headline.sr) (paper: 0.78), with
  t = #num(F.headline.t, d: 1) (5.7) and a drift-removed t\* = #num(F.headline.t_debiased, d: 1) (5.0). The trend P&L
  is only #num(F.headline.corr_trend_long) correlated with the long-only drift (paper: 0.15). Currencies and bonds
  match the paper closely. Commodities are much weaker on spot prices (Sharpe #num(F.sectors.Commodities.sr) vs
  0.80), as the paper itself anticipates, because spot data miss the futures' carry.
- *Saturation replicates.* A tanh fit of the next move on the signal saturates at
  s\* = #num(F.saturation.tanh_s_star) (paper: 0.89), beats the linear fit (F = #num(F.saturation.f_stat, d: 1)),
  and the cubic term is negative, as reported.
- *After publication the effect is weaker.* Over 2014–2026 the Sharpe ratio is #num(F.oos.sr_out)
  (t = #num(F.oos.t_out, d: 1)), against #num(F.oos.sr_in) in-sample. A block bootstrap of the in-sample months puts
  the probability of an out-of-sample Sharpe this low at #num(F.oos.p_oos_le_observed * 100, d: 0)%. So the result is
  weaker but not statistically rejected, and every n gives the same picture.
- *Two data traps are documented and avoided.* Most free series are *monthly averages*. Trading them the very next
  month manufactures a fake trend (Working, 1960). The paper's equation, which holds the position one month later,
  removes the artefact, and on markets with month-end data it reproduces the month-end result exactly
  (Sharpe #num(F.averaging.avg1) vs #num(F.averaging.eom0)). *Administered prices* (grain support, oil price
  controls) need a stale-price filter; without one, a single corn observation from 1972 (−467σ) cuts the
  1960–2013 Sharpe ratio from 0.82 to 0.34.
- *150 years of US data* (Shiller, from 1873) give a trend Sharpe of #num(F.long_us.sr) with
  t = #num(F.long_us.t, d: 1), positive in every 50-year block.

= The paper and what is replicated

The paper defines, for each market and an exponential moving average (EMA) time scale of $n$ months,

$ s_n (t) = (p(t-1) - ⟨p⟩_(n, t-1)) / (sigma_n (t-1)), quad
  Q_n (t) = sum_(t' < t) "sign"[s_n (t')] (p(t'+1) - p(t')) / (sigma_n (t'-1)), $

where $⟨p⟩_(n,t)$ is an EMA of past prices excluding $p(t)$ and $sigma_n$ is an EMA of absolute monthly
price changes. The position is long or short one unit of risk, with no costs. The paper uses monthly closes, $n = 5$,
27 markets (indices, 10-year bonds and currencies of seven countries, plus seven commodities) and Global Financial Data.
Its aggregate P&L is the sum of the risk-normalised P&Ls; Sharpe ratios need no risk-free rate because futures are
self-financed; t = Sharpe × √years; and the "de-biased" t\* is the t-stat of the intercept after regressing the trend
P&L on the long-only P&L.

*Two implementation details.* (i) As printed, eq. (2) pairs the signal built from $p(t'-1)$ with the price change
$p(t') -> p(t'+1)$, so the position is held one month after the information date; this replication follows the
equation literally (`lag = 1`). (ii) An EMA "with decay rate $n$ months" is implemented with weight $1/n$ on the newest
observation, and a 24-month warm-up precedes the first position.

= Data

#text(size: 8.5pt)[#set par(justify: false); #table(
  columns: (auto, 1fr, auto), stroke: none, inset: (x: 4pt, y: 3pt),
  table.hline(stroke: 0.8pt),
  table.header([*Sector*], [*Free source (paper: Global Financial Data)*], [*From*]),
  table.hline(stroke: 0.5pt),
  [Indices (7)], [OECD total share price indices (FRED `SPASTT01..M661N`)], [1955–60],
  [Bonds (7)], [OECD 10-year yields (FRED `IRLTLT01..M156N`), turned into a 10-year bond price by exact monthly repricing], [1953–69; Japan 1989],
  [Currencies (6)], [Fed exchange rates vs USD (FRED); Deutsche mark spliced to the euro in 1999], [1973 (end of Bretton Woods)],
  [Commodities (7)], [World Bank "Pink Sheet": maize, US HRW wheat, sugar, beef (live-cattle proxy), copper, US natural gas; WTI crude (FRED); IMF series extend the Pink Sheet], [1960; natural gas 1985; crude 1982],
  [US long history], [Shiller: S&P composite and 10-year rate], [1871; bond 1953],
  table.hline(stroke: 0.8pt),
)]

Start dates follow the paper's rule that only freely traded, moving prices can trend. Currencies start after Bretton
Woods; crude starts after US oil price controls ended in 1981 (the price was flat in 63 of 96 months in 1974–81);
natural gas starts after wellhead decontrol.

= Three data checks

== Monthly averages fake a trend unless the position is lagged

The OECD, Fed and World Bank monthly series are averages of daily prices. Averaging a random walk gives its monthly
changes a lag-1 autocorrelation of 0.25 (Working, 1960), and every series here shows 0.25–0.35. A rule that trades the
month right after the signal harvests that artefact. For the markets where free daily data exist (six currencies and
the US 10-year), @tbl-avg compares averaged and month-end prices directly.

#mtable(T.averaging, [Monthly averages vs month-end closes, $n = 5$. AC(1): lag-1 autocorrelation of monthly log changes. Lag 0 trades the next month; lag 1 is eq. (2) as printed.], size: 8pt) <tbl-avg>

#fig("fig07_averaging_check.png")[Mean Sharpe ratio over the seven markets in @tbl-avg.]

Month-end prices have no autocorrelation (≈0.03). On averaged data, lag 0 more than doubles the Sharpe ratio
(#num(F.averaging.avg0)), a pure artefact; a simulation in the test suite shows that the same rule earns a mean
t-stat of about 2 on averaged *random walks*. Lag 1 removes the artefact, and its Sharpe on averaged data
(#num(F.averaging.avg1)) matches the realistic month-end, lag-0 strategy (#num(F.averaging.eom0)). The main
specification (averaged data, lag 1) is therefore both faithful to the paper and realistic. The cost is that very
short time scales, whose information decays within a month, look weaker than in the paper (@tbl-n).

== Administered prices need a stale-price filter

Grain prices in the 1960s–70s were set by support programmes and often unchanged for months. $sigma_n$ then collapses
towards zero, and the first real move is divided by almost nothing: corn in January 1972 contributes −467σ. Without
a filter, this single observation pulls the 1960–2013 Sharpe ratio from 0.82 to 0.34. The paper requires "prices actually moving
(no gaps)". Here a market is traded in a month only if its price changed in at least 10 of the previous 12 months.
The rule uses only past data, and the result hardly depends on the threshold (Sharpe 0.74, 0.74 and 0.70 for 10, 11 and
12 of 12).

== Interpolated history is not data

Shiller's long-term rate before 1953 is interpolated from annual observations. Its monthly changes have a lag-1
autocorrelation of 0.92 (0.31 afterwards), which handed the US bond a spurious trend Sharpe of 2.0 in 1873–1899. The
long-history bond therefore starts in 1953.

= Replication, 1960–2013

#fig("fig01_aggregate_pnl.png")[Aggregate trend P&L ($n = 5$, σ units, summed over markets) and the long-only drift. Shaded: after publication.]

#mtable(T.horizons, [Paper's Table 1 vs this replication, 1960–2013, plus the out-of-sample Sharpe ratio. t\*: drift-removed t-stat.], size: 8.5pt) <tbl-n>

#fig("fig03_sharpe_by_n.png")[Sharpe ratio by EMA time scale: paper (futures), replication (spot proxies), and after publication.]

#mtable(T.sectors, [Paper's Table 2 vs this replication by sector, $n = 5$, through 2013, with the 2014–2026 Sharpe ratio. The paper's bond and index futures start in 1982; the spot proxies start around 1960.], size: 7pt)

#fig("fig02_sector_pnl.png")[Cumulative trend P&L by sector.]

#mtable(T.decades, [Paper's Table 3 vs this replication by decade, $n = 5$; the last row is after publication.], size: 8.5pt)

#fig("fig04_sharpe_by_decade.png")[Sharpe ratio by decade. Orange: after publication.]

The aggregate replication is close for $n >= 5$: Sharpe 0.53–0.74 vs 0.57–0.80. Every decade from the 1960s to 2013 is
positive. Sector by sector, currencies (#num(F.sectors.Currencies.sr) vs 0.57) and bonds
(#num(F.sectors.Bonds.sr) vs 0.49) match; indices are stronger on the longer spot history. Commodities are the clear
gap (#num(F.sectors.Commodities.sr) vs 0.80). The paper reports only a 65% spot–futures correlation for commodities,
because futures add a carry (roll-yield) term that spot prices lack. Averaged monthly commodity prices, and beef as a
stand-in for live cattle, add noise.

= The signal saturates

#fig("fig05_saturation.png")[Next normalised move vs signal, pooled over markets ($n = 5$, #F.saturation.n_points points): running average over 1,000 points, linear fit and tanh fit.]

#text(size: 9pt)[#table(
  columns: 5, stroke: none, inset: (x: 5pt, y: 3pt), align: (left, right, right, right, right),
  table.hline(stroke: 0.8pt),
  table.header([*Fit*], [*a*], [*b*], [*s\**], [*Note*]),
  table.hline(stroke: 0.5pt),
  [Linear, paper], [0.018], [0.038], [–], [],
  [Linear, ours], [#num(F.saturation.lin_a, d: 3)], [#num(F.saturation.lin_b, d: 3)], [–], [],
  [tanh, paper], [–], [0.075], [0.89], [],
  [tanh, ours], [#num(F.saturation.tanh_a, d: 3)], [#num(F.saturation.tanh_b, d: 3)], [#num(F.saturation.tanh_s_star) ± #num(F.saturation.tanh_s_star_se)], [F vs linear = #num(F.saturation.f_stat, d: 1)],
  table.hline(stroke: 0.8pt),
)]

The predictive slope flattens for strong signals. The tanh model is preferred to the linear one, the cubic coefficient
is negative (#num(F.saturation.cubic_s3, d: 4)), and the saturation scale s\* is close to the paper's. The intercept
is larger here because the spot proxies' drift is larger in σ units; the signal is noisy, so s\* is only loosely
determined.

= After publication: 2014–2026

#text(size: 9pt)[#table(
  columns: 5, stroke: none, inset: (x: 5pt, y: 3pt), align: (left, right, right, right, right),
  table.hline(stroke: 0.8pt),
  table.header([*Period*], [*Years*], [*Sharpe*], [*t-stat*], [*Long-only Sharpe*]),
  table.hline(stroke: 0.5pt),
  [1960–2013 (in sample)], [#num(F.oos.years_in, d: 0)], [#num(F.oos.sr_in)], [#num(F.oos.t_in, d: 1)], [#num(F.oos.long_sr_in)],
  [2014–2026 (after publication)], [#num(F.oos.years_out, d: 1)], [#num(F.oos.sr_out)], [#num(F.oos.t_out, d: 1)], [#num(F.oos.long_sr_out)],
  table.hline(stroke: 0.8pt),
)]

The aggregate Sharpe ratio fell from #num(F.oos.sr_in) to #num(F.oos.sr_out) after publication, and
#F.oos_years_negative of #F.oos_years calendar years were negative. Two tests put this in proportion:

- *Difference of Sharpe ratios:* z = #num(F.oos.z_diff), using the standard error √(1/Y#sub[1] + 1/Y#sub[2]).
- *Bootstrap:* drawing 12.75-year paths from the in-sample months (12-month blocks), an out-of-sample Sharpe at or
  below #num(F.oos.sr_out) occurs #num(F.oos.p_oos_le_observed * 100, d: 0)% of the time; the 90% range is
  #num(F.oos.sr_sim_5) to #num(F.oos.sr_sim_95).

So the post-publication period is unusually weak but not inconsistent with the historical effect. With a Sharpe ratio
near 0.7, drawdowns of several years are expected: the paper itself notes that their typical length is about 1/S²
years. The weakness is broad, not one sector: indices #num(F.sectors.Indices.sr_oos), bonds
#num(F.sectors.Bonds.sr_oos), currencies #num(F.sectors.Currencies.sr_oos), commodities
#num(F.sectors.Commodities.sr_oos). 2022, the year of the inflation shock, was the best year since 2014. The long-only
drift also weakened (#num(F.oos.long_sr_in) → #num(F.oos.long_sr_out)), so the period was poor for simple
directional strategies in general.

#fig("fig06_rolling_10y.png")[Trailing 10-year average trend P&L per market (σ units per year).]

The paper reports that the 10-year performance of the trend was never negative in two centuries. On these free spot
proxies it does dip below zero: briefly in 1996 (#num(F.rolling10_min, d: 2) at the low, #F.rolling10_min_date)
and again around 2018–2021. So that claim does not replicate on this data, even before publication. The likely cause
is the weaker commodity sector, which carried much of the paper's performance.

= 150 years of US data

#fig("fig08_us_since_1871.png")[Cumulative trend P&L on the S&P composite (from 1873) and the US 10-year bond (from 1953), Shiller data.]

#mtable(T.long_us, [Trend on US equity and bonds, Shiller data, $n = 5$, lag 1.])

On US data alone, the trend has a Sharpe of #num(F.long_us.sr) over #num(F.long_us.years, d: 0) years
(t = #num(F.long_us.t, d: 1), drift-removed #num(F.long_us.t_debiased, d: 1)) and is positive in every 50-year
block, consistent with the paper's long-history finding.

= Conclusions and limitations

The paper's central claims replicate on free data: a significant, drift-independent trend effect across asset
classes and decades, and saturation of the signal. Its size depends on details the paper does not dwell on. Monthly
averages fake a trend unless the position is lagged, administered prices must be filtered, interpolated history must
be excluded, and spot commodities miss most of the futures' trend. After publication the effect weakened to a Sharpe
ratio of about 0.27, which is low but within what its own history allows.

Limitations: spot and index proxies instead of futures (no carry; commodities in particular); monthly averages for
most series; no transaction costs; a fictitious P&L without portfolio-level risk targeting; and 27 markets, not a full
CTA universe.

*Next steps.* (i) Daily futures and the practitioner's version of the rule, the moving-average and breakout system
with ATR position sizing from A. Clenow's _Following the Trend_. (ii) Trend following as a convex overlay for a
long-only book (Dao et al., 2016, _Tail protection for long investors_), combined with the inverse-volatility study in
#link("https://github.com/lwang-genomics/inverse-vol-futures-overlay")[inverse-vol-futures-overlay].

= Appendix: code and reproducibility

`uv run trendrep` downloads the raw data once (cached in `data/raw/`, not committed), runs every analysis and writes
`results/` and `figures/`. `uv run trendrep-report` compiles this PDF, and `uv run pytest` runs the tests. The tests
check the EMA and P&L against hand calculations and verify that there is no look-ahead (changing later prices leaves
all earlier signals and P&L unchanged). They also verify that random walks give t-stats centred on zero with unit
spread, that monthly averaging fakes a trend at lag 0 but not at lag 1, that trending series are profitable, that
stale prices are not traded, and that the saturation fit and the de-biasing recover known parameters.

*Reference.* Y. Lempérière, C. Deremble, P. Seager, M. Potters, J.-P. Bouchaud (2014), "Two centuries of trend
following", _Journal of Investment Strategies_ 3(3); arXiv:1404.3274.
