"""LLM-powered result summarization with fallback."""

import asyncio
from typing import List, Optional
from nlp.gemini_client import generate_text


async def summarize_flight_results_async(
    results: List[str],
    query_context: Optional[str] = None
) -> str:
    """Summarize flight results using Gemini LLM."""
    print(f"📝 [SUMMARIZER] Starting flight summary for {len(results)} results")
    if not results:
        return "No flight results found."
    
    system_prompt = """You are a professional travel assistant AI. Your task is to provide a COMPLETE and DETAILED summary of flight search results.

IMPORTANT INSTRUCTIONS:
- Write a FULL, COMPREHENSIVE response (NOT just 1-2 lines)
- Include ALL important details: airlines, prices, departure times, duration
- Provide helpful insights and recommendations
- Compare different options if multiple are available
- Write in complete paragraphs with proper structure
- Aim for 4-6 sentences minimum
- Make the response conversational and helpful
- DO NOT stop mid-sentence - complete your thoughts fully"""

    results_text = "\n".join(f"- {r}" for r in results[:5])
    context = f" for {query_context}" if query_context else ""
    
    prompt = f"{system_prompt}\n\nSearch Query{context}\n\nFlight Results:\n{results_text}\n\nProvide your complete, detailed summary (4-6 sentences minimum):"
    
    try:
        print(f"📤 [SUMMARIZER] Calling Gemini LLM for summarization...")
        summary = await generate_text(
            prompt,
            generation_config={
                "temperature": 0.4,
                "max_output_tokens": 1500,
            }
        )
        print(f"✅ [SUMMARIZER] LLM summarized successfully: '{summary[:80]}...'")
        return f"✨ {summary}"
    except Exception as e:
        print(f"❌ [SUMMARIZER] LLM FAILED: {type(e).__name__}: {e}")
        fallback = f"[FALLBACK - API NOT USED] Found {len(results)} flight option(s). Check details below."
        print(f"🔄 [SUMMARIZER] Using fallback: '{fallback}'")
        return fallback


async def summarize_hotel_results_async(
    results: List[str],
    query_context: Optional[str] = None
) -> str:
    """Summarize hotel results using Gemini LLM."""
    if not results:
        return "No hotel results found."
    
    system_prompt = """You are a professional travel assistant AI. Your task is to provide a COMPLETE and DETAILED summary of hotel search results.

IMPORTANT INSTRUCTIONS:
- Write a FULL, COMPREHENSIVE response (NOT just 1-2 lines)
- Include ALL important details: hotel names, prices, ratings, amenities, locations
- Provide helpful insights and recommendations
- Compare different options if multiple are available
- Write in complete paragraphs with proper structure
- Aim for 4-6 sentences minimum
- Make the response conversational and helpful
- DO NOT stop mid-sentence - complete your thoughts fully"""

    results_text = "\n".join(f"- {r}" for r in results[:5])
    context = f" for {query_context}" if query_context else ""
    
    prompt = f"{system_prompt}\n\nSearch Query{context}\n\nHotel Results:\n{results_text}\n\nProvide your complete, detailed summary (4-6 sentences minimum):"
    
    try:
        summary = await generate_text(
            prompt,
            generation_config={
                "temperature": 0.4,
                "max_output_tokens": 1500,
            }
        )
        print(f"✅ LLM summarized {len(results)} hotel results")
        return f"✨ {summary}"
    except Exception as e:
        print(f"⚠️ LLM summarization failed: {e}")
        return f"[FALLBACK - API NOT USED] Found {len(results)} hotel option(s). Check details below."


async def summarize_combined_results_async(
    flight_results: List[str],
    hotel_results: List[str],
    query_context: Optional[str] = None
) -> str:
    """Summarize combined flight and hotel results."""
    if not flight_results and not hotel_results:
        return "No results found."
    
    if not hotel_results:
        return await summarize_flight_results_async(flight_results, query_context)
    if not flight_results:
        return await summarize_hotel_results_async(hotel_results, query_context)
    
    system_prompt = """You are a professional travel assistant AI. Your task is to provide a COMPLETE and DETAILED summary of a complete trip package including flights and hotels.

IMPORTANT INSTRUCTIONS:
- Write a FULL, COMPREHENSIVE response (NOT just 1-2 lines)
- Include ALL important details about both flights AND hotels
- Provide helpful insights about the complete trip package
- Suggest optimal combinations or best value options
- Write in complete paragraphs with proper structure
- Aim for 5-8 sentences minimum
- Make the response conversational and helpful
- Cover both transportation and accommodation thoroughly
- DO NOT stop mid-sentence - complete your thoughts fully"""

    flights_text = "\n".join(f"- {r}" for r in flight_results[:3])
    hotels_text = "\n".join(f"- {r}" for r in hotel_results[:3])
    context = f" for {query_context}" if query_context else ""
    
    prompt = f"{system_prompt}\n\nTrip Query{context}\n\nFlight Options:\n{flights_text}\n\nHotel Options:\n{hotels_text}\n\nProvide your complete, detailed trip summary (5-8 sentences minimum):"
    
    try:
        summary = await generate_text(
            prompt,
            generation_config={
                "temperature": 0.4,
                "max_output_tokens": 2000,
            }
        )
        print(f"✅ LLM summarized {len(flight_results)} flights + {len(hotel_results)} hotels")
        return f"✨ {summary}"
    except Exception as e:
        print(f"⚠️ LLM summarization failed: {e}")
        return f"[FALLBACK - API NOT USED] Found {len(flight_results)} flight(s) and {len(hotel_results)} hotel(s). Check details below."
