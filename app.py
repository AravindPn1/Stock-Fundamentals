import streamlit as st

st.set_page_config(layout="wide")

st.title("Stock Research Dashboard")

ticker = st.selectbox(
    "Select Ticker",
    ["AAPL", "MSFT", "NVDA", "TSLA"]
)

st.header(ticker)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Price", "$100")

with col2:
    st.metric("RSI", "58")

with col3:
    st.metric("RVOL", "1.8")

with col4:
    st.metric("Prob %", "67")

st.line_chart([1, 2, 3, 4, 5, 4, 6])

with st.expander("Education"):
    st.write("EMA20 above EMA50 = bullish structure")
    st.write("RSI < 70 = momentum not exhausted")
    st.write("RVOL > 1.5 = participation expansion")
