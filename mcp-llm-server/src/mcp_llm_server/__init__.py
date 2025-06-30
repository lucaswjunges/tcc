"""
MCP LLM Server - Um servidor MCP para múltiplos provedores de LLM.

Este módulo fornece um servidor MCP (Model Context Protocol) que oferece acesso
unificado a múltiplos provedores de LLM incluindo Claude AI, OpenAI, OpenRouter e Gemini.
"""

__version__ = "1.0.0"
__author__ = "MCP LLM Team"
__email__ = "team@mcpllm.com"
__description__ = "Multi-LLM MCP Server with OAuth support"

from .server import MCPLLMServer

__all__ = ["MCPLLMServer"]