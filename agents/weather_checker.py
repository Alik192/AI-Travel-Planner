import os
import requests
from dotenv import load_dotenv
from typing import Optional

# ... (load_dotenv and OPENWEATHER_API_KEY are the same) ...
load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


def get_weather_forecast(city: str, country_code: str = "") -> str:
    # ... (docstring is the same) ...
    if not OPENWEATHER_API_KEY:
        return "Error: OpenWeatherMap API key is not set."

    try:
        # --- MODIFICATION: Build the query string conditionally ---
        query = city
        if country_code:
            query += f",{country_code}"

        # Step 1: Get city coordinates (geocoding)
        geo_url = (
            f"http://api.openweathermap.org/geo/1.0/direct?q={query}"
            f"&limit=1&appid={OPENWEATHER_API_KEY}"
        )
        geo_response = requests.get(geo_url)
        geo_response.raise_for_status()
        geo_data = geo_response.json()

        if not geo_data or "lat" not in geo_data[0]:
            return f"Error: Could not find coordinates for the city '{city}'."

        # ... (The rest of the file is the same) ...
        lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]

        # Step 2: Get 7-day forecast data
        weather_url = (
            f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}"
            f"&units=metric&appid={OPENWEATHER_API_KEY}"
        )
        weather_response = requests.get(weather_url)
        weather_response.raise_for_status()
        weather_data = weather_response.json()

        if "list" not in weather_data:
            return f"Error: Forecast data not available for '{city}'."

        # Step 3: Process and format the forecast into a string
        forecast_summary = []
        seen_dates = set()
        for entry in weather_data["list"]:
            date_str = entry["dt_txt"].split(" ")[0]
            if date_str not in seen_dates:
                seen_dates.add(date_str)
                temp = entry["main"]["temp"]
                description = entry["weather"][0]["description"]
                forecast_summary.append(f"{date_str}: {temp}°C, {description}")
            if len(forecast_summary) >= 3:  # Limit to a 3-day forecast for brevity
                break
        
        if not forecast_summary:
            return f"Could not generate a forecast for {city}."

        return f"Forecast for {city}:\n" + "\n".join(forecast_summary)

    except requests.exceptions.RequestException as e:
        return f"Error connecting to weather service: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


# ... (Test block is the same) ...
if __name__ == "__main__":
    city_test = "Lisbon"
    country_test = "PT"

    weather_summary = get_weather_forecast(city_test, country_test)
    print(weather_summary)

    print("-" * 20)

    city_test_2 = "London"
    # Test without country code to ensure the fix works
    weather_summary_2 = get_weather_forecast(city_test_2)
    print(weather_summary_2)