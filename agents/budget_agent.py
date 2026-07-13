import asyncio

from state.trip_state import state_to_dict
from utils.logger_config import setup_logger
from utils.mcp_client import call_budget


logger = setup_logger(__name__)


def budget_agent(state):
    """
    Calculates the trip budget and requests human review when the
    estimate exceeds the user's budget.
    """

    state = state_to_dict(state)

    logger.info("Budget Agent executed")

    duration = state.get("duration")
    travelers = state.get("number_of_people")
    user_budget = state.get("budget")

    logger.info(
        "Budget input: duration=%s, travelers=%s, user_budget=%s",
        duration,
        travelers,
        user_budget,
    )

    updated_state = dict(state)

    if not duration or not travelers or not user_budget:
        updated_state["budget_plan"] = {
            "user_budget": user_budget,
            "estimated_total": None,
            "within_budget": None,
            "cost_breakdown": {},
            "calculation_explanation": (
                "Budget could not be calculated because duration, "
                "travelers, or user budget is missing."
            ),
        }

        updated_state["needs_replanning"] = False
        updated_state["human_review_required"] = False

        updated_state["replanner_message"] = (
            "Budget calculation requires trip duration, "
            "number of travelers, and user budget."
        )

        return updated_state

    budget_plan = asyncio.run(
        call_budget(
            duration,
            travelers,
            user_budget,
        )
    )

    logger.info(
        "MCP Budget result: %s",
        budget_plan,
    )

    updated_state["budget_plan"] = budget_plan

    within_budget = budget_plan.get("within_budget")
    estimated_total = budget_plan.get("estimated_total")

    if within_budget is False:
        updated_state["original_budget_plan"] = dict(
            budget_plan
        )

        updated_state["needs_replanning"] = True
        updated_state["human_review_required"] = True
        updated_state["human_decision"] = None

        if estimated_total is not None:
            updated_state["replanner_message"] = (
                f"The estimated total is INR {int(estimated_total):,}, "
                f"which exceeds the user budget of INR "
                f"{int(user_budget):,}. Please review the options."
            )
        else:
            updated_state["replanner_message"] = (
                "The estimated trip cost exceeds the entered budget. "
                "Please review the available options."
            )

    elif within_budget is True:
        updated_state["needs_replanning"] = False
        updated_state["human_review_required"] = False
        updated_state["human_decision"] = None

        updated_state["replanner_message"] = (
            "Replanning is not required because the estimated "
            "total is within the user budget."
        )

    else:
        updated_state["needs_replanning"] = False
        updated_state["human_review_required"] = False

        updated_state["replanner_message"] = (
            "Budget comparison could not be determined. "
            "The existing plan will continue."
        )

    return updated_state