from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tarot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Modelo de Usuário
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    # Outras colunas, como data de criação, etc.

# Modelo de Carta do Tarô
class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    meaning = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(200), nullable=True)

# Modelo de Tira (Spread)
class Spread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

# Modelo de Leitura
class Reading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    spread_id = db.Column(db.Integer, db.ForeignKey('spread.id'), nullable=False)
    cards = db.Column(db.String(500), nullable=False)  # String com IDs das cartas
    date = db.Column(db.DateTime, default=datetime.utcnow)
    interpretation = db.Column(db.Text, nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rotas de autenticação
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Lógica de login
        pass
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Lógica de registro
        pass
    return render_template('register.html')

# Página inicial
@app.route('/')
def index():
    return render_template('index.html')

# Página de Sobre
@app.route('/about')
def about():
    return render_template('about.html')

# Página de Leituras
@app.route('/readings')
@login_required
def readings():
    # Listar leituras do usuário logado
    return render_template('readings.html')

# Página de Tiras (Spreads)
@app.route('/spreads')
@login_required
def spreads():
    # Listar spreads disponíveis
    return render_template('spreads.html')

# Fazer uma leitura
@app.route('/draw', methods=['POST'])
@login_required
def draw():
    # Lógica para fazer uma leitura
    pass

# Configuração do banco de dados
def create_database():
    db.create_all()

if __name__ == '__main__':
    create_database()
    app.run(debug=True)