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

    top = []
    bottom = []
    extras = []
    
    # === OVERRIDES ===

    # 1. Extreme cold, wet, windy, dark
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

    # 3. Cool & wet night (your common use case)
    if not is_day and temp <= 21 and (rain > 0.2 or showers > 0.2 or cloud > 70):
        return {
            "Top": "Thermals, Jumper or hoody, Rain jacket",
            "Bottom": "Trackies",
            "Extras": "None"
        }

    # Apply chill factor for night
    if not is_day:
        temp -= 2

    # === BASED ON TEMP RANGE ===

    # Bottoms
    if temp < 17:
        bottom.append("Thermals")
        bottom.append("Trackies")
    elif temp < 23:
        bottom.append("Trackies")
    else:
        bottom.append("Shorts")

    # Tops
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

    # === WEATHER-BASED EXTRAS ===

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

def display_outfit(time_label, entry):
    print(f"\nTime: {time_label}")
    outfit = outfit_logic(entry)
    for key, val in outfit.items():
        print(f"→ {key}: {val}")

def describe_weather(entry):
    parts = []

    temp = entry["apparent_temp"]
    humidity = entry["humidity"]
    wind = entry["wind"]
    rain = entry["rain"]
    showers = entry["showers"]
    cloud = entry["cloud"]

    # Temperature
    if temp < 10:
        parts.append("very cold")
    elif temp < 14:
        parts.append("cold")
    elif temp < 18:
        parts.append("cool")
    elif temp < 25:
        parts.append("mild")
    elif temp < 33:
        parts.append("warm")
    else:
        parts.append("hot")

    # Rain / showers
    if rain > 2 or showers > 2:
        parts.append("moderate rain")
    elif rain > 0.5 or showers > 0.5:
        parts.append("light showers")
    elif rain > 0 or showers > 0:
        parts.append("drizzle")
    else:
        parts.append("dry")

    # Wind
    if wind > 35:
        parts.append("strong winds")
    elif wind > 20:
        parts.append("breezy")
    elif wind > 10:
        parts.append("light breeze")
    else:
        parts.append("calm")

    # Cloud
    if cloud > 90:
        parts.append("very overcast")
    elif cloud > 70:
        parts.append("overcast")
    elif cloud > 40:
        parts.append("partly cloudy")
    else:
        parts.append("mostly clear")

    return f"Conditions: {temp:.1f}°C apparent, {humidity}% humidity, {wind:.1f}km/h wind, {rain + showers:.1f}mm precip, {cloud}% cloud ({', '.join(parts)})."

def display_outfit(time_label, entry):
    print(f"\n⏰ {time_label}")
    outfit = outfit_logic(entry)
    for key, val in outfit.items():
        print(f"→ {key}: {val}")
    print(describe_weather(entry))


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
