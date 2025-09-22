import os
import requests
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

# Load API key
load_dotenv()
API_KEY = os.getenv("LITEAPI_KEY")

def get_hotels(
    city: str,
    country: str, # <-- THIS IS THE ONLY LINE THAT IS MATERIALLY CHANGED
    checkin: str,
    checkout: str,
    adults: int,
    children: int = 0,
    currency: str = "EUR",
    top_n: int = 15,
    per_page: int = 10
) -> Optional[List[Dict[str, Any]]]:
    """
    Searches for hotels in a given city and country using the LiteAPI.

    Args:
        city (str): The name of the city to search for hotels in.
        country (str): The country code for the city.
        checkin (str): The check-in date in 'YYYY-MM-DD' format.
        checkout (str): The check-out date in 'YYYY-MM-DD' format.
        adults (int): The number of adults.
        children (int, optional): The number of children. Defaults to 0.
        currency (str, optional): The currency for prices. Defaults to "EUR".
        top_n (int, optional): The number of top hotels (by price) to return. Defaults to 15.
        per_page (int, optional): The number of hotels to fetch per API page. Defaults to 10.

    Returns:
        Optional[List[Dict[str, Any]]]: A list of hotel data dictionaries, sorted by price,
                                        or a dictionary with an 'error' key if an issue occurs.
    """
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json", "Accept": "application/json"}

    url_hotels = (
        f"https://api.liteapi.travel/v3.0/data/hotels?"
        f"countryCode={country}&cityName={city}&checkin={checkin}&checkout={checkout}"
        f"&adults={adults}&currency={currency}&page=1&perPage={per_page}"
    )

    try:
        response = requests.get(url_hotels, headers=headers)
        response.raise_for_status()
        hotels_data = response.json().get("data", [])

        if not hotels_data:
            return {"error": "No hotels found for the initial search."}

        hotels = []
        url_rates = "https://api.liteapi.travel/v3.0/hotels/rates"
        children_ages = [10] * children

        for hotel in hotels_data[:3]:
            hotel_id = hotel.get("id")
            price = None

            body = {
                "hotelIds": [hotel_id],
                "checkin": checkin,
                "checkout": checkout,
                "currency": currency,
                "guestNationality": "US",
                "occupancies": [{"adults": adults, "children": children_ages}]
            }

            rates_response = requests.post(url_rates, json=body, headers=headers)

            if rates_response.status_code == 200:
                rates_json = rates_response.json()
                rates_data = rates_json.get("data", [])
                if rates_data and rates_data[0].get("roomTypes"):
                    room = rates_data[0]["roomTypes"][0]
                    if room.get("rates"):
                        rate_info = room["rates"][0]
                        price = rate_info.get("retailRate", {}).get("total", [{}])[0].get("amount")

            if price is None:
                continue

            hotel_data = {
                "name": hotel.get("name"),
                "address": hotel.get("address"),
                "city": hotel.get("city"),
                "country": hotel.get("country"),
                "rating": hotel.get("rating"),
                "reviewCount": hotel.get("reviewCount"),
                "main_photo": hotel.get("main_photo"),
                "website": hotel.get("website"),
                "price": price,
                "currency": currency,
                "description": hotel.get("hotelDescription"),
                "stars": hotel.get("stars")
            }
            hotels.append(hotel_data)

        return sorted(hotels, key=lambda x: x['price'])[:top_n]

    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching hotels: {e}"}
    except ValueError as ve:
        return {"error": f"Error parsing response: {ve}"}


if __name__ == "__main__":
    city_test = "Paris"
    country_test = "FR" # Test with a specific country
    checkin_test = "2025-10-20"
    checkout_test = "2025-10-26"
    adults_test = 2
    children_test = 0

    hotels_list = get_hotels(
        city=city_test,
        country=country_test, # Pass the country code for testing
        checkin=checkin_test,
        checkout=checkout_test,
        adults=adults_test,
        children=children_test,
        per_page=10,
        top_n=15
    )

    if isinstance(hotels_list, dict) and "error" in hotels_list:
        print("Error:", hotels_list["error"])
    elif hotels_list:
        for idx, hotel in enumerate(hotels_list, start=1):
            print(f"{idx}. {hotel['name']} - {hotel['price']} {hotel['currency']}")
    else:
        print("No hotels found.")