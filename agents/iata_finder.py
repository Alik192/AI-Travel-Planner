import pandas as pd
import os

# --- Load the local airport codes database ---
try:
    file_path = os.path.join('data', 'airport-codes.csv')
    df_airports = pd.read_csv(file_path)
except FileNotFoundError:
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, 'data', 'airport-codes.csv')
        df_airports = pd.read_csv(file_path)
    except FileNotFoundError:
        df_airports = None
        print("CRITICAL ERROR: Could not find 'data/airport-codes.csv'.")

# If the dataframe loaded successfully, prepare it for use.
if df_airports is not None:
    df_airports = df_airports[df_airports['iata_code'].notna()]
    df_airports = df_airports[df_airports['type'] != 'closed']
    df_airports['municipality'] = df_airports['municipality'].fillna('')
    
    # --- FINAL FIX: Create a more robust sort order ---
    # We want to find the city's main IATA code if it exists.
    # The main city code often has a 'iata_code' but no specific 'type'.
    # We will prioritize these, then large airports.
    df_airports['type'] = df_airports['type'].fillna('city_code') # Treat blanks as a city code
    airport_type_order = ['city_code', 'large_airport', 'medium_airport', 'small_airport']
    df_airports['type_cat'] = pd.Categorical(df_airports['type'], categories=airport_type_order, ordered=True)
    df_airports = df_airports.sort_values(by='type_cat', ascending=True)


def get_location_codes(city_name: str) -> dict:
    """
    Fetches the IATA code and country code for a given city from the local CSV database.
    """
    if df_airports is None:
        return {"error": "Airport database not loaded."}

    city_name_lower = city_name.lower()
    matches = df_airports[df_airports['municipality'].str.lower() == city_name_lower]

    if not matches.empty:
        # The dataframe is now sorted by airport size, so the first match is the best one.
        iata_code = matches.iloc[0]['iata_code']
        country_code = matches.iloc[0]['iso_country']
        
        print(f"--- Found local codes for '{city_name}': IATA='{iata_code}', Country='{country_code}' ---")
        return {'iata': iata_code, 'country': country_code}
    else:
        return {"error": f"Could not find location codes for {city_name} in the local database."}

if __name__ == '__main__':
    if df_airports is not None:
        print("\nTesting Paris (should be PAR):")
        print(f"Result: {get_location_codes('Paris')}")