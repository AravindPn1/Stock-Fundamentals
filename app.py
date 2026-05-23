import streamlit as st

st.set_page_config(layout="wide")

st.title("Trading Research Desk")

st.success("App boot successful")

ticker = st.selectbox(
"Ticker",
["AAPL", "MSFT", "NVDA", "TSLA"]
)

st.subheader(ticker)

c1, c2, c3, c4 = st.columns(4)

with c1:
st.metric("Price", "$100")

with c2:
st.metric("RSI", "58")

with c3:
st.metric("RVOL", "1.8")

with c4:
st.metric("Prob %", "67")

st.line_chart(
[1, 2, 3, 2, 5, 4, 6]
)

with st.expander("Educational Insights"):

```
st.write(
    "EMA20 above EMA50 indicates bullish trend structure."
)

st.write(
    "RSI below 70 suggests continuation room remains."
)

st.write(
    "Elevated RVOL indicates participation expansion."
)
```

