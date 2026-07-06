import re
from datetime import datetime

from utils.llm_config import invoke_llm_with_retry
from utils.json_utils import extract_json_from_text
from utils.logger_config import setup_logger


logger = setup_logger(__name__)


MONTH_MAP = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def extract_budget(text):
    patterns = [
        r"budget\s*(?:of|is|around|under|=|:)?\s*(\d{4,7})",
        r"with\s*budget\s*(?:of)?\s*(\d{4,7})",
        r"(\d{4,7})\s*(?:inr|rs|rupees)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return int(match.group(1))

    return None


def extract_people(text):
    lower_text = text.lower()

    if "couple" in lower_text:
        return "couple", 2

    family_match = re.search(r"family of (\d+)", lower_text)

    if family_match:
        people = int(family_match.group(1))
        return "family", people

    people_match = re.search(
        r"(\d+)\s*(people|persons|travellers|travelers|friends)",
        lower_text,
    )

    if people_match:
        people = int(people_match.group(1))
        return str(people) + " people", people

    return None, None


def extract_destination(text):
    patterns = [
        r"trip to ([A-Za-z\s]+?) from",
        r"trip to ([A-Za-z\s]+?) for",
        r"trip to ([A-Za-z\s]+?) with",
        r"visit ([A-Za-z\s]+?) from",
        r"go to ([A-Za-z\s]+?) from",
        r"plan.*to ([A-Za-z\s]+?) from",
        r"plan.*to ([A-Za-z\s]+?) for",
        r"plan.*to ([A-Za-z\s]+?) with",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            destination = match.group(1).strip()
            return destination.title()

    simple_match = re.search(r"to ([A-Za-z\s]+)", text, re.IGNORECASE)

    if simple_match:
        destination = simple_match.group(1).strip()

        destination = re.split(
            r"\bfrom\b|\bfor\b|\bwith\b|\bbudget\b|\bon\b|\bduring\b",
            destination,
            flags=re.IGNORECASE,
        )[0]

        destination = destination.strip()

        if destination:
            return destination.title()

    return None


def parse_date(day, month, year):
    try:
        month_number = MONTH_MAP.get(month.lower())

        if not month_number:
            return None

        date_obj = datetime(
            int(year),
            month_number,
            int(day),
        )

        return date_obj.strftime("%Y-%m-%d")

    except Exception:
        return None


def extract_dates(text):
    pattern = (
        r"from\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})"
        r"\s+to\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})"
    )

    match = re.search(pattern, text, re.IGNORECASE)

    if not match:
        return None, None, None, None, None

    start_day, start_month, start_year, end_day, end_month, end_year = match.groups()

    start_date = parse_date(
        start_day,
        start_month,
        start_year,
    )

    end_date = parse_date(
        end_day,
        end_month,
        end_year,
    )

    duration = None

    if start_date and end_date:
        start_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_obj = datetime.strptime(end_date, "%Y-%m-%d")
        duration = (end_obj - start_obj).days + 1

    dates = (
        start_day + " " + start_month + " " + start_year
        + " to "
        + end_day + " " + end_month + " " + end_year
    )

    return dates, start_date, end_date, start_month, duration


def calculate_missing_fields(planner_output):
    missing_fields = []

    if not planner_output.get("destination"):
        missing_fields.append("destination")

    if not planner_output.get("start_date") or not planner_output.get("end_date"):
        missing_fields.append("travel dates")

    if not planner_output.get("number_of_people"):
        missing_fields.append("number of travelers")

    if not planner_output.get("budget"):
        missing_fields.append("budget")

    return missing_fields


def build_missing_fields_message(missing_fields):
    if not missing_fields:
        return ""

    fields_text = ", ".join(missing_fields)

    return (
        "I need a few more details before creating the trip plan. "
        "Please provide: " + fields_text + ".\n\n"
        "Example: Plan a trip to Goa from 10 July 2026 to 14 July 2026 "
        "for a couple with budget 40000 INR."
    )


def fallback_planner_output(state):
    raw_user_input = state.get("raw_user_input", "")

    destination = extract_destination(raw_user_input)
    budget = extract_budget(raw_user_input)
    travelers, number_of_people = extract_people(raw_user_input)
    dates, start_date, end_date, month, duration = extract_dates(raw_user_input)

    planner_output = {
        "destination": destination,
        "origin": None,
        "dates": dates,
        "start_date": start_date,
        "end_date": end_date,
        "month": month,
        "duration": duration,
        "travelers": travelers,
        "number_of_people": number_of_people,
        "budget": budget,
        "currency": "INR",
        "travel_style": None,
        "preferences": [],
    }

    missing_fields = calculate_missing_fields(planner_output)

    planner_output["missing_fields"] = missing_fields
    planner_output["final_answer"] = build_missing_fields_message(missing_fields)

    return planner_output


def planner_agent(state):
    logger.info("Planner Agent executed")

    raw_user_input = state.get("raw_user_input", "")

    prompt = f"""
You are a Planner Agent for a Multi-Agent Smart Trip Planning Assistant.

Extract structured trip details from the user request.

User request:
{raw_user_input}

Return ONLY valid JSON with this exact structure:

{{
  "destination": null,
  "origin": null,
  "dates": null,
  "start_date": null,
  "end_date": null,
  "month": null,
  "duration": null,
  "travelers": null,
  "number_of_people": null,
  "budget": null,
  "currency": "INR",
  "travel_style": null,
  "preferences": [],
  "missing_fields": []
}}

Rules:
- start_date and end_date must be in YYYY-MM-DD format.
- duration should be number of travel days including start date and end date.
- If user says couple, number_of_people should be 2.
- If budget is mentioned in INR, return integer only.
- Origin is optional. Do not include origin in missing_fields.
- If dates are missing, include "travel dates" in missing_fields.
- If budget is missing, include "budget" in missing_fields.
- If travelers or number of people are missing, include "number of travelers" in missing_fields.
- Return JSON only.
- Do not include explanation.
"""

    try:
        response = invoke_llm_with_retry(
            prompt=prompt,
            agent_name="Planner Agent",
            retries=2,
            sleep_seconds=4,
        )

        logger.info("Planner response content type: %s", type(response.content))
        logger.info("Planner response content: %s", response.content)

        planner_output = extract_json_from_text(response.content)

    except Exception as e:
        logger.warning("Planner Agent Gemini failed. Using fallback planner.")
        logger.error("Planner error: %s", str(e))

        planner_output = fallback_planner_output(state)

    if not planner_output:
        logger.warning("Planner output empty. Using fallback planner.")
        planner_output = fallback_planner_output(state)

    optional_missing_fields = [
        "origin",
        "travel_style",
        "preferences",
    ]

    existing_missing = planner_output.get("missing_fields", [])

    existing_missing = [
        field
        for field in existing_missing
        if field not in optional_missing_fields
    ]

    recalculated_missing = calculate_missing_fields(planner_output)

    final_missing = []

    for field in existing_missing + recalculated_missing:
        if field not in final_missing:
            final_missing.append(field)

    planner_output["missing_fields"] = final_missing

    if final_missing:
        planner_output["final_answer"] = build_missing_fields_message(final_missing)
        planner_output["itinerary"] = {}
        logger.warning("Planner missing fields detected: %s", final_missing)
    else:
        planner_output["final_answer"] = ""
        logger.info("Planner found all required fields.")

    updated_state = dict(state)
    updated_state.update(planner_output)

    updated_state.setdefault("conversation_history", state.get("conversation_history", []))
    updated_state.setdefault("preferences", [])
    updated_state.setdefault("currency", "INR")
    updated_state.setdefault("needs_replanning", False)
    updated_state.setdefault("replan_count", 0)
    updated_state.setdefault("replanner_message", "")

    logger.info("Planner output destination: %s", updated_state.get("destination"))
    logger.info("Planner output duration: %s", updated_state.get("duration"))
    logger.info("Planner output budget: %s", updated_state.get("budget"))
    logger.info("Planner missing fields: %s", updated_state.get("missing_fields"))

    return updated_state
