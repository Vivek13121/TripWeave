import os
from nlp.gemini_client import generate_text
from typing import List, Dict

LLM_NARRATION_ENABLED = os.environ.get("LLM_NARRATION_ENABLED", "1") == "1"

async def narrate_itinerary(itinerary: List[Dict], travel_style: str, budget_level: str, destination: str) -> str:
    """
    Use LLM ONCE at the final stage to generate a polished, natural-language narrative.
    Input: Structured itinerary + user preferences.
    Output: Professional, flowing prose like a travel advisor would write.
    Fallback to readable text if LLM fails or is disabled.
    """
    if not itinerary:
        return "No itinerary available."
    if not LLM_NARRATION_ENABLED:
        return readable_itinerary(itinerary, travel_style, budget_level, destination)
    try:
        # Build a structured summary for the LLM
        days_summary = []
        for day in itinerary:
            day_num = day.get("day", "?")
            slots = day.get("slots", {})
            morning = slots.get("morning", [])
            afternoon = slots.get("afternoon", [])
            evening = slots.get("evening", [])
            day_text = f"Day {day_num}: "
            parts = []
            if morning:
                parts.append(f"Morning - {', '.join(a['name'] for a in morning)}")
            if afternoon:
                parts.append(f"Afternoon - {', '.join(a['name'] for a in afternoon)}")
            if evening:
                parts.append(f"Evening - {', '.join(a['name'] for a in evening)}")
            day_text += "; ".join(parts) if parts else "Free day"
            days_summary.append(day_text)
        
        itinerary_text = "\n".join(days_summary)
        
        prompt = (
            f"You are a professional travel advisor. Write a comprehensive, detailed narrative guide "
            f"for a {len(itinerary)}-day trip to {destination}.\n\n"
            f"User Preferences:\n"
            f"- Travel Style: {travel_style} (relaxed = fewer activities, balanced = moderate, packed = many activities)\n"
            f"- Budget Level: {budget_level}\n\n"
            f"Structured Itinerary:\n{itinerary_text}\n\n"
            f"Instructions:\n"
            f"- This is the PRIMARY content the client will read\n"
            f"- Start with a proper introduction (2-3 paragraphs) explaining:\n"
            f"  * The overall vision and theme of this {destination} trip\n"
            f"  * How the {travel_style} pace and {budget_level} budget shape the experience\n"
            f"  * Key highlights they can look forward to\n"
            f"- Then write a DETAILED paragraph for EACH day:\n"
            f"  * Day 1: [Describe the day's flow, morning activities, afternoon plans, evening wrap-up]\n"
            f"  * Day 2: [Same detailed treatment]\n"
            f"  * Continue for all {len(itinerary)} days\n"
            f"- Each day should be 3-5 sentences minimum, describing:\n"
            f"  * What they'll experience and why it fits the itinerary\n"
            f"  * Transitions between activities\n"
            f"  * The reasoning behind the pacing\n"
            f"  * If a slot is empty/free, describe it as intentional rest or flexible time\n"
            f"- End with a warm conclusion (1-2 paragraphs)\n"
            f"- FORMATTING RULES:\n"
            f"  * Use PLAIN TEXT ONLY - NO markdown symbols (no #, ##, ###, *, **, _, etc.)\n"
            f"  * Use simple paragraph breaks between sections\n"
            f"  * Start day sections with 'Day 1:', 'Day 2:', etc. (no hashtags)\n"
            f"  * Write in flowing, coherent prose (NOT bullet points)\n"
            f"- Be warm, engaging, and thorough\n"
            f"- Sound like a knowledgeable advisor who has personally designed this journey\n"
            f"- IMPORTANT: Complete the ENTIRE narrative without cutting off mid-sentence\n\n"
            f"Write the complete travel guide narrative:"
        )
        response = await generate_text(prompt, generation_config={"temperature": 0.6, "max_output_tokens": 4096})
        return response.strip()
    except Exception as e:
        print(f"[NARRATOR] LLM failed: {e}")
        return readable_itinerary(itinerary, travel_style, budget_level, destination)

def readable_itinerary(itinerary: List[Dict], travel_style: str, budget_level: str, destination: str) -> str:
    """
    Fallback: Generate a detailed, narrative-style guide when LLM is disabled or fails.
    This should be comprehensive prose, not a shallow summary.
    """
    if not itinerary:
        return "Your itinerary could not be generated at this time."
    
    num_days = len(itinerary)
    
    # Opening introduction
    intro = (
        f"Welcome to your {num_days}-day journey to {destination}! "
        f"This itinerary has been thoughtfully designed to match your {travel_style} travel style "
        f"and {budget_level} budget preferences. "
    )
    
    # Describe the approach
    if travel_style == "relaxed":
        pace_desc = (
            "We've prioritized rest and flexibility throughout your trip. Each day features just one or two "
            "key activities, leaving plenty of room for spontaneous exploration, leisurely meals, and recharging. "
            "This approach ensures you can truly savor each experience without feeling rushed."
        )
    elif travel_style == "packed":
        pace_desc = (
            "This is an action-packed schedule designed to help you experience as much as possible during your stay. "
            "Each day is filled with diverse activities from morning through evening, maximizing your time in "
            f"{destination}. While ambitious, the itinerary is carefully balanced to maintain energy and enthusiasm."
        )
    else:
        pace_desc = (
            "The itinerary strikes a thoughtful balance between exploration and downtime. You'll have structured "
            "activities to ensure you see the highlights, while still maintaining breathing room for rest, "
            "spontaneous discoveries, and personal reflection."
        )
    
    intro += pace_desc + "\n\n"
    
    # Day-by-day detailed descriptions
    day_descriptions = []
    for day in itinerary:
        day_num = day.get("day", "?")
        slots = day.get("slots", {})
        morning = slots.get("morning", [])
        afternoon = slots.get("afternoon", [])
        evening = slots.get("evening", [])
        
        day_text = f"Day {day_num}: "
        
        # Build descriptive narrative for the day
        day_parts = []
        if morning:
            morning_names = ", ".join(a["name"] for a in morning)
            day_parts.append(f"Your morning begins with {morning_names}")
        else:
            day_parts.append("Your morning is kept free for a leisurely start")
        
        if afternoon:
            afternoon_names = ", ".join(a["name"] for a in afternoon)
            day_parts.append(f"followed by {afternoon_names} in the afternoon")
        else:
            day_parts.append("with the afternoon left open for exploration at your own pace")
        
        if evening:
            evening_names = ", ".join(a["name"] for a in evening)
            day_parts.append(f"The day concludes with {evening_names}")
        else:
            day_parts.append("The evening is yours to enjoy as you wish")
        
        day_text += ", ".join(day_parts[:2])
        if len(day_parts) > 2:
            day_text += ". " + day_parts[2]
        day_text += "."
        
        day_descriptions.append(day_text)
    
    days_narrative = "\n\n".join(day_descriptions)
    
    # Closing
    closing = (
        f"\n\nThis {num_days}-day itinerary provides a complete framework for your {destination} adventure. "
        "Each activity has been selected to showcase the destination's character while respecting your "
        "preferences and budget. The detailed breakdown below allows you to see the full structure and "
        "make any adjustments that suit your interests. Enjoy your journey!"
    )
    
    return intro + days_narrative + closing
