```python
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Trading Research Desk",
    layout="wide"
)

# =====================================================
# STATE
# =====================================================

WATCHLIST = [
    "AAPL","MSFT","NVDA","TSLA",
    "META","AMZN","GOOGL","AMD",
    "PLTR","NFLX","AVGO","CRWD"
]

HOT_STOCKS = [
    "SMCI","COIN","MSTR","ARM",
    "SNOW","SHOP","NET","RDDT"
]

if "selected" not in st.session_state:
    st.session_state.selected = WATCHLIST[0]

# =====================================================
# LOAD DATA
# =====================================================

@st.cache_data(ttl=300)
def load_data(ticker):

    try:

        df = yf.download(
            ticker,
            period="2y",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False
        )

        if df.empty:
            return pd.DataFrame()

        df = df.reset_index()

        # flatten multiindex columns
        clean_cols = []

        for c in df.columns:

            if isinstance(c, tuple):
                clean_cols.append(c[0])
            else:
                clean_cols.append(c)

        df.columns = clean_cols

        needed = [
            "Date",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]

        for col in needed:

            if col not in df.columns:
                return pd.DataFrame()

        for col in [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

        df = df.dropna()

        return df

    except:
        return pd.DataFrame()

# =====================================================
# INDICATORS
# =====================================================

def add_indicators(df):

    if df.empty:
        return df

    df = df.copy()

    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()
    df["EMA200"] = df["Close"].ewm(span=200).mean()

    delta = df["Close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    rs = gain.rolling(14).mean() / loss.rolling(14).mean()

    df["RSI"] = 100 - (100 / (1 + rs))

    vol_avg = df["Volume"].rolling(20).mean()

    df["RVOL"] = np.where(
        vol_avg > 0,
        df["Volume"] / vol_avg,
        0
    )

    return df.dropna()

# =====================================================
# SUMMARY
# =====================================================

def summarize(df):

    if len(df) < 5:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    change = (
        (float(last["Close"]) - float(prev["Close"]))
        / float(prev["Close"])
    ) * 100

    score = 0

    if last["EMA20"] > last["EMA50"]:
        score += 1

    if last["RSI"] < 70:
        score += 1

    if last["RVOL"] > 1.5:
        score += 1

    prob = min(85, max(20, 40 + score * 12))

    return {
        "price": round(float(last["Close"]), 2),
        "change": round(float(change), 2),
        "rsi": round(float(last["RSI"]), 1),
        "rvol": round(float(last["RVOL"]), 2),
        "ema20": round(float(last["EMA20"]), 2),
        "ema50": round(float(last["EMA50"]), 2),
        "ema200": round(float(last["EMA200"]), 2),
        "prob": round(float(prob), 1)
    }

# =====================================================
# CHART
# =====================================================

def make_chart(df, ticker):

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Close"],
            name="Price"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["EMA20"],
            name="EMA20"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["EMA50"],
            name="EMA50"
        )
    )

    fig.update_layout(
        template="plotly_white",
        height=550,
        title=f"{ticker} — 2Y Chart"
    )

    return fig

# =====================================================
# LAYOUT
# =====================================================

left, right = st.columns([1,2])

# =====================================================
# LEFT PANEL
# =====================================================

with left:

    st.subheader("Watchlist")

    cols = st.columns(2)

    for idx, ticker in enumerate(WATCHLIST):

        df = add_indicators(load_data(ticker))

        if df.empty:
            continue

        s = summarize(df)

        if s is None:
            continue

        with cols[idx % 2]:

            color = "🟩" if s["change"] >= 0 else "🟥"

            st.markdown(
                f"""
                ### {color} {ticker}

                ${s['price']}

                {s['change']}%
                """
            )

            if st.button(
                f"Select {ticker}",
                key=ticker
            ):
                st.session_state.selected = ticker

    st.divider()

    st.subheader("Hot Stocks")

    hot_cols = st.columns(2)

    for idx, ticker in enumerate(HOT_STOCKS):

        with hot_cols[idx % 2]:

            if st.button(
                f"🔥 {ticker}",
                key=f"hot_{ticker}"
            ):
                st.session_state.selected = ticker

# =====================================================
# RIGHT PANEL
# =====================================================

with right:

    ticker = st.session_state.selected

    raw = load_data(ticker)

    if raw.empty:

        st.error("Unable to load ticker")

    else:

        df = add_indicators(raw)

        s = summarize(df)

        if s is not None:

            st.header(ticker)

            m1,m2,m3,m4,m5,m6,m7 = st.columns(7)

            metrics = [
                ("Price", s["price"]),
                ("RSI", s["rsi"]),
                ("RVOL", s["rvol"]),
                ("Prob %", s["prob"]),
                ("EMA20", s["ema20"]),
                ("EMA50", s["ema50"]),
                ("EMA200", s["ema200"])
            ]

            for col, item in zip(
                [m1,m2,m3,m4,m5,m6,m7],
                metrics
            ):

                with col:
                    st.metric(
                        item[0],
                        item[1]
                    )

            st.plotly_chart(
                make_chart(df, ticker),
                use_container_width=True
            )

            with st.expander(
                "Research & Educational Insights",
                expanded=True
            ):

                st.write(
                    "EMA20 above EMA50 suggests constructive trend alignment."
                )

                st.write(
                    "RSI below 70 suggests momentum is not yet technically overextended."
                )

                st.write(
                    "RVOL above 1.5 indicates elevated participation."
                )

                st.write(
                    "Probability model currently uses trend + momentum + volume confirmation."
                )

                st.write(
                    "Future upgrades can include volatility regime detection, earnings proximity, options flow, and sector-relative strength."
                )
```
