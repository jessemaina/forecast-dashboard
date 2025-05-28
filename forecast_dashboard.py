import streamlit as st
from datetime import datetime, timedelta
import io
import contextlib

# === Import your logic ===
from what_to_wear import (
    fetch_weather,
    outfit_logic,
    get_hour_index,
    build_entry,
    check_washing_days
)
from uber_demand_forecast import generate_forecast

# === Streamlit Page Config ===
st.set_page_config(page_title="Weather Dashboard", layout="wide")

# === Header ===
st.title("🌦️ Forecast")
st.markdown(f"**Date:** {datetime.now().strftime('%A, %B %d, %Y')}")
st.markdown("---")

# === Get Data Once ===
data = fetch_weather()
now = datetime.now()

# === Smart, Clean Outfit Renderer ===
def render_outfit_line(label, entry):
    outfit = outfit_logic(entry)
    temp = round(entry["apparent_temp"])
    rain = entry["rain"]
    showers = entry["showers"]

    # Emoji logic
    emojis = ""
    if temp < 7:
        emojis += "❄️❄️❄️"
    elif temp < 12:
        emojis += "❄️❄️"
    elif temp < 17:
        emojis += "❄️"

    if temp > 32:
        emojis += "☀️☀️☀️"
    elif temp > 23:
        emojis += "☀️☀️"
    elif temp > 18:
        emojis += "☀️"

    if rain > 0.3 or showers > 0.3:
        emojis += " 🌧️"

    # Flatten and filter clothing items
    all_items = outfit["Top"].split(", ") + outfit["Bottom"].split(", ") + outfit["Extras"].split(", ")
    cleaned = [item.strip().capitalize() for item in all_items if item.strip().lower() != "none"]

    # Normalize: Remove 'T-shirt' if also wearing jacket, hoodie, or jumper
    outerwear_keywords = ["jacket", "hoodie", "jumper"]
    has_outerwear = any(any(k in item.lower() for k in outerwear_keywords) for item in cleaned)
    final_items = []
    for item in cleaned:
        if item.lower() == "t-shirt" and has_outerwear:
            continue
        if "thermal" in item.lower() and "Thermals" not in final_items:
            final_items.append("Thermals")
        elif "thermal" not in item.lower():
            final_items.append(item)

    # Output block
    st.markdown(f"**⏰ {label} {emojis} {temp}°**")
    st.markdown(", ".join(final_items) + ".")
    st.markdown("")

# === Layout Columns ===
col1, col2, col3 = st.columns(3)

# === Column 1: What to Wear Forecasts ===
with col1:
    st.subheader("🧥 What to Wear")

    # Right Now
    idx = get_hour_index(data, now.replace(minute=0, second=0, microsecond=0))
    if idx is not None:
        entry = {
            "apparent_temp": data["hourly"]["apparent_temperature"][idx],
            "humidity": data["hourly"]["relative_humidity_2m"][idx],
            "rain": data["hourly"]["rain"][idx],
            "showers": data["hourly"]["showers"][idx],
            "precip": data["hourly"]["precipitation"][idx],
            "wind": data["hourly"]["wind_speed_10m"][idx],
            "cloud": data["hourly"]["cloud_cover"][idx],
            "is_day": bool(data["hourly"]["is_day"][idx]),
        }
        render_outfit_line("Right Now", entry)

    # Future 6 time blocks
    TIME_LABELS = {5: "5am Morning Walk", 12: "12pm Lunch", 21: "9pm Night Time"}
    hours_to_check = [5, 12, 21]
    count = 0
    max_forecasts = 6

    for day_offset in range(1, 5):
        for hour in hours_to_check:
            dt = now.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=day_offset)
            if dt > now:
                entry = build_entry(data, dt)
                if "error" not in entry:
                    time_label = f"{TIME_LABELS[hour]} ({dt.strftime('%A')})"
                    render_outfit_line(time_label, entry)
                    count += 1
                if count >= max_forecasts:
                    break
        if count >= max_forecasts:
            break

# === Column 2: Clothesline Forecast ===
with col2:
    st.subheader("🧺 Clothesline Forecast")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        check_washing_days(data)
    st.text(buf.getvalue())

# === Column 3: Uber Demand Forecast ===
with col3:
    st.subheader("🚗 Uber Demand Forecast")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        generate_forecast(data)
    st.text(buf.getvalue())
