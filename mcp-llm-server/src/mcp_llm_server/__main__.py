"""
Ponto de entrada principal para o MCP LLM Server.

Este módulo permite executar o servidor MCP como um módulo Python
usando `python -m mcp_llm_server`.
"""

import asyncio
import sys
import argparse
from pathlib import Path

from .server import main
from .config import settings
from .utils import init_logging_from_env


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MCP LLM Server - Multi-provider LLM server with OAuth support"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"MCP LLM Server {settings.server.version}"
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # Override settings if command line args provided
    if args.debug:
        settings.server.debug = True
    
    if args.log_level:
        settings.logging.level = args.log_level
    
    # Initialize logging
    init_logging_from_env()
    
    # Run the server
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer interrupted by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)