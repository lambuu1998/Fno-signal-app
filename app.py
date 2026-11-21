import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yfinance as yf
import pandas as pd
import ta
from datetime import datetime
import pytz

# 1. Page Configuration
st.set_page_config(page_title="Multi-Index & Top 100 NSE F&O Screener", layout="wide")

# 2. Auto-Refresh (Har 60 seconds mein apne aap update hoga)
st_autorefresh(interval=60 * 1000, key="fno_master_refresh")

# Header & Time
ist = pytz.timezone('Asia/Kolkata')
now_ist = datetime.now(ist).strftime('%d-%b-%Y | %I:%M:%S %p IST')

st.title("📈 F&O Live Signal & Top 100 NSE Stocks Screener")
st.caption(f"Auto-Refresh: ON (60s) | Last Updated: {now_ist}")

# Sidebar Settings
with st.sidebar:
    st.header("⚙️ Trade & Risk Settings")
    capital = st.number_input("Trading Capital (₹)", value=25000, step=5000)
    rr_ratio = st.selectbox("Risk : Reward Ratio", [1.5, 2.0, 2.5, 3.0], index=1)
    vol_multiplier = st.slider("Min Volume Spike (x Avg)", 1.2, 2.5, 1.5, 0.1)
    adx_min = st.slider("Min Trend Strength (ADX)", 20, 35, 25, 1)
    st.info("High-Accuracy Filter: 20/50 EMA + RSI + Volume Spike + ADX > 25 match hone par hi stock dikhega.")

# Create 2 Tabs
tab1, tab2 = st.tabs(["📊 Tab 1: Index F&O Live", "🚀 Tab 2: Top 100 NSE F&O Stocks"])

# ==========================================
# TAB 1: INDEX F&O LIVE (NIFTY, BANKNIFTY, SENSEX)
# ==========================================
INDEX_CONFIG = {
    "NIFTY 50": {"ticker": "^NSEI", "step": 50, "lot_size": 75, "sl_points": 35},
    "BANK NIFTY": {"ticker": "^NSEBANK", "step": 100, "lot_size": 30, "sl_points": 80},
    "SENSEX": {"ticker": "^BSESN", "step": 100, "lot_size": 20, "sl_points": 100}
}

def analyze_index(name, cfg):
    try:
        df = yf.download(cfg["ticker"], period="5d", interval="5m", progress=False)
        if df.empty or len(df) < 25:
            return None
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

        if price > ema9 and ema9 > sma20 and 52 <= rsi <= 72:
            signal = "BUY CALL (CE) 🟢"
            action = "BULLISH"
            option_name = f"{name} {atm_strike} CE"
            sl_price = price - sl_pts
            target_price = price + tgt_pts
        elif price < ema9 and ema9 < sma20 and 28 <= rsi <= 48:
            signal = "BUY PUT (PE) 🔴"
            action = "BEARISH"
            option_name = f"{name} {atm_strike} PE"
            sl_price = price + sl_pts
            target_price = price - tgt_pts
        else:
            signal = "NO TRADE / WAIT 🟡"
            action = "SIDEWAYS"
            option_name = f"Watch {atm_strike} CE/PE"
            sl_price = 0.0
            target_price = 0.0

        lot = cfg["lot_size"]
        est_loss = round(sl_pts * 0.5 * lot)
        est_profit = round(tgt_pts * 0.5 * lot)

        return {
            "price": price, "ema9": ema9, "sma20": sma20, "rsi": rsi,
            "signal": signal, "action": action, "option_name": option_name,
            "entry": price, "sl": sl_price, "target": target_price,
            "sl_pts": sl_pts, "tgt_pts": tgt_pts, "lot_size": lot,
            "est_profit": est_profit, "est_loss": est_loss
        }
    except Exception as e:
        return {"error": str(e)}

with tab1:
    st.subheader("Live Index Options Setup (5-Min Timeframe)")
    cols = st.columns(3)
    for idx, (name, cfg) in enumerate(INDEX_CONFIG.items()):
        with cols[idx]:
            st.markdown(f"### {name}")
            data = analyze_index(name, cfg)
            if not data:
                st.warning("Data load nahi ho paya.")
                continue
            if "error" in data:
                st.error(f"Error: {data['error']}")
                continue

            st.metric("Live Spot Price", f"₹{data['price']:,.2f}", f"RSI: {data['rsi']:.1f}")

            if data["action"] == "BULLISH":
                st.success(f"**Signal:** {data['signal']}\n\n**Strike:** `{data['option_name']}`")
            elif data["action"] == "BEARISH":
                st.error(f"**Signal:** {data['signal']}\n\n**Strike:** `{data['option_name']}`")
            else:
                st.warning(f"**Signal:** {data['signal']}\n\n**Range:** `{data['option_name']}`")

            st.divider()
            if data["action"] in ["BULLISH", "BEARISH"]:
                st.write(f"• **Entry:** `₹{data['entry']:,.2f}`")
                st.write(f"• **Target:** `₹{data['target']:,.2f}` *(+{data['tgt_pts']} pts)*")
                st.write(f"• **Stop Loss:** `₹{data['sl']:,.2f}` *(-{data['sl_pts']} pts)*")
                c1, c2 = st.columns(2)
                c1.success(f"**Profit:** +₹{data['est_profit']:,}")
                c2.error(f"**Loss:** -₹{data['est_loss']:,}")
            else:
                st.info("Clear trend nahi hai. Trade avoid karein.")
                st.caption(f"9 EMA: {data['ema9']:,.1f} | 20 SMA: {data['sma20']:,.1f}")

# ==========================================
# TAB 2: TOP 100 NSE F&O STOCKS SCREENER
# ==========================================
TOP_100_FNO_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "BHARTIARTL.NS", "SBIN.NS", "LICI.NS", "ITC.NS", "HINDUNILVR.NS",
    "LT.NS", "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "ADANIENT.NS", "KOTAKBANK.NS", "TITAN.NS", "ONGC.NS", "TATAMOTORS.NS",
    "NTPC.NS", "AXISBANK.NS", "ADANIPORTS.NS", "ULTRACEMCO.NS", "M&M.NS",
    "ASIANPAINT.NS", "COALINDIA.NS", "BAJAJFINSV.NS", "POWERGRID.NS", "WIPRO.NS",
    "NESTLEIND.NS", "IOC.NS", "TATASTEEL.NS", "JSWSTEEL.NS", "DLF.NS",
    "SIEMENS.NS", "HAL.NS", "BEL.NS", "VBL.NS", "TRENT.NS",
    "GRASIM.NS", "TECHM.NS", "INDUSINDBK.NS", "HINDALCO.NS", "DIVISLAB.NS",
    "SBILIFE.NS", "HDFCLIFE.NS", "DRREDDY.NS", "CIPLA.NS", "BPCL.NS",
    "EICHERMOT.NS", "BRITANNIA.NS", "APOLLOHOSP.NS", "HEROMOTOCO.NS", "TATACONSUM.NS",
    "BAJAJ-AUTO.NS", "PIDILITIND.NS", "HAVELLS.NS", "GODREJCP.NS", "DABUR.NS",
    "SHREECEM.NS", "AMBUJACEM.NS", "ACC.NS", "GAIL.NS", "BANKBARODA.NS",
    "PNB.NS", "CANBK.NS", "UNIONBANK.NS", "IDFCFIRSTB.NS", "FEDERALBNK.NS",
    "AUBANK.NS", "BANDHANBNK.NS", "CHOLAFIN.NS", "SHRIRAMFIN.NS", "MUTHOOTFIN.NS",
    "MANAPPURAM.NS", "RECLTD.NS", "PFC.NS", "IRCTC.NS", "IRFC.NS",
    "BHEL.NS", "SAIL.NS", "NMDC.NS", "VEDL.NS", "NATIONALUM.NS",
    "JINDALSTEL.NS", "INDIGO.NS", "ZOMATO.NS", "NAUKRI.NS", "PERSISTENT.NS",
    "COFORGE.NS", "LTIM.NS", "MPHASIS.NS", "KPITTECH.NS", "POLYCAB.NS",
    "ASTRAL.NS", "CUMMINSIND.NS", "TVSMOTOR.NS", "ASHOKLEY.NS", "MOTHERSON.NS"
]

@st.cache_data(ttl=55)
def scan_top_100_stocks(vol_mult, adx_threshold, rr):
    signals = []
    # Batch download for fast scanning (15m timeframe gives much higher accuracy for stocks)
    data = yf.download(TOP_100_FNO_STOCKS, period="5d", interval="15m", group_by="ticker", progress=False, threads=True)
    
    for ticker in TOP_100_FNO_STOCKS:
        try:
            df = data[ticker].dropna()
            if len(df) < 55:
                continue

            close = df['Close']
            high = df['High']
            low = df['Low']
            volume = df['Volume']

            df['EMA20'] = ta.trend.ema_indicator(close, window=20)
            df['EMA50'] = ta.trend.ema_indicator(close, window=50)
            df['RSI'] = ta.momentum.rsi(close, window=14)
            df['ADX'] = ta.trend.adx(high, low, close, window=14)
            df['ATR'] = ta.volatility.average_true_range(high, low, close, window=14)
            df['VOL_AVG'] = volume.rolling(window=20).mean()

            latest = df.iloc[-1]
            price = float(latest['Close'])
            ema20 = float(latest['EMA20'])
            ema50 = float(latest['EMA50'])
            rsi = float(latest['RSI'])
            adx = float(latest['ADX'])
            atr = float(latest['ATR'])
            curr_vol = float(latest['Volume'])
            avg_vol = float(latest['VOL_AVG'])

            if avg_vol == 0 or pd.isna(adx) or pd.isna(atr):
                continue

            vol_ratio = curr_vol / avg_vol
            clean_name = ticker.replace(".NS", "")

            # Dynamic SL & Target based on ATR (Volatility) for accurate levels
            sl_dist = round(atr * 1.5, 2)
            tgt_dist = round(sl_dist * rr, 2)

            # HIGH ACCURACY BULLISH CONDITION (All 4 must match)
            if (price > ema20 > ema50) and (55 <= rsi <= 70) and (adx >= adx_threshold) and (vol_ratio >= vol_mult):
                signals.append({
                    "Stock": clean_name,
                    "Direction": "BUY / CALL 🟢",
                    "Type": "BULLISH",
                    "Entry": round(price, 2),
                    "Target": round(price + tgt_dist, 2),
                    "SL": round(price - sl_dist, 2),
                    "RSI": round(rsi, 1),
                    "ADX": round(adx, 1),
                    "Vol_Spike": f"{vol_ratio:.1f}x"
                })

            # HIGH ACCURACY BEARISH CONDITION (All 4 must match)
            elif (price < ema20 < ema50) and (30 <= rsi <= 45) and (adx >= adx_threshold) and (vol_ratio >= vol_mult):
                signals.append({
                    "Stock": clean_name,
                    "Direction": "SELL / PUT 🔴",
                    "Type": "BEARISH",
                    "Entry": round(price, 2),
                    "Target": round(price - tgt_dist, 2),
                    "SL": round(price + sl_dist, 2),
                    "RSI": round(rsi, 1),
                    "ADX": round(adx, 1),
                    "Vol_Spike": f"{vol_ratio:.1f}x"
                })
        except Exception:
            continue

    return signals

with tab2:
    st.subheader("🎯 High-Accuracy NSE F&O Stocks Scanner (15-Min Breakout)")
    st.write("Yeh scanner Top 100 NSE F&O stocks mein **4 strict confirmations** (20/50 EMA Trend + RSI + ADX Strength + Volume Breakout) check karke sirf high-probability trades dikhata hai.")

    with st.spinner("Top 100 NSE F&O stocks scan ho rahe hain..."):
        matched_stocks = scan_top_100_stocks(vol_multiplier, adx_min, rr_ratio)

    if not matched_stocks:
        st.info("Abhi kisi bhi Top 100 stock mein 4/4 high-accuracy criteria match nahi ho rahe hain. Jab strong volume breakout aayega, stock yahan apne aap dikh jayega.")
    else:
        st.success(f"🔥 {len(matched_stocks)} High-Accuracy Stock Trade(s) Mile Hain!")
        
        # Display cards for matched stocks
        for i in range(0, len(matched_stocks), 2):
            row_cols = st.columns(2)
            for j in range(2):
                if i + j < len(matched_stocks):
                    stk = matched_stocks[i + j]
                    with row_cols[j]:
                        with st.container(border=True):
                            st.markdown(f"### {stk['Stock']} — {stk['Direction']}")
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Entry Price", f"₹{stk['Entry']}")
                            c2.metric("Target", f"₹{stk['Target']}")
                            c3.metric("Stop Loss", f"₹{stk['SL']}")
                            
                            st.caption(f"📊 **Confirmations:** RSI: `{stk['RSI']}` | ADX: `{stk['ADX']}` | Volume: `{stk['Vol_Spike']} Avg`")

st.divider()
st.caption("⚠️ Note: Stock market mein koi bhi indicator 100% guarantee nahi deta. Yeh 4-indicator filter false breakouts ko kam karne ke liye banaya gaya hai—hamesha Stop Loss ke saath trade karein.")
