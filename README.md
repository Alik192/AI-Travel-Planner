# AI Travel Planner

## Project Summary

The AI Travel Planner is a Python-based web application built with Streamlit that serves as a "smart" travel agent. The application takes user inputs for a desired vacation—such as destination, dates, budget, and travel style—and generates a comprehensive, personalized travel plan. It achieves this by orchestrating a series of specialized "agents" that gather real-time data from various external APIs. This data is then synthesized by a Large Language Model (Google's Gemini) into a coherent and actionable itinerary, presented to the user through a clean web interface.

## Area of Specialization (Fördjupningsområde)

This project represents a deep dive into the **design and implementation of a modular, agent-based system in Python that integrates multiple, disparate APIs and uses a Large Language Model (LLM) for complex data synthesis.**

This specialization is demonstrated through:
*   **Modular Architecture:** The system is not a single monolithic script. It is broken down into independent, single-responsibility agents (`flight_finder`, `hotel_finder`, etc.), which promotes maintainability and scalability.
*   **Complex API Integration:** The project successfully integrates data from five distinct external services (Amadeus, LiteAPI, Geoapify, OpenWeather, and Google Gemini), handling different authentication methods, data formats, and error responses for each.
*   **System Resilience:** Significant effort was invested in making the system robust. This is most evident in the `flight_finder` agent, which was engineered to gracefully handle the inconsistent and often empty responses from the Amadeus Test API, ensuring the application does not crash and provides clear user feedback.
*   **Advanced AI Application:** The LLM is used as a final synthesis engine. It receives structured, multi-source data (flight prices, hotel names, weather forecasts) and is prompted to transform this raw data into a creative, well-formatted, and human-readable travel plan, showcasing a modern and practical application of generative AI.

## Core Technologies

*   **Backend/Orchestration:** Python 3
*   **Web Framework:** Streamlit
*   **Generative AI:** Google Gemini
*   **External APIs:**
    *   **Flights:** Amadeus Self-Service API
    *   **Hotels:** LiteAPI
    *   **Tourist Attractions:** Geoapify
    *   **Weather:** OpenWeatherMap
*   **Key Python Libraries:** `requests`, `pandas`, `streamlit`, `python-dotenv`, `google-generativeai`, `amadeus`

## System Architecture

The application follows a modular, orchestrator-agent design pattern.

1.  **UI Layer (`app.py`):** A Streamlit application provides the user interface. It captures all user inputs (origin, destination, dates, etc.) and is responsible for displaying the final generated plan.

2.  **Orchestrator (`travel_pipeline.py`):** This is the central brain of the application. When a user submits the form, the orchestrator receives the inputs and begins a sequence of operations:
    *   It calls the necessary agents in a logical order.
    *   It utilizes Streamlit's caching (`@st.cache_data`) to store agent results, preventing redundant API calls and improving performance on repeated queries.
    *   It gathers all the data returned by the agents.
    *   It dynamically constructs a detailed prompt for the Gemini LLM, injecting the fetched data (flight options, hotel details, weather, etc.) into the prompt text.
    *   It sends the final prompt to the Gemini API and returns the generated text back to the UI layer.

3.  **Agent Layer (`agents/`):** Each agent is a Python script with a single responsibility, acting as a specialized data-gathering module.
    *   `iata_finder.py`: Translates a user-provided city name (e.g., "Paris") into its corresponding IATA airport code (`PAR`) and country code (`FR`) by searching a local CSV database.
    *   `flight_finder.py`: Searches for flight offers using the Amadeus API.
    *   `hotel_finder.py`: Searches for hotel availability and pricing using the LiteAPI.
    *   `geoapify_agent.py`: Fetches a list of popular tourist attractions for the destination city.
    *   `weather_checker.py`: Retrieves the current weather forecast for the destination.

## Challenges & Solutions

This section details two significant technical challenges encountered during development and the systematic approach taken to solve them, demonstrating a detailed understanding of the system.

### 1. Challenge: Ambiguous Location Identification

**Problem:** An early version of the `iata_finder` agent produced incorrect results for major cities. For example, a search for "Paris" returned `PRX` (Cox Field, Paris, Texas, USA) instead of `PAR` (the main IATA code for Paris, France). This caused downstream agents like the flight and hotel finders to fail by searching in the wrong country.

**Solution:** The problem was solved by refining the data processing logic within the `iata_finder`.
1.  **Analysis:** The `airport-codes.csv` database contains multiple entries for city names that exist in different parts of the world, including small, medium, and large airports. The original implementation simply took the first match it found.
2.  **Implementation:** A more robust sorting mechanism was implemented. The Pandas DataFrame containing the airport data is now pre-sorted based on airport `type`. A custom categorical order (`['city_code', 'large_airport', 'medium_airport', 'small_airport']`) was established. This ensures that when searching for a city, the code prioritizes the main city-level IATA code or the largest international airport, guaranteeing the correct location is identified.

### 2. Challenge: Building Resilience Against Unreliable API Data

**Problem:** The `flight_finder` agent, which uses the Amadeus Test API, was highly unreliable. It would work one day and fail the next, often returning a `[400] Bad Request` error or simply no data for routes that previously worked. This caused the entire application to fail or produce incomplete results.

**Solution:** The solution involved a deep dive into the Amadeus API documentation and implementing robust error handling and defensive coding.
1.  **Diagnosis:** Through systematic testing with different routes and dates, and by consulting the API documentation, it was confirmed that the Amadeus Test environment uses a limited, static dataset. The errors were not caused by our code being "wrong," but by the API having no test data for the requested query.
2.  **Graceful Error Handling:** The `except ResponseError` block in `flight_finder.py` was significantly enhanced. Instead of treating all errors as critical failures, it now inspects the error content. If the error contains specific codes like `NO_FARE_APPLICABLE`, the function understands this to mean "zero flights found" and returns an empty list `[]`. For any other unexpected error, it returns a `None` or error dictionary.
3.  **Dynamic Parameter Building:** To solve the `[400]` error on one-way searches, the API call was refactored to build its parameters dynamically. The `returnDate` parameter is now only added to the request if a value is explicitly provided, preventing the library from sending a `None` value that the API rejects.
4.  **User Feedback:** The `travel_pipeline.py` orchestrator was updated to interpret the agent's response. If it receives an empty list `[]` from the flight finder, it now generates a user-friendly message like "No flights were found for your destination on the selected dates," rather than showing an error.

This solution makes the application resilient and provides a better user experience, even when external dependencies are unreliable.

## How to Run the Project

Follow these steps to set up and run the application locally.

### 1. Prerequisites
*   Python 3.8 or newer.
*   Git.

### 2. Clone the Repository
```bash
git clone <your-repository-url>
cd AI_Travel_Planner
```

### 3. Set Up a Virtual Environment
*   **Windows:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
*   **macOS / Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

### 4. Install Dependencies
Install all required Python libraries from the `requirements.txt` file.
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
The application requires API keys to function.

1.  Create a file named `.env` in the root directory of the project.
2.  Add your API keys to this file in the following format:

    ```
    GEMINI_API_KEY="YOUR_GOOGLE_GEMINI_API_KEY"
    AMADEUS_CLIENT_ID="YOUR_AMADEUS_CLIENT_ID"
    AMADEUS_CLIENT_SECRET="YOUR_AMADEUS_CLIENT_SECRET"
    LITEAPI_KEY="YOUR_LITEAPI_KEY"
    GEOAPIFY_API_KEY="YOUR_GEOAPIFY_API_KEY"
    OPENWEATHER_API_KEY="YOUR_OPENWEATHER_API_KEY"
    ```

### 6. Run the Application
Launch the Streamlit web server with the following command:
```bash
streamlit run app.py
```
The application should now be open and accessible in your web browser.
