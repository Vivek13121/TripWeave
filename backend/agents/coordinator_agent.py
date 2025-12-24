from typing import Dict, Any, List


class CoordinatorAgent:
    def process_intent(self, parsed_data: Dict[str, Any]) -> str:
        """
        Process structured NLP output and extract intent for LangGraph state.
        
        Args:
            parsed_data: Dictionary containing parsed intent and entities from NLP module
            
        Returns:
            Intent string: "flight", "hotel", or "both"
        """
        intent_list = parsed_data.get("intent", [])
        
        # Convert intent list to string format
        if not intent_list:
            return "unknown"
        elif len(intent_list) == 2 or (len(intent_list) == 1 and "trip" in parsed_data.get("original_query", "").lower()):
            return "both"
        elif "flight" in intent_list:
            return "flight"
        elif "hotel" in intent_list:
            return "hotel"
        else:
            return "unknown"
    
    def get_entities(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract entities from parsed data for use in agents.
        
        Args:
            parsed_data: Dictionary containing parsed intent and entities
            
        Returns:
            Dictionary with extracted entities
        """
        return {
            "source": parsed_data.get("source"),
            "destination": parsed_data.get("destination"),
            "start_date": parsed_data.get("start_date"),
            "end_date": parsed_data.get("end_date"),
            "duration": parsed_data.get("duration"),
            "passengers": parsed_data.get("passengers", 1),
            "cabin_class": parsed_data.get("cabin_class"),
            "additional_info": parsed_data.get("additional_info")
        }

