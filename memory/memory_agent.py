from memory.memory_manager import (
    get_chat_history,
    get_memories,
    get_recent_trips,
    save_memory,
    save_trip,
)
from state.trip_state import state_to_dict
from utils.logger_config import setup_logger


logger = setup_logger(__name__)


def memory_retriever_agent(state):
    state = state_to_dict(state)

    user_id = state.get(
        "user_id",
        "default_user",
    )

    memories = get_memories(user_id)
    trips = get_recent_trips(user_id)
    chat_history = get_chat_history(user_id)

    updated_state = dict(state)

    updated_state["retrieved_memories"] = (
        memories
    )

    updated_state["previous_trips"] = (
        trips
    )

    updated_state["chat_history_db"] = (
        chat_history
    )

    logger.info(
        "Retrieved %s trips, %s memories and %s chat messages for %s",
        len(trips),
        len(memories),
        len(chat_history),
        user_id,
    )

    return updated_state


def memory_saver_agent(state):
    """
    Saves trip and preference memory.

    Chat history is intentionally saved only by app.py to avoid
    duplicate user and assistant messages.
    """

    state = state_to_dict(state)

    user_id = state.get(
        "user_id",
        "default_user",
    )

    destination = state.get("destination")
    budget = state.get("budget")
    duration = state.get("duration")
    travel_style = state.get("travel_style")

    if (
        destination
        and not state.get("missing_fields")
    ):
        save_trip(
            user_id=user_id,
            destination=destination,
            budget=budget,
            duration=duration,
            travel_style=travel_style,
        )

    new_memories = []

    if budget:
        if budget >= 75000:
            new_memories.append(
                "User generally prefers premium travel budgets."
            )

        elif budget >= 30000:
            new_memories.append(
                "User generally prefers comfortable travel budgets."
            )

        else:
            new_memories.append(
                "User generally prefers budget-friendly travel."
            )

    if destination:
        new_memories.append(
            f"User previously travelled to {destination}."
        )

    existing_memories = set(
        get_memories(
            user_id,
            limit=100,
        )
    )

    for memory_text in new_memories:
        if memory_text not in existing_memories:
            save_memory(
                user_id=user_id,
                memory_text=memory_text,
            )

    logger.info(
        "Trip and preference memory saved for user: %s",
        user_id,
    )

    return state