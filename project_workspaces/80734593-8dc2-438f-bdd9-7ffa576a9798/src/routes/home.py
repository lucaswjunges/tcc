from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import User, Reading, Card, ReadingType
from . import db
import random
import json
from datetime import datetime
import os
from .utils import generate_tarot_spread, get_card_images

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def home():
    return render_template('home.html')

@home_bp.route('/about')
def about():
    return render_template('about.html')

@home_bp.route('/how-it-works')
def how_it_works():
    return render_template('how-it-works.html')

@home_bp.route('/readings')
@login_required
def readings():
    user_readings = Reading.query.filter_by(user_id=current_user.id).order_by(Reading.date.desc()).all()
    return render_template('readings.html', readings=user_readings)

@home_bp.route('/tarot-spreads')
@login_required
def tarot_spreads():
    spreads = [
        {'name': 'Single Card', 'description': 'A simple reading with just one card for guidance.'},
        {'name': 'Three Card Past Present Future', 'description': 'A classic spread showing past, present, and future.'},
        {'name': 'Celtic Cross', 'description': 'A detailed spread with ten positions for comprehensive insight.'},
        {'name': 'Relationship Spread', 'description': 'Focuses on romantic relationships and compatibility.'},
        {'name': 'Career Path Spread', 'description': 'Helps clarify professional direction and opportunities.'}
    ]
    return render_template('tarot_spreads.html', spreads=spreads)

@home_bp.route('/start-reading', methods=['GET', 'POST'])
@login_required
def start_reading():
    if request.method == 'POST':
        spread_type = request.form.get('spread_type')
        num_cards = request.form.get('num_cards')
        reading_type_id = request.form.get('reading_type')
        question = request.form.get('question')
        
        # Get user to set
        user = User.query.get(current_user.id)
        
        # Get reading type
        reading_type = ReadingType.query.get(int(reading_type_id))
        
        # Create reading
        new_reading = Reading(
            user_id=user.id,
            reading_type_id=reading_type.id if reading_type_id else None,
            spread_type=spread_type,
            num_cards=num_cards,
            question=question,
            date=datetime.now()
        )
        
        db.session.add(new_reading)
        db.session.commit()
        
        # Get cards
        cards = Card.query.order_by(func.random()).limit(int(num_cards)).all()
        
        # Save cards to reading
        for card in cards:
            card.readings.append(new_reading)
            db.session.commit()
        
        # Redirect to reading details
        return redirect(url_for('home.reading_details', reading_id=new_reading.id))
    
    return render_template('start_reading.html')

@home_bp.route('/reading-details/<int:reading_id>')
@login_required
def reading_details(reading_id):
    reading = Reading.query.get(reading_id)
    cards = reading.cards
    
    # Generate interpretation
    interpretation = generate_tarot_interpretation(cards, reading.spread_type)
    
    return render_template('reading_details.html', reading=reading, cards=cards, interpretation=interpretation)

@home_bp.route('/pricing')
def pricing():
    return render_template('pricing.html')

@home_bp.route('/contact')
def contact():
    return render_template('contact.html')

@home_bp.route('/blog')
def blog():
    return render_template('blog.html')

@home_bp.route('/ethics')
def ethics():
    return render_template('ethics.html')

def generate_tarot_interpretation(cards, spread_type):
    # This is a simplified interpretation function
    # In a real application, this would be much more comprehensive
    interpretation = {
        'cards': [],
        'overall': 'Your reading shows...'
    }
    
    # Get card meanings
    card_meanings = {
        1: "The Fool: New beginnings, freedom, spontaneity",
        2: "The Magician: Manifestation, resourcefulness, power",
        3: "The High Priestess: Intuition, unconscious knowledge, divine feminine",
        4: "The Empress: Fertility, beauty, nature, abundance",
        5: "The Emperor: Authority, structure, control, fatherhood",
        6: "The Hierophant: Tradition, spirituality, conventional wisdom",
        7: "The Lovers: Relationships, harmony, values, choices",
        8: "The Chariot: Willpower, control, victory, movement",
        9: "Strength: Courage, persuasion, inner strength",
        10: "The Hermit: Solitude, introspection, guidance",
        11: "Wheel of Fortune: Change, destiny, karma, cycles",
        12: "Justice: Fairness, truth, cause and effect",
        13: "The Hanged Man: Surrender, new perspective, spiritual awakening",
        14: "Death: End of cycle, transformation, letting go",
        15: "Temperance: Moderation, patience, blending opposites",
        16: "The Devil: Attachment, illusion, materialism, bondage",
        17: "The Tower: Sudden change, upheaval, revelation",
        18: "The Star: Hope, faith, renewal, inspiration",
        19: "The Moon: Illusion, dreams, intuition, subconscious",
        20: "The Sun: Positivity, success, vitality, warmth",
        21: "Judgment: Awakening, reckoning, second chance",
        22: "The World: Completion, achievement, travel, wholeness"
    }
    
    # Assign random meanings to cards
    for i, card in enumerate(cards):
        card_num = card.card_number
        card_meaning = card_meanings.get(card_num, "Unknown card")
        interpretation['cards'].append({
            'card': card,
            'meaning': card_meaning,
            'position': f"Position {i+1} in {spread_type} spread"
        })
    
    # Add overall interpretation
    interpretation['overall'] += f" Your {spread_type} reading involves {len(cards)} cards. The cards drawn are: "
    for card in cards:
        interpretation['overall'] += f"{card.card_name}, "
    
    return interpretation

@home_bp.route('/blog-post')
def blog_post():
    return render_template('blog_post.html')