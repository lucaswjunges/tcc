import sys
from flask.cli import FlaskGroup
from backend.app import app

# Define o grupo de comandos da CLI
cli = FlaskGroup(app)

if __name__ == '__main__':
    cli.main()

# Configurações de ambiente
if len(sys.argv) > 1 and sys.argv[1] == 'dev':
    app.config.from_object('config.DevelopmentConfig')
    print('🔧 Executando no modo de desenvolvimento com debug ativado')
elif len(sys.argv) > 1 and sys.argv[1] == 'prod':
    app.config.from_object('config.ProductionConfig')
    print('🚀 Executando no modo de produção')
else:
    app.config.from_object('config.DefaultConfig')
    print('ℹ️ Executando no modo padrão')

# Comandos disponíveis
print('\n📋 Comandos disponíveis:')
print(' - python run.py dev   : Executar em modo de desenvolvimento (debug ativado)')
print(' - python run.py prod  : Executar em modo de produção (sem debug)')
print(' - python run.py test  : Executar testes unitários')
