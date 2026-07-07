from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field, ConfigDict


class TripState(BaseModel):
    """
    Shared Pydantic state used by all agents in the LangGraph workflow.

    Every agent reads from and writes back to this state.

    This replaces the earlier TypedDict-based TripState while keeping
    compatibility with existing code that uses state.get("field").
    """

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
    )

    raw_user_input: Optional[str] = None
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)

    destination: Optional[str] = None
    origin: Optional[str] = None

    dates: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    month: Optional[str] = None
    duration: Optional[int] = None

    travelers: Optional[str] = None
    number_of_people: Optional[int] = None
    budget: Optional[int] = None
    currency: str = "INR"
    travel_style: Optional[str] = None
    preferences: List[str] = Field(default_factory=list)

    missing_fields: List[str] = Field(default_factory=list)

    weather_info: Dict[str, Any] = Field(default_factory=dict)
    destination_plan: Dict[str, Any] = Field(default_factory=dict)
    transport_plan: Dict[str, Any] = Field(default_factory=dict)
    budget_plan: Dict[str, Any] = Field(default_factory=dict)
    itinerary: Dict[str, Any] = Field(default_factory=dict)

    needs_replanning: bool = False
    replan_reason: Optional[str] = None
    replan_count: int = 0
    replanner_message: Optional[str] = None

    final_answer: Optional[str] = None

    def get(self, key, default=None):
        """
        Provides dictionary-style access compatibility.

        This allows existing agent code like:
            state.get("destination")

        to continue working even if state is a Pydantic object.
        """

        return getattr(self, key, default)

    def to_dict(self):
        """
        Converts TripState into a normal Python dictionary.
        """

        return self.model_dump()


def state_to_dict(state):
    """
    Safely converts state into a plain dictionary.

    This helper allows your agents, graph routers, and app.py to work with:
    - normal dict state
    - Pydantic TripState state
    - any object that supports model_dump()
    """

    if isinstance(state, TripState):
        return state.model_dump()

    if isinstance(state, dict):
        return dict(state)

    if hasattr(state, "model_dump"):
        return state.model_dump()

    return dict(state)
