// Replication of "Two centuries of trend following" on free data (Part I),
// and Clenow's practitioner rules against the paper's signal on daily futures (Part II).
// Build from the repository root: uv run trendrep && uv run trendrep-daily && uv run trendrep-report
#let res = json("../results/results.json")
#let T = res.tables
#let F = res.facts
#let dres = json("../results/results_daily.json")
#let DT = dres.tables
#let DF = dres.facts
#let R(name) = DF.rules_stats.at(name)
#let SP(key) = DF.spanning.at(key)
#let num(x, d: 2) = {
  if x == none { return "–" }
  let neg = x < 0
  let parts = str(calc.round(calc.abs(x), digits: d)).split(".")
  let dec = if parts.len() > 1 { parts.at(1) } else { "" }
  (if neg { "−" } else { "" }) + parts.at(0) + (if d > 0 { "." + dec + "0" * (d - dec.len()) } else { "" })
}

#set document(title: "Trend Following: Replication, Out-of-Sample Test and Practitioner Rules", author: "Liangxi Wang")
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
#let mtable(t, caption, size: 9pt, left-cols: 1, left-also: (), columns: auto) = figure(
  text(size: size)[#set par(justify: false); #table(
    columns: if columns == auto { t.header.len() } else { columns },
    align: (x, y) => if x < left-cols or x in left-also { left } else { right },
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
  #text(size: 19pt)[Trend Following: Replication, Out-of-Sample Test \ and Practitioner Rules] \
  #v(0.3em)
  #text(size: 12pt)[Part I: Lempérière, Deremble, Seager, Potters & Bouchaud (2014), "Two centuries of trend
    following", reproduced on free data and tested after publication. \
    Part II: the core model of A. Clenow's _Following the Trend_ (2013) against the paper's signal, on daily futures] \
  #v(0.3em)
  #text(size: 10pt, fill: luma(110))[Liangxi Wang · monthly data #F.sample · daily futures 1990-01 → 2024-03 · October 2026 \
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

Part II takes the practitioner's side. Clenow's _Following the Trend_ argues that a simple, diversified trend
model with a moving-average filter, breakout entries, a trailing stop and volatility sizing captures much of what
professional trend followers earn, and that the exact rule matters less than diversification and risk sizing. The
model is run on #DF.n_markets daily back-adjusted futures (1990 to March 2024, net of costs) next to the paper's
signal on the same data.

- *Both work, and they are mostly the same bet.* Net Sharpe ratios for 1990–2013 are #num(R("Clenow core").sr_net_in)
  (Clenow) and #num(R("Paper EMA, 100 d").sr_net_in) (paper's EMA, 100 days ≈ 5 months), and
  #num(R("Clenow core").sr_net_post) and #num(R("Paper EMA, 100 d").sr_net_post) for 2014–2024. Their monthly
  returns are #num(R("Clenow core").corr_paper) correlated, and neither has a significant alpha over the other
  (t = #num(SP("Clenow core on paper EMA (100 d) | 1990–2013").alpha_t, d: 1) and
  #num(SP("Paper EMA (100 d) on Clenow core | 1990–2013").alpha_t, d: 1)).
- *The stop changes the shape, not the edge.* Clenow's model is in the market #num(R("Clenow core").in_market * 100, d: 0)%
  of the time. At equal volatility its worst drawdown is #num(-R("Clenow core").maxdd_10 * 100, d: 0)% against
  #num(-R("Paper EMA, 100 d").maxdd_10 * 100, d: 0)%, and its monthly skew is #num(R("Clenow core").skew_m) against
  #num(R("Paper EMA, 100 d").skew_m).
- *The parameters do not matter much, and cannot be tuned.* Across 30 breakout and stop settings, the net Sharpe ratio
  ranges from #num(DF.grid.in_min) to #num(DF.grid.in_max) before 2014 and from #num(DF.grid.post_min) to
  #num(DF.grid.post_max) after. The in-sample ranking does not predict the later one (rank correlation
  #num(DF.grid.rank_corr)).
- *A real trend fund.* The two rules together explain #num(DF.benchmark.r2_paper_and_core * 100, d: 0)% of the
  monthly variance of a public managed-futures fund (#DF.benchmark.name, 2010–2024).
- *Part I's weak commodities are mostly a data effect.* On the same seven commodities and months, the paper's monthly
  rule earns a Sharpe ratio of #num(DF.spot_vs_futures.all.spot) on averaged spot prices and
  #num(DF.spot_vs_futures.all.fut0) on month-end futures. Most of the gap comes from the one-month delay that averaged
  data force, not from carry.

#text(size: 9pt, fill: luma(90))[Part I: @sec-paper to @sec-us. Part II: @sec-p2 to @sec-spot. Conclusions: @sec-conc.]

= The paper and what is replicated <sec-paper>

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
stand-in for live cattle, add noise. Part II (@sec-spot) tests this on futures: most of the gap comes from the
one-month delay that averaged data force, not from carry.

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

= 150 years of US data <sec-us>

#fig("fig08_us_since_1871.png")[Cumulative trend P&L on the S&P composite (from 1873) and the US 10-year bond (from 1953), Shiller data.]

#mtable(T.long_us, [Trend on US equity and bonds, Shiller data, $n = 5$, lag 1.])

On US data alone, the trend has a Sharpe of #num(F.long_us.sr) over #num(F.long_us.years, d: 0) years
(t = #num(F.long_us.t, d: 1), drift-removed #num(F.long_us.t_debiased, d: 1)) and is positive in every 50-year
block, consistent with the paper's long-history finding.


= Part II: practitioner rules on daily futures <sec-p2>

Part I tested the academic version of trend following: one signal, monthly data, no costs. Practitioners trade
something that looks different. The core model of Clenow's _Following the Trend_ (2013) trades daily, enters on
breakouts, exits on trailing stops and sizes positions by volatility. The book's thesis is that this kind of simple
model, run on a diversified futures universe, captures much of what large trend-following funds earn. Part II asks
three questions:

+ Is the practitioner's rule better than, or different from, the paper's signal on the same data?
+ What does each component (filter, breakout, stop) contribute, and do the parameters matter?
+ How closely do both track a real managed-futures fund?

== Data, rules and costs

*Futures.* Daily back-adjusted ("Panama") prices of #DF.n_markets futures from the open-source pysystemtrade project,
pinned to one commit (#raw(DF.futures_commit.slice(0, 10)), data to 28 March 2024). Back-adjustment shifts history at
each roll, so price *changes* are those of the contract held, roll yield included. All P&L is therefore computed in
price points and converted to capital through risk-based sizing; no price level is used. Results start in January 1990
(#DF.markets_alive_1990 markets), and later contracts join as their data begin.

#mtable(DT.universe, [Futures universe. Cost: median cost per contract and side, as a percentage of the daily ATR.], size: 7.5pt, left-also: (5,), columns: (auto, auto, auto, auto, auto, 1fr)) <tbl-univ>

*Clenow's core model* (parameters as described in the book; `config.ClenowRules`):
- trend filter: long trades only while the 50-day EMA is above the 100-day EMA, short trades only while below;
- entry: a close at the highest (lowest) close of the last 50 days, in the filter's direction;
- exit: a trailing stop 3 ATRs from the best close since entry;
- size: 0.2% of capital per ATR(100), set at entry and not rebalanced.

*Closes only.* The data have no highs and lows, so the average true range is estimated from closes. On
#DF.true_range.n front-month futures with daily OHLC (Yahoo Finance, 2000–2024), the 100-day true range averages
#num(DF.true_range.median) times the mean absolute close-to-close change (range #num(DF.true_range.min) to
#num(DF.true_range.max), against 2 for a Brownian motion). ATR is therefore #num(DF.true_range.used, d: 1) × the mean
|Δp| over 100 days. Without this correction the "3 ATR" stop would be about half as wide as the book's.

*The paper's signal on daily data:* position = sign(p − EMA#sub[n]\[p\]) / σ#sub[n], with σ#sub[n] the EMA of |Δp|,
rebalanced daily, n = 100 days (≈ the paper's 5 months), and the same risk per market as Clenow's model.

*Components.* Three partial models isolate the parts of the core model: _Filter only_ (always positioned with the EMA
filter), _Breakout only_ (stop-and-reverse on 50-day highs and lows) and _Filter + breakout_ (breakout entries, exit
when the filter flips).

*Execution and costs.* Decisions use closes up to day t and are traded at the close of day t+1 (the book trades the
next open). Costs per contract and side are half the bid-ask spread plus commission, from the same project's
configuration. They are converted to a fraction of each market's recent ATR (median #num(DF.cost_atr_median * 100, d: 1)%)
and charged at that fraction of the ATR at the time of each trade, so they scale with volatility through history.
Every roll trades the position twice. These are today's costs, so results are also shown with costs tripled. EURIBOR's
spread estimate in the source (0.26 points, about 50 ticks) is an evident error and is replaced by one tick. P&L is
not compounded, and positions are fractional (a large account).

== Practitioner rule vs the paper's signal

#mtable(DT.ladder, [Net Sharpe ratios by rule, 1990–2013 unless stated. Max drawdown and skew over 1990–2024, with each rule scaled to 10% annual volatility.], size: 8.5pt) <tbl-ladder>

#mtable(DT.behaviour, [How the rules trade, 1990–2024. Vol: annual volatility at 0.2% risk per position. Changes: entries, exits and reversals. Open positions: average number. Correlations of monthly net returns.], size: 8pt, columns: (auto, ..range(6).map(_ => 1fr))) <tbl-behaviour>

#fig("fig09_daily_equity.png")[Cumulative net P&L, each rule scaled to 10% annual volatility over 1990–2024 (display only). Shaded: after the paper and the book were published.]

The paper's signal and Clenow's core model earn similar risk-adjusted returns: #num(R("Paper EMA, 100 d").sr_net_in)
and #num(R("Clenow core").sr_net_in) net before 2014, and #num(R("Paper EMA, 100 d").sr_net_post) and
#num(R("Clenow core").sr_net_post) after. A paired block bootstrap (63-day blocks) of the Sharpe difference, Clenow
minus paper, gives #num(DF.sr_diff_core_minus_paper.in.diff) (95% interval #num(DF.sr_diff_core_minus_paper.in.lo) to
#num(DF.sr_diff_core_minus_paper.in.hi)) before 2014 and #num(DF.sr_diff_core_minus_paper.post.diff)
(#num(DF.sr_diff_core_minus_paper.post.lo) to #num(DF.sr_diff_core_minus_paper.post.hi)) after. Neither is
distinguishable from zero.

#mtable(DT.spanning, [Spanning regressions of monthly net returns. Appraisal ratio: annualised alpha over residual volatility.], size: 8.5pt, left-cols: 2) <tbl-span>

The two are largely the same bet. The paper's signal explains #num(SP("Clenow core on paper EMA (100 d) | 1990–2013").r2 * 100, d: 0)%
of the monthly variance of Clenow's model, and four EMA horizons explain
#num(SP("Clenow core on 4 EMA horizons | 1990–2013").r2 * 100, d: 0)%. What remains has an appraisal ratio of
#num(SP("Clenow core on 4 EMA horizons | 1990–2013").appraisal) (t = #num(SP("Clenow core on 4 EMA horizons | 1990–2013").alpha_t, d: 1)),
which is not significant. The reverse regression gives the same answer
(t = #num(SP("Paper EMA (100 d) on Clenow core | 1990–2013").alpha_t, d: 1)).

#mtable(DT.ema_horizons, [The paper's signal on daily futures by EMA time scale.], size: 8.5pt)

On daily futures the paper's signal is strongest between 50 and 200 days, as in the paper's monthly Table 1. The
fastest version (20 days) loses most of its edge to costs.

== What each component does

#fig("fig10_rule_ladder.png")[Net Sharpe ratio of each rule before and after 2014.]

- *The filter carries the edge.* The 50/100-day EMA filter alone earns #num(R("Filter only").sr_net_in) before 2014,
  as much as anything else here. Breakouts alone earn less (#num(R("Breakout only").sr_net_in)); adding them to the
  filter changes little (#num(R("Filter + breakout").sr_net_in)).
- *The trailing stop changes the shape.* It keeps the model out of the market #num(100 - R("Clenow core").in_market * 100, d: 0)%
  of the time and cuts losing trades early. At equal volatility, the worst drawdown falls from
  #num(-R("Filter + breakout").maxdd_10 * 100, d: 0)% to #num(-R("Clenow core").maxdd_10 * 100, d: 0)%, and monthly
  skew rises from #num(R("Filter + breakout").skew_m) to #num(R("Clenow core").skew_m). The in-sample Sharpe ratio
  is a little lower, and with costs tripled it drops more than the filter's
  (#num(R("Clenow core").sr_stress_in) vs #num(R("Filter only").sr_stress_in)).
- *After 2014* every rule is weaker. The stop-based model held up best (#num(R("Clenow core").sr_net_post)), but the
  differences between rules are well within noise over ten years.

== Do the parameters matter?

#fig("fig11_robustness.png")[Net Sharpe ratio of the core model for breakout windows and trailing stops (in true-range ATRs); the filter stays at 50/100 days. Boxed: the book's setting.]

All 30 settings are profitable in both periods: #num(DF.grid.in_min) to #num(DF.grid.in_max) before 2014 and
#num(DF.grid.post_min) to #num(DF.grid.post_max) after. This supports the book's view that a reasonable trend model
does not depend on fine-tuning. It also shows why tuning does not help. Before 2014 the widest stops look best;
after 2014 the 2-ATR stop does, and the rank correlation between the two periods' grids is #num(DF.grid.rank_corr).
Choosing the in-sample optimum would not have improved the out-of-sample result.

== Sectors and years

#mtable(DT.daily_sectors, [Net Sharpe ratio by sector.], size: 8.5pt, columns: (auto, ..range(5).map(_ => 1fr)))

#fig("fig14_daily_sectors.png")[Net Sharpe ratio by sector, before and after 2014.]

Every sector contributes before 2014. After 2014, rates and energy carry both rules, while metals and currencies
lose. The sector pattern of the two rules is similar.

#fig("fig12_yearly.png")[Calendar-year net P&L at 10% volatility, 1990–2023.]

Year by year the two rules move together (correlation #num(DF.yearly_corr)). They have
#DF.yearly_losing.at("Clenow core") and #DF.yearly_losing.at("Paper EMA, 100 d") losing years out of 34, and both had
their best year in 2008, when equity markets fell sharply.

== A real trend fund

#fig("fig13_benchmark.png")[Monthly excess return over T-bills of a public managed-futures mutual fund (#DF.benchmark.name, after fees), and the two rules scaled to the fund's volatility (before fees).]

Clenow's thesis is that simple rules capture much of what professional trend followers do. As one test, the rules
are compared with a public managed-futures mutual fund (#DF.benchmark.name), whose monthly total return
(distributions reinvested, minus T-bills) is available from #DF.benchmark.start to #DF.benchmark.end. Its returns are
#num(DF.benchmark.corr.at("Clenow core")) correlated with Clenow's model and
#num(DF.benchmark.corr.at("Paper EMA, 100 d")) with the paper's signal; together the two explain
#num(DF.benchmark.r2_paper_and_core * 100, d: 0)% of its monthly variance. The fund's Sharpe ratio over the period
is #num(DF.benchmark.sr_fund) after fees, against #num(DF.benchmark.sr.at("Clenow core")) and
#num(DF.benchmark.sr.at("Paper EMA, 100 d")) for the rules before fees and management costs. One fund is not the
industry, but this one is largely explained by simple trend rules.

== Back to Part I: are spot commodities the problem? <sec-spot>

Part I found commodities far weaker on spot data than in the paper (Sharpe #num(F.sectors.Commodities.sr) vs 0.80)
and attributed it to the futures' carry. Month-end futures prices allow a direct test: the paper's monthly rule
($n = 5$) on the seven Part I commodities, spot and futures side by side, over the same months of 1990–2013.

#mtable(DT.spot_vs_futures, [Paper's monthly rule on spot (monthly averages, lag 1 as in Part I) and futures (month-end), same months up to 2013. Long-only: the drift term, lag 1.], size: 7.5pt) <tbl-spot>

On futures at the same lag, the seven-commodity trend Sharpe rises from #num(DF.spot_vs_futures.all.spot) to
#num(DF.spot_vs_futures.all.fut). Month-end prices can be traded without the one-month delay that averaged data need
(Part I, @tbl-avg); doing so raises it to #num(DF.spot_vs_futures.all.fut0), close to the paper's 0.80 (measured on a
longer period). The long-only drift is *lower* on futures (#num(DF.spot_vs_futures.all.fut_mu) vs
#num(DF.spot_vs_futures.all.spot_mu)), which is the carry cost of holding commodities in contango. So the commodity
shortfall of Part I is mostly due to the delay that monthly averages force on the rule, and only partly to carry.
For currencies and bonds the delay costs nothing (Part I), so commodity trends seem to be faster. With 18–24 years
per market these Sharpe ratios have standard errors of about 0.2, so the split is approximate.

= Conclusions and limitations <sec-conc>

*Part I.* The paper's central claims replicate on free data: a significant, drift-independent trend effect across
asset classes and decades, and saturation of the signal. Its size depends on details the paper does not dwell on.
Monthly averages fake a trend unless the position is lagged, administered prices must be filtered, and interpolated
history must be excluded. On spot data the effect weakened after publication to a Sharpe ratio of about 0.27, which
is low but within what its own history allows.

*Part II.* On daily futures net of costs, Clenow's core model and the paper's signal earn similar Sharpe ratios
(#num(R("Clenow core").sr_net_in) and #num(R("Paper EMA, 100 d").sr_net_in) before 2014,
#num(R("Clenow core").sr_net_post) and #num(R("Paper EMA, 100 d").sr_net_post) after) and are mostly the same
trend exposure. Neither adds significant alpha
to the other. The practitioner's stop does not add edge; it trades fewer days, with smaller drawdowns and more
positive skew. The results hold across a wide range of parameters, but the best in-sample settings did not stay best.
This is consistent with the book's argument that diversification and risk sizing matter more than the exact rule, and
with the paper's view of trend as a single robust effect: the book's rule and the paper's signal are two ways of
trading it.

*Limitations.* Part I: spot and index proxies, monthly averages, no costs. Part II: data end in March 2024; the
universe is the set of contracts listed today, so it includes some survivorship and selection; ATR is estimated from
closes; trades are at the next close, not the next open; costs are today's, scaled by volatility; positions are
fractional and P&L is not compounded; and the managed-futures comparison uses a single fund.

*Next step.* Trend following as a convex overlay for a long-only book (Dao et al., 2016, _Tail protection for long
investors_), combined with the inverse-volatility study in
#link("https://github.com/lwang-genomics/inverse-vol-futures-overlay")[inverse-vol-futures-overlay].

= Appendix: code and reproducibility

`uv run trendrep` (Part I) and `uv run trendrep-daily` (Part II) download the raw data once (cached in `data/raw/`,
not committed), run every analysis and write `results/` and `figures/`. `uv run trendrep-report` compiles this PDF,
and `uv run pytest` runs the tests. The tests check the EMA and P&L against hand calculations and verify that there
is no look-ahead (changing later prices leaves all earlier signals, positions and P&L unchanged). They also verify
that random walks give t-stats centred on zero with unit spread, that monthly averaging fakes a trend at lag 0 but
not at lag 1, that trending series are profitable, that stale prices are not traded, and that the saturation fit and
the de-biasing recover known parameters. For Part II they check every entry, exit and holding day of the core model
against its rules, that the filter blocks trades against the trend, the execution lag and P&L, and the cost
accounting, and that the rules earn nothing on random walks and make money on persistent trends.

*References.* Y. Lempérière, C. Deremble, P. Seager, M. Potters, J.-P. Bouchaud (2014), "Two centuries of trend
following", _Journal of Investment Strategies_ 3(3); arXiv:1404.3274. A. F. Clenow (2013), _Following the Trend:
Diversified Managed Futures Trading_, Wiley. R. Carver, pysystemtrade (GPL-3), data at commit
#raw(DF.futures_commit.slice(0, 10)). H. Working (1960), "Note on the correlation of first differences of averages in
a random chain", _Econometrica_ 28(4).
