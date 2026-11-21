import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yfinance as yf
import pandas as pd
import ta
from datetime import datetime
import pytz

# 1. Page Configuration (Hamesha sabse upar hona chahiye)
st.set_page_config(page_title="Multi-Index F&O Live Signal", layout="wide")

# 2. Auto-Refresh (Har 60 seconds mein page apne aap update hoga)
st_autorefresh(interval=60 * 1000, key="fno_auto_refresh")

# Header & Time
ist = pytz.timezone('Asia/Kolkata')
now_ist = datetime.now(ist).strftime('%d-%b-%Y | %I:%M:%S %p IST')

st.title("📈 F&O Live Signal & Target/SL Tracker")
st.caption(f"Capital: ₹25,000 | Auto-Refresh: ON (60s) | Last Updated: {now_ist}")

# Sidebar Settings (Aap yahan se apna risk/capital change kar sakte hain)
with st.sidebar:
    st.header("⚙️ Trade Settings")
    capital = st.number_input("Trading Capital (₹)", value=25000, step=5000)
    risk_percent = st.slider("Max Risk per Trade (%)", 1.0, 10.0, 4.0, 0.5)
    rr_ratio = st.selectbox("Risk : Reward Ratio", [1.5, 2.0, 2.5, 3.0], index=1)
    st.info("Note: Option premium movement spot ke ~50% (ATM Delta 0.5) ke hisaab se estimate kiya gaya hai.")

# Index Configuration (Updated Lot Sizes)
INDEX_CONFIG = {
    "NIFTY 50": {
        "ticker": "^NSEI",
        "step": 50,
        "lot_size": 75,
        "sl_points": 35
    },
    "BANK NIFTY": {
        "ticker": "^NSEBANK",
        "step": 100,
        "lot_size": 30,
        "sl_points": 80
    },
    "SENSEX": {
        "ticker": "^BSESN",
        "step": 100,
        "lot_size": 20,
        "sl_points": 100
    }
}

def analyze_index(name, cfg):
    try:
        df = yf.download(cfg["ticker"], period="5d", interval="5m", progress=False)
        if df.empty or len(df) < 25:
            return None

        # Multi-level columns fix for yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = df['Close']
        df['EMA9'] = ta.trend.ema_indicator(close, window=9)
        df['SMA20'] = ta.trend.sma_indicator(close, window=20)
        df['RSI'] = ta.momentum.rsi(close, window=14)

        latest = df.iloc[-1]
        price = float(latest['Close'])
        ema9 = float(latest['EMA9'])
        sma20 = float(latest['SMA20'])
        rsi = float(latest['RSI'])

        atm_strike = round(price / cfg["step"]) * cfg["step"]
        sl_pts = cfg["sl_points"]
        tgt_pts = round(sl_pts * rr_ratio)

        # Signal Logic: 9 EMA + 20 SMA + RSI
        if price > ema9 and ema9 > sma20 and 52 <= rsi <= 72:
            signal = "BUY CALL (CE) 🟢"
            action = "BULLISH"
            option_name = f"{name} {atm_strike} CE"
            entry_price = price
            sl_price = price - sl_pts
            target_price = price + tgt_pts
        elif price < ema9 and ema9 < sma20 and 28 <= rsi <= 48:
            signal = "BUY PUT (PE) 🔴"
            action = "BEARISH"
            option_name = f"{name} {atm_strike} PE"
            entry_price = price
            sl_price = price + sl_pts
            target_price = price - tgt_pts
        else:
            signal = "NO TRADE / WAIT 🟡"
            action = "SIDEWAYS"
            option_name = f"Watch {atm_strike} CE/PE"
            entry_price = price
            sl_price = 0.0
            target_price = 0.0

        # Profit & Loss Calculation (1 Lot, ATM Delta ~0.5)
        lot = cfg["lot_size"]
        est_loss = round(sl_pts * 0.5 * lot)
        est_profit = round(tgt_pts * 0.5 * lot)

        return {
            "price": price,
            "ema9": ema9,
            "sma20": sma20,
            "rsi": rsi,
            "signal": signal,
            "action": action,
            "option_name": option_name,
            "entry": entry_price,
            "sl": sl_price,
            "target": target_price,
            "sl_pts": sl_pts,
            "tgt_pts": tgt_pts,
            "lot_size": lot,
            "est_profit": est_profit,
            "est_loss": est_loss
        }
    except Exception as e:
        return {"error": str(e)}

# Display 3 Columns for Nifty, Bank Nifty, Sensex
cols = st.columns(3)

for idx, (name, cfg) in enumerate(INDEX_CONFIG.items()):
    with cols[idx]:
        st.subheader(f"📊 {name}")
        data = analyze_index(name, cfg)

        if not data:
            st.warning("Market data load nahi ho paya. Thodi der mein refresh hoga.")
            continue
        if "error" in data:
            st.error(f"Error: {data['error']}")
            continue

        # Live Spot Price & RSI
        st.metric(label="Live Spot Price", value=f"₹{data['price']:,.2f}", delta=f"RSI: {data['rsi']:.1f}")

        # Signal Box
        if data["action"] == "BULLISH":
            st.success(f"**Signal:** {data['signal']}\n\n**Strike:** `{data['option_name']}`")
        elif data["action"] == "BEARISH":
            st.error(f"**Signal:** {data['signal']}\n\n**Strike:** `{data['option_name']}`")
        else:
            st.warning(f"**Signal:** {data['signal']}\n\n**Range:** `{data['option_name']}`")

        st.divider()

        # Trade Levels & Profit/Loss Details
        if data["action"] in ["BULLISH", "BEARISH"]:
            st.markdown(f"**🎯 Trade Setup (Spot Levels):**")
            st.write(f"• **Entry Price:** `₹{data['entry']:,.2f}`")
            st.write(f"• **Target Price:** `₹{data['target']:,.2f}` *(+{data['tgt_pts']} pts)*")
            st.write(f"• **Stop Loss (SL):** `₹{data['sl']:,.2f}` *(-{data['sl_pts']} pts)*")

            st.markdown(f"**💰 Expected P&L (1 Lot = {data['lot_size']} Qty):**")
            c1, c2 = st.columns(2)
            c1.success(f"**Profit:** +₹{data['est_profit']:,}")
            c2.error(f"**Loss:** -₹{data['est_loss']:,}")
        else:
            st.info("Abhi clear trend nahi hai (9 EMA, 20 SMA aur RSI match nahi kar rahe). Trade avoid karein.")
            st.caption(f"9 EMA: {data['ema9']:,.1f} | 20 SMA: {data['sma20']:,.1f}")

st.divider()
st.caption("⚠️ Disclaimer: Yeh app educational aur technical analysis purpose ke liye hai. Real money trade lene se pehle apna risk management zaroor check karein.")
