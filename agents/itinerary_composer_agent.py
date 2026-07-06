from typing import Dict, Any

from utils.llm_config import get_llm
from utils.json_utils import extract_json_from_text
from utils.logger_config import setup_logger


logger = setup_logger(__name__)


def itinerary_composer_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Itinerary Composer Agent.

    Responsibilities:
    - Generate final day-wise itinerary.
    - Use exact trip dates.
    - Use weather information.
    - Use destination plan.
    - Use transport plan.
    - Use budget plan.
    - Explain tradeoffs.
    - Present final response clearly.
    """

    logger.info("Itinerary Composer Agent executed")

    llm = get_llm()

    prompt = f"""
You are an Itinerary Composer Agent.

Create a final travel plan using the shared state.

Shared state:
{state}

Return ONLY valid JSON with this structure:

{{
  "trip_summary": "",
  "day_wise_plan": [
    {{
      "day": "Day 1",
      "date": "YYYY-MM-DD",
      "title": "",
      "morning": "",
      "afternoon": "",
      "evening": "",
      "notes": ""
    }}
  ],
  "budget_summary": "",
  "weather_notes": "",
  "transport_notes": "",
  "tradeoffs_made": [],
  "final_recommendation": ""
}}

Rules:
- Use destination, start_date, end_date, duration, travelers, and budget from the shared state.
- Use weather_info from OpenWeatherMap.
- Mention temperature, humidity, wind, rain, and weather condition where useful.
- Generate exactly one itinerary item per trip day.
- Keep morning, afternoon, and evening as separate detailed paragraphs.
- If rain is expected, keep indoor backup options.
- If temperature is high, avoid outdoor afternoon plans.
- If wind or rain risk exists, avoid risky water activities.
- Use destination_plan to choose suitable activities.
- Use transport_plan to avoid unnecessary travel and backtracking.
- Use budget_plan to keep the trip realistic.
- The budget summary should use the Budget Agent's estimated_total.
- If the user provided a budget, keep the plan reasonably close to that budget without exceeding it.
- Do not make the trip unnecessarily too cheap if the user has provided a comfortable budget.
- Mention how the budget is used across stay, food, local transport, activities, and buffer.
- If replanner_message exists, consider it while explaining tradeoffs.
- Keep output strictly JSON only.
- Do not include markdown.
- Do not include explanation outside JSON.
"""

    try:
        logger.info("Gemini API Call: Composer Agent")

        response = llm.invoke(prompt)

        logger.info(
            "Itinerary response content type: %s",
            type(response.content),
        )

        logger.info(
            "Itinerary response content: %s",
            response.content,
        )

        itinerary = extract_json_from_text(response.content)

    except Exception as e:
        logger.error(
            "Composer Agent Gemini call failed: %s",
            str(e),
        )

        itinerary = {}

    if not itinerary:
        logger.warning(
            "Itinerary output empty. Using fallback itinerary."
        )

        itinerary = build_fallback_itinerary(state)

    logger.info(
        "Itinerary generated: %s",
        itinerary,
    )

    final_answer = format_final_answer(
        itinerary=itinerary,
        state=state,
    )

    updated_state = dict(state)

    updated_state["itinerary"] = itinerary
    updated_state["final_answer"] = final_answer

    logger.info("Final answer generated successfully")

    return updated_state


def build_fallback_itinerary(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a fallback itinerary if Gemini fails or returns invalid JSON.
    """

    destination = state.get("destination", "the selected destination")
    start_date = state.get("start_date", "Date not specified")
    duration = state.get("duration") or 1

    weather_info = state.get("weather_info", {})
    weather_analysis = weather_info.get("weather_analysis", {})

    travel_advice = weather_analysis.get(
        "travel_advice",
        "Keep the itinerary flexible based on local weather conditions.",
    )

    budget_plan = state.get("budget_plan", {})

    estimated_total = budget_plan.get(
        "estimated_total",
        "Not available",
    )

    user_budget = budget_plan.get(
        "user_budget",
        state.get("budget", "Not available"),
    )

    within_budget = budget_plan.get(
        "within_budget",
        "Not available",
    )

    destination_plan = state.get("destination_plan", {})

    suitable_activities = destination_plan.get(
        "suitable_activities",
        [
            "Sightseeing",
            "Local food exploration",
            "Cultural experiences",
        ],
    )

    activities_to_avoid = destination_plan.get(
        "activities_to_avoid",
        [
            "Overpacked schedule",
        ],
    )

    day_wise_plan = []

    try:
        number_of_days = int(duration)
    except Exception:
        number_of_days = 1

    if number_of_days <= 0:
        number_of_days = 1

    if not suitable_activities:
        suitable_activities = [
            "Sightseeing",
            "Local food exploration",
            "Cultural experiences",
        ]

    for day_number in range(1, number_of_days + 1):
        activity_index = (day_number - 1) % len(suitable_activities)
        selected_activity = suitable_activities[activity_index]

        day_wise_plan.append(
            {
                "day": f"Day {day_number}",
                "date": start_date if day_number == 1 else "Date based on trip sequence",
                "title": f"{destination} Exploration - Day {day_number}",
                "morning": (
                    f"Start the day with a relaxed breakfast and proceed for "
                    f"{selected_activity}. Keep the schedule flexible based on weather."
                ),
                "afternoon": (
                    "Continue with nearby attractions or indoor alternatives. "
                    "Avoid unnecessary long-distance travel and keep rest time included."
                ),
                "evening": (
                    "Enjoy local food, cafes, markets, or a relaxed evening experience "
                    "based on the destination and weather conditions."
                ),
                "notes": (
                    "This fallback day plan was generated because the LLM response "
                    "was unavailable or invalid. Weather and budget constraints should "
                    "still be considered while finalizing bookings."
                ),
            }
        )

    fallback_itinerary = {
        "trip_summary": (
            f"This is a fallback itinerary for {destination}. It uses the available "
            f"planner, weather, destination, transport, and budget information to create "
            f"a safe and flexible trip plan."
        ),
        "day_wise_plan": day_wise_plan,
        "budget_summary": (
            f"User budget: INR {user_budget}. Estimated total: INR {estimated_total}. "
            f"Within budget: {within_budget}. Refer to the budget section for the "
            f"detailed cost breakdown."
        ),
        "weather_notes": (
            f"Weather advice: {travel_advice}"
        ),
        "transport_notes": (
            "Transport should be planned by grouping nearby activities together and "
            "avoiding unnecessary backtracking."
        ),
        "tradeoffs_made": [
            "Fallback itinerary used because final LLM itinerary generation failed.",
            "Activities are kept flexible to handle weather and budget uncertainty.",
            f"Activities to avoid: {', '.join(activities_to_avoid)}",
        ],
        "final_recommendation": (
            "Use this itinerary as a safe baseline plan. Review weather, transport, "
            "and budget details before final booking."
        ),
    }

    return fallback_itinerary


def format_final_answer(
    itinerary: Dict[str, Any],
    state: Dict[str, Any],
) -> str:
    """
    Converts itinerary dictionary into readable Markdown.
    """

    lines = []

    lines.append("# Smart Trip Plan")
    lines.append("")

    lines.append("## Trip Summary")
    lines.append(
        itinerary.get(
            "trip_summary",
            "",
        )
    )
    lines.append("")

    lines.append("## Trip Details")
    lines.append(
        f"- Destination: {state.get('destination')}"
    )
    lines.append(
        f"- Origin: {state.get('origin')}"
    )
    lines.append(
        f"- Start Date: {state.get('start_date')}"
    )
    lines.append(
        f"- End Date: {state.get('end_date')}"
    )
    lines.append(
        f"- Duration: {state.get('duration')} days"
    )
    lines.append(
        f"- Travelers: {state.get('travelers')}"
    )
    lines.append(
        f"- Number of People: {state.get('number_of_people')}"
    )
    lines.append(
        f"- Budget: INR {state.get('budget')}"
    )
    lines.append("")

    lines.append("## Day-wise Itinerary")

    day_wise_plan = itinerary.get(
        "day_wise_plan",
        [],
    )

    if day_wise_plan:
        for day in day_wise_plan:
            lines.append(
                f"### {day.get('day', '')} "
                f"({day.get('date', 'Date not specified')}): "
                f"{day.get('title', '')}"
            )

            lines.append(
                f"**Morning:** {day.get('morning', '')}"
            )
            lines.append(
                f"**Afternoon:** {day.get('afternoon', '')}"
            )
            lines.append(
                f"**Evening:** {day.get('evening', '')}"
            )
            lines.append(
                f"**Notes:** {day.get('notes', '')}"
            )
            lines.append("")
    else:
        lines.append("- Day-wise itinerary not available.")
        lines.append("")

    lines.append("## Budget Summary")
    lines.append(
        itinerary.get(
            "budget_summary",
            "",
        )
    )
    lines.append("")

    budget_plan = state.get(
        "budget_plan",
        {},
    )

    if budget_plan:
        lines.append("### Budget Agent Output")
        lines.append(
            f"- User Budget: INR {budget_plan.get('user_budget')}"
        )
        lines.append(
            f"- Estimated Total: INR {budget_plan.get('estimated_total')}"
        )
        lines.append(
            f"- Within Budget: {budget_plan.get('within_budget')}"
        )

        cost_breakdown = budget_plan.get(
            "cost_breakdown",
            {},
        )

        if cost_breakdown:
            lines.append("- Cost Breakdown:")

            for cost_item, value in cost_breakdown.items():
                lines.append(
                    f"  - {cost_item}: INR {value}"
                )

        calculation_explanation = budget_plan.get(
            "calculation_explanation",
            "",
        )

        if calculation_explanation:
            lines.append(
                f"- Calculation Explanation: {calculation_explanation}"
            )

        lines.append("")

    lines.append("## Weather Notes")
    lines.append(
        itinerary.get(
            "weather_notes",
            "",
        )
    )
    lines.append("")

    weather_info = state.get(
        "weather_info",
        {},
    )

    if weather_info:
        lines.append("### Weather Agent Output")

        lines.append(
            f"- Weather Source: {weather_info.get('weather_source')}"
        )

        current_weather = weather_info.get(
            "current_weather",
            {},
        )

        if current_weather:
            lines.append(
                f"- API Used: {current_weather.get('api_used')}"
            )
            lines.append(
                f"- API Success: {current_weather.get('success')}"
            )
            lines.append(
                f"- Condition: {current_weather.get('description')}"
            )
            lines.append(
                f"- Temperature: {current_weather.get('temperature_c')} °C"
            )
            lines.append(
                f"- Feels Like: {current_weather.get('feels_like_c')} °C"
            )
            lines.append(
                f"- Humidity: {current_weather.get('humidity_percent')}%"
            )
            lines.append(
                f"- Wind Speed: {current_weather.get('wind_speed')}"
            )
            lines.append(
                f"- Cloudiness: {current_weather.get('cloudiness_percent')}%"
            )

        forecast = weather_info.get(
            "forecast",
            {},
        )

        if forecast:
            lines.append(
                f"- Forecast API Success: {forecast.get('success')}"
            )

        weather_analysis = weather_info.get(
            "weather_analysis",
            {},
        )

        if weather_analysis:
            lines.append(
                f"- Travel Advice: {weather_analysis.get('travel_advice')}"
            )

        lines.append("")

    lines.append("## Destination Plan")

    destination_plan = state.get(
        "destination_plan",
        {},
    )

    if destination_plan:
        recommended_regions = destination_plan.get(
            "recommended_regions",
            [],
        )

        suitable_activities = destination_plan.get(
            "suitable_activities",
            [],
        )

        activities_to_avoid = destination_plan.get(
            "activities_to_avoid",
            [],
        )

        experience_reasoning = destination_plan.get(
            "experience_reasoning",
            "",
        )

        if recommended_regions:
            lines.append("### Recommended Regions")
            for region in recommended_regions:
                lines.append(
                    f"- {region}"
                )

        if suitable_activities:
            lines.append("### Suitable Activities")
            for activity in suitable_activities:
                lines.append(
                    f"- {activity}"
                )

        if activities_to_avoid:
            lines.append("### Activities to Avoid")
            for activity in activities_to_avoid:
                lines.append(
                    f"- {activity}"
                )

        if experience_reasoning:
            lines.append("### Experience Reasoning")
            lines.append(experience_reasoning)

        lines.append("")
    else:
        lines.append("- Destination plan not available.")
        lines.append("")

    lines.append("## Transport Notes")
    lines.append(
        itinerary.get(
            "transport_notes",
            "",
        )
    )
    lines.append("")

    transport_plan = state.get(
        "transport_plan",
        {},
    )

    if transport_plan:
        lines.append("### Transport Plan Details")
        lines.append(
            str(transport_plan)
        )
        lines.append("")

    lines.append("## Tradeoffs Made")

    tradeoffs = itinerary.get(
        "tradeoffs_made",
        [],
    )

    if tradeoffs:
        for tradeoff in tradeoffs:
            lines.append(
                f"- {tradeoff}"
            )
    else:
        lines.append(
            "- No major tradeoffs required."
        )

    lines.append("")

    replanner_message = state.get(
        "replanner_message",
        "",
    )

    if replanner_message:
        lines.append("## Replanner Status")
        lines.append(replanner_message)
        lines.append("")

    lines.append("## Final Recommendation")
    lines.append(
        itinerary.get(
            "final_recommendation",
            "",
        )
    )

    return "\n".join(lines)
