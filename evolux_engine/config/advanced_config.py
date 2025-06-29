from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings
from pathlib import Path
import os
import yaml
import json
from datetime import datetime
import hashlib

from evolux_engine.utils.logging_utils import get_structured_logger
from evolux_engine.schemas.contracts import LLMProvider

logger = get_structured_logger("advanced_config")

class AdvancedSystemConfig(BaseSettings):
    """
    Sistema de configuração avançado com validação, múltiplas fontes
    e configurações enterprise-grade baseado nos commits históricos 15-25
    """
    
    # === Core System Configuration ===
    max_concurrent_tasks: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Número máximo de tarefas que podem ser executadas simultaneamente"
    )
    
    logging_level: str = Field(
        default="INFO",
        description="Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    project_base_directory: str = Field(
        default="./project_workspaces",
        description="Diretório base para workspaces de projetos"
    )
    
    log_dir: str = Field(
        default="./logs",
        description="Diretório para arquivos de log"
    )
    
    # === LLM Configuration ===
    default_llm_provider: LLMProvider = Field(
        default=LLMProvider.OPENROUTER,
        description="Provedor LLM padrão do sistema"
    )
    
    # OpenRouter Configuration
    OPENROUTER_API_KEY: Optional[str] = Field(
        None, 
        validation_alias='EVOLUX_OPENROUTER_API_KEY',
        description="Chave API do OpenRouter"
    )
    
    default_model_planner: str = Field(
        default="deepseek/deepseek-r1-0528-qwen3-8b:free",
        description="Modelo padrão para tarefas de planejamento"
    )
    
    default_model_executor: str = Field(
        default="deepseek/deepseek-r1-0528-qwen3-8b:free", 
        description="Modelo padrão para execução de tarefas"
    )
    
    default_model_validator: str = Field(
        default="deepseek/deepseek-r1-0528-qwen3-8b:free",
        description="Modelo padrão para validação"
    )
    
    # OpenAI Configuration  
    OPENAI_API_KEY: Optional[str] = Field(
        None,
        validation_alias='EVOLUX_OPENAI_API_KEY',
        description="Chave API do OpenAI"
    )
    
    # Google Configuration
    GOOGLE_API_KEY: Optional[str] = Field(
        None,
        validation_alias='EVOLUX_GOOGLE_API_KEY', 
        description="Chave API do Google/Gemini"
    )
    
    # === HTTP Configuration ===
    http_referer: Optional[str] = Field(
        None,
        description="HTTP Referer para requisições API"
    )
    
    x_title: str = Field(
        default="Evolux Engine",
        description="X-Title header para requisições"
    )
    
    request_timeout: int = Field(
        default=180,
        ge=30,
        le=600,
        description="Timeout para requisições HTTP em segundos"
    )
    
    max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Número máximo de tentativas para requisições"
    )
    
    # === Security Configuration ===
    security_level: str = Field(
        default="strict",
        description="Nível de segurança (strict, permissive, development)"
    )
    
    enable_docker_sandbox: bool = Field(
        default=True,
        description="Habilitar execução em sandbox Docker"
    )
    
    docker_memory_limit_mb: int = Field(
        default=512,
        ge=128,
        le=4096,
        description="Limite de memória para containers Docker em MB"
    )
    
    docker_cpu_limit: float = Field(
        default=0.5,
        ge=0.1,
        le=2.0,
        description="Limite de CPU para containers Docker (núcleos)"
    )
    
    # === Performance Configuration ===
    llm_cache_enabled: bool = Field(
        default=True,
        description="Habilitar cache de respostas LLM"
    )
    
    llm_cache_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="TTL do cache LLM em segundos"
    )
    
    parallel_task_execution: bool = Field(
        default=True,
        description="Executar tarefas independentes em paralelo"
    )
    
    # === Observability Configuration ===
    enable_structured_logging: bool = Field(
        default=True,
        description="Habilitar logging estruturado"
    )
    
    enable_metrics_collection: bool = Field(
        default=True,
        description="Habilitar coleta de métricas"
    )
    
    log_retention_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Dias de retenção de logs"
    )
    
    # === Advanced Features ===
    enable_ai_recovery: bool = Field(
        default=True,
        description="Habilitar recuperação automática com IA"
    )
    
    enable_cost_optimization: bool = Field(
        default=True,
        description="Habilitar otimização automática de custos"
    )
    
    backup_enabled: bool = Field(
        default=True,
        description="Habilitar backup automático de projetos"
    )
    
    backup_interval_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Intervalo de backup em horas"
    )
    
    # === Development Configuration ===
    debug_mode: bool = Field(
        default=False,
        description="Modo debug (logs verbosos, validações extras)"
    )
    
    development_mode: bool = Field(
        default=False,
        description="Modo desenvolvimento (segurança relaxada)"
    )
    
    enable_profiling: bool = Field(
        default=False,
        description="Habilitar profiling de performance"
    )
    
    # Configuração Pydantic v2
    model_config = {
        "env_prefix": "EVOLUX_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "case_sensitive": False,
        "validate_assignment": True,
        "use_enum_values": True
    }
    
    @field_validator('logging_level')
    @classmethod
    def validate_logging_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'logging_level deve ser um de: {valid_levels}')
        return v.upper()
    
    @field_validator('security_level')
    @classmethod
    def validate_security_level(cls, v):
        valid_levels = ['strict', 'permissive', 'development']
        if v.lower() not in valid_levels:
            raise ValueError(f'security_level deve ser um de: {valid_levels}')
        return v.lower()
    
    @model_validator(mode='after')
    def validate_api_keys(self):
        """Valida que pelo menos uma chave API está configurada"""
        api_keys = [
            self.OPENROUTER_API_KEY,
            self.OPENAI_API_KEY, 
            self.GOOGLE_API_KEY
        ]
        
        # Em desenvolvimento, permitir funcionamento sem API keys
        if not any(api_keys) and not self.development_mode:
            raise ValueError(
                'Pelo menos uma chave API deve estar configurada: '
                'EVOLUX_OPENROUTER_API_KEY, EVOLUX_OPENAI_API_KEY, ou EVOLUX_GOOGLE_API_KEY'
            )
        
        return self
    
    @model_validator(mode='after')
    def validate_directories(self):
        """Valida e cria diretórios necessários"""
        for field_name in ['project_base_directory', 'log_dir']:
            dir_path = getattr(self, field_name)
            if dir_path:
                try:
                    Path(dir_path).mkdir(parents=True, exist_ok=True)
                    logger.debug(f"Directory validated/created: {dir_path}")
                except Exception as e:
                    logger.warning(f"Failed to create directory {dir_path}: {e}")
        
        return self
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Obtém chave API para um provedor específico"""
        provider_keys = {
            'openrouter': self.OPENROUTER_API_KEY,
            'openai': self.OPENAI_API_KEY,
            'google': self.GOOGLE_API_KEY
        }
        
        key = provider_keys.get(provider.lower())
        if key:
            logger.debug(f"{provider.title()} API key: {key[:8]}...")
        else:
            logger.warning(f"No API key configured for provider: {provider}")
        
        return key
    
    def get_model_for_task(self, task_type: str) -> str:
        """Obtém modelo apropriado para tipo de tarefa"""
        task_models = {
            'planning': self.default_model_planner,
            'execution': self.default_model_executor,
            'validation': self.default_model_validator
        }
        
        return task_models.get(task_type.lower(), self.default_model_executor)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte configuração para dicionário (sem chaves sensíveis)"""
        config_dict = self.model_dump()
        
        # Mascarar chaves API
        sensitive_keys = ['OPENROUTER_API_KEY', 'OPENAI_API_KEY', 'GOOGLE_API_KEY']
        for key in sensitive_keys:
            if config_dict.get(key):
                config_dict[key] = f"{config_dict[key][:8]}***"
        
        return config_dict
    
    def validate_configuration(self) -> List[str]:
        """Valida configuração e retorna lista de problemas"""
        issues = []
        
        # Verificar diretórios
        for field in ['project_base_directory', 'log_dir']:
            path = getattr(self, field)
            if not os.path.exists(path):
                issues.append(f"Directory does not exist: {field}={path}")
        
        # Verificar configurações de performance
        if self.max_concurrent_tasks > 10 and not self.development_mode:
            issues.append("max_concurrent_tasks > 10 may cause resource exhaustion")
        
        # Verificar configurações de segurança
        if self.security_level == 'development' and not self.development_mode:
            issues.append("security_level=development should only be used with development_mode=True")
        
        # Verificar configurações de Docker
        if self.enable_docker_sandbox and self.docker_memory_limit_mb < 256:
            issues.append("docker_memory_limit_mb < 256 may cause container failures")
        
        return issues

class ConfigurationManager:
    """
    Gerenciador de configuração avançado que combina múltiplas fontes
    baseado nos commits históricos com melhorias modernas
    """
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.config: Optional[AdvancedSystemConfig] = None
        self._config_hash: Optional[str] = None
        self._load_timestamp: Optional[datetime] = None
        
        logger.info("ConfigurationManager initialized")
    
    def load_configuration(self, reload: bool = False) -> AdvancedSystemConfig:
        """Carrega configuração de múltiplas fontes com cache"""
        
        if self.config and not reload:
            return self.config
        
        try:
            # 1. Carregar configuração base do Pydantic (env vars + .env)
            base_config = AdvancedSystemConfig()
            
            # 2. Sobrepor com arquivo YAML se especificado
            if self.config_file and os.path.exists(self.config_file):
                file_config = self._load_yaml_config(self.config_file)
                base_config = self._merge_configs(base_config, file_config)
            
            # 3. Validar configuração final
            validation_issues = base_config.validate_configuration()
            if validation_issues:
                logger.warning("Configuration validation issues found",
                             issues=validation_issues)
            
            # 4. Calcular hash para detectar mudanças
            config_data = base_config.model_dump_json()
            self._config_hash = hashlib.sha256(config_data.encode()).hexdigest()
            self._load_timestamp = datetime.now()
            
            self.config = base_config
            
            logger.info("Configuration loaded successfully",
                       providers_configured=sum(1 for p in ['openrouter', 'openai', 'google'] 
                                               if base_config.get_api_key(p)),
                       config_hash=self._config_hash[:8])
            
            return base_config
            
        except Exception as e:
            logger.error("Failed to load configuration", error=str(e))
            raise
    
    def _load_yaml_config(self, file_path: str) -> Dict[str, Any]:
        """Carrega configuração de arquivo YAML"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                logger.debug("YAML configuration loaded", file=file_path)
                return config_data or {}
        except Exception as e:
            logger.error("Failed to load YAML config", file=file_path, error=str(e))
            return {}
    
    def _merge_configs(self, base: AdvancedSystemConfig, override: Dict[str, Any]) -> AdvancedSystemConfig:
        """Mescla configurações priorizando override"""
        base_dict = base.model_dump()
        
        # Merge recursivo preservando tipos
        for key, value in override.items():
            if key in base_dict:
                base_dict[key] = value
        
        return AdvancedSystemConfig(**base_dict)
    
    def save_configuration(self, file_path: str) -> bool:
        """Salva configuração atual em arquivo YAML"""
        if not self.config:
            logger.error("No configuration loaded to save")
            return False
        
        try:
            config_dict = self.config.to_dict()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, sort_keys=True)
            
            logger.info("Configuration saved", file=file_path)
            return True
            
        except Exception as e:
            logger.error("Failed to save configuration", file=file_path, error=str(e))
            return False
    
    def get_configuration(self) -> AdvancedSystemConfig:
        """Obtém configuração atual (carrega se necessário)"""
        if not self.config:
            return self.load_configuration()
        return self.config
    
    def configuration_changed(self) -> bool:
        """Verifica se configuração mudou desde último carregamento"""
        if not self.config or not self._config_hash:
            return True
        
        try:
            current_config = AdvancedSystemConfig()
            current_data = current_config.model_dump_json()
            current_hash = hashlib.sha256(current_data.encode()).hexdigest()
            
            return current_hash != self._config_hash
            
        except Exception:
            return True
    
    def reload_if_changed(self) -> bool:
        """Recarrega configuração se houve mudanças"""
        if self.configuration_changed():
            self.load_configuration(reload=True)
            logger.info("Configuration reloaded due to changes")
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da configuração"""
        if not self.config:
            return {'loaded': False}
        
        return {
            'loaded': True,
            'load_timestamp': self._load_timestamp.isoformat() if self._load_timestamp else None,
            'config_hash': self._config_hash[:8] if self._config_hash else None,
            'api_keys_configured': [
                provider for provider in ['openrouter', 'openai', 'google']
                if self.config.get_api_key(provider)
            ],
            'security_level': self.config.security_level,
            'debug_mode': self.config.debug_mode,
            'development_mode': self.config.development_mode
        }