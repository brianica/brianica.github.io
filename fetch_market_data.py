#!/usr/bin/env python3
"""
Davis Fund AI Framework — Market Data Fetcher
=============================================
Run this script locally to fetch live financial data and embed it into ai_framework.html.

Requirements:
    pip install yfinance

Usage:
    python3 fetch_market_data.py

Expected runtime: ~10-15 minutes for all companies.
"""

import yfinance as yf
import json
import re
import time
import logging
from datetime import datetime, date

# Suppress yfinance noise
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)

HTML_FILE = "ai_framework.html"

SKIP = {"ANSS", "PBCT", "WLTW"}

# yfinance uses hyphens, not periods
SYMBOL_MAP = {"BRK.B": "BRK-B", "BF.B": "BF-B"}


def get_tickers_from_html():
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html = f.read()
    tickers = re.findall(r'ticker:\s*"(\w+)"', html)
    seen, unique = set(), []
    for t in tickers:
        if t not in seen and t not in SKIP:
            seen.add(t)
            unique.append(t)
    return unique


def cagr(p_start, p_end, years):
    if not p_start or not p_end or p_start <= 0 or p_end <= 0:
        return None
    return round((p_end / p_start) ** (1.0 / years) - 1, 4)


def fetch_history_single(ticker):
    """Fetch 5yr monthly history for one ticker, return return metrics."""
    sym = SYMBOL_MAP.get(ticker, ticker)
    today = date.today()
    jan_first = date(today.year, 1, 1)

    try:
        t = yf.Ticker(sym)
        hist = t.history(period="5y", interval="1mo", auto_adjust=True)
        if hist.empty or len(hist) < 3:
            return {}

        closes = hist["Close"].dropna()
        price_now = float(closes.iloc[-1])

        # YTD — last close before Jan 1 this year
        ytd_base = None
        for idx in reversed(range(len(closes))):
            if closes.index[idx].date() < jan_first:
                ytd_base = float(closes.iloc[idx])
                break

        def price_at(years_back):
            target = date(today.year - years_back, today.month, today.day)
            candidates = closes[closes.index.date <= target]
            return float(candidates.iloc[-1]) if len(candidates) > 0 else None

        p1y = price_at(1)
        p3y = price_at(3)
        p5y = price_at(5)

        entry = {}
        if ytd_base:          entry["ytd"]      = round((price_now - ytd_base) / ytd_base, 4)
        if p1y:               entry["return1y"] = round((price_now - p1y) / p1y, 4)
        if p3y:               entry["cagr3y"]   = cagr(p3y, price_now, 3)
        if p5y and len(closes) >= 16:
                              entry["cagr5y"]   = cagr(p5y, price_now, 5)
        return entry
    except Exception:
        return {}


def fetch_fundamentals_single(ticker):
    """Fetch market cap, P/E, ROE, dividend for one ticker."""
    sym = SYMBOL_MAP.get(ticker, ticker)
    try:
        info = yf.Ticker(sym).info
        entry = {}
        if info.get("marketCap"):                    entry["marketCap"] = info["marketCap"]
        if info.get("trailingPE"):                   entry["pe"]        = round(info["trailingPE"], 2)
        if info.get("returnOnEquity"):               entry["roe"]       = round(info["returnOnEquity"], 4)
        div = info.get("trailingAnnualDividendYield") or info.get("dividendYield")
        if div and div > 0:                          entry["div"]       = round(div, 6)
        return entry
    except Exception:
        return {}


def embed_into_html(financial_data, as_of_str):
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    clean = {t: fd for t, fd in financial_data.items() if fd}
    data_json = json.dumps(clean, separators=(",", ":"))

    new_block = (
        "// FINANCE_DATA_START\n"
        f'        const FINANCE_AS_OF = "{as_of_str}";\n'
        f"        const financialData = {data_json};\n"
        "        // FINANCE_DATA_END"
    )

    html_new = re.sub(
        r"// FINANCE_DATA_START.*?// FINANCE_DATA_END",
        new_block,
        html,
        flags=re.DOTALL,
    )

    if html_new == html:
        print("ERROR: FINANCE_DATA_START marker not found. Did the file change?")
        return False

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_new)

    kb = len(data_json) / 1024
    print(f"Embedded {len(clean)} tickers ({kb:.0f} KB) into {HTML_FILE}")
    return True


def main():
    tickers = get_tickers_from_html()
    total = len(tickers)
    print(f"Davis Fund AI Framework — Market Data Fetcher")
    print(f"Fetching data for {total} tickers\n")

    merged = {}
    failed = []

    for i, ticker in enumerate(tickers):
        pct = int((i / total) * 100)
        print(f"  [{pct:3d}%] {ticker:<8}", end="\r", flush=True)

        fd = {}
        fd.update(fetch_history_single(ticker))
        fd.update(fetch_fundamentals_single(ticker))

        if fd:
            merged[ticker] = fd
        else:
            failed.append(ticker)

        # polite rate limiting
        time.sleep(0.4)

    print(f"\n  [100%] Done.                              ")
    print(f"\nResults: {len(merged)} tickers with data, {len(failed)} failed/skipped")
    if failed:
        print(f"Failed: {', '.join(failed[:20])}{'…' if len(failed)>20 else ''}")

    as_of = datetime.today().strftime("%B %d, %Y")
    print(f"\nWriting data as of {as_of} to {HTML_FILE}…")

    if embed_into_html(merged, as_of):
        print(f"\nDone! Now run:")
        print(f"  git add ai_framework.html")
        print(f"  git commit -m 'Market data {as_of}'")
        print(f"  git push")


if __name__ == "__main__":
    main()
