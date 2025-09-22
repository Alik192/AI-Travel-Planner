import os
import requests
from dotenv import load_dotenv
from typing import Union, Dict, Any

# Load environment variables
load_dotenv()
CURRENCY_API_KEY = os.getenv("CURRENCY_API_KEY")

def convert_currency(amount: float, from_currency: str, to_currency: str) -> Union[float, Dict[str, Any]]:
    """
    Convert an amount from one currency to another using the ExchangeRate.host API.

    Args:
        amount (float): The amount of money to convert.
        from_currency (str): The ISO 4217 code of the currency to convert from (e.g., "USD").
        to_currency (str): The ISO 4217 code of the currency to convert to (e.g., "EUR").

    Returns:
        Union[float, Dict[str, Any]]: The converted amount as a float, rounded to 2 decimal places,
                                     or a dictionary with an 'error' key on failure.
    """
    # Note: The free plan for exchangerate.host does not require an API key.
    # The `access_key` parameter is for paid plans.
    # If you have a paid key, ensure CURRENCY_API_KEY is set in your .env file.
    url = f"https://api.exchangerate.host/convert?from={from_currency}&to={to_currency}&amount={amount}"
    if CURRENCY_API_KEY:
        url += f"&access_key={CURRENCY_API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if data.get("success") and data.get("result") is not None:
            return round(data["result"], 2)
        else:
            # Capture the error message from the API if available
            error_info = data.get("error", {}).get("info", "Unknown conversion error.")
            return {"error": f"Conversion failed: {error_info}"}

    except requests.exceptions.RequestException as e:
        return {"error": f"Network error during currency conversion: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred in convert_currency: {e}"}

# ====== TEST ======
if __name__ == "__main__":
    amount_test = 150.0
    from_curr = "EUR"
    to_curr = "USD"

    converted_amount = convert_currency(amount_test, from_curr, to_curr)

    if isinstance(converted_amount, dict) and "error" in converted_amount:
        print(f"Error converting currency: {converted_amount['error']}")
    else:
        print(f"{amount_test} {from_curr} is equal to {converted_amount} {to_curr}")

    # Test an invalid currency
    print("-" * 20)
    invalid_conversion = convert_currency(100, "EUR", "XYZ")
    if isinstance(invalid_conversion, dict) and "error" in invalid_conversion:
        print(f"Correctly handled invalid currency: {invalid_conversion['error']}")
