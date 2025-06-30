import sys
import subprocess
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
import random
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Configuração inicial do Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_aqui'

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tarot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialização do SQLAlchemy
db = SQLAlchemy(app)

# Inicialização do LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Pasta para uploads
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB

# Pasta para imagens do tarô
IMAGES_FOLDER = 'static/images/tarot'
if not os.path.exists(IMAGES_FOLDER):
    os.makedirs(IMAGES_FOLDER)

# Pasta para imagens de perfil
AVATARS_FOLDER = 'static/uploads/avatars'
if not os.path.exists(AVATARS_FOLDER):
    os.makedirs(AVATARS_FOLDER)

# Modelos do banco de dados
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    avatar = db.Column(db.String(200), default='default_avatar.png')
    readings = db.relationship('Reading', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)

class Reading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    result = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(200), default='default_reading.png')
    rating = db.Column(db.Integer, default=5)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    rating = db.Column(db.Integer, default=5)

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    meaning_up = db.Column(db.Text, nullable=False)
    meaning_rev = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200), default='default_card.png')

class ReadingType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

# Criação das tabelas do banco de dados
def create_database():
    db.create_all()
    
    # Verifica se existem cartas no banco de dados
    if Card.query.count() == 0:
        # Dados de exemplo para cartas do tarô
        cards_data = [
            {'name': 'O Mago', 'meaning_up': 'Sabedoria e poder pessoal', 'meaning_rev': 'Impulso criativo bloqueado'},
            {'name': 'A Fada', 'meaning_up': 'Crescimento espiritual', 'meaning_rev': 'Desconexão com o propósito'},
            {'name': 'O Eremita', 'meaning_up': 'Busca interior', 'meaning_rev': 'Isolamento'},
            {'name': 'A Roda da Fortuna', 'meaning_up': 'Mudanças positivas', 'meaning_rev': 'Ciclos ruins'},
            {'name': 'A Justiça', 'meaning_up': 'Equidade e justiça', 'meaning_rev': 'Desproporção'},
            {'name': 'O Herói', 'meaning_up': 'Coragem e ação', 'meaning_rev': 'Medo'},
            {'name': 'A Rua', 'meaning_up': 'Viagem e aventura', 'meaning_rev': 'Fracasso'},
            {'name': 'A Justiça', 'meaning_up': 'Equidade e justiça', 'meaning_rev': 'Desproporção'},
            {'name': 'O Enamorado', 'meaning_up': 'Relacionamentos e escolhas', 'meaning_rev': 'Dúvida'},
            {'name': 'O Carro', 'meaning_up': 'Controle e sucesso', 'meaning_rev': 'Perda de poder'},
            {'name': 'A Justiça', 'meaning_up': 'Equidade e justiça', 'meaning_rev': 'Desproporção'},
            {'name': 'A Temperança', 'meaning_up': 'Moderação e flexibilidade', 'meaning_rev': 'Extremos'},
            {'name': 'A Morte', 'meaning_up': 'Fim e transformação', 'meaning_rev': 'Medo do fim'},
            {'name': 'A Temperança', 'meaning_up': 'Moderação e flexibilidade', 'meaning_rev': 'Extremos'},
            {'name': 'O Juiz', 'meaning_up': 'Decisão e julgamento', 'meaning_rev': 'Inação'},
        ]
        
        for card_data in cards_data:
            card = Card(**card_data)
            db.session.add(card)
        db.session.commit()
    
    # Verifica se existem tipos de leitura no banco de dados
    if ReadingType.query.count() == 0:
        reading_types = [
            {'name': 'Leitura de Cartas Únicas', 'description': 'Uma carta significativa é extraída para responder sua pergunta'},
            {'name': 'Leitura Espiritual', 'description': 'Explora questões espirituais e propósito de vida'},
            {'name': 'Leitura de Trajetória', 'description': 'Visualiza sua jornada nos próximos meses'},
            {'name': 'Leitura de Correção', 'description': 'Revela informações importantes que você precisa saber'},
            {'name': 'Leitura de Amor', 'description': 'Desvenda o amor em sua vida'},
        ]
        
        for rt_data in reading_types:
            rt = ReadingType(**rt_data)
            db.session.add(rt)
        db.session.commit()

# Configuração do LoginManager
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rota principal
@app.route('/')
def index():
    # Recupera os últimos 5 registros de leitura
    latest_readings = Reading.query.order_by(Reading.date.desc()).limit(5).all()
    
    # Recupera os tipos de leitura mais populares
    popular_reading_types = ReadingType.query.order_by(ReadingType.name).limit(5).all()
    
    return render_template('index.html', 
                         latest_readings=latest_readings,
                         popular_reading_types=popular_reading_types)

# Rota de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha incorretos', 'error')
    
    return render_template('login.html')

# Rota de logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('index'))

# Rota de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Verifica se o usuário já existe
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        
        if existing_user:
            flash('Este nome de usuário ou e-mail já está em uso', 'error')
            return render_template('register.html')
        
        # Cria novo usuário
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            avatar='default_avatar.png'
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        flash('Registro realizado com sucesso! Bem-vindo ao Tarô Online.', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html')

# Rota para criar uma nova leitura
@app.route('/new_reading', methods=['GET', 'POST'])
@login_required
def new_reading():
    if request.method == 'POST':
        reading_type_id = request.form.get('reading_type')
        description = request.form.get('description')
        
        # Seleciona 3 cartas aleatórias
        cards = Card.query.order_by(func.random()).limit(3).all()
        
        # Gera uma interpretação baseada nas cartas
        interpretation = generate_interpretation(cards)
        
        # Salva a leitura
        new_reading = Reading(
            user_id=current_user.id,
            type=reading_type_id,
            description=description,
            result=interpretation
        )
        
        db.session.add(new_reading)
        db.session.commit()
        
        flash('Sua leitura foi registrada com sucesso!', 'success')
        return redirect(url_for('profile'))
    
    reading_types = ReadingType.query.all()
    return render_template('new_reading.html', reading_types=reading_types)

# Gera uma interpretação baseada nas cartas selecionadas
def generate_interpretation(cards):
    interpretation = ""
    for i, card in enumerate(cards):
        interpretation += f"Carta {i+1}: {card.name}\n"
        interpretation += f"Positivo: {card.meaning_up}\n"
        interpretation += f"Negativo: {card.meaning_rev}\n\n"
    
    interpretation += "Interpretação Geral:\n"
    interpretation += "Combinando estas cartas, parece que você está em um período de transformação e crescimento. "
    interpretation += "As energias estão alinhadas para que você tome decisões importantes que o levarão a um caminho positivo. "
    interpretation += "Manter sua intuição e confiar no processo é essencial neste momento."
    
    return interpretation

# Rota para visualizar uma leitura específica
@app.route('/reading/<int:reading_id>')
def reading_detail(reading_id):
    reading = Reading.query.get_or_404(reading_id)
    return render_template('reading_detail.html', reading=reading)

# Rota para o perfil do usuário
@app.route('/profile')
@login_required
def profile():
    user_readings = Reading.query.filter_by(user_id=current_user.id).all()
    user_reviews = Review.query.filter_by(user_id=current_user.id).all()
    
    return render_template('profile.html', 
                         user_readings=user_readings,
                         user_reviews=user_reviews)

# Rota para adicionar uma avaliação
@app.route('/add_review', methods=['POST'])
@login_required
def add_review():
    content = request.form.get('content')
    rating = request.form.get('rating')
    
    new_review = Review(
        user_id=current_user.id,
        content=content,
        rating=rating
    )
    
    db.session.add(new_review)
    db.session.commit()
    
    flash('Sua avaliação foi registrada com sucesso!', 'success')
    return redirect(url_for('index'))

# Rota para deletar uma leitura
@app.route('/delete_reading/<int:reading_id>')
@login_required
def delete_reading(reading_id):
    reading = Reading.query.get_or_404(reading_id)
    
    if reading.user_id != current_user.id:
        flash('Você não tem permissão para excluir esta leitura', 'error')
        return redirect(url_for('profile'))
    
    db.session.delete(reading)
    db.session.commit()
    
    flash('Leitura deletada com sucesso!', 'success')
    return redirect(url_for('profile'))

# Rota para deletar uma avaliação
@app.route('/delete_review/<int:review_id>')
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    
    if review.user_id != current_user.id:
        flash('Você não tem permissão para excluir esta avaliação', 'error')
        return redirect(url_for('profile'))
    
    db.session.delete(review)
    db.session.commit()
    
    flash('Avaliação deletada com sucesso!', 'success')
    return redirect(url_for('profile'))

# Rota para upload de imagem de perfil
@app.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'avatar' not in request.files:
        flash('Nenhuma imagem selecionada', 'error')
        return redirect(url_for('profile'))
    
    file = request.files['avatar']
    
    if file.filename == '':
        flash('Nenhuma imagem selecionada', 'error')
        return redirect(url_for('profile'))
    
    if file:
        filename = f"{current_user.id}_{file.filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        current_user.avatar = filename
        db.session.commit()
        
        flash('Avatar atualizado com sucesso!', 'success')
        return redirect(url_for('profile'))

# Rota para página de revisão de leitura
@app.route('/review_reading/<int:reading_id>', methods=['GET', 'POST'])
@login_required
def review_reading(reading_id):
    reading = Reading.query.get_or_404(reading_id)
    
    if request.method == 'POST':
        rating = request.form.get('rating')
        content = request.form.get('content')
        
        new_review = Review(
            user_id=current_user.id,
            reading_id=reading.id,
            content=content,
            rating=rating
        )
        
        db.session.add(new_review)
        db.session.commit()
        
        flash('Obrigado pela sua avaliação!', 'success')
        return redirect(url_for('reading_detail', reading_id=reading.id))
    
    return render_template('review_reading.html', reading=reading)

# Rota para página de política de privacidade
@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

# Rota para página de termos de serviço
@app.route('/terms')
def terms():
    return render_template('terms.html')

# Rota para página de contato
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Rota para página de como funciona
@app.route('/how-it-works')
def how_it_works():
    return render_template('how_it_works.html')

# Rota para página de FAQs
@app.route('/faqs')
def faqs():
    return render_template('faqs.html')

# Inicialização do banco de dados na primeira execução
if __name__ == '__main__':
    # Cria o diretório de uploads se não existir
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # Cria o banco de dados se não existir
    if not os.path.exists('tarot.db'):
        create_database()
    
    # Inicia o servidor
    app.run(debug=True)