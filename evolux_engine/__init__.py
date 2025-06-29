"""
Evolux Engine - AI-Powered Software Development Orchestration Platform

Enterprise-grade AI orchestration system for autonomous software development
with advanced configuration, security, observability, and multi-provider LLM support.
"""

__version__ = "2.0.0"
__author__ = "Evolux Engine Team"

# Core exports
from .config.advanced_config import AdvancedSystemConfig, ConfigurationManager
from .services.enterprise_observability import EnterpriseObservabilityService
from .services.advanced_context_manager import AdvancedContextManager
from .security.security_gateway import SecurityGateway
from .llms.model_router import ModelRouter
from .llms.llm_factory import LLMFactory
from .prompts.prompt_engine import PromptEngine
from .core.project_scaffolding import IntelligentProjectScaffolding

__all__ = [
    "AdvancedSystemConfig",
    "ConfigurationManager", 
    "EnterpriseObservabilityService",
    "AdvancedContextManager",
    "SecurityGateway",
    "ModelRouter",
    "LLMFactory",
    "PromptEngine",
    "IntelligentProjectScaffolding"
]