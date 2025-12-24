from typing import TypedDict, Any
from langgraph.graph import StateGraph, END
from agents.coordinator_agent import CoordinatorAgent
from agents.flight_agent import FlightAgent
from agents.hotel_agent import HotelAgent
import asyncio


class State(TypedDict):
    user_message: str
    parsed_data: dict[str, Any]
    intent: str
    source: str | None
    destination: str | None
    start_date: str | None
    end_date: str | None
    duration: int | None
    passengers: int | None
    cabin_class: str | None
    additional_info: str | None
    flight_results: list[str]
    hotel_results: list[str]


def coordinator_node(state: State) -> dict[str, Any]:
    """Coordinator node that sets intent + entities from structured NLP output."""
    coordinator = CoordinatorAgent()

    parsed_data = state.get("parsed_data", {})
    intent = coordinator.process_intent(parsed_data)
    entities = coordinator.get_entities(parsed_data)

    return {
        "intent": intent,
        "source": entities.get("source"),
        "destination": entities.get("destination"),
        "start_date": entities.get("start_date"),
        "end_date": entities.get("end_date"),
        "duration": entities.get("duration"),
        "passengers": entities.get("passengers", 1),
        "cabin_class": entities.get("cabin_class"),
        "additional_info": entities.get("additional_info"),
    }


async def flight_agent_node(state: State) -> State:
    if state["intent"] not in ["flight", "both"]:
        return {}

    agent = FlightAgent()

    try:
        results = await agent.search_flights(
            source=state.get("source"),
            destination=state.get("destination"),
            start_date=state.get("start_date"),  # Maps to departure_date in Amadeus
            passengers=state.get("passengers", 1),
            cabin_class=state.get("cabin_class")
        )

        # Return only the field we're updating - LangGraph will merge it
        # Replace existing flight_results (don't append) to avoid duplicates
        return {
            "flight_results": results
        }

    except asyncio.CancelledError:
        raise
    except Exception as e:
        # Log but don't crash - return empty results
        print(f"❌ [FLIGHT_NODE] Unexpected error: {e}")
        return {"flight_results": []}




async def hotel_agent_node(state: State) -> State:
    if state["intent"] not in ["hotel", "both"]:
        return {}

    agent = HotelAgent()

    try:
        results = await agent.search_hotels(
            destination=state.get("destination"),
            start_date=state.get("start_date"),
            end_date=state.get("end_date"),
            duration=state.get("duration"),
            additional_info=state.get("additional_info"),
        )

        # Return only the field we're updating - LangGraph will merge it
        return {
            "hotel_results": state.get("hotel_results", []) + results
        }

    except asyncio.CancelledError:
        raise




# Create the graph
workflow = StateGraph(State)

# Add nodes
workflow.add_node("coordinator", coordinator_node)
workflow.add_node("flight_agent", flight_agent_node)
workflow.add_node("hotel_agent", hotel_agent_node)

# Set entry point
workflow.set_entry_point("coordinator")


# After coordinator, always go to flight_agent
workflow.add_edge("coordinator", "flight_agent")

# After flight_agent, go to hotel_agent
workflow.add_edge("flight_agent", "hotel_agent")

# After hotel_agent, go to END
workflow.add_edge("hotel_agent", END)

# Compile the graph
app = workflow.compile()
