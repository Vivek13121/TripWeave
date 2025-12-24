from typing import TypedDict, Literal, Any
from langgraph.graph import StateGraph, END

# State for itinerary input collection
class ItineraryInputState(TypedDict, total=False):
    number_of_days: int | None
    destination: str | None
    travel_style: Literal["relaxed", "balanced", "packed"] | None
    budget_level: Literal["low", "medium", "high"] | None
    confirmed: bool | None
    current_step: str | None
    user_input: str | None
    response: str | None

# Node: Ask for number_of_days
async def ask_number_of_days(state: ItineraryInputState) -> dict[str, Any]:
    return {
        "current_step": "number_of_days",
        "response": "How many days will your trip be? (Please enter a number)"
    }

# Node: Validate number_of_days
async def validate_number_of_days(state: ItineraryInputState) -> dict[str, Any]:
    user_input = state.get("user_input", "")
    try:
        days = int(user_input)
        if days < 1 or days > 60:
            raise ValueError
        return {"number_of_days": days, "current_step": None}
    except Exception:
        return {"response": "Please enter a valid number of days (1-60).", "current_step": "number_of_days"}

# Node: Ask for destination
async def ask_destination(state: ItineraryInputState) -> dict[str, Any]:
    return {
        "current_step": "destination",
        "response": "What is your destination? (Please enter a city or country)"
    }

# Node: Validate destination
async def validate_destination(state: ItineraryInputState) -> dict[str, Any]:
    user_input = state.get("user_input", "")
    if user_input and isinstance(user_input, str) and len(user_input) > 1:
        return {"destination": user_input.strip(), "current_step": None}
    return {"response": "Please enter a valid destination (at least 2 characters).", "current_step": "destination"}

# Node: Ask for travel_style
async def ask_travel_style(state: ItineraryInputState) -> dict[str, Any]:
    return {
        "current_step": "travel_style",
        "response": "What is your travel style? (relaxed, balanced, packed)"
    }

# Node: Validate travel_style
async def validate_travel_style(state: ItineraryInputState) -> dict[str, Any]:
    user_input = state.get("user_input", "")
    valid = ["relaxed", "balanced", "packed"]
    if user_input in valid:
        return {"travel_style": user_input, "current_step": None}
    return {"response": "Please enter one of: relaxed, balanced, packed.", "current_step": "travel_style"}

# Node: Ask for budget_level
async def ask_budget_level(state: ItineraryInputState) -> dict[str, Any]:
    return {
        "current_step": "budget_level",
        "response": "What is your budget level? (low, medium, high)"
    }

# Node: Validate budget_level
async def validate_budget_level(state: ItineraryInputState) -> dict[str, Any]:
    user_input = state.get("user_input", "")
    valid = ["low", "medium", "high"]
    if user_input in valid:
        return {"budget_level": user_input, "current_step": None}
    return {"response": "Please enter one of: low, medium, high.", "current_step": "budget_level"}

# Node: Confirmation
async def confirm_inputs(state: ItineraryInputState) -> dict[str, Any]:
    summary = (
        f"You entered:\n"
        f"- Number of days: {state.get('number_of_days')}\n"
        f"- Destination: {state.get('destination')}\n"
        f"- Travel style: {state.get('travel_style')}\n"
        f"- Budget level: {state.get('budget_level')}\n"
        "Is this correct? (yes/no or type the field to change)"
    )
    return {"current_step": "confirmation", "response": summary}

# Node: Handle confirmation
async def handle_confirmation(state: ItineraryInputState) -> dict[str, Any]:
    user_input = state.get("user_input", "")
    if user_input.lower() == "yes":
        return {"confirmed": True, "response": "Thank you! Your itinerary input is complete."}
    elif user_input.lower() == "no":
        return {"response": "Which field would you like to change? (number_of_days, destination, travel_style, budget_level)", "current_step": "confirmation"}
    elif user_input in ["number_of_days", "destination", "travel_style", "budget_level"]:
        return {"current_step": user_input, "response": f"Okay, let's update {user_input}."}
    else:
        return {"response": "Please reply 'yes', 'no', or the field name to change.", "current_step": "confirmation"}

# Build the LangGraph
workflow = StateGraph(ItineraryInputState)
workflow.add_node("ask_number_of_days", ask_number_of_days)
workflow.add_node("validate_number_of_days", validate_number_of_days)
workflow.add_node("ask_destination", ask_destination)
workflow.add_node("validate_destination", validate_destination)
workflow.add_node("ask_travel_style", ask_travel_style)
workflow.add_node("validate_travel_style", validate_travel_style)
workflow.add_node("ask_budget_level", ask_budget_level)
workflow.add_node("validate_budget_level", validate_budget_level)
workflow.add_node("confirm_inputs", confirm_inputs)
workflow.add_node("handle_confirmation", handle_confirmation)

# Edges for deterministic flow
workflow.set_entry_point("ask_number_of_days")
workflow.add_edge("ask_number_of_days", "validate_number_of_days")
workflow.add_edge("validate_number_of_days", "ask_destination")
workflow.add_edge("ask_destination", "validate_destination")
workflow.add_edge("validate_destination", "ask_travel_style")
workflow.add_edge("ask_travel_style", "validate_travel_style")
workflow.add_edge("validate_travel_style", "ask_budget_level")
workflow.add_edge("ask_budget_level", "validate_budget_level")
workflow.add_edge("validate_budget_level", "confirm_inputs")
workflow.add_edge("confirm_inputs", "handle_confirmation")
workflow.add_edge("handle_confirmation", END)

app = workflow.compile()
