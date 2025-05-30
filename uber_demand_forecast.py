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

        # 🌧️ Rain boosts demand
        if hour_data["precip"] > 4.0:
            score += 2.5
            reasons.append("heavy rain (+2.5)")
        elif 0.7 < hour_data["precip"] <= 4.0:
            score += 1.5
            reasons.append("moderate rain (+1.5)")
        elif hour_data["precip"] > 0.2:
            score += 1
            reasons.append("light rain (+1)")

        # 💨 Wind
        if hour_data["wind"] > 30:
            score += 2
            reasons.append("strong wind (+2)")
        elif hour_data["wind"] > 18:
            score += 1
            reasons.append("breezy night (+1)")

        # ❄️ Cold
        if hour_data["apparent_temp"] < 9:
            score += 2
            reasons.append("freezing apparent temp (+2)")
        elif hour_data["apparent_temp"] < 14:
            score += 1
            reasons.append("chilly apparent temp (+1)")

        # 🔥 Heat
        if hour_data["temp"] > 39:
            score += 2
            reasons.append("extreme heat (+2)")
        elif hour_data["temp"] > 33:
            score += 1.5
            reasons.append("very hot afternoon (+1.5)")

        # 🌫️ Humidity
        if hour_data["humidity"] > 70 and hour_data["dew"] > 17:
            score += 1
            reasons.append("sticky air (+1)")

        # ☁️ Cloud
        if hour_data["cloud"] > 65:
            score += 0.75
            reasons.append("heavy cloud cover (+0.75)")
        elif hour_data["cloud"] > 40:
            score += 0.5
            reasons.append("overcast (+0.5)")

        # 🗓️ Time-of-week bonuses
        if shift == "dinner":
            if weekday == 4:
                score += 2
                reasons.append("Friday dinner (+2)")
            elif weekday == 5:
                score += 2
                reasons.append("Saturday dinner (+2)")
            elif weekday == 3:
                score += 1.25
                reasons.append("Thursday dinner (+1.25)")

        if shift == "late":
            if weekday == 5:
                score += 1.5
                reasons.append("Saturday late crowd (+1.5)")
            elif weekday == 4:
                score += 1.25
                reasons.append("Friday late rush (+1.25)")
            elif weekday == 1:
                score += 0.75
                reasons.append("Monday cravings (+0.75)")

        if shift == "morning" and hour_data["temp"] < 11 and hour_data["wind"] < 10:
            score += 1.25
            reasons.append("cold calm morning (+1.25)")

        # ⛱️ Pleasant weather penalty softened
        if 20 <= hour_data["temp"] <= 27 and hour_data["cloud"] < 30 and hour_data["wind"] < 10 and hour_data["precip"] < 0.1:
            score -= 0.5
            reasons.append("pleasant weather (–0.5)")

        return score, reasons

    for day_offset in range(0, 7):
        date = (base_date + datetime.timedelta(days=day_offset)).strftime("%A")
        print(f"{date}")
        for shift in ["morning", "lunch", "dinner", "late"]:
            score, reasons = assess_opportunity(day_offset, shift)
            if score >= 4:
                label = "💸💸 High Opportunity"
            elif score >= 2:
                label = "💸 Good Opportunity"
            elif score >= 0.75:
                label = "🤍 Moderate Opportunity"
            else:
                label = "💤 Low Opportunity"

            reason_str = f" → ({', '.join(reasons)})" if reasons else ""
            print(f"- {shift.title()}: {label}{reason_str}")
        print("")
