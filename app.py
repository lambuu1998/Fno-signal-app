import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time

st.set_page_config(page_title="Strict F&O & Stock Filter", layout="wide")

st.title("🛡️ Strict F&O & NSE Stock Setup Filter")
st.caption("High-filter mode: Kam trades, zyada confirmation. Signal na ho toh trade skip karein.")

# Sidebar Controls
st.sidebar.header("⚙️ Filter & Risk Rules")
timeframe = st.sidebar.selectbox("Chart Timeframe", ["15m", "1h", "1d"], index=1)
min_adx = st.sidebar.slider("Minimum ADX (Trend Filter)", 22, 40, 28)
vol_surge = st.sidebar.slider("Stock Volume Multiplier (vs 20-bar avg)", 1.2, 3.0, 1.7)
capital = st.sidebar.number_input("Trading Capital (₹)", min_value=10000, max_value=10000000, value=100000, step=10000)
risk_pct = st.sidebar.slider("Max Risk Per Trade (%)", 0.5, 3.0, 1.0)
auto_refresh = st.sidebar.checkbox("Auto Refresh (60s)", value=False)

INDICES = {
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "SENSEX": "^BSESN"
}

TOP_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS", "LT.NS",
    "AXISBANK.NS", "BAJFINANCE.NS", "MARUTI.NS", "SUNPHARMA.NS", "TITAN.NS",
    "TATAMOTORS.NS", "NTPC.NS", "POWERGRID.NS", "ULTRACEMCO.NS", "M&M.NS",
    "ADANIENT.NS", "ADANIPORTS.NS", "COALINDIA.NS", "TATASTEEL.NS", "HINDALCO.NS",
    "JSWSTEEL.NS", "ONGC.NS", "TECHM.NS", "WIPRO.NS", "HCLTECH.NS",
    "CIPLA.NS", "APOLLOHOSP.NS", "EICHERMOT.NS", "BEL.NS", "HAL.NS", "TRENT.NS"
]

def add_indicators(df):
    df = df.copy()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()

    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))

    tr1 = df["High"] - df["Low"]
    tr2 = (df["High"] - df["Close"].shift()).abs()
    tr3 = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(14).mean()

    up_move = df["High"].diff()
    down_move = -df["Low"].diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    tr14 = tr.rolling(14).sum()
    plus_di = 100 * pd.Series(plus_dm, index=df.index).rolling(14).sum() / tr14.replace(0, np.nan)
    minus_di = 100 * pd.Series(minus_dm, index=df.index).rolling(14).sum() / tr14.replace(0, np.nan)
    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100
    df["ADX"] = dx.rolling(14).mean()

    df["VolAvg20"] = df["Volume"].rolling(20).mean()
    return df

def evaluate_symbol(label, symbol, is_index=False):
    try:
        period = "1mo" if timeframe in ["15m", "1h"] else "6mo"
        df = yf.download(symbol, period=period, interval=timeframe, progress=False)
        if df.empty or len(df) < 60:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = add_indicators(df).dropna(subset=["EMA20", "EMA50", "RSI", "ADX", "ATR"])
        if df.empty:
            return None

        curr = df.iloc[-1]
        prev = df.iloc[-2]

        price = float(curr["Close"])
        ema20 = float(curr["EMA20"])
        ema50 = float(curr["EMA50"])
        rsi = float(curr["RSI"])
        adx = float(curr["ADX"])
        atr = float(curr["ATR"])
        vol = float(curr["Volume"]) if "Volume" in curr and not np.isnan(curr["Volume"]) else 0.0
        vol_avg = float(curr["VolAvg20"]) if "VolAvg20" in curr and not np.isnan(curr["VolAvg20"]) else 0.0

        max_risk_amt = capital * (risk_pct / 100.0)
        sl_dist = max(atr * 1.5, price * 0.003)

        status = "NO TRADE"
        entry = "-"
        sl = "-"
        target = "-"
        qty_est = "-"

        if adx < min_adx:
            status = "SKIP (Weak Trend)"
        else:
            vol_pass = True if is_index else (vol_avg > 0 and vol >= vol_avg * vol_surge)
            bull_setup = (
                price > ema20
                and ema20 > ema50
                and prev["Close"] <= prev["EMA20"]
                and 55 <= rsi <= 70
                and vol_pass
            )
            bear_setup = (
                price < ema20
                and ema20 < ema50
                and prev["Close"] >= prev["EMA20"]
                and 30 <= rsi <= 45
                and vol_pass
            )

            if bull_setup:
                status = "STRONG BUY (CE/Long)" if is_index else "STRONG BUY"
                entry = round(price, 2)
                sl = round(price - sl_dist, 2)
                target = round(price + (2.0 * sl_dist), 2)
                if not is_index and sl_dist > 0:
                    qty_est = max(1, int(max_risk_amt // sl_dist))
            elif bear_setup:
                status = "STRONG SELL (PE/Short)" if is_index else "STRONG SELL"
                entry = round(price, 2)
                sl = round(price + sl_dist, 2)
                target = round(price - (2.0 * sl_dist), 2)
                if not is_index and sl_dist > 0:
                    qty_est = max(1, int(max_risk_amt // sl_dist))

        return {
            "Asset": label.replace(".NS", ""),
            "Price": round(price, 2),
            "Status": status,
            "Entry": entry,
            "SL": sl,
            "Target (1:2)": target,
            "Est. Qty": qty_est,
            "ADX": round(adx, 1),
            "RSI": round(rsi, 1),
        }
    except Exception:
        return None

max_day_loss = capital * (risk_pct / 100.0) * 2
st.info(f"💰 Capital: ₹{capital:,.0f} | Per-Trade Max Risk ({risk_pct}%): ₹{capital*(risk_pct/100):,.0f} | Din Ka Hard Stop (2 SL): ₹{max_day_loss:,.0f}")

st.subheader("1. Index Watch (Nifty / Bank Nifty / Sensex)")
idx_rows = [r for name, sym in INDICES.items() if (r := evaluate_symbol(name, sym, is_index=True))]
if idx_rows:
    st.dataframe(pd.DataFrame(idx_rows), use_container_width=True, hide_index=True)

st.subheader("2. High-Filter NSE Stock Setups")
stock_rows = []
for sym in TOP_STOCKS:
    res = evaluate_symbol(sym, sym, is_index=False)
    if res and res["Status"].startswith("STRONG"):
        stock_rows.append(res)

if stock_rows:
    st.dataframe(pd.DataFrame(stock_rows), use_container_width=True, hide_index=True)
else:
    st.warning("Abhi strict conditions (ADX + Pullback/EMA + RSI + Volume) ke hisab se koi naya STRONG setup nahi hai. Bina setup ke trade karne se loss badhta hai.")

st.caption(f"Updated at {datetime.now().strftime('%H:%M:%S')} | TF: {timeframe}")

if auto_refresh:
    time.sleep(60)
    st.rerun()
