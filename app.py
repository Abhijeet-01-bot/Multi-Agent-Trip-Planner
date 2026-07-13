import html
import re
import uuid

import streamlit as st
from dotenv import load_dotenv
from langgraph.types import Command

from graph.trip_graph import trip_graph
from memory.auth_manager import (
    authenticate_user,
    initialize_auth_table,
    register_user,
)
from memory.memory_manager import (
    create_user,
    get_chat_history,
    get_memories,
    get_recent_trips,
    save_chat_message,
)
from memory.memory_schema import initialize_database
from state.trip_state import TripState, state_to_dict


# ==================================================
# Application Configuration
# ==================================================

st.set_page_config(
    page_title="Multi-Agent Smart Trip Planner",
    page_icon="✈️",
    layout="wide",
)

load_dotenv()
initialize_database()
initialize_auth_table()


# ==================================================
# UI Styling
# ==================================================

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #eef6ff 50%, #f0fdf4 100%);
        color: #111827;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1250px;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafc 0%, #e0f2fe 55%, #dcfce7 100%);
        border-right: 1px solid #cbd5e1;
    }

    section[data-testid="stSidebar"] * {
        color: #111827 !important;
    }

    .main-header,
    .auth-header,
    .query-box,
    .soft-card {
        background: #ffffff;
        border: 1px solid #dbeafe;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
        margin-bottom: 16px;
    }

    .auth-header {
        text-align: center;
        max-width: 760px;
        margin: 2rem auto 1.5rem auto;
    }

    .main-header h1,
    .auth-header h1,
    .soft-card-title,
    .day-heading {
        color: #1e3a8a;
        font-weight: 900;
    }

    .main-header p,
    .auth-header p,
    .soft-card-text {
        color: #475569;
        line-height: 1.65;
    }

    .query-box {
        border-left: 7px solid #3b82f6;
    }

    .soft-card {
        min-height: 125px;
    }

    .process-complete,
    .process-pending {
        padding: 9px 11px;
        border-radius: 10px;
        margin-bottom: 7px;
        font-weight: 700;
    }

    .process-complete {
        background: #dcfce7;
        border-left: 5px solid #16a34a;
    }

    .process-pending {
        background: #f1f5f9;
        border-left: 5px solid #94a3b8;
    }

    .review-box {
        background: #fff7ed;
        border: 1px solid #fdba74;
        border-left: 7px solid #f97316;
        border-radius: 18px;
        padding: 18px;
        margin: 16px 0;
        color: #7c2d12;
    }

    .replanned-box {
        background: #ecfdf5;
        border: 1px solid #86efac;
        border-left: 7px solid #16a34a;
        border-radius: 18px;
        padding: 18px;
        margin: 16px 0;
        color: #14532d;
    }

    .memory-card {
        background: rgba(255, 255, 255, 0.85);
        border: 1px solid #bfdbfe;
        border-radius: 12px;
        padding: 10px 12px;
        margin-bottom: 9px;
    }

    .day-heading {
        font-size: 21px;
        margin-bottom: 4px;
    }

    .small-muted {
        color: #64748b;
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 10px;
    }

    div[data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #dbeafe !important;
        border-left: 5px solid #60a5fa !important;
        border-radius: 16px;
        padding: 14px;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06);
    }

    div[data-testid="stMetric"] * {
        color: #111827 !important;
    }

    div[data-testid="stAlert"] {
        border-radius: 14px !important;
        border: 1px solid #cbd5e1 !important;
    }

    div[data-testid="stAlert"] * {
        color: #111827 !important;
        font-weight: 600 !important;
    }

    div[data-testid="stChatMessage"],
    div[data-testid="stTabs"],
    details {
        background: #ffffff !important;
        border: 1px solid #dbeafe !important;
        border-radius: 14px !important;
    }

    div[data-testid="stTextArea"] textarea,
    div[data-testid="stTextInput"] input,
    div[data-baseweb="input"] input,
    div[data-baseweb="base-input"] input {
        background: #ffffff !important;
        color: #111827 !important;
        caret-color: #2563eb !important;
        cursor: text !important;
        pointer-events: auto !important;
        -webkit-text-fill-color: #111827 !important;
        opacity: 1 !important;
    }

    div[data-testid="stTextArea"] textarea::placeholder,
    div[data-testid="stTextInput"] input::placeholder {
        color: #94a3b8 !important;
        opacity: 1 !important;
    }

    label {
        color: #111827 !important;
        font-weight: 600 !important;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        background: #2563eb !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        min-height: 42px;
    }

    .stButton > button *,
    .stFormSubmitButton > button * {
        color: #ffffff !important;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        background: #1d4ed8 !important;
        color: #ffffff !important;
    }

    button[role="tab"],
    button[role="tab"] * {
        color: #1e3a8a !important;
        font-weight: 700 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# Session State
# ==================================================

SESSION_DEFAULTS = {
    "messages": [],
    "authenticated": False,
    "logged_in_user": None,
    "trip_state": TripState().model_dump(),
    "pending_review": None,
    "graph_thread_id": None,
}

for session_key, default_value in SESSION_DEFAULTS.items():
    if session_key not in st.session_state:
        st.session_state[session_key] = default_value


# ==================================================
# Utility Functions
# ==================================================

def clean_display_text(value):
    if value is None:
        return ""

    text = str(value)
    previous_text = None

    while previous_text != text:
        previous_text = text
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
    return cleaned if cleaned else default


def safe_money(value):
    if value is None or value == "":
        return "N/A"

    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def normalize_user_id(user_id):
    return str(user_id or "").strip()


def normalize_chat_rows(rows):
    normalized = []

    for row in rows or []:
        if isinstance(row, dict):
            role = row.get("role", "assistant")
            content = row.get("message") or row.get("content") or ""
        elif isinstance(row, (list, tuple)) and len(row) >= 2:
            role = row[0]
            content = row[1]
        else:
            continue

        if content:
            normalized.append(
                {
                    "role": str(role),
                    "content": str(content),
                }
            )

    return normalized


def load_user_data(user_id, load_messages=True):
    user_id = normalize_user_id(user_id)

    if not user_id:
        return

    create_user(user_id)

    previous_trips = get_recent_trips(user_id)
    retrieved_memories = get_memories(user_id)
    chat_rows = get_chat_history(user_id)

    st.session_state.trip_state["user_id"] = user_id
    st.session_state.trip_state["previous_trips"] = previous_trips
    st.session_state.trip_state["retrieved_memories"] = retrieved_memories
    st.session_state.trip_state["chat_history_db"] = chat_rows

    if load_messages:
        st.session_state.messages = normalize_chat_rows(chat_rows)


def create_fresh_trip_state(preserve_memory=True):
    user_id = st.session_state.logged_in_user or "default_user"
    fresh_state = TripState().model_dump()
    fresh_state["user_id"] = user_id

    if preserve_memory:
        fresh_state["previous_trips"] = get_recent_trips(user_id)
        fresh_state["retrieved_memories"] = get_memories(user_id)
        fresh_state["chat_history_db"] = get_chat_history(user_id)

    st.session_state.trip_state = fresh_state


def get_graph_config():
    return {
        "configurable": {
            "thread_id": st.session_state.graph_thread_id,
        }
    }


def extract_interrupt(result):
    if not isinstance(result, dict):
        return None

    interrupts = result.get("__interrupt__", [])

    if not interrupts:
        return None

    first_interrupt = interrupts[0]
    return getattr(first_interrupt, "value", first_interrupt)


def persist_assistant_result(user_id, result):
    final_answer = (
        result.get("final_answer")
        or "Trip plan generated successfully."
    )

    assistant_message = {
        "role": "assistant",
        "content": final_answer,
    }

    st.session_state.messages.append(assistant_message)

    save_chat_message(
        user_id=user_id,
        role="assistant",
        message=final_answer,
    )

    load_user_data(user_id, load_messages=False)


# ==================================================
# Authentication UI
# ==================================================

def render_login_screen():
    st.markdown(
        """
        <div class="auth-header">
            <h1>✈️ Multi-Agent Smart Trip Planner</h1>
            <p>Sign in to access your saved trips, preferences, and conversations.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, auth_column, _ = st.columns([1, 2, 1])

    with auth_column:
        login_tab, signup_tab = st.tabs(["🔑 Login", "🆕 Sign Up"])

        with login_tab:
            with st.form("login_form"):
                login_user = st.text_input(
                    "User ID",
                    placeholder="Enter your user ID",
                )
                login_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                )
                login_submitted = st.form_submit_button(
                    "Login",
                    use_container_width=True,
                )

            if login_submitted:
                login_user = normalize_user_id(login_user)

                if not login_user or not login_password:
                    st.error("Please enter both User ID and password.")
                elif authenticate_user(login_user, login_password):
                    st.session_state.authenticated = True
                    st.session_state.logged_in_user = login_user
                    create_fresh_trip_state(preserve_memory=False)
                    st.session_state.trip_state["user_id"] = login_user
                    load_user_data(login_user, load_messages=True)
                    st.session_state.pending_review = None
                    st.session_state.graph_thread_id = None
                    st.rerun()
                else:
                    st.error("Invalid User ID or password.")

        with signup_tab:
            with st.form("signup_form"):
                signup_user = st.text_input(
                    "Create User ID",
                    placeholder="Choose a unique user ID",
                )
                signup_password = st.text_input(
                    "Create Password",
                    type="password",
                    placeholder="At least 6 characters",
                )
                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Re-enter your password",
                )
                signup_submitted = st.form_submit_button(
                    "Create Account",
                    use_container_width=True,
                )

            if signup_submitted:
                signup_user = normalize_user_id(signup_user)

                if len(signup_user) < 3:
                    st.error("User ID must contain at least 3 characters.")
                elif len(signup_password) < 6:
                    st.error("Password must contain at least 6 characters.")
                elif signup_password != confirm_password:
                    st.error("Passwords do not match.")
                elif register_user(signup_user, signup_password):
                    create_user(signup_user)
                    st.success("Account created successfully. You can now log in.")
                else:
                    st.error("That User ID already exists.")


# ==================================================
# Main Header and Sidebar
# ==================================================

def render_header():
    st.markdown(
        """
        <div class="main-header">
            <h1>✈️ Multi-Agent Smart Trip Planner</h1>
            <p>
                Weather-aware and budget-aware trip planning with persistent
                memory and human approval for over-budget plans.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    state = st.session_state.trip_state

    with st.sidebar:
        st.subheader("👤 User Profile")
        st.success(f"Logged in as: {st.session_state.logged_in_user}")

        refresh_col, reset_col = st.columns(2)

        with refresh_col:
            if st.button("↻ Refresh", use_container_width=True):
                load_user_data(
                    st.session_state.logged_in_user,
                    load_messages=True,
                )
                st.rerun()

        with reset_col:
            if st.button("Reset", use_container_width=True):
                create_fresh_trip_state(preserve_memory=True)
                st.session_state.pending_review = None
                st.session_state.graph_thread_id = None
                st.rerun()

        st.divider()
        st.subheader("🧩 Workflow")

        stages = [
            (
                "Memory Retriever",
                bool(
                    state.get("previous_trips")
                    or state.get("retrieved_memories")
                    or state.get("chat_history_db")
                ),
            ),
            (
                "Planner",
                bool(state.get("destination") or state.get("missing_fields")),
            ),
            ("Weather", bool(state.get("weather_info"))),
            ("Destination", bool(state.get("destination_plan"))),
            ("Transport", bool(state.get("transport_plan"))),
            ("Budget", bool(state.get("budget_plan"))),
            (
                "Human Review",
                bool(
                    state.get("human_decision")
                    or st.session_state.pending_review
                ),
            ),
            ("Composer", bool(state.get("itinerary"))),
        ]

        completed_count = sum(done for _, done in stages)
        st.progress(completed_count / len(stages))
        st.caption(f"{completed_count}/{len(stages)} stages completed")

        for stage_name, is_complete in stages:
            css_class = "process-complete" if is_complete else "process-pending"
            icon = "✅" if is_complete else "⏳"
            st.markdown(
                f'<div class="{css_class}">{icon} {stage_name}</div>',
                unsafe_allow_html=True,
            )

        st.divider()
        st.subheader("📌 Current Trip")
        st.write("Destination:", safe_text(state.get("destination"), "Not set"))
        st.write(
            "Dates:",
            (
                f"{safe_text(state.get('start_date'), 'Not set')} → "
                f"{safe_text(state.get('end_date'), 'Not set')}"
            ),
        )
        st.write("People:", state.get("number_of_people") or "Not set")
        st.write("Budget:", f"INR {safe_money(state.get('budget'))}")

        if state.get("missing_fields"):
            st.markdown("#### ⚠️ Missing Details")
            for missing_field in state["missing_fields"]:
                st.write(f"• {safe_text(missing_field)}")

        st.divider()
        st.subheader("🧠 Long-Term Memory")

        trips = state.get("previous_trips", [])
        memories = state.get("retrieved_memories", [])
        chats = state.get("chat_history_db", [])

        metric_1, metric_2, metric_3 = st.columns(3)
        metric_1.metric("Trips", len(trips))
        metric_2.metric("Memory", len(memories))
        metric_3.metric("Chats", len(chats))

        with st.expander("📍 Previous Trips"):
            if not trips:
                st.caption("No saved trips yet.")

            for trip in trips[:10]:
                if isinstance(trip, dict):
                    destination = trip.get("destination", "Unknown")
                    budget = trip.get("budget")
                    duration = trip.get("duration")
                    travel_style = trip.get("travel_style")
                elif isinstance(trip, (list, tuple)):
                    destination = trip[0] if len(trip) > 0 else "Unknown"
                    budget = trip[1] if len(trip) > 1 else None
                    duration = trip[2] if len(trip) > 2 else None
                    travel_style = trip[3] if len(trip) > 3 else None
                else:
                    continue

                st.markdown(
                    f"""
                    <div class="memory-card">
                        <strong>{html.escape(safe_text(destination))}</strong><br>
                        Budget: INR {safe_money(budget)}<br>
                        Duration: {safe_text(duration, 'N/A')} days<br>
                        Style: {html.escape(safe_text(travel_style, 'Not specified'))}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with st.expander("💭 Learned Preferences"):
            unique_memories = list(dict.fromkeys(memories))

            if not unique_memories:
                st.caption("No learned preferences yet.")

            for memory in unique_memories[:15]:
                st.write(f"• {safe_text(memory)}")

        with st.expander("💬 Recent Chats"):
            normalized_chats = normalize_chat_rows(chats)

            if not normalized_chats:
                st.caption("No stored conversations yet.")

            for message in normalized_chats[-10:]:
                preview = safe_text(message["content"])
                if len(preview) > 110:
                    preview = f"{preview[:110]}..."
                st.caption(f"{message['role'].title()}: {preview}")

        st.divider()

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.logged_in_user = None
            st.session_state.messages = []
            st.session_state.trip_state = TripState().model_dump()
            st.session_state.pending_review = None
            st.session_state.graph_thread_id = None
            st.rerun()


# ==================================================
# Query and Human Review Forms
# ==================================================

def render_query_form():
    st.markdown(
        """
        <div class="query-box">
            <b>💬 Enter your trip request</b><br>
            <span style="color: #64748b;">
                Include destination, dates, travelers, and budget.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "Example: Plan a trip to Goa from 10 July 2026 to "
        "14 July 2026 for a couple with budget 40000 INR."
    )

    with st.form("trip_query_form", clear_on_submit=True):
        user_input = st.text_area(
            "Trip request",
            placeholder="Type your trip request here...",
            height=120,
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button(
            "🚀 Generate Trip Plan",
            use_container_width=True,
        )

    if submitted:
        cleaned_input = user_input.strip()
        if not cleaned_input:
            st.warning("Please type a trip request before generating the plan.")
            return None
        return cleaned_input

    return None


def render_budget_review(payload):
    st.markdown(
        """
        <div class="review-box">
            <h3>⚠️ Budget Review Required</h3>
            <p>
                The estimated trip cost exceeds your budget.
                Choose how the workflow should continue.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_budget = payload.get("user_budget")
    estimated_total = payload.get("estimated_total")

    try:
        excess_amount = int(estimated_total) - int(user_budget)
    except (TypeError, ValueError):
        excess_amount = None

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Your Budget", f"INR {safe_money(user_budget)}")
    metric_2.metric("Current Estimate", f"INR {safe_money(estimated_total)}")
    metric_3.metric("Excess", f"INR {safe_money(excess_amount)}")

    if payload.get("message"):
        st.info(clean_display_text(payload["message"]))

    approve_col, continue_col = st.columns(2)

    with approve_col:
        approve_replanning = st.button(
            "✅ Approve Replanning",
            use_container_width=True,
        )

    with continue_col:
        continue_current = st.button(
            "➡️ Continue Current Plan",
            use_container_width=True,
        )

    default_budget = int(user_budget) if user_budget else 1

    with st.form("updated_budget_form"):
        new_budget = st.number_input(
            "Or update your total budget",
            min_value=1,
            value=default_budget,
            step=1000,
        )
        update_budget = st.form_submit_button(
            "Update Budget and Recalculate",
            use_container_width=True,
        )

    if approve_replanning:
        return {"action": "approve_replan"}

    if continue_current:
        return {"action": "continue_current"}

    if update_budget:
        return {
            "action": "update_budget",
            "new_budget": int(new_budget),
        }

    return None


# ==================================================
# Result Rendering
# ==================================================

def render_day_card(day):
    with st.container(border=True):
        st.markdown(
            f"### {safe_text(day.get('day'), 'Day')}: "
            f"{safe_text(day.get('title'), 'Trip Plan')}"
        )
        st.caption(f"📅 {safe_text(day.get('date'), 'Date not specified')}")

        st.markdown("#### 🌅 Morning")
        st.write(safe_text(day.get("morning"), "Morning plan not specified."))

        st.markdown("#### ☀️ Afternoon")
        st.write(safe_text(day.get("afternoon"), "Afternoon plan not specified."))

        st.markdown("#### 🌙 Evening")
        st.write(safe_text(day.get("evening"), "Evening plan not specified."))

        notes = safe_text(
            day.get("notes"),
            "Keep the day flexible based on weather and availability.",
        )

        technical_phrases = [
            "fallback day plan",
            "llm response was unavailable",
            "llm response was invalid",
            "generated because the llm",
        ]

        if any(phrase in notes.lower() for phrase in technical_phrases):
            notes = (
                "Keep this day flexible based on weather, local traffic, "
                "opening hours, and personal energy levels."
            )

        st.markdown("#### 📝 Notes")
        st.info(notes)


def render_replanned_summary(result):
    revised_total = result.get("revised_estimated_total")

    if not revised_total:
        return

    original_total = result.get(
        "original_budget_plan",
        {},
    ).get("estimated_total")

    st.markdown(
        """
        <div class="replanned-box">
            <h3>✅ Human-Approved Replanned Trip</h3>
            <p>The updated budget and revised itinerary are shown below.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Original Estimate", f"INR {safe_money(original_total)}")
    metric_2.metric("Revised Estimate", f"INR {safe_money(revised_total)}")
    metric_3.metric("Savings", f"INR {safe_money(result.get('savings_amount'))}")

    for change in result.get("replan_changes", []):
        st.write(f"• {safe_text(change)}")

def format_label(key):
    return str(key).replace("_", " ").strip().title()


def render_value(value, currency=False):
    if value is None or value == "":
        return "Not available"

    if isinstance(value, bool):
        return "Yes" if value else "No"

    if currency and isinstance(value, (int, float)):
        return f"INR {safe_money(value)}"

    return safe_text(value)


def render_budget_panel(result):
    itinerary = result.get("itinerary", {})
    budget_plan = result.get("budget_plan", {})

    st.subheader("💰 Budget Summary")

    budget_summary = itinerary.get("budget_summary")

    if budget_summary:
        st.write(clean_display_text(budget_summary))

    if not budget_plan:
        st.info("Budget details are not available.")
        return

    user_budget = budget_plan.get(
        "user_budget",
        result.get("budget"),
    )

    estimated_total = budget_plan.get(
        "estimated_total"
    )

    within_budget = budget_plan.get(
        "within_budget"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "User Budget",
            f"INR {safe_money(user_budget)}",
        )

    with col2:
        st.metric(
            "Estimated Total",
            f"INR {safe_money(estimated_total)}",
        )

    with col3:
        if within_budget is True:
            budget_status = "Within Budget"
        elif within_budget is False:
            budget_status = "Over Budget"
        else:
            budget_status = "Not Determined"

        st.metric(
            "Budget Status",
            budget_status,
        )

    explanation = budget_plan.get(
        "calculation_explanation"
    )

    if explanation:
        st.info(
            clean_display_text(explanation)
        )

    cost_breakdown = budget_plan.get(
        "cost_breakdown",
        {},
    )

    if cost_breakdown:
        st.markdown("### Cost Breakdown")

        currency_keywords = [
            "cost",
            "budget",
            "total",
            "stay",
            "hotel",
            "accommodation",
            "food",
            "transport",
            "activity",
            "activities",
            "buffer",
            "miscellaneous",
        ]

        for key, value in cost_breakdown.items():
            is_currency = any(
                keyword in str(key).lower()
                for keyword in currency_keywords
            )

            col_label, col_value = st.columns([2, 1])

            with col_label:
                st.write(
                    f"**{format_label(key)}**"
                )

            with col_value:
                if is_currency and isinstance(
                    value,
                    (int, float),
                ):
                    st.write(
                        f"INR {safe_money(value)}"
                    )
                else:
                    st.write(
                        render_value(value)
                    )

    revised_total = result.get(
        "revised_estimated_total"
    )

    if revised_total:
        st.divider()
        st.markdown("### Replanning Result")

        original_total = result.get(
            "original_budget_plan",
            {},
        ).get("estimated_total")

        savings_amount = result.get(
            "savings_amount"
        )

        r1, r2, r3 = st.columns(3)

        with r1:
            st.metric(
                "Original Estimate",
                f"INR {safe_money(original_total)}",
            )

        with r2:
            st.metric(
                "Revised Estimate",
                f"INR {safe_money(revised_total)}",
            )

        with r3:
            st.metric(
                "Total Savings",
                f"INR {safe_money(savings_amount)}",
            )

        replan_changes = result.get(
            "replan_changes",
            [],
        )

        if replan_changes:
            st.markdown("#### Changes Made")

            for change in replan_changes:
                st.write(
                    f"• {clean_display_text(change)}"
                )


def render_weather_panel(result):
    itinerary = result.get("itinerary", {})
    weather_info = result.get("weather_info", {})

    st.subheader("🌦️ Weather Overview")

    weather_notes = itinerary.get(
        "weather_notes"
    )

    if weather_notes:
        st.write(
            clean_display_text(weather_notes)
        )

    if not weather_info:
        st.info("Weather information is not available.")
        return

    current_weather = weather_info.get(
        "current_weather",
        {},
    )

    if current_weather:
        if current_weather.get("success") is False:
            st.warning(
                safe_text(
                    current_weather.get("error"),
                    "The weather request was unsuccessful.",
                )
            )
        else:
            temperature = current_weather.get(
                "temperature_c"
            )

            humidity = current_weather.get(
                "humidity_percent"
            )

            wind_speed = (
                current_weather.get("wind_speed")
                or current_weather.get(
                    "wind_speed_mps"
                )
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Temperature",
                    (
                        f"{temperature} °C"
                        if temperature is not None
                        else "N/A"
                    ),
                )

            with col2:
                st.metric(
                    "Humidity",
                    (
                        f"{humidity}%"
                        if humidity is not None
                        else "N/A"
                    ),
                )

            with col3:
                st.metric(
                    "Wind Speed",
                    (
                        f"{wind_speed} m/s"
                        if wind_speed is not None
                        else "N/A"
                    ),
                )

            city = (
                current_weather.get("city")
                or current_weather.get("location")
            )

            country = current_weather.get(
                "country"
            )

            description = current_weather.get(
                "description"
            )

            feels_like = current_weather.get(
                "feels_like_c"
            )

            pressure = current_weather.get(
                "pressure_hpa"
            )

            cloudiness = current_weather.get(
                "cloudiness_percent"
            )

            with st.container(border=True):
                if city or country:
                    location_text = ", ".join(
                        part
                        for part in [city, country]
                        if part
                    )

                    st.write(
                        "**Location:**",
                        location_text,
                    )

                st.write(
                    "**Condition:**",
                    safe_text(description),
                )

                st.write(
                    "**Feels Like:**",
                    (
                        f"{feels_like} °C"
                        if feels_like is not None
                        else "Not available"
                    ),
                )

                st.write(
                    "**Pressure:**",
                    (
                        f"{pressure} hPa"
                        if pressure is not None
                        else "Not available"
                    ),
                )

                st.write(
                    "**Cloudiness:**",
                    (
                        f"{cloudiness}%"
                        if cloudiness is not None
                        else "Not available"
                    ),
                )

    weather_analysis = weather_info.get(
        "weather_analysis",
        {},
    )

    if weather_analysis:
        travel_advice = weather_analysis.get(
            "travel_advice"
        )

        if travel_advice:
            st.markdown("### Travel Advice")
            st.info(
                clean_display_text(travel_advice)
            )

    forecast = weather_info.get(
        "forecast",
        {},
    )

    if not forecast:
        return

    if forecast.get("success") is False:
        st.warning(
            safe_text(
                forecast.get("error"),
                "Forecast information could not be retrieved.",
            )
        )
        return

    daily_forecast = (
        forecast.get("daily_forecast")
        or forecast.get("daily_summary")
        or []
    )

    if not daily_forecast:
        return

    st.markdown("### Forecast")

    for forecast_day in daily_forecast:
        date = safe_text(
            forecast_day.get("date"),
            "Date not available",
        )

        condition = (
            forecast_day.get(
                "probable_condition"
            )
            or forecast_day.get(
                "dominant_condition"
            )
            or "Not available"
        )

        min_temperature = (
            forecast_day.get(
                "min_temperature_c"
            )
            or forecast_day.get(
                "min_temp_c"
            )
        )

        max_temperature = (
            forecast_day.get(
                "max_temperature_c"
            )
            or forecast_day.get(
                "max_temp_c"
            )
        )

        humidity = forecast_day.get(
            "avg_humidity_percent"
        )

        rain_expected = forecast_day.get(
            "rain_expected"
        )

        with st.container(border=True):
            st.markdown(f"#### 📅 {date}")

            forecast_col1, forecast_col2 = (
                st.columns(2)
            )

            with forecast_col1:
                st.write(
                    "**Condition:**",
                    safe_text(condition),
                )

                st.write(
                    "**Temperature:**",
                    (
                        f"{min_temperature} °C – "
                        f"{max_temperature} °C"
                        if (
                            min_temperature is not None
                            and max_temperature is not None
                        )
                        else "Not available"
                    ),
                )

            with forecast_col2:
                st.write(
                    "**Average Humidity:**",
                    (
                        f"{humidity}%"
                        if humidity is not None
                        else "Not available"
                    ),
                )

                st.write(
                    "**Rain Expected:**",
                    render_value(rain_expected),
                )


def render_transport_panel(result):
    itinerary = result.get("itinerary", {})
    transport_plan = result.get(
        "transport_plan",
        {},
    )

    st.subheader("🚗 Transport Plan")

    transport_notes = itinerary.get(
        "transport_notes"
    )

    if transport_notes:
        st.write(
            clean_display_text(transport_notes)
        )

    if not transport_plan:
        st.info("Transport details are not available.")
        return

    priority_fields = [
        "recommended_transport",
        "transport_mode",
        "primary_transport",
        "local_transport",
        "airport_transfer",
        "estimated_transport_cost",
        "transport_cost",
        "travel_time",
        "reasoning",
        "recommendation",
    ]

    displayed_keys = set()

    for key in priority_fields:
        if key not in transport_plan:
            continue

        value = transport_plan.get(key)

        if value in [None, "", [], {}]:
            continue

        displayed_keys.add(key)

        st.markdown(
            f"### {format_label(key)}"
        )

        if isinstance(value, list):
            for item in value:
                st.write(
                    f"• {clean_display_text(item)}"
                )

        elif isinstance(value, dict):
            with st.container(border=True):
                for sub_key, sub_value in value.items():
                    st.write(
                        f"**{format_label(sub_key)}:** "
                        f"{render_value(sub_value)}"
                    )

        elif (
            "cost" in key.lower()
            and isinstance(value, (int, float))
        ):
            st.write(
                f"INR {safe_money(value)}"
            )

        else:
            st.write(
                clean_display_text(value)
            )

    remaining_items = {
        key: value
        for key, value in transport_plan.items()
        if (
            key not in displayed_keys
            and value not in [None, "", [], {}]
        )
    }

    if remaining_items:
        st.markdown("### Additional Transport Details")

        for key, value in remaining_items.items():
            with st.container(border=True):
                st.markdown(
                    f"#### {format_label(key)}"
                )

                if isinstance(value, list):
                    for item in value:
                        st.write(
                            f"• {clean_display_text(item)}"
                        )

                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        st.write(
                            f"**{format_label(sub_key)}:** "
                            f"{render_value(sub_value)}"
                        )

                else:
                    st.write(
                        render_value(value)
                    )
def render_structured_trip_plan(result):
    if result.get("missing_fields"):
        st.warning(clean_display_text(result.get("final_answer")))
        return

    itinerary = result.get("itinerary", {})

    if not itinerary:
        if not result.get("human_review_required"):
            st.warning("No itinerary was generated.")
        return

    render_replanned_summary(result)

    st.subheader("📌 Trip Summary")
    st.success(safe_text(itinerary.get("trip_summary"), "Trip summary unavailable."))

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Destination", safe_text(result.get("destination"), "Not set"))
    metric_2.metric("Duration", f"{safe_text(result.get('duration'), 'N/A')} days")
    metric_3.metric("Budget", f"INR {safe_money(result.get('budget'))}")

    st.divider()
    st.subheader("🗓️ Day-wise Itinerary")

    for day in itinerary.get("day_wise_plan", []):
        render_day_card(day)

    budget_tab, weather_tab, transport_tab, tradeoff_tab = st.tabs(
        ["💰 Budget", "🌦️ Weather", "🚗 Transport", "🔁 Tradeoffs"]
    )

    with budget_tab:
        render_budget_panel(result)

    with weather_tab:
        render_weather_panel(result)

    with transport_tab:
        render_transport_panel(result)

    with tradeoff_tab:
        st.subheader("🔁 Tradeoffs and Replanning")

        tradeoffs = itinerary.get(
        "tradeoffs_made",
        [],
        )

        if tradeoffs:
            for tradeoff in tradeoffs:
                st.write(
                f"• {clean_display_text(tradeoff)}"
                )
        else:
            st.info(
            "No major tradeoffs were required."
            )

        replan_changes = result.get(
        "replan_changes",
        [],
        )

        if replan_changes:
            st.markdown("### Replanning Changes")

            for change in replan_changes:
                st.write(
                f"• {clean_display_text(change)}"
                )

        replanner_message = result.get(
        "replanner_message"
        )

        if replanner_message:
            st.info(
                clean_display_text(
                replanner_message
                )
            )

    st.divider()
    st.subheader("✅ Final Recommendation")
    st.write(
        safe_text(
            itinerary.get("final_recommendation"),
            "Final recommendation unavailable.",
        )
    )


def render_chat_history():
    if not st.session_state.messages:
        return

    st.subheader("💬 Conversation History")

    for message in st.session_state.messages:
        with st.chat_message(message.get("role", "assistant")):
            st.write(clean_display_text(message.get("content", "")))


# ==================================================
# Graph Execution
# ==================================================

def start_trip_graph(user_input):
    create_fresh_trip_state(preserve_memory=True)

    user_id = st.session_state.logged_in_user
    st.session_state.graph_thread_id = f"{user_id}-{uuid.uuid4()}"

    state = st.session_state.trip_state
    state["user_id"] = user_id
    state["raw_user_input"] = user_input
    state["conversation_history"] = [
        {
            "role": "user",
            "content": user_input,
        }
    ]

    user_message = {
        "role": "user",
        "content": user_input,
    }

    st.session_state.messages.append(user_message)

    save_chat_message(
        user_id=user_id,
        role="user",
        message=user_input,
    )

    result = trip_graph.invoke(
        state,
        config=get_graph_config(),
    )

    result = state_to_dict(result)
    st.session_state.trip_state.update(result)

    interrupt_payload = extract_interrupt(result)

    if interrupt_payload:
        st.session_state.pending_review = interrupt_payload
        return

    st.session_state.pending_review = None
    persist_assistant_result(user_id, st.session_state.trip_state)


def resume_trip_graph(decision):
    result = trip_graph.invoke(
        Command(resume=decision),
        config=get_graph_config(),
    )

    result = state_to_dict(result)
    st.session_state.trip_state.update(result)

    interrupt_payload = extract_interrupt(result)

    if interrupt_payload:
        st.session_state.pending_review = interrupt_payload
        return

    st.session_state.pending_review = None
    persist_assistant_result(
        st.session_state.logged_in_user,
        st.session_state.trip_state,
    )


# ==================================================
# Main Application
# ==================================================

if not st.session_state.authenticated:
    render_login_screen()
    st.stop()

current_user = st.session_state.logged_in_user

if st.session_state.trip_state.get("user_id") != current_user:
    create_fresh_trip_state(preserve_memory=False)
    st.session_state.trip_state["user_id"] = current_user
    load_user_data(current_user, load_messages=True)

render_header()
render_sidebar()

if st.session_state.pending_review:
    decision = render_budget_review(st.session_state.pending_review)

    if decision:
        with st.spinner("Continuing the workflow with your decision..."):
            resume_trip_graph(decision)
        st.rerun()
else:
    user_input = render_query_form()

    if user_input:
        with st.spinner("Multi-agent planner is preparing your trip..."):
            start_trip_graph(user_input)
        st.rerun()

if (
    st.session_state.trip_state.get("itinerary")
    or st.session_state.trip_state.get("missing_fields")
):
    render_structured_trip_plan(st.session_state.trip_state)

render_chat_history()
