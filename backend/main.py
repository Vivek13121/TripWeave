from dotenv import load_dotenv
load_dotenv()
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from schemas import ChatRequest, ChatResponse, HealthResponse
from graph.travel_graph import app as workflow_app
from graph.itinerary_input_graph import app as itinerary_input_app
from graph.itinerary_planning_graph import app as itinerary_planning_app
from plan_router import router as plan_router
from nlp.itinerary_narrator import narrate_itinerary
from nlp.parser import parse_user_message_async
from nlp.summarizer import (
    summarize_flight_results_async,
    summarize_hotel_results_async,
)








app = FastAPI()
app.include_router(plan_router)

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to track the currently running LangGraph task
current_task = None
last_processed_message = None
last_processed_time = 0

# Session state for each user (in-memory, replace with persistent store for production)
user_sessions = {}


@app.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(
        status="healthy",
        message="Travel Agent API is running"
    )


async def run_workflow(message: str, parsed_data: dict):
    """Async wrapper for the LangGraph workflow invocation."""
    result = await workflow_app.ainvoke({
        "user_message": message,
        "parsed_data": parsed_data,
        "intent": "",
        "source": None,
        "destination": None,
        "start_date": None,
        "end_date": None,
        "duration": None,
        "additional_info": None,
        "flight_results": [],
        "hotel_results": []
    })
    return result


# Old flight/hotel endpoint removed - unified in itinerary_chat below

# --- Unified /chat endpoint supporting itinerary, flights, and hotels ---
@app.post("/chat", response_model=ChatResponse)
async def unified_chat(request: ChatRequest):
    global current_task, last_processed_message, last_processed_time
    
    # For demo: use a single session (replace with user/session id for multi-user)
    session_id = "default"
    session = user_sessions.get(session_id, {
        "state": {},
        "step": None,
        "graph": "itinerary_input"
    })

    user_input = request.message.strip()
    
    # Detect if this is a flight/hotel search query (contains keywords)
    lower_msg = user_input.lower()
    is_flight_query = any(k in lower_msg for k in ["find flights", "search flights", "flight from", "flights from"])
    is_hotel_query = any(k in lower_msg for k in ["find hotels", "search hotels", "hotel in", "hotels in"])
    
    # FLIGHT/HOTEL FLOW - Process immediately
    if is_flight_query or is_hotel_query:
        print(f"🔵 [MAIN] ========== FLIGHT/HOTEL REQUEST ==========")
        print(f"📩 [MAIN] Message: '{request.message}'")
        
        # Prevent duplicate requests
        import time
        current_time = time.time()
        if (last_processed_message == request.message and 
            current_time - last_processed_time < 2.0):
            print(f"⚠️ [MAIN] DUPLICATE REQUEST DETECTED - Ignoring")
            return ChatResponse(
                response="Processing your previous request...",
                intent=None,
                flight_results=[],
                hotel_results=[],
            )
        
        last_processed_message = request.message
        last_processed_time = current_time
        
        # Cancel existing task if running
        if current_task is not None and not current_task.done():
            current_task.cancel()
            try:
                await current_task
            except asyncio.CancelledError:
                pass
        
        # Parse user message for context
        parsed_data = await parse_user_message_async(request.message)
        
        # Build query context for summarization
        query_context_parts = []
        if parsed_data.get("source"):
            query_context_parts.append(f"from {parsed_data['source']}")
        if parsed_data.get("destination"):
            query_context_parts.append(f"to {parsed_data['destination']}")
        if parsed_data.get("start_date"):
            query_context_parts.append(f"on {parsed_data['start_date']}")
        
        query_context = " ".join(query_context_parts) if query_context_parts else request.message
        
        # Start workflow task
        current_task = asyncio.create_task(run_workflow(request.message, parsed_data))
        result = await current_task
        
        # Extract results
        flight_results = result.get("flight_results", [])
        hotel_results = result.get("hotel_results", [])
        intent = result.get("intent", "")
        
        print(f"🎯 [MAIN] Intent: '{intent}', Flights: {len(flight_results)}, Hotels: {len(hotel_results)}")
        
        # For flights, skip LLM summarization - let frontend display real Amadeus data
        if intent == "flight":
            if flight_results:
                print(f"✅ [MAIN] Returning {len(flight_results)} real Amadeus flights without LLM summarization")
                reply = f"Found {len(flight_results)} available flights from {query_context or 'your search'}."
            else:
                print(f"⚠️ [MAIN] No flights found for this route")
                reply = (
                    f"No flights available for {query_context or 'this route'}. "
                    "This may be due to:\n"
                    "• No flights available for this date\n"
                    "• Limited test API data for this route\n"
                    "• Route not served by available airlines\n\n"
                    "Try searching for a different date or popular routes like DEL→BOM, DEL→BLR, or BOM→GOI."
                )
        elif intent == "hotel" and hotel_results:
            reply = await summarize_hotel_results_async(hotel_results, query_context)
        elif intent == "both" and (flight_results or hotel_results):
            # For combined, only summarize hotels if present
            if hotel_results and not flight_results:
                reply = await summarize_hotel_results_async(hotel_results, query_context)
            elif flight_results and not hotel_results:
                reply = f"Found {len(flight_results)} available flights from {query_context or 'your search'}."
            else:
                reply = f"Found {len(flight_results)} flights and {len(hotel_results)} hotels from {query_context or 'your search'}."
        else:
            reply = "I couldn't find any results. Please try rephrasing with more details."

        return ChatResponse(
            response=reply,
            intent=intent or None,
            flight_results=flight_results,
            hotel_results=hotel_results,
        )
    
    # ITINERARY FLOW - Collect sequential inputs
    state = session["state"]
    
    if not state:
        state = {"collected": []}
        
    collected = state.get("collected", [])
    collected.append(user_input)
    
    # Collect 5 inputs: days, destination, style, budget, confirmation
    if len(collected) < 5:
        state["collected"] = collected
        user_sessions[session_id] = {"state": state, "step": None, "graph": "itinerary_input"}
        return ChatResponse(response="Processing...")
    
    # All inputs collected - plan itinerary
    try:
        number_of_days = int(collected[0])
        destination = collected[1]
        travel_style = collected[2]
        budget_level = collected[3]
        
        planning_state = {
            "number_of_days": number_of_days,
            "destination": destination,
            "travel_style": travel_style,
            "budget_level": budget_level
        }
        plan_result = await itinerary_planning_app.ainvoke(planning_state)
        final_itin = plan_result.get("final_itinerary")
        
        # Generate narrative
        narration = await narrate_itinerary(
            final_itin,
            travel_style,
            budget_level,
            destination
        )
        user_sessions[session_id] = {"state": {}, "step": None, "graph": "itinerary_input"}
        return ChatResponse(response=narration, itinerary=final_itin)
    except Exception as e:
        print(f"Error planning itinerary: {e}")
        user_sessions[session_id] = {"state": {}, "step": None, "graph": "itinerary_input"}
        return ChatResponse(response=f"Error planning itinerary: {str(e)}")
