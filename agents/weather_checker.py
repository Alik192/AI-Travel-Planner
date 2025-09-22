import os
import requests
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

# Get OpenWeatherMap API key from environment variables
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

def get_weather_forecast(city: str, country_code: str = "") -> str:
    """
    Gets a summarized weather forecast for a city and formats it as a string.

    This function first finds the geographical coordinates (latitude and longitude)
    for the given city. It then uses these coordinates to fetch a 7-day weather
    forecast from the OpenWeatherMap API. Finally, it formats this information
    into a concise, human-readable string.

    Args:
        city (str): The name of the city (e.g., "Lisbon").
        country_code (str, optional): The two-letter ISO country code (e.g., "PT").
                                      Helps to specify the city if the name is common.
                                      Defaults to "".

    Returns:
        str: A string summarizing the weather forecast (e.g., "Forecast for Lisbon: ...")
             or an error message if the forecast could not be retrieved.
    """
    if not OPENWEATHER_API_KEY:
        return "Error: OpenWeatherMap API key is not set."

    try:
        # Step 1: Get city coordinates (geocoding)
        geo_url = (
            f"http://api.openweathermap.org/geo/1.0/direct?q={city},{country_code}"
            f"&limit=1&appid={OPENWEATHER_API_KEY}"
        )
        geo_response = requests.get(geo_url)
        geo_response.raise_for_status()  # Raise an exception for bad status codes
        geo_data = geo_response.json()

        if not geo_data or "lat" not in geo_data[0]:
            return f"Error: Could not find coordinates for the city '{city}'."

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


# ------------------ Test ------------------
if __name__ == "__main__":
    city_test = "Lisbon"
    country_test = "PT"

    weather_summary = get_weather_forecast(city_test, country_test)
    print(weather_summary)

    print("-" * 20)

    city_test_2 = "London"
    country_test_2 = "GB"
    weather_summary_2 = get_weather_forecast(city_test_2, country_test_2)
    print(weather_summary_2)