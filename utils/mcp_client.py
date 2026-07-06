import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from utils.logger_config import setup_logger


logger = setup_logger(__name__)


def parse_mcp_result(result):
    """
    Converts MCP CallToolResult into a normal Python dictionary.

    MCP tool calls usually return a CallToolResult object.
    The actual response is usually inside:
        result.content[0].text
    """

    try:
        logger.info("Parsing MCP result")

        if hasattr(result, "structuredContent") and result.structuredContent:
            logger.info("MCP result contains structuredContent")
            return result.structuredContent

        if hasattr(result, "content") and result.content:
            first_content = result.content[0]

            if hasattr(first_content, "text"):
                logger.info("MCP result contains text content")

                text_response = first_content.text

                try:
                    parsed_result = json.loads(text_response)

                    logger.info("MCP result parsed successfully")

                    return parsed_result

                except json.JSONDecodeError:
                    logger.warning(
                        "MCP text content is not valid JSON. Returning raw response."
                    )

                    return {
                        "raw_response": text_response
                    }

            logger.warning("MCP result content does not contain text field")

            return {
                "raw_response": str(first_content)
            }

        logger.warning("MCP result has no content")

        return {}

    except Exception as e:
        logger.error("MCP result parsing failed: %s", str(e))

        return {
            "error": str(e),
            "raw_result": str(result)
        }


async def call_weather(city):
    """
    Calls the Weather MCP Server and returns parsed weather information.
    """

    logger.info("Calling MCP Weather for city: %s", city)

    server_params = StdioServerParameters(
        command="python",
        args=[
            "mcp_servers/weather_server.py"
        ]
    )

    try:
        async with stdio_client(server_params) as (read, write):
            logger.info("Weather MCP stdio client connected")

            async with ClientSession(read, write) as session:
                logger.info("Weather MCP client session created")

                await session.initialize()

                logger.info("Weather MCP session initialized")

                result = await session.call_tool(
                    "get_weather",
                    {
                        "city": city
                    }
                )

                logger.info("Weather MCP tool call completed")

                parsed_result = parse_mcp_result(result)

                logger.info(
                    "Parsed MCP Weather result: %s",
                    parsed_result,
                )

                return parsed_result

    except Exception as e:
        logger.error("MCP Weather call failed: %s", str(e))

        return {
            "weather_source": "MCP Weather Server",
            "current_weather": {
                "success": False,
                "error": str(e)
            },
            "forecast": {
                "success": False,
                "daily_forecast": [],
                "error": str(e)
            },
            "weather_analysis": {
                "travel_advice": (
                    "Weather data could not be fetched due to MCP error."
                )
            }
        }


async def call_budget(days, travelers, user_budget):
    """
    Calls the Budget MCP Server and returns parsed budget information.
    """

    logger.info(
        "Calling MCP Budget with days=%s, travelers=%s, user_budget=%s",
        days,
        travelers,
        user_budget,
    )

    server_params = StdioServerParameters(
        command="python",
        args=[
            "mcp_servers/budget_server.py"
        ]
    )

    try:
        async with stdio_client(server_params) as (read, write):
            logger.info("Budget MCP stdio client connected")

            async with ClientSession(read, write) as session:
                logger.info("Budget MCP client session created")

                await session.initialize()

                logger.info("Budget MCP session initialized")

                result = await session.call_tool(
                    "estimate_budget",
                    {
                        "days": days,
                        "travelers": travelers,
                        "user_budget": user_budget
                    }
                )

                logger.info("Budget MCP tool call completed")

                parsed_result = parse_mcp_result(result)

                logger.info(
                    "Parsed MCP Budget result: %s",
                    parsed_result,
                )

                return parsed_result

    except Exception as e:
        logger.error("MCP Budget call failed: %s", str(e))

        return {
            "user_budget": user_budget,
            "estimated_total": None,
            "within_budget": None,
            "cost_breakdown": {},
            "calculation_explanation": (
                "Budget could not be calculated because the MCP Budget Server call failed."
            ),
            "error": str(e)
        }
