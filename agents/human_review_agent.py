from langgraph.types import interrupt

from state.trip_state import state_to_dict
from utils.logger_config import setup_logger


logger = setup_logger(__name__)


def human_review_agent(state):
    """
    Pauses graph execution when the budget exceeds the user's budget.

    The user can:
    - Approve replanning
    - Continue with the original plan
    - Update the budget and recalculate
    """

    state = state_to_dict(state)

    logger.info("Human Review Agent executed")

    budget_plan = state.get("budget_plan", {})

    review_request = {
        "type": "budget_review",
        "user_budget": budget_plan.get(
            "user_budget",
            state.get("budget"),
        ),
        "estimated_total": budget_plan.get(
            "estimated_total",
        ),
        "cost_breakdown": budget_plan.get(
            "cost_breakdown",
            {},
        ),
        "message": state.get(
            "replanner_message",
            "The estimated trip cost exceeds the entered budget.",
        ),
        "allowed_actions": [
            "approve_replan",
            "continue_current",
            "update_budget",
        ],
    }

    logger.info(
        "Waiting for human budget decision: %s",
        review_request,
    )

    decision = interrupt(review_request)

    if not isinstance(decision, dict):
        decision = {
            "action": str(decision),
        }

    action = decision.get(
        "action",
        "continue_current",
    )

    updated_state = dict(state)

    updated_state["human_decision"] = action
    updated_state["human_review_required"] = False

    if action == "update_budget":
        try:
            new_budget = int(
                decision.get("new_budget")
            )
        except (TypeError, ValueError):
            new_budget = None

        if new_budget and new_budget > 0:
            updated_state["budget"] = new_budget

            updated_state["replanner_message"] = (
                f"Budget updated by the user to INR {new_budget:,}. "
                "The budget is being recalculated."
            )

        else:
            updated_state["human_decision"] = (
                "continue_current"
            )

            updated_state["replanner_message"] = (
                "The supplied budget was invalid. "
                "The existing plan will continue."
            )

    elif action == "approve_replan":
        updated_state["replanner_message"] = (
            "The user approved budget replanning."
        )

    else:
        updated_state["needs_replanning"] = False

        updated_state["replanner_message"] = (
            "The user chose to continue with the current plan "
            "even though its estimate exceeds the entered budget."
        )

    logger.info(
        "Human budget decision: %s",
        updated_state["human_decision"],
    )

    return updated_state