from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field, ConfigDict


class TripState(BaseModel):
    """
    Shared Pydantic state used by all agents in the LangGraph workflow.

    Every agent reads from and writes back to this state.
    """

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
    )

    # ==================================================
    # User / Session
    # ==================================================

    user_id: str = "default_user"

    raw_user_input: Optional[str] = None

    # Current session conversation
    conversation_history: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    # Retrieved from SQLite
    chat_history_db: List[Any] = Field(
        default_factory=list
    )

    # ==================================================
    # Long-Term Memory
    # ==================================================

    previous_trips: List[Any] = Field(
        default_factory=list
    )

    retrieved_memories: List[str] = Field(
        default_factory=list
    )

    # ==================================================
    # Trip Inputs
    # ==================================================

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

    preferences: List[str] = Field(
        default_factory=list
    )

    missing_fields: List[str] = Field(
        default_factory=list
    )

    # ==================================================
    # Agent Outputs
    # ==================================================

    weather_info: Dict[str, Any] = Field(
        default_factory=dict
    )

    destination_plan: Dict[str, Any] = Field(
        default_factory=dict
    )

    transport_plan: Dict[str, Any] = Field(
        default_factory=dict
    )

    budget_plan: Dict[str, Any] = Field(
        default_factory=dict
    )

    itinerary: Dict[str, Any] = Field(
        default_factory=dict
    )

    # ==================================================
    # Replanner
    # ==================================================
    
    original_budget_plan: Dict[str, Any] = Field(
    default_factory=dict
    )

    human_review_required: bool = False
    human_decision: Optional[str] = None

    revised_estimated_total: Optional[int] = None
    savings_amount: Optional[int] = None

    replan_changes: List[str] = Field(
        default_factory=list
    )
    needs_replanning: bool = False

    replan_reason: Optional[str] = None

    replan_count: int = 0

    replanner_message: Optional[str] = None

    # ==================================================
    # Final Output
    # ==================================================

    final_answer: Optional[str] = None

    # ==================================================
    # Compatibility Helpers
    # ==================================================

    def get(self, key, default=None):
        return getattr(self, key, default)

    def to_dict(self):
        return self.model_dump()


def state_to_dict(state):

    if isinstance(state, TripState):
        return state.model_dump()

    if isinstance(state, dict):
        return dict(state)

    if hasattr(state, "model_dump"):
        return state.model_dump()

    return dict(state)