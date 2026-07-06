import re
import html
import streamlit as st
from dotenv import load_dotenv

from graph.trip_graph import trip_graph

load_dotenv()


st.set_page_config(
    page_title="Multi-Agent Smart Trip Planner",
    page_icon="✈️",
    layout="wide",
)


# --------------------------------------------------
# Session State
# --------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "trip_state" not in st.session_state:
    st.session_state.trip_state = {
        "conversation_history": [],
        "preferences": [],
        "currency": "INR",
        "needs_replanning": False,
        "replan_count": 0,
    }


# --------------------------------------------------
# Helper Functions
# --------------------------------------------------
def clean_display_text(value):
    """
    Removes HTML tags and escaped HTML from LLM/UI text before displaying.
    """

    if value is None:
        return ""

    text = str(value)

    text = html.unescape(text)

    text = text.replace("<br>", "\n")
    text = text.replace("<br/>", "\n")
    text = text.replace("<br />", "\n")

    text = re.sub(r"<[^>]+>", "", text)

    text = text.replace("&nbsp;", " ")

    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def safe_text(value, default="Not available"):
    cleaned = clean_display_text(value)

    if cleaned == "":
        return default

    return cleaned


def safe_money(value):
    if value is None or value == "":
        return "N/A"

    try:
        return f"{int(value):,}"
    except Exception:
        return str(value)


def reset_trip_data_for_new_query():
    keys_to_remove = [
        "destination",
        "origin",
        "dates",
        "start_date",
        "end_date",
        "month",
        "duration",
        "travelers",
        "number_of_people",
        "budget",
        "travel_style",
        "missing_fields",
        "weather_info",
        "destination_plan",
        "transport_plan",
        "budget_plan",
        "itinerary",
        "needs_replanning",
        "replan_reason",
        "replan_count",
        "final_answer",
        "replanner_message",
    ]

    for key in keys_to_remove:
        st.session_state.trip_state.pop(key, None)

    st.session_state.trip_state["preferences"] = []
    st.session_state.trip_state["currency"] = "INR"
    st.session_state.trip_state["needs_replanning"] = False
    st.session_state.trip_state["replan_count"] = 0


# --------------------------------------------------
# Header and Sidebar
# --------------------------------------------------
def render_header():
    st.title("✈️ Multi-Agent Smart Trip Planning Assistant")

    st.caption(
        "A smart travel assistant that uses multiple agents for planning, "
        "weather analysis, budget checking, transport optimization, and itinerary generation."
    )

    st.info(
        "Tip: For best weather-aware planning, provide exact travel dates.\n\n"
        "Example: Plan a trip to Goa from 10 July 2026 to 14 July 2026 "
        "for a couple with budget 40000 INR."
    )


def render_sidebar():
    current_state = st.session_state.trip_state

    with st.sidebar:
        st.header("🧭 Current Trip State")

        st.write("**Destination:**", safe_text(current_state.get("destination"), "Not set"))
        st.write("**Origin:**", safe_text(current_state.get("origin"), "Not set"))
        st.write("**Start Date:**", safe_text(current_state.get("start_date"), "Not set"))
        st.write("**End Date:**", safe_text(current_state.get("end_date"), "Not set"))
        st.write("**Month:**", safe_text(current_state.get("month"), "Not set"))
        st.write("**Duration:**", f"{safe_text(current_state.get('duration'), 'Not set')} days")
        st.write("**People:**", safe_text(current_state.get("number_of_people"), "Not set"))
        st.write("**Budget:**", f"INR {safe_money(current_state.get('budget'))}")
        st.write("**Travel Style:**", safe_text(current_state.get("travel_style"), "Not set"))

        st.divider()

        st.subheader("🌦️ Weather Status")

        weather_info = current_state.get("weather_info", {})
        current_weather = weather_info.get("current_weather", {})

        if current_weather:
            st.write("**Weather Source:**", weather_info.get("weather_source", "Not available"))
            st.write("**API Used:**", current_weather.get("api_used", "Not available"))
            st.write("**API Success:**", current_weather.get("success"))

            if current_weather.get("success"):
                st.write("**Condition:**", current_weather.get("description"))
                st.write("**Temperature:**", f"{current_weather.get('temperature_c')} °C")
                st.write("**Humidity:**", f"{current_weather.get('humidity_percent')}%")
            else:
                st.warning(current_weather.get("error", "Weather call failed."))
        else:
            st.write("Weather data not generated yet.")

        st.divider()

        if st.button("🔄 Reset Trip"):
            st.session_state.messages = []
            st.session_state.trip_state = {
                "conversation_history": [],
                "preferences": [],
                "currency": "INR",
                "needs_replanning": False,
                "replan_count": 0,
            }
            st.rerun()


# --------------------------------------------------
# Renderer Functions
# --------------------------------------------------
def render_day_card(day):
    day_name = safe_text(day.get("day", "Day"))
    date = safe_text(day.get("date", "Date not specified"))
    title = safe_text(day.get("title", "Trip Plan"))

    morning = safe_text(day.get("morning", "Morning plan not specified."))
    afternoon = safe_text(day.get("afternoon", "Afternoon plan not specified."))
    evening = safe_text(day.get("evening", "Evening plan not specified."))
    notes = safe_text(day.get("notes", ""))

    with st.container(border=True):
        st.subheader(f"{day_name}: {title}")
        st.caption(f"Date: {date}")

        st.markdown("#### 🌅 Morning")
        st.write(morning)

        st.markdown("#### ☀️ Afternoon")
        st.write(afternoon)

        st.markdown("#### 🌙 Evening")
        st.write(evening)

        if notes:
            st.markdown("#### 📝 Notes")
            st.info(notes)


def render_current_weather(weather_info):
    current_weather = weather_info.get("current_weather", {})

    if not current_weather:
        st.info("Current weather data is not available.")
        return

    if not current_weather.get("success"):
        st.warning(current_weather.get("error", "Weather call failed."))
        return

    city = current_weather.get("city") or current_weather.get("location")
    country = current_weather.get("country")

    wind_speed = current_weather.get("wind_speed") or current_weather.get("wind_speed_mps")
    rain_1h = current_weather.get("rain_1h_mm") or current_weather.get("rain_last_1h_mm") or 0

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Temperature", f"{current_weather.get('temperature_c')} °C")

    with c2:
        st.metric("Humidity", f"{current_weather.get('humidity_percent')}%")

    with c3:
        st.metric("Wind Speed", f"{wind_speed} m/s")

    st.write("**Weather Source:**", weather_info.get("weather_source"))
    st.write("**API Used:**", current_weather.get("api_used"))
    st.write("**Location:**", f"{safe_text(city)}, {safe_text(country)}")
    st.write("**Condition:**", current_weather.get("description"))
    st.write("**Feels Like:**", f"{current_weather.get('feels_like_c')} °C")
    st.write("**Pressure:**", f"{current_weather.get('pressure_hpa')} hPa")
    st.write("**Cloudiness:**", f"{current_weather.get('cloudiness_percent')}%")
    st.write("**Rain Last 1h:**", f"{rain_1h} mm")


def render_forecast(weather_info):
    forecast = weather_info.get("forecast", {})

    if not forecast:
        st.info("Forecast data is not available.")
        return

    if not forecast.get("success"):
        st.warning(forecast.get("error", "Forecast call failed."))
        return

    daily_forecast = forecast.get("daily_forecast") or forecast.get("daily_summary") or []

    if not daily_forecast:
        st.info("No forecast summary available.")
        return

    st.markdown("### 5-Day Probable Weather Forecast")

    for day in daily_forecast:
        probable_condition = (
            day.get("probable_condition")
            or day.get("dominant_condition")
            or "Not available"
        )

        min_temp = day.get("min_temperature_c") or day.get("min_temp_c")
        max_temp = day.get("max_temperature_c") or day.get("max_temp_c")
        total_rain = day.get("total_rain_3h_mm") or day.get("total_rain_mm") or 0

        with st.container(border=True):
            st.write("**Date:**", safe_text(day.get("date")))
            st.write("**Probable Condition:**", safe_text(probable_condition))
            st.write("**Min / Max Temp:**", f"{safe_text(min_temp)} °C / {safe_text(max_temp)} °C")
            st.write("**Average Humidity:**", f"{safe_text(day.get('avg_humidity_percent'))}%")
            st.write("**Rain Expected:**", safe_text(day.get("rain_expected")))
            st.write("**Total Rain:**", f"{safe_text(total_rain, 0)} mm")


def render_weather_analysis(weather_info):
    weather_analysis = weather_info.get("weather_analysis", {})

    if not weather_analysis:
        st.info("Weather analysis is not available.")
        return

    travel_advice = weather_analysis.get("travel_advice")

    if travel_advice:
        st.info(clean_display_text(travel_advice))


def render_budget_details(result):
    itinerary = result.get("itinerary", {})
    budget_plan = result.get("budget_plan", {})

    st.subheader("Budget Summary")

    budget_summary = itinerary.get("budget_summary")

    if budget_summary:
        st.write(clean_display_text(budget_summary))
    else:
        st.info("Budget summary from itinerary is not available.")

    if not budget_plan:
        st.info("Budget plan is not available.")
        return

    user_budget = budget_plan.get("user_budget", result.get("budget"))
    estimated_total = budget_plan.get("estimated_total")
    within_budget = budget_plan.get("within_budget")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("User Budget", f"INR {safe_money(user_budget)}")

    with c2:
        st.metric("Estimated Total", f"INR {safe_money(estimated_total)}")

    with c3:
        st.metric("Within Budget", str(within_budget))

    explanation = budget_plan.get("calculation_explanation")

    if explanation:
        st.info(clean_display_text(explanation))

    cost_breakdown = budget_plan.get("cost_breakdown", {})

    if cost_breakdown:
        with st.expander("View Cost Breakdown"):
            st.json(cost_breakdown)

    with st.expander("View Raw Budget Agent Output"):
        st.json(budget_plan)


def render_replanner_message(result):
    replanner_message = result.get("replanner_message")

    if replanner_message:
        st.warning(clean_display_text(replanner_message))


def render_structured_trip_plan(result):
    missing_fields = result.get("missing_fields", [])

    if missing_fields:
        final_answer = result.get("final_answer", "Please provide the missing trip details.")
        st.warning(clean_display_text(final_answer))
        return

    itinerary = result.get("itinerary", {})
    final_answer = result.get("final_answer", "")

    if not itinerary:
        if final_answer:
            st.write(clean_display_text(final_answer))
        else:
            st.warning("No itinerary was generated.")
        return

    trip_summary = itinerary.get("trip_summary", "")
    day_wise_plan = itinerary.get("day_wise_plan", [])

    if trip_summary:
        st.subheader("📌 Trip Summary")
        st.success(clean_display_text(trip_summary))

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Destination", safe_text(result.get("destination"), "Not set"))

    with col2:
        st.metric("Duration", f"{safe_text(result.get('duration'), 'N/A')} days")

    with col3:
        st.metric("Budget", f"INR {safe_money(result.get('budget'))}")

    st.divider()

    if day_wise_plan:
        st.subheader("🗓️ Day-wise Trip Plan")

        for day in day_wise_plan:
            render_day_card(day)
    else:
        st.write(clean_display_text(final_answer))

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(
        ["💰 Budget", "🌦️ Weather", "🚗 Transport", "🔁 Tradeoffs & Replanner"]
    )

    with tab1:
        render_budget_details(result)

    with tab2:
        st.subheader("Weather Notes")
        st.write(clean_display_text(itinerary.get("weather_notes", "Weather notes not available.")))

        weather_info = result.get("weather_info", {})

        if weather_info:
            st.write("### Current Weather")
            render_current_weather(weather_info)

            st.divider()

            render_weather_analysis(weather_info)

            st.divider()

            render_forecast(weather_info)

            with st.expander("View Raw Weather Agent Output"):
                st.json(weather_info)
        else:
            st.info("Weather information is not available.")

    with tab3:
        st.subheader("Transport Notes")
        st.write(clean_display_text(itinerary.get("transport_notes", "Transport notes not available.")))

        transport_plan = result.get("transport_plan", {})

        if transport_plan:
            with st.expander("View Transport Plan Details"):
                st.json(transport_plan)
        else:
            st.info("Transport plan is not available.")

    with tab4:
        st.subheader("Tradeoffs Made")

        tradeoffs = itinerary.get("tradeoffs_made", [])

        if tradeoffs:
            for tradeoff in tradeoffs:
                st.markdown(f"- {clean_display_text(tradeoff)}")
        else:
            st.markdown("- No major tradeoffs required.")

        render_replanner_message(result)

    st.divider()

    st.subheader("✅ Final Recommendation")
    st.write(clean_display_text(itinerary.get("final_recommendation", "No final recommendation available.")))

    render_replanner_message(result)


def render_chat_history():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(clean_display_text(message["content"]))


# --------------------------------------------------
# Main UI
# --------------------------------------------------
render_header()
render_sidebar()
render_chat_history()

user_input = st.chat_input(
    "Example: Plan a trip to Goa from 10 July 2026 to 14 July 2026 for a couple with budget 40000 INR"
)

if user_input:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    with st.chat_message("user"):
        st.write(user_input)

    reset_trip_data_for_new_query()

    st.session_state.trip_state["raw_user_input"] = user_input
    st.session_state.trip_state.setdefault("conversation_history", [])

    st.session_state.trip_state["conversation_history"].append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    with st.chat_message("assistant"):
        with st.spinner("Multi-agent planner is preparing your trip..."):
            try:
                graph_result = trip_graph.invoke(st.session_state.trip_state)

                st.session_state.trip_state.update(graph_result)

                merged_result = st.session_state.trip_state

                render_structured_trip_plan(merged_result)

                final_answer = merged_result.get(
                    "final_answer",
                    "Trip plan generated successfully.",
                )

                if not final_answer:
                    final_answer = "Trip plan generated successfully."

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": final_answer,
                    }
                )

                st.session_state.trip_state["conversation_history"].append(
                    {
                        "role": "assistant",
                        "content": final_answer,
                    }
                )

            except Exception as e:
                error_message = f"Something went wrong: {str(e)}"
                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                    }
                )
