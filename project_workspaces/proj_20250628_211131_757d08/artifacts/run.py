from backend.app import app

if __name__ == '__main__':
    import os
    # Configurar ambiente de desenvolvimento
    app.config['DEBUG'] = True
    app.run(host='0.0.0.0', port=5000)
