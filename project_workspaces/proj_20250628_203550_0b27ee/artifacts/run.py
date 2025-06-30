from backend.app import app

if __name__ == '__main__':
    import os
    
    # Configurações para desenvolvimento
    if os.environ.get('FLASK_ENV') == 'development':
        app.run(debug=True, host='0.0.0.0', port=5000)
    
    # Configurações para produção
    else:
        from waitress import serve
        serve(app, host='0.0.0.0', port=80)
