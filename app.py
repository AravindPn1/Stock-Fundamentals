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
# WATCHLISTS
# =========================

WATCHLIST = ["AAPL","MSFT","NVDA","TSLA","AMZN","META","GOOGL","AMD","PLTR","NFLX","COIN","MSTR"]
HOT = ["SMCI","ARM","SNOW","NET","SHOP","RDDT","CRWD","AVGO"]

# =========================
# STYLE (REDUCED WHITESPACE LEFT)
# =========================

st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg,#f8fafc,#eef2ff,#f1f5f9);
}

/* LEFT PANEL COMPACT */
.leftBox {
    background: rgba(255,255,255,0.85);
    border-radius: 18px;
    padding: 6px;
    height: 92vh;
    overflow: hidden;
}

/* TILE */
.tile {
    padding: 8px;
    border-radius: 14px;
    text-align: center;
    font-weight: 600;
    color: white;
    margin: 2px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.12);
    cursor: pointer;
}

/* TEXT SMALLER */
.small {
    font-size: 12px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# CHART (UNCHANGED)
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
# LEFT PANEL (FIXED - NO BUTTONS ANYWHERE)
# =========================

with left:

    st.markdown("<div class='leftBox'>", unsafe_allow_html=True)

    st.markdown("### 📊 Watchlist")

    def render_grid(lst):

        cols = st.columns(3)

        for i, t in enumerate(lst):

            df = ind(load(t))
            last = df.iloc[-1]
            prev = df.iloc[-2]

            chg = ((last["Close"] - prev["Close"]) / prev["Close"]) * 100
            color = "#22c55e" if chg > 0 else "#ef4444"

            # TILE ONLY (NO BUTTONS)
            with cols[i % 3]:

                clicked = st.container()

                with clicked:
                    if st.markdown(
                        f"""
                        <div class="tile" style="background:{color}">
                            {t}<br>
                            <span class="small">{chg:.2f}%</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    ):
                        pass

                # CLICK HANDLER (STREAMLIT SAFE)
                if st.checkbox("", key=f"sel_{t}"):
                    st.session_state.ticker = t

    render_grid(WATCHLIST)

    st.markdown("### 🔥 Hot Movers")
    render_grid(HOT)

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# RIGHT PANEL (UNCHANGED LOGIC)
# =========================

t = st.session_state.ticker
df = ind(load(t))
last = df.iloc[-1]

with right:

    st.markdown(f"# 📈 {t}")

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Price", round(last["Close"],2))
    c2.metric("RSI", round(last["RSI"],1))
    c3.metric("RVOL", round(last["RVOL"],2))
    c4.metric("Trend", "Bullish" if last["EMA20"] > last["EMA50"] else "Bearish")

    st.plotly_chart(chart(df), use_container_width=True)

    with st.expander("🧠 Thesis", expanded=True):
        st.write("""
- EMA structure defines regime
- RSI defines momentum pressure
- RVOL defines participation
- Combine all → trade bias
""")
