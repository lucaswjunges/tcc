from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tarot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Reading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    spread = db.Column(db.String(255)) # e.g., "Three-Card Spread"
    interpretation = db.Column(db.Text)

# --- Create Database if it doesn't exist ---
if not os.path.exists('tarot.db'):
    db.create_all()
    print("Database created!")

# --- Routes ---

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        question = request.form.get("question")

        # Placeholder - In a real application, integrate with a Tarot library/API
        interpretation = "This is a placeholder interpretation. In a real app, this would be generated based on the chosen spread and drawn cards." 
        
        reading = Reading(question=question, interpretation=interpretation)
        db.session.add(reading)
        db.session.commit()
        return redirect(url_for("reading", id=reading.id)) 
    return render_template("index.html")


@app.route("/reading/<int:id>")
def reading(id):
    reading = Reading.query.get(id)
    if reading:
        return render_template("reading.html", reading=reading)
    return "Reading not found", 404


if __name__ == "__main__":
    app.run(debug=True)