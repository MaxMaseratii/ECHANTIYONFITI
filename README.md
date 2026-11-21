# ECHANTIYONFITI — MMM Historical Market Data Library

Historical OHLCV (Open, High, Low, Close, Volume) data from [Yahoo Finance](https://finance.yahoo.com/) for backtesting **MMM Pro Edge**, Max’s trading indicator/strategy, on CME index and commodity futures.

This repository starts as a clean library (no prior history was present). Weekly updates append new bars and keep any older rows already stored here, which matters for intraday Yahoo windows (about 730 days for 1h, about 60 days for 15m/5m).

## Layout

```
data/<SYMBOL>/<SYMBOL>_<interval>.csv
symbols.csv
scripts/update_data.py
```

Example: `data/ES/ES_1d.csv`, `data/ES/ES_1h.csv`, `data/ES/ES_15m.csv`, `data/ES/ES_5m.csv`.

## Symbols

| symbol | Yahoo ticker | description |
| --- | --- | --- |
| ES | ES=F | E-mini S&P 500 Futures |
| NQ | NQ=F | E-mini Nasdaq-100 Futures |
| MNQ | MNQ=F | Micro E-mini Nasdaq-100 Futures |
| MES | MES=F | Micro E-mini S&P 500 Futures |
| YM | YM=F | E-mini Dow Jones Industrial Average Futures |
| RTY | RTY=F | E-mini Russell 2000 Futures |
| GC | GC=F | Gold Futures |
| CL | CL=F | WTI Crude Oil Futures |

Yahoo `=F` tickers are continuous front-month futures (Yahoo’s own roll). They are useful for research and backtests but are **not** a substitute for official CME or broker data. Expect roll artefacts around contract switches, and treat volume as Yahoo’s series (not always identical to pit/electronic official volume).

## Intervals and Yahoo limits

| interval | file suffix | Yahoo history window | notes |
| --- | --- | --- | --- |
| daily | `_1d` | full available history (`period=max`) | session date stored as midnight UTC after conversion |
| 1 hour | `_1h` | about 730 days | accumulated history is preserved on update |
| 15 minutes | `_15m` | about 60 days | accumulated history is preserved on update |
| 5 minutes | `_5m` | about 60 days | accumulated history is preserved on update |

All timestamps in the CSVs are **UTC**, ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`). Columns: `Datetime,Open,High,Low,Close,Volume`.

Source timezone for these CME products is typically America/New_York (US equities/futures session). Convert back if you need exchange-local session times:

```python
df["Datetime"] = pd.to_datetime(df["Datetime"], utc=True)
df["Datetime_NY"] = df["Datetime"].dt.tz_convert("America/New_York")
```

## Data inventory

Last refreshed by `scripts/update_data.py`. Ranges are inclusive UTC timestamps of the first and last bar in each file.

<!-- inventory:start -->

| symbol | interval | start (UTC) | end (UTC) | rows | last updated (UTC) |
| --- | --- | --- | --- | --- | --- |
| ES | 1d | 2000-09-18T04:00:00Z | 2026-11-20T05:00:00Z | 6610 | 2026-11-21T18:19:35Z |
| ES | 1h | 2024-07-01T04:00:00Z | 2026-11-20T21:00:00Z | 13726 | 2026-11-21T18:19:35Z |
| ES | 15m | 2026-09-13T22:00:00Z | 2026-11-20T21:45:00Z | 4606 | 2026-11-21T18:19:35Z |
| ES | 5m | 2026-09-13T22:10:00Z | 2026-11-20T21:55:00Z | 13737 | 2026-11-21T18:19:35Z |
| NQ | 1d | 2000-09-18T04:00:00Z | 2026-11-20T05:00:00Z | 6610 | 2026-11-21T18:19:35Z |
| NQ | 1h | 2024-07-01T04:00:00Z | 2026-11-20T21:00:00Z | 13722 | 2026-11-21T18:19:35Z |
| NQ | 15m | 2026-09-13T22:00:00Z | 2026-11-20T21:45:00Z | 4604 | 2026-11-21T18:19:35Z |
| NQ | 5m | 2026-09-13T22:10:00Z | 2026-11-20T21:55:00Z | 13734 | 2026-11-21T18:19:35Z |
| MNQ | 1d | 2019-05-03T04:00:00Z | 2026-11-20T05:00:00Z | 1903 | 2026-11-21T18:19:35Z |
| MNQ | 1h | 2024-07-01T04:00:00Z | 2026-11-20T21:00:00Z | 13750 | 2026-11-21T18:19:35Z |
| MNQ | 15m | 2026-09-13T22:00:00Z | 2026-11-20T21:45:00Z | 4603 | 2026-11-21T18:19:35Z |
| MNQ | 5m | 2026-09-13T22:10:00Z | 2026-11-20T21:55:00Z | 13735 | 2026-11-21T18:19:35Z |
| MES | 1d | 2019-05-03T04:00:00Z | 2026-11-20T05:00:00Z | 1903 | 2026-11-21T18:19:35Z |
| MES | 1h | 2024-07-01T04:00:00Z | 2026-11-20T21:00:00Z | 13747 | 2026-11-21T18:19:35Z |
| MES | 15m | 2026-09-13T22:00:00Z | 2026-11-20T21:45:00Z | 4601 | 2026-11-21T18:19:35Z |
| MES | 5m | 2026-09-13T22:10:00Z | 2026-11-20T21:55:00Z | 13734 | 2026-11-21T18:19:35Z |
| YM | 1d | 2002-04-05T05:00:00Z | 2026-11-20T05:00:00Z | 6201 | 2026-11-21T18:19:35Z |
| YM | 1h | 2024-07-01T04:00:00Z | 2026-11-20T21:00:00Z | 13716 | 2026-11-21T18:19:35Z |
| YM | 15m | 2026-09-13T22:00:00Z | 2026-11-20T21:45:00Z | 4600 | 2026-11-21T18:19:35Z |
| YM | 5m | 2026-09-13T22:00:00Z | 2026-11-20T21:55:00Z | 13768 | 2026-11-21T18:19:35Z |
| RTY | 1d | 2017-07-10T04:00:00Z | 2026-11-20T05:00:00Z | 2360 | 2026-11-21T18:19:35Z |
| RTY | 1h | 2024-07-01T04:00:00Z | 2026-11-20T21:00:00Z | 13740 | 2026-11-21T18:19:35Z |
| RTY | 15m | 2026-09-13T22:00:00Z | 2026-11-20T21:45:00Z | 4602 | 2026-11-21T18:19:35Z |
| RTY | 5m | 2026-09-13T22:10:00Z | 2026-11-20T21:55:00Z | 13726 | 2026-11-21T18:19:35Z |
| GC | 1d | 2000-08-30T04:00:00Z | 2026-11-20T05:00:00Z | 6583 | 2026-11-21T18:19:35Z |
| GC | 1h | 2024-07-01T04:00:00Z | 2026-11-20T21:00:00Z | 13756 | 2026-11-21T18:19:35Z |
| GC | 15m | 2026-09-13T22:00:00Z | 2026-11-20T21:45:00Z | 4605 | 2026-11-21T18:19:35Z |
| GC | 5m | 2026-09-13T22:10:00Z | 2026-11-20T21:55:00Z | 13775 | 2026-11-21T18:19:35Z |
| CL | 1d | 2000-08-23T04:00:00Z | 2026-11-20T05:00:00Z | 6591 | 2026-11-21T18:19:35Z |
| CL | 1h | 2024-07-01T04:00:00Z | 2026-11-20T21:00:00Z | 13595 | 2026-11-21T18:19:35Z |
| CL | 15m | 2026-09-13T22:00:00Z | 2026-11-20T21:45:00Z | 4604 | 2026-11-21T18:19:35Z |
| CL | 5m | 2026-09-13T22:10:00Z | 2026-11-20T21:55:00Z | 13777 | 2026-11-21T18:19:35Z |

<!-- inventory:end -->

A machine-readable copy lives at [`data/inventory.csv`](data/inventory.csv).

## How to load in Python

```python
import pandas as pd

df = pd.read_csv("data/ES/ES_1h.csv", parse_dates=["Datetime"])
df["Datetime"] = pd.to_datetime(df["Datetime"], utc=True)
df = df.set_index("Datetime")
```

Install updater dependencies with `pip install -r requirements.txt`. To refresh every symbol and interval (merge + de-dupe, no history loss):

```bash
python scripts/update_data.py
```

See [UPDATING.md](UPDATING.md) for the weekly update procedure.

## TradingView notes

TradingView does not import these CSVs into a live chart the way a Python backtest does. Practical options:

- Use TradingView’s built-in continuous futures symbols (for example `ES1!`, `NQ1!`, `MNQ1!`, `MES1!`, `YM1!`, `RTY1!`, `GC1!`, `CL1!`) when you want to inspect MMM Pro Edge visually. Those series are not guaranteed to match Yahoo `=F` rolls bar-for-bar.
- For a Python backtest that should stay consistent with this library, load the CSVs above rather than re-downloading ad hoc from another vendor.
- If you export a TradingView chart to CSV for comparison, align timezones first (TradingView often shows exchange time; this library stores UTC).

## Disclaimer

This data is provided for personal research and backtesting. Yahoo Finance coverage, adjustments, and availability can change. Past prices and simulated results are not a guarantee of future performance. Futures trading involves substantial risk of loss.
