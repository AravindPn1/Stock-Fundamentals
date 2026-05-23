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
# DATA (SAFE)
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
# UI (LIGHT FINTECH STYLE)
# =========================

st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg,#f8fafc,#eef2ff,#f1f5f9);
    color: #0f172a;
    font-size: 13px;
}

/* TILE STYLE */
.tile {
    padding: 10px;
    border-radius: 14px;
    text-align: center;
    font-weight: 600;
    cursor: pointer;
    margin: 3px;
    color: white;
    transition: 0.15s;
    box-shadow: 0 6px 14px rgba(0,0,0,0.15);
}

.tile:hover {
    transform: scale(1.03);
}

/* ACTIVE */
.active {
    outline: 2px solid #0ea5e9;
}

/* LEFT PANEL BOX */
.panel {
    background: rgba(255,255,255,0.75);
    border-radius: 18px;
    padding: 10px;
    height: 92vh;
    overflow: hidden;
}

/* RIGHT PANEL */
.right {
    background: rgba(255,255,255,0.9);
    border-radius: 18px;
    padding: 16px;
}

/* HEADERS */
h1,h2,h3 {
    color: #0f172a;
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
# LEFT / RIGHT LAYOUT (LOCKED)
# =========================

left, right = st.columns([1.05, 3])

# =========================
# LEFT PANEL (NO SCROLL GRID)
# =========================

with left:

    st.markdown("## 📊 Market Explorer")

    st.markdown("<div class='panel'>", unsafe_allow_html=True)

    def tile_grid(title, lst):

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

                # TILE CLICK ONLY (NO BUTTONS SHOWN)
                if st.button("", key=f"{t}_click"):
                    st.session_state.ticker = t

    tile_grid("Watchlist", WATCHLIST)
    tile_grid("Hot Movers", HOT)

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# RIGHT PANEL
# =========================

t = st.session_state.ticker
df = ind(load(t))
last = df.iloc[-1]

with right:

    st.markdown(f"# 📈 {t} Research Terminal")

    # TOP METRICS
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Price", round(last["Close"],2))
    c2.metric("RSI", round(last["RSI"],1))
    c3.metric("RVOL", round(last["RVOL"],2))
    c4.metric("Trend", "Bullish" if last["EMA20"] > last["EMA50"] else "Bearish")

    st.plotly_chart(chart(df), use_container_width=True)

    # =========================
    # COLLAPSIBLE EDUCATION SYSTEM
    # =========================

    with st.expander("🧠 1. Market Structure & Trend Regime", expanded=True):
        st.markdown(f"""
- EMA20 vs EMA50 → short-term direction
- EMA50 vs EMA200 → macro regime
- Current regime: **{'Bullish' if last['EMA20'] > last['EMA50'] else 'Bearish'}**

👉 Interpretation:
This determines whether we are in:
- Trend continuation phase
- Or distribution / reversal phase
""")

    with st.expander("📊 2. Momentum Analysis (RSI)", expanded=False):
        st.markdown(f"""
- RSI Value: **{last['RSI']:.2f}**
- Overbought > 70
- Oversold < 30

👉 Meaning:
- High RSI = exhaustion risk
- Low RSI = rebound opportunity
- Mid RSI = trend continuation zone
""")

    with st.expander("📦 3. Volume & Institutional Activity", expanded=False):
        st.markdown(f"""
- RVOL: **{last['RVOL']:.2f}**

👉 Interpretation:
- > 1.5 = institutional participation
- < 1.0 = weak conviction
- Spikes often precede breakouts or reversals
""")

    with st.expander("🎯 4. Investment Thesis (AI-style synthesis)", expanded=True):

        regime = "BULLISH" if last["EMA20"] > last["EMA50"] else "BEARISH"
        strength = "STRONG" if last["EMA50"] > last["EMA200"] else "WEAK"

        st.markdown(f"""
### Current Setup
- Regime: **{regime}**
- Strength: **{strength}**
- Momentum: **{last['RSI']:.1f} RSI**
- Participation: **{last['RVOL']:.2f} RVOL**

---

### Thesis Summary

This asset is currently in a:
> **{regime} + {strength} structured regime**

### Trade Bias:
- Trend-following preferred when EMA alignment holds
- Mean reversion only when RSI extremes occur
- Volume confirmation required for breakout conviction

---

### Risk Framework:
- RSI extremes → reversal risk
- EMA200 break → structural breakdown
- RVOL drop → weakening conviction
""")
