import os
from amadeus import Client, ResponseError
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any

# Load .env file
load_dotenv()

# ====== AMADEUS API KEYS ======
AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")

# ====== INITIALIZE AMADEUS CLIENT ======
amadeus = Client(
    client_id=AMADEUS_CLIENT_ID,
    client_secret=AMADEUS_CLIENT_SECRET
)

def search_flights(origin: str, destination: str, departure_date: str, adults: int, return_date: Optional[str] = None, top_n: int = 15) -> Optional[List[Dict[str, Any]]]:
    """
    Search flights using Amadeus API.
    """
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            returnDate=return_date,
            adults=adults,
            max=top_n
        )
        flights = response.data

        simplified_flights = []
        for offer in flights:
            total_price = offer['price']['total']
            itineraries_info = []
            for itinerary in offer['itineraries']:
                segments_info = []
                # --- BUG FIX: The duration belongs to the itinerary, not the segment ---
                itinerary_duration = itinerary['duration']
                for segment in itinerary['segments']:
                    segments_info.append({
                        'from': segment['departure']['iataCode'],
                        'to': segment['arrival']['iataCode'],
                        'departure': segment['departure']['at'],
                        'arrival': segment['arrival']['at'],
                        'carrier': segment['carrierCode'],
                        'flight_number': segment['number'],
                        'duration': itinerary_duration # Correctly assigned here
                    })
                itineraries_info.append(segments_info)

            simplified_flights.append({
                'itineraries': itineraries_info,
                'total_price': total_price
            })

        return simplified_flights

    except ResponseError as error:
        error_str = str(error)
        if "NO_FARE_APPLICABLE" in error_str or "NO_COMBINABLE_FARES" in error_str:
            print(f"--- Amadeus Info: No applicable fares found for {origin} to {destination} on {departure_date}. This is expected. ---")
            return []
        
        print(f"--- Amadeus Error: A non-fare related error occurred: {error} ---")
        return {"error": f"Error fetching flights: {error}"}


if __name__ == "__main__":
    print("--- Running Flight Finder Test ---")
    # We will test a route that is known to have data in the Amadeus test environment.
    test_origin = "STO"
    test_destination = "LIS"
    test_departure_date = "2025-10-10"
    test_return_date = "2025-10-17"
    test_adults = 2

    print(f"Searching for flights from {test_origin} to {test_destination} on {test_departure_date}...")
    
    flights_result = search_flights(
        origin=test_origin, 
        destination=test_destination, 
        departure_date=test_departure_date, 
        adults=test_adults, 
        return_date=test_return_date
    )

    print("\n--- TEST RESULTS ---")
    if isinstance(flights_result, list) and len(flights_result) > 0:
        print(f"Successfully found {len(flights_result)} flight options.")
        # Print details for the top 3 flights
        for idx, flight in enumerate(flights_result[:3], 1):
            print(f"\n--- Option {idx} ---")
            print(f"Total Price: {flight['total_price']} EUR")
            
            # Print outbound journey
            print("  Outbound Journey:")
            outbound_journey = flight['itineraries'][0]
            for leg in outbound_journey:
                print(f"    {leg['from']} -> {leg['to']} ({leg['carrier']} {leg['flight_number']})")
            
            # Print return journey if it exists
            if len(flight['itineraries']) > 1:
                print("  Return Journey:")
                return_journey = flight['itineraries'][1]
                for leg in return_journey:
                    print(f"    {leg['from']} -> {leg['to']} ({leg['carrier']} {leg['flight_number']})")

    elif isinstance(flights_result, list) and len(flights_result) == 0:
        print("Search was successful, but no flights were found for the specified route and dates.")
    
    elif isinstance(flights_result, dict) and "error" in flights_result:
        print(f"An error occurred during the search: {flights_result['error']}")
    
    else:
        print("An unknown result was returned.")