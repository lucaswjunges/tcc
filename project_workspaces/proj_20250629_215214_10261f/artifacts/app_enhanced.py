from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import json

# Configurações da aplicação
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'vapeshop-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///vapeshop.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

# Criar pasta de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inicializar extensões
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Faça login para acessar esta página.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Modelos do banco de dados
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    orders = db.relationship('Order', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    products = db.relationship('Product', backref='category_obj', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    short_description = db.Column(db.String(200), nullable=True)
    price = db.Column(db.Float, nullable=False)
    original_price = db.Column(db.Float, nullable=True)  # Para promoções
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    stock = db.Column(db.Integer, default=0)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    weight = db.Column(db.Float, nullable=True)  # em gramas
    dimensions = db.Column(db.String(100), nullable=True)  # formato: "10x5x2 cm"
    tags = db.Column(db.Text, nullable=True)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def category(self):
        return self.category_obj.slug if self.category_obj else 'uncategorized'
    
    @property
    def is_on_sale(self):
        return self.original_price and self.original_price > self.price
    
    @property
    def discount_percentage(self):
        if self.is_on_sale:
            return int(((self.original_price - self.price) / self.original_price) * 100)
        return 0

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_price = db.Column(db.Float, default=0.0)
    shipping_cost = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, shipped, delivered, cancelled
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, failed, refunded
    payment_method = db.Column(db.String(20), nullable=True)  # credit_card, debit_card, pix, boleto
    
    # Endereço de entrega
    shipping_name = db.Column(db.String(100), nullable=False)
    shipping_address = db.Column(db.String(200), nullable=False)
    shipping_city = db.Column(db.String(50), nullable=False)
    shipping_state = db.Column(db.String(2), nullable=False)
    shipping_zip = db.Column(db.String(10), nullable=False)
    shipping_phone = db.Column(db.String(20), nullable=True)
    
    tracking_code = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    @property
    def final_total(self):
        return self.total_price + self.shipping_cost

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, default=0.0)
    total_price = db.Column(db.Float, default=0.0)
    
    # Relacionamentos
    product = db.relationship('Product', backref='order_items')

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    product = db.relationship('Product', backref='cart_items')
    user = db.relationship('User', backref='cart_items')

# Rotas principais
@app.route('/')
def index():
    featured_products = Product.query.filter_by(is_featured=True, is_active=True).limit(8).all()
    categories = Category.query.all()
    return render_template('index.html', 
                         products=featured_products, 
                         categories=categories,
                         title='Início')

@app.route('/products')
def products():
    category_filter = request.args.get('category', 'all')
    sort_by = request.args.get('sort', 'name')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Query base
    query = Product.query.filter_by(is_active=True)
    
    # Filtro por categoria
    if category_filter != 'all':
        category = Category.query.filter_by(slug=category_filter).first()
        if category:
            query = query.filter_by(category_id=category.id)
    
    # Ordenação
    if sort_by == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'newest':
        query = query.order_by(Product.created_at.desc())
    else:
        query = query.order_by(Product.name.asc())
    
    # Paginação
    products_paginated = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    categories = Category.query.all()
    categories_dict = {cat.slug: cat.name for cat in categories}
    categories_dict['all'] = 'Todas as Categorias'
    
    return render_template('products.html', 
                         products=products_paginated.items,
                         pagination=products_paginated,
                         categories=categories_dict,
                         current_category=category_filter,
                         current_sort=sort_by,
                         title='Produtos')

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()
    
    return render_template('product_detail.html', 
                         product=product,
                         related_products=related_products,
                         title=product.name)

@app.route('/cart')
def cart():
    if current_user.is_authenticated:
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        total = sum(item.product.price * item.quantity for item in cart_items)
    else:
        cart_items = []
        total = 0
    
    return render_template('cart.html', 
                         cart_items=cart_items,
                         total=total,
                         title='Carrinho')

@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity', 1)
    
    product = Product.query.get_or_404(product_id)
    
    # Verifica estoque
    if product.stock < quantity:
        return jsonify({'success': False, 'message': 'Estoque insuficiente'})
    
    # Verifica se já existe no carrinho
    cart_item = CartItem.query.filter_by(
        user_id=current_user.id, 
        product_id=product_id
    ).first()
    
    if cart_item:
        if cart_item.quantity + quantity > product.stock:
            return jsonify({'success': False, 'message': 'Estoque insuficiente'})
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)
    
    db.session.commit()
    
    # Calcula total do carrinho
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    cart_total = sum(item.product.price * item.quantity for item in cart_items)
    cart_count = sum(item.quantity for item in cart_items)
    
    return jsonify({
        'success': True, 
        'message': 'Produto adicionado ao carrinho',
        'cart_count': cart_count,
        'cart_total': cart_total
    })

@app.route('/remove_from_cart', methods=['POST'])
@login_required
def remove_from_cart():
    cart_item_id = request.json.get('cart_item_id')
    cart_item = CartItem.query.filter_by(
        id=cart_item_id, 
        user_id=current_user.id
    ).first_or_404()
    
    db.session.delete(cart_item)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Item removido do carrinho'})

@app.route('/update_cart', methods=['POST'])
@login_required
def update_cart():
    cart_item_id = request.json.get('cart_item_id')
    quantity = request.json.get('quantity')
    
    cart_item = CartItem.query.filter_by(
        id=cart_item_id, 
        user_id=current_user.id
    ).first_or_404()
    
    if quantity <= 0:
        db.session.delete(cart_item)
    else:
        if quantity > cart_item.product.stock:
            return jsonify({'success': False, 'message': 'Estoque insuficiente'})
        cart_item.quantity = quantity
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Carrinho atualizado'})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash('Login realizado com sucesso!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        
        flash('Usuário ou senha incorretos.', 'error')
    
    return render_template('login.html', title='Login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validações
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe.', 'error')
            return render_template('register.html', title='Registrar')
        
        if User.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.', 'error')
            return render_template('register.html', title='Registrar')
        
        if password != confirm_password:
            flash('Senhas não coincidem.', 'error')
            return render_template('register.html', title='Registrar')
        
        # Criar usuário
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Conta criada com sucesso! Faça login para continuar.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Registrar')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('index'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    if not cart_items:
        flash('Seu carrinho está vazio.', 'warning')
        return redirect(url_for('cart'))
    
    if request.method == 'POST':
        # Processar pedido
        order = Order(
            user_id=current_user.id,
            shipping_name=request.form['shipping_name'],
            shipping_address=request.form['shipping_address'],
            shipping_city=request.form['shipping_city'],
            shipping_state=request.form['shipping_state'],
            shipping_zip=request.form['shipping_zip'],
            shipping_phone=request.form.get('shipping_phone'),
            payment_method=request.form['payment_method']
        )
        
        total = 0
        for cart_item in cart_items:
            order_item = OrderItem(
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                unit_price=cart_item.product.price,
                total_price=cart_item.product.price * cart_item.quantity
            )
            order.items.append(order_item)
            total += order_item.total_price
            
            # Atualizar estoque
            cart_item.product.stock -= cart_item.quantity
        
        order.total_price = total
        order.shipping_cost = 15.00 if total < 100 else 0  # Frete grátis acima de R$ 100
        
        db.session.add(order)
        
        # Limpar carrinho
        for cart_item in cart_items:
            db.session.delete(cart_item)
        
        db.session.commit()
        
        flash('Pedido realizado com sucesso!', 'success')
        return redirect(url_for('order_confirmation', order_id=order.id))
    
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    shipping = 15.00 if subtotal < 100 else 0
    total = subtotal + shipping
    
    return render_template('checkout.html', 
                         cart_items=cart_items,
                         subtotal=subtotal,
                         shipping=shipping,
                         total=total,
                         title='Checkout')

@app.route('/order/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template('order_confirmation.html', order=order, title='Confirmação do Pedido')

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    products = Product.query.all()
    orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    users_count = User.query.count()
    products_count = Product.query.count()
    orders_count = Order.query.count()
    
    return render_template('admin.html', 
                         products=products,
                         orders=orders,
                         stats={
                             'users': users_count,
                             'products': products_count,
                             'orders': orders_count
                         },
                         title='Administração')

@app.route('/contact')
def contact():
    return render_template('contact.html', title='Contato')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', title='Página não encontrada'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html', title='Erro interno'), 500

# Função para criar dados de exemplo
def create_sample_data():
    if Category.query.count() == 0:
        categories = [
            Category(name='Pods Descartáveis', slug='pods', description='Pods descartáveis de alta qualidade'),
            Category(name='Vapes', slug='vapes', description='Vaporizers e mods'),
            Category(name='E-líquidos', slug='liquids', description='E-líquidos e essências'),
            Category(name='Acessórios', slug='accessories', description='Acessórios e peças')
        ]
        
        for category in categories:
            db.session.add(category)
        
        db.session.commit()
        
        # Produtos de exemplo
        products = [
            Product(name='Pod Descartável Mango Ice', description='Pod descartável sabor manga com gelo, 600 puffs', 
                   price=29.90, category_id=1, stock=50, sku='POD001', is_featured=True),
            Product(name='Vape Mod Zeus', description='Mod Zeus com controle de temperatura e bateria de longa duração', 
                   price=189.90, category_id=2, stock=25, sku='VAPE001', is_featured=True),
            Product(name='E-líquido Strawberry', description='E-líquido sabor morango 30ml', 
                   price=19.90, category_id=3, stock=100, sku='LIQ001'),
            Product(name='Coil Mesh 0.4ohm', description='Resistência mesh 0.4ohm para melhor sabor', 
                   price=9.90, category_id=4, stock=200, sku='ACC001')
        ]
        
        for product in products:
            db.session.add(product)
        
        # Usuário admin
        admin_user = User(
            username='admin',
            email='admin@vapeshop.com',
            first_name='Admin',
            last_name='User',
            is_admin=True
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        
        db.session.commit()

# Inicializar banco de dados
with app.app_context():
    db.create_all()
    create_sample_data()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)