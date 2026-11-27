import time
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="ARVANO SELL | BUY Split Scanner",
    page_icon="⚡",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b0b0e;
        color: #f6f1e7;
    }
    .sell-box {
        background: linear-gradient(145deg, #1d1315 0%, #261719 100%);
        border: 1px solid #52292f;
        border-left: 5px solid #ef4444;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 12px;
    }
    .buy-box {
        background: linear-gradient(145deg, #121c17 0%, #17231c 100%);
        border: 1px solid #284a37;
        border-left: 5px solid #22c55e;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 12px;
    }
    .box-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 6px;
    }
    .box-name {
        font-size: 1.04rem;
        font-weight: 800;
        color: #fff7e8;
    }
    .tag-sell {
        background: rgba(239, 68, 68, 0.24);
        color: #f87171;
        border: 1px solid #ef4444;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 800;
    }
    .tag-buy {
        background: rgba(34, 197, 94, 0.22);
        color: #4ade80;
        border: 1px solid #22c55e;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 800;
    }
    .box-lvl {
        font-size: 0.90rem;
        color: #f3e6ce;
        margin-bottom: 8px;
        line-height: 1.45;
    }
    .st-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 8px;
    }
    .st-pill {
        font-size: 0.78rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.14);
        color: #e9e0cf;
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
    .box-why {
        font-size: 0.84rem;
        color: #e6ddcc;
        background: rgba(0, 0, 0, 0.25);
        border-radius: 8px;
        padding: 8px 10px;
        line-height: 1.4;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

FNO_INDICES = {
    "NIFTY 50": {"ticker": "^NSEI", "step": 50},
    "BANK NIFTY": {"ticker": "^NSEBANK", "step": 100},
    "SENSEX": {"ticker": "^BSESN", "step": 100},
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

GOLD_SILVER = {
    "GOLD FUTURES (USD)": "GC=F",
    "SILVER FUTURES (USD)": "SI=F",
    "GOLDBEES (NSE)": "GOLDBEES.NS",
    "SILVERBEES (NSE)": "SILVERBEES.NS",
}


def strike_pick(price: float, step: int, side: str) -> int:
    atm = int(round(price / step) * step)
    return atm + step if side == "BUY" else atm - step


def compute_setup_df(df: pd.DataFrame) -> pd.DataFrame:
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

    # Customized EMAs (10 EMA & 50 EMA)
    d["ema10"] = close.ewm(span=10, adjust=False).mean()
    d["ema50"] = close.ewm(span=50, adjust=False).mean()

    # Intraday VWAP
    tp = (high + low + close) / 3.0
    if vol.sum() > 0:
        day_key = d.index.date
        pv_cum = (tp * vol).groupby(day_key).cumsum()
        v_cum = vol.groupby(day_key).cumsum().replace(0, np.nan)
        d["vwap"] = (pv_cum / v_cum).ffill().fillna(close.ewm(span=24, adjust=False).mean())
    else:
        d["vwap"] = close.ewm(span=24, adjust=False).mean()

    # RSI (14)
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    d["rsi14"] = (100 - (100 / (1 + rs))).fillna(50.0)

    # ATR (14) & ATR%
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low).abs(), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    d["atr14"] = tr.ewm(alpha=1 / 14, adjust=False).mean()
    d["atr_pct"] = (d["atr14"] / close.replace(0, np.nan)) * 100.0

    # ADX (14)
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    atr_safe = d["atr14"].replace(0, np.nan)
    plus_di = 100 * pd.Series(plus_dm, index=d.index).ewm(alpha=1 / 14, adjust=False).mean() / atr_safe
    minus_di = 100 * pd.Series(minus_dm, index=d.index).ewm(alpha=1 / 14, adjust=False).mean() / atr_safe
    dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)).fillna(0.0)
    d["adx14"] = dx.ewm(alpha=1 / 14, adjust=False).mean()

    # Support / Resistance & Break Structure
    d["res20"] = high.shift(1).rolling(20).max()
    d["sup20"] = low.shift(1).rolling(20).min()
    d["hh10"] = high.shift(1).rolling(10).max()
    d["ll10"] = low.shift(1).rolling(10).min()

    return d.dropna(subset=["ema50", "atr14", "res20", "sup20", "hh10", "ll10"])


def target_sl_flags(d: pd.DataFrame, side: str, sl: float, t1: float, t2: float, t3: float) -> dict:
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


def get_active_move(d: pd.DataFrame, name: str, strike_step: int | None = None) -> dict | None:
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

    # BUY criteria: EMA trend + VWAP + RSI/ADX momentum + S/R or pattern break
    buy_ok = (
        (price > ema50)
        and (ema10 >= ema50 * 0.999)
        and (price > vwap)
        and (rsi >= 55)
        and (adx >= 22)
        and (
            (price > res20)
            or (price > hh10)
            or (abs(price - res20) / max(price, 1e-6) <= 0.004)
            or (abs(min_low - sup20) / max(sup20, 1e-6) <= 0.004 and price > ema10)
        )
    )

    # SELL criteria: EMA trend + VWAP + RSI/ADX momentum + S/R or pattern breakdown
    sell_ok = (
        (price < ema50)
        and (ema10 <= ema50 * 1.001)
        and (price < vwap)
        and (rsi <= 45)
        and (adx >= 22)
        and (
            (price < sup20)
            or (price < ll10)
            or (abs(price - sup20) / max(price, 1e-6) <= 0.004)
            or (abs(max_high - res20) / max(res20, 1e-6) <= 0.004 and price < ema10)
        )
    )

    if buy_ok:
        side = "BUY"
        action_text = f"BUY {strike_pick(price, strike_step, 'BUY')} CE" if strike_step else "BUY"
        entry = price
        sl = max(0.0, entry - 2.0 * atr)
        t1 = entry + 1.5 * atr
        t2 = entry + 2.8 * atr
        t3 = entry + 4.2 * atr
        pat = f"Res {res20:.2f} Break" if price > res20 else ("Double Bottom" if abs(min_low - sup20) / max(sup20, 1e-6) <= 0.004 else "HH Breakout")
        why = f"{pat} | >50 EMA ({ema50:.2f}) & VWAP ({vwap:.2f}) | RSI {rsi:.1f} | ADX {adx:.1f}"
    elif sell_ok:
        side = "SELL"
        action_text = f"BUY {strike_pick(price, strike_step, 'SELL')} PE" if strike_step else "SELL"
        entry = price
        sl = entry + 2.0 * atr
        t1 = max(0.0, entry - 1.5 * atr)
        t2 = max(0.0, entry - 2.8 * atr)
        t3 = max(0.0, entry - 4.2 * atr)
        pat = f"Sup {sup20:.2f} Break" if price < sup20 else ("Double Top" if abs(max_high - res20) / max(res20, 1e-6) <= 0.004 else "LL Breakdown")
        why = f"{pat} | <50 EMA ({ema50:.2f}) & VWAP ({vwap:.2f}) | RSI {rsi:.1f} | ADX {adx:.1f}"
    else:
        return None

    lock_key = f"move_lock_{name}"
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

    flags = target_sl_flags(d, side, sl, t1, t2, t3)
    score = (atr_pct * 2.2) + (adx * 0.6)

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
        "score": score,
        **flags,
    }


@st.cache_data(ttl=25, show_spinner=False)
def fetch_candles(ticker: str, period: str = "10d", interval: str = "15m") -> pd.DataFrame:
    try:
        raw = yf.download(ticker, period=period, interval=interval, progress=False, threads=False)
        if raw is None or raw.empty:
            return pd.DataFrame()
        return compute_setup_df(raw)
    except Exception:
        return pd.DataFrame()


def render_side_box(item: dict):
    is_sell = item["side"] == "SELL"
    box_cls = "sell-box" if is_sell else "buy-box"
    tag_cls = "tag-sell" if is_sell else "tag-buy"

    t1_cls = "st-pill st-hit" if item["t1_hit"] else "st-pill"
    t2_cls = "st-pill st-hit" if item["t2_hit"] else "st-pill"
    t3_cls = "st-pill st-hit" if item["t3_hit"] else "st-pill"
    sl_cls = "st-pill st-sl" if item["sl_hit"] else "st-pill"

    st.markdown(
        f"""
        <div class="{box_cls}">
            <div class="box-head">
                <div class="box-name">{item['name']}</div>
                <span class="{tag_cls}">{item['action_text']}</span>
            </div>
            <div class="box-lvl">
                <b>Entry:</b> {item['entry']:.2f} &nbsp;|&nbsp;
                <b>CMP:</b> {item['cmp']:.2f} &nbsp;|&nbsp;
                <b>ATR%:</b> {item['atr_pct']:.2f}%
            </div>
            <div class="st-row">
                <span class="{t1_cls}">T1 {item['t1']:.2f} {'(HIT)' if item['t1_hit'] else ''}</span>
                <span class="{t2_cls}">T2 {item['t2']:.2f} {'(HIT)' if item['t2_hit'] else ''}</span>
                <span class="{t3_cls}">T3 {item['t3']:.2f} {'(HIT)' if item['t3_hit'] else ''}</span>
                <span class="{sl_cls}">SL {item['sl']:.2f} {'(SL HIT)' if item['sl_hit'] else ''}</span>
            </div>
            <div class="box-why">{item['why']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_split_row(title: str, sell_list: list, buy_list: list):
    st.subheader(title)
    c_left, c_div, c_right = st.columns([10, 0.2, 10])

    with c_left:
        for item in sell_list:
            render_side_box(item)

    with c_div:
        st.markdown(
            '<div style="border-left: 2px solid #574834; min-height: 140px; height: 100%; margin: 0 auto;"></div>',
            unsafe_allow_html=True,
        )

    with c_right:
        for item in buy_list:
            render_side_box(item)


# Sidebar Controls
st.sidebar.header("Scanner Controls")
refresh_sec = st.sidebar.slider("Auto-Refresh (Seconds)", min_value=30, max_value=60, value=45, step=5)
auto_refresh = st.sidebar.checkbox("Auto-Refresh ON (30–60s)", value=True)
tf = st.sidebar.selectbox("Timeframe", ["15m", "5m", "30m"], index=0)
period_map = {"5m": "5d", "15m": "10d", "30m": "15d"}

if st.sidebar.button("Refresh Now"):
    st.cache_data.clear()

st.title("⚡ ARVANO Split Scanner (SELL Left | BUY Right)")
st.caption(f"Auto-refresh: {refresh_sec}s | Left = SELL / PUT | Right = BUY / CALL | Order: F&O → Top 100 NSE Stocks → Gold & Silver")

# 1. F&O INDICES (Nifty 50, Bank Nifty, Sensex)
fno_sell, fno_buy = [], []
for idx_name, cfg in FNO_INDICES.items():
    df_i = fetch_candles(cfg["ticker"], period=period_map[tf], interval=tf)
    if not df_i.empty:
        sig_i = get_active_move(df_i, idx_name, strike_step=cfg["step"])
        if sig_i:
            (fno_sell if sig_i["side"] == "SELL" else fno_buy).append(sig_i)

render_split_row("1. F&O (Nifty 50 • Bank Nifty • Sensex)", fno_sell, fno_buy)
st.markdown("---")

# 2. TOP 100 NSE STOCKS (Only Active Chalne Wale Movers)
stk_sell, stk_buy = [], []
prog = st.progress(0, text="Scanning Top 100 NSE stocks...")
for i, sym in enumerate(TOP_100_NSE):
    df_s = fetch_candles(sym, period=period_map[tf], interval=tf)
    if not df_s.empty:
        s_name = sym.replace(".NS", "")
        sig_s = get_active_move(df_s, s_name, strike_step=None)
        if sig_s:
            (stk_sell if sig_s["side"] == "SELL" else stk_buy).append(sig_s)
    prog.progress((i + 1) / len(TOP_100_NSE), text=f"Scanning Top 100 NSE ({i + 1}/{len(TOP_100_NSE)})...")
prog.empty()

stk_sell.sort(key=lambda x: x["score"], reverse=True)
stk_buy.sort(key=lambda x: x["score"], reverse=True)

render_split_row("2. Active NSE Stocks (Filtered from Top 100)", stk_sell, stk_buy)
st.markdown("---")

# 3. GOLD & SILVER
gs_sell, gs_buy = [], []
for g_name, g_ticker in GOLD_SILVER.items():
    df_g = fetch_candles(g_ticker, period=period_map[tf], interval=tf)
    if not df_g.empty:
        sig_g = get_active_move(df_g, g_name, strike_step=None)
        if sig_g:
            (gs_sell if sig_g["side"] == "SELL" else gs_buy).append(sig_g)

render_split_row("3. Gold & Silver", gs_sell, gs_buy)

if auto_refresh:
    time.sleep(refresh_sec)
    st.rerun()
