import requests
from dotenv import load_dotenv
load_dotenv()
from services.amadeus_auth import get_amadeus_access_token

AMADEUS_FLIGHT_OFFERS_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"


def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    adults: int = 1,
    max_results: int = 5,
    travel_class: str = "ECONOMY"
):
    """
    Fetch real flight offers from Amadeus and return formatted results.
    
    Args:
        origin: Origin airport IATA code
        destination: Destination airport IATA code
        departure_date: Departure date in YYYY-MM-DD format
        adults: Number of adult passengers
        max_results: Maximum number of results to return
        travel_class: Cabin class - ECONOMY, PREMIUM_ECONOMY, BUSINESS, or FIRST
    """
    token = get_amadeus_access_token()

    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date,
        "adults": adults,
        "travelClass": travel_class,
        "currencyCode": "INR",
        "max": max_results,
    }
    
    print(f"📤 [AMADEUS] Requesting flights: {origin} → {destination} on {departure_date}")
    print(f"📤 [AMADEUS] Full params: {params}")

    response = requests.get(
        AMADEUS_FLIGHT_OFFERS_URL,
        headers={
            "Authorization": f"Bearer {token}"
        },
        params=params,
        timeout=15
    )

    response.raise_for_status()
    raw_data = response.json()
    
    print(f"🔍 [AMADEUS] Raw response contains {len(raw_data.get('data', []))} offers")
    if raw_data.get('data'):
        first_offer = raw_data['data'][0]
        first_segment = first_offer['itineraries'][0]['segments'][0]
        print(f"🔍 [AMADEUS] First flight: {first_segment['departure']['iataCode']} → {first_segment['arrival']['iataCode']}")

    formatted_results = format_flight_offers(raw_data, destination)
    
    if not formatted_results:
        print(f"⚠️ [AMADEUS] No flights found matching destination {destination}")
        print(f"⚠️ [AMADEUS] This may be due to Test API limitations or no available flights for this route")
    
    return formatted_results


def format_flight_offers(data: dict, requested_destination: str = None):
    """
    Convert raw Amadeus flight-offers JSON into clean, UI-ready objects.
    Filters out flights that don't match the requested destination.
    
    Args:
        data: Raw Amadeus API response
        requested_destination: Expected destination IATA code for validation
    """
    formatted_flights = []

    for offer in data.get("data", []):
        itinerary = offer["itineraries"][0]
        segment = itinerary["segments"][0]

        traveler = offer["travelerPricings"][0]
        fare_details = traveler["fareDetailsBySegment"][0]
        
        actual_destination = segment['arrival']['iataCode']
        
        print(f"🔍 [AMADEUS] Processing flight: {segment['departure']['iataCode']} → {actual_destination} | {segment['carrierCode']} {segment['number']}")
        
        # Validate destination matches if provided
        if requested_destination and actual_destination != requested_destination:
            print(f"⚠️ [AMADEUS] Skipping flight - destination mismatch (expected {requested_destination}, got {actual_destination})")
            continue

        # Safely extract baggage information with fallbacks
        checked_bags = fare_details.get("includedCheckedBags", {})
        cabin_bags = fare_details.get("includedCabinBags", {})
        
        checked_weight = checked_bags.get("weight") if checked_bags else None
        cabin_weight = cabin_bags.get("weight") if cabin_bags else None
        
        flight = {
            "airline": segment["carrierCode"],
            "flight_number": f'{segment["carrierCode"]} {segment["number"]}',
            "departure": {
                "airport": segment["departure"]["iataCode"],
                "time": segment["departure"]["at"][11:16],
            },
            "arrival": {
                "airport": segment["arrival"]["iataCode"],
                "time": segment["arrival"]["at"][11:16],
            },
            "duration": _format_duration(itinerary["duration"]),
            "stops": segment["numberOfStops"],
            "price": {
                "amount": offer["price"]["total"],
                "currency": offer["price"]["currency"],
            },
            "cabin": fare_details["cabin"],
            "baggage": {
                "checked": f"{checked_weight} kg" if checked_weight else "Not included",
                "cabin": f"{cabin_weight} kg" if cabin_weight else "Not included",
            }
        }

        formatted_flights.append(flight)

    return formatted_flights


def _format_duration(duration: str) -> str:
    """
    Convert ISO 8601 duration (e.g. PT2H30M) into readable format (2h 30m).
    """
    duration = duration.replace("PT", "")
    hours = "0"
    minutes = "0"

    if "H" in duration:
        hours, duration = duration.split("H")
    if "M" in duration:
        minutes = duration.replace("M", "")

    return f"{hours}h {minutes}m"
