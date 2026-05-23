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

if "ticker" not in st.session_state:
    st.session_state.ticker = "AAPL"

# =========================
# DATA
# =========================

@st.cache_data(ttl=300)
def load(t):
    df = yf.download(t, period="2y", interval="1d", auto_adjust=True)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()

    for c in ["Open","High","Low","Close","Volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return df.dropna()

def ind(df):
    df = df.copy()

    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()
    df["EMA200"] = df["Close"].ewm(span=200).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + rs))

    df["VOL_MA"] = df["Volume"].rolling(20).mean()
    df["RVOL"] = np.where(df["VOL_MA"] == 0, 0, df["Volume"] / df["VOL_MA"])

    return df.dropna()

# =========================
# DATASETS
# =========================

WATCHLIST = ["AAPL","MSFT","NVDA","TSLA","AMZN","META","GOOGL","AMD","PLTR","NFLX","COIN","MSTR"]
HOT = ["SMCI","ARM","SNOW","NET","SHOP","RDDT","CRWD","AVGO"]

# =========================
# STYLE (CLEAN + LIGHT + POP)
# =========================

st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg,#f8fafc,#eef2ff,#f1f5f9);
}

/* LEFT PANEL */
.leftPane {
    background: rgba(255,255,255,0.9);
    border-radius: 18px;
    padding: 10px;
    height: 92vh;
}

/* TILE LOOK */
.tile {
    padding: 10px;
    border-radius: 16px;
    text-align: center;
    font-weight: 700;
    color: white;
    margin: 4px;
    cursor: pointer;
    box-shadow: 0 6px 14px rgba(0,0,0,0.12);
}

/* RADIO HIDE BULLETS */
div[role="radiogroup"] > label {
    background: transparent !important;
}

/* RIGHT PANEL */
.rightPane {
    background: rgba(255,255,255,0.92);
    border-radius: 18px;
    padding: 16px;
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

    fig.update_layout(height=600, template="plotly")

    return fig

# =========================
# LAYOUT
# =========================

left, right = st.columns([1.05, 3])

# =========================
# LEFT PANEL (FIXED STRUCTURE)
# =========================

with left:

    st.markdown("<div class='leftPane'>", unsafe_allow_html=True)

    st.markdown("### 📊 Watchlist")

    def tile_options(lst):

        options = lst
        labels = []

        for t in lst:
            df = ind(load(t))
            last = df.iloc[-1]
            prev = df.iloc[-2]

            chg = ((last["Close"] - prev["Close"]) / prev["Close"]) * 100
            labels.append(f"{t}  |  {chg:.2f}%")

        choice = st.radio(
            " ",
            options=options,
            format_func=lambda x: labels[options.index(x)],
            label_visibility="collapsed"
        )

        return choice

    st.session_state.ticker = tile_options(WATCHLIST)

    st.markdown("### 🔥 Hot Movers")

    hot_choice = tile_options(HOT)
    if hot_choice:
        st.session_state.ticker = hot_choice

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# RIGHT PANEL
# =========================

t = st.session_state.ticker
df = ind(load(t))
last = df.iloc[-1]

with right:

    st.markdown(f"<div class='rightPane'>", unsafe_allow_html=True)

    st.markdown(f"# 📈 {t}")

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Price", round(last["Close"],2))
    c2.metric("RSI", round(last["RSI"],1))
    c3.metric("RVOL", round(last["RVOL"],2))
    c4.metric("Trend", "Bullish" if last["EMA20"] > last["EMA50"] else "Bearish")

    st.plotly_chart(chart(df), use_container_width=True)

    with st.expander("🧠 Investment Thesis", expanded=True):
        st.markdown("""
### Structure
- EMA alignment defines regime
- RSI defines momentum pressure
- Volume defines conviction

### Interpretation
- Trend-following when EMA20 > EMA50
- Mean reversion when RSI extreme
- Breakout confirmation requires RVOL spike

### Risk
- EMA200 breakdown = structural failure
- Low volume = false breakout risk
""")

    st.markdown("</div>", unsafe_allow_html=True)
