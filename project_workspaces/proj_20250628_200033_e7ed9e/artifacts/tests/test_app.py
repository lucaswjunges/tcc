import pytest
from unittest.mock import patch, MagicMock
from backend.models import Product, User, Order
from backend.app import app
from backend.auth import hash_password

# Fixture para criar uma aplicação de teste
@pytest.fixture
def test_app():
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        WTF_CSRF_ENABLED=False
    )
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

db = SQLAlchemy(app)

# Gerar dados de teste
@pytest.fixture
def test_products():
    return [
        Product(id=1, name="Pod 1", description="Primeira pod", price=10.99, stock=10),
        Product(id=2, name="Pod 2", description="Segunda pod", price=15.99, stock=5)
    ]

# Testes de Modelos
@pytest.mark.models
@pytest.mark.parametrize("product_data", [
    ({"name": "Pod Test", "description": "Teste", "price": 19.99, "stock": 5}),
    pytest.param(
        {"name": "", "description": "Teste", "price": 0, "stock": -1},
        marks=pytest.mark.xfail(reason="Campos inválidos não podem ser salvos automaticamente")
    )
])
def test_product_model(product_data):
    product = Product(**product_data)
    assert product.name == product_data["name"]
    assert product.description == product_data["description"]
    assert product.price == product_data["price"]
    assert product.stock == product_data["stock"]

@pytest.mark.models
@pytest.mark.parametrize("user_data", [
    ({"username": "testuser", "email": "test@example.com", "password": "testpass"}),
    pytest.param(
        {"username": "", "email": "test@example.com", "password": "testpass"},
        marks=pytest.mark.xfail(reason="Username obrigatório")
    )
])
def test_user_model(user_data):
    user = User(**user_data)
    assert user.username == user_data["username"]
    assert user.email == user_data["email"]
    assert user.password_hash.startswith("$2b$12$")  # bcrypt hash format

# Testes de API
@pytest.mark.api
def test_product_list(test_app):
    client = test_app.test_client()
    response = client.get("/products")
    assert response.status_code == 200
    assert b"Vape Shop" in response.data

@pytest.mark.api
@patch("backend.app.Product.query")
def test_search_products(mock_query):
    mock_query.filter_by.return_value.all.return_value = [
        Product(id=1, name="Pod 1", description="Primeira pod", price=10.99, stock=10)
    ]
    with app.test_request_context("/products?search=pod"):
        products = Product.query.filter_by(name="pode aqui")
        assert len(products.all()) == 1

# Testes de Autenticação
@pytest.mark.auth
def test_user_registration(test_app):
    client = test_app.test_client()
    response = client.post(
        "register",
        data={
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpassword"
        }
    )
    assert response.status_code == 302

@pytest.mark.auth
def test_user_login(test_app):
    client = test_app.test_client()
    response = client.post(
        "login",
        data={
            "username": "testuser",
            "password": "testpass"
        }
    )
    assert "Login realizado com sucesso" in response.get_data(as_text=True)

# Testes de Cobertura
@pytest.mark.coverage
def test_order_model_creation():
    user = User(username="testuser", email="test@example.com", password_hash="testpass")
    product = Product(id=1)
    order = Order(user_id=user.id, product_id=product.id, quantity=2)
    assert order.user_id == user.id
    assert order.product_id == product.id
    assert order.quantity == 2

# Casos de teste para senhas
@pytest.mark.security
def test_password_hashing():
    plain_password = "securepassword123"
    hashed = hash_password(plain_password)
    assert hashed != plain_password
    assert hashed.startswith("$2b$12$")