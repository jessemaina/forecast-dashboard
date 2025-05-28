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
        hour_data = get_hour_data(day_offset, h)
        score = 0.0
        reasons = []

        # Rule 1: Sudden temp drop
        try:
            past_avg = sum(forecast["temperature_2m"][(day_offset - 1) * 24 + h - 24 : (day_offset - 1) * 24 + h]) / 2
            if (
                forecast["temperature_2m"][day_offset * 24 + h] <= past_avg - 5
                and forecast["temperature_2m"][day_offset * 24 + h] < 12
            ):
                score += 2
                reasons.append("cold snap after warm days (+2)")
        except:
            pass

        # Rule 2: Cold spell after warm days
        try:
            warm_streak = all(
                t > 22 for t in forecast["temperature_2m"][(day_offset - 3) * 24 + h : (day_offset - 1) * 24 + h]
            )
            cold_now = all(forecast["apparent_temperature"][day_offset * 24 + h + i] < 13 for i in range(2))
            if warm_streak and cold_now:
                score += 2
                reasons.append("cold spell after warm streak (+2)")
        except:
            pass

        # Rule 3: Weekend rain after dry week
        if day_offset in [5, 6]:
            try:
                if all(
                    forecast["precipitation"][(day_offset - 3) * 24 + h : (day_offset) * 24 + h] < 0.5
                ) and forecast["precipitation"][day_offset * 24 + h] > 1.0:
                    score += 2
                    reasons.append("weekend rain after dry week (+2)")
            except:
                pass

        # Rule 4: Light to moderate rain during mealtimes
        if shift in ["lunch", "dinner"] and 0.5 <= hour_data["precip"] <= 3.0:
            score += 2
            reasons.append("moderate rain during meal window (+2)")

        # Rule 5: Heavy rain / wind = risk
        if hour_data["precip"] > 5.0 or hour_data["wind"] > 30:
            score -= 1
            reasons.append("heavy rain or wind disruption (–1)")

        # Rule 6: High evening demand temp + cloud
        if shift == "dinner" and 7 <= hour_data["apparent_temp"] <= 12 and hour_data["cloud"] > 50:
            score += 1.5
            reasons.append("evening chill + cloud (+1.5)")

        # Rule 7: Cold, calm morning
        if shift == "morning" and hour_data["temp"] < 13 and hour_data["wind"] < 15:
            score += 1.5
            reasons.append("cold, calm morning (+1.5)")

        # Rule 8: Humidity + dew discomfort
        if hour_data["humidity"] > 70 and hour_data["dew"] > 15:
            score += 1
            reasons.append("humidity discomfort (+1)")

        # Rule 9: Wind chill
        if (hour_data["temp"] - hour_data["apparent_temp"]) >= 3 and hour_data["wind"] > 20:
            score += 1
            reasons.append("wind chill effect (+1)")

        # Rule 10: Clear, mild midweek evening
        if shift in ["dinner", "late"]:
            if 17 <= hour_data["temp"] <= 22 and hour_data["cloud"] < 30 and hour_data["wind"] < 10:
                score -= 1
                reasons.append("mild clear evening (–1)")

        # Rule 11: Day-of-week overrides
        weekday = (base_date + datetime.timedelta(days=day_offset)).weekday()

        if shift == "dinner":
            if weekday == 4:
                score += 1
                reasons.append("Friday dinner baseline (+1)")
            if weekday == 5:
                score += 1
                reasons.append("Saturday dinner baseline (+1)")
            if weekday in [3, 4, 5] and (hour_data["temp"] < 18 or hour_data["precip"] > 0.3):
                score += 1.5
                reasons.append("Thu–Sat weather-assisted (+1.5)")

        if shift == "late":
            if weekday == 1:
                score += 1
                reasons.append("Tuesday fatigue (+1)")
            if weekday in [4, 5]:
                score += 0.5
                reasons.append("weekend late-night vibe (+0.5)")

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

