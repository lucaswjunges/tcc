from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import User, Reading, Card, ReadingCard
from . import db
import random
from datetime import datetime
import json
import os

reading_bp = Blueprint('reading', __name__)

@reading_bp.route('/reading', methods=['GET', 'POST'])
@login_required
def reading():
    if request.method == 'POST':
        # Get form data
        question = request.form.get('question')
        num_cards = int(request.form.get('num_cards', 3))
        spread_type = request.form.get('spread_type', 'celtic')
        
        # Validate input
        if not question:
            flash('Por favor, insira sua pergunta.', 'error')
            return redirect(url_for('reading.reading'))
        
        # Create reading
        reading = Reading(
            user_id=current_user.id,
            question=question,
            num_cards=num_cards,
            spread_type=spread_type,
            status='pending'
        )
        db.session.add(reading)
        db.session.commit()

        # Get tarot cards
        cards = Card.query.all()
        selected_cards = random.sample(cards, num_cards)
        
        # Create reading cards
        for card in selected_cards:
            reading_card = ReadingCard(
                reading_id=reading.id,
                card_id=card.id,
                position=selected_cards.index(card) + 1
            )
            db.session.add(reading_card)
        
        db.session.commit()
        
        # Prepare card data for template
        card_data = []
        for rc in selected_cards:
            card_data.append({
                'id': rc.id,
                'name': rc.name,
                'meaning': rc.meaning,
                'image_url': url_for('static', filename=f'cards/{rc.image_file}')
            })
        
        return render_template('reading_result.html', 
                             reading=reading, 
                             card_data=card_data,
                             spread_type=spread_type)
    
    # GET request - show form
    spreads = [
        {'name': 'Celta', 'value': 'celtic'},
        {'name': 'Tripla', 'value': 'triple'},
        {'name': 'Hierófila', 'value': 'hierophylactic'},
        {'name': 'Tempo/Esperança/Destruição', 'value': 'time_hope_destroy'}
    ]
    
    return render_template('reading_form.html', spreads=spreads)

@reading_bp.route('/readings')
@login_required
def user_readings():
    readings = Reading.query.filter_by(user_id=current_user.id).all()
    return render_template('user_readings.html', readings=readings)

@reading_bp.route('/reading/<int:reading_id>')
@login_required
def view_reading(reading_id):
    reading = Reading.query.get(reading_id)
    if not reading or reading.user_id != current_user.id:
        flash('Acesso não autorizado.', 'error')
        return redirect(url_for('main.home'))
    
    # Get all cards for this reading
    reading_cards = ReadingCard.query.filter_by(reading_id=reading_id).all()
    card_data = []
    for rc in reading_cards:
        card = Card.query.get(rc.card_id)
        card_data.append({
            'id': card.id,
            'name': card.name,
            'meaning': card.meaning,
            'image_url': url_for('static', filename=f'cards/{card.image_file}')
        })
    
    return render_template('reading_detail.html', 
                         reading=reading, 
                         card_data=card_data,
                         spread_type=reading.spread_type)

@reading_bp.route('/interpretation/<int:reading_id>/<int:card_position>')
@login_required
def show_interpretation(reading_id, card_position):
    reading = Reading.query.get(reading_id)
    if not reading or reading.user_id != current_user.id:
        flash('Acesso não autorizado.', 'error')
        return redirect(url_for('main.home'))
    
    # Get the card
    reading_card = ReadingCard.query.filter_by(
        reading_id=reading_id, position=card_position
    ).first()
    
    if not reading_card:
        flash('Carta não encontrada.', 'error')
        return redirect(url_for('reading.view_reading', reading_id=reading_id))
    
    card = Card.query.get(reading_card.card_id)
    
    # Get all cards for this reading
    reading_cards = ReadingCard.query.filter_by(
        reading_id=reading_id
    ).all()
    
    card_data = []
    for rc in reading_cards:
        card = Card.query.get(rc.card_id)
        card_data.append({
            'id': card.id,
            'name': card.name,
            'meaning': card.meaning,
            'image_url': url_for('static', filename=f'cards/{card.image_file}'),
            'position': rc.position
        })
    
    return render_template('interpretation.html', 
                         reading=reading, 
                         card_data=card_data,
                         card_position=card_position,
                         spread_type=reading.spread_type)