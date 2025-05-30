import datetime

def generate_forecast(data):
    forecast = data["hourly"]
    base_time = datetime.datetime.strptime(forecast["time"][0], "%Y-%m-%dT%H:%M")
    base_time = base_time.replace(tzinfo=datetime.timezone.utc)

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

    def assess_shift(day_offset, shift):
        hour_lookup = {
            "morning": 6,
            "lunch": 12,
            "dinner": 18,
            "late": 22
        }
        h = hour_lookup[shift]
        data = get_hour_data(day_offset, h)
        score_demand = 0
        score_supply = 0
        reasons = []

        # 📈 Demand signals
        if data["precip"] > 3:
            score_demand += 2
            reasons.append("heavy rain")
        elif data["precip"] > 1:
            score_demand += 1.5
            reasons.append("moderate rain")

        if data["wind"] > 30:
            score_demand += 1
            reasons.append("strong wind")

        if data["apparent_temp"] < 10:
            score_demand += 1
            reasons.append("cold feels")

        # 🧍‍♂️ Supply suppression (drivers don't want to work)
        if data["precip"] > 3 or data["wind"] > 40:
            score_supply -= 1
            reasons.append("driver deterrent: storm")

        if data["wind"] > 25 and data["temp"] < 13:
            score_supply -= 0.5
            reasons.append("driver deterrent: windchill")

        # 🔁 Baseline demand by time/week
        weekday = (base_time + datetime.timedelta(days=day_offset)).weekday()
        if shift == "dinner":
            if weekday in [4, 5]:  # Friday/Saturday
                score_demand += 1
                reasons.append("weekend dinner")
        if shift == "late" and weekday == 5:
            score_demand += 1
            score_supply -= 0.5
            reasons.append("Saturday late surge")

        return score_demand, score_supply, reasons

    def label(score):
        if score >= 3:
            return "🤑🤑 Very High"
        elif score >= 2:
            return "🤑 High"
        elif score >= 1:
            return "📈 Moderate"
        else:
            return "💤 Low"

    for day_offset in range(7):
        date = (base_time + datetime.timedelta(days=day_offset)).strftime("%A")
        print(f"{date}")
        for shift in ["morning", "lunch", "dinner", "late"]:
            d, s, reasons = assess_shift(day_offset, shift)
            net = d - s  # net opportunity for driver
            print(f"- {shift.title()}: Demand: {label(d)} | Drivers: {label(-s)} → Opportunity: {label(net)}")
            if reasons:
                print(f"  • Factors: {', '.join(reasons)}")
        print("")
