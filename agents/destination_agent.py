from typing import Dict, Any

from utils.llm_config import invoke_llm_with_retry
from utils.json_utils import extract_json_from_text
from utils.logger_config import setup_logger


logger = setup_logger(__name__)


def destination_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Destination & Experience Agent.

    Responsibilities:
    - Suggest regions and activities
    - Match user preferences
    - Use weather information from MCP weather agent
    - Avoid risky or unsuitable activities
    """

    logger.info("Destination Agent executed")

    prompt = f"""
You are a Destination & Experience Agent.

Create a suitable destination experience plan based on the shared trip state.

Shared state:
{state}

Return ONLY valid JSON with this structure:

{{
  "recommended_regions": [],
  "suitable_activities": [],
  "activities_to_avoid": [],
  "experience_reasoning": ""
}}

Rules:
- Use weather_info from shared state.
- Use destination, duration, travel_style, preferences, and budget from shared state.
- Consider temperature, humidity, wind speed, rain, cloudiness, and weather condition.
- If rain or storm is detected, avoid outdoor-heavy plans.
- If high temperature is detected, avoid afternoon outdoor sightseeing.
- If wind/rain risk exists, avoid risky water activities and island trips.
- Match user preferences and travel style.
- Keep output strictly JSON only.
- Do not include markdown.
- Do not include explanation outside JSON.
"""

    try:
        response = invoke_llm_with_retry(
            prompt=prompt,
            agent_name="Destination Agent",
            retries=3,
            sleep_seconds=6,
        )

        logger.info(
            "Destination response content type: %s",
            type(response.content),
        )

        logger.info(
            "Destination response content: %s",
            response.content,
        )

        destination_plan = extract_json_from_text(response.content)

    except Exception as e:
        logger.warning(
            "Destination Agent Gemini failed. Using fallback destination plan."
        )

        logger.error(
            "Destination error: %s",
            str(e),
        )

        destination_plan = {}

    if not destination_plan:
        logger.warning(
            "Destination plan empty. Using fallback destination plan."
        )

        destination_plan = {
            "recommended_regions": [
                "Main tourist region",
                "Popular central area",
                "Local cultural area",
            ],
            "suitable_activities": [
                "Sightseeing",
                "Local food exploration",
                "Cultural experiences",
                "Indoor cafes or museums if weather is rainy",
            ],
            "activities_to_avoid": [
                "Overpacked schedule",
                "Risky outdoor activities during bad weather",
            ],
            "experience_reasoning": (
                "Fallback plan generated because the LLM response was unavailable. "
                "The plan is kept balanced using available destination, budget, "
                "duration, and weather constraints."
            ),
        }

    updated_state = dict(state)

    updated_state["destination_plan"] = destination_plan

    logger.info(
        "Destination plan generated: %s",
        destination_plan,
    )

    return updated_state
