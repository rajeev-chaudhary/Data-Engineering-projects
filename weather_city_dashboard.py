import requests
import pandas as pd
import sqlite3
import streamlit as st

st.set_page_config(page_title="🌍 Weather Dashboard", layout="wide")

# ------------------------
# Step 1: User Input City
# ------------------------
st.title("🌤 Advanced Weather Dashboard")
city = st.text_input("Enter City Name", "Delhi")

if st.button("Get Weather Data"):
    # ------------------------
    # Step 2: Get Latitude & Longitude from Open-Meteo Geocoding API
    # ------------------------
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    geo_resp = requests.get(geo_url).json()

    if "results" not in geo_resp:
        st.error("❌ City not found. Please try again.")
        st.stop()

    lat = geo_resp["results"][0]["latitude"]
    lon = geo_resp["results"][0]["longitude"]
    cname = geo_resp["results"][0]["name"]
    country = geo_resp["results"][0]["country"]

    st.success(f"📍 Location found: {cname}, {country} (Lat: {lat}, Lon: {lon})")

    # ------------------------
    # Step 3: Fetch Weather Forecast (Hourly Temp + Humidity)
    # ------------------------
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,precipitation"
    weather_resp = requests.get(weather_url).json()

    times = weather_resp["hourly"]["time"]
    temps = weather_resp["hourly"]["temperature_2m"]
    humidity = weather_resp["hourly"]["relative_humidity_2m"]
    precip = weather_resp["hourly"]["precipitation"]

    df = pd.DataFrame({
        "Datetime": pd.to_datetime(times),
        "Temp (°C)": temps,
        "Humidity (%)": humidity,
        "Precipitation (mm)": precip
    })

    # ------------------------
    # Step 4: Load into SQLite
    # ------------------------
    conn = sqlite3.connect("weather_city.db")
    with conn:
        df.to_sql("forecast", conn, if_exists="replace", index=False)

    # ------------------------
    # Step 5: Dashboard
    # ------------------------
    st.subheader(f"📊 Weather Forecast for {cname}, {country}")

    st.dataframe(df.head(20))

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🌡 Temperature Trend")
        st.line_chart(df.set_index("Datetime")["Temp (°C)"])

    with col2:
        st.subheader("💧 Humidity Trend")
        st.line_chart(df.set_index("Datetime")["Humidity (%)"])

    st.subheader("☔ Precipitation Forecast")
    st.bar_chart(df.set_index("Datetime")["Precipitation (mm)"])

    st.success("✅ Weather Dashboard Ready!")
