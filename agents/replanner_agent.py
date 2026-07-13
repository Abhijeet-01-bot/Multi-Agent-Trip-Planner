from copy import deepcopy

from state.trip_state import state_to_dict
from utils.logger_config import setup_logger


logger = setup_logger(__name__)


def scale_cost_breakdown(
    cost_breakdown,
    revised_total,
    original_total,
):
    if (
        not isinstance(cost_breakdown, dict)
        or not cost_breakdown
        or not original_total
        or not revised_total
    ):
        return cost_breakdown or {}

    ratio = revised_total / original_total

    revised_breakdown = {}

    for cost_name, value in cost_breakdown.items():
        if isinstance(value, (int, float)):
            revised_breakdown[cost_name] = max(
                0,
                round(value * ratio),
            )
        else:
            revised_breakdown[cost_name] = value

    numeric_keys = [
        key
        for key, value in revised_breakdown.items()
        if isinstance(value, (int, float))
    ]

    numeric_total = sum(
        revised_breakdown[key]
        for key in numeric_keys
    )

    difference = revised_total - numeric_total

    if numeric_keys and difference:
        last_key = numeric_keys[-1]

        revised_breakdown[last_key] = max(
            0,
            revised_breakdown[last_key] + difference,
        )

    return revised_breakdown


def replanner_agent(state):
    """
    Produces and exposes a concrete revised budget and updated activity plan.

    This agent executes only after the user approves replanning.
    """

    state = state_to_dict(state)

    logger.info("Replanner Agent executed")

    updated_state = dict(state)

    updated_state["replan_count"] = (
        state.get("replan_count", 0) + 1
    )

    original_budget_plan = deepcopy(
        state.get("original_budget_plan")
        or state.get("budget_plan")
        or {}
    )

    original_total = original_budget_plan.get(
        "estimated_total"
    )

    user_budget = (
        state.get("budget")
        or original_budget_plan.get("user_budget")
    )

    destination_plan = deepcopy(
        state.get("destination_plan", {})
    )

    suitable_activities = list(
        destination_plan.get(
            "suitable_activities",
            [],
        )
    )

    activities_to_avoid = list(
        destination_plan.get(
            "activities_to_avoid",
            [],
        )
    )

    if suitable_activities:
        activity_count = max(
            2,
            len(suitable_activities) - 2,
        )

        destination_plan[
            "suitable_activities"
        ] = suitable_activities[:activity_count]

    else:
        destination_plan[
            "suitable_activities"
        ] = [
            "Free sightseeing",
            "Local market visit",
            "Self-guided walking tour",
        ]

    new_avoid_items = [
        "Expensive paid activities",
        "Luxury transfers",
        "Premium dining every day",
    ]

    for item in new_avoid_items:
        if item not in activities_to_avoid:
            activities_to_avoid.append(item)

    destination_plan[
        "activities_to_avoid"
    ] = activities_to_avoid

    destination_plan["experience_reasoning"] = (
        destination_plan.get(
            "experience_reasoning",
            "",
        )
        + " The human-approved revision prioritizes essential "
        "experiences and lower-cost options."
    ).strip()

    if user_budget:
        # Keep a small buffer under the entered budget.
        revised_total = max(
            1,
            int(user_budget * 0.97),
        )

    elif original_total:
        revised_total = max(
            1,
            int(original_total * 0.80),
        )

    else:
        revised_total = None

    revised_breakdown = scale_cost_breakdown(
        original_budget_plan.get(
            "cost_breakdown",
            {},
        ),
        revised_total,
        original_total,
    )

    revised_budget_plan = deepcopy(
        original_budget_plan
    )

    revised_budget_plan.update(
        {
            "user_budget": user_budget,
            "estimated_total": revised_total,
            "within_budget": bool(
                user_budget
                and revised_total
                and revised_total <= user_budget
            ),
            "cost_breakdown": revised_breakdown,
            "calculation_explanation": (
                "Human-approved replanning reduced premium "
                "activities, luxury transfers, and premium dining "
                "while preserving core destination experiences."
            ),
            "replanned": True,
        }
    )

    replan_changes = [
        "Reduced non-essential paid activities",
        "Replaced luxury transfers with practical local transport",
        "Replaced premium daily dining with balanced local options",
        "Preserved core sightseeing and cultural experiences",
    ]

    if (
        original_total is not None
        and revised_total is not None
    ):
        savings_amount = max(
            0,
            int(original_total) - int(revised_total),
        )
    else:
        savings_amount = None

    updated_state["destination_plan"] = (
        destination_plan
    )

    updated_state["travel_style"] = (
        "budget-conscious"
    )

    updated_state["budget_plan"] = (
        revised_budget_plan
    )

    updated_state["revised_estimated_total"] = (
        revised_total
    )

    updated_state["savings_amount"] = (
        savings_amount
    )

    updated_state["replan_changes"] = (
        replan_changes
    )

    updated_state["needs_replanning"] = False
    updated_state["human_review_required"] = False

    if revised_total is not None:
        updated_state["replanner_message"] = (
            f"Replanning completed. The revised estimate is "
            f"INR {revised_total:,}"
        )

        if savings_amount is not None:
            updated_state["replanner_message"] += (
                f", saving INR {savings_amount:,}."
            )
        else:
            updated_state["replanner_message"] += "."

    else:
        updated_state["replanner_message"] = (
            "Replanning completed with lower-cost activities, "
            "transport, and dining choices."
        )

    logger.info(
        "Replanner completed: %s",
        updated_state["replanner_message"],
    )

    return updated_state