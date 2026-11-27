import time
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="ARVANO Single-Screen F&O + Active Stocks",
    page_icon="🎯",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b0b0e;
        color: #f6f1e7;
    }
    .box-fno {
        background: linear-gradient(145deg, #151419 0%, #1d1914 100%);
        border: 1px solid #3d3325;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 12px;
    }
    .box-buy {
        border-left: 6px solid #22c55e;
    }
    .box-sell {
        border-left: 6px solid #ef4444;
    }
    .row-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 6px;
    }
    .title-txt {
        font-size: 1.05rem;
        font-weight: 800;
        color: #fff8ea;
    }
    .badge-buy {
        background: rgba(34, 197, 94, 0.22);
        color: #4ade80;
        border: 1px solid #22c55e;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 800;
    }
    .badge-sell {
        background: rgba(239, 68, 68, 0.22);
        color: #f87171;
        border: 1px solid #ef4444;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 800;
    }
    .hit-yes {
        background: #16a34a;
        color: #ffffff;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 800;
    }
    .hit-sl {
        background: #dc2626;
        color: #ffffff;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 800;
    }
    .hit-live {
        background: rgba(255, 255, 255, 0.08);
        color: #e8decb;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 700;
    }
    .lvl-txt {
        font-size: 0.92rem;
        color: #f3e6cc;
        line-height: 1.45;
        margin-bottom: 6px;
    }
    .why-txt {
        font-size: 0.84rem;
        color: #d6cbb7;
        background: rgba(255, 255, 255, 0.035);
        border-radius: 8px;
        padding: 8px 10px;
    }
    .stock-card {
        background: #141318;
        border: 1px solid #2e271e;
        border-radius: 10px;
        padding: 12px 15px;
        margin-bottom: 9px;
    }
    .names-banner {
        background: rgba(212, 163, 89, 0.1);
        border: 1px solid rgba(212, 163, 89, 0.4);
        border-radius: 10px;
        padding: 11px 14px;
        margin-bottom: 14px;
        font-size: 0.95rem;
        color: #fff3d6;
        line-height: 1.5;
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


def pick_strike(price: float, step: int, side: str) -> str:
    atm = int(round(price / step) * step)
    return f"BUY {atm + step} CE" if side == "BUY" else f"BUY {atm - step} PE"


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

    # Support / Resistance & Pattern Break Levels
    d["res20"] = high.shift(1).rolling(20).max()
    d["sup20"] = low.shift(1).rolling(20).min()
    d["hh10"] = high.shift(1).rolling(10).max()
    d["ll10"] = low.shift(1).rolling(10).min()

    return d.dropna(subset=["ema50", "atr14", "res20", "sup20", "hh10", "ll10"])


def check_hit_status(d: pd.DataFrame, start_pos: int, side: str, sl: float, t1: float, t2: float, t3: float) -> tuple[str, str]:
    sub = d.iloc[start_pos:]
    if sub.empty:
        sub = d.tail(1)
    max_h = float(sub["High"].max())
    min_l = float(sub["Low"].min())
    last_c = float(d["Close"].iloc[-1])

    if side == "BUY":
        if max_h >= t3 or last_c >= t3:
            return "T3 HIT", "hit-yes"
        if max_h >= t2 or last_c >= t2:
            return "T2 HIT", "hit-yes"
        if max_h >= t1 or last_c >= t1:
            return "T1 HIT", "hit-yes"
        if min_l <= sl or last_c <= sl:
            return "SL HIT", "hit-sl"
        return "TARGET NOT HIT (LIVE)", "hit-live"

    if min_l <= t3 or last_c <= t3:
        return "T3 HIT", "hit-yes"
    if min_l <= t2 or last_c <= t2:
        return "T2 HIT", "hit-yes"
    if min_l <= t1 or last_c <= t1:
        return "T1 HIT", "hit-yes"
    if max_h >= sl or last_c >= sl:
        return "SL HIT", "hit-sl"
    return "TARGET NOT HIT (LIVE)", "hit-live"


def evaluate_trade(d: pd.DataFrame, name: str, strike_step: int | None = None, is_index: bool = False) -> dict | None:
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

    buy_ok = (
        (price > ema50)
        and (ema10 >= ema50 * 0.999)
        and (price > vwap)
        and (rsi >= 55)
        and (adx >= 20)
        and ((price > res20) or (price > hh10) or (abs(price - res20) / max(price, 1e-6) <= 0.004))
    )

    sell_ok = (
        (price < ema50)
        and (ema10 <= ema50 * 1.001)
        and (price < vwap)
        and (rsi <= 45)
        and (adx >= 20)
        and ((price < sup20) or (price < ll10) or (abs(price - sup20) / max(price, 1e-6) <= 0.004))
    )

    if buy_ok:
        side = "BUY"
        take_what = pick_strike(price, strike_step, "BUY") if strike_step else "BUY"
        entry = price
        sl = max(0.0, entry - 2.0 * atr)
        t1 = entry + 1.5 * atr
        t2 = entry + 2.8 * atr
        t3 = entry + 4.2 * atr
        reason = f"Res {res20:.2f} / HH {hh10:.2f} break | >50 EMA ({ema50:.2f}) & VWAP ({vwap:.2f}) | RSI {rsi:.1f} | ADX {adx:.1f}"
    elif sell_ok:
        side = "SELL"
        take_what = pick_strike(price, strike_step, "SELL") if strike_step else "SELL"
        entry = price
        sl = entry + 2.0 * atr
        t1 = max(0.0, entry - 1.5 * atr)
        t2 = max(0.0, entry - 2.8 * atr)
        t3 = max(0.0, entry - 4.2 * atr)
        reason = f"Sup {sup20:.2f} / LL {ll10:.2f} break | <50 EMA ({ema50:.2f}) & VWAP ({vwap:.2f}) | RSI {rsi:.1f} | ADX {adx:.1f}"
    else:
        return None

    lock_key = f"unified_lock_{name}"
    if lock_key not in st.session_state or st.session_state[lock_key]["side"] != side:
        st.session_state[lock_key] = {
            "side": side,
            "entry": round(entry, 2),
            "sl": round(sl, 2),
            "t1": round(t1, 2),
            "t2": round(t2, 2),
            "t3": round(t3, 2),
            "pos": len(d) - 1,
        }

    locked = st.session_state[lock_key]
    hit_txt, hit_cls = check_hit_status(
        d=d,
        start_pos=locked["pos"],
        side=side,
        sl=locked["sl"],
        t1=locked["t1"],
        t2=locked["t2"],
        t3=locked["t3"],
    )

    return {
        "name": name,
        "is_index": is_index,
        "side": side,
        "take_what": take_what,
        "cmp": round(price, 2),
        "entry": locked["entry"],
        "sl": locked["sl"],
        "t1": locked["t1"],
        "t2": locked["t2"],
        "t3": locked["t3"],
        "reason": reason,
        "hit_txt": hit_txt,
        "hit_cls": hit_cls,
        "score": (atr_pct * 2.2) + (adx * 0.6),
    }


@st.cache_data(ttl=25, show_spinner=False)
def load_15m(ticker: str, period: str = "10d", interval: str = "15m") -> pd.DataFrame:
    try:
        raw = yf.download(ticker, period=period, interval=interval, progress=False, threads=False)
        if raw is None or raw.empty:
            return pd.DataFrame()
        return add_indicators(raw)
    except Exception:
        return pd.DataFrame()


def render_fno_item(item: dict):
    is_buy = item["side"] == "BUY"
    box_cls = f"box-fno {'box-buy' if is_buy else 'box-sell'}"
    side_cls = "badge-buy" if is_buy else "badge-sell"

    st.markdown(
        f"""
        <div class="{box_cls}">
            <div class="row-top">
                <span class="title-txt">{item['name']} → LENA HAI: {item['take_what']}</span>
                <span>
                    <span class="{side_cls}">{item['side']}</span> &nbsp;
                    <span class="{item['hit_cls']}">{item['hit_txt']}</span>
                </span>
            </div>
            <div class="lvl-txt">
                <b>Entry:</b> {item['entry']:.2f} (CMP: {item['cmp']:.2f}) &nbsp;|&nbsp;
                <b>SL:</b> {item['sl']:.2f} &nbsp;|&nbsp;
                <b>T1:</b> {item['t1']:.2f} &nbsp;|&nbsp;
                <b>T2:</b> {item['t2']:.2f} &nbsp;|&nbsp;
                <b>T3:</b> {item['t3']:.2f}
            </div>
            <div class="why-txt"><b>Kyun:</b> {item['reason']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stock_item(item: dict):
    is_buy = item["side"] == "BUY"
    card_cls = f"stock-card {'box-buy' if is_buy else 'box-sell'}"
    side_cls = "badge-buy" if is_buy else "badge-sell"

    st.markdown(
        f"""
        <div class="{card_cls}">
            <div class="row-top">
                <span class="title-txt">{item['name']}</span>
                <span>
                    <span class="{side_cls}">{item['side']}</span> &nbsp;
                    <span class="{item['hit_cls']}">{item['hit_txt']}</span>
                </span>
            </div>
            <div class="lvl-txt">
                <b>Entry:</b> {item['entry']:.2f} (CMP: {item['cmp']:.2f}) &nbsp;|&nbsp;
                <b>SL:</b> {item['sl']:.2f} &nbsp;|&nbsp;
                <b>T1:</b> {item['t1']:.2f} &nbsp;|&nbsp;
                <b>T2:</b> {item['t2']:.2f} &nbsp;|&nbsp;
                <b>T3:</b> {item['t3']:.2f}
            </div>
            <div class="why-txt"><b>Kyun:</b> {item['reason']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Sidebar Controls
st.sidebar.header("Scanner Controls")
refresh_sec = st.sidebar.slider("Auto-Refresh (sec)", min_value=30, max_value=60, value=30, step=5)
auto_refresh = st.sidebar.checkbox("Auto-Refresh ON", value=True)
tf = st.sidebar.selectbox("Timeframe", ["15m", "30m"], index=0)
period_map = {"15m": "10d", "30m": "15d"}

if st.sidebar.button("Refresh Now"):
    st.cache_data.clear()

st.title("🎯 ARVANO F&O + Active Stocks (Single Screen, No Charts)")
st.caption(f"Auto-refresh: {refresh_sec}s | 1. F&O (Nifty 50, Bank Nifty, Sensex) first | 2. Active BUY & SELL Stocks together")

# 1. F&O SECTION FIRST (Nifty 50, Bank Nifty, Sensex)
st.subheader("1. F&O Calls / Puts (Nifty 50 • Bank Nifty • Sensex)")
fno_active = []
for idx_name, cfg in FNO_INDICES.items():
    df_i = load_15m(cfg["ticker"], period=period_map[tf], interval=tf)
    if not df_i.empty:
        sig_i = evaluate_trade(df_i, idx_name, strike_step=cfg["step"], is_index=True)
        if sig_i:
            fno_active.append(sig_i)

if fno_active:
    for f in fno_active:
        render_fno_item(f)
else:
    st.info("Abhi F&O mein koi clear BUY/SELL breakout signal nahi aaya hai.")

st.markdown("---")

# 2. ACTIVE STOCKS TOGETHER (BUY & SELL combined, filtered from Top 100 NSE)
st.subheader("2. Active Stocks — BUY & SELL Together (Filtered from Top 100 NSE)")
active_stocks = []
prog = st.progress(0, text="Scanning Top 100 NSE stocks...")
for idx, sym in enumerate(TOP_100_NSE):
    df_s = load_15m(sym, period=period_map[tf], interval=tf)
    if not df_s.empty:
        s_name = sym.replace(".NS", "")
        sig_s = evaluate_trade(df_s, s_name, strike_step=None, is_index=False)
        if sig_s:
            active_stocks.append(sig_s)
    prog.progress((idx + 1) / len(TOP_100_NSE), text=f"Scanning Top 100 NSE ({idx + 1}/{len(TOP_100_NSE)})...")
prog.empty()

active_stocks.sort(key=lambda x: x["score"], reverse=True)

if active_stocks:
    names_joined = " • ".join([f"{x['name']} ({x['side']})" for x in active_stocks])
    st.markdown(
        f'<div class="names-banner"><b>Chalne Wale Active Stocks Ek Saath:</b> {names_joined}</div>',
        unsafe_allow_html=True,
    )
    for st_item in active_stocks:
        render_stock_item(st_item)
else:
    st.info("Abhi Top 100 NSE mein koi active BUY/SELL stock setup nahi bana hai.")

if auto_refresh:
    time.sleep(refresh_sec)
    st.rerun()
