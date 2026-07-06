import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP

from utils.logger_config import setup_logger


logger = setup_logger(__name__)

mcp = FastMCP("BudgetServer")


def calculate_base_trip_cost(days, travelers):
    """
    Calculates the minimum realistic trip cost.

    This base cost is used only to check whether the user's budget
    is lower than a basic realistic estimate.
    """

    hotel_cost = days * travelers * 1500
    food_cost = days * travelers * 800
    transport_cost = days * 1000
    activities_cost = days * travelers * 700

    base_total = (
        hotel_cost
        + food_cost
        + transport_cost
        + activities_cost
    )

    return {
        "hotel": hotel_cost,
        "food": food_cost,
        "transport": transport_cost,
        "activities": activities_cost,
        "base_total": base_total,
    }


def allocate_budget_close_to_user_budget(user_budget):
    """
    Allocates the user's provided budget across travel categories.

    The estimated total is intentionally kept close to the user's budget
    but slightly below it to preserve a safety buffer.
    """

    target_total = int(user_budget * 0.95)

    hotel_cost = int(target_total * 0.40)
    food_cost = int(target_total * 0.20)
    transport_cost = int(target_total * 0.15)
    activities_cost = int(target_total * 0.20)

    allocated_so_far = (
        hotel_cost
        + food_cost
        + transport_cost
        + activities_cost
    )

    buffer_cost = target_total - allocated_so_far

    return {
        "hotel": hotel_cost,
        "food": food_cost,
        "transport": transport_cost,
        "activities": activities_cost,
        "buffer": buffer_cost,
        "estimated_total": target_total,
    }


@mcp.tool()
def estimate_budget(days, travelers, user_budget):
    """
    MCP Budget Tool.

    Responsibilities:
    - Estimate trip cost using duration, travelers, and user budget.
    - Keep the estimated total close to the user's entered budget.
    - Return category-wise cost breakdown.
    - Compare estimated total with user's budget.
    """

    logger.info("MCP Budget Server called")

    logger.info(
        "Budget input received: days=%s, travelers=%s, user_budget=%s",
        days,
        travelers,
        user_budget,
    )

    try:
        days = int(days or 1)
        travelers = int(travelers or 1)
        user_budget = int(user_budget or 0)

        logger.info(
            "Budget input after conversion: days=%s, travelers=%s, user_budget=%s",
            days,
            travelers,
            user_budget,
        )

        base_cost = calculate_base_trip_cost(
            days=days,
            travelers=travelers,
        )

        base_total = base_cost["base_total"]

        logger.info(
            "Base minimum trip cost calculated: %s",
            base_cost,
        )

        if user_budget <= 0:
            estimated_total = base_total

            cost_breakdown = {
                "hotel": base_cost["hotel"],
                "food": base_cost["food"],
                "transport": base_cost["transport"],
                "activities": base_cost["activities"],
                "buffer": 0,
            }

            within_budget = False

            calculation_explanation = (
                "User budget was not provided or was invalid. "
                "The estimated total is calculated using basic per-day costs "
                "for hotel, food, transport, and activities."
            )

        elif user_budget < base_total:
            estimated_total = base_total

            cost_breakdown = {
                "hotel": base_cost["hotel"],
                "food": base_cost["food"],
                "transport": base_cost["transport"],
                "activities": base_cost["activities"],
                "buffer": 0,
            }

            within_budget = False

            calculation_explanation = (
                "The user's budget is lower than the basic estimated trip cost. "
                "The estimate shows the minimum realistic cost required for this trip."
            )

        else:
            allocated_budget = allocate_budget_close_to_user_budget(
                user_budget=user_budget,
            )

            estimated_total = allocated_budget["estimated_total"]

            cost_breakdown = {
                "hotel": allocated_budget["hotel"],
                "food": allocated_budget["food"],
                "transport": allocated_budget["transport"],
                "activities": allocated_budget["activities"],
                "buffer": allocated_budget["buffer"],
            }

            within_budget = estimated_total <= user_budget

            calculation_explanation = (
                "Budget is estimated close to the user's provided budget. "
                "The system allocates approximately 95% of the user budget across "
                "hotel, food, transport, activities, and buffer so the plan feels "
                "aligned with the user's spending capacity while staying within budget."
            )

        budget_result = {
            "user_budget": user_budget,
            "estimated_total": estimated_total,
            "within_budget": within_budget,
            "cost_breakdown": cost_breakdown,
            "base_minimum_cost": base_total,
            "calculation_explanation": calculation_explanation,
        }

        logger.info(
            "Budget result generated successfully: %s",
            budget_result,
        )

        return budget_result

    except Exception as e:
        logger.error(
            "Budget calculation failed: %s",
            str(e),
        )

        return {
            "user_budget": user_budget,
            "estimated_total": None,
            "within_budget": None,
            "cost_breakdown": {},
            "base_minimum_cost": None,
            "calculation_explanation": (
                "Budget could not be calculated because an error occurred "
                "inside the Budget MCP Server."
            ),
            "error": str(e),
        }


if __name__ == "__main__":
    logger.info("Starting Budget MCP Server")
    mcp.run()
