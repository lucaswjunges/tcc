import re
import asyncio
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import shlex
import os

from evolux_engine.utils.logging_utils import get_structured_logger

logger = get_structured_logger("security_gateway")

class SecurityLevel(Enum):
    STRICT = "strict"
    PERMISSIVE = "permissive"
    DEVELOPMENT = "development"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityValidationResult:
    """Resultado da validação de segurança de um comando"""
    is_safe: bool
    risk_level: RiskLevel
    blocked_reason: Optional[str] = None
    sanitized_command: Optional[str] = None
    security_warnings: List[str] = None
    
    def __post_init__(self):
        if self.security_warnings is None:
            self.security_warnings = []

class SecurityGateway:
    """
    Gateway de segurança que implementa defense-in-depth para validação de comandos.
    Segue a especificação da Seção 6 do README.md.
    """
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.STRICT):
        self.security_level = security_level
        self.command_whitelist = self._get_default_whitelist()
        self.danger_patterns = self._get_danger_patterns()
        self.validation_count = 0
        self.blocked_count = 0
        
        logger.info("SecurityGateway initialized", 
                   security_level=security_level.value,
                   whitelist_size=len(self.command_whitelist))
    
    def _get_default_whitelist(self) -> Set[str]:
        """Comandos permitidos por padrão (whitelist)"""
        base_commands = {
            # Linguagens de programação
            'python', 'python3', 'pip', 'pip3',
            'node', 'npm', 'npx', 'yarn',
            'java', 'javac', 'mvn', 'gradle',
            'go', 'cargo', 'rustc',
            
            # Ferramentas de desenvolvimento
            'git', 'docker', 'docker-compose',
            'make', 'cmake', 'gcc', 'g++',
            'flask', 'django-admin',
            
            # Ferramentas de sistema (seguras)
            'ls', 'cat', 'head', 'tail', 'grep',
            'find', 'which', 'echo', 'pwd',
            'mkdir', 'touch', 'cp', 'mv',
            'chmod', 'chown',  # Limitados
            
            # Ferramentas de texto
            'sed', 'awk', 'sort', 'uniq', 'wc',
            'curl', 'wget',  # Para downloads
            
            # Ferramentas de teste
            'pytest', 'unittest', 'jest', 'mocha',
            'phpunit', 'cargo test', 'go test'
        }
        
        if self.security_level == SecurityLevel.DEVELOPMENT:
            # Adiciona comandos extras para desenvolvimento
            base_commands.update({
                'vim', 'nano', 'code', 'emacs',
                'ps', 'top', 'htop', 'kill', 'killall',
                'tar', 'zip', 'unzip', 'gzip', 'gunzip'
            })
        
        return base_commands
    
    def _get_danger_patterns(self) -> List[Dict[str, Any]]:
        """Padrões perigosos que devem ser bloqueados"""
        return [
            {
                'pattern': r'rm\s+.*-rf?\s*/',
                'risk': RiskLevel.CRITICAL,
                'reason': 'Tentativa de deletar sistema de arquivos raiz'
            },
            {
                'pattern': r'sudo\s+',
                'risk': RiskLevel.CRITICAL,
                'reason': 'Tentativa de execução com privilégios elevados'
            },
            {
                'pattern': r'chmod\s+.*777',
                'risk': RiskLevel.HIGH,
                'reason': 'Tentativa de dar permissões totais (777)'
            },
            {
                'pattern': r'mkfs\.|format\s+',
                'risk': RiskLevel.CRITICAL,
                'reason': 'Tentativa de formatar sistema de arquivos'
            },
            {
                'pattern': r'/dev/(sd[a-z]|hd[a-z]|nvme)',
                'risk': RiskLevel.CRITICAL,
                'reason': 'Acesso direto a dispositivos de armazenamento'
            },
            {
                'pattern': r'dd\s+.*of=/dev/',
                'risk': RiskLevel.CRITICAL,
                'reason': 'Tentativa de escrita direta em dispositivo'
            },
            {
                'pattern': r'>(>?)\s*/dev/(null|zero|random)',
                'risk': RiskLevel.MEDIUM,
                'reason': 'Redirecionamento para dispositivos especiais'
            },
            {
                'pattern': r'eval\s+.*\$',
                'risk': RiskLevel.HIGH,
                'reason': 'Execução dinâmica de código perigosa'
            },
            {
                'pattern': r'curl.*\|\s*(bash|sh|python)',
                'risk': RiskLevel.HIGH,
                'reason': 'Download e execução de script remoto'
            },
            {
                'pattern': r'nc\s+.*-[el]',
                'risk': RiskLevel.HIGH,
                'reason': 'Tentativa de criação de backdoor com netcat'
            },
            {
                'pattern': r'(^|\s+):(){ :|:& };:',
                'risk': RiskLevel.CRITICAL,
                'reason': 'Fork bomb detectada'
            },
            {
                'pattern': r'/etc/(passwd|shadow|sudoers)',
                'risk': RiskLevel.CRITICAL,
                'reason': 'Tentativa de acesso a arquivos críticos do sistema'
            }
        ]
    
    def _sanitize_command(self, command: str) -> str:
        """Remove caracteres de controle e normaliza comando"""
        # Remove caracteres de controle perigosos
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', command)
        
        # Remove múltiplos espaços
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        # Remove comentários inline perigosos
        sanitized = re.sub(r'#.*$', '', sanitized).strip()
        
        return sanitized
    
    def _check_whitelist(self, command: str) -> bool:
        """Verifica se o comando base está na whitelist com validação aprimorada"""
        try:
            # Normalizar comando removendo caracteres de escape e encoding
            normalized_command = self._normalize_command(command)
            
            # Parse do comando para extrair o executável base
            parts = shlex.split(normalized_command)
            if not parts:
                return False
            
            base_command = parts[0]
            
            # Validar se não há tentativas de path traversal
            if '..' in base_command or base_command.startswith('/'):
                logger.warning("Path traversal attempt detected", command=command)
                return False
            
            # Remove path se presente (depois de validar)
            if '/' in base_command:
                base_command = os.path.basename(base_command)
            
            # Verificar se o comando base não contém caracteres suspeitos
            if not re.match(r'^[a-zA-Z0-9_.-]+$', base_command):
                logger.warning("Invalid characters in command", command=base_command)
                return False
            
            return base_command in self.command_whitelist
            
        except ValueError:
            # Erro de parsing (aspas não fechadas, etc)
            logger.warning("Command parsing failed", command=command)
            return False
    
    def _normalize_command(self, command: str) -> str:
        """Normaliza comando para prevenir bypass via encoding"""
        # Remove null bytes
        command = command.replace('\x00', '')
        
        # Decode possíveis encodings
        try:
            # Tenta decodificar hex encoding
            if '\\x' in command:
                command = bytes(command, 'utf-8').decode('unicode_escape')
        except:
            pass
        
        # Remove caracteres de controle
        command = ''.join(char for char in command if ord(char) >= 32 or char in '\t\n')
        
        return command.strip()
    
    def _check_danger_patterns(self, command: str) -> Optional[Dict[str, Any]]:
        """Verifica padrões perigosos no comando"""
        for pattern_info in self.danger_patterns:
            if re.search(pattern_info['pattern'], command, re.IGNORECASE):
                return pattern_info
        return None
    
    def _analyze_command_structure(self, command: str) -> List[str]:
        """Analisa estrutura do comando para riscos adicionais"""
        warnings = []
        
        # Pipes perigosos
        if '|' in command and any(danger in command for danger in ['rm', 'dd', 'mkfs']):
            warnings.append("Pipe com comando potencialmente destrutivo")
        
        # Redirecionamentos perigosos
        if '>>' in command and '/etc/' in command:
            warnings.append("Tentativa de append em arquivo de sistema")
        
        # Execução em background suspeita
        if '&' in command and ('nc' in command or 'ncat' in command):
            warnings.append("Execução em background de ferramenta de rede")
        
        # Múltiplos comandos
        if ';' in command or '&&' in command or '||' in command:
            warnings.append("Múltiplos comandos em uma linha")
        
        # Wildcards perigosos
        if re.search(r'/\*', command):
            warnings.append("Wildcard em path absoluto")
        
        return warnings
    
    async def validate_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> SecurityValidationResult:
        """
        Valida um comando através da pipeline de segurança completa.
        
        Args:
            command: Comando a ser validado
            context: Contexto adicional (working_directory, task_info, etc.)
            
        Returns:
            SecurityValidationResult com resultado da validação
        """
        self.validation_count += 1
        
        logger.debug("Validating command", 
                    command=command[:100], 
                    validation_count=self.validation_count)
        
        # 1. Sanitização
        sanitized = self._sanitize_command(command)
        if not sanitized:
            self.blocked_count += 1
            return SecurityValidationResult(
                is_safe=False,
                risk_level=RiskLevel.HIGH,
                blocked_reason="Comando vazio após sanitização"
            )
        
        # 2. Verificação de padrões perigosos (prioritária)
        danger_match = self._check_danger_patterns(sanitized)
        if danger_match:
            self.blocked_count += 1
            logger.warning("Dangerous pattern detected",
                          pattern=danger_match['pattern'],
                          reason=danger_match['reason'],
                          command=sanitized[:50])
            
            return SecurityValidationResult(
                is_safe=False,
                risk_level=danger_match['risk'],
                blocked_reason=danger_match['reason'],
                sanitized_command=sanitized
            )
        
        # 3. Verificação de whitelist
        if not self._check_whitelist(sanitized):
            # Em modo permissivo, apenas avisa
            if self.security_level == SecurityLevel.PERMISSIVE:
                logger.warning("Command not in whitelist (permissive mode)",
                              command=sanitized[:50])
                warnings = ["Comando não está na whitelist (modo permissivo)"]
            else:
                self.blocked_count += 1
                logger.warning("Command not in whitelist (blocked)",
                              command=sanitized[:50])
                return SecurityValidationResult(
                    is_safe=False,
                    risk_level=RiskLevel.MEDIUM,
                    blocked_reason="Comando não está na lista de comandos permitidos",
                    sanitized_command=sanitized
                )
        else:
            warnings = []
        
        # 4. Análise estrutural
        structural_warnings = self._analyze_command_structure(sanitized)
        warnings.extend(structural_warnings)
        
        # 5. Determinar nível de risco final
        risk_level = RiskLevel.LOW
        if warnings:
            risk_level = RiskLevel.MEDIUM if len(warnings) > 2 else RiskLevel.LOW
        
        logger.info("Command validated successfully",
                   command=sanitized[:50],
                   risk_level=risk_level.value,
                   warnings_count=len(warnings))
        
        return SecurityValidationResult(
            is_safe=True,
            risk_level=risk_level,
            sanitized_command=sanitized,
            security_warnings=warnings
        )
    
    def add_whitelist_command(self, command: str) -> None:
        """Adiciona comando à whitelist"""
        self.command_whitelist.add(command)
        logger.info("Command added to whitelist", command=command)
    
    def remove_whitelist_command(self, command: str) -> None:
        """Remove comando da whitelist"""
        self.command_whitelist.discard(command)
        logger.info("Command removed from whitelist", command=command)
    
    async def is_command_safe(
        self, 
        command: str, 
        working_directory: Optional[str] = None
    ) -> bool:
        """
        Interface simplificada para verificar se um comando é seguro.
        Usado pelo TaskExecutorAgent.
        """
        context = {'working_directory': working_directory} if working_directory else None
        result = await self.validate_command(command, context)
        return result.is_safe
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de segurança"""
        block_rate = (self.blocked_count / self.validation_count * 100) if self.validation_count > 0 else 0
        
        return {
            'total_validations': self.validation_count,
            'blocked_commands': self.blocked_count,
            'block_rate_percent': round(block_rate, 2),
            'security_level': self.security_level.value,
            'whitelist_size': len(self.command_whitelist)
        }