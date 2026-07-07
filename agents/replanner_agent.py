from utils.logger_config import setup_logger
from state.trip_state import state_to_dict


logger = setup_logger(__name__)


def replanner_agent(state):
    """
    Replanner Agent.

    Responsibilities:
    - Trigger only when budget exceeds user budget.
    - Reduce expensive activities.
    - Avoid luxury transfers and premium dining.
    - Shift travel style to budget-conscious.
    - Add a clear replanner_message for UI display.
    """

    state = state_to_dict(state)

    logger.info("Replanner Agent executed")

    updated_state = dict(state)

    replan_count = updated_state.get("replan_count", 0)
    updated_state["replan_count"] = replan_count + 1

    logger.info(
        "Replan count updated to: %s",
        updated_state["replan_count"],
    )

    destination_plan = updated_state.get("destination_plan", {})

    suitable_activities = destination_plan.get("suitable_activities", [])
    activities_to_avoid = destination_plan.get("activities_to_avoid", [])

    logger.info(
        "Original suitable activities: %s",
        suitable_activities,
    )

    logger.info(
        "Original activities to avoid: %s",
        activities_to_avoid,
    )

    if suitable_activities:
        reduced_activities = suitable_activities[
            :max(2, len(suitable_activities) - 2)
        ]
    else:
        reduced_activities = [
            "Free sightseeing",
            "Local market visit",
            "Self-guided walking tour",
        ]

    logger.info(
        "Reduced activities after replanning: %s",
        reduced_activities,
    )

    destination_plan["suitable_activities"] = reduced_activities

    destination_plan["activities_to_avoid"] = activities_to_avoid + [
        "Expensive paid activities",
        "Luxury transfers",
        "Premium dining every day",
    ]

    destination_plan["experience_reasoning"] = (
        destination_plan.get("experience_reasoning", "")
        + " The plan was replanned to reduce cost and better fit the user's budget."
    )

    updated_state["destination_plan"] = destination_plan

    current_style = updated_state.get("travel_style")

    logger.info(
        "Current travel style before replanning: %s",
        current_style,
    )

    if current_style in ["luxury", "premium", "mid-range", None]:
        updated_state["travel_style"] = "budget-conscious"

    logger.info(
        "Travel style after replanning: %s",
        updated_state.get("travel_style"),
    )

    updated_state["needs_replanning"] = False

    updated_state["replanner_message"] = (
        "Replanner executed successfully. The plan was adjusted by reducing expensive "
        "activities, avoiding luxury transfers, avoiding premium dining every day, "
        "and shifting the travel style toward a budget-conscious plan."
    )

    logger.info(
        "Replanner message: %s",
        updated_state["replanner_message"],
    )

    logger.info("Replanner Agent completed successfully")

    return updated_state