from flask import Flask, render_template, request, redirect, url_for, flash
import os
import random
from datetime import datetime
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, IntegerField, FileField
from wtforms.validators import DataRequired, Email, Length, NumberRange, InputRequired
from werkzeug.utils import secure_filename
import stripe
from flask_mail import Mail, Message

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

# Configuração do Stripe
stripe.api_key = app.config['STRIPE_SECRET_KEY']

# Configuração de upload de arquivos
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    purchases = db.relationship('TarotPurchase', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)

class TarotCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)

class TarotPurchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('tarot_card.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(100), unique=True, nullable=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('tarot_card.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = StringField('Senha', validators=[DataRequired(), Length(min=4)])
    submit = SubmitField('Entrar')

class RegisterForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(min=3)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = StringField('Senha', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Registrar')

class TarotCardForm(FlaskForm):
    name = StringField('Nome da Carta', validators=[DataRequired(), Length(min=5)])
    description = StringField('Descrição', validators=[DataRequired(), Length(min=10)])
    image = FileField('Imagem da Carta', validators=[InputRequired()])
    price = IntegerField('Preço (em centavos)', validators=[InputRequired(), NumberRange(min=1000)])
    submit = SubmitField('Adicionar Carta')

class PurchaseForm(FlaskForm):
    card_id = SelectField('Escolha uma Carta', coerce=int)
    submit = SubmitField('Comprar')

class ReviewForm(FlaskForm):
    rating = SelectField('Avaliação', coerce=int, choices=[(i, i) for i in range(1, 6)])
    comment = StringField('Comentário', validators=[Length(max=500)])
    submit = SubmitField('Enviar Avaliação')

@app.route('/')
def index():
    featured_cards = TarotCard.query.order_by(TarotCard.id).limit(3).all()
    return render_template('index.html', cards=featured_cards)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Email ou senha incorretos', 'error')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = form.password.data  # Em um sistema real, use hashing
        user = User(name=form.name.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Registro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    cards = TarotCard.query.all()
    purchases = TarotPurchase.query.filter_by(user_id=current_user.id).all()
    reviews = Review.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', cards=cards, purchases=purchases, reviews=reviews)

@app.route('/tarot/<int:card_id>')
def tarot_detail(card_id):
    card = TarotCard.query.get_or_404(card_id)
    return render_template('tarot_detail.html', card=card)

@app.route('/buy/<int:card_id>', methods=['GET', 'POST'])
@login_required
def buy_card(card_id):
    card = TarotCard.query.get_or_404(card_id)
    form = PurchaseForm()
    form.card_id.choices = [(c.id, c.name) for c in TarotCard.query.all()]
    
    if form.validate_on_submit():
        # Criar sessão Stripe
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'brl',
                    'product_name': card.name,
                    'unit_amount': int(card.price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('payment_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('payment_cancel', _external=True),
        )
        
        # Salvar a sessão ID para rastreamento
        new_purchase = TarotPurchase(
            user_id=current_user.id,
            card_id=card.id,
            session_id=session['id']
        )
        db.session.add(new_purchase)
        db.session.commit()
        
        return redirect(session['url'])
    
    return render_template('buy.html', form=form, card=card)

@app.route('/payment-success')
def payment_success():
    session_id = request.args.get('session_id')
    session = stripe.checkout.Session.retrieve(session_id)
    
    # Atualizar saldo do usuário
    card_id = session.metadata.get('card_id')
    card = TarotCard.query.get(card_id)
    current_user.balance += card.price
    db.session.commit()
    
    flash('Pagamento realizado com sucesso! Você ganhou créditos.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/payment-cancel')
def payment_cancel():
    flash('Pagamento cancelado.', 'error')
    return redirect(url_for('dashboard'))

@app.route('/review/<int:card_id>', methods=['GET', 'POST'])
@login_required
def review(card_id):
    card = TarotCard.query.get_or_404(card_id)
    form = ReviewForm()
    
    if form.validate_on_submit():
        existing_review = Review.query.filter_by(user_id=current_user.id, card_id=card_id).first()
        if existing_review:
            flash('Você já deu uma avaliação para esta carta.', 'error')
        else:
            new_review = Review(
                user_id=current_user.id,
                card_id=card_id,
                rating=form.rating.data,
                comment=form.comment.data
            )
            db.session.add(new_review)
            db.session.commit()
            flash('Avaliação enviada com sucesso!', 'success')
            return redirect(url_for('tarot_detail', card_id=card_id))
    
    return render_template('review.html', form=form, card=card)

@app.route('/admin')
@login_required
def admin():
    if current_user.id != 1:  # ID do administrador
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard'))
    
    cards = TarotCard.query.all()
    return render_template('admin.html', cards=cards)

@app.route('/admin/add-card', methods=['GET', 'POST'])
@login_required
def add_card():
    if current_user.id != 1:  # ID do administrador
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard'))
    
    form = TarotCardForm()
    
    if form.validate_on_submit():
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.image.data.save(file_path)
            
            new_card = TarotCard(
                name=form.name.data,
                description=form.description.data,
                image_path=filename,
                price=form.price.data / 100  # Converter de centavos para reais
            )
            db.session.add(new_card)
            db.session.commit()
            
            flash('Carta adicionada com sucesso!', 'success')
            return redirect(url_for('admin'))
    
    return render_template('add_card.html', form=form)

@app.route('/admin/delete-card/<int:card_id>', methods=['POST'])
@login_required
def delete_card(card_id):
    if current_user.id != 1:  # ID do administrador
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard'))
    
    card = TarotCard.query.get_or_404(card_id)
    db.session.delete(card)
    db.session.commit()
    flash('Carta deletada com sucesso!', 'success')
    return redirect(url_for('admin'))

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

if __name__ == '__main__':
    app.run(debug=False)