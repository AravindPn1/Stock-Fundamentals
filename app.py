import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(layout="wide")

# =========================
# SUPER COLORFUL UI (NO GREY TERMINAL LOOK)
# =========================

st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg, #0f172a, #1e1b4b, #0f172a);
    color: white;
}

/* LEFT PANEL TILE GRID */
.tile {
    padding: 14px;
    border-radius: 16px;
    text-align: center;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.25s ease;
    color: white;
    box-shadow: 0px 6px 18px rgba(0,0,0,0.35);
    backdrop-filter: blur(10px);
}

/* hover glow */
.tile:hover {
    transform: scale(1.08);
    box-shadow: 0px 0px 25px rgba(59,130,246,0.6);
}

/* active selection */
.active {
    outline: 3px solid #22d3ee;
    box-shadow: 0px 0px 30px rgba(34,211,238,0.5);
}

/* boxes */
.box {
    background: rgba(255,255,255,0.06);
    border-radius: 20px;
    padding: 14px;
    margin-bottom: 14px;
    box-shadow: 0px 8px 30px rgba(0,0,0,0.3);
}

/* headers */
h1, h2, h3 {
    color: #e0f2fe;
}

</style>
""", unsafe_allow_html=True)

# =========================
# STATE
# =========================

if "ticker" not in st.session_state:
    st.session_state.ticker = "AAPL"

# =========================
# DATA
# =========================

WATCHLIST = ["AAPL","MSFT","NVDA","TSLA","AMZN","META","GOOGL","AMD","PLTR","NFLX","COIN","MSTR"]
HOT = ["SMCI","ARM","SNOW","NET","SHOP","RDDT","CRWD","AVGO"]

OVERLAYS = ["EMA20","EMA50","EMA200"]

@st.cache_data(ttl=300)
def load(t):
    df = yf.download(t, period="2y", interval="1d", auto_adjust=True)
    df = df.reset_index()
    return df.dropna()

def ind(df):
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()
    df["EMA200"] = df["Close"].ewm(span=200).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + rs))

    df["VOL_MA"] = df["Volume"].rolling(20).mean()
    df["RVOL"] = df["Volume"] / df["VOL_MA"]

    return df.dropna()

def thesis(df):
    l = df.iloc[-1]

    trend = "BULLISH" if l["EMA20"] > l["EMA50"] else "BEARISH"
    strength = "STRONG" if l["EMA50"] > l["EMA200"] else "WEAK"

    rsi_state = (
        "OVERBOUGHT" if l["RSI"] > 70 else
        "OVERSOLD" if l["RSI"] < 30 else
        "NEUTRAL"
    )

    vol_state = "HIGH PARTICIPATION" if l["RVOL"] > 1.5 else "NORMAL"

    score = (
        (l["EMA20"] > l["EMA50"]) * 30 +
        (l["EMA50"] > l["EMA200"]) * 20 +
        (40 < l["RSI"] < 70) * 25 +
        (l["RVOL"] > 1.5) * 25
    )

    return {
        "trend": trend,
        "strength": strength,
        "rsi": rsi_state,
        "volume": vol_state,
        "score": min(95, max(10, score))
    }

# =========================
# CHART (CLEAN + LABELED)
# =========================

def chart(df, overlays, show_rsi=True):

    fig = make_subplots(
        rows=3 if show_rsi else 2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.25, 0.15] if show_rsi else [0.7, 0.3],
        vertical_spacing=0.03
    )

    # PRICE
    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Close"],
            name="Price",
            line=dict(color="#38bdf8", width=2)
        ),
        row=1, col=1
    )

    if "EMA20" in overlays:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA20"], name="EMA20"), row=1, col=1)
    if "EMA50" in overlays:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA50"], name="EMA50"), row=1, col=1)
    if "EMA200" in overlays:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA200"], name="EMA200"), row=1, col=1)

    # VOLUME
    fig.add_trace(
        go.Bar(
            x=df["Date"],
            y=df["Volume"],
            name="Volume",
            marker_color="rgba(34,211,238,0.35)"
        ),
        row=2, col=1
    )

    # RSI
    if show_rsi:
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["RSI"],
                name="RSI",
                line=dict(color="#a78bfa")
            ),
            row=3, col=1
        )

    fig.update_layout(
        height=750,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)

    return fig

# =========================
# LAYOUT (LOCKED LEFT/RIGHT)
# =========================

left, right = st.columns([1.2, 3])

# =========================
# LEFT PANEL (CLICKABLE TILE GRID ONLY)
# =========================

with left:

    st.markdown("## 📌 Watchlist")

    cols = st.columns(3)

    for i, t in enumerate(WATCHLIST):

        df = ind(load(t))
        l = df.iloc[-1]
        p = df.iloc[-2]

        chg = ((l["Close"] - p["Close"]) / p["Close"]) * 100

        bg = "#10b981" if chg > 0 else "#ef4444"

        active = "active" if t == st.session_state.ticker else ""

        with cols[i % 3]:

            st.markdown(
                f"""
                <div class="tile {active}" style="background:{bg}">
                    {t}<br>
                    {chg:.2f}%
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(t, key=f"sel_{t}"):
                st.session_state.ticker = t

    st.markdown("## 🔥 Hot Movers")

    cols2 = st.columns(3)

    for i, t in enumerate(HOT):

        df = ind(load(t))
        l = df.iloc[-1]
        p = df.iloc[-2]

        chg = ((l["Close"] - p["Close"]) / p["Close"]) * 100

        bg = "#22c55e" if chg > 0 else "#f97316"

        with cols2[i % 3]:

            st.markdown(
                f"""
                <div class="tile" style="background:{bg}">
                    {t}<br>
                    {chg:.2f}%
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(t + "_hot", key=f"hot_{t}"):
                st.session_state.ticker = t

# =========================
# RIGHT PANEL (FULL ANALYSIS)
# =========================

t = st.session_state.ticker
df = ind(load(t))
th = thesis(df)

l = df.iloc[-1]

st.markdown(f"# 📊 {t} Research Terminal")

# TOP METRICS
c1, c2, c3, c4 = st.columns(4)

c1.metric("Price", round(l["Close"], 2))
c2.metric("RSI", round(l["RSI"], 1))
c3.metric("RVOL", round(l["RVOL"], 2))
c4.metric("Score", th["score"])

# CHART CONTROLS
overlays = st.multiselect("Overlays", OVERLAYS, default=["EMA20","EMA50"])
show_rsi = st.checkbox("RSI Panel", True)

st.plotly_chart(chart(df, overlays, show_rsi), use_container_width=True)

# =========================
# DEEP EDUCATION / THESIS ENGINE
# =========================

with st.expander("🧠 Investment Thesis (Deep Analysis)", expanded=True):

    st.markdown(f"""
### 🔍 Signal Interpretation

- **Trend:** {th["trend"]}
- **Strength:** {th["strength"]}
- **Momentum (RSI):** {th["rsi"]}
- **Volume:** {th["volume"]}

---

### 📊 What is driving this view?

- EMA20 vs EMA50 shows **short-term directional bias**
- EMA50 vs EMA200 defines **macro trend regime**
- RSI measures **momentum exhaustion vs continuation**
- RVOL shows **institutional participation**

---

### 🎯 Why this matters

This setup suggests:
- Trend alignment = {th["trend"] == "BULLISH"}
- Institutional participation = {l["RVOL"] > 1.5}
- Momentum regime = {th["rsi"]}

---

### 💡 Trade Thesis (Auto-generated)

If trend + strength align:
> “Momentum continuation trade likely with trend-following bias”

If mixed signals:
> “Range / mean reversion conditions dominate”

---

### ⚠️ Risk Notes

- RSI extremes increase reversal risk
- RVOL spikes may indicate short-term exhaustion
- EMA200 breakdown invalidates bullish structure
""")
