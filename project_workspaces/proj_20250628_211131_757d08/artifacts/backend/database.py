from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize SQLAlchemy and Migrate
db = SQLAlchemy()
migrate = Migrate()

# Database configuration
SQLALCHEMY_DATABASE_URI = 'postgresql://username:password@localhost:5432/failure_prevention_db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Initialize extensions
def init_app(app):
    db.init_app(app)
    migrate.init_app(app, db)

# Database models
# (These would be imported from backend/models.py in a real project)
# class User(db.Model):
#     pass

# class Motor(db.Model):
#     pass

# class FailurePrediction(db.Model):
#     pass