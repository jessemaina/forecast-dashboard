import streamlit as st
from datetime import datetime, timedelta
import io
import contextlib

import pytz
import requests

def fetch_sun_times(date: str):
    lat = -31.8931
    lon = 115.952
    url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&date={date}&formatted=0"
    res = requests.get(url)
    res.raise_for_status()
    return res.json()["results"]
    

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
st.title("🌦️ Your Daily Forecast Assistant")
st.markdown(f"**Date:** {datetime.now().strftime('%A, %B %d, %Y')}")
st.markdown("---")

# === Get Data Once ===
data = fetch_weather()
now = datetime.now()

# === Outfit Renderer ===
def render_outfit_line(label, entry):
    outfit = outfit_logic(entry)
    temp = round(entry["apparent_temp"])
    rain = entry["rain"]
    showers = entry["showers"]

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

    items = outfit["Top"].split(", ") + outfit["Bottom"].split(", ") + outfit["Extras"].split(", ")
    cleaned = [item.strip().capitalize() for item in items if item.strip().lower() != "none"]

    outerwear = ["jacket", "hoodie", "jumper"]
    has_outerwear = any(any(k in item.lower() for k in outerwear) for item in cleaned)

    final = []
    for item in cleaned:
        if item.lower() == "t-shirt" and has_outerwear:
            continue
        if "thermal" in item.lower() and "Thermals" not in final:
            final.append("Thermals")
        elif "thermal" not in item.lower():
            final.append(item)

    st.markdown(f"**⏰ {label} {emojis} {temp}°**")
    st.markdown(", ".join(final) + ".")
    st.markdown("")

# === Layout Columns ===
col1, col2, col3 = st.columns(3)

# === Column 1: What to Wear Forecasts ===
with col1:
    st.subheader("🧥 What to Wear")

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
    else:
        st.caption("⚠️ No data available for current time")

    TIME_LABELS = {5: "5am Morning Walk", 12: "12pm Lunch", 21: "9pm Night Time"}
    count = 0
    max_forecasts = 6

    for day_offset in range(1, 5):
        for hour in [5, 12, 21]:
            dt = now.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=day_offset)
            if dt > now:
                entry = build_entry(data, dt)
                if "error" not in entry:
                    label = f"{TIME_LABELS[hour]} ({dt.strftime('%A')})"
                    render_outfit_line(label, entry)
                    count += 1
                if count >= max_forecasts:
                    break
        if count >= max_forecasts:
            break

    st.subheader("📅 7-Day Forecast")
    for i in range(7):
        date_str = data["daily"]["time"][i]
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        day_label = date_obj.strftime("%A")

        sunrise = data["daily"]["sunrise"][i][-5:]
        sunset = data["daily"]["sunset"][i][-5:]

        t_max = round(data["daily"]["temperature_2m_max"][i])
        t_min = round(data["daily"]["temperature_2m_min"][i])
        app_max = round(data["daily"]["apparent_temperature_max"][i])
        app_min = round(data["daily"]["apparent_temperature_min"][i])
        rain = round(data["daily"]["precipitation_sum"][i], 1)

        if rain > 5:
            emoji = "🌧️"
        elif rain > 1:
            emoji = "🌦️"
        elif t_max > 32:
            emoji = "🔥"
        elif t_max > 23:
            emoji = "☀️"
        elif t_max > 17:
            emoji = "🌤️"
        elif t_max < 13:
            emoji = "❄️"
        else:
            emoji = "🌥️"

        st.markdown(f"**{emoji} {day_label}**")
        st.markdown(f"- 🌅 **Sunrise**: {sunrise} | 🌇 **Sunset**: {sunset}")
        st.markdown(f"- 🌡️ **Max**: {t_max}° (Feels {app_max}°) | **Min**: {t_min}° (Feels {app_min}°)")
        st.markdown(f"- 🌧️ **Rain**: {rain} mm")
        st.markdown("")

# === Column 2: Clothesline Forecast ===
with col2:
    st.subheader("🧺 Clothesline Forecast")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        check_washing_days(data)
    st.text(buf.getvalue())

from datetime import timezone
import pytz

st.subheader("🌄 Twilight Times (Today)")

try:
    today_str = datetime.now().strftime("%Y-%m-%d")
    results = fetch_sun_times(today_str)
    perth_tz = pytz.timezone("Australia/Perth")

    def local(t): return datetime.fromisoformat(t).astimezone(perth_tz).strftime("%H:%M")

    st.markdown(f"- 🌅 **Sunrise**: {local(results['sunrise'])}")
    st.markdown(f"- 🌇 **Sunset**: {local(results['sunset'])}")
    st.markdown(f"- 🌤️ **Civil Twilight**: {local(results['civil_twilight_begin'])} → {local(results['civil_twilight_end'])}")
    st.markdown(f"- 🌊 **Nautical Twilight**: {local(results['nautical_twilight_begin'])} → {local(results['nautical_twilight_end'])}")
    st.markdown(f"- 🌌 **Astronomical Twilight**: {local(results['astronomical_twilight_begin'])} → {local(results['astronomical_twilight_end'])}")
except Exception as e:
    st.warning("Could not load twilight times.")


# === Column 3: Uber Demand Forecast ===
with col3:
    st.subheader("🚗 Uber Demand Forecast")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        generate_forecast(data)
    st.text(buf.getvalue())
