import pytest
from unittest.mock import patch, MagicMock
from backend import app, db, User, Product
from backend.models import Product, User
from backend.auth import requires_auth

test_server_host = "localhost"
test_server_port = 5000

test_user_credentials = {
    "username": "testuser",
    "password": "TestPass123"
}

test_product_data = {
    "name": "Test Product",
    "description": "Test Description",
    "price": 19.99,
    "stock": 10
}

test_update_product_data = {
    "name": "Updated Product",
    "price": 24.99
}

# Fixtures
@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.create_all()
    with app.test_client() as client:
        yield client
    db.session.remove()
    db.drop_all()

@pytest.fixture
def auth_headers(client):
    with client.application.app_context():
        user = User(**test_user_credentials)
        db.session.add(user)
        db.session.commit()
        token = user.generate_token()
    return {"Authorization": f"Bearer {token}"}

test_data = [
    ("POST", "/api/auth/login", {"username": "testuser", "password": "TestPass123"}, 200),
    ("POST", "/api/auth/register", {"username": "newuser", "password": "NewPass123", "email": "new@example.com"}, 201),
    ("GET", "/api/products", None, 200),
    ("GET", "/api/products/1", None, 200),
    ("POST", "/api/products", test_product_data, 201),
    ("PUT", "/api/products/1", test_update_product_data, 200),
    ("DELETE", "/api/products/1", None, 200)
]

@patch("backend.auth.requires_auth")
def test_authenticated_endpoints(client, auth_headers, requires_auth_mock):
    requires_auth_mock.return_value = lambda f: f
    
    for method, url, data, expected_code in test_data:
        if method == "POST" or method == "PUT" or method == "DELETE":
            response = client.post(url, json=data, headers=auth_headers)
        else:
            response = client.get(url, headers=auth_headers)
        
        assert response.status_code == expected_code

@patch("backend.auth.requires_auth")
def test_unauthenticated_endpoints(client, requires_auth_mock):
    requires_auth_mock.side_effect = lambda f: lambda *args, **kwargs: f(*args, **kwargs)
    
    test_unprotected_endpoints = [
        ("GET", "/api/products"),
        ("GET", "/api/products/1")
    ]
    
    for method, url in test_unprotected_endpoints:
        response = client.get(url)
        assert response.status_code == 200

def test_product_model_creation(client):
    with client.application.app_context():
        new_product = Product(**test_product_data)
        db.session.add(new_product)
        db.session.commit()
        assert new_product in db.session
        assert isinstance(new_product, Product)
        assert new_product.name == "Test Product"

@patch("backend.models.User.query")
def test_user_model_creation(mock_query, client):
    mock_get = MagicMock()
    mock_get.return_value = None
    mock_query.filter_by.return_value.first = mock_get
    
    with client.application.app_context():
        new_user = User(**test_user_credentials)
        assert new_user.username == "testuser"
        assert new_user.verify_password("TestPass123")
        assert new_user.is_authenticated()

@patch("backend.auth.requests.post")
def test_auth_integration(mock_post, client, auth_headers):
    mock_post.return_value.status_code = 200
    with client.application.app_context():
        with patch("backend.auth.current_app") as mock_app:
            mock_app.config = MagicMock()
            mock_app.config["AUTH0_DOMAIN"] = "test.auth0.com"
            mock_app.config["AUTH0_CLIENT_ID"] = "test_client_id"
            mock_app.config["AUTH0_CLIENT_SECRET"] = "test_secret"
            mock_app.config["AUTH0_AUDIENCE"] = "test_audience"
            mock_app.test = MagicMock()
            
            response = requires_auth(lambda: True)(MagicMock())
            assert mock_post.call_count == 1
            assert response.status_code == 200

@patch("backend.models.Product.query")
def test_product_crud_operations(mock_query, client):
    mock_filter = MagicMock()
    mock_all = MagicMock()
    mock_first = MagicMock()
    mock_all.return_value = [MagicMock(id=1)]
    mock_first.return_value = MagicMock(id=1)
    
    mock_query.filter_by = MagicMock()
    mock_query.filter_by.return_value = mock_filter
    mock_filter.all = MagicMock(return_value=[MagicMock(id=1)])
    mock_filter.first = MagicMock(return_value=MagicMock(id=1))
    
    with client.application.app_context():
        # Test GET all products
        assert mock_query.filter_by.call_args_list[0][0] == ("visible",)
        
        # Test GET product by id
        assert mock_query.filter_by.call_args_list[1][0] == ("visible",)
        
        # Test POST create product
        db.session.add(MagicMock())
        db.session.commit()
        
        # Test PUT update product
        existing_product = MagicMock()
        existing_product.update.return_value = True
        
        # Test DELETE product
        existing_product.delete.return_value = True
