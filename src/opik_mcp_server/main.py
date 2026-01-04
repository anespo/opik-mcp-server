#!/usr/bin/env python3
"""
Main entry point for Opik MCP Server
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from opik_mcp_server.server import app
from opik_mcp_server.config import settings


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Main entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting Opik MCP Server")
    logger.info(f"AgentCore integration: {'enabled' if settings.agentcore_enabled else 'disabled'}")
    logger.info(f"AWS region: {settings.aws_region}")
    logger.info(f"Opik workspace: {settings.opik_workspace}")
    
    # Always run as MCP server via stdio
    logger.info("Running as MCP server via stdio")
    try:
        # FastMCP handles stdio communication automatically
        app.run()
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        raise


if __name__ == "__main__":
    main()