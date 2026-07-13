from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from agents.budget_agent import budget_agent
from agents.destination_agent import destination_agent
from agents.human_review_agent import human_review_agent
from agents.itinerary_composer_agent import (
    itinerary_composer_agent,
)
from agents.planner_agent import planner_agent
from agents.replanner_agent import replanner_agent
from agents.transport_agent import transport_agent
from agents.weather_agent import weather_agent
from memory.memory_agent import (
    memory_retriever_agent,
    memory_saver_agent,
)
from state.trip_state import (
    TripState,
    state_to_dict,
)
from utils.logger_config import setup_logger


logger = setup_logger(__name__)


def should_continue_after_planner(state):
    state = state_to_dict(state)

    if state.get("missing_fields"):
        return "end"

    return "weather"


def budget_router(state):
    state = state_to_dict(state)

    if state.get("human_review_required"):
        return "human_review"

    return "composer"


def human_review_router(state):
    state = state_to_dict(state)

    action = state.get("human_decision")

    if action == "approve_replan":
        return "replanner"

    if action == "update_budget":
        return "budget"

    return "composer"


def build_trip_graph():
    logger.info(
        "Building Trip Graph with human-in-the-loop review"
    )

    graph_builder = StateGraph(TripState)

    graph_builder.add_node(
        "memory_retriever",
        memory_retriever_agent,
    )

    graph_builder.add_node(
        "planner",
        planner_agent,
    )

    graph_builder.add_node(
        "weather",
        weather_agent,
    )

    graph_builder.add_node(
        "destination",
        destination_agent,
    )

    graph_builder.add_node(
        "transport",
        transport_agent,
    )

    graph_builder.add_node(
        "budget",
        budget_agent,
    )

    graph_builder.add_node(
        "human_review",
        human_review_agent,
    )

    graph_builder.add_node(
        "replanner",
        replanner_agent,
    )

    graph_builder.add_node(
        "composer",
        itinerary_composer_agent,
    )

    graph_builder.add_node(
        "memory_saver",
        memory_saver_agent,
    )

    graph_builder.set_entry_point(
        "memory_retriever"
    )

    graph_builder.add_edge(
        "memory_retriever",
        "planner",
    )

    graph_builder.add_conditional_edges(
        "planner",
        should_continue_after_planner,
        {
            "weather": "weather",
            "end": END,
        },
    )

    graph_builder.add_edge(
        "weather",
        "destination",
    )

    graph_builder.add_edge(
        "destination",
        "transport",
    )

    graph_builder.add_edge(
        "transport",
        "budget",
    )

    graph_builder.add_conditional_edges(
        "budget",
        budget_router,
        {
            "human_review": "human_review",
            "composer": "composer",
        },
    )

    graph_builder.add_conditional_edges(
        "human_review",
        human_review_router,
        {
            "replanner": "replanner",
            "budget": "budget",
            "composer": "composer",
        },
    )

    # The revised budget is created directly by Replanner.
    # It then goes to Composer so the revised itinerary is displayed.
    graph_builder.add_edge(
        "replanner",
        "composer",
    )

    graph_builder.add_edge(
        "composer",
        "memory_saver",
    )

    graph_builder.add_edge(
        "memory_saver",
        END,
    )

    checkpointer = MemorySaver()

    compiled_graph = graph_builder.compile(
        checkpointer=checkpointer,
    )

    logger.info(
        "Trip Graph compiled successfully with HITL support"
    )

    return compiled_graph


trip_graph = build_trip_graph()