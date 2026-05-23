import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# =========================
# CONFIG
# =========================

WATCHLIST = [
    "AAPL","MSFT","NVDA","TSLA",
    "AMZN","META","GOOGL","AMD",
    "PLTR","NFLX","COIN","MSTR"
]

HOT = ["SMCI","ARM","SNOW","NET","SHOP","RDDT","CRWD","AVGO"]

OVERLAYS = ["EMA20", "EMA50", "EMA200"]

# =========================
# DATA
# =========================

@st.cache_data(ttl=300)
def load(ticker):
    df = yf.download(ticker, period="2y", interval="1d", auto_adjust=True)
    df = df.reset_index()
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df.dropna()

def add_ind(df):
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

def summarize(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    change = ((last["Close"] - prev["Close"]) / prev["Close"]) * 100

    score = 0
    if last["EMA20"] > last["EMA50"]:
        score += 1
    if last["RSI"] < 70:
        score += 1
    if last["RVOL"] > 1.5:
        score += 1

    prob = min(85, 35 + score * 15)

    return {
        "price": round(last["Close"],2),
        "change": round(change,2),
        "rsi": round(last["RSI"],1),
        "rvol": round(last["RVOL"],2),
        "prob": round(prob,1),
        "ema20": round(last["EMA20"],2),
        "ema50": round(last["EMA50"],2),
        "ema200": round(last["EMA200"],2)
    }

# =========================
# CHART
# =========================

def chart(df, ticker, overlays, show_spy):

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["Close"],
        name="Price", line=dict(color="black")
    ))

    if "EMA20" in overlays:
        fig.add_trace(go.Scatter(
            x=df["Date"], y=df["EMA20"],
            name="EMA20"
        ))

    if "EMA50" in overlays:
        fig.add_trace(go.Scatter(
            x=df["Date"], y=df["EMA50"],
            name="EMA50"
        ))

    if "EMA200" in overlays:
        fig.add_trace(go.Scatter(
            x=df["Date"], y=df["EMA200"],
            name="EMA200"
        ))

    if show_spy:
        spy = load("SPY")
        fig.add_trace(go.Scatter(
            x=spy["Date"], y=spy["Close"],
            name="SPY",
            opacity=0.4
        ))

    fig.update_layout(
        template="plotly_white",
        height=550,
        margin=dict(l=10,r=10,t=40,b=10),
        title=f"{ticker} — 2Y Chart"
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

left, right = st.columns([1, 3])

# =========================
# LEFT: CHECKERBOARD
# =========================

with left:

    st.subheader("Watchlist")

    grid = st.columns(3)

    for i, t in enumerate(WATCHLIST):

        df = add_ind(load(t))
        s = summarize(df)

        color = "🟢" if s["change"] >= 0 else "🔴"

        with grid[i % 3]:

            if st.button(f"{t} {color} {s['change']}%", key=t):
                st.session_state.selected = t

    st.divider()

    st.subheader("Hot Movers")

    grid2 = st.columns(3)

    for i, t in enumerate(HOT):

        df = add_ind(load(t))
        s = summarize(df)

        color = "🟢" if s["change"] >= 0 else "🔴"

        with grid2[i % 3]:

            if st.button(f"{t} {color} {s['change']}%", key=f"hot_{t}"):
                st.session_state.selected = t

# =========================
# RIGHT: RESEARCH
# =========================

with right:

    t = st.session_state.selected

    df = add_ind(load(t))
    s = summarize(df)

    st.header(f"{t}")

    # METRICS ROW
    m1,m2,m3,m4,m5,m6,m7 = st.columns(7)

    m1.metric("Price", s["price"])
    m2.metric("Change %", s["change"])
    m3.metric("RSI", s["rsi"])
    m4.metric("RVOL", s["rvol"])
    m5.metric("Prob%", s["prob"])
    m6.metric("EMA20", s["ema20"])
    m7.metric("EMA50/200", f"{s['ema50']} / {s['ema200']}")

    # CONTROLS
    st.subheader("Chart Controls")

    overlays = st.multiselect(
        "Overlays",
        OVERLAYS,
        default=["EMA20","EMA50"]
    )

    show_spy = st.checkbox("Overlay SPY", value=False)

    st.plotly_chart(
        chart(df, t, overlays, show_spy),
        use_container_width=True
    )

    # =========================
    # EDUCATION (RICH + NON-REPETITIVE)
    # =========================

    with st.expander("Research & Thesis (Deep)", expanded=True):

        st.markdown("### Market Structure")

        st.write(
            f"{t} is currently showing a "
            f"{'bullish' if s['ema20'] > s['ema50'] else 'bearish'} trend regime."
        )

        st.markdown("### Momentum Context")

        if s["rsi"] < 30:
            st.write("Oversold rebound setup potential.")
        elif s["rsi"] > 70:
            st.write("Overbought risk zone — momentum exhaustion possible.")
        else:
            st.write("Neutral momentum — continuation depends on volume confirmation.")

        st.markdown("### Volume Participation")

        if s["rvol"] > 1.5:
            st.write("Institutional participation likely increasing (high RVOL).")
        else:
            st.write("Normal participation — no breakout volume detected.")

        st.markdown("### Investment Thesis (Auto-Generated)")

        thesis_score = (
            (s["ema20"] > s["ema50"]) +
            (s["rsi"] < 70) +
            (s["rvol"] > 1.2)
        )

        if thesis_score >= 3:
            st.success("Strong trend continuation candidate (low-to-medium risk momentum setup).")
        elif thesis_score == 2:
            st.info("Mixed signals — tactical trade only, not conviction setup.")
        else:
            st.warning("Weak structure — avoid unless catalyst-driven.")

        st.markdown("### Risk Notes")

        st.write("- Always confirm breakout with volume expansion")
        st.write("- Avoid chasing extended RSI > 75 without pullback")
        st.write("- SPY correlation matters for macro regime")
