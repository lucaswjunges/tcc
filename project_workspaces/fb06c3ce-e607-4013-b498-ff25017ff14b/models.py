from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    readings = db.relationship('Reading', backref='user', lazy=True)

class Reading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    spread_type = db.Column(db.String(50))  # e.g., 'Three-Card', 'Celtic Cross'
    cards = db.Column(db.Text) # Store card data (e.g., JSON)
    interpretation = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    price = db.Column(db.Float) # Store the price of the reading
    payment_status = db.Column(db.String(20), default='pending') # e.g., 'pending', 'paid', 'refunded'


class TarotCard(db.Model): #  To manage the Tarot deck
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    arcana = db.Column(db.String(20)) # 'Major' or 'Minor'
    suit = db.Column(db.String(20)) #  'Wands', 'Cups', 'Swords', 'Pentacles' or None for Major Arcana
    number = db.Column(db.Integer)  # Number for Minor Arcana, or Roman numeral equivalent for Major Arcana (e.g., I, II, ...)
    keywords = db.Column(db.Text) # Comma-separated keywords
    meaning_upright = db.Column(db.Text)
    meaning_reversed = db.Column(db.Text)
    image_url = db.Column(db.String(255))



#  A model to handle spread types and their configurations:
class Spread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # e.g., 'Three-Card', 'Celtic Cross'
    description = db.Column(db.Text)
    card_positions = db.Column(db.Text) # JSON defining card positions and their meanings