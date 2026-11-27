import time
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="ARVANO Single-Screen BUY | SELL Scanner",
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
    .col-buy-head {
        background: rgba(34, 197, 94, 0.16);
        border: 1px solid #22c55e;
        border-radius: 10px;
        padding: 10px 14px;
        font-size: 1.1rem;
        font-weight: 800;
        color: #4ade80;
        text-align: center;
        margin-bottom: 12px;
    }
    .col-sell-head {
        background: rgba(239, 68, 68, 0.16);
        border: 1px solid #ef4444;
        border-radius: 10px;
        padding: 10px 14px;
        font-size: 1.1rem;
        font-weight: 800;
        color: #f87171;
        text-align: center;
        margin-bottom: 12px;
    }
    .item-buy {
        background: #121b16;
        border: 1px solid #264734;
        border-left: 5px solid #22c55e;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }
    .item-sell {
        background: #1c1315;
        border: 1px solid #4c272d;
        border-left: 5px solid #ef4444;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }
    .row-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 6px;
    }
    .item-name {
        font-size: 1.02rem;
        font-weight: 800;
        color: #fff8ea;
    }
    .hit-yes {
        background: #16a34a;
        color: #ffffff;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.80rem;
        font-weight: 800;
    }
    .hit-sl {
        background: #dc2626;
        color: #ffffff;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.80rem;
        font-weight: 800;
    }
    .hit-no {
        background: rgba(255, 255, 255, 0.08);
        color: #e5dccb;
        border: 1px solid rgba(255, 255, 255, 0.18);
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.80rem;
        font-weight: 700;
    }
    .item-nums {
        font-size: 0.90rem;
        color: #f3e6cc;
        line-height: 1.45;
        margin-bottom: 5px;
    }
    .item-reason {
        font-size: 0.82rem;
        color: #cfc4b0;
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


def strike_choice(price: float, step: int, side: str) -> str:
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

    d["ema10"] = close.ewm(span=10, adjust=False).mean()
    d["ema50"] = close.ewm(span=50, adjust=False).mean()

    tp = (high + low + close) / 3.0
    if vol.sum() > 0:
        day_key = d.index.date
        pv_cum = (tp * vol).groupby(day_key).cumsum()
        v_cum = vol.groupby(day_key).cumsum().replace(0, np.nan)
        d["vwap"] = (pv_cum / v_cum).ffill().fillna(close.ewm(span=24, adjust=False).mean())
    else:
        d["vwap"] = close.ewm(span=24, adjust=False).mean()

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

    d["res20"] = high.shift(1).rolling(20).max()
    d["sup20"] = low.shift(1).rolling(20).min()
    d["hh10"] = high.shift(1).rolling(10).max()
    d["ll10"] = low.shift(1).rolling(10).min()

    return d.dropna(subset=["ema50", "atr14", "res20", "sup20", "hh10", "ll10"])


def hit_status_label(d: pd.DataFrame, start_pos: int, side: str, sl: float, t1: float, t2: float, t3: float) -> tuple[str, str]:
    sub = d.iloc[start_pos:]
    if sub.empty:
        sub = d.tail(1)
    max_h = float(sub["High"].max())
    min_l = float(sub["Low"].min())
    last_c = float(d["Close"].iloc[-1])

    if side == "BUY":
        if max_h >= t3 or last_c >= t3:
            return "T3 HIT (TARGET HIT)", "hit-yes"
        if max_h >= t2 or last_c >= t2:
            return "T2 HIT (TARGET HIT)", "hit-yes"
        if max_h >= t1 or last_c >= t1:
            return "T1 HIT (TARGET HIT)", "hit-yes"
        if min_l <= sl or last_c <= sl:
            return "SL HIT", "hit-sl"
        return "TARGET NOT HIT YET (LIVE)", "hit-no"

    if min_l <= t3 or last_c <= t3:
        return "T3 HIT (TARGET HIT)", "hit-yes"
    if min_l <= t2 or last_c <= t2:
        return "T2 HIT (TARGET HIT)", "hit-yes"
    if min_l <= t1 or last_c <= t1:
        return "T1 HIT (TARGET HIT)", "hit-yes"
    if max_h >= sl or last_c >= sl:
        return "SL HIT", "hit-sl"
    return "TARGET NOT HIT YET (LIVE)", "hit-no"


def eval_setup(d: pd.DataFrame, label: str, strike_step: int | None = None, is_index: bool = False) -> dict | None:
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
        call_name = strike_choice(price, strike_step, "BUY") if strike_step else "BUY"
        entry = price
        sl = max(0.0, entry - 2.0 * atr)
        t1 = entry + 1.5 * atr
        t2 = entry + 2.8 * atr
        t3 = entry + 4.2 * atr
        reason = f"Res/HH breakout | >50 EMA ({ema50:.2f}) & VWAP ({vwap:.2f}) | RSI {rsi:.1f} | ADX {adx:.1f}"
    elif sell_ok:
        side = "SELL"
        call_name = strike_choice(price, strike_step, "SELL") if strike_step else "SELL"
        entry = price
        sl = entry + 2.0 * atr
        t1 = max(0.0, entry - 1.5 * atr)
        t2 = max(0.0, entry - 2.8 * atr)
        t3 = max(0.0, entry - 4.2 * atr)
        reason = f"Sup/LL breakdown | <50 EMA ({ema50:.2f}) & VWAP ({vwap:.2f}) | RSI {rsi:.1f} | ADX {adx:.1f}"
    else:
        return None

    lock_key = f"single_lock_{label}"
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
    status_text, status_cls = hit_status_label(
        d=d,
        start_pos=locked["pos"],
        side=side,
        sl=locked["sl"],
        t1=locked["t1"],
        t2=locked["t2"],
        t3=locked["t3"],
    )

    return {
        "label": label,
        "is_index": is_index,
        "side": side,
        "call_name": call_name,
        "cmp": round(price, 2),
        "entry": locked["entry"],
        "sl": locked["sl"],
        "t1": locked["t1"],
        "t2": locked["t2"],
        "t3": locked["t3"],
        "reason": reason,
        "status_text": status_text,
        "status_cls": status_cls,
        "score": (1000.0 if is_index else 0.0) + (atr_pct * 2.0) + (adx * 0.5),
    }


@st.cache_data(ttl=25, show_spinner=False)
def get_df(ticker: str, period: str = "10d", interval: str = "15m") -> pd.DataFrame:
    try:
        raw = yf.download(ticker, period=period, interval=interval, progress=False, threads=False)
        if raw is None or raw.empty:
            return pd.DataFrame()
        return add_indicators(raw)
    except Exception:
        return pd.DataFrame()


def render_row_card(item: dict):
    is_buy = item["side"] == "BUY"
    box_cls = "item-buy" if is_buy else "item-sell"
    title_txt = f"{item['label']} ({item['call_name']})" if item["is_index"] else f"{item['label']} — {item['call_name']}"

    st.markdown(
        f"""
        <div class="{box_cls}">
            <div class="row-top">
                <span class="item-name">{title_txt}</span>
                <span class="{item['status_cls']}">{item['status_text']}</span>
            </div>
            <div class="item-nums">
                <b>Entry:</b> {item['entry']:.2f} (CMP: {item['cmp']:.2f}) &nbsp;|&nbsp;
                <b>SL:</b> {item['sl']:.2f} &nbsp;|&nbsp;
                <b>T1:</b> {item['t1']:.2f} &nbsp;|&nbsp;
                <b>T2:</b> {item['t2']:.2f} &nbsp;|&nbsp;
                <b>T3:</b> {item['t3']:.2f}
            </div>
            <div class="item-reason">{item['reason']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.sidebar.header("Controls")
refresh_sec = st.sidebar.slider("Auto-Refresh (sec)", min_value=30, max_value=60, value=30, step=5)
auto_refresh = st.sidebar.checkbox("Auto-Refresh ON", value=True)
tf = st.sidebar.selectbox("Timeframe", ["15m", "30m"], index=0)
period_map = {"15m": "10d", "30m": "15d"}

if st.sidebar.button("Refresh Now"):
    st.cache_data.clear()

st.title("🎯 ARVANO Single-Screen Scanner — BUY Left | SELL Right (No Charts)")
st.caption(f"Refresh: {refresh_sec}s | Left = BUY Only (Indices CE + BUY Stocks) | Right = SELL Only (Indices PE + SELL Stocks)")

buy_items = []
sell_items = []

# 1. Indices (Nifty 50, Bank Nifty, Sensex) with CE / PE strike suggestion
for idx_name, cfg in INDICES.items():
    df_i = get_df(cfg["ticker"], period=period_map[tf], interval=tf)
    if not df_i.empty:
        sig_i = eval_setup(df_i, idx_name, strike_step=cfg["step"], is_index=True)
        if sig_i:
            (buy_items if sig_i["side"] == "BUY" else sell_items).append(sig_i)

# 2. Top 100 NSE Stocks (only active BUY/SELL setups)
prog = st.progress(0, text="Scanning Top 100 NSE stocks...")
for idx, sym in enumerate(TOP_100_NSE):
    df_s = get_df(sym, period=period_map[tf], interval=tf)
    if not df_s.empty:
        s_name = sym.replace(".NS", "")
        sig_s = eval_setup(df_s, s_name, strike_step=None, is_index=False)
        if sig_s:
            (buy_items if sig_s["side"] == "BUY" else sell_items).append(sig_s)
    prog.progress((idx + 1) / len(TOP_100_NSE), text=f"Scanning Top 100 NSE ({idx + 1}/{len(TOP_100_NSE)})...")
prog.empty()

buy_items.sort(key=lambda x: x["score"], reverse=True)
sell_items.sort(key=lambda x: x["score"], reverse=True)

# Single Screen Side-by-Side: Left BUY ONLY | Right SELL ONLY
col_left, col_right = st.columns(2, gap="large")

with col_left:
    st.markdown('<div class="col-buy-head">LEFT SIDE — BUY ONLY (INDEX CE + BUY STOCKS)</div>', unsafe_allow_html=True)
    if buy_items:
        for b in buy_items:
            render_row_card(b)
    else:
        st.info("Abhi koi BUY setup criteria match nahi kar raha.")

with col_right:
    st.markdown('<div class="col-sell-head">RIGHT SIDE — SELL ONLY (INDEX PE + SELL STOCKS)</div>', unsafe_allow_html=True)
    if sell_items:
        for s in sell_items:
            render_row_card(s)
    else:
        st.info("Abhi koi SELL setup criteria match nahi kar raha.")

if auto_refresh:
    time.sleep(refresh_sec)
    st.rerun()
