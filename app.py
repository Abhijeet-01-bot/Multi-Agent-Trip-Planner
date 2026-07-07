import re
import html
import streamlit as st
from dotenv import load_dotenv

from graph.trip_graph import trip_graph
from state.trip_state import TripState, state_to_dict


load_dotenv()


st.set_page_config(
    page_title="Multi-Agent Smart Trip Planner",
    page_icon="✈️",
    layout="wide",
)


# --------------------------------------------------
# UI Styling - Simple Classic Bold Theme
# --------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #e0f2fe 45%, #ecfdf5 100%);
        color: #111827;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1250px;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1f3a 0%, #123c69 55%, #0f766e 100%);
    }

    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stAlert"] {
        background: rgba(255, 255, 255, 0.15) !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 12px !important;
    }

    .hero-box {
        background: linear-gradient(135deg, #0b1f3a 0%, #1d4ed8 55%, #0f766e 100%);
        padding: 30px;
        border-radius: 24px;
        color: white;
        box-shadow: 0 14px 34px rgba(15, 23, 42, 0.25);
        margin-bottom: 18px;
    }

    .hero-title {
        font-size: 38px;
        font-weight: 900;
        color: #ffffff;
        margin-bottom: 8px;
    }

    .hero-subtitle {
        font-size: 17px;
        line-height: 1.7;
        color: #e0f2fe;
        max-width: 980px;
    }

    .quick-tip {
        background: #ffffff;
        border-left: 7px solid #d97706;
        border-radius: 16px;
        padding: 16px 18px;
        margin-bottom: 16px;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.10);
        color: #111827;
        font-weight: 600;
    }

    .section-card {
        background: #ffffff;
        border-radius: 20px;
        padding: 18px;
        border: 1px solid #cbd5e1;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.10);
        margin-bottom: 16px;
        color: #111827;
    }

    .blue-card {
        border-left: 7px solid #1d4ed8;
    }

    .green-card {
        border-left: 7px solid #16a34a;
    }

    .red-card {
        border-left: 7px solid #dc2626;
    }

    .gold-card {
        border-left: 7px solid #d97706;
    }

    .card-title {
        font-size: 19px;
        font-weight: 900;
        color: #0b1f3a;
        margin-bottom: 6px;
    }

    .card-text {
        font-size: 14.5px;
        color: #334155;
        line-height: 1.7;
        font-weight: 550;
    }

    .missing-box {
        background: #fff7ed;
        border-left: 8px solid #ea580c;
        border-radius: 18px;
        padding: 18px;
        color: #7c2d12;
        box-shadow: 0 8px 20px rgba(124, 45, 18, 0.16);
        margin-bottom: 16px;
    }

    .missing-box h3 {
        color: #7c2d12;
        font-weight: 900;
    }

    .summary-box {
        background: #ecfdf5;
        border-left: 8px solid #16a34a;
        border-radius: 18px;
        padding: 18px;
        color: #14532d;
        box-shadow: 0 8px 20px rgba(20, 83, 45, 0.16);
        margin-bottom: 16px;
    }

    .summary-box h3 {
        color: #14532d;
        font-weight: 900;
    }

    .summary-box p {
        color: #14532d;
        font-weight: 600;
        line-height: 1.7;
    }

    div[data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #bfdbfe !important;
        border-left: 6px solid #1d4ed8 !important;
        border-radius: 16px;
        padding: 14px;
        box-shadow: 0 7px 18px rgba(15, 23, 42, 0.10);
    }

    div[data-testid="stMetric"] * {
        color: #111827 !important;
    }

    div[data-testid="stAlert"] {
        border-radius: 14px !important;
        color: #111827 !important;
        font-weight: 600 !important;
        border: 1px solid #94a3b8 !important;
    }

    div[data-testid="stAlert"] * {
        color: #111827 !important;
        font-weight: 600 !important;
    }

    div[data-testid="stTabs"] {
        background: #ffffff;
        border-radius: 18px;
        padding: 12px;
        border: 1px solid #cbd5e1;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.10);
    }

    div[data-testid="stChatMessage"] {
        background: #ffffff;
        border-radius: 18px;
        border: 1px solid #cbd5e1;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.09);
        color: #111827;
    }

    div[data-testid="stChatMessage"] * {
        color: #111827 !important;
    }

    .day-heading {
        font-size: 22px;
        font-weight: 900;
        color: #0b1f3a;
        margin-bottom: 4px;
    }

    .small-muted {
        color: #475569;
        font-weight: 600;
        font-size: 14px;
    }

    details {
        background: #ffffff !important;
        border-radius: 14px !important;
        border: 1px solid #cbd5e1 !important;
        padding: 8px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Session State
# --------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "trip_state" not in st.session_state:
    st.session_state.trip_state = TripState().model_dump()


# --------------------------------------------------
# Helper Functions
# --------------------------------------------------
def clean_display_text(value):
    if value is None:
        return ""

    text = str(value)

    previous = None
    while previous != text:
        previous = text
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
    st.session_state.trip_state = TripState().model_dump()


def get_trip_completion_status(current_state):
    missing_fields = current_state.get("missing_fields", [])

    if missing_fields:
        return "incomplete"

    required_values = [
        current_state.get("destination"),
        current_state.get("start_date"),
        current_state.get("end_date"),
        current_state.get("number_of_people"),
        current_state.get("budget"),
    ]

    if all(required_values):
        return "complete"

    if current_state.get("destination"):
        return "partial"

    return "empty"


# --------------------------------------------------
# Header and Sidebar
# --------------------------------------------------
def render_header():
    st.markdown(
        """
        <div class="hero-box">
            <div class="hero-title">✈️ Multi-Agent Smart Trip Planner</div>
            <div class="hero-subtitle">
                A clean AI trip assistant that combines planning, live weather,
                destination suggestions, transport strategy, budget estimation,
                replanning, and final itinerary generation.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="quick-tip">
            💡 <b>Best input format:</b>
            Plan a trip to Goa from 10 July 2026 to 14 July 2026 for a couple with budget 40000 INR.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
            <div class="section-card blue-card">
                <div class="card-title">🧠 Planner</div>
                <div class="card-text">Extracts destination, dates, people, budget, and missing fields.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="section-card green-card">
                <div class="card-title">🌦️ Weather</div>
                <div class="card-text">Uses MCP and OpenWeather to fetch live weather and forecast.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="section-card gold-card">
                <div class="card-title">💰 Budget</div>
                <div class="card-text">Estimates trip cost close to the user-entered budget.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            """
            <div class="section-card red-card">
                <div class="card-title">🔁 Replanner</div>
                <div class="card-text">Adjusts the trip plan when budget or constraints need improvement.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("📘 How this assistant works"):
        st.markdown(
            """
            1. **Planner Agent** extracts trip details from your message.  
            2. **Weather Agent** fetches weather using MCP.  
            3. **Destination Agent** chooses suitable activities.  
            4. **Transport Agent** creates a practical movement strategy.  
            5. **Budget Agent** calculates cost using MCP.  
            6. **Replanner Agent** adjusts the plan if needed.  
            7. **Composer Agent** prepares the final day-wise itinerary.
            """
        )


def render_sidebar():
    current_state = st.session_state.trip_state
    status = get_trip_completion_status(current_state)

    with st.sidebar:
        st.title("🧭 Trip State")

        if status == "empty":
            st.info("No trip planned yet. Enter a request to begin.")

        elif status in ["partial", "incomplete"]:
            st.warning("Awaiting missing trip details.")

            missing_fields = current_state.get("missing_fields", [])

            if missing_fields:
                st.write("Missing details:")
                for field in missing_fields:
                    st.write(f"• {safe_text(field)}")

        else:
            st.success("Trip details are complete.")

        st.divider()

        st.subheader("📌 Current Details")

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
            if current_weather.get("success"):
                st.success("Weather data available.")
                st.write("Condition:", safe_text(current_weather.get("description")))
                st.write("Temperature:", f"{safe_text(current_weather.get('temperature_c'))} °C")
                st.write("Humidity:", f"{safe_text(current_weather.get('humidity_percent'))}%")
            else:
                st.warning(safe_text(current_weather.get("error"), "Weather call failed."))
        else:
            st.info("Weather data not generated yet.")

        st.divider()

        if st.button("🔄 Reset Trip", use_container_width=True):
            st.session_state.messages = []
            st.session_state.trip_state = TripState().model_dump()
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

    notes = (
        day.get("notes")
        or day.get("note")
        or day.get("important_notes")
        or day.get("travel_notes")
        or "Keep this day flexible based on weather, local traffic, and availability."
    )

    notes = safe_text(notes)

    with st.container(border=True):
        st.markdown(
            f"<div class='day-heading'>{day_name}: {title}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='small-muted'>📅 Date: {date}</div>",
            unsafe_allow_html=True,
        )

        st.markdown("#### 🌅 Morning")
        st.write(morning)

        st.markdown("#### ☀️ Afternoon")
        st.write(afternoon)

        st.markdown("#### 🌙 Evening")
        st.write(evening)

        st.markdown("#### 📝 Notes")
        st.info(notes)


def render_current_weather(weather_info):
    current_weather = weather_info.get("current_weather", {})

    if not current_weather:
        st.info("Current weather data is not available.")
        return

    if not current_weather.get("success"):
        st.warning(safe_text(current_weather.get("error"), "Weather call failed."))
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

    with st.container(border=True):
        st.write("**Weather Source:**", safe_text(weather_info.get("weather_source")))
        st.write("**API Used:**", safe_text(current_weather.get("api_used")))
        st.write("**Location:**", f"{safe_text(city)}, {safe_text(country)}")
        st.write("**Condition:**", safe_text(current_weather.get("description")))
        st.write("**Feels Like:**", f"{safe_text(current_weather.get('feels_like_c'))} °C")
        st.write("**Pressure:**", f"{safe_text(current_weather.get('pressure_hpa'))} hPa")
        st.write("**Cloudiness:**", f"{safe_text(current_weather.get('cloudiness_percent'))}%")
        st.write("**Rain Last 1h:**", f"{safe_text(rain_1h, 0)} mm")


def render_forecast(weather_info):
    forecast = weather_info.get("forecast", {})

    if not forecast:
        st.info("Forecast data is not available.")
        return

    if not forecast.get("success"):
        st.warning(safe_text(forecast.get("error"), "Forecast call failed."))
        return

    daily_forecast = forecast.get("daily_forecast") or forecast.get("daily_summary") or []

    if not daily_forecast:
        st.info("No forecast summary available.")
        return

    st.markdown("### 5-Day Forecast")

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
            st.write("**Condition:**", safe_text(probable_condition))
            st.write("**Min / Max Temp:**", f"{safe_text(min_temp)} °C / {safe_text(max_temp)} °C")
            st.write("**Humidity:**", f"{safe_text(day.get('avg_humidity_percent'))}%")
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

        st.markdown(
            """
            <div class="missing-box">
                <h3>⚠️ More details needed</h3>
                <p>The assistant needs a few required values before generating the full trip plan.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

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
        st.markdown(
            f"""
            <div class="summary-box">
                <h3>📌 Trip Summary</h3>
                <p>{clean_display_text(trip_summary)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Destination", safe_text(result.get("destination"), "Not set"))

    with col2:
        st.metric("Duration", f"{safe_text(result.get('duration'), 'N/A')} days")

    with col3:
        st.metric("Budget", f"INR {safe_money(result.get('budget'))}")

    st.divider()

    if day_wise_plan:
        st.subheader("🗓️ Day-wise Itinerary")

        for day in day_wise_plan:
            render_day_card(day)
    else:
        st.write(clean_display_text(final_answer))

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(
        ["💰 Budget", "🌦️ Weather", "🚗 Transport", "🔁 Tradeoffs"]
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

            with st.expander("View Raw Weather Output"):
                st.json(weather_info)
        else:
            st.info("Weather information is not available.")

    with tab3:
        st.subheader("Transport Notes")
        st.write(clean_display_text(itinerary.get("transport_notes", "Transport notes not available.")))

        transport_plan = result.get("transport_plan", {})

        if transport_plan:
            with st.expander("View Transport Plan"):
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

                graph_result = state_to_dict(graph_result)

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