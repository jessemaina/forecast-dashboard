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

    def assess_opportunity(day_offset, shift):
        hours = {
            "morning": 6,
            "lunch": 12,
            "dinner": 18,
            "late": 22,
        }
        h = hours[shift]
        hour_data = get_hour_data(day_offset, h)
        weekday = (base_date + datetime.timedelta(days=day_offset)).weekday()

        score = 0.0
        reasons = []

        # 🌧️ Wet weather = people stay home
        if hour_data["precip"] > 5.0:
            score += 2.5
            reasons.append("heavy rain (+2.5)")
        elif 1.0 < hour_data["precip"] <= 5.0:
            score += 1.5
            reasons.append("moderate rain (+1.5)")
        elif hour_data["precip"] > 0.2:
            score += 1
            reasons.append("light rain (+1)")

        # 💨 Wind amplifies cold or deters going out
        if hour_data["wind"] > 35:
            score += 2
            reasons.append("gale-force wind (+2)")
        elif hour_data["wind"] > 20:
            score += 1
            reasons.append("strong wind (+1)")

        # ❄️ Cold snaps increase comfort food cravings
        if hour_data["apparent_temp"] < 10:
            score += 2
            reasons.append("very cold apparent temp (+2)")
        elif hour_data["apparent_temp"] < 15:
            score += 1
            reasons.append("cold apparent temp (+1)")

        # 🔥 Extreme heat = too hot to cook
        if hour_data["temp"] > 40:
            score += 2
            reasons.append("oppressively hot (+2)")
        elif hour_data["temp"] > 34:
            score += 1.5
            reasons.append("very hot afternoon (+1.5)")

        # 🌫️ Humidity makes people sluggish
        if hour_data["humidity"] > 75 and hour_data["dew"] > 18:
            score += 1
            reasons.append("humid and sticky (+1)")

        # ☁️ Cloud cover adds to 'stay in' vibes
        if hour_data["cloud"] > 70:
            score += 0.5
            reasons.append("heavy cloud cover (+0.5)")

        # 🗓️ Cultural & day-based factors
        if shift == "dinner":
            if weekday == 4:
                score += 2
                reasons.append("Friday dinner peak (+2)")
            elif weekday == 5:
                score += 2
                reasons.append("Saturday dinner peak (+2)")
            elif weekday == 3:
                score += 1
                reasons.append("Thursday dinner (+1)")

        if shift == "late":
            if weekday == 5:
                score += 1.5
                reasons.append("Saturday late rush (+1.5)")
            elif weekday == 4:
                score += 1
                reasons.append("Friday late rush (+1)")
            elif weekday == 1:
                score += 0.5
                reasons.append("Monday hangover craving (+0.5)")

        if shift == "morning" and hour_data["temp"] < 10 and hour_data["wind"] < 10:
            score += 1.5
            reasons.append("cold, calm morning cravings (+1.5)")

        # ⛱️ Perfect weather = slight drop
        if 19 <= hour_data["temp"] <= 26 and hour_data["cloud"] < 30 and hour_data["wind"] < 10 and hour_data["precip"] < 0.1:
            score -= 1
            reasons.append("pleasant outdoor weather (–1)")

        return score, reasons

    for day_offset in range(0, 7):
        date = (base_date + datetime.timedelta(days=day_offset)).strftime("%A")
        print(f"{date}")
        for shift in ["morning", "lunch", "dinner", "late"]:
            score, reasons = assess_opportunity(day_offset, shift)
            if score >= 4:
                label = "💸💸 High Opportunity"
            elif score >= 2.5:
                label = "💸 Good Opportunity"
            elif score >= 1:
                label = "🤍 Moderate Opportunity"
            else:
                label = "💤 Low Opportunity"

            reason_str = f" → ({', '.join(reasons)})" if reasons else ""
            print(f"- {shift.title()}: {label}{reason_str}")
        print("")
