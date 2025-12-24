from typing import TypedDict, Literal, Any, List, Dict
from langgraph.graph import StateGraph, END
import random

# --- State Definition ---
class ItineraryPlanningState(TypedDict, total=False):
    number_of_days: int
    destination: str
    travel_style: Literal["relaxed", "balanced", "packed"]
    budget_level: Literal["low", "medium", "high"]
    skeleton: List[Dict[str, Any]]
    activities: List[Dict[str, Any]]
    assignments: List[Dict[str, Any]]
    validation_passed: bool
    final_itinerary: List[Dict[str, Any]]
    validation_errors: List[str]
    current_step: str

# --- Agent 1: ItineraryPlannerAgent ---
def itinerary_planner_agent(state: ItineraryPlanningState) -> Dict[str, Any]:
    days = state["number_of_days"]
    travel_style = state["travel_style"]
    skeleton = []
    # Activity density by style
    density = {"relaxed": (1,2), "balanced": (2,3), "packed": (3,4)}
    min_a, max_a = density[travel_style]
    for day in range(1, days+1):
        skeleton.append({
            "day": day,
            "slots": {
                "morning": [],
                "afternoon": [],
                "evening": []
            },
            "min_activities": min_a,
            "max_activities": max_a
        })
    return {"skeleton": skeleton, "current_step": "activity_research"}

# --- Agent 2: ActivityResearchAgent ---
def activity_research_agent(state: ItineraryPlanningState) -> Dict[str, Any]:
    # Simulate web search (replace with real search in production)
    # Categories: sightseeing, food, cultural, leisure
    destination = state["destination"]
    # For demo, use static activities
    all_activities = [
        {"name": f"{destination} Museum", "type": "cultural"},
        {"name": f"{destination} Park", "type": "leisure"},
        {"name": f"{destination} Landmark", "type": "sightseeing"},
        {"name": f"{destination} Food Market", "type": "food"},
        {"name": f"{destination} Art Gallery", "type": "cultural"},
        {"name": f"{destination} River Walk", "type": "leisure"},
        {"name": f"{destination} Historic Site", "type": "sightseeing"},
        {"name": f"{destination} Local Eatery", "type": "food"},
        {"name": f"{destination} Festival", "type": "cultural"},
        {"name": f"{destination} Botanical Garden", "type": "leisure"},
    ]
    return {"activities": all_activities, "current_step": "assignment"}

# --- Agent 3: DayAssignmentAgent ---
def day_assignment_agent(state: ItineraryPlanningState) -> Dict[str, Any]:
    skeleton = state["skeleton"]
    activities = state["activities"][:]
    random.shuffle(activities)
    assignments = []
    used = set()
    for day in skeleton:
        slots = ["morning", "afternoon", "evening"]
        min_a = day["min_activities"]
        max_a = day["max_activities"]
        n_acts = random.randint(min_a, max_a)
        acts_for_day = []
        for _ in range(n_acts):
            for act in activities:
                if act["name"] not in used:
                    acts_for_day.append(act)
                    used.add(act["name"])
                    break
        # Assign to slots
        slot_assignments = {slot: [] for slot in slots}
        for idx, act in enumerate(acts_for_day):
            slot = slots[idx % 3]
            slot_assignments[slot].append(act)
        assignments.append({"day": day["day"], "slots": slot_assignments})
    return {"assignments": assignments, "current_step": "validation"}

# --- Agent 4: ItineraryValidationAgent ---
def itinerary_validation_agent(state: ItineraryPlanningState) -> Dict[str, Any]:
    assignments = state["assignments"]
    skeleton = state["skeleton"]
    valid = True
    errors = []
    # Validate each day
    for idx, day in enumerate(skeleton):
        assigned = assignments[idx]["slots"]
        acts = sum(len(v) for v in assigned.values())
        if acts < day["min_activities"]:
            valid = False
            errors.append(f"Day {day['day']} has too few activities.")
        if acts > day["max_activities"]:
            valid = False
            errors.append(f"Day {day['day']} has too many activities.")
        if acts == 0:
            valid = False
            errors.append(f"Day {day['day']} is empty.")
        if state["travel_style"] == "relaxed" and acts > 2:
            valid = False
            errors.append(f"Day {day['day']} is too busy for relaxed style.")
    # If not valid, adjust: remove extras, add rest
    if not valid:
        # Simple fix: trim to max, add 'Rest' if too few
        for idx, day in enumerate(skeleton):
            assigned = assignments[idx]["slots"]
            acts = sum(len(v) for v in assigned.values())
            if acts > day["max_activities"]:
                # Remove extras
                for slot in ["evening", "afternoon", "morning"]:
                    while acts > day["max_activities"] and assigned[slot]:
                        assigned[slot].pop()
                        acts -= 1
            if acts < day["min_activities"]:
                for slot in ["morning", "afternoon", "evening"]:
                    if acts < day["min_activities"]:
                        assigned[slot].append({"name": "Rest", "type": "leisure"})
                        acts += 1
        return {"assignments": assignments, "validation_passed": False, "validation_errors": errors, "current_step": "assignment"}
    # If valid, finalize
    return {"final_itinerary": assignments, "validation_passed": True, "validation_errors": [], "current_step": "done"}

# --- LangGraph Construction ---
workflow = StateGraph(ItineraryPlanningState)
workflow.add_node("planner", itinerary_planner_agent)
workflow.add_node("activity_research", activity_research_agent)
workflow.add_node("assignment", day_assignment_agent)
workflow.add_node("validation", itinerary_validation_agent)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "activity_research")
workflow.add_edge("activity_research", "assignment")
workflow.add_edge("assignment", "validation")

# Conditional routing from validation
def should_continue(state: ItineraryPlanningState) -> str:
    return "assignment" if not state.get("validation_passed", False) else END

workflow.add_conditional_edges("validation", should_continue, {"assignment": "assignment", END: END})

app = workflow.compile()
