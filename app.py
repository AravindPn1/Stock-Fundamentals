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
# COLORFUL APP UI
# =========================

st.markdown("""
<style>

/* App background */
.stApp {
    background: linear-gradient(135deg, #eef2ff, #f8fafc);
}

/* Section boxes */
.box {
    background: white;
    border-radius: 18px;
    padding: 12px;
    margin-bottom: 12px;
    box-shadow: 0px 6px 20px rgba(0,0,0,0.08);
}

/* ticker tile */
.tile {
    padding: 12px;
    border-radius: 14px;
    text-align: center;
    font-weight: 600;
    cursor: pointer;
    transition: 0.25s;
    color: #111827;
    box-shadow: 0px 3px 10px rgba(0,0,0,0.08);
}

/* hover pop */
.tile:hover {
    transform: scale(1.07);
    box-shadow: 0px 8px 18px rgba(0,0,0,0.15);
}

/* selected */
.active {
    border: 3px solid #2563eb;
    box-shadow: 0px 0px 18px rgba(37,99,235,0.4);
}

/* headings */
h3 {
    margin-bottom: 6px;
}

</style>
""", unsafe_allow_html=True)

st.title("📊 Smart Trading Terminal")

# =========================
# DATA
# =========================

WATCHLIST = ["AAPL","MSFT","NVDA","TSLA","AMZN","META","GOOGL","AMD","PLTR","NFLX","COIN","MSTR"]

HOT = ["SMCI","ARM","SNOW","NET","SHOP","RDDT","CRWD","AVGO"]

OVERLAYS = ["EMA20","EMA50","EMA200"]

if "ticker" not in st.session_state:
    st.session_state.ticker = "AAPL"

@st.cache_data(ttl=300)
def load(t):
    df = yf.download(t, period="2y", interval="1d", auto_adjust=True)
    df = df.reset_index()
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
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

# =========================
# PROBABILITY ENGINE
# =========================

def prob(df):
    l = df.iloc[-1]

    trend = l["EMA20"] > l["EMA50"]
    strong = l["EMA50"] > l["EMA200"]
    momentum = 40 < l["RSI"] < 70
    volume = l["RVOL"] > 1.5

    score = (
        trend * 30 +
        strong * 20 +
        momentum * 25 +
        volume * 25
    )

    return min(95, max(20, score))

# =========================
# CHART
# =========================

def chart(df, overlays, rsi=True):

    fig = make_subplots(
        rows=3 if rsi else 2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.6,0.25,0.15] if rsi else [0.7,0.3]
    )

    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["Close"],
        name="Price",
        line=dict(color="#111827", width=2)
    ), row=1, col=1)

    if "EMA20" in overlays:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA20"], name="EMA20"), row=1, col=1)
    if "EMA50" in overlays:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA50"], name="EMA50"), row=1, col=1)
    if "EMA200" in overlays:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA200"], name="EMA200"), row=1, col=1)

    fig.add_trace(go.Bar(
        x=df["Date"], y=df["Volume"],
        name="Volume",
        marker_color="rgba(99,102,241,0.35)"
    ), row=2, col=1)

    if rsi:
        fig.add_trace(go.Scatter(
            x=df["Date"], y=df["RSI"],
            name="RSI",
            line=dict(color="#7c3aed")
        ), row=3, col=1)

    fig.update_layout(height=720, template="plotly_white")

    return fig

# =========================
# LAYOUT
# =========================

left, right = st.columns([1.2, 3])

# =========================
# LEFT PANEL (BIG COLOR BOXES)
# =========================

with left:

    # WATCHLIST BOX
    st.markdown('<div class="box"><h3>📌 Watchlist</h3>', unsafe_allow_html=True)

    grid = st.columns(3)

    for i, t in enumerate(WATCHLIST):

        df = ind(load(t))
        last = df.iloc[-1]
        prev = df.iloc[-2]

        chg = ((last["Close"] - prev["Close"]) / prev["Close"]) * 100

        color = "#dcfce7" if chg > 0 else "#fee2e2"
        active = "active" if t == st.session_state.ticker else ""

        with grid[i % 3]:

            st.markdown(
                f"""
                <div class="tile {active}" style="background:{color}">
                    {t}<br>
                    {round(chg,2)}%
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(f"Select {t}", key=f"w_{t}"):
                st.session_state.ticker = t

    st.markdown("</div>", unsafe_allow_html=True)

    # HOT BOX
    st.markdown('<div class="box"><h3>🔥 Hot Movers</h3>', unsafe_allow_html=True)

    grid2 = st.columns(3)

    for i, t in enumerate(HOT):

        df = ind(load(t))
        last = df.iloc[-1]
        prev = df.iloc[-2]

        chg = ((last["Close"] - prev["Close"]) / prev["Close"]) * 100

        color = "#dcfce7" if chg > 0 else "#fee2e2"

        with grid2[i % 3]:

            st.markdown(
                f"""
                <div class="tile" style="background:{color}">
                    {t}<br>
                    {round(chg,2)}%
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(f"Trade {t}", key=f"h_{t}"):
                st.session_state.ticker = t

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# RIGHT PANEL
# =========================

t = st.session_state.ticker

df = ind(load(t))
p = prob(df)

l = df.iloc[-1]

st.header(f"{t}")

c1,c2,c3,c4 = st.columns(4)

c1.metric("Price", round(l["Close"],2))
c2.metric("RSI", round(l["RSI"],1))
c3.metric("RVOL", round(l["RVOL"],2))
c4.metric("Prob%", round(p,1))

overlays = st.multiselect("Overlays", OVERLAYS, default=["EMA20","EMA50"])
rsi = st.checkbox("Show RSI", value=True)

st.plotly_chart(chart(df, overlays, rsi), use_container_width=True)

# =========================
# EDUCATION (UNCHANGED BUT CLEAN)
# =========================

with st.expander("📘 Research Engine", expanded=True):

    trend = "Bullish" if l["EMA20"] > l["EMA50"] else "Bearish"

    st.write(f"Trend: **{trend}**")

    if l["RSI"] > 70:
        st.write("Overbought condition")
    elif l["RSI"] < 30:
        st.write("Oversold condition")
    else:
        st.write("Neutral momentum")

    if l["RVOL"] > 1.5:
        st.success("High participation detected")
    else:
        st.write("Normal volume conditions")

    if p > 70:
        st.success("High probability setup")
    elif p > 50:
        st.info("Moderate setup")
    else:
        st.warning("Low quality setup")
