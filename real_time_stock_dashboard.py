import yfinance as yf
import pandas as pd
import sqlite3
import streamlit as st
import time
from datetime import datetime

# ------------------------
# Streamlit Page Config
# ------------------------
st.set_page_config(page_title="🚀 Real-Time Stock Dashboard", layout="wide")
st.title("🚀 Real-Time Stock/Financial Dashboard (Simulated)")

# ------------------------
# User Inputs
# ------------------------
ticker = st.text_input("Enter Stock Symbol (e.g. TSLA, AAPL, RELIANCE.BSE):", "TSLA")
refresh_interval = st.slider("Refresh Interval (seconds)", 5, 60, 10)

# ------------------------
# SQLite Setup
# ------------------------
conn = sqlite3.connect("real_time_stocks.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS stock_live (
    datetime TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL
)
""")
conn.commit()

# ------------------------
# Streamlit Placeholders
# ------------------------
price_placeholder = st.empty()
line_chart_placeholder = st.empty()
volume_chart_placeholder = st.empty()

# ------------------------
# Real-Time Simulation Loop
# ------------------------
if st.button("Start Real-Time Tracking"):
    st.success(f"Tracking {ticker} every {refresh_interval}s ...")
    
    while True:
        try:
            # Fetch last 1 day intraday data (1-min interval)
            stock = yf.download(tickers=ticker, period="1d", interval="1m", progress=False)

            if stock.empty:
                st.warning("❌ No data available. Check ticker symbol.")
                break

            # Flatten columns if MultiIndex
            if isinstance(stock.columns, pd.MultiIndex):
                stock.columns = [col[0] for col in stock.columns]

            # Take latest tick
            latest_row = stock.tail(1)
            dt = latest_row.index[0].to_pydatetime()
            open_price = float(latest_row["Open"].iloc[0])
            high_price = float(latest_row["High"].iloc[0])
            low_price = float(latest_row["Low"].iloc[0])
            close_price = float(latest_row["Close"].iloc[0])
            volume = float(latest_row["Volume"].iloc[0])

            # Insert into SQLite
            cursor.execute("""
                INSERT INTO stock_live(datetime, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (dt, open_price, high_price, low_price, close_price, volume))
            conn.commit()

            # Read last 50 records for dashboard
            df = pd.read_sql("SELECT * FROM stock_live ORDER BY datetime DESC LIMIT 50", conn)
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.sort_values("datetime")

            # ------------------------
            # Dashboard Metrics
            # ------------------------
            price_placeholder.metric(
                "Latest Price", 
                f"${close_price:.2f}", 
                delta=f"{close_price - open_price:.2f}"
            )

            # Price Line Chart
            line_chart_placeholder.line_chart(df.set_index("datetime")["close"])

            # Volume Bar Chart
            volume_chart_placeholder.bar_chart(df.set_index("datetime")["volume"])

            # Sleep for refresh_interval seconds
            time.sleep(refresh_interval)

        except Exception as e:
            st.error(f"Error: {e}")
            break
