#!/usr/bin/env python3
"""Idempotent Yahoo Finance OHLCV updater for the MMM data library.

Downloads the latest history for each symbol/interval in symbols.csv,
merges with any existing CSV (append + de-duplicate on timestamp),
sorts by Datetime (UTC), and rewrites:
  data/<SYMBOL>/<SYMBOL>_<interval>.csv
  data/inventory.csv

Yahoo Finance history limits (as of 2026):
  1d  — full available history (period=max)
  1h  — about 730 days
  15m — about 60 days
  5m  — about 60 days

Existing rows older than those windows are preserved when present.
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
SYMBOLS_FILE = REPO_ROOT / "symbols.csv"
INVENTORY_FILE = DATA_DIR / "inventory.csv"
README_FILE = REPO_ROOT / "README.md"

COLUMNS = ["Datetime", "Open", "High", "Low", "Close", "Volume"]

INTERVALS = {
    "1d": {"yf": "1d", "period": "max"},
    "1h": {"yf": "1h", "period": "730d"},
    "15m": {"yf": "15m", "period": "60d"},
    "5m": {"yf": "5m", "period": "60d"},
}

INVENTORY_MARKERS = (
    "<!-- inventory:start -->",
    "<!-- inventory:end -->",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def folder_name(yahoo_ticker: str, symbol: str | None = None) -> str:
    if symbol:
        return str(symbol).strip()
    return yahoo_ticker.replace("=F", "").replace("=", "").strip()


def load_symbols(path: Path = SYMBOLS_FILE) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"symbols list not found: {path}")
    df = pd.read_csv(path)
    required = {"symbol", "yahoo_ticker"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} missing columns: {sorted(missing)}")
    return df


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = [
            str(level0) if level0 and str(level0) != "nan" else str(level1)
            for level0, *rest in df.columns
            for level1 in (rest[-1] if rest else "",)
        ]
        # Fallback if the comprehension above is awkward — use first level if unique
        if df.columns.duplicated().any() or any(c == "" for c in df.columns):
            df.columns = [str(col[0]) for col in df.columns.to_list()]
    df.columns = [str(c).strip() for c in df.columns]
    return df


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    """Return a clean OHLCV frame with UTC Datetime and no duplicates."""
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=COLUMNS)

    df = _flatten_columns(df.copy())

    if "Datetime" not in df.columns and "Date" not in df.columns:
        df = df.reset_index()
        df = _flatten_columns(df)

    rename = {}
    for col in df.columns:
        key = col.strip().lower()
        if key in {"datetime", "date", "index"} and "Datetime" not in rename.values():
            rename[col] = "Datetime"
        elif key == "open":
            rename[col] = "Open"
        elif key == "high":
            rename[col] = "High"
        elif key == "low":
            rename[col] = "Low"
        elif key == "close":
            rename[col] = "Close"
        elif key == "volume":
            rename[col] = "Volume"
    df = df.rename(columns=rename)

    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns after normalize: {missing}; have {list(df.columns)}")

    out = df[COLUMNS].copy()
    out["Datetime"] = pd.to_datetime(out["Datetime"], utc=True, errors="coerce")
    out = out.dropna(subset=["Datetime"])
    for col in ("Open", "High", "Low", "Close"):
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["Volume"] = pd.to_numeric(out["Volume"], errors="coerce").fillna(0).astype("int64")
    out = out.dropna(subset=["Open", "High", "Low", "Close"])
    out = out.drop_duplicates(subset=["Datetime"], keep="last")
    out = out.sort_values("Datetime").reset_index(drop=True)
    return out


def format_for_csv(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Datetime"] = pd.to_datetime(out["Datetime"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return out[COLUMNS]


def csv_path(symbol: str, interval: str) -> Path:
    return DATA_DIR / symbol / f"{symbol}_{interval}.csv"


def read_existing(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=COLUMNS)
    return normalize_df(pd.read_csv(path))


def merge_frames(existing: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    if existing is None or existing.empty:
        return new.copy() if new is not None else pd.DataFrame(columns=COLUMNS)
    if new is None or new.empty:
        return existing.copy()
    combined = pd.concat([existing, new], ignore_index=True)
    combined = combined.drop_duplicates(subset=["Datetime"], keep="last")
    return combined.sort_values("Datetime").reset_index(drop=True)


def download_yahoo(ticker: str, yf_interval: str, period: str, retries: int = 3) -> pd.DataFrame:
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            hist = yf.Ticker(ticker).history(
                period=period,
                interval=yf_interval,
                auto_adjust=False,
                actions=False,
                timeout=60,
            )
            if hist is None or hist.empty:
                # Some Yahoo endpoints prefer download()
                hist = yf.download(
                    ticker,
                    period=period,
                    interval=yf_interval,
                    auto_adjust=False,
                    actions=False,
                    progress=False,
                    threads=False,
                    timeout=60,
                )
            return normalize_df(hist)
        except Exception as exc:  # noqa: BLE001 — surface Yahoo flakiness, then retry
            last_err = exc
            time.sleep(1.5 * attempt)
    raise RuntimeError(f"Yahoo download failed for {ticker} {yf_interval}: {last_err}")


def inventory_row(symbol: str, ticker: str, interval: str, df: pd.DataFrame, updated: str) -> dict:
    if df is None or df.empty:
        return {
            "symbol": symbol,
            "yahoo_ticker": ticker,
            "interval": interval,
            "start": "",
            "end": "",
            "rows": 0,
            "last_updated_utc": updated,
        }
    start = pd.to_datetime(df["Datetime"].iloc[0], utc=True).strftime("%Y-%m-%dT%H:%M:%SZ")
    end = pd.to_datetime(df["Datetime"].iloc[-1], utc=True).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "symbol": symbol,
        "yahoo_ticker": ticker,
        "interval": interval,
        "start": start,
        "end": end,
        "rows": int(len(df)),
        "last_updated_utc": updated,
    }


def render_inventory_table(inv: pd.DataFrame) -> str:
    headers = ["symbol", "interval", "start (UTC)", "end (UTC)", "rows", "last updated (UTC)"]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in inv.iterrows():
        lines.append(
            "| {symbol} | {interval} | {start} | {end} | {rows} | {last_updated_utc} |".format(
                symbol=row["symbol"],
                interval=row["interval"],
                start=row["start"] or "—",
                end=row["end"] or "—",
                rows=row["rows"],
                last_updated_utc=row["last_updated_utc"],
            )
        )
    return "\n".join(lines)


def update_readme_inventory(inv: pd.DataFrame) -> None:
    if not README_FILE.exists():
        return
    text = README_FILE.read_text(encoding="utf-8")
    start, end = INVENTORY_MARKERS
    if start not in text or end not in text:
        return
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    table = render_inventory_table(inv)
    README_FILE.write_text(
        before + start + "\n\n" + table + "\n\n" + end + after,
        encoding="utf-8",
    )


def update_one(symbol: str, ticker: str, interval: str, sleep_s: float) -> tuple[pd.DataFrame, str]:
    cfg = INTERVALS[interval]
    path = csv_path(symbol, interval)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = read_existing(path)
    new = download_yahoo(ticker, cfg["yf"], cfg["period"])
    merged = merge_frames(existing, new)
    if merged.empty:
        status = f"{symbol} {interval}: no rows returned (existing={len(existing)})"
    else:
        format_for_csv(merged).to_csv(path, index=False)
        added = len(merged) - len(existing)
        status = (
            f"{symbol} {interval}: {len(merged)} rows "
            f"({merged['Datetime'].iloc[0]} → {merged['Datetime'].iloc[-1]}); "
            f"delta={added:+d}"
        )
    if sleep_s:
        time.sleep(sleep_s)
    return merged, status

INTERVAL_ORDER = {name: i for i, name in enumerate(INTERVALS)}


def sort_inventory(inv: pd.DataFrame, symbols_df: pd.DataFrame) -> pd.DataFrame:
    order = {str(s).upper(): i for i, s in enumerate(symbols_df["symbol"])}
    out = inv.copy()
    out["_s"] = out["symbol"].astype(str).str.upper().map(lambda s: order.get(s, 999))
    out["_i"] = out["interval"].map(lambda i: INTERVAL_ORDER.get(i, 99))
    out = out.sort_values(["_s", "_i"], kind="mergesort").drop(columns=["_s", "_i"]).reset_index(drop=True)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Update MMM Yahoo Finance OHLCV library")
    parser.add_argument(
        "--symbols",
        nargs="*",
        default=None,
        help="Subset of library symbols (e.g. ES NQ). Default: all in symbols.csv",
    )
    parser.add_argument(
        "--intervals",
        nargs="*",
        default=list(INTERVALS.keys()),
        help="Intervals to update (default: 1d 1h 15m 5m)",
    )
    parser.add_argument("--sleep", type=float, default=0.4, help="Pause between Yahoo calls (seconds)")
    parser.add_argument(
        "--skip-readme",
        action="store_true",
        help="Do not rewrite the inventory table in README.md",
    )
    args = parser.parse_args(argv)

    unknown = [i for i in args.intervals if i not in INTERVALS]
    if unknown:
        print(f"Unknown intervals: {unknown}. Allowed: {list(INTERVALS)}", file=sys.stderr)
        return 2

    symbols = load_symbols()
    if args.symbols:
        wanted = {s.upper() for s in args.symbols}
        symbols = symbols[symbols["symbol"].str.upper().isin(wanted)]
        if symbols.empty:
            print("No matching symbols.", file=sys.stderr)
            return 2

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    updated = utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")
    inventory_rows: list[dict] = []
    errors: list[str] = []

    # Keep inventory rows for intervals we did not touch this run
    prior = read_existing_inventory() if not set(args.intervals) >= set(INTERVALS.keys()) or args.symbols else None

    for _, row in symbols.iterrows():
        symbol = folder_name(str(row["yahoo_ticker"]), str(row["symbol"]))
        ticker = str(row["yahoo_ticker"]).strip()
        for interval in args.intervals:
            try:
                merged, status = update_one(symbol, ticker, interval, args.sleep)
                print(status)
                inventory_rows.append(inventory_row(symbol, ticker, interval, merged, updated))
            except Exception as exc:  # noqa: BLE001
                msg = f"{symbol} {interval}: ERROR {exc}"
                print(msg, file=sys.stderr)
                errors.append(msg)
                existing = read_existing(csv_path(symbol, interval))
                inventory_rows.append(inventory_row(symbol, ticker, interval, existing, updated))

    inv = pd.DataFrame(inventory_rows)
    if prior is not None and not prior.empty:
        inv = merge_inventory(prior, inv)
    inv = sort_inventory(inv, load_symbols())
    inv.to_csv(INVENTORY_FILE, index=False)
    if not args.skip_readme:
        update_readme_inventory(inv)

    print(f"Wrote {INVENTORY_FILE}")
    if errors:
        print(f"{len(errors)} download error(s).", file=sys.stderr)
        return 1
    return 0


def read_existing_inventory() -> pd.DataFrame:
    if not INVENTORY_FILE.exists():
        return pd.DataFrame()
    return pd.read_csv(INVENTORY_FILE)


def merge_inventory(prior: pd.DataFrame, current: pd.DataFrame) -> pd.DataFrame:
    key = ["symbol", "interval"]
    if prior.empty:
        return current
    # current wins on overlap
    prior = prior.copy()
    current = current.copy()
    # drop prior rows that were refreshed
    mask = prior.set_index(key).index.isin(current.set_index(key).index)
    kept = prior.loc[~mask.values]
    return pd.concat([kept, current], ignore_index=True)


if __name__ == "__main__":
    sys.exit(main())
