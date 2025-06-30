from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Modelo de usuário
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))
    is_admin = db.Column(db.Boolean, default=False)

# Modelo de produto
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)

# Criação das tabelas
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rota para a página inicial
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', title='Home')

# Rota para listar produtos
@app.route('/products')
def products():
    return render_template('products.html', title='Produtos')

# Rota para o carrinho
@app.route('/cart')
@login_required
def cart():
    return render_template('cart.html', title='Carrinho')

# Rota para o login
@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html', title='Entrar')

# Rota para o logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Rota para o cadastro
@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html', title='Registrar')

# Rota para detalhes do produto
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    return render_template('product_detail.html', title='Detalhes do Produto')

# Rota para checkout
@app.route('/checkout')
@login_required
def checkout():
    return render_template('checkout.html', title='Checkout')

# Rota para admin
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        return redirect(url_for('home'))
    return render_template('admin.html', title='Admin Panel')

if __name__ == '__main__':
    app.run(debug=True)