#!/usr/bin/env python3
"""
Main entry point for the beauchbot MCP server.

This server provides various tools and utilities that can be used by
MCP-compatible clients like Claude Desktop.
"""

import logging

from mcp_server.server import beauchbot_mcp
# Import tools and resources to register them
from mcp_server import tools  # noqa: F401
from mcp_server import resources  # noqa: F401

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


logger.info("Starting beauchbot MCP server...")
app = beauchbot_mcp.streamable_http_app()