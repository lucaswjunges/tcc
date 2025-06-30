"""
Gerenciador de tokens JWT para autenticação OAuth 2.0.

Este módulo implementa criação, validação, refresh e revogação de tokens JWT
para o sistema de autenticação do MCP LLM Server.
"""

import time
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

import jwt
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt

from ..config import settings
from ..utils import LoggerMixin, get_logger
from ..utils.exceptions import AuthenticationError, AuthorizationError


@dataclass
class TokenInfo:
    """Informações sobre um token JWT."""
    token: str
    token_type: str
    expires_at: datetime
    scope: List[str]
    user_id: Optional[str] = None
    client_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TokenManager(LoggerMixin):
    """
    Gerenciador de tokens JWT para autenticação OAuth 2.0.
    
    Implementa criação, validação, refresh e revogação de tokens
    seguindo as especificações OAuth 2.0 e JWT.
    """
    
    def __init__(self):
        """Inicializa o gerenciador de tokens."""
        self.secret_key = settings.security.secret_key
        self.token_expiry_hours = settings.security.token_expiry_hours
        self.algorithm = "HS256"
        
        # Cache de tokens revogados (em produção, usar Redis/database)
        self._revoked_tokens: set = set()
        
        # Cache de refresh tokens
        self._refresh_tokens: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info(
            "Token manager initialized",
            algorithm=self.algorithm,
            expiry_hours=self.token_expiry_hours
        )
    
    def create_access_token(
        self,
        user_id: str,
        client_id: str,
        scopes: List[str],
        expires_delta: Optional[timedelta] = None
    ) -> TokenInfo:
        """
        Cria um token de acesso JWT.
        
        Args:
            user_id: ID do usuário
            client_id: ID do cliente OAuth
            scopes: Lista de escopos autorizados
            expires_delta: Tempo de expiração customizado
            
        Returns:
            Informações do token criado
        """
        if expires_delta is None:
            expires_delta = timedelta(hours=self.token_expiry_hours)
        
        now = datetime.utcnow()
        expires_at = now + expires_delta
        
        # Claims do JWT
        payload = {
            "sub": user_id,  # Subject (user ID)
            "client_id": client_id,
            "scope": " ".join(scopes),
            "iat": int(now.timestamp()),  # Issued at
            "exp": int(expires_at.timestamp()),  # Expires at
            "jti": secrets.token_urlsafe(16),  # JWT ID
            "token_type": "access_token"
        }
        
        # Cria o token
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        self.log_method_call(
            "create_access_token",
            user_id=user_id,
            client_id=client_id,
            scopes=scopes,
            expires_at=expires_at.isoformat()
        )
        
        return TokenInfo(
            token=token,
            token_type="Bearer",
            expires_at=expires_at,
            scope=scopes,
            user_id=user_id,
            client_id=client_id,
            metadata={"jti": payload["jti"]}
        )
    
    def create_refresh_token(
        self,
        user_id: str,
        client_id: str,
        scopes: List[str]
    ) -> str:
        """
        Cria um refresh token.
        
        Args:
            user_id: ID do usuário
            client_id: ID do cliente OAuth
            scopes: Lista de escopos autorizados
            
        Returns:
            Refresh token
        """
        refresh_token = secrets.token_urlsafe(32)
        
        # Armazena informações do refresh token
        self._refresh_tokens[refresh_token] = {
            "user_id": user_id,
            "client_id": client_id,
            "scopes": scopes,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=30)  # Refresh tokens duram 30 dias
        }
        
        self.logger.info(
            "Refresh token created",
            user_id=user_id,
            client_id=client_id,
            token_prefix=refresh_token[:8] + "..."
        )
        
        return refresh_token
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Valida um token JWT.
        
        Args:
            token: Token JWT a ser validado
            
        Returns:
            Payload do token decodificado
            
        Raises:
            AuthenticationError: Se o token for inválido
        """
        try:
            # Remove prefixo "Bearer " se presente
            if token.startswith("Bearer "):
                token = token[7:]
            
            # Decodifica o token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Verifica se o token foi revogado
            jti = payload.get("jti")
            if jti and jti in self._revoked_tokens:
                raise AuthenticationError("Token has been revoked")
            
            # Verifica expiração
            exp = payload.get("exp")
            if exp and datetime.utcnow().timestamp() > exp:
                raise AuthenticationError("Token has expired")
            
            self.logger.debug(
                "Token validated successfully",
                user_id=payload.get("sub"),
                client_id=payload.get("client_id"),
                jti=jti
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {e}")
        except Exception as e:
            self.log_error(e)
            raise AuthenticationError(f"Token validation failed: {e}")
    
    def refresh_access_token(self, refresh_token: str) -> TokenInfo:
        """
        Cria um novo access token usando um refresh token.
        
        Args:
            refresh_token: Refresh token válido
            
        Returns:
            Novo access token
            
        Raises:
            AuthenticationError: Se o refresh token for inválido
        """
        if refresh_token not in self._refresh_tokens:
            raise AuthenticationError("Invalid refresh token")
        
        token_data = self._refresh_tokens[refresh_token]
        
        # Verifica se o refresh token expirou
        if datetime.utcnow() > token_data["expires_at"]:
            del self._refresh_tokens[refresh_token]
            raise AuthenticationError("Refresh token has expired")
        
        # Cria novo access token
        new_token = self.create_access_token(
            user_id=token_data["user_id"],
            client_id=token_data["client_id"],
            scopes=token_data["scopes"]
        )
        
        self.logger.info(
            "Access token refreshed",
            user_id=token_data["user_id"],
            client_id=token_data["client_id"]
        )
        
        return new_token
    
    def revoke_token(self, token: str) -> None:
        """
        Revoga um token JWT.
        
        Args:
            token: Token a ser revogado
        """
        try:
            payload = self.validate_token(token)
            jti = payload.get("jti")
            
            if jti:
                self._revoked_tokens.add(jti)
                self.logger.info("Token revoked", jti=jti, user_id=payload.get("sub"))
            
        except AuthenticationError:
            # Token já inválido, não precisa fazer nada
            pass
    
    def revoke_refresh_token(self, refresh_token: str) -> None:
        """
        Revoga um refresh token.
        
        Args:
            refresh_token: Refresh token a ser revogado
        """
        if refresh_token in self._refresh_tokens:
            token_data = self._refresh_tokens[refresh_token]
            del self._refresh_tokens[refresh_token]
            
            self.logger.info(
                "Refresh token revoked",
                user_id=token_data["user_id"],
                client_id=token_data["client_id"]
            )
    
    def get_token_info(self, token: str) -> TokenInfo:
        """
        Extrai informações de um token válido.
        
        Args:
            token: Token JWT
            
        Returns:
            Informações do token
        """
        payload = self.validate_token(token)
        
        scopes = payload.get("scope", "").split()
        expires_at = datetime.fromtimestamp(payload["exp"])
        
        return TokenInfo(
            token=token,
            token_type="Bearer",
            expires_at=expires_at,
            scope=scopes,
            user_id=payload.get("sub"),
            client_id=payload.get("client_id"),
            metadata={"jti": payload.get("jti")}
        )
    
    def check_scope(self, token: str, required_scope: str) -> bool:
        """
        Verifica se um token possui um escopo específico.
        
        Args:
            token: Token JWT
            required_scope: Escopo necessário
            
        Returns:
            True se o token possui o escopo
        """
        try:
            payload = self.validate_token(token)
            scopes = payload.get("scope", "").split()
            return required_scope in scopes
        except AuthenticationError:
            return False
    
    def cleanup_expired_tokens(self) -> None:
        """Remove tokens expirados dos caches."""
        now = datetime.utcnow()
        
        # Remove refresh tokens expirados
        expired_refresh = [
            token for token, data in self._refresh_tokens.items()
            if now > data["expires_at"]
        ]
        
        for token in expired_refresh:
            del self._refresh_tokens[token]
        
        if expired_refresh:
            self.logger.info("Expired refresh tokens cleaned up", count=len(expired_refresh))
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do gerenciador de tokens.
        
        Returns:
            Dicionário com estatísticas
        """
        return {
            "revoked_tokens": len(self._revoked_tokens),
            "active_refresh_tokens": len(self._refresh_tokens),
            "token_expiry_hours": self.token_expiry_hours,
            "algorithm": self.algorithm
        }