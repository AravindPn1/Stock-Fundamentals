import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

# =========================
# PAGE STYLE (LIGHT UI)
# =========================

st.set_page_config(layout="wide")

st.markdown("""
<style>
.stApp {
    background-color: #f7f9fc;
}
.block-container {
    padding-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Trading Research Desk")

# =========================
# DATA SETS
# =========================

WATCHLIST = ["AAPL","MSFT","NVDA","TSLA","AMZN","META","GOOGL","AMD","PLTR","NFLX","COIN","MSTR"]

HOT = ["SMCI","ARM","SNOW","NET","SHOP","RDDT","CRWD","AVGO"]

OVERLAYS = ["EMA20","EMA50","EMA200"]

# =========================
# LOAD DATA
# =========================

@st.cache_data(ttl=300)
def load(ticker):
    df = yf.download(ticker, period="2y", interval="1d", auto_adjust=True)
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

    vavg = df["Volume"].rolling(20).mean()
    df["RVOL"] = df["Volume"] / vavg

    return df.dropna()

# =========================
# ADVANCED PROBABILITY MODEL
# =========================

def probability(df, spy_df):

    last = df.iloc[-1]

    trend = 1 if last["EMA20"] > last["EMA50"] else 0
    strong_trend = 1 if last["EMA50"] > last["EMA200"] else 0

    momentum = 1 if 40 < last["RSI"] < 70 else 0

    vol_shock = 1 if last["RVOL"] > 1.5 else 0

    spy_align = 1 if spy_df["Close"].iloc[-1] < spy_df["Close"].iloc[-20] else 0

    score = (
        trend * 30 +
        strong_trend * 20 +
        momentum * 20 +
        vol_shock * 20 +
        spy_align * 10
    )

    return min(92, max(25, score))

# =========================
# SUMMARY
# =========================

def summarize(df, spy):

    last = df.iloc[-1]
    prev = df.iloc[-2]

    change = ((last["Close"] - prev["Close"]) / prev["Close"]) * 100

    prob = probability(df, spy)

    return {
        "price": round(last["Close"],2),
        "change": round(change,2),
        "rsi": round(last["RSI"],1),
        "rvol": round(last["RVOL"],2),
        "ema20": round(last["EMA20"],2),
        "ema50": round(last["EMA50"],2),
        "ema200": round(last["EMA200"],2),
        "prob": round(prob,1)
    }

# =========================
# CHART
# =========================

def chart(df, overlays):

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=df["Close"],
        name="Price",
        line=dict(color="#111827", width=2)
    ))

    if "EMA20" in overlays:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA20"], name="EMA20"))
    if "EMA50" in overlays:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA50"], name="EMA50"))
    if "EMA200" in overlays:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA200"], name="EMA200"))

    fig.update_layout(
        template="plotly_white",
        height=520,
        margin=dict(l=10,r=10,t=40,b=10)
    )

    return fig

# =========================
# SESSION
# =========================

if "selected" not in st.session_state:
    st.session_state.selected = "AAPL"

# =========================
# LAYOUT
# =========================

left, right = st.columns([1,3])

# =========================
# LEFT: COLOR CHECKERBOARD
# =========================

with left:

    st.subheader("📌 Watchlist")

    grid = st.columns(3)

    for i, t in enumerate(WATCHLIST):

        df = ind(load(t))
        spy = ind(load("SPY"))

        s = summarize(df, spy)

        bg = "#dcfce7" if s["change"] > 0 else "#fee2e2"

        with grid[i % 3]:

            st.markdown(
                f"""
                <div style="
                    padding:10px;
                    border-radius:10px;
                    background:{bg};
                    text-align:center;
                    margin-bottom:8px;
                ">
                <b>{t}</b><br>
                {s['change']}%
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button("Select", key=t):
                st.session_state.selected = t

    st.divider()

    st.subheader("🔥 Hot Movers")

    grid2 = st.columns(3)

    for i, t in enumerate(HOT):

        df = ind(load(t))
        spy = ind(load("SPY"))
        s = summarize(df, spy)

        bg = "#dcfce7" if s["change"] > 0 else "#fee2e2"

        with grid2[i % 3]:

            st.markdown(
                f"""
                <div style="
                    padding:10px;
                    border-radius:10px;
                    background:{bg};
                    text-align:center;
                    margin-bottom:8px;
                ">
                <b>{t}</b><br>
                {s['change']}%
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button("Trade", key=f"hot_{t}"):
                st.session_state.selected = t

# =========================
# RIGHT: RESEARCH ENGINE
# =========================

with right:

    t = st.session_state.selected

    df = ind(load(t))
    spy = ind(load("SPY"))

    s = summarize(df, spy)

    st.header(f"{t}")

    # =====================
    # METRICS
    # =====================

    c1,c2,c3,c4,c5,c6,c7 = st.columns(7)

    c1.metric("Price", s["price"])
    c2.metric("Change%", s["change"])
    c3.metric("RSI", s["rsi"])
    c4.metric("RVOL", s["rvol"])
    c5.metric("Prob%", s["prob"])
    c6.metric("EMA20", s["ema20"])
    c7.metric("EMA50/200", f"{s['ema50']} | {s['ema200']}")

    # =====================
    # CONTROLS
    # =====================

    overlays = st.multiselect(
        "Overlays",
        OVERLAYS,
        default=["EMA20","EMA50"]
    )

    st.plotly_chart(chart(df, overlays), use_container_width=True)

    # =====================
    # DEEP RESEARCH ENGINE
    # =====================

    with st.expander("🧠 Deep Thesis Engine", expanded=True):

        st.markdown("### Regime Detection")

        regime = "Trending Up" if s["ema20"] > s["ema50"] else "Weak / Transition"

        st.write(f"Market state: **{regime}**")

        st.markdown("### Momentum Quality")

        if s["rsi"] < 30:
            st.write("Deep oversold — reversal candidate")
        elif s["rsi"] > 70:
            st.write("Overheated — pullback risk elevated")
        else:
            st.write("Healthy momentum range")

        st.markdown("### Volume Behavior")

        if s["rvol"] > 1.5:
            st.success("Institutional participation detected")
        else:
            st.write("Normal participation")

        st.markdown("### Investment Thesis")

        if s["prob"] > 70:
            st.success("High probability continuation setup")
        elif s["prob"] > 50:
            st.info("Moderate setup — wait for confirmation")
        else:
            st.warning("Low quality setup — avoid entry")
