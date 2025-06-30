from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vapes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelagem do banco de dados
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    orders = db.relationship('Order', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)

# Criação das tabelas
with app.app_context():
    db.create_all()

# Templates HTML
index_template = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VapeStore - Sua loja de vapes e atomizadores</title>
    <style>
        /* Estilos gerais */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Arial', sans-serif;
        }

        body {
            background-color: #f8f9fa;
            color: #333;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }

        /* Header */
        header {
            background-color: #2c3e50;
            color: white;
            padding: 15px 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            font-size: 24px;
            font-weight: bold;
        }

        nav ul {
            display: flex;
            list-style: none;
        }

        nav ul li {
            margin-left: 20px;
        }

        nav ul li a {
            color: white;
            text-decoration: none;
            transition: color 0.3s;
        }

        nav ul li a:hover {
            color: #f39c12;
        }

        .cart-icon {
            position: relative;
            cursor: pointer;
        }

        .cart-count {
            position: absolute;
            top: -10px;
            right: -10px;
            background-color: #e74c3c;
            color: white;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 12px;
        }

        /* Hero Section */
        .hero {
            background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://via.placeholder.com/1500x500');
            background-size: cover;
            background-position: center;
            height: 500px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            color: white;
        }

        .hero-content h1 {
            font-size: 48px;
            margin-bottom: 20px;
        }

        .hero-content p {
            font-size: 20px;
            margin-bottom: 30px;
        }

        .btn {
            display: inline-block;
            background-color: #f39c12;
            color: white;
            padding: 12px 30px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            transition: background-color 0.3s;
        }

        .btn:hover {
            background-color: #e67e22;
        }

        /* Produtos */
        .products {
            padding: 50px 0;
        }

        .section-title {
            text-align: center;
            margin-bottom: 40px;
            color: #2c3e50;
        }

        .product-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 30px;
        }

        .product-card {
            background-color: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }

        .product-card:hover {
            transform: translateY(-10px);
        }

        .product-image {
            height: 200px;
            width: 100%;
            object-fit: cover;
        }

        .product-info {
            padding: 20px;
        }

        .product-name {
            font-size: 18px;
            margin-bottom: 10px;
        }

        .product-description {
            color: #7f8c8d;
            margin-bottom: 15px;
            font-size: 14px;
        }

        .product-price {
            font-size: 20px;
            font-weight: bold;
            color: #e74c3c;
            margin-bottom: 15px;
        }

        .add-to-cart {
            width: 100%;
            padding: 10px;
            background-color: #2c3e50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s;
        }

        .add-to-cart:hover {
            background-color: #1a252f;
        }

        /* Categorias */
        .categories {
            padding: 50px 0;
            background-color: #ecf0f1;
        }

        .category-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
        }

        .category-card {
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }

        .category-card:hover {
            transform: translateY(-5px);
        }

        .category-icon {
            font-size: 40px;
            margin-bottom: 15px;
            color: #2c3e50;
        }

        /* Footer */
        footer {
            background-color: #2c3e50;
            color: white;
            padding: 50px 0 20px;
        }

        .footer-content {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }

        .footer-column h3 {
            margin-bottom: 20px;
            font-size: 18px;
        }

        .footer-column ul {
            list-style: none;
        }

        .footer-column ul li {
            margin-bottom: 10px;
        }

        .footer-column ul li a {
            color: #bdc3c7;
            text-decoration: none;
            transition: color 0.3s;
        }

        .footer-column ul li a:hover {
            color: #f39c12;
        }

        .copyright {
            text-align: center;
            padding-top: 20px;
            border-top: 1px solid #34495e;
            color: #bdc3c7;
        }

        /* Modal de Login */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0,0,0,0.4);
        }

        .modal-content {
            background-color: white;
            margin: 10% auto;
            padding: 20px;
            border-radius: 8px;
            width: 400px;
            max-width: 90%;
        }

        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }

        .close:hover {
            color: black;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 5px;
        }

        .form-group input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }

        /* Responsividade */
        @media (max-width: 768px) {
            .header-content {
                flex-direction: column;
            }

            nav ul {
                margin-top: 15px;
            }

            .hero-content h1 {
                font-size: 36px;
            }
        }
    </style>
</head>
<body>
    <!-- Modal de Login -->
    <div id="loginModal" class="modal">
        <div class="modal-content">
            <span class="close">&times;</span>
            <h2>Login</h2>
            <form id="loginForm">
                <div class="form-group">
                    <label for="loginEmail">Email</label>
                    <input type="email" id="loginEmail" required>
                </div>
                <div class="form-group">
                    <label for="loginPassword">Senha</label>
                    <input type="password" id="loginPassword" required>
                </div>
                <button type="submit" class="btn">Entrar</button>
            </form>
        </div>
    </div>

    <!-- Modal de Registro -->
    <div id="registerModal" class="modal">
        <div class="modal-content">
            <span class="close">&times;</span>
            <h2>Cadastro</h2>
            <form id="registerForm">
                <div class="form-group">
                    <label for="registerName">Nome</label>
                    <input type="text" id="registerName" required>
                </div>
                <div class="form-group">
                    <label for="registerEmail">Email</label>
                    <input type="email" id="registerEmail" required>
                </div>
                <div class="form-group">
                    <label for="registerPassword">Senha</label>
                    <input type="password" id="registerPassword" required>
                </div>
                <button type="submit" class="btn">Cadastrar</button>
            </form>
        </div>
    </div>

    <!-- Header -->
    <header>
        <div class="container header-content">
            <div class="logo">VapeStore</div>
            <nav>
                <ul>
                    <li><a href="{{ url_for('index') }}">Home</a></li>
                    <li><a href="{{ url_for('products') }}">Produtos</a></li>
                    <li><a href="{{ url_for('categories') }}">Categorias</a></li>
                    <li><a href="{{ url_for('about') }}">Sobre</a></li>
                    <li><a href="{{ url_for('contact') }}">Contato</a></li>
                    <li class="cart-icon">
                        <a href="{{ url_for('cart') }}">🛒</a>
                        <span id="cart-count" class="cart-count">{{ session.get('cart_count', 0) }}</span>
                    </li>
                </ul>
            </nav>
        </div>
    </header>

    <!-- Hero Section -->
    <section class="hero">
        <div class="hero-content">
            <h1>Explore o mundo dos vapes</h1>
            <p>Descubra nossa coleção exclusiva de produtos de vape e atomizadores</p>
            <a href="{{ url_for('products') }}" class="btn">Comprar Agora</a>
        </div>
    </section>

    <!-- Produtos -->
    <section class="products">
        <div class="container">
            <h2 class="section-title">Nossos Produtos</h2>
            <div class="product-grid">
                {% for product in products %}
                <div class="product-card">
                    <img src="{{ product.image_url or 'https://via.placeholder.com/300' }}" alt="{{ product.name }}" class="product-image">
                    <div class="product-info">
                        <h3 class="product-name">{{ product.name }}</h3>
                        <p class="product-description">{{ product.description }}</p>
                        <p class="product-price">R$ {{ product.price }}</p>
                        <button class="add-to-cart" onclick="addToCart({{ product.id }})">Adicionar ao Carrinho</button>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </section>

    <!-- Categorias -->
    <section class="categories">
        <div class="container">
            <h2 class="section-title">Nossas Categorias</h2>
            <div class="category-grid">
                <div class="category-card">
                    <div class="category-icon">🚬</div>
                    <h3>Vapes</h3>
                    <p>Dispositivos de vape de alta qualidade</p>
                </div>
                <div class="category-card">
                    <div class="category-icon">💨</div>
                    <h3>Atomizadores</h3>
                    <p>Atomizadores para óleo canábico</p>
                </div>
                <div class="category-card">
                    <div class="category-icon">💧</div>
                    <h3>Liquidos</h3>
                    <p>Vários sabores e concentrações</p>
                </div>
                <div class="category-card">
                    <div class="category-icon">🔋</div>
                    <h3>Baterias</h3>
                    <p>Baterias de longa duração</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer>
        <div class="container">
            <div class="footer-content">
                <div class="footer-column">
                    <h3>VapeStore</h3>
                    <p>A sua loja especializada em produtos de vape e atomizadores de óleo canábico.</p>
                </div>
                <div class="footer-column">
                    <h3>Links Rápidos</h3>
                    <ul>
                        <li><a href="{{ url_for('index') }}">Home</a></li>
                        <li><a href="{{ url_for('products') }}">Produtos</a></li>
                        <li><a href="{{ url_for('categories') }}">Categorias</a></li>
                        <li><a href="{{ url_for('about') }}">Sobre Nós</a></li>
                    </ul>
                </div>
                <div class="footer-column">
                    <h3>Contato</h3>
                    <ul>
                        <li>Email: contato@vapystore.com</li>
                        <li>Telefone: (11) 9999-9999</li>
                        <li>Endereço: Av. das Lojas, 1000 - SP</li>
                    </ul>
                </div>
            </div>
            <div class="copyright">
                <p>&copy; {{ current_year }} VapeStore. Todos os direitos reservados.</p>
            </div>
        </div>
    </footer>

    <script>
        // Função para abrir o modal de login
        function openLoginModal() {
            document.getElementById('loginModal').style.display = 'block';
        }

        // Função para abrir o modal de registro
        function openRegisterModal() {
            document.getElementById('registerModal').style.display = 'block';
        }

        // Função para fechar os modais
        function closeModals() {
            document.getElementById('loginModal').style.display = 'none';
            document.getElementById('registerModal').style.display = 'none';
        }

        // Função para adicionar ao carrinho
        function addToCart(productId) {
            // Incrementa a quantidade no carrinho
            let cart = JSON.parse(localStorage.getItem('cart')) || {};
            if (cart[productId]) {
                cart[productId].quantity += 1;
            } else {
                // Busca o produto do banco de dados
                const product = Product.query.get(productId);
                if (product) {
                    cart[productId] = {
                        id: product.id,
                        name: product.name,
                        price: product.price,
                        quantity: 1
                    };
                }
            }
            localStorage.setItem('cart', JSON.stringify(cart));
            updateCartCount();
            alert('Produto adicionado ao carrinho!');
        }

        // Atualiza o contador do carrinho
        function updateCartCount() {
            const cart = JSON.parse(localStorage.getItem('cart')) || {};
            const totalItems = Object.values(cart).reduce((sum, item) => sum + item.quantity, 0);
            document.getElementById('cart-count').textContent = totalItems;
        }

        // Verifica se o usuário está logado
        function checkLogin() {
            if (!session.get('logged_in', False)) {
                document.querySelector('.cart-icon a').addEventListener('click', openLoginModal);
            }
        }

        // Event listeners
        document.addEventListener('DOMContentLoaded', function() {
            // Fechar modais ao clicar fora deles
            window.onclick = function(event) {
                const loginModal = document.getElementById('loginModal');
                const registerModal = document.getElementById('registerModal');
                if (event.target == loginModal) {
                    closeModals();
                }
                if (event.target == registerModal) {
                    closeModals();
                }
            };

            // Verifica login
            checkLogin();

            // Inicializa o contador do carrinho
            updateCartCount();
        });
    </script>
</body>
</html>
'''

# Rotas da aplicação
@app.route('/')
def index():
    return render_template_string(index_template)

@app.route('/products')
def products():
    # Simulando a consulta ao banco de dados
    products_data = [
        {
            'id': 1,
            'name': 'Vape X-Tech',
            'description': 'Dispositivo de vape com tecnologia avançada',
            'price': 199.90,
            'category': 'vapes',
            'image_url': 'https://via.placeholder.com/300'
        },
        {
            'id': 2,
            'name': 'Atomizador Pro',
            'description': 'Atomizador de óleo canábico de alta qualidade',
            'price': 89.90,
            'category': 'atomizadores',
            'image_url': 'https://via.placeholder.com/300'
        },
        {
            'id': 3,
            'name': 'Líquido Original',
            'description': 'Líquido para vape com sabor neutro',
            'price': 49.90,
            'category': 'liquidos',
            'image_url': 'https://via.placeholder.com/300'
        },
        {
            'id': 4,
            'name': 'Bateria Max',
            'description': 'Bateria de longa duração para vapes',
            'price': 79.90,
            'category': 'baterias',
            'image_url': 'https://via.placeholder.com/300'
        }
    ]
    return render_template_string(index_template, products=products_data, current_year=datetime.now().year)

@app.route('/categories')
def categories():
    return render_template_string(index_template, current_year=datetime.now().year)

@app.route('/about')
def about():
    return render_template_string(index_template, current_year=datetime.now().year)

@app.route('/contact')
def contact():
    return render_template_string(index_template, current_year=datetime.now().year)

@app.route('/cart')
def cart():
    return render_template_string(index_template, current_year=datetime.now().year)

if __name__ == '__main__':
    app.run(debug=True)