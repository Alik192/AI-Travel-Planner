import streamlit as st
from datetime import date, timedelta
from travel_pipeline import vacation_plan
import re

# --- Data for Origin City Dropdown ---
SWEDISH_AIRPORTS = {
    "Stockholm (ARN)": "ARN",
    "Gothenburg (GOT)": "GOT",
    "Malmö (MMX)": "MMX",
    "Luleå (LLA)": "LLA",
    "Umeå (UME)": "UME",
    "Kiruna (KRN)": "KRN"
}

# --- Helper Function to Parse the Plan ---
def parse_plan(plan_text: str) -> dict:
    """Splits the generated plan text into a dictionary of sections."""
    sections = {
        "overview": "", "flights": "", "accommodation": "",
        "weather": "", "attractions": "", "cost": ""
    }
    parts = re.split(r'(?=\*\*Flights\*\*|\*\*Accommodation\*\*|\*\*Weather\*\*|\*\*Top Attractions\*\*|\*\*Cost Breakdown\*\*)', plan_text)
    for part in parts:
        if part.startswith("**Destination Overview:"): sections["overview"] = part
        elif part.startswith("**Flights**"): sections["flights"] = part
        elif part.startswith("**Accommodation**"): sections["accommodation"] = part
        elif part.startswith("**Weather**"): sections["weather"] = part
        elif part.startswith("**Top Attractions**"): sections["attractions"] = part
        elif part.startswith("**Cost Breakdown**"): sections["cost"] = part
    return sections

def parse_cost_breakdown(cost_text: str) -> dict:
    """Parses the cost breakdown section to extract items and values."""
    costs = {}
    pattern = re.compile(r"^\s*(.*?):\**\s*([\d,]+\.?\d*)\s*EUR", re.MULTILINE)
    matches = pattern.findall(cost_text)
    for match in matches:
        item_name = match[0].strip().strip('*').strip()
        cost_value = float(match[1].replace(",", ""))
        costs[item_name] = cost_value
    return costs

# --- Streamlit App Configuration ---
st.set_page_config(page_title="AI Travel Planner", page_icon="✈️", layout="wide")
st.title("✈️ AI Travel Planner")
st.markdown("Fill in your travel details below and let the AI create a personalized plan for you!")

# --- Input Parameters ---
with st.form("travel_form"):
    st.header("Your Travel Preferences")
    
    col1, col2 = st.columns(2)
    with col1:
        origin_city_name = st.selectbox("Departure City", options=list(SWEDISH_AIRPORTS.keys()))
        origin_iata = SWEDISH_AIRPORTS[origin_city_name]
        start_date = st.date_input("Start Date", value=date.today() + timedelta(days=30))
        adults = st.number_input("Adults", min_value=1, max_value=10, value=2)

    with col2:
        destination_city = st.text_input("Destination City Name", "Lisbon")
        duration = st.number_input("Duration (days)", min_value=1, max_value=30, value=7)
        children = st.number_input("Children", min_value=0, max_value=10, value=0)
        
    vacation_type = st.selectbox("Vacation Type", ["Relaxing", "Adventure", "Cultural"])
    budget_eur = st.slider("Budget (EUR)", min_value=500, max_value=10000, value=3000, step=100)
    
    submitted = st.form_submit_button("Generate Vacation Plan")

# --- Plan Generation and Display ---
if submitted:
    with st.spinner("Generating your personalized travel plan... This may take a moment."):
        try:
            start_date_str = start_date.strftime("%Y-%m-%d")
            # MODIFICATION: destination_iata is no longer passed from the UI
            plan_text = vacation_plan(
                origin_iata=origin_iata,
                destination_city=destination_city,
                vacation_type=vacation_type,
                adults=adults,
                children=children,
                duration=duration,
                start_date=start_date_str,
                budget_eur=budget_eur
            )

            # Check if the pipeline returned an error message
            if "Error:" in plan_text:
                st.error(plan_text)
            else:
                st.subheader("Your Generated Vacation Plan")
                parsed_plan = parse_plan(plan_text)
                
                if parsed_plan["overview"]: st.markdown(parsed_plan["overview"])

                if parsed_plan["cost"]:
                    st.markdown("---")
                    st.markdown(parsed_plan["cost"].split('\n')[0])
                    costs = parse_cost_breakdown(parsed_plan["cost"])
                    
                    total_key = next((key for key in costs if "total" in key.lower()), None)
                    total_cost_value = costs.pop(total_key) if total_key else None
                    
                    cost_items = costs
                    
                    if cost_items:
                        cost_cols = st.columns(len(cost_items))
                        for i, (item, value) in enumerate(cost_items.items()):
                            cost_cols[i].metric(label=item, value=f"€ {value:,.2f}")

                    if total_cost_value is not None:
                        st.metric(label=total_key, value=f"€ {total_cost_value:,.2f}")
                    st.markdown("---")

                if parsed_plan["flights"]:
                    with st.expander("✈️ Flight Details", expanded=True): st.markdown(parsed_plan["flights"])
                if parsed_plan["accommodation"]:
                    with st.expander("🏨 Accommodation Details", expanded=True): st.markdown(parsed_plan["accommodation"])
                if parsed_plan["weather"]:
                    with st.expander("☀️ Weather Forecast"): st.markdown(parsed_plan["weather"])
                if parsed_plan["attractions"]:
                    with st.expander("🏰 Top Attractions"): st.markdown(parsed_plan["attractions"])

        except Exception as e:
            st.error(f"An error occurred while generating your vacation plan: {e}")