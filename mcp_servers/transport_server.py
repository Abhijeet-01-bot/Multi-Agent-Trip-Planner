from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger_config import setup_logger


logger = setup_logger(__name__)

mcp = FastMCP("TransportServer")


@mcp.tool()
def suggest_transport(distance: int):
    """
    MCP tool to suggest transport mode based on distance.
    """

    logger.info("MCP Transport Server called")
    logger.info("Distance received: %s", distance)

    if distance < 100:
        mode = "Car"

    elif distance < 500:
        mode = "Train"

    else:
        mode = "Flight"

    result = {
        "recommended_mode": mode
    }

    logger.info("Recommended transport mode: %s", mode)
    logger.info("Transport result generated successfully: %s", result)

    return result


if __name__ == "__main__":
    logger.info("Starting Transport MCP Server")
    mcp.run()