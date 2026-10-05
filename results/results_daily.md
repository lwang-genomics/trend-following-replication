# Results, Part II

Daily futures, sample 1990-01-02 → 2024-03-29; in-sample to 2013-12-31.

## universe

| Sector | Markets | First data | Last start | Cost (% ATR) | Markets (pysystemtrade names) |
| --- | --- | --- | --- | --- | --- |
| Equities | 13 | 1982 | 2014 | 1.2 | SP500, NASDAQ, DOW, FTSE100, DAX, CAC, AEX, IBEX, EUROSTX, SMI, HANG, NIKKEI, KOSPI |
| Rates | 14 | 1978 | 2012 | 2.4 | US2, US5, US10, US20, US30, BUND, BOBL, SHATZ, GILT, JGB, CAD10, BTP, OAT, EURIBOR |
| Currencies | 8 | 1972 | 2003 | 1.9 | EUR, JPY, GBP, CHF, AUD, CAD, NZD, MXP |
| Energy | 6 | 1980 | 2006 | 1.5 | CRUDE_W, CRUDE_ICE, HEATOIL, GASOILINE, GASOIL, GAS_US |
| Metals | 5 | 1970 | 1995 | 1.8 | GOLD, SILVER, COPPER, PLAT, PALLAD |
| Agriculturals | 16 | 1969 | 2007 | 3.2 | CORN, WHEAT, REDWHEAT, SOYBEAN, SOYMEAL, SOYOIL, SUGAR11, COFFEE, COCOA, COTTON2, OJ, RICE, OATIES, LIVECOW, FEEDCOW, LEANHOG |

## ladder

| Rule | SR gross | SR net | SR net, costs ×3 | SR net 2014–24 | Max DD (10% vol) | Skew (monthly) |
| --- | --- | --- | --- | --- | --- | --- |
| Filter only | 0.90 | 0.83 | 0.68 | 0.40 | −39% | 0.52 |
| Breakout only | 0.55 | 0.46 | 0.27 | 0.30 | −37% | 0.51 |
| Filter + breakout | 0.89 | 0.82 | 0.69 | 0.45 | −35% | 0.54 |
| Clenow core | 0.86 | 0.75 | 0.54 | 0.57 | −21% | 0.84 |
| Paper EMA, 100 d | 1.04 | 0.86 | 0.51 | 0.48 | −28% | 0.36 |

## behaviour

| Rule | Vol (risk 0.2%) | Time in market | Changes per market-year | Open positions | Corr. with paper EMA | Corr. with Clenow |
| --- | --- | --- | --- | --- | --- | --- |
| Filter only | 41% | 99% | 8.6 | 49 | 0.87 | 0.72 |
| Breakout only | 37% | 99% | 9.8 | 49 | 0.81 | 0.84 |
| Filter + breakout | 41% | 93% | 8.9 | 46 | 0.86 | 0.72 |
| Clenow core | 23% | 48% | 10.4 | 24 | 0.83 | 1.00 |
| Paper EMA, 100 d | 32% | 99% | 15.5 | 49 | 1.00 | 0.83 |

## ema_horizons

| EMA n (days) | SR gross | SR net | SR net 2014–24 | Corr. with Clenow core |
| --- | --- | --- | --- | --- |
| 20 (1 month) | 0.73 | 0.33 | 0.20 | 0.76 |
| 50 (2 months) | 1.00 | 0.76 | 0.34 | 0.85 |
| 100 (5 months) | 1.04 | 0.86 | 0.48 | 0.83 |
| 200 (10 months) | 0.95 | 0.81 | 0.65 | 0.72 |

## daily_sectors

| Sector | Markets | Clenow 1990–2013 | Clenow 2014–24 | Paper EMA 1990–2013 | Paper EMA 2014–24 |
| --- | --- | --- | --- | --- | --- |
| Equities | 13 | 0.29 | −0.04 | 0.44 | 0.19 |
| Rates | 14 | 0.44 | 0.57 | 0.61 | 0.63 |
| Currencies | 8 | 0.43 | 0.01 | 0.37 | −0.11 |
| Energy | 6 | 0.36 | 0.83 | 0.44 | 0.42 |
| Metals | 5 | 0.33 | −0.26 | 0.41 | −0.27 |
| Agriculturals | 16 | 0.43 | 0.33 | 0.37 | 0.14 |

## spanning

| Regression (monthly, net) | Period | t(alpha) | Appraisal ratio | R² |
| --- | --- | --- | --- | --- |
| Clenow core on paper EMA (100 d) | 1990–2013 | 0.4 | 0.09 | 0.69 |
| Clenow core on paper EMA (100 d) | 1990–2024 | 1.0 | 0.17 | 0.68 |
| Clenow core on 4 EMA horizons | 1990–2013 | 1.3 | 0.27 | 0.77 |
| Clenow core on 4 EMA horizons | 1990–2024 | 1.7 | 0.29 | 0.76 |
| Paper EMA (100 d) on Clenow core | 1990–2013 | 1.8 | 0.39 | 0.69 |
| Paper EMA (100 d) on Clenow core | 1990–2024 | 1.5 | 0.25 | 0.68 |

## spot_vs_futures

| Commodity | Futures | From | Trend SR, spot (avg., lag 1) | Trend SR, futures (lag 1) | Trend SR, futures (lag 0) | Long-only SR, spot | Long-only SR, futures |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Crude | CRUDE_W | 1992 | 0.21 | 0.36 | 0.34 | 0.35 | 0.53 |
| Natgas | GAS_US | 1992 | 0.13 | 0.05 | 0.33 | 0.45 | 0.06 |
| Corn | CORN | 1990 | 0.11 | −0.08 | 0.33 | 0.28 | 0.06 |
| Wheat | REDWHEAT | 1997 | −0.12 | 0.16 | 0.42 | 0.46 | 0.03 |
| Sugar | SUGAR11 | 1990 | 0.10 | 0.03 | 0.32 | 0.22 | 0.39 |
| Cattle | LIVECOW | 1990 | −0.13 | 0.23 | 0.33 | 0.36 | 0.22 |
| Copper | COPPER | 1997 | 0.39 | 0.39 | 0.21 | 0.51 | 0.26 |
| All seven |  |  | 0.19 | 0.32 | 0.72 | 0.72 | 0.41 |
