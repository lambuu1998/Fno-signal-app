import time
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="ARVANO Split BUY / SELL Portal Scanner",
    page_icon="⚖️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0c0c0f;
        color: #f6f1e7;
    }
    .portal-header-buy {
        background: rgba(34, 197, 94, 0.14);
        border: 1px solid rgba(34, 197, 94, 0.45);
        border-radius: 10px;
        padding: 10px 14px;
        font-size: 1.05rem;
        font-weight: 800;
        color: #4ade80;
        margin-bottom: 12px;
        text-align: center;
    }
    .portal-header-sell {
        background: rgba(239, 68, 68, 0.14);
        border: 1px solid rgba(239, 68, 68, 0.45);
        border-radius: 10px;
        padding: 10px 14px;
        font-size: 1.05rem;
        font-weight: 800;
        color: #f87171;
        margin-bottom: 12px;
        text-align: center;
    }
    .split-card-buy {
        background: linear-gradient(145deg, #131b17 0%, #19211b 100%);
        border: 1px solid #284635;
        border-left: 5px solid #22c55e;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 12px;
    }
    .split-card-sell {
        background: linear-gradient(145deg, #1d1416 0%, #241719 100%);
        border: 1px solid #4d292f;
        border-left: 5px solid #ef4444;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 12px;
    }
    .card-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 6px;
    }
    .card-title {
        font-size: 1.04rem;
        font-weight: 800;
        color: #fff7e8;
    }
    .card-action-buy {
        background: rgba(34, 197, 94, 0.22);
        color: #4ade80;
        border: 1px solid #22c55e;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 800;
    }
    .card-action-sell {
        background: rgba(239, 68, 68, 0.22);
        color: #f87171;
        border: 1px solid #ef4444;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 800;
    }
    .card-levels {
        font-size: 0.90rem;
        color: #f2e6ce;
        margin-bottom: 8px;
        line-height: 1.45;
    }
    .badge-strip {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 8px;
    }
    .st-badge {
        font-size: 0.78rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.14);
        color: #e8decb;
    }
    .st-hit {
        background: rgba(34, 197, 94, 0.24);
        border: 1px solid #22c55e;
        color: #4ade80;
    }
    .st-sl {
        background: rgba(239, 68, 68, 0.25);
        border: 1px solid #ef4444;
        color: #f87171;
    }
    .card-why {
        font-size: 0.84rem;
        color: #e5dccb;
        background: rgba(0, 0, 0, 0.22);
        border-radius: 8px;
        padding: 8px 10px;
        line-height: 1.4;
    }
    .empty-portal {
        background: rgba(255, 255, 255, 0.025);
        border: 1px dashed rgba(255, 255, 255, 0.16);
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        color: #b7ab96;
        font-size: 0.90rem;
        margin-bottom: 12px;
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
    return atm - step


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

    # Criterion 1: Trend EMAs (10 EMA & 50 EMA)
    d["ema10"] = close.ewm(span=10, adjust=False).mean()
    d["ema50"] = close.ewm(span=50, adjust=False).mean()

    # Criterion 2: Intraday VWAP
    tp = (high + low + close) / 3.0
    if vol.sum() > 0:
        day_key = d.index.date
        pv_cum = (tp * vol).groupby(day_key).cumsum()
        v_cum = vol.groupby(day_key).cumsum().replace(0, np.nan)
        d["vwap"] = (pv_cum / v_cum).ffill().fillna(close.ewm(span=24, adjust=False).mean())
    else:
        d["vwap"] = close.ewm(span=24, adjust=False).mean()

    # Criterion 3: RSI (14) & ADX (14)
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    d["rsi14"] = (100 - (100 / (1 + rs))).fillna(50.0)

    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low).abs(), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    d["atr14"] = tr.ewm(alpha=1 / 14, adjust=False).mean()
    d["atr_pct"] = (d["atr14"] / close.replace(0, np.nan)) * 100.0

    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    atr_safe = d["atr14"].replace(0, np.nan)
    plus_di = 100 * pd.Series(plus_dm, index=d.index).ewm(alpha=1 / 14, adjust=False).mean() / atr_safe
    minus_di = 100 * pd.Series(minus_dm, index=d.index).ewm(alpha=1 / 14, adjust=False).mean() / atr_safe
    dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)).fillna(0.0)
    d["adx14"] = dx.ewm(alpha=1 / 14, adjust=False).mean()

    # Criterion 4: Support / Resistance & Pattern Break levels
    d["res20"] = high.shift(1).rolling(20).max()
    d["sup20"] = low.shift(1).rolling(20).min()
    d["hh10"] = high.shift(1).rolling(10).max()
    d["ll10"] = low.shift(1).rolling(10).min()

    return d.dropna(subset=["ema50", "atr14", "res20", "sup20", "hh10", "ll10"])


def check_hits(d: pd.DataFrame, side: str, sl: float, t1: float, t2: float, t3: float) -> dict:
    today = d.index[-1].date()
    today_df = d[d.index.date == today]
    if today_df.empty:
        today_df = d.tail(4)

    max_high = float(today_df["High"].max())
    min_low = float(today_df["Low"].min())
    last_close = float(d["Close"].iloc[-1])

    if side == "BUY":
        return {
            "t1_hit": (max_high >= t1) or (last_close >= t1),
            "t2_hit": (max_high >= t2) or (last_close >= t2),
            "t3_hit": (max_high >= t3) or (last_close >= t3),
            "sl_hit": (min_low <= sl) or (last_close <= sl),
        }

    return {
        "t1_hit": (min_low <= t1) or (last_close <= t1),
        "t2_hit": (min_low <= t2) or (last_close <= t2),
        "t3_hit": (min_low <= t3) or (last_close <= t3),
        "sl_hit": (max_high >= sl) or (last_close >= sl),
    }


def evaluate_four_criteria(d: pd.DataFrame, name: str, strike_step: int | None = None) -> dict | None:
    """
    Requires all 4 core criteria to align in the same direction (BUY or SELL):
      1. EMA Trend (10 EMA & 50 EMA)
      2. VWAP position
      3. Momentum & Strength (RSI 14 + ADX 14)
      4. Support/Resistance & Chart Pattern structure
    """
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
    hh10 = float(last["hh10"])
    ll10 = float(last["ll10"])

    lows_win = d["Low"].iloc[-25:-1]
    highs_win = d["High"].iloc[-25:-1]
    min_low = float(lows_win.min()) if len(lows_win) else sup20
    max_high = float(highs_win.max()) if len(highs_win) else res20

    # --- ALL 4 BUY CRITERIA ---
    c1_buy = (price > ema50) and (ema10 >= ema50 * 0.999)
    c2_buy = price > vwap
    c3_buy = (rsi >= 55) and (adx >= 20)
    bull_pattern = "Breakout / Continuation"
    if price > res20:
        bull_pattern = f"Resistance {res20:.2f} Break"
    elif abs(min_low - sup20) / max(sup20, 1e-6) <= 0.004 and price > ema10:
        bull_pattern = "Double Bottom Breakout"
    elif price > hh10:
        bull_pattern = "Higher-High Pattern Break"
    c4_buy = (price > res20) or (price > hh10) or (abs(price - res20) / max(price, 1e-6) <= 0.004) or ("Double Bottom" in bull_pattern)

    # --- ALL 4 SELL CRITERIA ---
    c1_sell = (price < ema50) and (ema10 <= ema50 * 1.001)
    c2_sell = price < vwap
    c3_sell = (rsi <= 45) and (adx >= 20)
    bear_pattern = "Breakdown / Continuation"
    if price < sup20:
        bear_pattern = f"Support {sup20:.2f} Break"
    elif abs(max_high - res20) / max(res20, 1e-6) <= 0.004 and price < ema10:
        bear_pattern = "Double Top Breakdown"
    elif price < ll10:
        bear_pattern = "Lower-Low Pattern Break"
    c4_sell = (price < sup20) or (price < ll10) or (abs(price - sup20) / max(price, 1e-6) <= 0.004) or ("Double Top" in bear_pattern)

    if c1_buy and c2_buy and c3_buy and c4_buy:
        side = "BUY"
        action_text = f"BUY {round_strike(price, strike_step, 'BUY')} CE" if strike_step else "BUY"
        entry = price
        sl = max(0.0, entry - 2.0 * atr)
        t1 = entry + 1.5 * atr
        t2 = entry + 2.8 * atr
        t3 = entry + 4.2 * atr
        why = (
            f"All 4 BUY criteria matched | Pattern/SR: {bull_pattern} | "
            f"EMA10/50: {ema10:.2f}/{ema50:.2f} | VWAP: {vwap:.2f} | RSI: {rsi:.1f} | ADX: {adx:.1f}"
        )
    elif c1_sell and c2_sell and c3_sell and c4_sell:
        side = "SELL"
        action_text = f"BUY {round_strike(price, strike_step, 'SELL')} PE" if strike_step else "SELL"
        entry = price
        sl = entry + 2.0 * atr
        t1 = max(0.0, entry - 1.5 * atr)
        t2 = max(0.0, entry - 2.8 * atr)
        t3 = max(0.0, entry - 4.2 * atr)
        why = (
            f"All 4 SELL criteria matched | Pattern/SR: {bear_pattern} | "
            f"EMA10/50: {ema10:.2f}/{ema50:.2f} | VWAP: {vwap:.2f} | RSI: {rsi:.1f} | ADX: {adx:.1f}"
        )
    else:
        return None

    lock_key = f"split_lock_{name}"
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

    hits = check_hits(d, side, sl, t1, t2, t3)
    move_score = (atr_pct * 2.2) + (adx * 0.6)

    return {
        "name": name,
        "side": side,
        "action_text": action_text,
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
def fetch_data(ticker: str, period: str = "10d", interval: str = "15m") -> pd.DataFrame:
    try:
        raw = yf.download(ticker, period=period, interval=interval, progress=False, threads=False)
        if raw is None or raw.empty:
            return pd.DataFrame()
        return add_indicators(raw)
    except Exception:
        return pd.DataFrame()


def render_split_card(item: dict):
    is_buy = item["side"] == "BUY"
    card_cls = "split-card-buy" if is_buy else "split-card-sell"
    pill_cls = "card-action-buy" if is_buy else "card-action-sell"

    t1_cls = "st-badge st-hit" if item["t1_hit"] else "st-badge"
    t2_cls = "st-badge st-hit" if item["t2_hit"] else "st-badge"
    t3_cls = "st-badge st-hit" if item["t3_hit"] else "st-badge"
    sl_cls = "st-badge st-sl" if item["sl_hit"] else "st-badge"

    t1_lbl = f"T1 {item['t1']:.2f} — HIT" if item["t1_hit"] else f"T1 {item['t1']:.2f}"
    t2_lbl = f"T2 {item['t2']:.2f} — HIT" if item["t2_hit"] else f"T2 {item['t2']:.2f}"
    t3_lbl = f"T3 {item['t3']:.2f} — HIT" if item["t3_hit"] else f"T3 {item['t3']:.2f}"
    sl_lbl = f"SL {item['sl']:.2f} — SL HIT" if item["sl_hit"] else f"SL {item['sl']:.2f}"

    st.markdown(
        f"""
        <div class="{card_cls}">
            <div class="card-top">
                <div class="card-title">{item['name']}</div>
                <span class="{pill_cls}">{item['action_text']}</span>
            </div>
            <div class="card-levels">
                <b>Entry:</b> {item['entry']:.2f} &nbsp;|&nbsp;
                <b>CMP:</b> {item['cmp']:.2f} &nbsp;|&nbsp;
                <b>ATR%:</b> {item['atr_pct']:.2f}%
            </div>
            <div class="badge-strip">
                <span class="{t1_cls}">{t1_lbl}</span>
                <span class="{t2_cls}">{t2_lbl}</span>
                <span class="{t3_cls}">{t3_lbl}</span>
                <span class="{sl_cls}">{sl_lbl}</span>
            </div>
            <div class="card-why">{item['why']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_divided_portals(section_title: str, buy_items: list, sell_items: list, empty_buy_msg: str, empty_sell_msg: str):
    st.subheader(section_title)
    left_col, mid_col, right_col = st.columns([10, 0.25, 10])

    with left_col:
        st.markdown('<div class="portal-header-buy">LEFT PORTAL — BUY / CALL (ALL 4 CRITERIA MATCHED)</div>', unsafe_allow_html=True)
        if buy_items:
            for it in buy_items:
                render_split_card(it)
        else:
            st.markdown(f'<div class="empty-portal">{empty_buy_msg}</div>', unsafe_allow_html=True)

    with mid_col:
        st.markdown(
            '<div style="border-left: 2px solid #5c4d38; height: 100%; min-height: 220px; margin: 0 auto;"></div>',
            unsafe_allow_html=True,
        )

    with right_col:
        st.markdown('<div class="portal-header-sell">RIGHT PORTAL — SELL / PUT (ALL 4 CRITERIA MATCHED)</div>', unsafe_allow_html=True)
        if sell_items:
            for it in sell_items:
                render_split_card(it)
        else:
            st.markdown(f'<div class="empty-portal">{empty_sell_msg}</div>', unsafe_allow_html=True)


# Sidebar Controls
st.sidebar.header("Split Portal Controls")
refresh_sec = st.sidebar.slider("Auto-Refresh (Seconds)", min_value=30, max_value=60, value=45, step=5)
auto_refresh = st.sidebar.checkbox("Auto-Refresh ON (30–60s)", value=True)
tf = st.sidebar.selectbox("Timeframe", ["15m", "30m"], index=0)
period_map = {"15m": "10d", "30m": "15d"}

if st.sidebar.button("Refresh Now"):
    st.cache_data.clear()

st.title("⚖️ ARVANO Split BUY / SELL Portal Scanner (No Charts)")
st.caption(
    f"Auto-refresh: {refresh_sec}s | Left = BUY Portal | Right = SELL Portal | Strict 4-Criteria Lock (EMA Trend + VWAP + RSI/ADX + S/R & Pattern)"
)

# 1. Indices Split Portal (Nifty 50, Bank Nifty, Sensex)
idx_buy, idx_sell = [], []
for idx_name, cfg in INDICES.items():
    df_i = fetch_data(cfg["ticker"], period=period_map[tf], interval=tf)
    if not df_i.empty:
        sig_i = evaluate_four_criteria(df_i, idx_name, strike_step=cfg["step"])
        if sig_i:
            (idx_buy if sig_i["side"] == "BUY" else idx_sell).append(sig_i)

render_divided_portals(
    section_title="1. F&O Indices Split Portal (Nifty 50 • Bank Nifty • Sensex)",
    buy_items=idx_buy,
    sell_items=idx_sell,
    empty_buy_msg="Indices mein abhi saare 4 BUY criteria match nahi hue hain — trade nahi.",
    empty_sell_msg="Indices mein abhi saare 4 SELL criteria match nahi hue hain — trade nahi.",
)

st.markdown("---")

# 2. Gold & Silver Split Portal
metal_buy, metal_sell = [], []
for m_name, m_ticker in METALS.items():
    df_m = fetch_data(m_ticker, period=period_map[tf], interval=tf)
    if not df_m.empty:
        sig_m = evaluate_four_criteria(df_m, m_name, strike_step=None)
        if sig_m:
            (metal_buy if sig_m["side"] == "BUY" else metal_sell).append(sig_m)

render_divided_portals(
    section_title="2. Gold & Silver Split Portal",
    buy_items=metal_buy,
    sell_items=metal_sell,
    empty_buy_msg="Gold/Silver mein abhi saare 4 BUY criteria match nahi hue hain — trade nahi.",
    empty_sell_msg="Gold/Silver mein abhi saare 4 SELL criteria match nahi hue hain — trade nahi.",
)

st.markdown("---")

# 3. Top 100 NSE Stocks Split Portal
stock_buy, stock_sell = [], []
prog = st.progress(0, text="Scanning Top 100 NSE against all 4 BUY/SELL criteria...")
for i, sym in enumerate(TOP_100_NSE):
    df_s = fetch_data(sym, period=period_map[tf], interval=tf)
    if not df_s.empty:
        s_name = sym.replace(".NS", "")
        sig_s = evaluate_four_criteria(df_s, s_name, strike_step=None)
        if sig_s:
            (stock_buy if sig_s["side"] == "BUY" else stock_sell).append(sig_s)
    prog.progress((i + 1) / len(TOP_100_NSE), text=f"Scanning Top 100 NSE ({i + 1}/{len(TOP_100_NSE)})...")
prog.empty()

stock_buy.sort(key=lambda x: x["move_score"], reverse=True)
stock_sell.sort(key=lambda x: x["move_score"], reverse=True)

render_divided_portals(
    section_title="3. Top 100 NSE Stocks Split Portal (Left BUY vs Right SELL)",
    buy_items=stock_buy,
    sell_items=stock_sell,
    empty_buy_msg="Top 100 NSE mein abhi koi stock saare 4 BUY criteria poore nahi kar raha.",
    empty_sell_msg="Top 100 NSE mein abhi koi stock saare 4 SELL criteria poore nahi kar raha.",
)

if auto_refresh:
    time.sleep(refresh_sec)
    st.rerun()
