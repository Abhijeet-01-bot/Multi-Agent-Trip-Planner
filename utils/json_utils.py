import json
import re


def normalize_llm_output(output):
    """
    Converts different LLM response formats into plain text.

    Gemini/LangChain may return:
    - string
    - list of content blocks
    - dictionary
    - response object having .content
    """

    if output is None:
        return ""

    if isinstance(output, str):
        return output

    if hasattr(output, "content"):
        return normalize_llm_output(output.content)

    if isinstance(output, list):
        parts = []

        for item in output:
            if isinstance(item, str):
                parts.append(item)

            elif isinstance(item, dict):
                if "text" in item:
                    parts.append(str(item["text"]))
                elif "content" in item:
                    parts.append(str(item["content"]))
                else:
                    parts.append(json.dumps(item))

            else:
                parts.append(str(item))

        return "\n".join(parts)

    if isinstance(output, dict):
        if "text" in output:
            return str(output["text"])

        if "content" in output:
            return str(output["content"])

        return json.dumps(output)

    return str(output)


def extract_json_from_text(text):
    """
    Extracts valid JSON safely from LLM output.
    Handles:
    - plain JSON
    - JSON inside markdown code fences
    - Gemini list-based content
    - LangChain response content
    """

    text = normalize_llm_output(text)

    if not text:
        return {}

    cleaned = text.strip()

    cleaned = cleaned.replace("```json", "")
    cleaned = cleaned.replace("```JSON", "")
    cleaned = cleaned.replace("```", "")
    cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)

        if isinstance(parsed, dict):
            return parsed

        return {}

    except json.JSONDecodeError:
        pass

    json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)

    if json_match:
        try:
            parsed = json.loads(json_match.group())

            if isinstance(parsed, dict):
                return parsed

            return {}

        except json.JSONDecodeError:
            return {}

    return {}
