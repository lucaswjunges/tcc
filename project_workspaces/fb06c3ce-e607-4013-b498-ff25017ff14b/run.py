from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configuration for SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tarot.db'
db = SQLAlchemy(app)

class Reading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spread = db.Column(db.String(255)) #e.g., 'Three Card Spread', 'Celtic Cross'
    cards = db.Column(db.String(255)) #e.g., 'The Fool, The Magician, The High Priestess'
    interpretation = db.Column(db.Text) 
    timestamp = db.Column(db.DateTime, default=db.func.now())


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reading', methods=['GET', 'POST'])
def reading():
    if request.method == 'POST':
        spread = request.form.get('spread')
        #  Logic for generating card reading and interpretation would go here.
        #  This is a placeholder, and should be replaced by actual tarot logic.
        cards = "The Fool, The Magician, The High Priestess" # Placeholder
        interpretation = "This is a placeholder interpretation." # Placeholder

        reading = Reading(spread=spread, cards=cards, interpretation=interpretation)
        db.session.add(reading)
        db.session.commit()
        return redirect(url_for('reading'))
    return render_template('reading.html')


if __name__ == "__main__":
    if not os.path.exists('tarot.db'):
        db.create_all()
    app.run(debug=True)