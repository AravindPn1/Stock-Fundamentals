import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =========================
# PAGE CONFIG + STYLE
# =========================

st.set_page_config(layout="wide")

st.markdown("""
<style>

/* App background */
.stApp {
    background: linear-gradient(180deg, #f5f7fb 0%, #eef2ff 100%);
}

/* Left tiles */
.tile {
    padding: 10px;
    margin: 6px;
    border-radius: 16px;
    text-align: center;
    font-weight: 600;
    cursor: pointer;
    transition: 0.2s;
    box-shadow: 0px 3px 10px rgba(0,0,0,0.05);
}

/* hover effect */
.tile:hover {
    transform: scale(1.05);
}

/* active selection */
.active {
    border: 2px solid #2563eb;
    box-shadow: 0px 0px 14px rgba(37,99,235,0.4);
}

/* header spacing */
.block-container {
    padding-top: 1rem;
}

</style>
""", unsafe_allow_html=True)

# =========================
# APP STATE
# =========================

st.title("📊 Smart Trading Research Desk")

WATCHLIST = [
    "AAPL","MSFT","NVDA","TSLA","AMZN","META",
    "GOOGL","AMD","PLTR","NFLX","COIN","MSTR"
]

OVERLAYS = ["EMA20","EMA50","EMA200"]

if "ticker" not in st.session_state:
    st.session_state.ticker = "AAPL"

# =========================
# DATA
# =========================

@st.cache_data(ttl=300)
def load(t):
    df = yf.download(t, period="2y", interval="1d", auto_adjust=True)
    df = df.reset_index()
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df.dropna()

def indicators(df):
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
# PROBABILITY MODEL v3 (RESTORED + IMPROVED)
# =========================

def probability(df):

    l = df.iloc[-1]

    trend_up = l["EMA20"] > l["EMA50"]
    trend_strong = l["EMA50"] > l["EMA200"]

    momentum_ok = 40 < l["RSI"] < 70
    volume_ok = l["RVOL"] > 1.4

    score = (
        trend_up * 28 +
        trend_strong * 22 +
        momentum_ok * 25 +
        volume_ok * 25
    )

    return min(95, max(20, score))

# =========================
# CHART (PRICE + VOLUME + RSI)
# =========================

def chart(df, overlays, show_rsi=True):

    fig = make_subplots(
        rows=3 if show_rsi else 2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.6,0.25,0.15] if show_rsi else [0.7,0.3],
        vertical_spacing=0.05
    )

    # PRICE
    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=df["Close"],
        name="Price",
        line=dict(color="#111827", width=2)
    ), row=1, col=1)

    if "EMA20" in overlays:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA20"], name="EMA20"), row=1, col=1)
    if "EMA50" in overlays:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA50"], name="EMA50"), row=1, col=1)
    if "EMA200" in overlays:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA200"], name="EMA200"), row=1, col=1)

    # VOLUME
    fig.add_trace(go.Bar(
        x=df["Date"],
        y=df["Volume"],
        name="Volume",
        marker_color="rgba(99,102,241,0.35)"
    ), row=2, col=1)

    # RSI
    if show_rsi:
        fig.add_trace(go.Scatter(
            x=df["Date"],
            y=df["RSI"],
            name="RSI",
            line=dict(color="#7c3aed")
        ), row=3, col=1)

        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    fig.update_layout(
        height=720,
        template="plotly_white",
        margin=dict(l=10,r=10,t=30,b=10)
    )

    return fig

# =========================
# LAYOUT (RESTORED LEFT/RIGHT)
# =========================

left, right = st.columns([1.1, 3])

# =========================
# LEFT PANE (APP-LIKE TILE GRID)
# =========================

with left:

    st.subheader("Watchlist")

    grid = st.columns(3)

    for i, t in enumerate(WATCHLIST):

        df = indicators(load(t))
        last = df.iloc[-1]
        prev = df.iloc[-2]

        chg = ((last["Close"] - prev["Close"]) / prev["Close"]) * 100

        bg = "#dcfce7" if chg > 0 else "#fee2e2"
        active = "active" if t == st.session_state.ticker else ""

        tile = f"""
        <div class="tile {active}" style="background:{bg}"
            onclick="">
            {t}<br>
            {round(chg,2)}%
        </div>
        """

        with grid[i % 3]:
            if st.button(t, key=f"btn_{t}"):
                st.session_state.ticker = t

            st.markdown(tile, unsafe_allow_html=True)

# =========================
# RIGHT PANE (RESEARCH)
# =========================

t = st.session_state.ticker

df = indicators(load(t))
p = probability(df)

l = df.iloc[-1]

st.header(f"{t}")

# =========================
# METRICS (RESTORED FULL SET)
# =========================

c1,c2,c3,c4,c5,c6,c7 = st.columns(7)

c1.metric("Price", round(l["Close"],2))
c2.metric("Change", round(((l["Close"]-df.iloc[-2]["Close"])/df.iloc[-2]["Close"])*100,2))
c3.metric("RSI", round(l["RSI"],1))
c4.metric("RVOL", round(l["RVOL"],2))
c5.metric("Prob%", round(p,1))
c6.metric("EMA20", round(l["EMA20"],2))
c7.metric("EMA50/200", f"{round(l['EMA50'],1)} | {round(l['EMA200'],1)}")

# =========================
# CONTROLS
# =========================

overlays = st.multiselect(
    "Overlays",
    OVERLAYS,
    default=["EMA20","EMA50"]
)

show_rsi = st.checkbox("Show RSI Panel", value=True)

st.plotly_chart(chart(df, overlays, show_rsi), use_container_width=True)

# =========================
# EDUCATION (IMPROVED + NON-REPETITIVE)
# =========================

with st.expander("📘 Research & Trade Thesis", expanded=True):

    trend = "Bullish" if l["EMA20"] > l["EMA50"] else "Bearish / Transition"

    st.markdown("### Market Structure")
    st.write(f"Regime: **{trend}**")

    st.markdown("### Momentum Interpretation")

    if l["RSI"] > 70:
        st.write("Momentum extended — expect mean reversion risk.")
    elif l["RSI"] < 30:
        st.write("Oversold compression — reversal probability increasing.")
    else:
        st.write("Neutral momentum — trend continuation depends on volume.")

    st.markdown("### Volume Intelligence")

    if l["RVOL"] > 1.5:
        st.success("High participation breakout conditions present.")
    else:
        st.write("Normal participation — no expansion detected.")

    st.markdown("### Trade Thesis Engine")

    if p > 75:
        st.success("High-probability momentum continuation setup.")
    elif p > 55:
        st.info("Moderate setup — wait for confirmation trigger.")
    else:
        st.warning("Low-quality setup — avoid or size down risk.")

    st.markdown("### Risk Framework")

    st.write("- EMA50 break invalidates bullish thesis")
    st.write("- Low RVOL = false breakout risk")
    st.write("- RSI extremes require confirmation candle")
