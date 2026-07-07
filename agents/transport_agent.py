from typing import Dict, Any

from tools.distance_tool import create_transport_strategy
from utils.logger_config import setup_logger
from state.trip_state import state_to_dict


logger = setup_logger(__name__)


def transport_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transport & Distance Agent.

    Responsibilities:
    - Reduce unnecessary travel
    - Suggest realistic movement strategy
    - Group nearby activities
    """

    state = state_to_dict(state)

    logger.info("Transport Agent executed")

    destination = state.get("destination")
    duration = state.get("duration") or 3

    logger.info("Transport Agent destination: %s", destination)
    logger.info("Transport Agent duration: %s", duration)

    destination_plan = state.get("destination_plan", {})
    activities = destination_plan.get("suitable_activities", [])

    logger.info("Transport Agent received activities: %s", activities)

    transport_plan = create_transport_strategy(
        destination=destination,
        activities=activities,
        duration=duration,
    )

    logger.info("Transport plan generated: %s", transport_plan)

    updated_state = dict(state)
    updated_state["transport_plan"] = transport_plan

    logger.info("Transport Agent completed successfully")

    return updated_state