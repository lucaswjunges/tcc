from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from src.models import User, Reading, Card, Spread
from src import db, mail
from src.utils import generate_tarot_spread, draw_cards, get_card_meaning
from datetime import datetime
from flask_mail import Message
import random
import os

reading_bp = Blueprint('reading', __name__)

@reading_bp.route('/reading', methods=['GET', 'POST'])
@login_required
def reading():
    if request.method == 'POST':
        # Process the reading request
        spread_type = request.form.get('spread_type')
        num_questions = request.form.get('num_questions')
        
        # Validate form data
        if not spread_type or not num_questions:
            flash('Please select a spread type and number of questions')
            return redirect(url_for('reading.reading'))
        
        # Create a new reading
        reading = Reading(
            user_id=current_user.id,
            spread_type=spread_type,
            num_questions=num_questions,
            status='in-progress'
        )
        db.session.add(reading)
        db.session.commit()
        
        # Generate the reading details
        reading_details = generate_tarot_spread(
            spread_type, 
            int(num_questions)
        )
        
        # Save the reading details
        reading.details = str(reading_details)
        db.session.commit()
        
        # Send email notification
        send_reading_email(current_user.email, reading_details)
        
        # Redirect to results page
        return redirect(url_for('reading.view_reading', reading_id=reading.id))
    
    # Get available spreads
    spreads = Spread.query.all()
    
    return render_template('reading.html', spreads=spreads)

@reading_bp.route('/view_reading/<int:reading_id>')
@login_required
def view_reading(reading_id):
    reading = Reading.query.get_or_404(reading_id)
    
    if reading.user_id != current_user.id:
        flash('You don\'t have permission to view this reading')
        return redirect(url_for('main.home'))
    
    if reading.status == 'completed':
        details = eval(reading.details)
        return render_template('reading_results.html', details=details)
    else:
        flash('Reading is still in progress')
        return redirect(url_for('reading.reading'))

@reading_bp.route('/complete_reading/<int:reading_id>')
@login_required
def complete_reading(reading_id):
    reading = Reading.query.get_or_404(reading_id)
    
    if reading.user_id != current_user.id:
        flash('You don\'t have permission to complete this reading')
        return redirect(url_for('main.home'))
    
    reading.status = 'completed'
    db.session.commit()
    
    flash('Reading marked as completed!')
    return redirect(url_for('reading.view_reading', reading_id=reading_id))

def send_reading_email(email, reading_details):
    msg = Message("Your Tarot Reading is Ready!", 
                  sender="noreply@tarotadivinhacao.com",
                  recipients=[email])
    
    msg.body = f"Dear User,\n\nYour Tarot reading is ready. You can view it by logging into our website.\n\nBest regards,\nThe Tarot Adivinhacao Team"
    
    mail.send(msg)