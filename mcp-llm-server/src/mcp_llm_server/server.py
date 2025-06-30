"""
Servidor MCP principal para múltiplos provedores de LLM.

Este módulo implementa o servidor MCP (Model Context Protocol) que oferece
acesso unificado a múltiplos provedores de LLM através de ferramentas e prompts.
"""

import asyncio
import sys
from typing import List, Dict, Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from .config.simple_settings import settings
from .utils import get_logger, LoggerMixin, init_logging_from_env
from .utils.exceptions import ConfigurationError, MCPLLMException
from .clients import LLMClientFactory
from .auth import OAuthManager
from .tools import (
    ChatTool,
    CompletionTool,
    ModelInfoTool,
)


class MCPLLMServer(LoggerMixin):
    """
    Servidor MCP principal que orquestra todos os componentes.
    
    O servidor gerencia:
    - Autenticação OAuth
    - Clientes para múltiplos provedores LLM
    - Ferramentas MCP para interação com LLMs
    - Configuração e logging
    """
    
    def __init__(self):
        """Inicializa o servidor MCP."""
        # Inicializa logging
        init_logging_from_env()
        self._settings = settings()
        self.logger.info("Initializing MCP LLM Server", version=self._settings.server.version)
        
        # Valida configurações
        try:
            self._settings.validate_all()
            self.logger.info("Configuration validated successfully")
        except Exception as e:
            self.logger.error("Configuration validation failed", error=str(e))
            raise ConfigurationError(f"Configuration validation failed: {e}")
        
        # Inicializa componentes
        self._server = Server(self._settings.server.name)
        self._oauth_manager = OAuthManager()
        self._llm_factory = LLMClientFactory()
        self._tools = self._initialize_tools()
        
        # Registra handlers
        self._register_handlers()
        
        self.logger.info("MCP LLM Server initialized successfully")
    
    def _initialize_tools(self) -> Dict[str, Any]:
        """
        Inicializa todas as ferramentas MCP disponíveis.
        
        Returns:
            Dicionário com ferramentas indexadas por nome
        """
        self.logger.debug("Initializing MCP tools")
        
        tools = {
            "chat": ChatTool(self._llm_factory),
            "completion": CompletionTool(self._llm_factory),
            "model_info": ModelInfoTool(self._llm_factory),
        }
        
        self.logger.info("Tools initialized", tool_count=len(tools), tools=list(tools.keys()))
        return tools
    
    def _register_handlers(self) -> None:
        """Registra todos os handlers MCP."""
        self.logger.debug("Registering MCP handlers")
        
        # Handler para listar ferramentas
        @self._server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """Retorna lista de ferramentas disponíveis."""
            self.logger.debug("Listing available tools")
            
            tools = []
            for tool_name, tool_instance in self._tools.items():
                tool_definition = await tool_instance.get_definition()
                tools.append(tool_definition)
            
            self.logger.info("Tools listed", tool_count=len(tools))
            return tools
        
        # Handler para chamar ferramentas
        @self._server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """
            Executa uma ferramenta específica.
            
            Args:
                name: Nome da ferramenta
                arguments: Argumentos para a ferramenta
                
            Returns:
                Lista de conteúdo de resposta
            """
            self.log_method_call("handle_call_tool", tool_name=name, args=arguments)
            
            if name not in self._tools:
                error_msg = f"Tool '{name}' not found"
                self.logger.error(error_msg, available_tools=list(self._tools.keys()))
                raise ValueError(error_msg)
            
            try:
                tool = self._tools[name]
                result = await tool.execute(arguments)
                
                self.logger.info("Tool executed successfully", tool_name=name)
                return [TextContent(type="text", text=result)]
                
            except Exception as e:
                error_msg = f"Tool execution failed: {str(e)}"
                self.log_error(e, {"tool_name": name, "arguments": arguments})
                raise MCPLLMException(error_msg)
        
        # Handler para listar prompts
        @self._server.list_prompts()
        async def handle_list_prompts():
            """Retorna lista de prompts disponíveis."""
            self.logger.debug("Listing available prompts")
            
            prompts = []
            for tool_name, tool_instance in self._tools.items():
                if hasattr(tool_instance, 'get_prompts'):
                    tool_prompts = await tool_instance.get_prompts()
                    prompts.extend(tool_prompts)
            
            self.logger.info("Prompts listed", prompt_count=len(prompts))
            return prompts
        
        # Handler para obter prompt
        @self._server.get_prompt()
        async def handle_get_prompt(name: str, arguments: Optional[Dict[str, str]] = None):
            """
            Obtém um prompt específico.
            
            Args:
                name: Nome do prompt
                arguments: Argumentos opcionais para o prompt
                
            Returns:
                Conteúdo do prompt
            """
            self.log_method_call("handle_get_prompt", prompt_name=name, args=arguments)
            
            # Procura o prompt em todas as ferramentas
            for tool_name, tool_instance in self._tools.items():
                if hasattr(tool_instance, 'get_prompt'):
                    try:
                        result = await tool_instance.get_prompt(name, arguments or {})
                        if result:
                            self.logger.info("Prompt retrieved successfully", prompt_name=name)
                            return result
                    except Exception:
                        continue  # Tenta próxima ferramenta
            
            error_msg = f"Prompt '{name}' not found"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Handler para listar recursos
        @self._server.list_resources()
        async def handle_list_resources():
            """Retorna lista de recursos disponíveis."""
            self.logger.debug("Listing available resources")
            
            resources = []
            for tool_name, tool_instance in self._tools.items():
                if hasattr(tool_instance, 'get_resources'):
                    tool_resources = await tool_instance.get_resources()
                    resources.extend(tool_resources)
            
            self.logger.info("Resources listed", resource_count=len(resources))
            return resources
        
        # Handler para ler recurso
        @self._server.read_resource()
        async def handle_read_resource(uri: str):
            """
            Lê um recurso específico.
            
            Args:
                uri: URI do recurso
                
            Returns:
                Conteúdo do recurso
            """
            self.log_method_call("handle_read_resource", uri=uri)
            
            # Procura o recurso em todas as ferramentas
            for tool_name, tool_instance in self._tools.items():
                if hasattr(tool_instance, 'read_resource'):
                    try:
                        result = await tool_instance.read_resource(uri)
                        if result:
                            self.logger.info("Resource read successfully", uri=uri)
                            return result
                    except Exception:
                        continue  # Tenta próxima ferramenta
            
            error_msg = f"Resource '{uri}' not found"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.logger.info("MCP handlers registered successfully")
    
    async def run(self) -> None:
        """
        Executa o servidor MCP usando stdio transport.
        
        Este método bloqueia até que o servidor seja encerrado.
        """
        self.logger.info("Starting MCP LLM Server", transport="stdio")
        
        try:
            # Executa servidor com transporte stdio
            async with stdio_server() as (read_stream, write_stream):
                await self._server.run(
                    read_stream,
                    write_stream,
                    self._server.create_initialization_options()
                )
        except KeyboardInterrupt:
            self.logger.info("Server shutdown requested by user")
        except Exception as e:
            self.log_error(e, {"phase": "server_execution"})
            raise
        finally:
            self.logger.info("MCP LLM Server stopped")
    
    async def shutdown(self) -> None:
        """Encerra o servidor graciosamente."""
        self.logger.info("Shutting down MCP LLM Server")
        
        try:
            # Fecha conexões dos clientes LLM
            await self._llm_factory.close_all()
            
            # Cleanup OAuth manager
            if hasattr(self._oauth_manager, 'cleanup'):
                await self._oauth_manager.cleanup()
            
            self.logger.info("Server shutdown completed successfully")
            
        except Exception as e:
            self.log_error(e, {"phase": "server_shutdown"})
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retorna o status atual do servidor.
        
        Returns:
            Status do servidor incluindo configurações e estatísticas
        """
        return {
            "server": {
                "name": self._settings.server.name,
                "version": self._settings.server.version,
                "status": "running"
            },
            "tools": list(self._tools.keys()),
            "providers": self._llm_factory.get_available_providers(),
            "configuration": self._settings.to_dict()
        }


async def main():
    """
    Função principal para executar o servidor MCP.
    
    Esta função é chamada quando o módulo é executado diretamente.
    """
    server = None
    try:
        server = MCPLLMServer()
        await server.run()
    except KeyboardInterrupt:
        print("\nServer interrupted by user", file=sys.stderr)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if server:
            await server.shutdown()


if __name__ == "__main__":
    # Executa o servidor quando chamado diretamente
    asyncio.run(main())