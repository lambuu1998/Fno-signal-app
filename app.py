import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import pytz

# Page Config
st.set_page_config(page_title="Pro S/R & Pattern Trading Terminal", layout="wide")

# Custom CSS for clean dark/pro look
st.markdown("""
<style>
    .main { background-color: #0e1117; color: #ffffff; }
    .signal-card {
        background-color: #161b22;
        border-left: 5px solid #00ff88;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    .sell-card {
        background-color: #161b22;
        border-left: 5px solid #ff4b4b;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    .metric-box {
        background-color: #1f2937;
        padding: 10px;
        border-radius: 6px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

IST = pytz.timezone('Asia/Kolkata')
now_ist = datetime.now(IST).strftime('%d %b %Y | %I:%M:%S %p IST')

st.title("📈 Pro Price-Action, Support/Resistance & Pattern Scanner")
st.caption(f"Live Market Scanner (5-Min F&O | 15-Min Stocks) • Last Updated: {now_ist}")

# Sidebar Controls
st.sidebar.header("⚙️ Scanner Settings")
scan_mode = st.sidebar.radio("Kya Scan Karna Hai?", ["🔥 Both (F&O + Top Stocks)", "⚡ Only F&O (5-Min)", "📊 Only Stocks (15-Min)"])
strictness = st.sidebar.select_slider(
    "Signal Filter Mode",
    options=["Balanced (More Trades)", "Strict (High Accuracy)"],
    value="Balanced (More Trades)"
)
auto_refresh = st.sidebar.checkbox("Auto-Refresh (Every 60 sec)", value=False)

if auto_refresh:
    st.markdown('<meta http-equiv="refresh" content="60">', unsafe_allow_html=True)

# Symbols
FNO_INDICES = {
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "SENSEX": "^BSESN"
}

TOP_STOCKS = {
    "RELIANCE": "RELIANCE.NS", "TCS": "TCS.NS", "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS", "INFY": "INFY.NS", "SBIN": "SBIN.NS",
    "BHARTIARTL": "BHARTIARTL.NS", "LT": "LT.NS", "AXISBANK": "AXISBANK.NS",
    "KOTAKBANK": "KOTAKBANK.NS", "TATAMOTORS": "TATAMOTORS.NS", "TATASTEEL": "TATASTEEL.NS",
    "BAJFINANCE": "BAJFINANCE.NS", "MARUTI": "MARUTI.NS", "SUNPHARMA": "SUNPHARMA.NS",
    "TITAN": "TITAN.NS", "ADANIENT": "ADANIENT.NS", "ADANIPORTS": "ADANIPORTS.NS",
    "M&M": "M&M.NS", "NTPC": "NTPC.NS", "POWERGRID": "POWERGRID.NS",
    "ONGC": "ONGC.NS", "HINDALCO": "HINDALCO.NS", "JSWSTEEL": "JSWSTEEL.NS",
    "INDUSINDBK": "INDUSINDBK.NS", "DLF": "DLF.NS", "HAL": "HAL.NS", "BEL": "BEL.NS"
}

# --- TECHNICAL & PATTERN ENGINE ---
def calculate_indicators(df):
    # EMAs
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
    
    # RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # ATR (14) for dynamic SL & Targets
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['ATR'] = true_range.rolling(14).mean()
    
    # VWAP (Intraday)
    df['Date'] = df.index.date
    df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['TP_Vol'] = df['Typical_Price'] * df['Volume']
    df['VWAP'] = df.groupby('Date')['TP_Vol'].cumsum() / df.groupby('Date')['Volume'].cumsum()
    # Fallback if Volume is 0 (like Indices)
    df['VWAP'] = df['VWAP'].fillna(df['EMA21'])
    
    # Supertrend (10, 3)
    hl2 = (df['High'] + df['Low']) / 2
    df['UpperBand'] = hl2 + (2.5 * df['ATR'])
    df['LowerBand'] = hl2 - (2.5 * df['ATR'])
    df['Supertrend'] = True
    for i in range(1, len(df)):
        if df['Close'].iloc[i] > df['UpperBand'].iloc[i-1]:
            df['Supertrend'].iloc[i] = True
        elif df['Close'].iloc[i] < df['LowerBand'].iloc[i-1]:
            df['Supertrend'].iloc[i] = False
        else:
            df['Supertrend'].iloc[i] = df['Supertrend'].iloc[i-1]
            
    return df

def find_support_resistance(df, window=20):
    recent = df.iloc[-window:-1]
    resistance = recent['High'].max()
    support = recent['Low'].min()
    return round(support, 2), round(resistance, 2)

def detect_pattern_and_signal(name, ticker, interval, is_fno=False, mode="Balanced (More Trades)"):
    try:
        df = yf.download(ticker, period="5d", interval=interval, progress=False)
        if df.empty or len(df) < 30:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df = calculate_indicators(df)
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        support, resistance = find_support_resistance(df, window=22)
        price = round(float(curr['Close']), 2)
        atr = round(float(curr['ATR']), 2)
        rsi = round(float(curr['RSI']), 1)
        ema9 = float(curr['EMA9'])
        ema21 = float(curr['EMA21'])
        vwap = float(curr['VWAP'])
        st_bull = bool(curr['Supertrend'])
        
        # Pattern Detection Logic
        pattern = "Trend Continuation"
        lows = df['Low'].iloc[-15:-1]
        highs = df['High'].iloc[-15:-1]
        
        # Check Double Bottom (W)
        if abs(lows.min() - curr['Low']) <= (0.5 * atr) and price > ema9:
            pattern = "Double Bottom (W Pattern) Reversal"
        # Check Double Top (M)
        elif abs(highs.max() - curr['High']) <= (0.5 * atr) and price < ema9:
            pattern = "Double Top (M Pattern) Reversal"
        # Check Resistance Breakout
        elif price > resistance and prev['Close'] <= resistance:
            pattern = "Resistance Breakout 🚀"
        # Check Support Breakdown
        elif price < support and prev['Close'] >= support:
            pattern = "Support Breakdown 🔻"
        # Pullback to VWAP/EMA21
        elif abs(price - ema21) <= (0.4 * atr):
            pattern = "EMA21 / VWAP Bounce Setup"

        # Signal Conditions
        signal_type = None
        reason = ""
        
        # Bullish Conditions
        bull_core = (price > ema9 > ema21) and (price > vwap) and (52 <= rsi <= 72)
        if mode == "Strict (High Accuracy)":
            bull_core = bull_core and st_bull and (price >= resistance - 0.3 * atr)
            
        # Bearish Conditions
        bear_core = (price < ema9 < ema21) and (price < vwap) and (28 <= rsi <= 48)
        if mode == "Strict (High Accuracy)":
            bear_core = bear_core and (not st_bull) and (price <= support + 0.3 * atr)

        if bull_core:
            signal_type = "BUY CALL (CE)" if is_fno else "BUY (LONG)"
            entry = price
            sl = round(max(support, price - 1.5 * atr), 2)
            risk = max(entry - sl, atr * 0.8)
            target1 = round(entry + (1.5 * risk), 2)
            target2 = round(entry + (2.5 * risk), 2)
            points_move = round(target1 - entry, 2)
            breakout_note = f"Agar **{resistance}** ke upar sustain karta hai toh **+{points_move} pts** ka fast move aayega."
            
        elif bear_core:
            signal_type = "BUY PUT (PE)" if is_fno else "SELL (SHORT)"
            entry = price
            sl = round(min(resistance, price + 1.5 * atr), 2)
            risk = max(sl - entry, atr * 0.8)
            target1 = round(entry - (1.5 * risk), 2)
            target2 = round(entry - (2.5 * risk), 2)
            points_move = round(entry - target1, 2)
            breakout_note = f"Agar **{support}** ke niche sustain karta hai toh **-{points_move} pts** ka fast fall aayega."
        else:
            # Show Watchlist Setup near S/R even if active trigger isn't fired yet
            dist_res = round(resistance - price, 2)
            dist_sup = round(price - support, 2)
            if dist_res <= 1.2 * atr or dist_sup <= 1.2 * atr:
                signal_type = "WATCHLIST (NEAR S/R)"
                entry = resistance if dist_res < dist_sup else support
                sl = round(entry - atr, 2) if dist_res < dist_sup else round(entry + atr, 2)
                target1 = round(entry + 1.8 * atr, 2) if dist_res < dist_sup else round(entry - 1.8 * atr, 2)
                target2 = round(entry + 3.0 * atr, 2) if dist_res < dist_sup else round(entry - 3.0 * atr, 2)
                points_move = round(abs(target1 - entry), 2)
                breakout_note = (
                    f"Resistance **{resistance}** tootne par **BUY / CE** (+{points_move} pts) | "
                    f"Support **{support}** tootne par **SELL / PE** (-{points_move} pts)"
                )
            else:
                return None

        return {
            "Name": name,
            "Timeframe": interval,
            "Signal": signal_type,
            "Pattern": pattern,
            "Price": price,
            "Support": support,
            "Resistance": resistance,
            "Entry": entry,
            "SL": sl,
            "Target1": target1,
            "Target2": target2,
            "Points": points_move,
            "RSI": rsi,
            "Note": breakout_note,
            "DF": df.iloc[-45:]
        }
    except Exception:
        return None

def plot_chart(item):
    df = item["DF"]
    fig = go.Figure()
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="Price"
    ))
    
    # EMA 9 & VWAP
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA9'], line=dict(color='#00d4ff', width=1.2), name='9 EMA'))
    fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], line=dict(color='#ffaa00', width=1.5, dash='dot'), name='VWAP'))
    
    # Support & Resistance Lines
    fig.add_hline(y=item["Resistance"], line_dash="dash", line_color="#ff4b4b", annotation_text=f"Resistance: {item['Resistance']}")
    fig.add_hline(y=item["Support"], line_dash="dash", line_color="#00ff88", annotation_text=f"Support: {item['Support']}")
    
    fig.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=30, b=10),
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        title=f"{item['Name']} ({item['Timeframe']}) — {item['Pattern']}"
    )
    return fig

# --- SCAN EXECUTION ---
fno_results = []
stock_results = []

with st.spinner("🔍 Market data, Support/Resistance levels aur Chart Patterns scan ho rahe hain..."):
    if "F&O" in scan_mode or "Both" in scan_mode:
        for name, ticker in FNO_INDICES.items():
            res = detect_pattern_and_signal(name, ticker, interval="5m", is_fno=True, mode=strictness)
            if res:
                fno_results.append(res)

    if "Stocks" in scan_mode or "Both" in scan_mode:
        for name, ticker in TOP_STOCKS.items():
            res = detect_pattern_and_signal(name, ticker, interval="15m", is_fno=False, mode=strictness)
            if res:
                stock_results.append(res)

# --- DISPLAY RESULTS ---
def render_section(title, results):
    st.subheader(title)
    if not results:
        st.info("Abhi koi clear setup nahi bana hai. Sidebar se 'Balanced' mode check karein ya thodi der mein refresh karein.")
        return
    
    for item in results:
        is_sell = "SELL" in item["Signal"] or "PUT" in item["Signal"]
        card_class = "sell-card" if is_sell else "signal-card"
        
        st.markdown(f"""
        <div class="{card_class}">
            <h3>{item['Name']} ({item['Timeframe']}) — <span style="color:#ffd700;">{item['Signal']}</span></h3>
            <p><b>📐 Chart Pattern:</b> {item['Pattern']} &nbsp;|&nbsp; <b>📊 RSI:</b> {item['RSI']}</p>
            <p><b>🎯 Breakout/Breakdown Plan:</b> {item['Note']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Current Price", f"₹{item['Price']}")
        c2.metric("Support (SL Zone)", f"₹{item['Support']}")
        c3.metric("Resistance (Breakout)", f"₹{item['Resistance']}")
        c4.metric("Stop Loss (SL)", f"₹{item['SL']}")
        c5.metric("Target 1", f"₹{item['Target1']}")
        c6.metric("Target 2", f"₹{item['Target2']}")
        
        with st.expander(f"📉 {item['Name']} Live Chart (Support, Resistance & VWAP dekhein)", expanded=True):
            st.plotly_chart(plot_chart(item), use_container_width=True)
        st.divider()

if "F&O" in scan_mode or "Both" in scan_mode:
    render_section("⚡ F&O Indices Signals & S/R Levels (5-Min Timeframe)", fno_results)

if "Stocks" in scan_mode or "Both" in scan_mode:
    render_section("📊 Top NSE Stocks Signals & Patterns (15-Min Timeframe)", stock_results)
