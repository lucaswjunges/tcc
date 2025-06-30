"""
Gerenciador OAuth 2.0 para o MCP LLM Server.

Este módulo implementa o fluxo OAuth 2.0 Authorization Code Grant
para autenticação segura de clientes do servidor MCP.
"""

import secrets
import time
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlencode, parse_qs, urlparse
from datetime import datetime, timedelta

from authlib.integrations.base_client import OAuthError
from authlib.oauth2 import OAuth2Error
import httpx

from .token_manager import TokenManager, TokenInfo
from ..config import settings
from ..utils import LoggerMixin
from ..utils.exceptions import AuthenticationError, AuthorizationError, ConfigurationError


class OAuthClient:
    """Representa um cliente OAuth registrado."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uris: List[str],
        scopes: List[str],
        name: str = ""
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uris = redirect_uris
        self.scopes = scopes
        self.name = name
        self.created_at = datetime.utcnow()


class OAuthManager(LoggerMixin):
    """
    Gerenciador OAuth 2.0 para autenticação de clientes.
    
    Implementa o fluxo Authorization Code Grant do OAuth 2.0
    para permitir que clientes se autentiquem de forma segura.
    """
    
    def __init__(self):
        """Inicializa o gerenciador OAuth."""
        self.token_manager = TokenManager()
        
        # Configurações OAuth
        self.client_id = settings.oauth.client_id
        self.client_secret = settings.oauth.client_secret
        self.redirect_uri = settings.oauth.redirect_uri
        self.scopes = settings.oauth.scopes
        
        # Armazenamento em memória (em produção, usar database)
        self._clients: Dict[str, OAuthClient] = {}
        self._authorization_codes: Dict[str, Dict[str, Any]] = {}
        self._user_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Registra cliente padrão se configurado
        if self.client_id and self.client_secret:
            self._register_default_client()
        
        self.logger.info("OAuth manager initialized")
    
    def _register_default_client(self) -> None:
        """Registra o cliente padrão da configuração."""
        client = OAuthClient(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uris=[self.redirect_uri],
            scopes=self.scopes,
            name="Default MCP Client"
        )
        
        self._clients[self.client_id] = client
        
        self.logger.info(
            "Default OAuth client registered",
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope_count=len(self.scopes)
        )
    
    def register_client(
        self,
        client_id: str,
        client_secret: str,
        redirect_uris: List[str],
        scopes: List[str],
        name: str = ""
    ) -> None:
        """
        Registra um novo cliente OAuth.
        
        Args:
            client_id: ID único do cliente
            client_secret: Senha secreta do cliente
            redirect_uris: URIs de redirecionamento válidas
            scopes: Escopos que o cliente pode solicitar
            name: Nome descritivo do cliente
        """
        if client_id in self._clients:
            raise ValueError(f"Client {client_id} already registered")
        
        client = OAuthClient(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uris=redirect_uris,
            scopes=scopes,
            name=name
        )
        
        self._clients[client_id] = client
        
        self.logger.info(
            "OAuth client registered",
            client_id=client_id,
            name=name,
            redirect_uri_count=len(redirect_uris)
        )
    
    def get_authorization_url(
        self,
        client_id: str,
        redirect_uri: str,
        scope: str,
        response_type: str = "code",
        state: Optional[str] = None
    ) -> str:
        """
        Gera URL de autorização OAuth.
        
        Args:
            client_id: ID do cliente
            redirect_uri: URI de redirecionamento
            scope: Escopos solicitados
            response_type: Tipo de resposta (sempre "code")
            state: Estado opcional para prevenir CSRF
            
        Returns:
            URL de autorização
            
        Raises:
            AuthorizationError: Se os parâmetros forem inválidos
        """
        # Valida cliente
        if client_id not in self._clients:
            raise AuthorizationError("Invalid client_id")
        
        client = self._clients[client_id]
        
        # Valida redirect_uri
        if redirect_uri not in client.redirect_uris:
            raise AuthorizationError("Invalid redirect_uri")
        
        # Valida escopos
        requested_scopes = scope.split()
        if not all(s in client.scopes for s in requested_scopes):
            raise AuthorizationError("Invalid scope")
        
        # Valida response_type
        if response_type != "code":
            raise AuthorizationError("Unsupported response_type")
        
        # Gera parâmetros da URL
        params = {
            "response_type": response_type,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope
        }
        
        if state:
            params["state"] = state
        
        # URL base de autorização (em produção, seria um endpoint web)
        base_url = "https://auth.mcpllm.com/authorize"
        authorization_url = f"{base_url}?{urlencode(params)}"
        
        self.logger.info(
            "Authorization URL generated",
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope
        )
        
        return authorization_url
    
    def create_authorization_code(
        self,
        client_id: str,
        redirect_uri: str,
        scope: str,
        user_id: str
    ) -> str:
        """
        Cria um código de autorização após o usuário aprovar.
        
        Args:
            client_id: ID do cliente
            redirect_uri: URI de redirecionamento
            scope: Escopos aprovados
            user_id: ID do usuário que aprovou
            
        Returns:
            Código de autorização
        """
        # Gera código de autorização
        code = secrets.token_urlsafe(32)
        
        # Armazena informações do código
        self._authorization_codes[code] = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=10)  # Códigos expiram em 10 minutos
        }
        
        self.logger.info(
            "Authorization code created",
            client_id=client_id,
            user_id=user_id,
            code_prefix=code[:8] + "..."
        )
        
        return code
    
    def exchange_code_for_tokens(
        self,
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Troca código de autorização por tokens de acesso.
        
        Args:
            code: Código de autorização
            client_id: ID do cliente
            client_secret: Senha secreta do cliente
            redirect_uri: URI de redirecionamento
            
        Returns:
            Dicionário com access_token, refresh_token e metadata
            
        Raises:
            AuthenticationError: Se os parâmetros forem inválidos
        """
        # Valida código de autorização
        if code not in self._authorization_codes:
            raise AuthenticationError("Invalid authorization code")
        
        code_data = self._authorization_codes[code]
        
        # Verifica expiração do código
        if datetime.utcnow() > code_data["expires_at"]:
            del self._authorization_codes[code]
            raise AuthenticationError("Authorization code has expired")
        
        # Valida cliente
        if client_id not in self._clients:
            raise AuthenticationError("Invalid client_id")
        
        client = self._clients[client_id]
        
        # Valida client_secret
        if client.client_secret != client_secret:
            raise AuthenticationError("Invalid client_secret")
        
        # Valida consistência dos parâmetros
        if (code_data["client_id"] != client_id or 
            code_data["redirect_uri"] != redirect_uri):
            raise AuthenticationError("Invalid request parameters")
        
        # Remove código usado
        del self._authorization_codes[code]
        
        # Cria tokens
        scopes = code_data["scope"].split()
        user_id = code_data["user_id"]
        
        access_token = self.token_manager.create_access_token(
            user_id=user_id,
            client_id=client_id,
            scopes=scopes
        )
        
        refresh_token = self.token_manager.create_refresh_token(
            user_id=user_id,
            client_id=client_id,
            scopes=scopes
        )
        
        self.logger.info(
            "Tokens issued",
            client_id=client_id,
            user_id=user_id,
            scope=code_data["scope"]
        )
        
        return {
            "access_token": access_token.token,
            "token_type": access_token.token_type,
            "expires_in": int((access_token.expires_at - datetime.utcnow()).total_seconds()),
            "refresh_token": refresh_token,
            "scope": code_data["scope"]
        }
    
    def refresh_token(
        self,
        refresh_token: str,
        client_id: str,
        client_secret: str
    ) -> Dict[str, Any]:
        """
        Atualiza um access token usando refresh token.
        
        Args:
            refresh_token: Refresh token válido
            client_id: ID do cliente
            client_secret: Senha secreta do cliente
            
        Returns:
            Novo access token
        """
        # Valida cliente
        if client_id not in self._clients:
            raise AuthenticationError("Invalid client_id")
        
        client = self._clients[client_id]
        
        # Valida client_secret
        if client.client_secret != client_secret:
            raise AuthenticationError("Invalid client_secret")
        
        # Renova token
        new_token = self.token_manager.refresh_access_token(refresh_token)
        
        return {
            "access_token": new_token.token,
            "token_type": new_token.token_type,
            "expires_in": int((new_token.expires_at - datetime.utcnow()).total_seconds()),
            "scope": " ".join(new_token.scope)
        }
    
    def revoke_token(
        self,
        token: str,
        client_id: str,
        client_secret: str,
        token_type_hint: Optional[str] = None
    ) -> None:
        """
        Revoga um token (access ou refresh).
        
        Args:
            token: Token a ser revogado
            client_id: ID do cliente
            client_secret: Senha secreta do cliente
            token_type_hint: Tipo do token (opcional)
        """
        # Valida cliente
        if client_id not in self._clients:
            raise AuthenticationError("Invalid client_id")
        
        client = self._clients[client_id]
        
        # Valida client_secret
        if client.client_secret != client_secret:
            raise AuthenticationError("Invalid client_secret")
        
        # Tenta revogar como access token
        try:
            self.token_manager.revoke_token(token)
        except:
            pass
        
        # Tenta revogar como refresh token
        try:
            self.token_manager.revoke_refresh_token(token)
        except:
            pass
        
        self.logger.info("Token revoked", client_id=client_id)
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Valida um token de acesso.
        
        Args:
            token: Token a ser validado
            
        Returns:
            Payload do token
        """
        return self.token_manager.validate_token(token)
    
    def check_authorization(self, token: str, required_scope: str) -> bool:
        """
        Verifica se um token tem autorização para um escopo.
        
        Args:
            token: Token de acesso
            required_scope: Escopo necessário
            
        Returns:
            True se autorizado
        """
        return self.token_manager.check_scope(token, required_scope)
    
    def cleanup_expired_data(self) -> None:
        """Remove dados expirados."""
        now = datetime.utcnow()
        
        # Remove códigos de autorização expirados
        expired_codes = [
            code for code, data in self._authorization_codes.items()
            if now > data["expires_at"]
        ]
        
        for code in expired_codes:
            del self._authorization_codes[code]
        
        # Limpa tokens expirados
        self.token_manager.cleanup_expired_tokens()
        
        if expired_codes:
            self.logger.info("Expired authorization codes cleaned up", count=len(expired_codes))
    
    def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Retorna informações sobre um cliente.
        
        Args:
            client_id: ID do cliente
            
        Returns:
            Informações do cliente ou None
        """
        if client_id not in self._clients:
            return None
        
        client = self._clients[client_id]
        
        return {
            "client_id": client.client_id,
            "name": client.name,
            "redirect_uris": client.redirect_uris,
            "scopes": client.scopes,
            "created_at": client.created_at.isoformat()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do OAuth manager.
        
        Returns:
            Dicionário com estatísticas
        """
        return {
            "registered_clients": len(self._clients),
            "active_authorization_codes": len(self._authorization_codes),
            "token_manager_stats": self.token_manager.get_stats()
        }