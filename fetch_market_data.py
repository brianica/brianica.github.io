#!/usr/bin/env python3
"""
Davis Fund AI Framework — Market Data Fetcher
=============================================
Run this script locally to fetch live financial data and embed it into ai_framework.html.

Requirements:
    pip install yfinance

Usage:
    python3 fetch_market_data.py

The script will:
  1. Fetch market cap, P/E, YTD return, 1Y return, 3Y CAGR, 5Y CAGR, ROE, dividend yield
  2. Embed the data directly into ai_framework.html
  3. Print a summary when done

Expected runtime: ~5-10 minutes for all 560 companies (respects Yahoo Finance rate limits).
"""

import yfinance as yf
import json
import re
import time
from datetime import datetime, date

HTML_FILE = "ai_framework.html"

# All tickers in the database
TICKERS = """NVDA,ASML,MSFT,AMZN,GOOGL,AVGO,VRT,ETN,META,AMD,INTC,QCOM,AMAT,LRCX,KLAC,MU,ARM,MRVL,ON,MPWR,NXPI,ADI,TXN,CSCO,ANET,DELL,HPE,WDC,STX,ORCL,IBM,SNPS,CDNS,ANSS,CEG,VST,PWR,EQIX,DLR,CCI,SMCI,JPM,BAC,WFC,GS,MS,C,COF,AXP,V,MA,SPGI,MCO,ICE,CME,BLK,SCHW,UNH,ELV,CI,HUM,LLY,ABBV,JNJ,PFE,MRK,BMY,ISRG,ABT,TMO,DHR,GILD,REGN,VRTX,GEHC,IDXX,BIIB,CVS,PGR,ALL,TRV,CB,WMT,HD,TGT,FDX,UPS,CAT,DE,HON,RTX,LMT,NOC,GD,BA,ADBE,INTU,NOW,CRM,WDAY,NFLX,VRSK,MSCI,FTNT,PLTR,TSLA,SNOW,CRWD,PANW,ZS,DDOG,NET,TTD,APP,TEAM,MELI,COST,WM,RSG,KO,PEP,PG,CL,MDLZ,MNST,KDP,PM,MO,GIS,HSY,MCD,SBUX,CMG,YUM,DIS,NEE,SO,DUK,D,AEP,EXC,XEL,WEC,XOM,CVX,COP,EOG,SLB,PSX,MPC,PLD,O,SPG,ORLY,AZO,PCAR,URI,FAST,NEM,FCX,LIN,APD,SHW,CHGG,EXPE,CTSH,WBA,PARA,WBD,FOXA,MTCH,OMC,IPG,ACN,EPAM,BKNG,EBAY,GDDY,CSGP,AAPL,ADSK,ADP,PAYX,FICO,ROP,PAYC,TYL,VRSN,ZBRA,KEYS,MCHP,NTAP,SWKS,TRMB,PTC,GEN,BR,EFX,AXON,BK,STT,USB,TFC,PNC,FITB,HBAN,KEY,RF,MTB,CFG,ZION,AON,MMC,AJG,PRU,MET,AFL,HIG,GL,CINF,TROW,IVZ,BEN,DFS,SYF,CBOE,NDAQ,NTRS,RJF,AMP,PFG,L,AIZ,MDT,SYK,BSX,EW,ZBH,DXCM,RMD,IQV,MCK,CAH,HCA,CNC,MOH,UHS,BDX,HOLX,ILMN,MRNA,COO,STE,HSIC,ZTS,WAT,A,MTD,RVTY,NKE,LOW,TJX,ROST,MAR,HLT,LVS,MGM,WYNN,GM,F,APTV,BWA,LEN,PHM,DHI,NVR,ULTA,LULU,ABNB,KMX,DPZ,GPC,BBY,CCL,RCL,KHC,KMB,CLX,CHD,STZ,ADM,BG,TSN,HRL,CAG,CPB,SJM,MKC,EL,SYY,LW,GE,EMR,ITW,PH,AME,IR,JCI,TT,CARR,OTIS,TDG,HWM,HII,LHX,LDOS,BAH,CSX,NSC,UNP,JBHT,ODFL,WAB,DAL,UAL,CPRT,CTAS,NDSN,XYL,VLTO,SNA,IEX,MAS,AOS,ALLE,OXY,DVN,FANG,MRO,APA,HES,CTRA,OKE,WMB,TRGP,HAL,BKR,VLO,NRG,SRE,PCG,ED,EIX,ETR,FE,AEE,CNP,CMS,LNT,EVRG,PPL,PEG,AES,AWK,NI,ECL,DD,DOW,PPG,EMN,CE,CF,MOS,NUE,STLD,ALB,IFF,VMC,MLM,PKG,IP,AMCR,AVY,FMC,CTVA,IRM,PSA,EXR,WELL,VTR,ARE,HST,EQR,AVB,MAA,ESS,CPT,UDR,BXP,KIM,REG,FRT,INVH,CBRE,NNN,WY,CHTR,T,VZ,TMUS,EA,TTWO,LYV,NWS,NWSA,SIRI,IAC,AMGN,AZN,DASH,PYPL,FSLR,FISV,FIS,GPN,ALLY,CPAY,DVA,THC,DRI,RL,TPR,PVH,HAS,MAT,GRMN,ALGN,PODD,XRAY,SWK,DOV,GNRC,HUBB,FTV,AKAM,FFIV,HPQ,ENPH,OKTA,TKO,SCI,NWL,WHR,MHK,LKQ,LEA,SEE,WRK,UNM,RE,RNR,SOLV,CRL,FOX,DG,KR,COTY,K,KMI,SAIC,CACI,DRS,BALL,ROL,PNR,WCN,BLDR,WEX,MANH,JKHY,MMM,GOOG,AAL,AIG,AMT,APH,APO,ACGL,ATO,BBWI,BIO,BX,BRO,CZR,CTLT,CDW,CMCSA,GLW,CMI,DLTR,DTE,ETSY,EQT,ES,FDS,FI,IT,DOC,INCY,JBL,JNPR,KVUE,KKR,LH,LII,LYB,MKTX,MSI,NCLH,OGN,PNW,POOL,QRVO,ROK,SBAC,LUV,TDY,TE,TFX,TER,TXT,TSCO,WST,WTW,GWW""".split(",")


def cagr(start_price, end_price, years):
    if not start_price or not end_price or start_price <= 0:
        return None
    return (end_price / start_price) ** (1.0 / years) - 1


def fetch_batch(tickers, batch_size=100):
    """Fetch quote data for a batch of tickers using yfinance."""
    result = {}
    today = date.today()
    jan_first = date(today.year, 1, 1)

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        print(f"  Fetching quotes {i+1}–{min(i+batch_size, len(tickers))} of {len(tickers)}…")

        try:
            data = yf.download(
                batch,
                start=str(date(today.year - 5, today.month, today.day)),
                end=str(today),
                interval="1mo",
                progress=False,
                auto_adjust=True,
                group_by="ticker",
            )

            for ticker in batch:
                try:
                    if len(batch) == 1:
                        closes = data["Close"].dropna()
                    else:
                        closes = data["Close"][ticker].dropna()

                    if len(closes) < 2:
                        continue

                    price_now = float(closes.iloc[-1])

                    # YTD
                    ytd_closes = closes[closes.index < str(jan_first)]
                    ytd_base = float(ytd_closes.iloc[-1]) if len(ytd_closes) > 0 else None
                    ytd = (price_now - ytd_base) / ytd_base if ytd_base else None

                    # 1Y
                    one_yr_closes = closes[closes.index <= str(date(today.year - 1, today.month, today.day))]
                    p1y = float(one_yr_closes.iloc[-1]) if len(one_yr_closes) > 0 else None
                    ret1y = (price_now - p1y) / p1y if p1y else None

                    # 3Y CAGR
                    three_yr_closes = closes[closes.index <= str(date(today.year - 3, today.month, today.day))]
                    p3y = float(three_yr_closes.iloc[-1]) if len(three_yr_closes) > 0 else None
                    cagr3y = cagr(p3y, price_now, 3) if p3y else None

                    # 5Y CAGR
                    five_yr_closes = closes[closes.index <= str(date(today.year - 5, today.month, today.day))]
                    p5y = float(five_yr_closes.iloc[-1]) if len(five_yr_closes) > 0 else None
                    cagr5y = cagr(p5y, price_now, 5) if p5y else None

                    result[ticker] = {
                        "ytd": round(ytd, 4) if ytd is not None else None,
                        "return1y": round(ret1y, 4) if ret1y is not None else None,
                        "cagr3y": round(cagr3y, 4) if cagr3y is not None else None,
                        "cagr5y": round(cagr5y, 4) if cagr5y is not None else None,
                    }
                except Exception as e:
                    print(f"    Warning: history failed for {ticker}: {e}")

        except Exception as e:
            print(f"  Batch download error: {e}")

        time.sleep(1)

    return result


def fetch_fundamentals(tickers):
    """Fetch market cap, P/E, ROE, dividend yield per ticker."""
    result = {}
    for i, ticker in enumerate(tickers):
        if i % 20 == 0:
            print(f"  Fetching fundamentals {i+1}/{len(tickers)}…")
        try:
            t = yf.Ticker(ticker)
            info = t.info
            result[ticker] = {
                "marketCap": info.get("marketCap"),
                "pe": info.get("trailingPE"),
                "roe": info.get("returnOnEquity"),
                "div": info.get("trailingAnnualDividendYield") or info.get("dividendYield"),
            }
        except Exception as e:
            print(f"    Warning: fundamentals failed for {ticker}: {e}")
        time.sleep(0.15)
    return result


def embed_into_html(financial_data, as_of_str):
    """Replace the FINANCE_DATA_START...FINANCE_DATA_END block in the HTML file."""
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    # Compact JSON — store as decimals rounded to 4 places
    clean = {}
    for ticker, fd in financial_data.items():
        entry = {k: v for k, v in fd.items() if v is not None}
        if entry:
            clean[ticker] = entry

    data_json = json.dumps(clean, separators=(",", ":"))

    new_block = f"""        // ── Financial data (embedded — run fetch_market_data.py to refresh) ──
        // FINANCE_DATA_START
        const FINANCE_AS_OF = "{as_of_str}";
        const financialData = {data_json};
        // FINANCE_DATA_END"""

    html_new = re.sub(
        r"// FINANCE_DATA_START.*?// FINANCE_DATA_END",
        new_block.strip(),
        html,
        flags=re.DOTALL,
    )

    if html_new == html:
        print("ERROR: Could not find FINANCE_DATA_START marker in HTML file.")
        return False

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_new)

    print(f"\nEmbedded data for {len(clean)} tickers into {HTML_FILE}")
    return True


def main():
    print(f"Davis Fund AI Framework — Market Data Fetcher")
    print(f"Fetching data for {len(TICKERS)} tickers…\n")

    # Step 1: Historical prices for return calculations
    print("Step 1/2: Historical price data (for YTD, 1Y, 3Y CAGR, 5Y CAGR)…")
    price_data = fetch_batch(TICKERS, batch_size=50)

    # Step 2: Fundamentals (market cap, P/E, ROE, dividend)
    print("\nStep 2/2: Fundamental data (Market Cap, P/E, ROE, Dividend)…")
    fund_data = fetch_fundamentals(TICKERS)

    # Merge
    merged = {}
    for ticker in TICKERS:
        merged[ticker] = {}
        if ticker in price_data:
            merged[ticker].update(price_data[ticker])
        if ticker in fund_data:
            merged[ticker].update({k: v for k, v in fund_data[ticker].items() if v is not None})

    # Embed into HTML
    as_of = datetime.today().strftime("%B %d, %Y")
    print(f"\nEmbedding data as of {as_of}…")
    success = embed_into_html(merged, as_of)

    if success:
        covered = sum(1 for v in merged.values() if v)
        print(f"\nDone! {covered}/{len(TICKERS)} tickers have data.")
        print(f"Now commit and push ai_framework.html to GitHub.")


if __name__ == "__main__":
    main()
