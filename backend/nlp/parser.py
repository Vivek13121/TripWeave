# LLM-powered parser with robust error handling
import re
import asyncio
import json
from typing import Dict, Any, Optional
from nlp.gemini_client import generate_text


def _heuristic_parse(user_message: str, error: Optional[str] = None) -> Dict[str, Any]:
    """Rule-based fallback parser."""
    text = user_message.strip()
    lower = text.lower()

    intent = []
    if any(k in lower for k in ["flight", "flights", "fly", "airline", "airlines", "plane"]):
        intent.append("flight")
    if any(k in lower for k in ["hotel", "hotels", "accommodation", "stay", "room", "rooms", "plan", "trip", "visit", "travel", "vacation"]):
        intent.append("hotel")

    source = None
    destination = None
    
    # Match "from X to Y" pattern
    m = re.search(r"\bfrom\s+(.+?)\s+to\s+(.+?)(?:[\.,;\n]|departing|returning|for|on|$)", text, flags=re.IGNORECASE)
    if m:
        source = m.group(1).strip() or None
        destination = m.group(2).strip() or None
        print(f"🎯 [PARSER] Regex extracted - Source: '{source}', Destination: '{destination}'")
    
    # Also check for "in LOCATION" or "to LOCATION" patterns
    if not destination:
        # Match "in LOCATION" pattern
        m = re.search(r"(?:hotel|hotels|stay|accommodation|room|rooms|trip|visit|travel|vacation)\s+(?:in|to)\s+([A-Za-z\s]+?)(?:[\.,;\n]|for|from|on|check|$)", text, flags=re.IGNORECASE)
        if m:
            destination = m.group(1).strip() or None
            print(f"🎯 [PARSER] Extracted destination: {destination}")

    # Extract dates
    start_date = None
    end_date = None
    
    # Match "departing on DATE" or "on DATE"
    m = re.search(r"(?:departing|departure|on)\s+(\d{4}-\d{2}-\d{2})", text, flags=re.IGNORECASE)
    if m:
        start_date = m.group(1)
    
    # Match "returning on DATE" or "return DATE"
    m = re.search(r"(?:returning|return)\s+(?:on\s+)?(\d{4}-\d{2}-\d{2})", text, flags=re.IGNORECASE)
    if m:
        end_date = m.group(1)
    
    # Match "check-in on DATE" or "check in DATE"
    if not start_date:
        m = re.search(r"check[- ]in\s+(?:on\s+)?(\d{4}-\d{2}-\d{2})", text, flags=re.IGNORECASE)
        if m:
            start_date = m.group(1)
    
    # Match "check-out on DATE" or "check out DATE"
    if not end_date:
        m = re.search(r"check[- ]out\s+(?:on\s+)?(\d{4}-\d{2}-\d{2})", text, flags=re.IGNORECASE)
        if m:
            end_date = m.group(1)
    
    # Extract additional info like passengers, cabin class, guests, rooms
    additional_info_parts = []
    passengers = 1  # Default
    cabin_class = None
    
    # Match "X passenger(s)"
    m = re.search(r"(\d+)\s+passenger(?:s)?", text, flags=re.IGNORECASE)
    if m:
        passengers = int(m.group(1))
        additional_info_parts.append(f"{m.group(1)} passenger(s)")
    
    # Match cabin class
    m = re.search(r"(economy|premium_economy|premium economy|business|first class|first)\s+class", text, flags=re.IGNORECASE)
    if m:
        cabin_class = m.group(1).replace('_', ' ').replace(' ', '_').upper()
        # Normalize to Amadeus format
        if cabin_class == "PREMIUM_ECONOMY":
            cabin_class = "PREMIUM_ECONOMY"
        elif cabin_class == "FIRST_CLASS" or cabin_class == "FIRST":
            cabin_class = "FIRST"
        elif cabin_class == "BUSINESS":
            cabin_class = "BUSINESS"
        elif cabin_class == "ECONOMY":
            cabin_class = "ECONOMY"
        additional_info_parts.append(f"{m.group(1).replace('_', ' ')} class")
    
    # Match "X guest(s)"
    m = re.search(r"(\d+)\s+guest(?:s)?", text, flags=re.IGNORECASE)
    if m:
        additional_info_parts.append(f"{m.group(1)} guest(s)")
    
    # Match "X room(s)"
    m = re.search(r"(\d+)\s+room(?:s)?", text, flags=re.IGNORECASE)
    if m:
        additional_info_parts.append(f"{m.group(1)} room(s)")
    
    # Match star rating
    m = re.search(r"(\d+)\s+star(?:s)?", text, flags=re.IGNORECASE)
    if m:
        additional_info_parts.append(f"{m.group(1)} star rating")

    duration = None
    m = re.search(r"\bfor\s+(\d+)\s+(?:day|days|night|nights)\b", lower)
    if m:
        try:
            duration = int(m.group(1))
        except ValueError:
            duration = None

    result: Dict[str, Any] = {
        "intent": intent,
        "source": source,
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "duration": duration,
        "passengers": passengers,
        "cabin_class": cabin_class,
        "additional_info": " ".join(additional_info_parts) if additional_info_parts else None,
        "original_query": user_message,
    }
    if error:
        result["error"] = error
    
    print(f"📋 [PARSER] Extracted: intent={intent}, source={source}, dest={destination}, dates={start_date}/{end_date}, passengers={passengers}, cabin={cabin_class}")
    return result


async def parse_user_message_async(user_message: str) -> Dict[str, Any]:
    """
    Smart hybrid parser: Try regex first, use LLM only if needed.
    This saves API quota while providing NLP flexibility.
    """
    print(f"🧠 [PARSER] Parsing: '{user_message}'")
    
    # Step 1: Try fast regex-based parsing first
    regex_result = _heuristic_parse(user_message)
    
    # Step 2: Check if regex extraction is sufficient
    has_intent = len(regex_result.get("intent", [])) > 0
    has_location = regex_result.get("destination") or regex_result.get("source")
    
    # If regex successfully extracted intent AND location, use it (no LLM needed)
    if has_intent and has_location:
        print(f"✅ [PARSER] Regex extraction sufficient: intent={regex_result['intent']}, locations found")
        return regex_result
    
    # Step 3: Regex failed or incomplete - use LLM for complex/ambiguous queries
    print(f"🤖 [PARSER] Regex incomplete (intent={has_intent}, location={has_location}), trying LLM...")
    
    prompt = f"""You are a JSON parser. Extract travel information and return ONLY the JSON object.

User message: "{user_message}"

Return this exact JSON structure (replace values, use null for missing):
{{"intent": ["flight", "hotel"], "source": null, "destination": "CityName", "start_date": null, "end_date": null, "duration": null, "additional_info": null}}

Rules:
- intent can be "flight", "hotel", or both
- If planning a trip/vacation, include "hotel"
- destination is the city being visited
- NO explanations, NO markdown, ONLY the JSON object

JSON:"""

    try:
        response = await generate_text(
            prompt,
            generation_config={"temperature": 0.1, "max_output_tokens": 300},
            timeout=10.0,
            use_google_search=False
        )
        
        # Extract JSON from response
        print(f"📄 [PARSER] LLM response: {response}")
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                parsed["original_query"] = user_message
                print(f"✅ [PARSER] LLM success: intent={parsed.get('intent')}, dest={parsed.get('destination')}")
                return parsed
            except json.JSONDecodeError as je:
                print(f"⚠️ [PARSER] Invalid JSON: {je}, using regex fallback")
                return regex_result
        else:
            print(f"⚠️ [PARSER] No JSON in LLM response (got {len(response)} chars), using regex fallback")
            return regex_result
            
    except Exception as e:
        print(f"❌ [PARSER] LLM failed: {e}, using regex result")
        return regex_result

