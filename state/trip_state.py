from typing import TypedDict, List, Dict, Any, Optional


class TripState(TypedDict, total=False):
    """
    Shared state used by all agents in the LangGraph workflow.
    Every agent reads from and writes back to this state.
    """

    raw_user_input: str
    conversation_history: List[Dict[str, str]]

    destination: Optional[str]
    origin: Optional[str]

    dates: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    month: Optional[str]
    duration: Optional[int]

    travelers: Optional[str]
    number_of_people: Optional[int]
    budget: Optional[int]
    currency: str
    travel_style: Optional[str]
    preferences: List[str]

    missing_fields: List[str]
    weather_info: Dict[str, Any]
    destination_plan: Dict[str, Any]
    transport_plan: Dict[str, Any]
    budget_plan: Dict[str, Any]
    itinerary: Dict[str, Any]

    needs_replanning: bool
    replan_reason: Optional[str]
    replan_count: int

    final_answer: str
