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
#let cres = json("../results/results_convexity.json")
#let CT = cres.tables
#let C = cres.facts
#let OV(name) = C.overlay.stats.at(name)
#let num(x, d: 2) = {
  if x == none { return "–" }
  let neg = x < 0
  let parts = str(calc.round(calc.abs(x), digits: d)).split(".")
  let dec = if parts.len() > 1 { parts.at(1) } else { "" }
  (if neg { "−" } else { "" }) + parts.at(0) + (if d > 0 { "." + dec + "0" * (d - dec.len()) } else { "" })
}

#let pc(x, d: 1) = num(x * 100, d: d) + "%"

#set document(title: "Trend Following: Replication, Practitioner Rules and Tail Protection", author: "Liangxi Wang")
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
  #text(size: 19pt)[Trend Following: Replication, Practitioner Rules \ and Tail Protection] \
  #v(0.3em)
  #text(size: 12pt)[Part I: Lempérière, Deremble, Seager, Potters & Bouchaud (2014), "Two centuries of trend
    following", reproduced on free data and tested after publication. \
    Part II: the core model of A. Clenow's _Following the Trend_ (2013) against the paper's signal, on daily futures. \
    Part III: Dao et al. (2016), "Tail protection for long investors: trend convexity at work", and trend as an
    overlay on an inverse-volatility portfolio] \
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

Part III tests the follow-up paper by the same group, Dao et al. (2016). It argues that trend following is a cheap
form of tail protection for long investors because its P&L is the difference between long-term and short-term
realised variance. It then puts that protection to work on the inverse-volatility portfolio of the companion study
#link("https://github.com/lwang-genomics/inverse-vol-futures-overlay")[inverse-vol-futures-overlay].

- *The mechanics replicate exactly.* The paper's identity holds to machine precision on S&P 500 futures, and the
  P&L of a linear trend aggregated over ≈ 90 days is a parabola in the trend indicator (R² = #num(C.sp.lin.r2),
  curvature #num(C.sp.lin.c, d: 3) vs #num(C.sp.lin_theory_c, d: 3) predicted). The sign rule gives the predicted V.
- *Convexity in a real fund is weaker than in the paper.* A diversified replicator reaches a monthly correlation of
  #num(C.replicator.corr.at("62").at("180")) with a public managed-futures fund at the paper's τ = 180 days. Measured
  at the right horizon, the fund's convexity against the S&P 500 rises from R² = #num(C.fund_convexity.naive.r2) to
  #num(C.fund_convexity.agg.r2), less than the paper's 0.02 → 0.18 on the SG CTA Index.
- *The risk-parity bound holds on every day* (#num(C.rp_bound.n, d: 0) days, 16 futures), as eq. (24) guarantees.
- *As an overlay, trend improves the inverse-vol book at equal risk.* At 10% volatility, adding the diversified
  trend raises the Sharpe ratio from #num(OV("Book alone").sr) to #num(OV("Book + 1 × diversified trend τ=180").sr),
  cuts the worst drawdown from #pc(-OV("Book alone").maxdd, d: 0) to
  #pc(-OV("Book + 1 × diversified trend τ=180").maxdd, d: 0) and turns quarterly skew from
  #num(OV("Book alone").skew_q) to #num(OV("Book + 1 × diversified trend τ=180").skew_q). In 2022, when the book
  lost #pc(-C.stress.at("2022 rate shock").book, d: 0), the trend overlay made
  #pc(C.stress.at("2022 rate shock").div_slow, d: 0). It does not, on average, pay off in the book's worst quarters.
- *Puts protect sooner but cost more.* The CBOE 5% put-protection index lost #pc(C.options.put_cost) a year against
  the S&P 500. Implied variance exceeded the variance realised afterwards in #pc(C.vrp.share_iv_above, d: 0) of
  months. Puts helped most in the fast COVID crash, where a 180-day trend helped little.

#text(size: 9pt, fill: luma(90))[Part I: @sec-paper to @sec-us. Part II: @sec-p2 to @sec-spot. Part III: @sec-p3 to @sec-options. Conclusions: @sec-conc.]

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

= Part III: trend convexity and tail protection <sec-p3>

Dao, Nguyen, Deremble, Lempérière, Bouchaud and Potters (2016) explain why trend following tends to do well when
markets move a lot. For a linear trend on one asset, they show that the P&L aggregated over the trend's horizon is,
exactly, a long-term variance minus a short-term variance. A trend follower is therefore "long" large moves over its
own time scale, like an option holder, and pays for it with short-term realised variance rather than an option
premium. Part III checks the mathematics, measures the convexity in a real trend fund, and asks what the property is
worth to a long-only investor. The investor in question holds the inverse-volatility portfolio of the companion
study.

== Trend P&L is long-term minus short-term variance

Following the paper, each market's daily price change $D_t$ is normalised by a 10-day risk estimate,
$R_t = D_t \/ sigma_(t-1)$ with $sigma_t = gamma sqrt(L_10 [D_t^2])$, where $L_tau$ is an EMA with weight
$2\/(tau+1)$. A linear trend holds $Pi_t = lambda tau L_tau [R_t] \/ sigma_t$, so its daily P&L is
$G_t = lambda tau L_tau [R]_(t-1) R_t$. The paper's eq. (13) states

$ L_(tau') [G_t] = (lambda tau) / (tau - 1) (tau L_tau [R_t]^2 - L_(tau') [R_t^2]), quad tau' = tau / 2 + 1 / (2 tau). $

With the trend indicator $T = sqrt(tau) L_tau [R]$ and the P&L aggregated over ≈ τ' days,
$overline(G) = tau' L_(tau') [G]$, this reads $overline(G) = Upsilon (T^2 - L_(tau') [R^2])$: a parabola in the
long-term move, minus the short-term variance. On S&P 500 futures the two sides agree to
about 10#super[−17], the precision of the computer, and a test checks the identity on arbitrary fat-tailed series.

One detail differs from the paper. Its calibration factor γ = 1.05 makes $R$ unit-variance; here γ = 1.16 is needed
on S&P 500 futures (and 1.10 even on Gaussian returns). With the paper's value, $⟨R^2⟩ = #num(C.sp.var_R)$, which
shifts the parabola down but leaves its curvature unchanged. The theory curves below use the measured $⟨R^2⟩$.

== The smile on S&P 500 futures

#fig("fig15_sp500_smile.png")[Aggregated P&L $overline(G)$ (over τ' ≈ 90 days) of a trend on S&P 500 futures against the trend indicator T, τ = 180 days, #C.sp.start to #C.sp.end (the paper's Figs. 4–5). (a) Linear trend, scaled to 1% daily P&L. (b) Sign of the trend. Dashed: theory.]

The linear trend traces the predicted parabola: fitted curvature #num(C.sp.lin.c, d: 4) against
#num(C.sp.lin_theory_c, d: 4) from theory, intercept #num(C.sp.lin.a, d: 3) against
#num(C.sp.lin_theory_a, d: 3), R² = #num(C.sp.lin.r2). Capping the position at ±1 turns the parabola into the
predicted V (slope #num(C.sp.sign_b, d: 3) vs #num(C.sp.sign_theory_b, d: 3), R² = #num(C.sp.sign_r2)). The
continuous-time theory for the sign rule is approximate; the test suite checks it on simulated random walks.

#mtable(CT.sp_horizons, [Trend P&L on the S&P 500 against the S&P 500 move over the same non-overlapping periods, by horizon (linear trend, τ = 180 days, 1984–2024). Quadratic fit: curvature c and R².], size: 8.5pt) <tbl-horizon>

The convexity only appears at the trend's own horizon. Measured day by day or week by week the curvature is nil; it
grows with the horizon and dominates at three to twelve months (@tbl-horizon). A monthly scatter of trend P&L
against S&P 500 returns gives R² = #num(C.sp.naive_monthly.r2), which is why naive plots hardly show the effect.

== Convexity in a real trend fund

The paper replicates the SG CTA Index with a linear trend on about 20 liquid futures, equal risk per market, and finds
a broad maximum of correlation (above 80%) at τ ≈ 180 days. The SG CTA Index is not freely available, so the
comparison here uses the public managed-futures fund of Part II (#DF.benchmark.name, monthly excess returns since
2010). Two replicators are tested: the paper's list as available here (16 futures from 2002; Eurodollar and Short
Sterling are missing, and the DAX stands in for the EuroStoxx 50) and the 62 futures of Part II.

#fig("fig16_corr_by_tau.png")[Monthly correlation between the replicator and the managed-futures fund (2010–2024) by trend time scale τ (the paper's Fig. 7).]

The correlation rises with τ and flattens from about 180 days, at #num(C.replicator.corr.at("62").at("180")) for the
62-market replicator and #num(C.replicator.corr.at("16").at("180")) for the 16-market one. This is the same broad
maximum as in the paper, at somewhat lower levels for a single fund.

#fig("fig17_fund_convexity.png")[The fund against the S&P 500. (a) Monthly returns: the naive view (the paper's Fig. 2). (b) The fund's P&L aggregated over τ' ≈ 90 days against the S&P 500 trend indicator, τ = 180 days (the paper's Fig. 9). Dashed: quadratic fits.]

#mtable(CT.fund_convexity, [Convexity of the fund and of the 16-futures replicator against the S&P 500: naive monthly view vs aggregated view.], size: 8pt, left-cols: 2)

Measured the paper's way, the fund's convexity is clearer than in the naive view (R² #num(C.fund_convexity.naive.r2)
→ #num(C.fund_convexity.agg.r2)), and the replicator behaves the same way over 2003–2024 (#num(C.fund_convexity.rep_naive.r2)
→ #num(C.fund_convexity.rep_agg.r2)). The gain is about half the paper's (0.02 → 0.18 on the SG CTA Index,
2000–2015). The paper explains part of the gap: a diversified trend is convex in its own markets' moves, and only
partly in the moves of one reference market such as the S&P 500.

== A bound for risk-parity portfolios

The paper's answer to that dilution is eq. (24). Take the equal-risk long-only portfolio of the same markets, a simple
risk-parity portfolio with daily return $G^"RP" = sum_k w_k R_k$ and trend indicator $T_"RP" = sqrt(tau) L_tau [G^"RP"]$.
Because the square of an average is at most the average of the squares, the diversified trend's aggregated P&L can
never fall below $Upsilon (T_"RP"^2 - sum_k w_k L_(tau') [R_k^2])$. This is a strict inequality, not a statistical
tendency.

#fig("fig18_rp_bound.png")[Aggregated P&L of the 16-futures trend against the trend of the equal-risk portfolio of the same futures, daily from #C.rp_bound.start (the paper's Fig. 10). Dashed: the bound with $⟨R^2⟩ = 1$.]

The exact bound holds on all #num(C.rp_bound.n, d: 0) days, as it must, and the simple parabola with
$⟨R^2⟩ = 1$ on #pc(C.rp_bound.share_above_parabola) of them. Large moves of a risk-parity portfolio, up or down, over
about six months are therefore always accompanied by trend profits. The inverse-volatility book below is a
risk-parity portfolio of this kind, on three assets.

== Trend as an overlay on the inverse-volatility book

The companion study builds a long-only book of the S&P 500, the 10-year Treasury and gold. It uses inverse-volatility
weights from the trailing year, quarter-end rebalancing, 10 bp costs and a 10% ex-ante volatility target. The same
rules are run here on futures from 1990, and a trend overlay is added:
- the paper's linear trend at τ = 180 days on the 62 futures, or on the book's three assets only, or at τ = 40 days;
- equal risk per market, next-close execution and the costs of Part II;
- the overlay is scaled to 10% ex-ante volatility, and every combination is rescaled to 10% ex-ante volatility, so
  that all portfolios carry the same risk.

#mtable(CT.overlay, [The inverse-vol book with and without a trend overlay, #C.overlay.start to #C.overlay.end; combinations rescaled to 10% ex-ante volatility. Quarterly CVaR: mean of the worst 5% of quarters.], size: 7.5pt) <tbl-overlay>

#mtable(CT.stress, [Returns over market stress episodes: the book, and each overlay on its own at 10% volatility.], size: 8pt) <tbl-stress>

At equal risk, the diversified slow trend improves the book on every summary measure except the single worst quarter
(@tbl-overlay): Sharpe ratio #num(OV("Book alone").sr) → #num(OV("Book + 1 × diversified trend τ=180").sr), maximum
drawdown #pc(-OV("Book alone").maxdd, d: 0) → #pc(-OV("Book + 1 × diversified trend τ=180").maxdd, d: 0), quarterly
skew #num(OV("Book alone").skew_q) → #num(OV("Book + 1 × diversified trend τ=180").skew_q). Most of the gain comes
from adding a positive-return stream with a low correlation to the book (#num(C.overlay.corr_book.div_slow) monthly).
Trend on the book's own three assets adds much less (Sharpe #num(OV("Book + 1 × 3-asset trend τ=180").sr)):
diversification across markets matters more than hedging the same assets.

#fig("fig19_overlay_quintiles.png")[Mean return of the trend overlay by quintile of the book's return over the same month (a) or quarter (b).] <fig-quint>

The overlay is not a put on the book. On average it earns *more* when the book does well (@fig-quint), because a
trend follower is usually long the assets that are rising, and the book holds rising assets most of the time. Its
protection is episodic and depends on time scale (@tbl-stress). The slow trend made money through the slow bear
markets: the 2000–02 dot-com bear, 2007–09 and the 2022 rate shock, when stocks and bonds fell together and the book
lost #pc(-C.stress.at("2022 rate shock").book, d: 0). In the five-week COVID crash the fast trend (τ = 40) helped far
more than the slow one, and the 2018 sell-off was too quick for the slow trend. This is the paper's warning made concrete:
a six-month trend cannot hedge a crash that lasts a few weeks.

#fig("fig20_overlay_drawdowns.png")[Drawdowns of the book alone and of the book with the diversified trend overlay, both at 10% volatility.]

== Trend vs options <sec-options>

The paper's last result is that a portfolio of strangles buys the same long-term variance as the trend, at a different
price: the trend pays the short-term variance realised as it trades, the options pay the implied variance fixed at
purchase. Options therefore protect against sudden moves that a trend cannot see, but they are sold at a premium. On
the S&P 500, 1990–2024, the VIX (30-day implied volatility) averaged #pc(C.vrp.iv) against #pc(C.vrp.rv) realised over
the following month, and exceeded it in #pc(C.vrp.share_iv_above, d: 0) of months: implied variance cost
#num(C.vrp.var_ratio) times realised variance.

#mtable(CT.options, [S&P 500 protection, 1990–2024: buying 5% out-of-the-money puts every month (CBOE PPUT index) vs adding a trend overlay at 10% volatility. Excess returns over T-bills; episodes as in @tbl-stress.], size: 7.5pt) <tbl-options>

#fig("fig21_protection.png")[Cumulative excess log return of the S&P 500 alone, with monthly 5% puts, and with a trend overlay.]

The put strategy cost #pc(C.options.put_cost) a year and lowered the Sharpe ratio, but it protected best in the COVID
crash. Trend on the S&P 500 alone did little. The diversified trend overlay roughly doubled the excess return at
slightly higher volatility, and protected in the slow 2007–09 and 2022 bear markets, much less in March 2020. These are not risk-matched portfolios, so the table shows trade-offs rather than a ranking. The pattern
is the paper's: options are the better hedge, trend the cheaper one.

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

*Part III.* The convexity mechanism of Dao et al. replicates exactly where it is mathematics (the identity, the
parabola and V on one market, the risk-parity bound), and more weakly where it is empirical: a public trend fund is
convex in the S&P 500 at the right horizon, but less clearly than the SG CTA Index in the paper. For a long-only
inverse-volatility book, a diversified slow trend overlay improves risk-adjusted returns, drawdowns and skew at equal
risk. That protection is episodic and depends on time scale: it covers bear markets that unfold over months, such as
2022 when stocks and bonds fell together, and not crashes that last a few weeks. Puts cover those, at a cost of
several percent a year.

*Limitations.* Part I: spot and index proxies, monthly averages, no costs. Part II: data end in March 2024; the
universe is the set of contracts listed today, so it includes some survivorship and selection; ATR is estimated from
closes; trades are at the next close, not the next open; costs are today's, scaled by volatility; positions are
fractional and P&L is not compounded; and the managed-futures comparison uses a single fund. Part III: one public
fund instead of the SG CTA Index; the convexity analysis uses gross P&L, as in the paper; the book is rebuilt on
futures, not the ETF and UCITS implementation of the companion study; the put comparison uses one listed strategy and
is not risk-matched.

*Possible extensions.* The SG CTA Index itself, if available; the convexity of Clenow's stop-based rules, whose
positive skew (Part II) suggests a V-like profile; and a hedge built from actual option prices rather than an index.

= Appendix: code and reproducibility

`uv run trendrep` (Part I), `uv run trendrep-daily` (Part II) and `uv run trendrep-convexity` (Part III, after
Part II) download the raw data once (cached in `data/raw/`,
not committed), run every analysis and write `results/` and `figures/`. `uv run trendrep-report` compiles this PDF,
and `uv run pytest` runs the tests. The tests check the EMA and P&L against hand calculations and verify that there
is no look-ahead (changing later prices leaves all earlier signals, positions and P&L unchanged). They also verify
that random walks give t-stats centred on zero with unit spread, that monthly averaging fakes a trend at lag 0 but
not at lag 1, that trending series are profitable, that stale prices are not traded, and that the saturation fit and
the de-biasing recover known parameters. For Part II they check every entry, exit and holding day of the core model
against its rules, that the filter blocks trades against the trend, the execution lag and P&L, and the cost
accounting, and that the rules earn nothing on random walks and make money on persistent trends. For Part III they
check the trend identity exactly on fat-tailed returns, the parabola and V-shape on random walks, the risk-parity
bound on every day of correlated simulated returns, the volatility target of the book and that the risk estimates
and the volatility scaling use past data only.

*References.* Y. Lempérière, C. Deremble, P. Seager, M. Potters, J.-P. Bouchaud (2014), "Two centuries of trend
following", _Journal of Investment Strategies_ 3(3); arXiv:1404.3274. A. F. Clenow (2013), _Following the Trend:
Diversified Managed Futures Trading_, Wiley. R. Carver, pysystemtrade (GPL-3), data at commit
#raw(DF.futures_commit.slice(0, 10)). H. Working (1960), "Note on the correlation of first differences of averages in
a random chain", _Econometrica_ 28(4). T.-L. Dao, T.-T. Nguyen, C. Deremble, Y. Lempérière, J.-P. Bouchaud,
M. Potters (2016), "Tail protection for long investors: trend convexity at work", arXiv:1607.02410. CBOE S&P 500 5%
Put Protection Index (PPUT); VIX from FRED (VIXCLS).
