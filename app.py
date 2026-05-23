import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =========================
# CONFIG
# =========================

st.set_page_config(layout="wide")

# =========================
# STATE
# =========================

if "ticker" not in st.session_state:
    st.session_state.ticker = "AAPL"

# =========================
# DATA LOADER (FIXED FOR YF SHAPES)
# =========================

@st.cache_data(ttl=300)
def load(t):

    df = yf.download(t, period="2y", interval="1d", auto_adjust=True)

    # FIX: flatten multiindex columns if they exist
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()

    # FORCE CLEAN NUMERIC TYPES
    for c in ["Open","High","Low","Close","Volume"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df.dropna()

# =========================
# INDICATORS (FIXED RVOL BUG)
# =========================

def ind(df):

    df = df.copy()

    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()
    df["EMA200"] = df["Close"].ewm(span=200).mean()

    # RSI
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + rs))

    # VOLUME SAFE FIX
    df["VOL_MA"] = df["Volume"].rolling(20).mean()

    df["RVOL"] = np.where(
        df["VOL_MA"] == 0,
        0,
        df["Volume"] / df["VOL_MA"]
    )

    df = df.replace([np.inf, -np.inf], np.nan).dropna()

    return df

# =========================
# WATCHLISTS
# =========================

WATCHLIST = ["AAPL","MSFT","NVDA","TSLA","AMZN","META","GOOGL","AMD","PLTR","NFLX","COIN","MSTR"]
HOT = ["SMCI","ARM","SNOW","NET","SHOP","RDDT","CRWD","AVGO"]

# =========================
# UI STYLE (CLEAN + MODERN)
# =========================

st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg,#0b1020,#111827,#0b1020);
    color: white;
    font-size: 13px;
}

/* TILE */
.tile {
    padding: 10px;
    border-radius: 14px;
    text-align: center;
    font-weight: 600;
    cursor: pointer;
    margin: 4px;
    transition: 0.2s;
    color: white;
}

.tile:hover {
    transform: scale(1.05);
    box-shadow: 0 0 18px rgba(59,130,246,0.5);
}

.active {
    outline: 2px solid #22d3ee;
}

/* LEFT PANEL CONTAINER */
.panel {
    background: rgba(255,255,255,0.04);
    border-radius: 18px;
    padding: 10px;
}

/* HEADERS */
h1,h2,h3 {
    color: #e5e7eb;
}

</style>
""", unsafe_allow_html=True)

# =========================
# CHART
# =========================

def chart(df):

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.7,0.3])

    fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], name="Price"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA20"], name="EMA20"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA50"], name="EMA50"), row=1, col=1)

    fig.add_trace(go.Bar(x=df["Date"], y=df["Volume"], name="Volume"), row=2, col=1)

    fig.update_layout(height=650, template="plotly_dark")

    return fig

# =========================
# LAYOUT (LOCKED LEFT/RIGHT)
# =========================

left, right = st.columns([1.1, 3])

# =========================
# LEFT PANEL (WATCHLIST + HOT STACKED SAME PAGE)
# =========================

with left:

    st.markdown("## 📌 Market")

    st.markdown("<div class='panel'>", unsafe_allow_html=True)

    def render_list(title, lst):

        st.markdown(f"### {title}")

        cols = st.columns(3)

        for i, t in enumerate(lst):

            df = ind(load(t))
            last = df.iloc[-1]
            prev = df.iloc[-2]

            chg = ((last["Close"] - prev["Close"]) / prev["Close"]) * 100
            color = "#22c55e" if chg > 0 else "#ef4444"

            with cols[i % 3]:

                st.markdown(
                    f"""
                    <div class="tile" style="background:{color}">
                        {t}<br>
                        {chg:.2f}%
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.button(
                    t,
                    key=f"sel_{t}",
                    on_click=lambda x=t: st.session_state.update({"ticker": x})
                )

    render_list("Watchlist", WATCHLIST)
    render_list("Hot Movers", HOT)

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# RIGHT PANEL (RESEARCH)
# =========================

t = st.session_state.ticker

df = ind(load(t))

last = df.iloc[-1]

st.markdown(f"# 📊 {t} Research")

c1,c2,c3,c4 = st.columns(4)

c1.metric("Price", round(last["Close"],2))
c2.metric("RSI", round(last["RSI"],1))
c3.metric("RVOL", round(last["RVOL"],2))
c4.metric("EMA Trend", "Bull" if last["EMA20"] > last["EMA50"] else "Bear")

st.plotly_chart(chart(df), use_container_width=True)

# =========================
# EDUCATION / THESIS (STABLE)
# =========================

with st.expander("🧠 Thesis & Education", expanded=True):

    trend = "BULLISH" if last["EMA20"] > last["EMA50"] else "BEARISH"
    strength = "STRONG" if last["EMA50"] > last["EMA200"] else "WEAK"
    rsi_state = "OVERBOUGHT" if last["RSI"] > 70 else "OVERSOLD" if last["RSI"] < 30 else "NEUTRAL"

    st.markdown(f"""
### Signal Summary

- Trend: **{trend}**
- Strength: **{strength}**
- Momentum: **{rsi_state}**
- RVOL: **{last['RVOL']:.2f}**

---

### Interpretation

- EMA20 vs EMA50 → short-term direction
- EMA50 vs EMA200 → macro regime
- RSI → exhaustion vs continuation
- RVOL → institutional activity

---

### Thesis

This ticker is currently in a:
> **{trend} + {strength} regime**

Meaning:
- Trend-following strategies favored
- Avoid counter-trend unless RSI extreme
- Volume confirms participation when RVOL > 1.5

---

### Risk Notes

- RSI > 70 → pullback risk
- RSI < 30 → rebound opportunity
- EMA200 break invalidates structure
""")
