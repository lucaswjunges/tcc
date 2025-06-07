import sys
import os

print("--- DIAGNÓSTICO DO AMBIENTE PYTHON ---")

print("\n[1] Python Executável:")
print(sys.executable)

print("\n[2] Caminhos de Módulos (sys.path):")
for path in sys.path:
    print(path)

print("\n[3] Tentando localizar 'project_context'...")
try:
    # Este import é a chave do teste
    from src.models import project_context
    
    print("\n[SUCESSO] Módulo 'project_context' importado.")
    print("   -> ARQUIVO CARREGADO DE:")
    print(f"      {project_context.__file__}")
    
    print("\n[4] Verificando o conteúdo do objeto carregado...")
    has_config = hasattr(project_context.ProjectContext, 'config')
    print(f"   -> O objeto 'ProjectContext' carregado tem o atributo 'config'? {has_config}")

except ImportError as e:
    print(f"\n[FALHA] Não foi possível importar o módulo: {e}")
except Exception as e:
    print(f"\n[ERRO INESPERADO] Ocorreu um erro: {e}")

