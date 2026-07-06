
from typing import Dict, Any


def estimate_trip_cost(
    destination: str,
    duration: int,
    number_of_people: int,
    travel_style: str,
    user_budget: int = 0
) -> Dict[str, Any]:
    """
    Estimates high-level trip cost.

    This version tries to keep the estimated trip cost close to the user's provided budget.
    Target usage is around 90% of user budget when budget is available.
    """

    duration = duration or 3
    number_of_people = number_of_people or 1
    user_budget = user_budget or 0
    travel_style = (travel_style or "mid-range").lower()

    # Base cost assumptions
    if travel_style in ["luxury", "premium"]:
        stay_per_night = 6500
        food_per_person_per_day = 1800
        local_transport_per_day = 2500
        activity_per_person_per_day = 1600

    elif travel_style in ["budget", "low budget", "economy"]:
        stay_per_night = 2200
        food_per_person_per_day = 800
        local_transport_per_day = 1000
        activity_per_person_per_day = 600

    else:
        stay_per_night = 4000
        food_per_person_per_day = 1300
        local_transport_per_day = 1600
        activity_per_person_per_day = 1000

    nights = max(duration - 1, 1)

    accommodation = stay_per_night * nights
    food = food_per_person_per_day * number_of_people * duration
    local_transport = local_transport_per_day * duration
    activities = activity_per_person_per_day * number_of_people * duration

    buffer_amount = int(
        0.10 * (accommodation + food + local_transport + activities)
    )

    base_total = accommodation + food + local_transport + activities + buffer_amount

    # If user budget is given and base estimate is much lower,
    # scale the plan closer to user's budget.
    if user_budget > 0:
        target_total = int(user_budget * 0.90)

        if base_total < int(user_budget * 0.80):
            extra_available = target_total - base_total

            if extra_available > 0:
                # Distribute extra budget smartly
                accommodation_extra = int(extra_available * 0.40)
                food_extra = int(extra_available * 0.20)
                transport_extra = int(extra_available * 0.15)
                activities_extra = int(extra_available * 0.20)
                buffer_extra = extra_available - (
                    accommodation_extra
                    + food_extra
                    + transport_extra
                    + activities_extra
                )

                accommodation += accommodation_extra
                food += food_extra
                local_transport += transport_extra
                activities += activities_extra
                buffer_amount += buffer_extra

    estimated_total = accommodation + food + local_transport + activities + buffer_amount

    return {
        "accommodation": accommodation,
        "food": food,
        "local_transport": local_transport,
        "activities": activities,
        "buffer": buffer_amount,
        "estimated_total": estimated_total,
        "assumption": (
            f"{travel_style.title()} style estimate for {number_of_people} traveler(s). "
            f"Budget-aware scaling is applied when user budget is higher than base estimate."
        )
    }


def suggest_budget_tradeoffs(estimated_total: int, user_budget: int) -> Dict[str, Any]:
    """
    Suggests tradeoffs if estimated cost exceeds user budget.
    """

    difference = estimated_total - user_budget

    if difference <= 0:
        return {
            "required": False,
            "message": "Trip is within budget.",
            "suggestions": []
        }

    suggestions = [
        "Choose budget or mid-range accommodation",
        "Reduce paid activities and add free sightseeing spots",
        "Use public transport, scooter rental, or shared cabs",
        "Stay in one region to reduce local travel cost",
        "Keep one relaxed low-cost day in the itinerary"
    ]

    return {
        "required": True,
        "message": f"Estimated cost exceeds budget by around INR {difference}.",
        "suggestions": suggestions
    }