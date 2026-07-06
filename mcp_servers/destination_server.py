from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from utils.logger_config import setup_logger


logger = setup_logger(__name__)

mcp = FastMCP("DestinationServer")


@mcp.tool()
def get_destination_context(query: str):
    """
    MCP tool to return destination-related context.
    """

    logger.info("MCP Destination Server called")
    logger.info("Destination context query received: %s", query)

    result = {
        "context": f"Retrieved destination information for: {query}"
    }

    logger.info("Destination context generated successfully: %s", result)

    return result


if __name__ == "__main__":
    logger.info("Starting Destination MCP Server")
    mcp.run()