#!/usr/bin/env python3
"""
Davis Fund AI Framework — Market Data Fetcher
=============================================
Run this script locally to fetch live financial data and embed it into ai_framework.html.

Requirements:
    pip install yfinance

Usage:
    python3 fetch_market_data.py

Expected runtime: ~5-10 minutes for all companies.
"""

import yfinance as yf
import json
import re
import sys
import time
import logging
from datetime import datetime, date

# Suppress yfinance / urllib noise for delisted tickers
logging.getLogger("yfinance").setLevel(logging.CRITICAL)

HTML_FILE = "ai_framework.html"

# Tickers to skip (delisted, merged, or no longer independent)
SKIP = {
    "ANSS",   # Acquired by Synopsys (SNPS) Jan 2025
    "PBCT",   # Merged into MTB 2022
    "WLTW",   # Renamed — use WTW instead
}

# Ticker symbol overrides for yfinance (period → hyphen for BRK.B etc.)
SYMBOL_MAP = {
    "BRK.B": "BRK-B",
    "BF.B":  "BF-B",
}


def get_tickers_from_html():
    """Extract tickers directly from the HTML database."""
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html = f.read()
    tickers = re.findall(r'ticker:\s*"(\w+)"', html)
    seen, unique = set(), []
    for t in tickers:
        if t not in seen and t not in SKIP:
            seen.add(t)
            unique.append(t)
    return unique


def cagr(start_price, end_price, years):
    if not start_price or not end_price or start_price <= 0 or end_price <= 0:
        return None
    return (end_price / start_price) ** (1.0 / years) - 1


def fetch_price_history(tickers, batch_size=50):
    """Download monthly price history and compute return metrics."""
    result = {}
    today = date.today()
    jan_first = date(today.year, 1, 1)
    start_date = date(today.year - 5, today.month, today.day)
    total = len(tickers)

    for i in range(0, total, batch_size):
        batch = [SYMBOL_MAP.get(t, t) for t in tickers[i:i + batch_size]]
        orig_batch = tickers[i:i + batch_size]
        pct = int((i / total) * 100)
        print(f"  [{pct:3d}%] Price history {i+1}–{min(i+batch_size, total)} of {total}…",
              end="\r", flush=True)

        try:
            data = yf.download(
                batch,
                start=str(start_date),
                end=str(today),
                interval="1mo",
                progress=False,
                auto_adjust=True,
                group_by="ticker",
            )
        except Exception as e:
            print(f"\n  Batch error: {e}")
            time.sleep(2)
            continue

        for orig, sym in zip(orig_batch, batch):
            try:
                closes = (data["Close"] if len(batch) == 1
                          else data["Close"].get(sym, data["Close"].get(orig)))
                if closes is None:
                    continue
                closes = closes.dropna()
                if len(closes) < 3:
                    continue

                price_now = float(closes.iloc[-1])

                # YTD — last close before Jan 1
                ytd_base = None
                for idx in reversed(range(len(closes))):
                    if closes.index[idx].date() < jan_first:
                        ytd_base = float(closes.iloc[idx])
                        break

                # 1Y, 3Y, 5Y anchor prices
                def price_at(years_back):
                    target = date(today.year - years_back, today.month, today.day)
                    candidates = closes[closes.index.date <= target]
                    return float(candidates.iloc[-1]) if len(candidates) > 0 else None

                p1y, p3y, p5y = price_at(1), price_at(3), price_at(5)

                entry = {}
                if ytd_base: entry["ytd"]     = round((price_now - ytd_base) / ytd_base, 4)
                if p1y:      entry["return1y"] = round((price_now - p1y) / p1y, 4)
                if p3y:      entry["cagr3y"]   = round(cagr(p3y, price_now, 3), 4)
                if p5y and len(closes) >= 16:
                             entry["cagr5y"]   = round(cagr(p5y, price_now, 5), 4)
                if entry:
                    result[orig] = entry

            except Exception:
                pass  # Skip silently; delisted tickers produce errors here

        time.sleep(0.8)

    print(f"  [100%] Price history done. Got data for {len(result)}/{total} tickers.")
    return result


def fetch_fundamentals(tickers):
    """Fetch market cap, P/E, ROE, dividend yield one ticker at a time."""
    result = {}
    total = len(tickers)

    for i, ticker in enumerate(tickers):
        sym = SYMBOL_MAP.get(ticker, ticker)
        if i % 25 == 0:
            pct = int((i / total) * 100)
            print(f"  [{pct:3d}%] Fundamentals {i+1}/{total}…", end="\r", flush=True)
        try:
            info = yf.Ticker(sym).info
            entry = {}
            if info.get("marketCap"):          entry["marketCap"] = info["marketCap"]
            if info.get("trailingPE"):         entry["pe"]        = info["trailingPE"]
            if info.get("returnOnEquity"):     entry["roe"]       = info["returnOnEquity"]
            div = info.get("trailingAnnualDividendYield") or info.get("dividendYield")
            if div and div > 0:                entry["div"]       = div
            if entry:
                result[ticker] = entry
        except Exception:
            pass  # Skip silently
        time.sleep(0.12)

    print(f"  [100%] Fundamentals done. Got data for {len(result)}/{total} tickers.  ")
    return result


def embed_into_html(financial_data, as_of_str):
    """Replace the FINANCE_DATA_START…FINANCE_DATA_END block in the HTML."""
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
        print("ERROR: FINANCE_DATA_START marker not found in HTML. Was it removed?")
        return False

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_new)

    kb = len(data_json) / 1024
    print(f"\nEmbedded {len(clean)} tickers ({kb:.0f} KB) into {HTML_FILE}")
    return True


def main():
    tickers = get_tickers_from_html()
    print(f"Davis Fund AI Framework — Market Data Fetcher")
    print(f"Found {len(tickers)} tickers in database (skipping: {', '.join(SKIP)})\n")

    print("Step 1/2  — Price history (YTD, 1Y, 3Y CAGR, 5Y CAGR)")
    price_data = fetch_price_history(tickers)

    print("\nStep 2/2  — Fundamentals (Market Cap, P/E, ROE, Dividend %)")
    fund_data = fetch_fundamentals(tickers)

    # Merge both datasets
    merged = {}
    for t in tickers:
        fd = {}
        fd.update(price_data.get(t, {}))
        fd.update(fund_data.get(t, {}))   # fundamentals win on overlap
        if fd:
            merged[t] = fd

    as_of = datetime.today().strftime("%B %d, %Y")
    print(f"\nEmbedding data as of {as_of}…")
    if embed_into_html(merged, as_of):
        print(f"\n✓ Done! {len(merged)}/{len(tickers)} tickers populated.")
        print("  Next: git add ai_framework.html && git commit -m 'Refresh market data' && git push")


if __name__ == "__main__":
    main()
