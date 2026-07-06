import asyncio

from utils.mcp_client import call_budget
from utils.logger_config import setup_logger


logger = setup_logger(__name__)


def budget_agent(state):
    """
    Budget Agent.

    Responsibilities:
    - Read duration, number of travelers, and user budget from shared state.
    - Call Budget MCP Server through MCP client.
    - Store budget calculation result in state["budget_plan"].
    - Decide whether replanning is required.
    - Add replanner_message for UI explanation.
    """

    logger.info("Budget Agent executed")

    duration = state.get("duration")
    travelers = state.get("number_of_people")
    user_budget = state.get("budget")

    logger.info(
        "Budget Agent input: duration=%s, travelers=%s, user_budget=%s",
        duration,
        travelers,
        user_budget,
    )

    if not duration or not travelers or not user_budget:
        updated_state = dict(state)

        updated_state["budget_plan"] = {
            "user_budget": user_budget,
            "estimated_total": None,
            "within_budget": None,
            "cost_breakdown": {},
            "calculation_explanation": (
                "Budget could not be calculated because duration, travelers, "
                "or user budget is missing."
            ),
        }

        updated_state["needs_replanning"] = False

        updated_state["replanner_message"] = (
            "Replanner was not triggered because budget calculation could not be completed. "
            "Please provide complete trip duration, number of travelers, and budget."
        )

        logger.warning(
            "Budget Agent warning: %s",
            updated_state["replanner_message"],
        )

        return updated_state

    budget_plan = asyncio.run(
        call_budget(
            duration,
            travelers,
            user_budget,
        )
    )

    logger.info("MCP Budget result: %s", budget_plan)

    within_budget = budget_plan.get("within_budget")

    updated_state = dict(state)

    updated_state["budget_plan"] = budget_plan

    if within_budget is False:
        updated_state["needs_replanning"] = True

        updated_state["replanner_message"] = (
            "Replanner triggered because the estimated budget exceeds the user budget. "
            "The system will attempt to reduce activities, luxury choices, transport cost, "
            "or unnecessary expenses."
        )

    elif within_budget is True:
        updated_state["needs_replanning"] = False

        updated_state["replanner_message"] = (
            "Replanner not required because the estimated budget is within the user budget."
        )

    else:
        updated_state["needs_replanning"] = False

        updated_state["replanner_message"] = (
            "Replanner not triggered because budget comparison could not be determined."
        )

    logger.info(
        "Replanner message: %s",
        updated_state["replanner_message"],
    )

    return updated_state
