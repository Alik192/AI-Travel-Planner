import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import google.generativeai as genai
import streamlit as st

from agents.hotel_finder import get_hotels
from agents.weather_checker import get_weather_forecast
from agents.geoapify_agent import get_tourist_attractions_by_city
from agents.flight_finder import search_flights
from agents.iata_finder import get_location_codes # MODIFICATION: Using the new function

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
else:
    model = None

# --- Caching Decorators for Agent Functions ---
@st.cache_data(ttl=3600)
def cached_search_flights(*args, **kwargs):
    return search_flights(*args, **kwargs)

@st.cache_data(ttl=3600)
def cached_get_hotels(*args, **kwargs):
    return get_hotels(*args, **kwargs)

@st.cache_data(ttl=3600)
def cached_get_weather_forecast(*args, **kwargs):
    return get_weather_forecast(*args, **kwargs)

@st.cache_data(ttl=3600)
def cached_get_tourist_attractions_by_city(*args, **kwargs):
    return get_tourist_attractions_by_city(*args, **kwargs)

# MODIFICATION: Caching the new location finder function
@st.cache_data(ttl=86400)
def cached_get_location_codes(*args, **kwargs):
    return get_location_codes(*args, **kwargs)

def vacation_plan(
    origin_iata: str,
    destination_city: str,
    vacation_type: str,
    adults: int,
    children: int,
    duration: int,
    start_date: str,
    budget_eur: int
):
    if not model:
        return "Error: Gemini API key not configured."

    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        return_date = (start_date_obj + timedelta(days=duration)).strftime("%Y-%m-%d")
    except ValueError:
        return "Error: Invalid date format provided."

    # --- Agent Calls ---
    # MODIFICATION: Get both IATA and country code from the destination city
    location_codes = cached_get_location_codes(city_name=destination_city)
    if "error" in location_codes:
        return f"Could not generate plan. {location_codes['error']}"
    
    destination_iata = location_codes['iata']
    destination_country_code = location_codes['country']

    # Flights
    flights = cached_search_flights(
        origin=origin_iata, destination=destination_iata, departure_date=start_date,
        return_date=return_date, adults=adults, top_n=5
    )
    flight_details = "No flights found or an error occurred."
    if flights and not isinstance(flights, dict):
        flights.sort(key=lambda x: float(x['total_price']))
        flight_details = "\n".join([
            f"  - Option {i+1}: {f['total_price']} EUR, Stops: {len(f['itineraries'][0])-1}"
            for i, f in enumerate(flights)
        ])

    # Hotels (MODIFICATION: Pass the dynamic country code to fix the bug)
    hotels = cached_get_hotels(
        city=destination_city,
        country=destination_country_code, # <-- This is the critical fix
        checkin=start_date,
        checkout=return_date,
        adults=adults,
        children=children,
        top_n=5
    )
    hotel_details = "No hotels found or an error occurred."
    if hotels and not isinstance(hotels, dict):
        hotel_details = "\n".join([
            f"  - {h['name']}, Address: {h['address']}, Price: {h['price']} {h['currency']}"
            for h in hotels
        ])

    # Weather
    weather = cached_get_weather_forecast(city=destination_city)

    # Attractions
    attractions = cached_get_tourist_attractions_by_city(city=destination_city, limit=6)
    attraction_list = [f"Popular attraction in {destination_city} #{i+1}" for i in range(6)]
    if "results" in attractions and attractions["results"]:
        attraction_list = [attraction['name'] for attraction in attractions['results']]

    # --- Plan Generation (Using the more robust prompt we developed) ---
    prompt = f"""
    You are a travel agent. A user wants to go on a {vacation_type} vacation to {destination_city}.
    They are traveling with {adults} adults and {children} children. The trip will last {duration} days,
    starting on {start_date}. The budget is {budget_eur} EUR.

    Here's some information to help you create a detailed vacation plan. If any information says 'No data found' or 'unavailable', you must state that you could not find specific options but should still suggest a reasonable budget for that category based on the overall trip budget.

    Flight Options from {origin_iata} to {destination_iata}:
    {flight_details}

    Hotel Options in {destination_city}:
    {hotel_details}
    
    Weather Forecast:
    {weather}

    Based on this information, generate ONLY the following sections with the exact formatting as shown below. Do not include any extra text, disclaimers, or explanations.

    **Destination Overview: {destination_city}**

    **Flights**
    Flight Option 1:** [Price] EUR per person (Total: [Total Price] EUR), with [Number] stop(s).

    **Accommodation**
    Hotel:** [If a hotel was found, list its name. If not, state 'A suitable hotel within your budget.']
    Address:** [If a hotel was found, list its address. If not, state 'N/A']
    Price:** [If a hotel was found, list its price. If not, estimate a reasonable price for {duration} nights based on the total budget.]

    **Weather**
    [Provide a brief summary of the weather based on the forecast data provided.]

    **Top Attractions**
    *   {attraction_list[0]}
    *   {attraction_list[1]}
    *   {attraction_list[2]}
    *   {attraction_list[3]}
    *   {attraction_list[4]}
    *   {attraction_list[5]}

    **Cost Breakdown**
    Flights:** [Flight Cost] EUR
    Accommodation:** [Accommodation Cost] EUR
    Food:** [Food Cost] EUR
    Activities/Entrance Fees:** [Activities Cost] EUR
    Transportation:** [Transportation Cost] EUR
    Buffer/Miscellaneous:** [Buffer Cost] EUR

    **Total Estimated Cost:** [Total Cost] EUR
    """

    response = model.generate_content(prompt)
    return response.text