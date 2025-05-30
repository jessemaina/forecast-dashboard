import requests
from datetime import datetime, timedelta

# === CONFIG ===
API_URL = "https://api.open-meteo.com/v1/forecast?latitude=-31.893106844411854&longitude=115.952&daily=sunrise,sunset,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum&hourly=temperature_2m,rain,precipitation,apparent_temperature,relative_humidity_2m,dew_point_2m,showers,cloud_cover,wind_speed_10m,is_day&current=temperature_2m,is_day,rain,showers,precipitation&timezone=auto"

KEY_HOURS = [5, 12, 21]

# === FETCH & PARSE ===
def fetch_weather():
    res = requests.get(API_URL)
    res.raise_for_status()
    return res.json()

def get_hour_index(data, dt):
    target_str = dt.strftime("%Y-%m-%dT%H:00")
    if target_str in data["hourly"]["time"]:
        return data["hourly"]["time"].index(target_str)
    return None

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

    reasons = []

    # === OVERRIDES ===
    if not is_day and wind > 25 and (rain > 0.3 or showers > 0.3) and temp < 20:
        reasons.append("Nighttime + cold + windy + rain → Miserable override")
        return {
            "Top": "Thermal, Jumper, Waterproof jacket",
            "Bottom": "Track pants",
            "Extras": "Beanie, Gloves, Windbreaker, Rain jacket",
            "Reasons": "; ".join(reasons)
        }

    if temp > 35 and humidity > 40:
        reasons.append("Oppressively hot and humid → Heat override")
        return {
            "Top": "Light singlet",
            "Bottom": "Shorts",
            "Extras": "Sunglasses, Cold water bottle, Apply sunscreen",
            "Reasons": "; ".join(reasons)
        }

    if is_day and 18 <= temp <= 23 and wind > 15 and cloud > 60:
        reasons.append("Chilly daylight trap: overcast, windy → Needs coverage")
        return {
            "Top": "Long-sleeve or Hoodie",
            "Bottom": "Jeans or Track pants",
            "Extras": "Optional Windbreaker",
            "Reasons": "; ".join(reasons)
        }

    # === NIGHT CORRECTION ===
    if not is_day:
        temp -= 2
        reasons.append("Night-time temp adjustment (–2°C)")

    top = []
    bottom = []
    extras = []

    # === THERMALS & LAYERS ===
    if temp < 13:
        top.append("Thermal")
        bottom.append("Thermal")
        reasons.append("Very cold (<13°C) → Thermals")

    if temp < 17:
        top.append("Jumper")
        reasons.append("Cool (<17°C) → Jumper")

    if temp >= 30:
        top.append("T-shirt or Singlet")
        reasons.append("Hot (≥30°C) → T-shirt or Singlet")
    elif 20 <= temp < 30:
        top.append("T-shirt")
        reasons.append("Mild (20–29°C) → T-shirt")
    else:
        top.append("Long-sleeve shirt")
        reasons.append("Cool (<20°C) → Long-sleeve")

    # === BOTTOMS ===
    if temp >= 25:
        bottom.append("Shorts")
        reasons.append("Warm (≥25°C) → Shorts")
    elif 17 <= temp < 25:
        bottom.append("Jeans")
        reasons.append("Mild (17–24°C) → Jeans")
    else:
        bottom.append("Track pants")
        reasons.append("Cool (<17°C) → Track pants")

    # === EXTRAS ===
    if rain > 0.3 or showers > 0.3:
        extras.append("Rain jacket")
        reasons.append("Rain detected → Rain jacket")

    if wind > 25:
        extras.append("Windbreaker")
        reasons.append("Strong wind (>25 km/h) → Windbreaker")

    if temp < 10 or (temp < 13 and wind > 30):
        extras.extend(["Beanie", "Gloves"])
        reasons.append("Bitter cold or wind chill → Beanie & Gloves")

    if humidity > 70 and temp >= 24:
        extras.append("Breathable fabrics")
        reasons.append("High humidity + warmth → Breathable needed")

    if cloud > 80 and 16 <= temp <= 20:
        top.append("Extra layer (cloud chill)")
        reasons.append("Overcast and cool → Feels colder")

    return {
        "Top": ", ".join(top),
        "Bottom": ", ".join(bottom),
        "Extras": ", ".join(extras) if extras else "None",
        "Reasons": "; ".join(reasons)
    }



def display_outfit(time_label, entry):
    print(f"\nTime: {time_label}")
    outfit = outfit_logic(entry)
    for key, val in outfit.items():
        print(f"→ {key}: {val}")

# === CLOTHESLINE FORECAST ===
def check_washing_days(data):
    print("\nClothesline Forecast (Next 7 Days):")
    daily = data["daily"]
    for i in range(7):
        date_str = daily["time"][i]
        rain = daily["precipitation_sum"][i]

        # Convert string to datetime, get weekday name
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        weekday = date_obj.strftime("%A")

        if rain == 0:
            print(f"👕 {weekday} ({date_str}): Good day to hang washing")
        else:
            print(f"🌧️ {weekday} ({date_str}): Rain expected — bring washing in")

# === MAIN ===
def main():
    data = fetch_weather()
    now = datetime.now()

    # RIGHT NOW
    current_idx = get_hour_index(data, now.replace(minute=0, second=0, microsecond=0))
    if current_idx is not None:
        current_entry = {
            "apparent_temp": data["hourly"]["apparent_temperature"][current_idx],
            "humidity": data["hourly"]["relative_humidity_2m"][current_idx],
            "rain": data["hourly"]["rain"][current_idx],
            "showers": data["hourly"]["showers"][current_idx],
            "precip": data["hourly"]["precipitation"][current_idx],
            "wind": data["hourly"]["wind_speed_10m"][current_idx],
            "cloud": data["hourly"]["cloud_cover"][current_idx],
            "is_day": bool(data["hourly"]["is_day"][current_idx]),
        }
        display_outfit("Right Now", current_entry)

    # TODAY AND TOMORROW
    for offset in [0, 1]:
        label = "Today" if offset == 0 else "Tomorrow"
        for hour in [5, 12, 21]:
            dt = now.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=offset)
            entry = build_entry(data, dt)
            if "error" not in entry:
                display_outfit(f"{hour:02}:00 ({label})", entry)

    # CLOTHESLINE FORECAST
    check_washing_days(data)

# === RUN ===
if __name__ == "__main__":
    main()
