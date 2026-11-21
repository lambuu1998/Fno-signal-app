import streamlit as st
import yfinance as yf
import pandas as pd
import ta
from datetime import datetime
import pytz

st.set_page_config(page_title="Multi-Index F&O Signal App", page_icon="📈", layout="centered")

st.title("📈 F&O Live Signal App")
st.caption("Capital: ₹25,000 | Daily Max Risk: ₹1,000 | Target: ₹1,500")

INDEX_CONFIG = {
    "NIFTY 50": {
        "ticker": "^NSEI",
        "strike_step": 50,
        "lot_size": 75,
        "sl_points": 12,
        "target_points": 20
    },
    "BANK NIFTY": {
        "ticker": "^NSEBANK",
        "strike_step": 100,
        "lot_size": 30,
        "sl_points": 30,
        "target_points": 50
    },
    "SENSEX": {
        "ticker": "^BSESN",
        "strike_step": 100,
        "lot_size": 20,
        "sl_points": 45,
        "target_points": 75
    }
}

selected_index = st.selectbox("Index Chunein (Select Index):", list(INDEX_CONFIG.keys()))
config = INDEX_CONFIG[selected_index]

if st.button(f"🔄 Refresh {selected_index} Data", use_container_width=True):
    st.rerun()

def fetch_signal(ticker):
    df = yf.download(ticker, period="2d", interval="5m", progress=False)
    if df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df['EMA_9'] = ta.trend.ema_indicator(df['Close'], window=9)
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['RSI_14'] = ta.momentum.rsi(df['Close'], window=14)
    return df

df = fetch_signal(config["ticker"])

if df is not None and len(df) > 20:
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    close_price = float(latest['Close'])
    ema_9 = float(latest['EMA_9'])
    sma_20 = float(latest['SMA_20'])
    rsi_14 = float(latest['RSI_14'])
    prev_high = float(prev['High'])
    prev_low = float(prev['Low'])

    step = config["strike_step"]
    atm_strike = round(close_price / step) * step

    lot_size = config["lot_size"]
    sl_pts = config["sl_points"]
    tgt_pts = config["target_points"]
    max_loss_rs = lot_size * sl_pts
    target_profit_rs = lot_size * tgt_pts

    ist = pytz.timezone('Asia/Kolkata')
    now_time = datetime.now(ist).strftime('%d %b %Y, %I:%M %p')
    st.write(f"**Last Checked (IST):** {now_time}")

    col1, col2, col3 = st.columns(3)
    col1.metric(f"{selected_index} Spot", f"{close_price:,.1f}")
    col2.metric("9 EMA", f"{ema_9:,.1f}")
    col3.metric("RSI (14)", f"{rsi_14:.1f}")

    st.divider()

    if close_price > ema_9 and close_price > sma_20 and rsi_14 > 60 and close_price > prev_high:
        st.success(f"🟢 **STRONG BUY SIGNAL: {selected_index} {atm_strike} CE (CALL)**")
        st.markdown(f"""
        **Trade Setup (₹25,000 Capital ke hisab se):**
        * **Option Strike:** `{selected_index} {atm_strike} CE` (Current Weekly/Monthly Expiry)
        * **Quantity:** 1 Lot ({lot_size} Qty)
        * **Stop-Loss:** Entry premium se **{sl_pts} points neeche** (Max Loss ~₹{max_loss_rs:,})
        * **Target:** Entry premium se **{tgt_pts} points upar** (Target Profit ~₹{target_profit_rs:,})
        """)

    elif close_price < ema_9 and close_price < sma_20 and rsi_14 < 40 and close_price < prev_low:
        st.error(f"🔴 **STRONG BUY SIGNAL: {selected_index} {atm_strike} PE (PUT)**")
        st.markdown(f"""
        **Trade Setup (₹25,000 Capital ke hisab se):**
        * **Option Strike:** `{selected_index} {atm_strike} PE` (Current Weekly/Monthly Expiry)
        * **Quantity:** 1 Lot ({lot_size} Qty)
        * **Stop-Loss:** Entry premium se **{sl_pts} points neeche** (Max Loss ~₹{max_loss_rs:,})
        * **Target:** Entry premium se **{tgt_pts} points upar** (Target Profit ~₹{target_profit_rs:,})
        """)

    else:
        st.warning(f"⚪ **NO TRADE ZONE ({selected_index})**")
        st.info("Abhi clear breakout ya momentum nahi hai. Sideways market mein trade na karein aur thodi der baad check karein.")

    st.divider()
    st.subheader(f"📊 {selected_index} - Last 30 Candles (5-Min Trend)")
    st.line_chart(df[['Close', 'EMA_9', 'SMA_20']].tail(30))

else:
    st.error("Market data abhi load nahi ho pa raha hai. Kripya thodi der baad Refresh dabayein.")
