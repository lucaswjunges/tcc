#!/usr/bin/env python3
"""
VapeShop - Website de Venda de Pods e Vapes
Arquivo de inicialização do servidor
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório atual ao path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from app_enhanced import app
    
    if __name__ == '__main__':
        # Configurações de desenvolvimento
        debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
        port = int(os.environ.get('PORT', 5000))
        host = os.environ.get('HOST', '0.0.0.0')
        
        print("🚀 Iniciando VapeShop Server...")
        print(f"📡 Servidor rodando em: http://{host}:{port}")
        print(f"🔧 Modo debug: {'Ativado' if debug_mode else 'Desativado'}")
        print("─" * 50)
        
        app.run(
            debug=debug_mode,
            host=host,
            port=port,
            threaded=True
        )
        
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("\n📋 Verifique se todas as dependências estão instaladas:")
    print("pip install -r requirements_fixed.txt")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Erro ao iniciar o servidor: {e}")
    sys.exit(1)