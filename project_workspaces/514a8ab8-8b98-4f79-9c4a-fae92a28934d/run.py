from flask import Flask
from config import config

# Import blueprints
from routes.main import main_bp
from routes.auth import auth_bp
from routes.api import api_bp

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')


    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)