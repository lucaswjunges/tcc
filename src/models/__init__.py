# src/models/__init__.py

"""
Este módulo serve como a interface pública para os modelos de dados.

Ele importa os modelos principais e, crucialmente, executa model_rebuild()
para resolver quaisquer referências circulares (forward references) que
foram definidas durante a inicialização.
"""
from .project_context import ProjectContext
from ..schemas.contracts import SystemConfig

# O passo mágico: diz ao Pydantic para resolver as referências pendentes.
# Isso garante que todos os modelos estejam totalmente definidos e interligados.
ProjectContext.model_rebuild()
SystemConfig.model_rebuild()

# Exportamos os modelos para que outras partes do aplicativo possam importá-los
# a partir daqui, como um ponto central.
__all__ = ["ProjectContext", "SystemConfig"]
