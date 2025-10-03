import pandas as pd
import sqlite3
import re
import streamlit as st
import requests
from io import StringIO

# ------------------------
# Step 1: Download Open-Source Log File
# ------------------------
# Linux Academy sample Apache log file (public dataset)
url = "https://raw.githubusercontent.com/linuxacademy/content-elastic-log-samples/master/access.log"
response = requests.get(url)
log_text = response.text

# Save locally also (optional)
with open("access.log", "w", encoding="utf-8") as f:
    f.write(log_text)

lines = log_text.splitlines()

# ------------------------
# Step 2: Parse Apache Logs
# ------------------------
pattern = r'(\d+\.\d+\.\d+\.\d+) - - \[(.*?)\] "(.*?)" (\d{3}) (\d+|-)'

data = []
for line in lines:
    m = re.match(pattern, line)
    if m:
        ip = m.group(1)
        ts = m.group(2)
        req = m.group(3)
        status = int(m.group(4))
        size_str = m.group(5)
        size = int(size_str) if size_str != "-" else 0
        data.append([ip, ts, req, status, size])

df = pd.DataFrame(data, columns=["IP", "Timestamp", "Request", "Status", "Size"])

# Convert timestamp → datetime
df["Timestamp"] = pd.to_datetime(df["Timestamp"], format="%d/%b/%Y:%H:%M:%S %z", errors="coerce")

# Drop rows where timestamp parse failed
df = df.dropna(subset=["Timestamp"])

# ------------------------
# Step 3: Load into SQLite
# ------------------------
conn = sqlite3.connect("log_open.db")
with conn:
    df.to_sql("access_logs", conn, if_exists="replace", index=False)

# ------------------------
# Step 4: Dashboard with Streamlit
# ------------------------
st.title("📁 Log File Dashboard (Open-Source Access Logs)")

# Show sample data
st.subheader("🔹 Sample Logs")
st.write(df.head())

# Status Code Distribution
st.subheader("🔹 Status Code Distribution")
status_counts = df["Status"].value_counts().reset_index()
status_counts.columns = ["Status", "Count"]
st.bar_chart(status_counts.set_index("Status"))

# Top IPs
st.subheader("🔹 Top 10 IP Addresses")
ip_ct = df["IP"].value_counts().head(10).reset_index()
ip_ct.columns = ["IP", "Count"]
st.bar_chart(ip_ct.set_index("IP"))

# Requests Over Time (by hour)
st.subheader("🔹 Requests by Hour")
df["Hour"] = df["Timestamp"].dt.hour
hour_ct = df.groupby("Hour").size().reset_index(name="Requests")
st.line_chart(hour_ct.set_index("Hour"))

st.success("✅ Dashboard Ready with Open-Source Logs")
