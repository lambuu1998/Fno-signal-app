import time
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="ARVANO Client & F&O Live Box Scanner",
    page_icon="⚡",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0d0d10;
        color: #f6f1e7;
    }
    .client-box {
        position: relative;
        background: linear-gradient(145deg, #161519 0%, #1f1b16 100%);
        border: 1px solid #3c3326;
        border-left: 6px solid #d4a359;
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 14px;
    }
    .box-buy {
        border-left: 6px solid #22c55e;
    }
    .box-sell {
        border-left: 6px solid #ef4444;
    }
    .box-wait {
        border-left: 6px solid #eab308;
    }
    .box-top-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;
        flex-wrap: wrap;
    }
    .box-heading {
        font-size: 1.08rem;
        font-weight: 800;
        color: #fff7e8;
    }
    .hit-badge {
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 800;
        letter-spacing: 0.3px;
    }
    .hit-t1 {
        background: rgba(34, 197, 94, 0.22);
        color: #4ade80;
        border: 1px solid #22c55e;
    }
    .hit-t2 {
        background: rgba(16, 185, 129, 0.28);
        color: #6ee7b7;
        border: 1px solid #10b981;
    }
    .hit-t3 {
        background: rgba(212, 163, 89, 0.28);
        color: #fde68a;
        border: 1px solid #f59e0b;
    }
    .hit-sl {
        background: rgba(239, 68, 68, 0.24);
        color: #f87171;
        border: 1px solid #ef4444;
    }
    .hit-active {
        background: rgba(59, 130, 246, 0.22);
        color: #93c5fd;
        border: 1px solid #3b82f6;
    }
    .hit-wait {
        background: rgba(148, 163, 184, 0.18);
        color: #cbd5e1;
        border: 1px solid #64748b;
    }
    .box-grid {
        font-size: 0.95rem;
        color: #f2e5cb;
        margin-bottom: 8px;
        line-height: 1.5;
    }
    .box-reason {
        background: rgba(255, 255, 255, 0.04);
        border-radius: 8px;
        padding: 9px 12px;
        font-size: 0.89rem;
        color: #ebe2d2;
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
    "GOLD FUTURES (COMEX USD)": "GC=F",
    "SILVER FUTURES (COMEX USD)": "SI=F",
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

    return d.dropna(subset=["ema50", "atr14", "res20", "sup20"])


def detect_hit_status(d: pd.DataFrame, side: str, entry: float, sl: float, t1: float, t2: float, t3: float) -> str:
    today = d.index[-1].date()
    today_df = d[d.index.date == today]
    if today_df.empty:
        today_df = d.tail(4)

    max_high = float(today_df["High"].max())
    min_low = float(today_df["Low"].min())
    last_close = float(d["Close"].iloc[-1])

    if side == "BUY":
        if max_high >= t3 or last_close >= t3:
            return "T3 HIT"
        if max_high >= t2 or last_close >= t2:
            return "T2 HIT"
        if max_high >= t1 or last_close >= t1:
            return "T1 HIT"
        if min_low <= sl or last_close <= sl:
            return "SL HIT"
        return "ACTIVE (RUNNING)"

    if side == "SELL":
        if min_low <= t3 or last_close <= t3:
            return "T3 HIT"
        if min_low <= t2 or last_close <= t2:
            return "T2 HIT"
        if min_low <= t1 or last_close <= t1:
            return "T1 HIT"
        if max_high >= sl or last_close >= sl:
            return "SL HIT"
        return "ACTIVE (RUNNING)"

    return "NO TRADE (WAIT)"


def build_signal(d: pd.DataFrame, name: str, strike_step: int | None = None) -> dict:
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

    reasons = []
    if price > res20:
        reasons.append(f"Resistance {res20:.2f} break")
    elif price < sup20:
        reasons.append(f"Support {sup20:.2f} break")

    bull_score = int(price > ema50) + int(price > vwap) + int(rsi >= 55) + int(adx >= 20) + int(price >= ema10)
    bear_score = int(price < ema50) + int(price < vwap) + int(rsi <= 45) + int(adx >= 20) + int(price <= ema10)

    if bull_score >= 4 and price > ema50 and price > vwap:
        side = "BUY"
        call_text = f"BUY {round_strike(price, strike_step, 'BUY')} CE" if strike_step else "BUY"
        entry = price
        sl = max(0.0, entry - 2.0 * atr)
        t1 = entry + 1.5 * atr
        t2 = entry + 2.8 * atr
        t3 = entry + 4.2 * atr
        reasons.append(f"Bullish ({bull_score}/5): >50 EMA & VWAP, RSI {rsi:.1f}, ADX {adx:.1f}")
    elif bear_score >= 4 and price < ema50 and price < vwap:
        side = "SELL"
        call_text = f"BUY {round_strike(price, strike_step, 'SELL')} PE" if strike_step else "SELL"
        entry = price
        sl = entry + 2.0 * atr
        t1 = max(0.0, entry - 1.5 * atr)
        t2 = max(0.0, entry - 2.8 * atr)
        t3 = max(0.0, entry - 4.2 * atr)
        reasons.append(f"Bearish ({bear_score}/5): <50 EMA & VWAP, RSI {rsi:.1f}, ADX {adx:.1f}")
    else:
        side = "WAIT"
        call_text = "WAIT (NO TRADE)"
        entry = price
        sl = max(0.0, entry - 2.0 * atr)
        t1 = entry + 1.5 * atr if price >= ema50 else max(0.0, entry - 1.5 * atr)
        t2 = entry + 2.8 * atr if price >= ema50 else max(0.0, entry - 2.8 * atr)
        t3 = entry + 4.2 * atr if price >= ema50 else max(0.0, entry - 4.2 * atr)
        reasons.append(f"Mixed setup (Bull {bull_score}/5, Bear {bear_score}/5, RSI {rsi:.1f}, ADX {adx:.1f})")

    lock_key = f"locked_{name}"
    if side in ("BUY", "SELL"):
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
    else:
        st.session_state.pop(lock_key, None)

    hit_status = detect_hit_status(d, side, entry, sl, t1, t2, t3)
    move_score = (atr_pct * 2.2) + (adx * 0.5) + (35.0 if side != "WAIT" else 0.0)

    return {
        "name": name,
        "side": side,
        "call_text": call_text,
        "cmp": round(price, 2),
        "entry": round(entry, 2),
        "sl": round(sl, 2),
        "t1": round(t1, 2),
        "t2": round(t2, 2),
        "t3": round(t3, 2),
        "atr_pct": round(atr_pct, 2),
        "hit_status": hit_status,
        "reason": " | ".join(reasons),
        "move_score": move_score,
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


def status_badge_html(status: str) -> str:
    if "T3 HIT" in status:
        return f'<span class="hit-badge hit-t3">{status}</span>'
    if "T2 HIT" in status:
        return f'<span class="hit-badge hit-t2">{status}</span>'
    if "T1 HIT" in status:
        return f'<span class="hit-badge hit-t1">{status}</span>'
    if "SL HIT" in status:
        return f'<span class="hit-badge hit-sl">{status}</span>'
    if "ACTIVE" in status:
        return f'<span class="hit-badge hit-active">{status}</span>'
    return f'<span class="hit-badge hit-wait">{status}</span>'


def render_client_box(title_left: str, sig: dict, next_stock_line: str = ""):
    box_cls = (
        "client-box box-buy"
        if sig["side"] == "BUY"
        else ("client-box box-sell" if sig["side"] == "SELL" else "client-box box-wait")
    )
    badge = status_badge_html(sig["hit_status"])
    next_html = (
        f'<div style="color:#ffd98e; font-size:0.90rem; margin-bottom:6px;"><b>Aage Chalne Wala Pick:</b> {next_stock_line}</div>'
        if next_stock_line
        else ""
    )

    st.markdown(
        f"""
        <div class="{box_cls}">
            <div class="box-top-row">
                <div class="box-heading">{title_left} → {sig['call_text']}</div>
                <div>{badge}</div>
            </div>
            <div class="box-grid">
                <b>Price / Entry:</b> {sig['entry']:.2f} (CMP: {sig['cmp']:.2f}) &nbsp;|&nbsp;
                <b>SL:</b> {sig['sl']:.2f} &nbsp;|&nbsp;
                <b>T1:</b> {sig['t1']:.2f} &nbsp;|&nbsp;
                <b>T2:</b> {sig['t2']:.2f} &nbsp;|&nbsp;
                <b>T3:</b> {sig['t3']:.2f}
            </div>
            {next_html}
            <div class="box-reason"><b>Kyun (Reason):</b> {sig['reason']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Sidebar Controls
st.sidebar.header("Live Auto-Refresh Controls")
refresh_sec = st.sidebar.slider("Auto-Refresh Interval (Seconds)", min_value=30, max_value=60, value=45, step=5)
auto_loop = st.sidebar.checkbox("Auto-Refresh ON (30–60s)", value=True)
tf = st.sidebar.selectbox("Chart Timeframe Logic", ["15m", "30m"], index=0)
period_map = {"15m": "10d", "30m": "15d"}

if st.sidebar.button("Manual Refresh Now"):
    st.cache_data.clear()

st.title("⚡ ARVANO Client & F&O Box Scanner (No Charts)")
st.caption(
    f"Auto-refresh: {refresh_sec}s | Auto-checks T1 / T2 / T3 / SL hit status | Nifty 50 • Bank Nifty • Sensex • Gold & Silver • Top 100 NSE"
)

# 1. Scan Top 100 NSE Stocks
all_stocks = []
prog = st.progress(0, text="Scanning Top 100 NSE stocks...")
for idx, sym in enumerate(TOP_100_NSE):
    df_s = fetch_data(sym, period=period_map[tf], interval=tf)
    if not df_s.empty:
        s_name = sym.replace(".NS", "")
        all_stocks.append(build_signal(df_s, s_name, strike_step=None))
    prog.progress((idx + 1) / len(TOP_100_NSE), text=f"Scanning Top 100 NSE ({idx + 1}/{len(TOP_100_NSE)})...")
prog.empty()

all_stocks.sort(key=lambda x: x["move_score"], reverse=True)
top_mover_str = (
    f"{all_stocks[0]['name']} ({all_stocks[0]['call_text']}) | Price {all_stocks[0]['entry']:.2f} | "
    f"T1 {all_stocks[0]['t1']:.2f} | T2 {all_stocks[0]['t2']:.2f} | T3 {all_stocks[0]['t3']:.2f} | Status: {all_stocks[0]['hit_status']}"
    if all_stocks
    else "No mover data"
)

# 2. F&O / INDICES SECTION (Nifty 50, Bank Nifty, Sensex)
st.subheader("1. F&O Indices Box (Nifty 50 • Bank Nifty • Sensex)")
for idx_label, cfg in INDICES.items():
    df_i = fetch_data(cfg["ticker"], period=period_map[tf], interval=tf)
    if df_i.empty:
        st.warning(f"{idx_label}: Live feed unavailable right now.")
        continue
    sig_i = build_signal(df_i, idx_label, strike_step=cfg["step"])
    render_client_box(title_left=idx_label, sig=sig_i, next_stock_line=top_mover_str)

st.markdown("---")

# 3. GOLD & SILVER BOXES
st.subheader("2. Gold & Silver Boxes (Futures & NSE ETFs)")
for m_label, m_ticker in METALS.items():
    df_m = fetch_data(m_ticker, period=period_map[tf], interval=tf)
    if df_m.empty:
        st.warning(f"{m_label}: Live feed unavailable right now.")
        continue
    sig_m = build_signal(df_m, m_label, strike_step=None)
    render_client_box(title_left=m_label, sig=sig_m)

st.markdown("---")

# 4. ALL TOP 100 NSE STOCKS SINGLE CLEAN BOX LIST
st.subheader("3. Top 100 NSE Stocks — Clean Client Box (Stock • Buy/Sell • Price • Kyun • T1/T2/T3 • Live Hit Status)")
if all_stocks:
    for rank, item in enumerate(all_stocks, start=1):
        nxt_txt = ""
        if rank < len(all_stocks):
            nxt = all_stocks[rank]
            nxt_txt = f"{nxt['name']} ({nxt['call_text']}) @ {nxt['entry']:.2f} [T1: {nxt['t1']:.2f} | {nxt['hit_status']}]"
        render_client_box(
            title_left=f"#{rank} {item['name']}",
            sig=item,
            next_stock_line=nxt_txt,
        )

    st.markdown("---")
    st.subheader("4. Quick Status Summary Table (Top 100 NSE)")
    summary_df = pd.DataFrame(
        [
            {
                "Rank": i + 1,
                "Stock": r["name"],
                "Action": r["call_text"],
                "Price": r["entry"],
                "Kyun": r["reason"],
                "T1": r["t1"],
                "T2": r["t2"],
                "T3": r["t3"],
                "SL": r["sl"],
                "Live Status": r["hit_status"],
            }
            for i, r in enumerate(all_stocks)
        ]
    )
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
else:
    st.info("No stock data returned.")

if auto_loop:
    time.sleep(refresh_sec)
    st.rerun()
