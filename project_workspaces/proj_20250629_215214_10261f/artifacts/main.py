from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from datetime import datetime

# Configurações da aplicação
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pods_vapes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar banco de dados
db = SQLAlchemy(app)

# Gerenciador de usuários
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Modelo de usuário
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

# Modelo de produto
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    stock = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Modelo de pedido
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_price = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Modelo de item do pedido
class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, default=0.0)

# Página inicial
@app.route('/')
def index():
    featured_products = Product.query.filter_by(category='featured').limit(4).all()
    return render_template('index.html', title='Home', products=featured_products)

# Página de produtos
@app.route('/products')
def products():
    products = Product.query.all()
    categories = {'all': 'Todos', 'electronic': 'Eletrônicos', 'pods': 'Pods', 'vapes': 'Vapes', 'accessories': 'Acessórios'}
    return render_template('products.html', title='Produtos', products=products, categories=categories)

# Página de detalhes do produto
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', title=product.name, product=product)

# Página de carrinho
@app.route('/cart')
@login_required
def cart():
    # Lógica para recuperar itens do carrinho do usuário
    return render_template('cart.html', title='Carrinho')

# Página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and current_user.is_authenticated:
        return redirect(url_for('index'))
    # Lógica de login
    return render_template('login.html', title='Login')

# Página de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST' and current_user.is_authenticated:
        return redirect(url_for('index'))
    # Lógica de registro
    return render_template('register.html', title='Registrar')

# Página de checkout
@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'POST':
        # Processar o pedido
        return redirect(url_for('confirmation'))
    return render_template('checkout.html', title='Checkout')

# Página de confirmação
@app.route('/confirmation')
@login_required
def confirmation():
    return render_template('confirmation.html', title='Confirmação de Pedido')

# Página de administração
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    products = Product.query.all()
    return render_template('admin.html', title='Administração', products=products)

# Página de contato
@app.route('/contact')
def contact():
    return render_template('contact.html', title='Contato')

# Erro 404
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

# Inicializar o banco de dados
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
