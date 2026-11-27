import time
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="ARVANO F&O + Active Stocks Scanner",
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
    .fno-card {
        background: linear-gradient(145deg, #151419 0%, #1d1914 100%);
        border: 1px solid #3d3325;
        border-radius: 12px;
        padding: 15px 18px;
        margin-bottom: 12px;
    }
    .fno-buy {
        border-left: 6px solid #22c55e;
    }
    .fno-sell {
        border-left: 6px solid #ef4444;
    }
    .fno-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 8px;
    }
    .fno-title {
        font-size: 1.08rem;
        font-weight: 800;
        color: #fff8eb;
    }
    .pill-ce {
        background: rgba(34, 197, 94, 0.22);
        color: #4ade80;
        border: 1px solid #22c55e;
        padding: 3px 11px;
        border-radius: 999px;
        font-size: 0.80rem;
        font-weight: 800;
    }
    .pill-pe {
        background: rgba(239, 68, 68, 0.22);
        color: #f87171;
        border: 1px solid #ef4444;
        padding: 3px 11px;
        border-radius: 999px;
        font-size: 0.80rem;
        font-weight: 800;
    }
    .lvl-text {
        font-size: 0.94rem;
        color: #f3e6cc;
        margin-bottom: 8px;
        line-height: 1.5;
    }
    .status-line {
        display: flex;
        flex-wrap: wrap;
        gap: 7px;
        margin-bottom: 8px;
    }
    .s-box {
        padding: 4px 10px;
        border-radius: 7px;
        font-size: 0.80rem;
        font-weight: 700;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.14);
        color: #ebe2d2;
    }
    .s-green {
        background: rgba(34, 197, 94, 0.24);
        border: 1px solid #22c55e;
        color: #4ade80;
    }
    .s-red {
        background: rgba(239, 68, 68, 0.25);
        border: 1px solid #ef4444;
        color: #f87171;
    }
    .why-note {
        font-size: 0.86rem;
        color: #e6ddcc;
        background: rgba(255, 255, 255, 0.035);
        border-radius: 8px;
        padding: 8px 11px;
    }
    .stock-row {
        background: #141317;
        border: 1px solid #2d271e;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
    }
    .stock-row-buy {
        border-left: 5px solid #22c55e;
    }
    .stock-row-sell {
        border-left: 5px solid #ef4444;
    }
    .stock-main {
        font-size: 0.93rem;
        color: #f6efe2;
        line-height: 1.45;
    }
    .stock-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        align-items: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

FNO_LIST = {
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


def get_strike(price: float, step: int, side: str) -> int:
    atm = int(round(price / step) * step)
    return atm + step if side == "BUY" else atm - step


def enrich_15m(df: pd.DataFrame) -> pd.DataFrame:
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

    # 1. Customized EMAs (10 EMA & 50 EMA)
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

    # Support / Resistance & Pattern structure
    d["res20"] = high.shift(1).rolling(20).max()
    d["sup20"] = low.shift(1).rolling(20).min()
    d["hh10"] = high.shift(1).rolling(10).max()
    d["ll10"] = low.shift(1).rolling(10).min()

    return d.dropna(subset=["ema50", "atr14", "res20", "sup20", "hh10", "ll10"])


def evaluate_post_signal_hits(d: pd.DataFrame, signal_idx_pos: int, side: str, sl: float, t1: float, t2: float, t3: float) -> dict:
    """Checks ONLY candles AFTER the signal formed so pre-signal moves don't falsely mark SL HIT."""
    after_df = d.iloc[signal_idx_pos:]
    if after_df.empty:
        after_df = d.tail(1)

    max_high = float(after_df["High"].max())
    min_low = float(after_df["Low"].min())
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


def scan_movement(d: pd.DataFrame, name: str, strike_step: int | None = None) -> dict | None:
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

    buy_ok = (
        (price > ema50)
        and (ema10 >= ema50 * 0.999)
        and (price > vwap)
        and (rsi >= 55)
        and (adx >= 20)
        and (
            (price > res20)
            or (price > hh10)
            or (abs(price - res20) / max(price, 1e-6) <= 0.004)
            or (abs(min_low - sup20) / max(sup20, 1e-6) <= 0.004 and price > ema10)
        )
    )

    sell_ok = (
        (price < ema50)
        and (ema10 <= ema50 * 1.001)
        and (price < vwap)
        and (rsi <= 45)
        and (adx >= 20)
        and (
            (price < sup20)
            or (price < ll10)
            or (abs(price - sup20) / max(price, 1e-6) <= 0.004)
            or (abs(max_high - res20) / max(res20, 1e-6) <= 0.004 and price < ema10)
        )
    )

    if buy_ok:
        side = "BUY"
        trade_call = f"BUY {get_strike(price, strike_step, 'BUY')} CE" if strike_step else "BUY"
        entry = price
        sl = max(0.0, entry - 2.0 * atr)
        t1 = entry + 1.5 * atr
        t2 = entry + 2.8 * atr
        t3 = entry + 4.2 * atr
        pat = (
            f"Res {res20:.2f} Break"
            if price > res20
            else ("Double Bottom" if abs(min_low - sup20) / max(sup20, 1e-6) <= 0.004 else "HH Breakout")
        )
        why = f"{pat} | >50 EMA ({ema50:.2f}) & VWAP ({vwap:.2f}) | RSI {rsi:.1f} | ADX {adx:.1f}"
    elif sell_ok:
        side = "SELL"
        trade_call = f"BUY {get_strike(price, strike_step, 'SELL')} PE" if strike_step else "SELL"
        entry = price
        sl = entry + 2.0 * atr
        t1 = max(0.0, entry - 1.5 * atr)
        t2 = max(0.0, entry - 2.8 * atr)
        t3 = max(0.0, entry - 4.2 * atr)
        pat = (
            f"Sup {sup20:.2f} Break"
            if price < sup20
            else ("Double Top" if abs(max_high - res20) / max(res20, 1e-6) <= 0.004 else "LL Breakdown")
        )
        why = f"{pat} | <50 EMA ({ema50:.2f}) & VWAP ({vwap:.2f}) | RSI {rsi:.1f} | ADX {adx:.1f}"
    else:
        return None

    lock_key = f"msg_lock_{name}"
    if lock_key not in st.session_state or st.session_state[lock_key]["side"] != side:
        st.session_state[lock_key] = {
            "side": side,
            "entry": round(entry, 2),
            "sl": round(sl, 2),
            "t1": round(t1, 2),
            "t2": round(t2, 2),
            "t3": round(t3, 2),
            "bar_pos": len(d) - 1,
        }

    locked = st.session_state[lock_key]
    hits = evaluate_post_signal_hits(
        d=d,
        signal_idx_pos=locked["bar_pos"],
        side=side,
        sl=locked["sl"],
        t1=locked["t1"],
        t2=locked["t2"],
        t3=locked["t3"],
    )

    if hits["t3_hit"]:
        hit_summary = "T3 HIT"
    elif hits["t2_hit"]:
        hit_summary = "T2 HIT"
    elif hits["t1_hit"]:
        hit_summary = "T1 HIT"
    elif hits["sl_hit"]:
        hit_summary = "SL HIT"
    else:
        hit_summary = "SIGNAL LIVE (WAITING)"

    return {
        "name": name,
        "side": side,
        "trade_call": trade_call,
        "cmp": round(price, 2),
        "entry": locked["entry"],
        "sl": locked["sl"],
        "t1": locked["t1"],
        "t2": locked["t2"],
        "t3": locked["t3"],
        "atr_pct": round(atr_pct, 2),
        "why": why,
        "score": (atr_pct * 2.2) + (adx * 0.6),
        "hit_summary": hit_summary,
        **hits,
    }


@st.cache_data(ttl=25, show_spinner=False)
def fetch_15m(ticker: str, period: str = "10d", interval: str = "15m") -> pd.DataFrame:
    try:
        raw = yf.download(ticker, period=period, interval=interval, progress=False, threads=False)
        if raw is None or raw.empty:
            return pd.DataFrame()
        return enrich_15m(raw)
    except Exception:
        return pd.DataFrame()


def render_fno_box(item: dict):
    is_buy = item["side"] == "BUY"
    card_cls = "fno-card fno-buy" if is_buy else "fno-card fno-sell"
    pill_cls = "pill-ce" if is_buy else "pill-pe"

    t1_cls = "s-box s-green" if item["t1_hit"] else "s-box"
    t2_cls = "s-box s-green" if item["t2_hit"] else "s-box"
    t3_cls = "s-box s-green" if item["t3_hit"] else "s-box"
    sl_cls = "s-box s-red" if item["sl_hit"] else "s-box"

    st.markdown(
        f"""
        <div class="{card_cls}">
            <div class="fno-top">
                <div class="fno-title">{item['name']} — {item['trade_call']}</div>
                <span class="{pill_cls}">{item['hit_summary']}</span>
            </div>
            <div class="lvl-text">
                <b>Price / Entry:</b> {item['entry']:.2f} (CMP: {item['cmp']:.2f}) &nbsp;|&nbsp;
                <b>SL:</b> {item['sl']:.2f} &nbsp;|&nbsp;
                <b>T1:</b> {item['t1']:.2f} &nbsp;|&nbsp;
                <b>T2:</b> {item['t2']:.2f} &nbsp;|&nbsp;
                <b>T3:</b> {item['t3']:.2f}
            </div>
            <div class="status-line">
                <span class="{t1_cls}">T1 {item['t1']:.2f} {'✓ HIT' if item['t1_hit'] else ''}</span>
                <span class="{t2_cls}">T2 {item['t2']:.2f} {'✓ HIT' if item['t2_hit'] else ''}</span>
                <span class="{t3_cls}">T3 {item['t3']:.2f} {'✓ HIT' if item['t3_hit'] else ''}</span>
                <span class="{sl_cls}">SL {item['sl']:.2f} {'✕ SL HIT' if item['sl_hit'] else ''}</span>
            </div>
            <div class="why-note"><b>Kyun Chal Raha Hai:</b> {item['why']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_single_page_stock_line(item: dict):
    is_buy = item["side"] == "BUY"
    row_cls = "stock-row stock-row-buy" if is_buy else "stock-row stock-row-sell"
    side_cls = "s-box s-green" if is_buy else "s-box s-red"

    t1_cls = "s-box s-green" if item["t1_hit"] else "s-box"
    t2_cls = "s-box s-green" if item["t2_hit"] else "s-box"
    t3_cls = "s-box s-green" if item["t3_hit"] else "s-box"
    sl_cls = "s-box s-red" if item["sl_hit"] else "s-box"

    if item["t3_hit"]:
        outcome_badge = '<span class="s-box s-green">T3 TARGET HIT</span>'
    elif item["t2_hit"]:
        outcome_badge = '<span class="s-box s-green">T2 TARGET HIT</span>'
    elif item["t1_hit"]:
        outcome_badge = '<span class="s-box s-green">T1 TARGET HIT</span>'
    elif item["sl_hit"]:
        outcome_badge = '<span class="s-box s-red">SL HIT</span>'
    else:
        outcome_badge = '<span class="s-box">ACTIVE</span>'

    st.markdown(
        f"""
        <div class="{row_cls}">
            <div class="stock-main">
                <b>{item['name']}</b> &nbsp;
                <span class="{side_cls}">{item['side']}</span> &nbsp;
                <b>Price:</b> {item['entry']:.2f} &nbsp;|&nbsp;
                <b>T1:</b> {item['t1']:.2f} &nbsp;|&nbsp;
                <b>T2:</b> {item['t2']:.2f} &nbsp;|&nbsp;
                <b>T3:</b> {item['t3']:.2f} &nbsp;|&nbsp;
                <b>SL:</b> {item['sl']:.2f}
            </div>
            <div class="stock-badges">
                <span class="{t1_cls}">T1 {'HIT' if item['t1_hit'] else '—'}</span>
                <span class="{t2_cls}">T2 {'HIT' if item['t2_hit'] else '—'}</span>
                <span class="{t3_cls}">T3 {'HIT' if item['t3_hit'] else '—'}</span>
                <span class="{sl_cls}">SL {'HIT' if item['sl_hit'] else '—'}</span>
                {outcome_badge}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Sidebar Controls
st.sidebar.header("Live Scanner Controls")
refresh_sec = st.sidebar.slider("Auto-Refresh (Seconds)", min_value=30, max_value=60, value=45, step=5)
auto_refresh = st.sidebar.checkbox("Auto-Refresh ON (30–60s)", value=True)
tf = st.sidebar.selectbox("Timeframe", ["15m", "30m"], index=0)
period_map = {"15m": "10d", "30m": "15d"}

if st.sidebar.button("Refresh Now"):
    st.cache_data.clear()

st.title("⚡ ARVANO F&O + Active Stocks Scanner (No Charts)")
st.caption(f"Auto-refresh: {refresh_sec}s | F&O first (Nifty 50, Bank Nifty, Sensex) → Active Stocks on single page | Only real movements shown")

# 1. F&O SECTION FIRST (Nifty 50, Bank Nifty, Sensex)
st.subheader("1. F&O Calls / Puts (Nifty 50 • Bank Nifty • Sensex)")
fno_signals = []
for idx_name, cfg in FNO_LIST.items():
    df_i = fetch_15m(cfg["ticker"], period=period_map[tf], interval=tf)
    if not df_i.empty:
        sig_i = scan_movement(df_i, idx_name, strike_step=cfg["step"])
        if sig_i:
            fno_signals.append(sig_i)

if fno_signals:
    for f_item in fno_signals:
        render_fno_box(f_item)
else:
    st.info("Abhi Nifty 50 / Bank Nifty / Sensex mein koi naya clear CALL/PUT movement lock nahi hua hai.")

st.markdown("---")

# 2. SINGLE-PAGE ACTIVE STOCKS (Filtered from Top 100 NSE)
st.subheader("2. Active Stocks — Single Page (Stock • BUY/SELL • Price • T1 • T2 • T3 • SL • Hit Status)")
active_stocks = []
prog = st.progress(0, text="Scanning Top 100 NSE for active movements...")
for i, sym in enumerate(TOP_100_NSE):
    df_s = fetch_15m(sym, period=period_map[tf], interval=tf)
    if not df_s.empty:
        s_name = sym.replace(".NS", "")
        sig_s = scan_movement(df_s, s_name, strike_step=None)
        if sig_s:
            active_stocks.append(sig_s)
    prog.progress((i + 1) / len(TOP_100_NSE), text=f"Scanning Top 100 NSE ({i + 1}/{len(TOP_100_NSE)})...")
prog.empty()

active_stocks.sort(key=lambda x: x["score"], reverse=True)

if active_stocks:
    for s_item in active_stocks:
        render_single_page_stock_line(s_item)
else:
    st.info("Abhi Top 100 NSE mein koi strong BUY/SELL movement setup nahi bana hai.")

if auto_refresh:
    time.sleep(refresh_sec)
    st.rerun()
