import os
import requests
from dotenv import load_dotenv
import urllib.parse
from typing import Dict, Any

# Load API key from .env
load_dotenv()
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")


def get_city_coordinates(city: str, country_code: str = "") -> Dict[str, Any]:
    """
    Get the coordinates (latitude and longitude) of a city using the Geoapify Geocoding API.

    Args:
        city (str): The name of the city.
        country_code (str, optional): The two-letter ISO country code to refine the search. Defaults to "".

    Returns:
        Dict[str, Any]: A dictionary containing 'lat' and 'lon' on success,
                        or an 'error' key on failure.
    """
    if not GEOAPIFY_API_KEY:
        return {"error": "Geoapify API key not found."}

    try:
        query = f"{city},{country_code}" if country_code else city
        query = urllib.parse.quote(query)  # URL-encode

        url = f"https://api.geoapify.com/v1/geocode/search?text={query}&apiKey={GEOAPIFY_API_KEY}"
        
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if "features" not in data or not data["features"]:
            return {"error": f"City not found: {city}"}

        coords = data["features"][0]["properties"]
        lat = coords.get("lat")
        lon = coords.get("lon")
        return {"lat": lat, "lon": lon}

    except requests.exceptions.RequestException as e:
        return {"error": f"Network error while fetching coordinates: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred in get_city_coordinates: {e}"}


def get_tourist_attractions_by_city(city: str, country_code: str = "", radius: int = 5000, limit: int = 10) -> Dict[str, Any]:
    """
    Get tourist attractions for a city by first finding its coordinates.

    Args:
        city (str): The name of the city.
        country_code (str, optional): The two-letter ISO country code. Defaults to "".
        radius (int, optional): The search radius in meters. Defaults to 5000.
        limit (int, optional): The maximum number of attractions to return. Defaults to 10.

    Returns:
        Dict[str, Any]: A dictionary with a 'results' key containing a list of attractions,
                        or an 'error' key if an issue occurs.
    """
    coords = get_city_coordinates(city, country_code)
    if "error" in coords:
        return coords  # Return error from get_city_coordinates

    lat, lon = coords["lat"], coords["lon"]

    try:
        url = (
            f"https://api.geoapify.com/v2/places"
            f"?categories=tourism.attraction"
            f"&filter=circle:{lon},{lat},{radius}"
            f"&limit={limit}"
            f"&apiKey={GEOAPIFY_API_KEY}"
        )

        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if "features" not in data:
            return {"error": f"Unexpected API response format: {data}"}

        attractions = []
        for place in data["features"]:
            props = place["properties"]
            attractions.append({
                "name": props.get("name", "Unnamed"),
                "address": props.get("formatted", "No address available"),
                "lat": props.get("lat"),
                "lon": props.get("lon"),
                "categories": props.get("categories", [])
            })

        return {"results": attractions}

    except requests.exceptions.RequestException as e:
        return {"error": f"Network error while fetching attractions: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred in get_tourist_attractions_by_city: {e}"}


# ===== TEST THE FUNCTION =====
if __name__ == "__main__":
    city_test = "Lisbon"
    country_test = "PT"

    attractions_data = get_tourist_attractions_by_city(city_test, country_test, limit=5)
    
    print(f"Tourist Attractions in {city_test}:")
    if "error" in attractions_data:
        print(f"  Error: {attractions_data['error']}")
    elif attractions_data.get("results"):
        for attraction in attractions_data["results"]:
            print(f"  - {attraction['name']}")
    else:
        print("  No attractions found.")