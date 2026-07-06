from mcp.server.fastmcp import FastMCP
from pipeline.retriever import retrieve_documents
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from utils.logger_config import setup_logger


logger = setup_logger(__name__)

mcp = FastMCP("RAGServer")


@mcp.tool()
def destination_knowledge(query: str):
    """
    MCP tool to retrieve destination-related knowledge using the RAG retriever.
    """

    logger.info("MCP RAG Server called")
    logger.info("RAG query received: %s", query)

    try:
        docs = retrieve_documents(query)

        logger.info("Documents retrieved successfully")
        logger.info("Retrieved documents: %s", docs)

        return str(docs)

    except Exception as e:
        logger.error("RAG retrieval failed: %s", str(e))

        return str(
            {
                "error": str(e),
                "message": "RAG retrieval failed inside MCP RAG Server."
            }
        )


if __name__ == "__main__":
    logger.info("Starting RAG MCP Server")
    mcp.run()