"""MCP server command — start the aethersy-research MCP server for agent integration."""

from __future__ import annotations

import sys


def mcp() -> None:
    """Start the MCP server (stdio transport) for Claude Desktop, Cursor, etc.

    Requires: pip install aethersy-research[mcp]
    """
    try:
        from aethersy_research.mcp.server import server
    except ImportError:
        print("MCP server requires: pip install aethersy-research[mcp]", file=sys.stderr)
        sys.exit(1)

    server.run()
