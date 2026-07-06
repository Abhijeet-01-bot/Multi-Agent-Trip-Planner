from langgraph.graph import StateGraph, END

from state.trip_state import TripState

from agents.planner_agent import planner_agent
from agents.weather_agent import weather_agent
from agents.destination_agent import destination_agent
from agents.transport_agent import transport_agent
from agents.budget_agent import budget_agent
from agents.replanner_agent import replanner_agent
from agents.itinerary_composer_agent import itinerary_composer_agent

from utils.logger_config import setup_logger


logger = setup_logger(__name__)


def should_continue_after_planner(state):
    """
    Decides whether the graph should continue after Planner Agent.

    If required fields are missing, graph ends and UI shows the missing-fields message.
    If no required fields are missing, graph moves to Weather Agent.
    """

    logger.info("=" * 60)
    logger.info("ROUTER: CHECKING STATE AFTER PLANNER")
    logger.info("destination: %s", state.get("destination"))
    logger.info("start_date: %s", state.get("start_date"))
    logger.info("end_date: %s", state.get("end_date"))
    logger.info("budget: %s", state.get("budget"))
    logger.info("number_of_people: %s", state.get("number_of_people"))
    logger.info("missing_fields: %s", state.get("missing_fields"))
    logger.info("=" * 60)

    missing_fields = state.get("missing_fields", [])

    if missing_fields:
        logger.warning(
            "Graph stopped because required fields are missing: %s",
            missing_fields,
        )

        return "end"

    logger.info("Planner completed successfully. Moving to Weather Agent.")

    return "weather"


def budget_router(state):
    """
    Decides whether the graph should go to Replanner Agent or Composer Agent.

    If budget exceeds user budget and replanning count is less than 2,
    route to Replanner Agent.

    Otherwise, route to Itinerary Composer Agent.
    """

    needs_replanning = state.get("needs_replanning", False)
    replan_count = state.get("replan_count", 0)

    logger.info("Budget router executed")
    logger.info("needs_replanning: %s", needs_replanning)
    logger.info("replan_count: %s", replan_count)

    if needs_replanning and replan_count < 2:
        logger.info("Budget router: sending plan to Replanner Agent.")

        return "replanner"

    logger.info("Budget router: sending plan to Composer Agent.")

    return "composer"


def build_trip_graph():
    """
    Builds and compiles the LangGraph workflow.

    Workflow:
    planner -> weather -> destination -> transport -> budget
    budget -> replanner or composer
    replanner -> transport -> budget
    composer -> END
    """

    logger.info("Building Trip Graph")

    graph_builder = StateGraph(TripState)

    logger.info("Adding graph nodes")

    graph_builder.add_node("planner", planner_agent)
    graph_builder.add_node("weather", weather_agent)
    graph_builder.add_node("destination", destination_agent)
    graph_builder.add_node("transport", transport_agent)
    graph_builder.add_node("budget", budget_agent)
    graph_builder.add_node("replanner", replanner_agent)
    graph_builder.add_node("composer", itinerary_composer_agent)

    logger.info("Setting graph entry point to Planner Agent")

    graph_builder.set_entry_point("planner")

    logger.info("Adding conditional edge after Planner Agent")

    graph_builder.add_conditional_edges(
        "planner",
        should_continue_after_planner,
        {
            "weather": "weather",
            "end": END,
        },
    )

    logger.info("Adding normal graph edges")

    graph_builder.add_edge("weather", "destination")
    graph_builder.add_edge("destination", "transport")
    graph_builder.add_edge("transport", "budget")

    logger.info("Adding conditional edge after Budget Agent")

    graph_builder.add_conditional_edges(
        "budget",
        budget_router,
        {
            "replanner": "replanner",
            "composer": "composer",
        },
    )

    graph_builder.add_edge("replanner", "transport")
    graph_builder.add_edge("composer", END)

    logger.info("Compiling Trip Graph")

    compiled_graph = graph_builder.compile()

    logger.info("Trip Graph compiled successfully")

    return compiled_graph


trip_graph = build_trip_graph()
