import requests
from datetime import datetime, timedelta

# === CONFIG ===
API_URL = (
    "https://api.open-meteo.com/v1/forecast?"
    "latitude=-31.893106844411854&longitude=115.952&daily=sunrise,sunset,temperature_2m_max,"
    "temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum&"
    "hourly=temperature_2m,rain,precipitation,apparent_temperature,relative_humidity_2m,"
    "dew_point_2m,showers,cloud_cover,wind_speed_10m,is_day&current=temperature_2m,"
    "is_day,rain,showers,precipitation&timezone=auto"
)

KEY_HOURS = [5, 12, 21]

# === FETCH & PARSE ===
def fetch_weather():
    res = requests.get(API_URL)
    res.raise_for_status()
    return res.json()

def get_hour_index(data, dt):
    target_str = dt.strftime("%Y-%m-%dT%H:00")
    return data["hourly"]["time"].index(target_str) if target_str in data["hourly"]["time"] else None

def build_entry(data, hour_dt):
    idx = get_hour_index(data, hour_dt)
    if idx is None:
        return {"error": "No data"}
    return {
        "apparent_temp": data["hourly"]["apparent_temperature"][idx],
        "humidity": data["hourly"]["relative_humidity_2m"][idx],
        "rain": data["hourly"]["rain"][idx],
        "showers": data["hourly"]["showers"][idx],
        "precip": data["hourly"]["precipitation"][idx],
        "wind": data["hourly"]["wind_speed_10m"][idx],
        "cloud": data["hourly"]["cloud_cover"][idx],
        "is_day": bool(data["hourly"]["is_day"][idx]),
    }

# === OUTFIT LOGIC ===
def outfit_logic(entry):
    temp = entry["apparent_temp"]
    humidity = entry["humidity"]
    wind = entry["wind"]
    rain = entry["rain"]
    showers = entry["showers"]
    cloud = entry["cloud"]
    is_day = entry["is_day"]

    top = []
    bottom = []
    extras = []

    # === OVERRIDES ===

    # 1. Miserable cold, wet, windy night
    if not is_day and temp < 13 and (rain > 0.3 or showers > 0.3) and wind > 25:
        return {
            "Top": "Thermals, Thick jumper or hoody, Rain jacket or Windbreaker",
            "Bottom": "Thermals, Trackies",
            "Extras": "Beanie, Gloves"
        }

    # 2. Oppressive heat
    if temp > 35 and humidity > 40:
        return {
            "Top": "T-shirt or Singlet",
            "Bottom": "Shorts",
            "Extras": "Sunglasses, Cold water bottle, Apply sunscreen"
        }

    # 3. Damp, cool night
    if not is_day and temp <= 21 and (rain > 0.2 or showers > 0.2 or cloud > 70):
        return {
            "Top": "Thermals, Jumper or hoody, Rain jacket",
            "Bottom": "Trackies",
            "Extras": "None"
        }

    # Adjust for night chill
    if not is_day:
        temp -= 2

    # === TEMPERATURE-BASED ===
    if temp < 17:
        bottom.append("Thermals")
        bottom.append("Trackies")
    elif temp < 23:
        bottom.append("Trackies")
    else:
        bottom.append("Shorts")

    if temp < 13:
        top.append("Thermals")
        top.append("Thick jumper or hoody")
        top.append("Warm jacket")
    elif temp < 17:
        top.append("Thermals")
        top.append("Jumper or hoody")
    elif temp < 22:
        top.append("T-shirt")
        top.append("Jumper or hoody")
    elif temp < 27:
        top.append("T-shirt")
    else:
        top.append("T-shirt or Singlet")

    # === WEATHER EXTRAS ===
    if rain > 0.3 or showers > 0.3:
        extras.append("Rain jacket")
    elif wind > 25:
        extras.append("Windbreaker")

    if temp < 10 or (temp < 13 and wind > 30):
        extras.append("Beanie")
        extras.append("Gloves")

    return {
        "Top": ", ".join(top),
        "Bottom": ", ".join(bottom),
        "Extras": ", ".join(extras) if extras else "None"
    }

# === WEATHER DESCRIPTION ===
def describe_weather(entry):
    temp = entry["apparent_temp"]
    humidity = entry["humidity"]
    wind = entry["wind"]
    rain = entry["rain"]
    showers = entry["showers"]
    cloud = entry["cloud"]

    total_precip = rain + showers

    return (
        f"🌡️ {temp:.1f}°C  💧 {humidity}% humidity  💨 {wind:.1f}km/h wind  "
        f"🌧️ {total_precip:.1f}mm precip  ☁️ {cloud}% cloud"
    )


# === DISPLAY OUTFIT ===
def display_outfit(time_label, entry):
    print(f"\n⏰ {time_label}")
    outfit = outfit_logic(entry)
    for key, val in outfit.items():
        print(f"→ {key}: {val}")
    print(describe_weather(entry))

# === CLOTHESLINE FORECAST ===
def check_washing_days(data):
    print("\nClothesline Forecast (Next 7 Days):")
    for i in range(7):
        date_str = data["daily"]["time"][i]
        rain = data["daily"]["precipitation_sum"][i]
        weekday = datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
        if rain == 0:
            print(f"👕 {weekday} ({date_str}): Good day to hang washing")
        else:
            print(f"🌧️ {weekday} ({date_str}): Rain expected — bring washing in")

# === MAIN ===
def main():
    data = fetch_weather()
    now = datetime.now()

    # Right now
    current_idx = get_hour_index(data, now.replace(minute=0, second=0, microsecond=0))
    if current_idx is not None:
        current_entry = build_entry(data, now.replace(minute=0, second=0, microsecond=0))
        display_outfit("Right Now", current_entry)

    # Forecast for today and tomorrow
    for offset in [0, 1]:
        label = "Today" if offset == 0 else "Tomorrow"
        for hour in KEY_HOURS:
            dt = now.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=offset)
            entry = build_entry(data, dt)
            if "error" not in entry:
                display_outfit(f"{hour:02}:00 ({label})", entry)

    check_washing_days(data)

if __name__ == "__main__":
    main()
