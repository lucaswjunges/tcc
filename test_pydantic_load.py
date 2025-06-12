import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Limpar explicitamente variáveis de ambiente que podem interferir
# Fazemos isso ANTES de importar qualquer coisa que possa lê-las
vars_to_clear = ["EVOLUX_OPENROUTER_API_KEY", "EVOLUX_OPENAI_API_KEY"]
for var_name in vars_to_clear:
    if var_name in os.environ:
        print(f"[TEST_PYDANTIC] Removendo variável de ambiente: {var_name}")
        del os.environ[var_name]

# Caminho para o arquivo .env (relativo ao CWD, que será a raiz do projeto)
ENV_FILE_PATH = ".env" 
# Ou absoluto:
# ENV_FILE_PATH = str(Path(__file__).resolve().parent / ".env")


print(f"[TEST_PYDANTIC] Verificando arquivo .env em: {Path(ENV_FILE_PATH).resolve()}")
if Path(ENV_FILE_PATH).exists():
    print(f"[TEST_PYDANTIC] Arquivo .env ENCONTRADO.")
    with open(ENV_FILE_PATH, "r") as f:
        print(f"[TEST_PYDANTIC] Conteúdo .env (preview):\n---\n{f.read(200)}\n---")
else:
    print(f"[TEST_PYDANTIC] Arquivo .env NÃO ENCONTRADO. O teste falhará.")


class TestSettings(BaseSettings):
    MY_OPENROUTER_KEY: Optional[str] = Field(
        default=None, 
        validation_alias="EVOLUX_OPENROUTER_API_KEY" # Nome EXATO como no .env
    )
    MY_OPENAI_KEY: Optional[str] = Field(
        default=None,
        validation_alias="EVOLUX_OPENAI_API_KEY" # Nome EXATO como no .env
    )
    # Teste com um nome de campo idêntico ao do .env (sem alias)
    EVOLUX_HTTP_REFERER: Optional[str] = Field(default=None) # Adicione esta linha ao seu .env se não estiver: EVOLUX_HTTP_REFERER="http://test.com"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False # Mantenha False, é o padrão e mais flexível
    )

print("[TEST_PYDANTIC] Instanciando TestSettings...")
try:
    test_settings = TestSettings()
    print("[TEST_PYDANTIC] TestSettings instanciado.")
    print(f"[TEST_PYDANTIC] test_settings.MY_OPENROUTER_KEY: {test_settings.MY_OPENROUTER_KEY}")
    print(f"[TEST_PYDANTIC] test_settings.MY_OPENAI_KEY: {test_settings.MY_OPENAI_KEY}")
    print(f"[TEST_PYDANTIC] test_settings.EVOLUX_HTTP_REFERER: {test_settings.EVOLUX_HTTP_REFERER}")

    if test_settings.MY_OPENROUTER_KEY:
        print("\n[TEST_PYDANTIC] SUCESSO: Chave OpenRouter carregada!\n")
    else:
        print("\n[TEST_PYDANTIC] FALHA: Chave OpenRouter NÃO carregada.\n")

except Exception as e:
    print(f"[TEST_PYDANTIC] ERRO ao instanciar TestSettings: {e}")

print("\n[TEST_PYDANTIC] Verificando os.environ após Pydantic:")
print(f"[TEST_PYDANTIC] os.environ.get('EVOLUX_OPENROUTER_API_KEY'): {os.environ.get('EVOLUX_OPENROUTER_API_KEY')}")

