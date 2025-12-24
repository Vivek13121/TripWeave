from typing import Optional
from services.serp_hotels import search_hotels


class HotelAgent:
    async def search_hotels(
        self,
        destination: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        duration: Optional[int] = None,
        additional_info: Optional[str] = None
    ) -> list[dict]:
        """
        Search for hotels using SERP API Google Hotels.
        
        Args:
            destination: City/location for hotel search
            start_date: Check-in date
            end_date: Check-out date
            duration: Length of stay in days (unused)
            additional_info: Any additional requirements (unused)
            
        Returns:
            List of hotel dictionaries with real data from Google Hotels
        """
        print(f"🔍 [HOTEL_AGENT] Searching hotels:")
        print(f"  - destination: {destination}")
        print(f"  - start_date: {start_date}")
        print(f"  - end_date: {end_date}")
        
        # Gracefully handle missing inputs
        if not destination or not start_date or not end_date:
            print(f"⚠️ [HOTEL_AGENT] Missing required inputs, returning empty list")
            return []
        
        try:
            # Call SERP API hotel search
            hotels = search_hotels(
                city=destination,
                check_in_date=start_date,
                check_out_date=end_date
            )
            
            print(f"✅ [HOTEL_AGENT] Found {len(hotels)} hotels from SERP API")
            return hotels
            
        except Exception as e:
            print(f"❌ [HOTEL_AGENT] SERP API failed: {e}")
            return []  # Gracefully return empty list on error
