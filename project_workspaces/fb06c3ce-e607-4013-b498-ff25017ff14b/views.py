from flask import render_template, request, redirect, url_for, flash
from . import app, db
from .models import Reading, Card, Spread
from .forms import ReadingForm
import random

@app.route('/', methods=['GET', 'POST'])
def index():
    spreads = Spread.query.all()
    form = ReadingForm()
    form.spread.choices = [(spread.id, spread.name) for spread in spreads]

    if form.validate_on_submit():
        spread = Spread.query.get(form.spread.data)
        cards = Card.query.all()
        selected_cards = random.sample(cards, spread.card_count)

        reading = Reading(spread=spread, question=form.question.data)
        for card in selected_cards:
            reading.cards.append(card)
        db.session.add(reading)
        db.session.commit()

        return redirect(url_for('reading', reading_id=reading.id))

    return render_template('index.html', form=form, spreads=spreads)

@app.route('/reading/<int:reading_id>')
def reading(reading_id):
    reading = Reading.query.get_or_404(reading_id)
    return render_template('reading.html', reading=reading)

@app.route('/about')
def about():
    return render_template('about.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500