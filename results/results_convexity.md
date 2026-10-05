# Results, Part III

## sp_horizons

| Horizon (days) | Periods | Curvature c (×100) | R² |
| --- | --- | --- | --- |
| 1 | 10122 | −0.05 | 0.23 |
| 5 | 2024 | 0.00 | 0.24 |
| 21 | 482 | 1.28 | 0.36 |
| 63 | 160 | 2.55 | 0.51 |
| 126 | 80 | 7.33 | 0.79 |
| 252 | 40 | 12.00 | 0.75 |

## fund_convexity

| Series | View | Sample | R² (quadratic fit) |
| --- | --- | --- | --- |
| Managed-futures fund | Monthly return vs S&P 500 monthly return | 2010–2024 | 0.04 |
| Managed-futures fund | P&L over τ' ≈ 90 d vs S&P 500 trend (τ = 180 d) | 2010–2024 | 0.10 |
| Replicator (16 futures) | Monthly return vs S&P 500 monthly return | 2003–2024 | 0.06 |
| Replicator (16 futures) | P&L over τ' ≈ 90 d vs S&P 500 trend (τ = 180 d) | 2003–2024 | 0.09 |

## overlay

| Portfolio | Return p.a. | Vol | Sharpe | Max DD | Worst quarter | CVaR 5% (quarter) | Skew (quarter) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Book alone | 7.2% | 10.8% | 0.66 | −28% | −15.0% | −10.3% | −0.71 |
| Book + 0.5 × diversified trend τ=180 | 9.6% | 10.3% | 0.93 | −21% | −16.9% | −10.0% | −0.24 |
| Book + 1 × diversified trend τ=180 | 10.2% | 10.3% | 0.99 | −21% | −15.6% | −9.3% | 0.12 |
| Book + 1 × diversified trend τ=40 | 6.6% | 10.2% | 0.64 | −29% | −13.9% | −8.1% | 0.45 |
| Book + 1 × 3-asset trend τ=180 | 7.0% | 10.5% | 0.67 | −26% | −10.7% | −7.2% | 0.60 |
| Overlay alone, diversified trend τ=180 | 7.8% | 10.4% | 0.75 | −26% | −10.7% | −7.2% | 0.84 |
| Overlay alone, diversified trend τ=40 | 1.9% | 10.4% | 0.18 | −37% | −8.0% | −7.4% | 1.19 |
| Overlay alone, 3-asset trend τ=180 | 4.0% | 10.7% | 0.37 | −30% | −10.7% | −8.1% | 0.58 |

## stress

| Episode | Book | Diversified, τ = 180 | Diversified, τ = 40 | Book's assets, τ = 180 |
| --- | --- | --- | --- | --- |
| 2000–02 dot-com bear | 0.5% | 52.9% | 17.0% | 29.5% |
| 2007–09 financial crisis | 8.8% | 45.9% | 46.5% | 21.9% |
| 2018 Q4 sell-off | −2.0% | −2.5% | 3.9% | −3.7% |
| 2020 COVID crash | −12.9% | 8.1% | 25.2% | 3.0% |
| 2022 rate shock | −26.7% | 31.8% | 13.3% | 13.2% |

## options

| Excess return over T-bills | Return p.a. | Vol | Sharpe | Max DD | 2007–09 | COVID 2020 | 2022 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S&P 500 | 8.9% | 18.1% | 0.49 | −60% | −56% | −34% | −25% |
| S&P 500 + 5% puts (CBOE PPUT) | 5.3% | 13.5% | 0.39 | −52% | −42% | −11% | −22% |
| S&P 500 + trend on the S&P 500 | 9.7% | 21.5% | 0.45 | −60% | −45% | −38% | −26% |
| S&P 500 + diversified trend | 17.0% | 19.7% | 0.86 | −46% | −38% | −28% | −0% |
