import asyncio
from typing import Dict, Any

from utils.mcp_client import call_weather
from utils.logger_config import setup_logger
from state.trip_state import state_to_dict


logger = setup_logger(__name__)


def weather_agent(state: Dict[str, Any]):
    state = state_to_dict(state)

    logger.info("Weather Agent executed")

    destination = state.get("destination")

    logger.info("Weather Agent destination: %s", destination)

    if not destination:
        logger.warning("Weather Agent skipped because destination is missing.")
        return state

    try:
        weather_info = asyncio.run(
            call_weather(destination)
        )

        logger.info("Weather result received: %s", weather_info)

        updated_state = dict(state)

        updated_state["weather_info"] = weather_info

        return updated_state

    except Exception as e:
        logger.error("Weather Agent error type: %s", type(e))
        logger.error("Weather Agent error: %s", str(e))

        raise e