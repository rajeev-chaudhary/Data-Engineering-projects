import yfinance as yf
import pandas as pd
import sqlite3
import streamlit as st
import datetime

st.set_page_config(page_title="📊 Stock Dashboard", layout="wide")

st.title("📈 Robust Stock/Financial Dashboard")

# Input
ticker = st.text_input("Enter Stock Symbol (e.g. AAPL, TSLA, RELIANCE.BSE):", "TSLA")
start_date = st.date_input("Start Date", datetime.date(2024, 1, 1))
end_date = st.date_input("End Date", datetime.date.today())

if st.button("Get Stock Data"):
    # Download
    stock = yf.download(ticker, start=start_date, end=end_date, progress=False)

    if stock.empty:
        st.error("❌ No data found. Try another symbol.")
        st.stop()

    # Flatten columns if multi-index
    if isinstance(stock.columns, pd.MultiIndex):
        stock.columns = [col[0] for col in stock.columns]

    # Ensure required columns exist
    required_cols = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    for col in required_cols:
        if col not in stock.columns:
            stock[col] = pd.NA  # Fill missing columns

    stock.reset_index(inplace=True)

    # Moving Averages only if Close exists
    if "Close" in stock.columns:
        stock["MA20"] = stock["Close"].rolling(20).mean()
        stock["MA50"] = stock["Close"].rolling(50).mean()
    else:
        st.warning("⚠ 'Close' column missing, skipping moving averages.")

    # SQLite
    conn = sqlite3.connect("stocks.db")
    with conn:
        stock.to_sql("stock_data", conn, if_exists="replace", index=False)

    # Dashboard
    st.subheader(f"📊 Stock Data for {ticker}")
    st.dataframe(stock.tail(20))

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📉 Closing Price Trend")
        if "Close" in stock.columns:
            st.line_chart(stock.set_index("Date")[["Close", "MA20", "MA50"]])
        else:
            st.info("No Close price available for chart.")

    with col2:
        st.subheader("📦 Trading Volume Trend")
        st.bar_chart(stock.set_index("Date")["Volume"])

    # Summary
    st.subheader("📑 Key Statistics")
    if not stock["Close"].isna().all():
        latest = stock.iloc[-1]
        st.write({
            "Last Close": latest.get("Close"),
            "20-Day Avg": latest.get("MA20"),
            "50-Day Avg": latest.get("MA50"),
            "Highest Price": stock["High"].max(),
            "Lowest Price": stock["Low"].min(),
            "Total Volume": stock["Volume"].sum()
        })
    else:
        st.info("No Close price data to calculate statistics.")

    st.success("✅ Stock Dashboard Ready!")
