import os
from dotenv import load_dotenv
load_dotenv()
import requests

SERP_API_URL = "https://serpapi.com/search"


def search_hotels(
    city: str,
    check_in_date: str,
    check_out_date: str,
):
    """
    Search hotels using SERP API (Google Hotels).
    Minimal parameter set for reliability.
    """
    api_key = os.getenv("SERP_API_KEY")
    if not api_key:
        raise RuntimeError("SERP_API_KEY not found in environment variables")

    params = {
        "engine": "google_hotels",
        "q": city,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "api_key": api_key,
    }

    response = requests.get(SERP_API_URL, params=params, timeout=20)

    # Helpful debug if it fails again
    if response.status_code != 200:
        print("SERP API error response:", response.text)

    response.raise_for_status()
    raw_data = response.json()
    return format_hotels(raw_data)


def format_hotels(data: dict, max_results: int = 8):
    """
    Convert SERP API hotel results into clean, UI-ready objects.
    """
    hotels = []

    properties = data.get("properties", [])

    for prop in properties[:max_results]:
        # Extract price using SERP API's actual structure
        price = "Price not available"
        rate_per_night = prop.get("rate_per_night", {})
        total_rate = prop.get("total_rate", {})
        
        if rate_per_night.get("lowest"):
            price = rate_per_night.get("lowest")
        elif total_rate.get("lowest"):
            price = total_rate.get("lowest")
        
        hotel = {
            "name": prop.get("name"),
            "price": price,
            "rating": prop.get("rating"),
            "reviews": prop.get("reviews"),
            "amenities": prop.get("amenities", []),
            "image": (
                prop.get("images", [{}])[0].get("thumbnail")
                if prop.get("images")
                else None
            ),
            "link": prop.get("link"),
        }

        hotels.append(hotel)

    return hotels
