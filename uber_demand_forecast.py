import datetime

def generate_forecast(data):
    from_zone = datetime.timezone.utc
    forecast = data["hourly"]
    base_date = datetime.datetime.strptime(forecast["time"][0], "%Y-%m-%dT%H:%M")
    base_date = base_date.replace(tzinfo=from_zone)

    def get_hour_data(day_offset, hour):
        idx = day_offset * 24 + hour
        return {
            "time": forecast["time"][idx],
            "temp": forecast["temperature_2m"][idx],
            "apparent_temp": forecast["apparent_temperature"][idx],
            "humidity": forecast["relative_humidity_2m"][idx],
            "dew": forecast["dew_point_2m"][idx],
            "rain": forecast["rain"][idx],
            "precip": forecast["precipitation"][idx],
            "wind": forecast["wind_speed_10m"][idx],
            "cloud": forecast["cloud_cover"][idx],
        }

def assess_shift_conditions(day_offset, shift):
    hours = {
        "morning": 6,
        "lunch": 12,
        "dinner": 18,
        "late": 22,
    }
    h = hours[shift]
    idx = day_offset * 24 + h
    hour_data = get_hour_data(day_offset, h)

    score = 0.0
    reasons = []

    # 🚗 Weather-driven demand boosts (bad weather = good for drivers)
    if hour_data["precip"] > 3.0:
        score += 2
        reasons.append("heavy rain (+2)")
    elif 0.5 < hour_data["precip"] <= 3.0:
        score += 1.5
        reasons.append("moderate rain (+1.5)")

    if hour_data["wind"] > 30:
        score += 1
        reasons.append("strong wind (+1)")

    if hour_data["temp"] < 13 and hour_data["wind"] > 15:
        score += 1.5
        reasons.append("cold + windy (+1.5)")

    # 🌡️ Unpleasant chill boosts demand
    if hour_data["apparent_temp"] < 10:
        score += 1
        reasons.append("very cold apparent temp (+1)")

    # 🌫️ Humidity discomfort = stay home
    if hour_data["humidity"] > 70 and hour_data["dew"] > 15:
        score += 1
        reasons.append("humidity discomfort (+1)")

    # 💸 Time-of-week baselines
    weekday = (base_date + datetime.timedelta(days=day_offset)).weekday()

    if shift == "dinner":
        if weekday == 4:
            score += 1.5
            reasons.append("Friday dinner baseline (+1.5)")
        elif weekday == 5:
            score += 1.5
            reasons.append("Saturday dinner baseline (+1.5)")
        elif weekday == 3:
            score += 1
            reasons.append("Thursday dinner baseline (+1)")

    if shift == "late":
        if weekday == 5:
            score += 1.5
            reasons.append("Saturday late-night baseline (+1.5)")
        elif weekday == 4:
            score += 1
            reasons.append("Friday late-night baseline (+1)")
        elif weekday == 1:
            score += 0.5
            reasons.append("Tuesday fatigue orders (+0.5)")

    # ❌ Calm pleasant weather = low urgency
    if 17 <= hour_data["temp"] <= 23 and hour_data["cloud"] < 40 and hour_data["wind"] < 10 and hour_data["precip"] < 0.1:
        score -= 1
        reasons.append("pleasant clear evening (–1)")

    return score, reasons


    for day_offset in range(0, 7):
        date = (base_date + datetime.timedelta(days=day_offset)).strftime("%A")
        print(f"{date}")
        for shift in ["morning", "lunch", "dinner", "late"]:
            score, reasons = assess_shift_conditions(day_offset, shift)
            if score >= 3:
                label = "💸💸 Demand Highly Likely"
            elif score >= 2:
                label = "💸 Demand Likely"
            elif score >= 0.5:
                label = "🤍 Neutral"
            else:
                label = "💤 Demand Slump"

            reason_str = f" → ({', '.join(reasons)})" if reasons else ""
            print(f"- {shift.title()}: {label}{reason_str}")
        print("")

