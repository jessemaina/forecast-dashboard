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

from datetime import datetime, timedelta

def get_hour_index(data, dt):
    print("🔍 Using updated get_hour_index")
    target = dt.replace(minute=0, second=0, microsecond=0)
    times = [datetime.strptime(t, "%Y-%m-%dT%H:%M") for t in data["hourly"]["time"]]
    closest_idx = min(range(len(times)), key=lambda i: abs(times[i] - target))
    return closest_idx if abs(times[closest_idx] - target) <= timedelta(hours=1) else None




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

    if not is_day:
        temp -= 2  # night-time chill factor

    top = []
    bottom = []
    extras = []

    # Thermals
    if temp < 15:
        top.append("Thermal")
        bottom.append("Thermal")

    # Top Layers
    if temp < 5:
        top += ["T-shirt", "Jumper", "Patagonia jacket"]
    elif temp < 10:
        top += ["T-shirt", "Jumper", "Hoodie"]
    elif temp < 15:
        top += ["T-shirt", "Jumper"]
    elif temp < 20:
        top += ["T-shirt", "Hoodie"]
    else:
        top += ["T-shirt"]

    # Bottom Layers
    if temp < 10:
        bottom += ["Track pants"]
    elif temp < 15:
        bottom += ["Shorts or light track pants"]
    else:
        bottom += ["Shorts"]

    # Rain
    if (rain > 0.3) or (showers > 0.3):
        extras.append("Rain jacket")

    # Wind
    if wind > 20 and temp < 15:
        extras.append("Windbreaker")

    # Cloudy and cold
    if cloud > 70 and temp < 15:
        extras.append("Maybe add scarf or thicker hoodie")

    # Cold accessories
    if temp < 10:
        extras += ["Beanie", "Gloves"]
    elif temp < 5:
        extras.append("Scarf")

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
