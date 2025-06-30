from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import os

# Importar configurações
from config import Config

# Inicializar a aplicação
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Inicializar o gerenciador de login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configurar o banco de dados
db = SQLAlchemy(app)
db.init_app(app)

# Modelo de usuário
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

# Modelo de consulta
class Reading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    cards = db.Column(db.Text, nullable=False)
    interpretation = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, default=0.0)
    is_paid = db.Column(db.Boolean, default=False)

# Modelo de carta
class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.String(100), nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/how-it-works')
def how_it_works():
    return render_template('how-it-works.html')

@app.route('/readings')
@login_required
def readings():
    user_readings = Reading.query.filter_by(user_id=current_user.id).all()
    return render_template('readings.html', readings=user_readings)

@app.route('/tarot-deck')
@login_required
def tarot_deck():
    cards = Card.query.all()
    return render_template('tarot_deck.html', cards=cards)

@app.route('/single-card')
@login_required
def single_card():
    cards = Card.query.all()
    return render_template('single_card.html', cards=cards)

@app.route('/spread')
@login_required
def spread():
    return render_template('spread.html')

@app.route('/read', methods=['POST'])
@login_required
def read():
    num_cards = int(request.form.get('num_cards', 3))
    card_ids = random.sample([c.id for c in Card.query.all()], num_cards)
    cards = Card.query.filter(Card.id.in_(card_ids)).all()
    
    # Criar string para armazenamento no banco
    cards_str = ','.join([str(card.id) for card in cards])
    
    # Calcular preço baseado no número de cartas
    price = num_cards * Config.PRICE_PER_CARD
    
    # Criar nova consulta
    new_reading = Reading(
        user_id=current_user.id,
        cards=cards_str,
        price=price
    )
    
    db.session.add(new_reading)
    db.session.commit()
    
    return redirect(url_for('interpretation', reading_id=new_reading.id))

@app.route('/interpretation/<reading_id>')
@login_required
def interpretation(reading_id):
    reading = Reading.query.get_or_404(reading_id)
    # Aqui você faria a interpretação das cartas
    # Para este exemplo, vamos gerar uma interpretação aleatória
    interpretations = [
        "Esta carta sugere que você deve confiar em seu instinto e tomar decisões com confiança.",
        "Esta carta indica que mudanças positivas estão se aproximando. Aja com otimismo.",
        "Esta carta representa desafios que você precisa superar. Mostre persistência e determinação."
    ]
    reading.interpretation = random.choice(interpretations)
    db.session.commit()
    
    return render_template('interpretation.html', reading=reading)

@app.route('/payment/<reading_id>', methods=['POST'])
@login_required
def payment(reading_id):
    reading = Reading.query.get_or_404(reading_id)
    # Processar pagamento aqui (integraria um gateway de pagamento real)
    reading.is_paid = True
    db.session.commit()
    
    flash("Pagamento realizado com sucesso! Obrigado pela sua compra.")
    return redirect(url_for('readings'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:  # Em um sistema real, usar hashing!
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha incorretos')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Verificar se o usuário já existe
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            flash('Este nome de usuário ou e-mail já está em uso')
            return render_template('register.html')
        
        new_user = User(
            username=username,
            email=email,
            password=password
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Acesso negado!')
        return redirect(url_for('index'))
    
    users = User.query.all()
    readings = Reading.query.all()
    cards = Card.query.all()
    
    return render_template('admin.html', users=users, readings=readings, cards=cards)

@app.route('/admin/user/<int:user_id>/toggle_admin')
@login_required
def toggle_admin(user_id):
    if not current_user.is_admin:
        flash('Acesso negado!')
        return redirect(url_for('admin'))
    
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    
    flash(f'Administrador status atualizado para {user.username}')
    return redirect(url_for('admin'))

@app.route('/admin/card/add', methods=['POST'])
@login_required
def add_card():
    if not current_user.is_admin:
        flash('Acesso negado!')
        return redirect(url_for('admin'))
    
    name = request.form.get('name')
    description = request.form.get('description')
    image_path = request.form.get('image_path')
    
    new_card = Card(
        name=name,
        description=description,
        image_path=image_path
    )
    
    db.session.add(new_card)
    db.session.commit()
    
    flash('Carta adicionada com sucesso!')
    return redirect(url_for('admin'))

@app.route('/admin/reading/<int:reading_id>/delete')
@login_required
def delete_reading(reading_id):
    if not current_user.is_admin:
        flash('Acesso negado!')
        return redirect(url_for('admin'))
    
    reading = Reading.query.get_or_404(reading_id)
    db.session.delete(reading)
    db.session.commit()
    
    flash('Leitura deletada com sucesso!')
    return redirect(url_for('admin'))

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

if __name__ == '__main__':
    app.run(debug=Config.DEBUG)