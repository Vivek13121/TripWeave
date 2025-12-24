from fastapi import APIRouter
from graph.itinerary_planning_graph import app as planning_graph
from schemas import ChatResponse

router = APIRouter()

# This endpoint expects all required structured inputs in the request state
@router.post("/plan_itinerary", response_model=ChatResponse)
async def plan_itinerary(state: dict):
    # Run the planning graph
    result = await planning_graph.ainvoke(state)
    # Return only the structured itinerary
    return ChatResponse(response="Itinerary planned.", intent=None, flight_results=[], hotel_results=[], itinerary=result.get("final_itinerary"))
