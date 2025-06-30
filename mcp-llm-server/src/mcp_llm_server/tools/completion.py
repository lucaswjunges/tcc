"""
Ferramenta de completion para o MCP LLM Server.

Esta ferramenta permite aos clientes executar text completions
com qualquer provedor LLM suportado através de uma interface unificada.
"""

import json
from typing import Dict, Any, List, Optional

from mcp.types import Tool

from ..clients import LLMClientFactory, CompletionRequest
from ..utils import LoggerMixin
from ..utils.exceptions import ValidationError, LLMProviderError


class CompletionTool(LoggerMixin):
    """
    Ferramenta MCP para text completion com LLMs.
    
    Permite executar text completions com qualquer provedor LLM
    suportado, incluindo streaming opcional.
    """
    
    def __init__(self, llm_factory: LLMClientFactory):
        """
        Inicializa a ferramenta de completion.
        
        Args:
            llm_factory: Factory para criação de clientes LLM
        """
        self.llm_factory = llm_factory
        self.logger.info("Completion tool initialized")
    
    async def get_definition(self) -> Tool:
        """
        Retorna a definição da ferramenta MCP.
        
        Returns:
            Definição da ferramenta
        """
        return Tool(
            name="completion",
            description="Execute text completions with LLM providers",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Text prompt for completion",
                        "minLength": 1
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
                    },
                    "stop": {
                        "type": "array",
                        "description": "Stop sequences for completion",
                        "items": {
                            "type": "string"
                        },
                        "maxItems": 4
                    }
                },
                "required": ["prompt"]
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """
        Executa a ferramenta de completion.
        
        Args:
            arguments: Argumentos da ferramenta
            
        Returns:
            Resultado do text completion
            
        Raises:
            ValidationError: Se os argumentos forem inválidos
            LLMProviderError: Se houver erro na execução
        """
        self.log_method_call("execute", args=arguments)
        
        try:
            # Valida argumentos
            prompt = arguments.get("prompt", "").strip()
            if not prompt:
                raise ValidationError("Prompt is required and cannot be empty")
            
            provider = arguments.get("provider")
            model = arguments.get("model")
            max_tokens = arguments.get("max_tokens")
            temperature = arguments.get("temperature")
            stream = arguments.get("stream", False)
            stop = arguments.get("stop")
            
            # Determina provedor a usar
            if provider:
                if provider not in self.llm_factory.get_available_providers():
                    raise ValidationError(f"Provider '{provider}' not available")
                client = await self.llm_factory.get_client(provider)
            else:
                client = await self.llm_factory.get_default_client()
                provider = client.provider_name
            
            # Cria requisição de completion
            completion_request = CompletionRequest(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream,
                metadata={"stop": stop} if stop else None
            )
            
            self.logger.info(
                "Executing completion request",
                provider=provider,
                model=model or "default",
                prompt_length=len(prompt),
                stream=stream
            )
            
            # Executa completion
            if stream:
                # Executa com streaming
                response_parts = []
                async for chunk in client.stream_completion(completion_request):
                    response_parts.append(chunk)
                
                response_content = "".join(response_parts)
                
                result = {
                    "provider": provider,
                    "model": model or client._get_default_model(),
                    "prompt": prompt,
                    "completion": response_content,
                    "stream": True,
                    "chunk_count": len(response_parts)
                }
            else:
                # Executa sem streaming
                response = await client.completion(completion_request)
                
                result = {
                    "provider": provider,
                    "model": response.model,
                    "prompt": prompt,
                    "completion": response.content,
                    "usage": response.usage,
                    "metadata": response.metadata,
                    "stream": False
                }
            
            self.logger.info(
                "Completion request completed successfully",
                provider=provider,
                completion_length=len(result["completion"])
            )
            
            return json.dumps(result, indent=2)
            
        except ValidationError:
            raise
        except Exception as e:
            self.log_error(e)
            raise LLMProviderError(
                provider or "unknown",
                f"Completion execution failed: {e}"
            )
    
    async def get_prompts(self) -> List[Dict[str, Any]]:
        """
        Retorna prompts pré-definidos para completion.
        
        Returns:
            Lista de prompts disponíveis
        """
        return [
            {
                "name": "code_completion",
                "description": "Complete code snippets",
                "arguments": {
                    "code": {
                        "type": "string",
                        "description": "Partial code to complete"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language",
                        "enum": ["python", "javascript", "typescript", "java", "cpp", "rust", "go"]
                    },
                    "provider": {
                        "type": "string",
                        "description": "LLM provider to use",
                        "enum": ["openai", "claude", "openrouter", "gemini"]
                    }
                }
            },
            {
                "name": "text_generation",
                "description": "Generate text from a prompt",
                "arguments": {
                    "topic": {
                        "type": "string",
                        "description": "Topic or theme for text generation"
                    },
                    "style": {
                        "type": "string",
                        "description": "Writing style",
                        "enum": ["formal", "casual", "creative", "technical", "academic"]
                    },
                    "length": {
                        "type": "string",
                        "description": "Desired length",
                        "enum": ["short", "medium", "long"]
                    },
                    "provider": {
                        "type": "string",
                        "description": "LLM provider to use",
                        "enum": ["openai", "claude", "openrouter", "gemini"]
                    }
                }
            },
            {
                "name": "summarization",
                "description": "Summarize text content",
                "arguments": {
                    "text": {
                        "type": "string",
                        "description": "Text to summarize"
                    },
                    "length": {
                        "type": "string",
                        "description": "Summary length",
                        "enum": ["brief", "detailed", "executive"]
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
        if name == "code_completion":
            code = arguments.get("code", "")
            language = arguments.get("language", "python")
            provider = arguments.get("provider", "")
            
            if not code:
                raise ValidationError("Code is required for code_completion prompt")
            
            prompt = f"Complete the following {language} code:\n\n```{language}\n{code}\n```\n\nCompletion:"
            
            return {
                "prompt": prompt,
                "provider": provider if provider else None,
                "max_tokens": 1000,
                "temperature": 0.1,
                "stop": ["```", "\n\n"]
            }
        
        elif name == "text_generation":
            topic = arguments.get("topic", "")
            style = arguments.get("style", "casual")
            length = arguments.get("length", "medium")
            provider = arguments.get("provider", "")
            
            if not topic:
                raise ValidationError("Topic is required for text_generation prompt")
            
            length_instructions = {
                "short": "Write a brief paragraph (50-100 words)",
                "medium": "Write 2-3 paragraphs (150-300 words)",
                "long": "Write a detailed piece (400-600 words)"
            }
            
            style_instructions = {
                "formal": "Use formal, professional language",
                "casual": "Use conversational, friendly tone",
                "creative": "Use creative, engaging language with vivid descriptions",
                "technical": "Use precise, technical language appropriate for experts",
                "academic": "Use scholarly, analytical language with proper citations style"
            }
            
            prompt = f"{length_instructions.get(length, length_instructions['medium'])} about {topic}. {style_instructions.get(style, style_instructions['casual'])}.\n\nText:"
            
            max_tokens_map = {"short": 200, "medium": 500, "long": 800}
            
            return {
                "prompt": prompt,
                "provider": provider if provider else None,
                "max_tokens": max_tokens_map.get(length, 500),
                "temperature": 0.7
            }
        
        elif name == "summarization":
            text = arguments.get("text", "")
            length = arguments.get("length", "brief")
            provider = arguments.get("provider", "")
            
            if not text:
                raise ValidationError("Text is required for summarization prompt")
            
            length_instructions = {
                "brief": "Provide a brief summary in 1-2 sentences",
                "detailed": "Provide a detailed summary in 1-2 paragraphs",
                "executive": "Provide an executive summary with key points and conclusions"
            }
            
            prompt = f"{length_instructions.get(length, length_instructions['brief'])} of the following text:\n\n{text}\n\nSummary:"
            
            max_tokens_map = {"brief": 100, "detailed": 300, "executive": 400}
            
            return {
                "prompt": prompt,
                "provider": provider if provider else None,
                "max_tokens": max_tokens_map.get(length, 200),
                "temperature": 0.3
            }
        
        return None