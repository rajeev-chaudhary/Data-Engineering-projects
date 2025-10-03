import yfinance as yf
import pandas as pd
import sqlite3
import streamlit as st
import datetime

st.set_page_config(page_title="📊 Multi-Stock Comparative Dashboard", layout="wide")
st.title("📈 Multi-Stock Comparative Dashboard + Analytics (Fixed)")

# ------------------------
# User Inputs
# ------------------------
tickers_input = st.text_input(
    "Enter Stock Symbols (comma separated, e.g. TSLA,AAPL,RELIANCE.BSE):", 
    "TSLA,AAPL"
)
tickers = [t.strip().upper() for t in tickers_input.split(",")]

start_date = st.date_input("Start Date", datetime.date(2024, 1, 1))
end_date = st.date_input("End Date", datetime.date.today())

if st.button("Fetch & Compare"):

    if len(tickers) < 2:
        st.warning("⚠ Enter at least 2 stock symbols for comparison.")
        st.stop()

    # ------------------------
    # Fetch Data
    # ------------------------
    data_dict = {}
    for ticker in tickers:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if df.empty:
            st.warning(f"No data for {ticker}. Skipping...")
            continue
        df.reset_index(inplace=True)
        
        # Flatten MultiIndex if exists
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]

        df["Ticker"] = ticker
        df["MA20"] = df["Close"].rolling(20).mean()
        df["MA50"] = df["Close"].rolling(50).mean()
        df["Close"] = df["Close"].astype(float)
        data_dict[ticker] = df

    if not data_dict:
        st.error("No valid data fetched. Exiting.")
        st.stop()

    # ------------------------
    # Store in SQLite
    # ------------------------
    conn = sqlite3.connect("multi_stocks.db")
    for ticker, df in data_dict.items():
        df.to_sql(f"stock_{ticker}", conn, if_exists="replace", index=False)

    # ------------------------
    # Combine for Dashboard
    # ------------------------
    combined = pd.concat(data_dict.values(), ignore_index=True)

    # Ensure 'Close' column is float
    combined["Close"] = combined["Close"].astype(float)

    # ------------------------
    # Closing Price Comparison
    # ------------------------
    st.subheader("📉 Closing Price Trend (Multi-Stock)")
    try:
        price_df = combined.pivot(index="Date", columns="Ticker", values="Close")
        st.line_chart(price_df)
    except Exception as e:
        st.error(f"Error in pivoting Close prices: {e}")

    # ------------------------
    # Volume Comparison
    # ------------------------
    st.subheader("📦 Volume Trend")
    try:
        volume_df = combined.pivot(index="Date", columns="Ticker", values="Volume")
        st.bar_chart(volume_df)
    except Exception as e:
        st.error(f"Error in pivoting Volume: {e}")

    # ------------------------
    # Correlation Matrix
    # ------------------------
    st.subheader("📊 Closing Price Correlation")
    try:
        corr = price_df.corr()
        st.dataframe(corr)
    except Exception as e:
        st.error(f"Error computing correlation: {e}")

    # ------------------------
    # Returns Comparison (%)
    # ------------------------
    st.subheader("📈 Daily Returns Comparison (%)")
    try:
        returns = price_df.pct_change() * 100
        st.line_chart(returns)
    except Exception as e:
        st.error(f"Error computing returns: {e}")

    # ------------------------
    # Moving Average Crossover Signals
    # ------------------------
    st.subheader("⚡ Moving Average Crossover Signals")
    signals = {}
    for ticker, df in data_dict.items():
        df = df.copy()
        df["Signal"] = 0
        df.loc[df["MA20"] > df["MA50"], "Signal"] = 1
        df.loc[df["MA20"] < df["MA50"], "Signal"] = -1
        signals[ticker] = df[["Date", "Close", "MA20", "MA50", "Signal"]].tail(10)
    
    for ticker, sig_df in signals.items():
        st.write(f"**{ticker}** last 10 signals")
        st.dataframe(sig_df)
    
    st.success("✅ Multi-Stock Dashboard Ready!")
