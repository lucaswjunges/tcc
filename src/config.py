# src/config.py (VERSÃO CORRETA E SIMPLIFICADA)

from src.schemas.contracts import SystemConfig

# A instância de settings agora é criada diretamente da SystemConfig,
# que sabe como ler o arquivo .env por conta própria.
settings = SystemConfig()
