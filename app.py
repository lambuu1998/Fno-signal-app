import time
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="ARVANO Direct 15m Trade Box (No Charts)",
    page_icon="🎯",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0d0d0f;
        color: #f5f0e6;
    }
    .trade-box {
        background: linear-gradient(145deg, #161518 0%, #1e1a15 100%);
        border: 1px solid #3c3326;
        border-left: 6px solid #d4a359;
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 14px;
    }
    .trade-buy {
        border-left: 6px solid #22c55e;
    }
    .trade-sell {
        border-left: 6px solid #ef4444;
    }
    .trade-wait {
        border-left: 6px solid #d4a359;
    }
    .action-line {
        font-size: 1.12rem;
        font-weight: 800;
        margin-bottom: 8px;
        color: #fff6e5;
    }
    .levels-line {
        font-size: 0.98rem;
        font-weight: 600;
        color: #f3e5c8;
        margin-bottom: 8px;
    }
    .detail-line {
        font-size: 0.88rem;
        color: #c9bca6;
        margin-bottom: 6px;
    }
    .reason-box {
        background: rgba(255, 255, 255, 0.04);
        border-radius: 8px;
        padding: 10px 12px;
        font-size: 0.90rem;
        color: #efe7d8;
    }
    .pill-buy {
        background: rgba(34, 197, 94, 0.2);
        color: #4ade80;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 800;
    }
    .pill-sell {
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 800;
    }
    .pill-wait {
        background: rgba(212, 163, 89, 0.2);
        color: #fbbf24;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 800;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

INDICES = {
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "SENSEX": "^BSESN",
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


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)

    d = d.dropna(subset=["Open", "High", "Low", "Close"]).copy()
    if len(d) < 60:
        return pd.DataFrame()

    close = d["Close"].astype(float)
    high = d["High"].astype(float)
    low = d["Low"].astype(float)
    vol = d["Volume"].fillna(0).astype(float) if "Volume" in d.columns else pd.Series(0.0, index=d.index)

    # Customized EMAs (10 EMA & 50 EMA + 20 EMA)
    d["ema10"] = close.ewm(span=10, adjust=False).mean()
    d["ema20"] = close.ewm(span=20, adjust=False).mean()
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
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
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

    # Support & Resistance (20-bar)
    d["res20"] = high.shift(1).rolling(20).max()
    d["sup20"] = low.shift(1).rolling(20).min()
    d["range14_high"] = high.shift(1).rolling(14).max()
    d["range14_low"] = low.shift(1).rolling(14).min()

    return d.dropna(subset=["ema50", "atr14", "res20", "sup20"])


def evaluate_direct_trade(d: pd.DataFrame, is_index: bool = False) -> dict:
    last = d.iloc[-1]
    prev = d.iloc[-2] if len(d) > 1 else last

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

    breakout_str = "Range Hold"
    pattern_str = "Normal 15m Structure"
    reasons = []

    if price > res20:
        breakout_str = f"Resistance Break (> {res20:.2f})"
        reasons.append(f"Resistance {res20:.2f} ke upar trade")
    elif price < sup20:
        breakout_str = f"Support Break (< {sup20:.2f})"
        reasons.append(f"Support {sup20:.2f} ke niche trade")

    if abs(min_low - sup20) / max(sup20, 1e-6) <= 0.004 and price >= ema10:
        pattern_str = "Double Bottom Break"
        reasons.append("Double Bottom support zone active")
    elif abs(max_high - res20) / max(res20, 1e-6) <= 0.004 and price <= ema10:
        pattern_str = "Double Top Break"
        reasons.append("Double Top resistance zone active")

    # Strict direct call/put/buy/sell rules
    bull_conds = [
        price > ema50,
        price > vwap,
        rsi >= 55,
        adx >= 20,
        price >= ema10,
    ]
    bear_conds = [
        price < ema50,
        price < vwap,
        rsi <= 45,
        adx >= 20,
        price <= ema10,
    ]

    bull_pts = sum(int(x) for x in bull_conds)
    bear_pts = sum(int(x) for x in bear_conds)

    if bull_pts >= 4 and price > ema50 and price > vwap:
        action = "BUY / CALL (CE)" if is_index else "BUY LONG"
        mode = "BUY"
        sl = max(0.0, price - 2.0 * atr)
        t1 = price + 1.5 * atr
        t2 = price + 2.8 * atr
        t3 = price + 4.2 * atr
        reasons.append(f"Bullish lock ({bull_pts}/5): Price > 50 EMA ({ema50:.2f}) & VWAP ({vwap:.2f}), RSI {rsi:.1f}, ADX {adx:.1f}")
    elif bear_pts >= 4 and price < ema50 and price < vwap:
        action = "SELL / PUT (PE)" if is_index else "SELL SHORT"
        mode = "SELL"
        sl = price + 2.0 * atr
        t1 = max(0.0, price - 1.5 * atr)
        t2 = max(0.0, price - 2.8 * atr)
        t3 = max(0.0, price - 4.2 * atr)
        reasons.append(f"Bearish lock ({bear_pts}/5): Price < 50 EMA ({ema50:.2f}) & VWAP ({vwap:.2f}), RSI {rsi:.1f}, ADX {adx:.1f}")
    else:
        action = "NO TRADE - WAIT"
        mode = "WAIT"
        sl = max(0.0, price - 2.0 * atr)
        t1 = price + 1.5 * atr if price >= ema50 else max(0.0, price - 1.5 * atr)
        t2 = price + 2.8 * atr if price >= ema50 else max(0.0, price - 2.8 * atr)
        t3 = price + 4.2 * atr if price >= ema50 else max(0.0, price - 4.2 * atr)
        reasons.append(f"Signal clear nahi hai (Bull {bull_pts}/5, Bear {bear_pts}/5, RSI {rsi:.1f}, ADX {adx:.1f}) — SL bachane ke liye wait")

    move_score = (atr_pct * 2.2) + (adx * 0.5) + (30.0 if mode != "WAIT" else 0.0) + (20.0 if "Break" in breakout_str else 0.0)

    return {
        "action": action,
        "mode": mode,
        "price": price,
        "sl": sl,
        "t1": t1,
        "t2": t2,
        "t3": t3,
        "ema10": ema10,
        "ema50": ema50,
        "vwap": vwap,
        "rsi": rsi,
        "adx": adx,
        "atr": atr,
        "atr_pct": atr_pct,
        "breakout": breakout_str,
        "pattern": pattern_str,
        "why_move": " | ".join(reasons),
        "move_score": move_score,
    }


@st.cache_data(ttl=120, show_spinner=False)
def load_15m(ticker: str, period: str = "10d", interval: str = "15m") -> pd.DataFrame:
    try:
        raw = yf.download(ticker, period=period, interval=interval, progress=False, threads=False)
        if raw is None or raw.empty:
            return pd.DataFrame()
        return compute_indicators(raw)
    except Exception:
        return pd.DataFrame()


def draw_box(title: str, sub_info: str, sig: dict, next_pick: str = ""):
    if sig["mode"] == "BUY":
        box_cls = "trade-box trade-buy"
        pill = '<span class="pill-buy">DIRECT BUY</span>'
    elif sig["mode"] == "SELL":
        box_cls = "trade-box trade-sell"
        pill = '<span class="pill-sell">DIRECT SELL</span>'
    else:
        box_cls = "trade-box trade-wait"
        pill = '<span class="pill-wait">NO TRADE / WAIT</span>'

    next_html = (
        f'<div class="detail-line" style="color:#ffd88a;"><b>Next Pick / Follow-up:</b> {next_pick}</div>'
        if next_pick
        else ""
    )

    st.markdown(
        f"""
        <div class="{box_cls}">
            <div class="action-line">{title} &nbsp; {pill} &nbsp; → &nbsp; {sig['action']}</div>
            <div class="levels-line">
                Entry / CMP: <b>{sig['price']:.2f}</b> &nbsp;|&nbsp;
                SL (2x ATR): <b>{sig['sl']:.2f}</b> &nbsp;|&nbsp;
                Target 1: <b>{sig['t1']:.2f}</b> &nbsp;|&nbsp;
                Target 2: <b>{sig['t2']:.2f}</b> &nbsp;|&nbsp;
                Target 3: <b>{sig['t3']:.2f}</b>
            </div>
            <div class="detail-line">
                {sub_info} &nbsp;|&nbsp;
                S/R Break: <b>{sig['breakout']}</b> &nbsp;|&nbsp;
                Pattern: <b>{sig['pattern']}</b> &nbsp;|&nbsp;
                10 EMA: <b>{sig['ema10']:.2f}</b> &nbsp;|&nbsp;
                50 EMA: <b>{sig['ema50']:.2f}</b> &nbsp;|&nbsp;
                VWAP: <b>{sig['vwap']:.2f}</b> &nbsp;|&nbsp;
                RSI: <b>{sig['rsi']:.1f}</b> &nbsp;|&nbsp;
                ADX: <b>{sig['adx']:.1f}</b>
            </div>
            {next_html}
            <div class="reason-box"><b>Kyun Gira / Kyun Utha / Direct Logic:</b> {sig['why_move']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.sidebar.header("Direct Trade Controls")
tf = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h"], index=0)
period_map = {"15m": "10d", "30m": "15d", "1h": "30d"}
capital = st.sidebar.number_input("Capital per Trade (₹)", min_value=5000, value=100000, step=5000)
risk_pct = st.sidebar.slider("Risk per Trade (%)", min_value=0.5, max_value=3.0, value=1.0, step=0.25)
auto_refresh = st.sidebar.checkbox("Auto-refresh every 120s", value=False)

if st.sidebar.button("Refresh Now"):
    st.cache_data.clear()

st.title("🎯 ARVANO Direct 15m Trade Boxes (Zero Charts)")
st.caption("10 EMA + 50 EMA + VWAP + RSI(14) + ADX(14) + ATR(14) | 2.0x ATR Stop-Loss + T1/T2/T3 | Direct Action Only")

# Scan Top 100 NSE Stocks
stock_list = []
prog = st.progress(0, text="Scanning Top 100 NSE stocks...")
for i, sym in enumerate(TOP_100_NSE):
    df_s = load_15m(sym, period=period_map[tf], interval=tf)
    if not df_s.empty:
        sig = evaluate_direct_trade(df_s, is_index=False)
        risk_ps = abs(sig["price"] - sig["sl"])
        qty = int((capital * (risk_pct / 100.0)) / risk_ps) if risk_ps > 0 else 1
        sig["symbol"] = sym.replace(".NS", "")
        sig["qty"] = max(qty, 1)
        stock_list.append(sig)
    prog.progress((i + 1) / len(TOP_100_NSE), text=f"Scanning Top 100 NSE stocks ({i + 1}/{len(TOP_100_NSE)})...")
prog.empty()

stock_list.sort(key=lambda x: x["move_score"], reverse=True)

# 1. INDICES BOXES (Nifty 50, Bank Nifty, Sensex)
st.subheader("1. Indices Boxes (Nifty 50 • Bank Nifty • Sensex)")
for idx_name, idx_ticker in INDICES.items():
    df_i = load_15m(idx_ticker, period=period_map[tf], interval=tf)
    if df_i.empty:
        st.warning(f"{idx_name}: Feed data not available.")
        continue
    sig_i = evaluate_direct_trade(df_i, is_index=True)
    top_s = stock_list[0] if stock_list else None
    nxt_str = (
        f"{top_s['symbol']} -> {top_s['action']} | CMP {top_s['price']:.2f} | SL {top_s['sl']:.2f} | T1 {top_s['t1']:.2f} | T2 {top_s['t2']:.2f}"
        if top_s
        else ""
    )
    draw_box(
        title=f"{idx_name}",
        sub_info=f"ATR%: {sig_i['atr_pct']:.2f}%",
        sig=sig_i,
        next_pick=nxt_str,
    )

st.markdown("---")

# 2. HIGH-MOVEMENT F&O / STOCK BOXES (Top 10 Movers from Top 100 NSE)
st.subheader("2. High-Movement Stock & F&O Boxes (Top 10 Movers)")
for rank, s in enumerate(stock_list[:10], start=1):
    nxt = stock_list[rank] if rank < len(stock_list) else None
    nxt_str = (
        f"{nxt['symbol']} ({nxt['action']}) | CMP {nxt['price']:.2f} | SL {nxt['sl']:.2f} | T1 {nxt['t1']:.2f} | T2 {nxt['t2']:.2f} | T3 {nxt['t3']:.2f}"
        if nxt
        else "End of Top 10"
    )
    draw_box(
        title=f"#{rank} {s['symbol']} (Qty ~ {s['qty']})",
        sub_info=f"Move Score: {s['move_score']:.1f} | ATR%: {s['atr_pct']:.2f}%",
        sig=s,
        next_pick=nxt_str,
    )

st.markdown("---")

# 3. GOLD & SILVER BOXES
st.subheader("3. Gold & Silver Boxes")
for m_name, m_ticker in METALS.items():
    df_m = load_15m(m_ticker, period=period_map[tf], interval=tf)
    if df_m.empty:
        st.warning(f"{m_name}: Feed data not available.")
        continue
    sig_m = evaluate_direct_trade(df_m, is_index=False)
    draw_box(
        title=f"{m_name}",
        sub_info=f"ATR%: {sig_m['atr_pct']:.2f}%",
        sig=sig_m,
    )

st.markdown("---")

# 4. ALL TOP 100 NSE STOCKS BOX TABLE
st.subheader("4. Top 100 NSE Stocks — Direct Action Table")
if stock_list:
    rows = [
        {
            "Rank": idx + 1,
            "Stock": item["symbol"],
            "Action": item["action"],
            "CMP": round(item["price"], 2),
            "SL": round(item["sl"], 2),
            "T1": round(item["t1"], 2),
            "T2": round(item["t2"], 2),
            "T3": round(item["t3"], 2),
            "S/R Break": item["breakout"],
            "Pattern": item["pattern"],
            "ATR%": round(item["atr_pct"], 2),
            "Why Move": item["why_move"],
        }
        for idx, item in enumerate(stock_list)
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

if auto_refresh:
    time.sleep(120)
    st.rerun()
