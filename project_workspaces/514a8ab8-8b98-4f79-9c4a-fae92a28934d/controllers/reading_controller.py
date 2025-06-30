from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import Reading, Card, Spread, db
from .forms import ReadingForm
import random

reading_bp = Blueprint('reading', __name__, url_prefix='/reading')


@reading_bp.route('/new', methods=['GET', 'POST'])
def new_reading():
    form = ReadingForm()
    spreads = Spread.query.all()
    form.spread.choices = [(spread.id, spread.name) for spread in spreads]

    if form.validate_on_submit():
        spread = Spread.query.get(form.spread.data)
        cards = Card.query.all()
        selected_cards = random.sample(cards, spread.card_count)

        reading = Reading(spread=spread, user_question=form.question.data)
        db.session.add(reading)

        for i, card in enumerate(selected_cards):
            reading.cards.append(card)
            # Logic for card positions within the spread (future implementation)
            # Example:  card.position = spread.positions[i]

        db.session.commit()
        return redirect(url_for('reading.view_reading', reading_id=reading.id))

    return render_template('reading/new.html', form=form)


@reading_bp.route('/<int:reading_id>')
def view_reading(reading_id):
    reading = Reading.query.get_or_404(reading_id)
    return render_template('reading/view.html', reading=reading)



@reading_bp.route('/<int:reading_id>/interpret')
def interpret_reading(reading_id):
    reading = Reading.query.get_or_404(reading_id)
    # Placeholder for future interpretation logic. Currently just displays cards.
    return render_template('reading/interpret.html', reading=reading)


@reading_bp.route('/')
def readings():
    readings = Reading.query.all()
    return render_template('reading/list.html', readings=readings)