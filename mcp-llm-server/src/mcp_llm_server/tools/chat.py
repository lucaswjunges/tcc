"""
Ferramenta de chat para o MCP LLM Server.

Esta ferramenta permite aos clientes executar conversas de chat
com qualquer provedor LLM suportado através de uma interface unificada.
"""

import json
from typing import Dict, Any, List, Optional

from mcp.types import Tool

from ..clients import LLMClientFactory, ChatRequest, ChatMessage, MessageRole
from ..utils import LoggerMixin
from ..utils.exceptions import ValidationError, LLMProviderError


class ChatTool(LoggerMixin):
    """
    Ferramenta MCP para chat com LLMs.
    
    Permite executar conversas de chat com qualquer provedor LLM
    suportado, incluindo streaming opcional.
    """
    
    def __init__(self, llm_factory: LLMClientFactory):
        """
        Inicializa a ferramenta de chat.
        
        Args:
            llm_factory: Factory para criação de clientes LLM
        """
        self.llm_factory = llm_factory
        self.logger.info("Chat tool initialized")
    
    async def get_definition(self) -> Tool:
        """
        Retorna a definição da ferramenta MCP.
        
        Returns:
            Definição da ferramenta
        """
        return Tool(
            name="chat",
            description="Execute chat conversations with LLM providers",
            inputSchema={
                "type": "object",
                "properties": {
                    "messages": {
                        "type": "array",
                        "description": "Array of chat messages",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {
                                    "type": "string",
                                    "enum": ["system", "user", "assistant"],
                                    "description": "Role of the message sender"
                                },
                                "content": {
                                    "type": "string",
                                    "description": "Content of the message"
                                }
                            },
                            "required": ["role", "content"]
                        }
                    },
                    "provider": {
                        "type": "string",
                        "description": "LLM provider to use (openai, claude, openrouter, gemini)",
                        "enum": ["openai", "claude", "openrouter", "gemini"]
                    },
                    "model": {
                        "type": "string",
                        "description": "Specific model to use (optional, uses provider default if not specified)"
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Maximum tokens in response",
                        "minimum": 1,
                        "maximum": 32000
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Temperature for response generation",
                        "minimum": 0.0,
                        "maximum": 2.0
                    },
                    "stream": {
                        "type": "boolean",
                        "description": "Whether to stream the response",
                        "default": False
                    }
                },
                "required": ["messages"]
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """
        Executa a ferramenta de chat.
        
        Args:
            arguments: Argumentos da ferramenta
            
        Returns:
            Resultado da conversa de chat
            
        Raises:
            ValidationError: Se os argumentos forem inválidos
            LLMProviderError: Se houver erro na execução
        """
        self.log_method_call("execute", args=arguments)
        
        try:
            # Valida argumentos
            messages_data = arguments.get("messages", [])
            if not messages_data:
                raise ValidationError("At least one message is required")
            
            provider = arguments.get("provider")
            model = arguments.get("model")
            max_tokens = arguments.get("max_tokens")
            temperature = arguments.get("temperature")
            stream = arguments.get("stream", False)
            
            # Converte mensagens para formato interno
            messages = []
            for msg_data in messages_data:
                try:
                    role = MessageRole(msg_data["role"])
                    content = msg_data["content"]
                    messages.append(ChatMessage(role=role, content=content))
                except (KeyError, ValueError) as e:
                    raise ValidationError(f"Invalid message format: {e}")
            
            # Determina provedor a usar
            if provider:
                if provider not in self.llm_factory.get_available_providers():
                    raise ValidationError(f"Provider '{provider}' not available")
                client = await self.llm_factory.get_client(provider)
            else:
                client = await self.llm_factory.get_default_client()
                provider = client.provider_name
            
            # Cria requisição de chat
            chat_request = ChatRequest(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream
            )
            
            self.logger.info(
                "Executing chat request",
                provider=provider,
                model=model or "default",
                message_count=len(messages),
                stream=stream
            )
            
            # Executa chat
            if stream:
                # Executa com streaming
                response_parts = []
                async for chunk in client.stream_chat(chat_request):
                    response_parts.append(chunk)
                
                response_content = "".join(response_parts)
                
                result = {
                    "provider": provider,
                    "model": model or client._get_default_model(),
                    "response": response_content,
                    "stream": True,
                    "chunk_count": len(response_parts)
                }
            else:
                # Executa sem streaming
                response = await client.chat(chat_request)
                
                result = {
                    "provider": provider,
                    "model": response.model,
                    "response": response.content,
                    "usage": response.usage,
                    "metadata": response.metadata,
                    "stream": False
                }
            
            self.logger.info(
                "Chat request completed successfully",
                provider=provider,
                response_length=len(result["response"])
            )
            
            return json.dumps(result, indent=2)
            
        except ValidationError:
            raise
        except Exception as e:
            self.log_error(e)
            raise LLMProviderError(
                provider or "unknown",
                f"Chat execution failed: {e}"
            )
    
    async def get_prompts(self) -> List[Dict[str, Any]]:
        """
        Retorna prompts pré-definidos para chat.
        
        Returns:
            Lista de prompts disponíveis
        """
        return [
            {
                "name": "simple_chat",
                "description": "Simple single-message chat",
                "arguments": {
                    "message": {
                        "type": "string",
                        "description": "Message to send to the LLM"
                    },
                    "provider": {
                        "type": "string",
                        "description": "LLM provider to use",
                        "enum": ["openai", "claude", "openrouter", "gemini"]
                    }
                }
            },
            {
                "name": "conversation",
                "description": "Multi-turn conversation",
                "arguments": {
                    "system_prompt": {
                        "type": "string", 
                        "description": "System prompt to set context"
                    },
                    "user_message": {
                        "type": "string",
                        "description": "User message"
                    },
                    "provider": {
                        "type": "string",
                        "description": "LLM provider to use",
                        "enum": ["openai", "claude", "openrouter", "gemini"]
                    }
                }
            }
        ]
    
    async def get_prompt(self, name: str, arguments: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Gera um prompt específico.
        
        Args:
            name: Nome do prompt
            arguments: Argumentos para o prompt
            
        Returns:
            Prompt gerado ou None se não encontrado
        """
        if name == "simple_chat":
            message = arguments.get("message", "")
            provider = arguments.get("provider", "")
            
            if not message:
                raise ValidationError("Message is required for simple_chat prompt")
            
            return {
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                "provider": provider if provider else None
            }
        
        elif name == "conversation":
            system_prompt = arguments.get("system_prompt", "")
            user_message = arguments.get("user_message", "")
            provider = arguments.get("provider", "")
            
            if not user_message:
                raise ValidationError("User message is required for conversation prompt")
            
            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user", 
                "content": user_message
            })
            
            return {
                "messages": messages,
                "provider": provider if provider else None
            }
        
        return None