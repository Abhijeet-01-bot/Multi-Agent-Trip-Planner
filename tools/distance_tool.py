from typing import List, Dict, Any


def create_transport_strategy(destination: str, activities: List[str], duration: int) -> Dict[str, Any]:
    """
    Creates a practical transport strategy.

    This is not live map calculation.
    It uses reasoning to reduce unnecessary travel.
    """

    destination_lower = (destination or "").lower()

    if "goa" in destination_lower:
        return {
            "recommended_mode": "Scooter rental or local cab",
            "movement_strategy": "Cluster nearby places together to avoid North-South backtracking.",
            "region_plan": [
                "Keep North Goa activities together",
                "Keep South Goa activities together",
                "Avoid switching hotel regions repeatedly"
            ],
            "pacing_advice": "Keep the itinerary flexible because weather and traffic can affect travel time."
        }

    return {
        "recommended_mode": "Local cab, public transport, or rental vehicle depending on destination",
        "movement_strategy": "Group nearby attractions on the same day.",
        "region_plan": [
            "Avoid covering far-away attractions on the same day",
            "Prioritize important experiences first"
        ],
        "pacing_advice": "Keep buffer time between activities."
    }