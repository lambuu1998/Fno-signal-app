import time
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="ARVANO Active Movers Box Scanner",
    page_icon="🎯",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0c0c0f;
        color: #f6f1e7;
    }
    .pro-box {
        background: linear-gradient(145deg, #151418 0%, #1d1914 100%);
        border: 1px solid #3a3124;
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35);
    }
    .pro-box-buy {
        border-left: 6px solid #22c55e;
    }
    .pro-box-sell {
        border-left: 6px solid #ef4444;
    }
    .box-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 10px;
    }
    .box-title {
        font-size: 1.14rem;
        font-weight: 800;
        color: #fff7e8;
    }
    .side-pill-buy {
        background: rgba(34, 197, 94, 0.2);
        color: #4ade80;
        border: 1px solid #22c55e;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 800;
    }
    .side-pill-sell {
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
        border: 1px solid #ef4444;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 800;
    }
    .price-strip {
        font-size: 0.96rem;
        color: #f3e6cc;
        margin-bottom: 12px;
        line-height: 1.5;
    }
    .target-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 12px;
    }
    .t-chip {
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 0.86rem;
        font-weight: 700;
        border: 1px solid #474034;
        background: rgba(255, 255, 255, 0.04);
        color: #e8decb;
    }
    .t-green {
        background: rgba(34, 197, 94, 0.22);
        border: 1px solid #22c55e;
        color: #4ade80;
    }
    .sl-red {
        background: rgba(239, 68, 68, 0.24);
        border: 1px solid #ef4444;
        color: #f87171;
    }
    .logic-box {
        background: rgba(255, 255, 255, 0.035);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 9px;
        padding: 10px 13px;
        font-size: 0.90rem;
        color: #ebe2d2;
        line-height: 1.45;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

INDICES = {
    "NIFTY 50": {"ticker": "^NSEI", "step": 50},
    "BANK NIFTY": {"ticker": "^NSEBANK", "step": 100},
    "SENSEX": {"ticker": "^BSESN", "step": 100},
}

METALS = {
    "GOLD FUTURES (USD)": "GC=F",
    "SILVER FUTURES (USD)": "SI=F",
    "GOLDBEES (NSE)": "GOLDBEES.NS",
    "SILVERBEES (NSE)": "SILVERBEES.NS",
}

TOP_100_NSE = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS",
    "SBIN.NS", "INFY.NS", "ITC.NS", "LT.NS", "HINDUNILVR.NS",
    "AXISBANK.NS", "KOTAKBANK.NS", "BAJFINANCE.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "M&M.NS", "HCLTECH.NS", "TITAN.NS", "ULTRACEMCO.NS", "NTPC.NS",
    "POWERGRID.NS", "ADANIENT.NS", "ADANIPORTS.NS", "ONGC.NS", "COALINDIA.NS",
    "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "ASIANPAINT.NS", "BAJAJFINSV.NS",
    "WIPRO.NS", "TECHM.NS", "INDUSINDBK.NS", "BANKBARODA.NS", "PNB.NS",
    "CANBK.NS", "IDFCFIRSTB.NS", "FEDERALBNK.NS", "AUBANK.NS", "CHOLAFIN.NS",
    "SHRIRAMFIN.NS", "MUTHOOTFIN.NS", "RECLTD.NS", "PFC.NS", "IRCTC.NS",
    "HAL.NS", "BEL.NS", "MAZDOCK.NS", "TRENT.NS", "ZOMATO.NS",
    "DMART.NS", "HAVELLS.NS", "VOLTAS.NS", "PIDILITIND.NS", "BERGEPAINT.NS",
    "DABUR.NS", "GODREJCP.NS", "MARICO.NS", "BRITANNIA.NS", "NESTLEIND.NS",
    "TATACONSUM.NS", "VBL.NS", "JUBLFOOD.NS", "INDIGO.NS", "DLF.NS",
    "GODREJPROP.NS", "OBEROIRLTY.NS", "LODHA.NS", "PHOENIXLTD.NS", "SIEMENS.NS",
    "ABB.NS", "CGPOWER.NS", "CUMMINSIND.NS", "BHEL.NS", "SUZLON.NS",
    "TATAPOWER.NS", "IOC.NS", "BPCL.NS", "HINDPETRO.NS", "GAIL.NS",
    "VEDL.NS", "NMDC.NS", "JINDALSTEL.NS", "SAIL.NS", "CIPLA.NS",
    "DRREDDY.NS", "DIVISLAB.NS", "LUPIN.NS", "AUROPHARMA.NS", "APOLLOHOSP.NS",
    "MAXHEALTH.NS", "FORTIS.NS", "SBILIFE.NS", "HDFCLIFE.NS", "ICICIPRULI.NS",
    "ICICIGI.NS", "SBICARD.NS", "TVSMOTOR.NS", "EICHERMOT.NS",
]
TOP_100_NSE = list(dict.fromkeys(TOP_100_NSE))


def round_strike(price: float, step: int, side: str) -> int:
    atm = int(round(price / step) * step)
    if side == "BUY":
        return atm + step
    if side == "SELL":
        return atm - step
    return atm


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)

    d = d.dropna(subset=["Open", "High", "Low", "Close"]).copy()
    if len(d) < 55:
        return pd.DataFrame()

    close = d["Close"].astype(float)
    high = d["High"].astype(float)
    low = d["Low"].astype(float)
    vol = d["Volume"].fillna(0).astype(float) if "Volume" in d.columns else pd.Series(0.0, index=d.index)

    # 1. Customized 10 EMA & 50 EMA
    d["ema10"] = close.ewm(span=10, adjust=False).mean()
    d["ema50"] = close.ewm(span=50, adjust=False).mean()

    # 2. VWAP
    tp = (high + low + close) / 3.0
    if vol.sum() > 0:
        day_key = d.index.date
        pv_cum = (tp * vol).groupby(day_key).cumsum()
        v_cum = vol.groupby(day_key).cumsum().replace(0, np.nan)
        d["vwap"] = (pv_cum / v_cum).ffill().fillna(close.ewm(span=24, adjust=False).mean())
    else:
        d["vwap"] = close.ewm(span=24, adjust=False).mean()

    # 3. RSI (14)
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    d["rsi14"] = (100 - (100 / (1 + rs))).fillna(50.0)

    # 4. ATR (14) & ATR%
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low).abs(), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    d["atr14"] = tr.ewm(alpha=1 / 14, adjust=False).mean()
    d["atr_pct"] = (d["atr14"] / close.replace(0, np.nan)) * 100.0

    # 5. ADX (14)
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    atr_safe = d["atr14"].replace(0, np.nan)
    plus_di = 100 * pd.Series(plus_dm, index=d.index).ewm(alpha=1 / 14, adjust=False).mean() / atr_safe
    minus_di = 100 * pd.Series(minus_dm, index=d.index).ewm(alpha=1 / 14, adjust=False).mean() / atr_safe
    dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)).fillna(0.0)
    d["adx14"] = dx.ewm(alpha=1 / 14, adjust=False).mean()

    # Support & Resistance (20-bar)
    d["res20"] = high.shift(1).rolling(20).max()
    d["sup20"] = low.shift(1).rolling(20).min()

    return d.dropna(subset=["ema50", "atr14", "res20", "sup20"])


def evaluate_hits(d: pd.DataFrame, side: str, sl: float, t1: float, t2: float, t3: float) -> dict:
    today = d.index[-1].date()
    today_df = d[d.index.date == today]
    if today_df.empty:
        today_df = d.tail(4)

    max_high = float(today_df["High"].max())
    min_low = float(today_df["Low"].min())
    last_close = float(d["Close"].iloc[-1])

    if side == "BUY":
        t1_hit = (max_high >= t1) or (last_close >= t1)
        t2_hit = (max_high >= t2) or (last_close >= t2)
        t3_hit = (max_high >= t3) or (last_close >= t3)
        sl_hit = (min_low <= sl) or (last_close <= sl)
    else:
        t1_hit = (min_low <= t1) or (last_close <= t1)
        t2_hit = (min_low <= t2) or (last_close <= t2)
        t3_hit = (min_low <= t3) or (last_close <= t3)
        sl_hit = (max_high >= sl) or (last_close >= sl)

    return {
        "t1_hit": t1_hit,
        "t2_hit": t2_hit,
        "t3_hit": t3_hit,
        "sl_hit": sl_hit,
    }


def scan_active_setup(d: pd.DataFrame, name: str, strike_step: int | None = None) -> dict | None:
    last = d.iloc[-1]
    price = float(last["Close"])
    ema10 = float(last["ema10"])
    ema50 = float(last["ema50"])
    vwap = float(last["vwap"])
    rsi = float(last["rsi14"])
    adx = float(last["adx14"])
    atr = float(last["atr14"])
    atr_pct = float(last["atr_pct"])
    res20 = float(last["res20"])
    sup20 = float(last["sup20"])

    lows_win = d["Low"].iloc[-25:-1]
    highs_win = d["High"].iloc[-25:-1]
    min_low = float(lows_win.min()) if len(lows_win) else sup20
    max_high = float(highs_win.max()) if len(highs_win) else res20

    bull_score = int(price > ema50) + int(price > vwap) + int(rsi >= 55) + int(adx >= 20) + int(price >= ema10)
    bear_score = int(price < ema50) + int(price < vwap) + int(rsi <= 45) + int(adx >= 20) + int(price <= ema10)

    sr_note = ""
    if price > res20:
        sr_note = f"Resistance {res20:.2f} break"
    elif price < sup20:
        sr_note = f"Support {sup20:.2f} break"
    elif abs(price - res20) / max(price, 1e-6) <= 0.003:
        sr_note = f"Resistance {res20:.2f} zone"
    elif abs(price - sup20) / max(price, 1e-6) <= 0.003:
        sr_note = f"Support {sup20:.2f} zone"

    pattern_note = ""
    if abs(min_low - sup20) / max(sup20, 1e-6) <= 0.004 and price >= ema10:
        pattern_note = "Double Bottom structure"
    elif abs(max_high - res20) / max(res20, 1e-6) <= 0.004 and price <= ema10:
        pattern_note = "Double Top structure"

    # Only return actionable BUY or SELL setups (filter out sideways/no-trade noise)
    if bull_score >= 4 and price > ema50 and price > vwap:
        side = "BUY"
        action_label = f"BUY {round_strike(price, strike_step, 'BUY')} CE" if strike_step else "BUY"
        entry = price
        sl = max(0.0, entry - 2.0 * atr)
        t1 = entry + 1.5 * atr
        t2 = entry + 2.8 * atr
        t3 = entry + 4.2 * atr
        why = f"Bullish alignment ({bull_score}/5): >50 EMA ({ema50:.2f}) & VWAP ({vwap:.2f}), RSI {rsi:.1f}, ADX {adx:.1f}"
    elif bear_score >= 4 and price < ema50 and price < vwap:
        side = "SELL"
        action_label = f"BUY {round_strike(price, strike_step, 'SELL')} PE" if strike_step else "SELL"
        entry = price
        sl = entry + 2.0 * atr
        t1 = max(0.0, entry - 1.5 * atr)
        t2 = max(0.0, entry - 2.8 * atr)
        t3 = max(0.0, entry - 4.2 * atr)
        why = f"Bearish alignment ({bear_score}/5): <50 EMA ({ema50:.2f}) & VWAP ({vwap:.2f}), RSI {rsi:.1f}, ADX {adx:.1f}"
    else:
        return None

    if sr_note:
        why = f"{sr_note} | {why}"
    if pattern_note:
        why = f"{pattern_note} | {why}"

    lock_key = f"active_lock_{name}"
    if lock_key not in st.session_state or st.session_state[lock_key]["side"] != side:
        st.session_state[lock_key] = {
            "side": side,
            "entry": round(entry, 2),
            "sl": round(sl, 2),
            "t1": round(t1, 2),
            "t2": round(t2, 2),
            "t3": round(t3, 2),
        }
    locked = st.session_state[lock_key]
    entry, sl, t1, t2, t3 = locked["entry"], locked["sl"], locked["t1"], locked["t2"], locked["t3"]

    hits = evaluate_hits(d, side, sl, t1, t2, t3)
    move_score = (atr_pct * 2.2) + (adx * 0.5) + (25.0 if "break" in sr_note.lower() else 0.0)

    return {
        "name": name,
        "side": side,
        "action_label": action_label,
        "cmp": round(price, 2),
        "entry": entry,
        "sl": sl,
        "t1": t1,
        "t2": t2,
        "t3": t3,
        "atr_pct": round(atr_pct, 2),
        "why": why,
        "move_score": move_score,
        **hits,
    }


@st.cache_data(ttl=25, show_spinner=False)
def fetch_15m(ticker: str, period: str = "10d", interval: str = "15m") -> pd.DataFrame:
    try:
        raw = yf.download(ticker, period=period, interval=interval, progress=False, threads=False)
        if raw is None or raw.empty:
            return pd.DataFrame()
        return add_indicators(raw)
    except Exception:
        return pd.DataFrame()


def render_mover_box(item: dict):
    is_buy = item["side"] == "BUY"
    box_cls = "pro-box pro-box-buy" if is_buy else "pro-box pro-box-sell"
    pill_cls = "side-pill-buy" if is_buy else "side-pill-sell"

    t1_cls = "t-chip t-green" if item["t1_hit"] else "t-chip"
    t2_cls = "t-chip t-green" if item["t2_hit"] else "t-chip"
    t3_cls = "t-chip t-green" if item["t3_hit"] else "t-chip"
    sl_cls = "t-chip sl-red" if item["sl_hit"] else "t-chip"

    t1_txt = f"T1: {item['t1']:.2f} — GREEN / HIT" if item["t1_hit"] else f"T1: {item['t1']:.2f} — Pending"
    t2_txt = f"T2: {item['t2']:.2f} — GREEN / HIT" if item["t2_hit"] else f"T2: {item['t2']:.2f} — Pending"
    t3_txt = f"T3: {item['t3']:.2f} — GREEN / HIT" if item["t3_hit"] else f"T3: {item['t3']:.2f} — Pending"
    sl_txt = f"SL: {item['sl']:.2f} — SL HIT" if item["sl_hit"] else f"SL: {item['sl']:.2f} — Safe"

    st.markdown(
        f"""
        <div class="{box_cls}">
            <div class="box-header">
                <div class="box-title">{item['name']}</div>
                <span class="{pill_cls}">{item['action_label']}</span>
            </div>
            <div class="price-strip">
                <b>Entry Price:</b> {item['entry']:.2f} &nbsp;|&nbsp;
                <b>CMP:</b> {item['cmp']:.2f} &nbsp;|&nbsp;
                <b>ATR%:</b> {item['atr_pct']:.2f}%
            </div>
            <div class="target-row">
                <span class="{t1_cls}">{t1_txt}</span>
                <span class="{t2_cls}">{t2_txt}</span>
                <span class="{t3_cls}">{t3_txt}</span>
                <span class="{sl_cls}">{sl_txt}</span>
            </div>
            <div class="logic-box"><b>Kyun (Logic):</b> {item['why']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Sidebar Controls
st.sidebar.header("Live Mover Controls")
refresh_sec = st.sidebar.slider("Auto-Refresh (Seconds)", min_value=30, max_value=60, value=45, step=5)
auto_refresh = st.sidebar.checkbox("Auto-Refresh ON (30–60s)", value=True)
tf = st.sidebar.selectbox("Timeframe", ["15m", "30m"], index=0)
period_map = {"15m": "10d", "30m": "15d"}

if st.sidebar.button("Refresh Now"):
    st.cache_data.clear()

st.title("🎯 ARVANO Active Movers Box Scanner (No Charts)")
st.caption(
    f"Auto-refresh: {refresh_sec}s | Shows ONLY active BUY / SELL movement setups across Nifty 50, Bank Nifty, Sensex, Gold & Silver, and Top 100 NSE"
)

# 1. F&O Indices (Only Active BUY/SELL setups)
st.subheader("1. F&O Indices Active Setups (Nifty 50 • Bank Nifty • Sensex)")
active_indices = []
for idx_name, cfg in INDICES.items():
    df_i = fetch_15m(cfg["ticker"], period=period_map[tf], interval=tf)
    if not df_i.empty:
        sig_i = scan_active_setup(df_i, idx_name, strike_step=cfg["step"])
        if sig_i:
            active_indices.append(sig_i)

if active_indices:
    for item in active_indices:
        render_mover_box(item)
else:
    st.info("Abhi Nifty 50 / Bank Nifty / Sensex mein koi clean BUY/SELL breakout lock nahi hua hai.")

st.markdown("---")

# 2. Gold & Silver (Only Active BUY/SELL setups)
st.subheader("2. Gold & Silver Active Setups")
active_metals = []
for m_name, m_ticker in METALS.items():
    df_m = fetch_15m(m_ticker, period=period_map[tf], interval=tf)
    if not df_m.empty:
        sig_m = scan_active_setup(df_m, m_name, strike_step=None)
        if sig_m:
            active_metals.append(sig_m)

if active_metals:
    for item in active_metals:
        render_mover_box(item)
else:
    st.info("Abhi Gold/Silver mein koi clean BUY/SELL movement setup nahi bana hai.")

st.markdown("---")

# 3. Top 100 NSE Backend Scan -> Only Active BUY/SELL Movers Shown
st.subheader("3. Active Stock Movers Today (Filtered from Top 100 NSE)")
active_stocks = []
prog = st.progress(0, text="Filtering Top 100 NSE for active BUY/SELL movers...")
for i, sym in enumerate(TOP_100_NSE):
    df_s = fetch_15m(sym, period=period_map[tf], interval=tf)
    if not df_s.empty:
        s_name = sym.replace(".NS", "")
        sig_s = scan_active_setup(df_s, s_name, strike_step=None)
        if sig_s:
            active_stocks.append(sig_s)
    prog.progress((i + 1) / len(TOP_100_NSE), text=f"Scanning Top 100 NSE ({i + 1}/{len(TOP_100_NSE)})...")
prog.empty()

active_stocks.sort(key=lambda x: x["move_score"], reverse=True)

if active_stocks:
    st.success(f"Aaj {len(active_stocks)} active stock movers mile hain:")
    for item in active_stocks:
        render_mover_box(item)
else:
    st.info("Abhi Top 100 NSE stocks mein koi strong BUY/SELL signal lock nahi hua hai.")

if auto_refresh:
    time.sleep(refresh_sec)
    st.rerun()
