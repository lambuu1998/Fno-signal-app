import time
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="ARVANO F&O + Active Stocks",
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
    .main-box {
        background: #141318;
        border: 1px solid #3d3325;
        border-radius: 12px;
        padding: 10px 10px 12px 10px;
        margin-bottom: 14px;
        overflow-x: auto;
    }
    .sec-hdr {
        font-size: 0.95rem;
        font-weight: 800;
        padding: 7px 10px;
        border-radius: 8px;
        margin: 6px 0 8px 0;
        letter-spacing: 0.3px;
    }
    .hdr-buy {
        background: rgba(34, 197, 94, 0.16);
        color: #4ade80;
        border-left: 4px solid #22c55e;
    }
    .hdr-sell {
        background: rgba(239, 68, 68, 0.16);
        color: #f87171;
        border-left: 4px solid #ef4444;
    }
    table.sig-tbl {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.80rem;
        white-space: nowrap;
    }
    table.sig-tbl th {
        background: #1e1b16;
        color: #e6c88a;
        font-weight: 800;
        text-align: left;
        padding: 7px 8px;
        border-bottom: 1px solid #3d3325;
        position: sticky;
        top: 0;
    }
    table.sig-tbl td {
        padding: 7px 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.07);
        color: #f6f1e7;
        font-weight: 600;
    }
    table.sig-tbl tr:last-child td {
        border-bottom: none;
    }
    .col-name {
        font-weight: 800;
        color: #fff8ea;
    }
    .col-t {
        color: #86efac;
        font-weight: 700;
    }
    .col-sl {
        color: #fca5a5;
        font-weight: 700;
    }
    .st-hit {
        background: #16a34a;
        color: #ffffff;
        padding: 2px 7px;
        border-radius: 5px;
        font-size: 0.72rem;
        font-weight: 800;
    }
    .st-sl {
        background: #dc2626;
        color: #ffffff;
        padding: 2px 7px;
        border-radius: 5px;
        font-size: 0.72rem;
        font-weight: 800;
    }
    .st-live {
        background: rgba(255, 255, 255, 0.1);
        color: #e8decb;
        padding: 2px 7px;
        border-radius: 5px;
        font-size: 0.72rem;
        font-weight: 700;
    }
    .empty-msg {
        font-size: 0.82rem;
        color: #b8ad99;
        padding: 6px 10px;
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
    return f"{atm + step} CE" if side == "BUY" else f"{atm - step} PE"


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
        d["vol_ma20"] = vol.rolling(20).mean().fillna(0.0)
    else:
        d["vwap"] = close.ewm(span=24, adjust=False).mean()
        d["vol_ma20"] = 0.0

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


def check_hit_status(
    d: pd.DataFrame, start_pos: int, side: str, sl: float, t1: float, t2: float, t3: float
) -> tuple[str, str]:
    sub = d.iloc[start_pos:]
    if sub.empty:
        sub = d.tail(1)
    max_h = float(sub["High"].max())
    min_l = float(sub["Low"].min())
    last_c = float(d["Close"].iloc[-1])

    if side == "BUY":
        if max_h >= t3 or last_c >= t3:
            return "T3 HIT", "st-hit"
        if max_h >= t2 or last_c >= t2:
            return "T2 HIT", "st-hit"
        if max_h >= t1 or last_c >= t1:
            return "T1 HIT", "st-hit"
        if min_l <= sl or last_c <= sl:
            return "SL HIT", "st-sl"
        return "LIVE", "st-live"

    if min_l <= t3 or last_c <= t3:
        return "T3 HIT", "st-hit"
    if min_l <= t2 or last_c <= t2:
        return "T2 HIT", "st-hit"
    if min_l <= t1 or last_c <= t1:
        return "T1 HIT", "st-hit"
    if max_h >= sl or last_c >= sl:
        return "SL HIT", "st-sl"
    return "LIVE", "st-live"


def evaluate_trade(
    d: pd.DataFrame, name: str, strike_step: int | None = None, is_index: bool = False
) -> dict | None:
    last = d.iloc[-1]
    prev = d.iloc[-2]
    price = float(last["Close"])
    prev_close = float(prev["Close"])
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

    vol_ok = True
    if not is_index and float(last["vol_ma20"]) > 0 and "Volume" in d.columns:
        vol_ok = float(last["Volume"]) >= float(last["vol_ma20"]) * 1.15

    # Strong momentum + actual breakout confirmation (sirf chalne wale setups)
    buy_ok = (
        (price > prev_close)
        and (price > ema10 > ema50)
        and (price > vwap)
        and (58 <= rsi <= 76)
        and (adx >= 23)
        and ((price > res20) or (price > hh10))
        and vol_ok
    )

    sell_ok = (
        (price < prev_close)
        and (price < ema10 < ema50)
        and (price < vwap)
        and (24 <= rsi <= 42)
        and (adx >= 23)
        and ((price < sup20) or (price < ll10))
        and vol_ok
    )

    if buy_ok:
        side = "BUY"
        label = f"{name} ({pick_strike(price, strike_step, 'BUY')})" if strike_step else name
        entry = price
        sl = max(0.0, entry - 1.8 * atr)
        t1 = entry + 1.4 * atr
        t2 = entry + 2.6 * atr
        t3 = entry + 3.8 * atr
    elif sell_ok:
        side = "SELL"
        label = f"{name} ({pick_strike(price, strike_step, 'SELL')})" if strike_step else name
        entry = price
        sl = entry + 1.8 * atr
        t1 = max(0.0, entry - 1.4 * atr)
        t2 = max(0.0, entry - 2.6 * atr)
        t3 = max(0.0, entry - 3.8 * atr)
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
        "label": label,
        "is_index": is_index,
        "side": side,
        "cmp": round(price, 2),
        "entry": locked["entry"],
        "sl": locked["sl"],
        "t1": locked["t1"],
        "t2": locked["t2"],
        "t3": locked["t3"],
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


def build_table_html(items: list[dict], col_title: str, entry_title: str) -> str:
    rows_html = ""
    for it in items:
        rows_html += (
            f"<tr>"
            f"<td class='col-name'>{it['label']}</td>"
            f"<td>{it['entry']:.2f}</td>"
            f"<td>{it['cmp']:.2f}</td>"
            f"<td class='col-t'>{it['t1']:.2f}</td>"
            f"<td class='col-t'>{it['t2']:.2f}</td>"
            f"<td class='col-t'>{it['t3']:.2f}</td>"
            f"<td class='col-sl'>{it['sl']:.2f}</td>"
            f"<td><span class='{it['hit_cls']}'>{it['hit_txt']}</span></td>"
            f"</tr>"
        )
    return f"""
    <table class="sig-tbl">
        <thead>
            <tr>
                <th>{col_title}</th>
                <th>{entry_title}</th>
                <th>CMP</th>
                <th>T1</th>
                <th>T2</th>
                <th>T3</th>
                <th>SL</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """


st.sidebar.header("Scanner Controls")
refresh_sec = st.sidebar.slider("Auto-Refresh (sec)", min_value=30, max_value=60, value=30, step=5)
auto_refresh = st.sidebar.checkbox("Auto-Refresh ON", value=True)
tf = st.sidebar.selectbox("Timeframe", ["15m", "30m"], index=0)
period_map = {"15m": "10d", "30m": "15d"}

if st.sidebar.button("Refresh Now"):
    st.cache_data.clear()

st.title("🎯 ARVANO F&O + Active Stocks")
st.caption(f"{tf} • Auto-Refresh {refresh_sec}s • Pehle BUY (Call) phir SELL (Put) — Single Box View")

# 1. F&O SINGLE BOX (NIFTY 50, BANK NIFTY, SENSEX)
fno_buy, fno_sell = [], []
for idx_name, cfg in FNO_INDICES.items():
    df_i = load_15m(cfg["ticker"], period=period_map[tf], interval=tf)
    if not df_i.empty:
        sig_i = evaluate_trade(df_i, idx_name, strike_step=cfg["step"], is_index=True)
        if sig_i:
            if sig_i["side"] == "BUY":
                fno_buy.append(sig_i)
            else:
                fno_sell.append(sig_i)

st.subheader("1. F&O (Nifty 50 • Bank Nifty • Sensex)")
fno_html = '<div class="main-box">'
fno_html += '<div class="sec-hdr hdr-buy">▲ F&O BUY (CALL SIDE)</div>'
if fno_buy:
    fno_html += build_table_html(fno_buy, "Index / Strike", "Buy At")
else:
    fno_html += '<div class="empty-msg">Abhi F&O BUY (CE) ka koi active setup nahi hai.</div>'

fno_html += '<div class="sec-hdr hdr-sell">▼ F&O SELL (PUT SIDE)</div>'
if fno_sell:
    fno_html += build_table_html(fno_sell, "Index / Strike", "Sell At")
else:
    fno_html += '<div class="empty-msg">Abhi F&O SELL (PE) ka koi active setup nahi hai.</div>'
fno_html += "</div>"
st.markdown(fno_html, unsafe_allow_html=True)

# 2. ACTIVE STOCKS SINGLE BOX (PEHLE BUY, NEECHE SELL)
stock_buy, stock_sell = [], []
prog = st.progress(0, text="Scanning Top 100 NSE...")
for idx, sym in enumerate(TOP_100_NSE):
    df_s = load_15m(sym, period=period_map[tf], interval=tf)
    if not df_s.empty:
        s_name = sym.replace(".NS", "")
        sig_s = evaluate_trade(df_s, s_name, strike_step=None, is_index=False)
        if sig_s:
            if sig_s["side"] == "BUY":
                stock_buy.append(sig_s)
            else:
                stock_sell.append(sig_s)
    prog.progress((idx + 1) / len(TOP_100_NSE), text=f"Scanning ({idx + 1}/{len(TOP_100_NSE)})...")
prog.empty()

stock_buy.sort(key=lambda x: x["score"], reverse=True)
stock_sell.sort(key=lambda x: x["score"], reverse=True)

st.subheader("2. Active Stocks (Pehle BUY • Neeche SELL)")
stk_html = '<div class="main-box">'
stk_html += f'<div class="sec-hdr hdr-buy">▲ BUY STOCKS — LENA HAI ({len(stock_buy)})</div>'
if stock_buy:
    stk_html += build_table_html(stock_buy, "Stock", "Buy At")
else:
    stk_html += '<div class="empty-msg">Abhi BUY side mein koi active stock nahi hai.</div>'

stk_html += f'<div class="sec-hdr hdr-sell">▼ SELL STOCKS — BECHNA HAI ({len(stock_sell)})</div>'
if stock_sell:
    stk_html += build_table_html(stock_sell, "Stock", "Sell At")
else:
    stk_html += '<div class="empty-msg">Abhi SELL side mein koi active stock nahi hai.</div>'
stk_html += "</div>"
st.markdown(stk_html, unsafe_allow_html=True)

if auto_refresh:
    time.sleep(refresh_sec)
    st.rerun()
