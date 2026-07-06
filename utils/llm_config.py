import os
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from utils.logger_config import setup_logger


logger = setup_logger(__name__)

load_dotenv()


def get_llm(model_name=None):
    """
    Returns Gemini LLM instance.
    """

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        logger.error("GOOGLE_API_KEY is missing in .env file.")

        raise ValueError(
            "GOOGLE_API_KEY is missing. Please add it inside your .env file."
        )

    selected_model = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    logger.info("Creating Gemini LLM instance with model: %s", selected_model)

    llm = ChatGoogleGenerativeAI(
        model=selected_model,
        google_api_key=api_key,
        temperature=0.3,
    )

    return llm


def get_fallback_models():
    """
    Returns primary + fallback Gemini models.
    """

    primary_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    fallback_models_env = os.getenv(
        "GEMINI_FALLBACK_MODELS",
        "gemini-1.5-flash,gemini-3.5-flash"
    )

    fallback_models = [
        model.strip()
        for model in fallback_models_env.split(",")
        if model.strip()
    ]

    models = [primary_model]

    for model in fallback_models:
        if model not in models:
            models.append(model)

    logger.info("Gemini model fallback list: %s", models)

    return models


def invoke_llm_with_retry(prompt, agent_name="Agent", retries=3, sleep_seconds=6):
    """
    Calls Gemini with retry and fallback model handling.

    Handles temporary errors like:
    - 503 UNAVAILABLE
    - high demand
    - service unavailable
    """

    models = get_fallback_models()

    last_error = None

    for model in models:
        logger.info(
            "Gemini API Call: %s using model: %s",
            agent_name,
            model,
        )

        llm = get_llm(model)

        for attempt in range(1, retries + 1):
            try:
                logger.info(
                    "%s attempt %s/%s using model %s",
                    agent_name,
                    attempt,
                    retries,
                    model,
                )

                response = llm.invoke(prompt)

                logger.info(
                    "%s succeeded using model %s on attempt %s",
                    agent_name,
                    model,
                    attempt,
                )

                return response

            except Exception as e:
                last_error = e
                error_text = str(e)

                retryable_error = (
                    "503" in error_text
                    or "UNAVAILABLE" in error_text
                    or "high demand" in error_text.lower()
                    or "temporarily unavailable" in error_text.lower()
                    or "429" in error_text
                    or "resource exhausted" in error_text.lower()
                )

                logger.warning(
                    "%s failed on model %s, attempt %s/%s: %s",
                    agent_name,
                    model,
                    attempt,
                    retries,
                    error_text,
                )

                if retryable_error and attempt < retries:
                    sleep_time = sleep_seconds * attempt

                    logger.info(
                        "Retryable Gemini error detected. Sleeping for %s seconds before retry.",
                        sleep_time,
                    )

                    time.sleep(sleep_time)

                    continue

                break

    logger.error(
        "%s failed after retrying Gemini models. Last error: %s",
        agent_name,
        last_error,
    )

    raise Exception(
        f"{agent_name} failed after retrying Gemini models. Last error: {last_error}"
    )
