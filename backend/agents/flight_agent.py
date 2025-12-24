import asyncio
from typing import Optional
from services.amadeus_flights import search_flights as amadeus_search_flights


class FlightAgent:
    async def search_flights(
        self,
        source: Optional[str] = None,
        destination: Optional[str] = None,
        start_date: Optional[str] = None,
        passengers: int = 1,
        cabin_class: Optional[str] = None
    ) -> list[str]:
        """
        Search for one-way flights using Amadeus API.
        
        Args:
            source: Origin city/airport (3-letter IATA code, e.g., 'NYC', 'LAX')
            destination: Destination city/airport (3-letter IATA code)
            start_date: Departure date (YYYY-MM-DD format)
            passengers: Number of passengers (default: 1)
            cabin_class: Cabin class - ECONOMY, PREMIUM_ECONOMY, BUSINESS, or FIRST (default: ECONOMY)
            
        Returns:
            List of formatted flight strings for display
        """
        # Validate required inputs
        if not source or not destination or not start_date:
            print(f"⚠️ [FLIGHT_AGENT] Missing required inputs: source={source}, destination={destination}, start_date={start_date}")
            return []
        
        # Normalize cabin class
        if not cabin_class:
            cabin_class = "ECONOMY"
        
        print(f"🔍 [FLIGHT_AGENT] Received - Source: '{source}', Destination: '{destination}', Date: '{start_date}', Passengers: {passengers}, Cabin: {cabin_class}")
        
        try:
            print(f"🔍 [FLIGHT_AGENT] Searching flights: {source} → {destination} on {start_date}")
            
            # Call Amadeus API synchronously in a thread pool to avoid blocking
            flight_data = await asyncio.to_thread(
                amadeus_search_flights,
                origin=source,
                destination=destination,
                departure_date=start_date,
                adults=passengers,
                max_results=5,
                travel_class=cabin_class
            )
            
            # Format the flight data into strings for display
            formatted_flights = []
            for flight in flight_data:
                flight_str = (
                    f"{flight['flight_number']} | "
                    f"{flight['departure']['airport']} {flight['departure']['time']} → "
                    f"{flight['arrival']['airport']} {flight['arrival']['time']} | "
                    f"Duration: {flight['duration']} | "
                    f"Stops: {flight['stops']} | "
                    f"Price: {flight['price']['currency']} {flight['price']['amount']} | "
                    f"Cabin: {flight['cabin']}"
                )
                formatted_flights.append(flight_str)
            
            print(f"✅ [FLIGHT_AGENT] Found {len(formatted_flights)} flights from Amadeus")
            return formatted_flights
            
        except Exception as e:
            print(f"❌ [FLIGHT_AGENT] Amadeus API failed: {e}")
            return []  # Return empty list on error to fail gracefully
