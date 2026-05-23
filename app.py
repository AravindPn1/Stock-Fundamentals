import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide")

# =========================
# CSS (GLASS UI)
# =========================

st.markdown("""
<style>

.block-container {
    padding-top: 1rem;
}

/* Glass tile */
.glass {
    padding: 10px;
    margin: 6px;
    border-radius: 14px;
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.3);
    text-align:center;
    cursor:pointer;
    transition: 0.2s;
    font-weight: 600;
}

.glass:hover {
    transform: scale(1.03);
}

/* active highlight */
.active {
    border: 2px solid #2563eb;
    box-shadow: 0px 0px 10px rgba(37,99,235,0.4);
}

</style>
""", unsafe_allow_html=True)

# =========================
# DATA
# =========================

WATCHLIST = ["AAPL","MSFT","NVDA","TSLA","AMZN","META","GOOGL","AMD","PLTR","NFLX","COIN","MSTR"]

OVERLAYS = ["EMA20","EMA50","EMA200"]

if "selected" not in st.session_state:
    st.session_state.selected = "AAPL"

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
# PROB MODEL (IMPROVED)
# =========================

def prob(df):

    l = df.iloc[-1]

    trend = l["EMA20"] > l["EMA50"]
    strong = l["EMA50"] > l["EMA200"]

    momentum = 40 < l["RSI"] < 70
    vol = l["RVOL"] > 1.5

    score = (
        trend * 30 +
        strong * 20 +
        momentum * 25 +
        vol * 25
    )

    return min(92, max(20, score))

# =========================
# CHART (PRICE + VOLUME + RSI)
# =========================

def chart(df, show_rsi=True, overlays=None):

    fig = make_subplots(
        rows=3 if show_rsi else 2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.6,0.2,0.2] if show_rsi else [0.7,0.3],
        vertical_spacing=0.05
    )

    # PRICE
    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=df["Close"],
        name="Price",
        line=dict(color="black", width=2)
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
        marker_color="rgba(100,100,100,0.4)"
    ), row=2, col=1)

    # RSI
    if show_rsi:
        fig.add_trace(go.Scatter(
            x=df["Date"],
            y=df["RSI"],
            name="RSI",
            line=dict(color="purple")
        ), row=3, col=1)

        fig.add_hline(y=70, line_dash="dash", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", row=3, col=1)

    fig.update_layout(height=700, template="plotly_white")

    return fig

# =========================
# LAYOUT
# =========================

left, right = st.columns([1,3])

# =========================
# LEFT: GLASS GRID (NO BUTTONS)
# =========================

with left:

    st.subheader("Watchlist")

    grid = st.columns(3)

    for i, t in enumerate(WATCHLIST):

        df = ind(load(t))
        last = df.iloc[-1]
        prev = df.iloc[-2]

        chg = ((last["Close"] - prev["Close"]) / prev["Close"]) * 100

        color = "#dcfce7" if chg > 0 else "#fee2e2"

        active = "active" if t == st.session_state.selected else ""

        html = f"""
        <div class="glass {active}" style="background:{color}"
             onclick="window.location.href='?ticker={t}'">
            {t}<br>
            {round(chg,2)}%
        </div>
        """

        with grid[i % 3]:
            st.markdown(html, unsafe_allow_html=True)

# capture click via query param (Streamlit trick)
import streamlit as st
query = st.query_params

if "ticker" in query:
    st.session_state.selected = query["ticker"]

# =========================
# RIGHT: ANALYTICS
# =========================

t = st.session_state.selected

df = ind(load(t))
p = prob(df)

st.title(t)

c1,c2,c3,c4 = st.columns(4)

l = df.iloc[-1]

c1.metric("Price", round(l["Close"],2))
c2.metric("RSI", round(l["RSI"],1))
c3.metric("RVOL", round(l["RVOL"],2))
c4.metric("Prob%", round(p,1))

# controls
show_rsi = st.checkbox("Show RSI", value=True)
overlays = st.multiselect("Overlays", OVERLAYS, default=["EMA20","EMA50"])

st.plotly_chart(chart(df, show_rsi, overlays), use_container_width=True)

# =========================
# EDUCATION (RICH + STRUCTURED)
# =========================

with st.expander("📘 Deep Research Engine", expanded=True):

    st.markdown("### Trend Structure")

    trend = "Bullish" if l["EMA20"] > l["EMA50"] else "Bearish / Weak"

    st.write(f"Current regime: **{trend}**")

    st.markdown("### Momentum Interpretation")

    if l["RSI"] > 70:
        st.write("Overbought zone — risk of pullback increases")
    elif l["RSI"] < 30:
        st.write("Oversold — reversal probability rises")
    else:
        st.write("Neutral momentum zone")

    st.markdown("### Volume Behavior")

    if l["RVOL"] > 1.5:
        st.success("Strong participation (institutional activity likely)")
    else:
        st.write("Normal liquidity conditions")

    st.markdown("### Investment Thesis")

    if p > 70:
        st.success("High probability continuation setup (low-risk momentum trade)")
    elif p > 50:
        st.info("Moderate setup — wait for confirmation")
    else:
        st.warning("Weak setup — avoid or reduce size")

    st.markdown("### Key Risk Notes")

    st.write("- Trend break below EMA50 invalidates setup")
    st.write("- Low RVOL = false breakout risk")
    st.write("- RSI extremes require confirmation")
