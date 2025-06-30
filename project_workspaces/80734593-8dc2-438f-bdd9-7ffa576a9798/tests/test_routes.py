import pytest
from unittest.mock import patch
from flask import url_for
from app import app, db
from models import User, Divination, Card, Reading

@pytest.fixture
def test_client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['SECRET_KEY'] = 'testsecret'
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()

@pytest.fixture
def init_database(test_client):
    with app.app_context():
        db.create_all()
        yield
        db.drop_all()

@pytest.fixture
def test_user():
    with app.app_context():
        user = User(username='testuser', email='test@example.com', password='testpassword')
        db.session.add(user)
        db.session.commit()
        yield user
        db.session.delete(user)
        db.session.commit()

@pytest.fixture
def mock_tarot_deck():
    with patch('adivinhacao.tarot_deck') as mock_deck:
        yield mock_deck

def test_homepage(test_client):
    response = test_client.get(url_for('home'))
    assert response.status_code == 200
    assert b'Bem-vindo ao Portal da Sabedoria Tarot' in response.data

def test_about_page(test_client):
    response = test_client.get(url_for('about'))
    assert response.status_code == 200
    assert b'Acreditamos em práticas éticas' in response.data

def test_divination_page(test_client, test_user):
    login_response = test_client.post(url_for('login'), 
                                      data=dict(email='test@example.com', password='testpassword'),
                                      follow_redirects=True)
    assert login_response.status_code == 200
    
    response = test_client.get(url_for('divination'))
    assert response.status_code == 200
    assert b'Escolha o número de cartas para sua leitura' in response.data

def test_make_divination(test_client, test_user, mock_tarot_deck):
    login_response = test_client.post(url_for('login'), 
                                      data=dict(email='test@example.com', password='testpassword'),
                                      follow_redirects=True)
    assert login_response.status_code == 200
    
    response = test_client.post(url_for('divination'), 
                               data=dict(num_cartas=3, submit='Realizar Leitura'),
                               follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Seu resultado de leitura Tarot' in response.data
    assert mock_tarot_deck.draw_card.called

def test_payment_process(test_client, test_user):
    login_response = test_client.post(url_for('login'), 
                                      data=dict(email='test@example.com', password='testpassword'),
                                      follow_redirects=True)
    assert login_response.status_code == 200
    
    # First get to divination page
    divination_response = test_client.get(url_for('divination'))
    assert divination_response.status_code == 200
    
    # Submit divination
    divination_post = test_client.post(url_for('divination'), 
                                       data=dict(num_cartas=3, submit='Realizar Leitura'),
                                       follow_redirects=True)
    assert divination_post.status_code == 200
    
    # Find the payment link in the response
    payment_link = None
    for link in divination_post.get_data(as_text=True).split():
        if 'pagar' in link:
            payment_link = link
            break
    
    assert payment_link is not None
    
    # Test payment processing
    with patch('adivinhacao.process_payment') as mock_process:
        mock_process.return_value = True
        payment_response = test_client.post(payment_link, 
                                          data=dict(card='1234-5678-9012-3456', 
                                                   expiry='12/25', 
                                                   cvv='123', 
                                                   amount=10.00),
                                          follow_redirects=True)
        
        assert payment_response.status_code == 200
        assert b'Pagamento processado com sucesso!' in payment_response.data
        assert mock_process.called

def test_results_page(test_client, test_user):
    login_response = test_client.post(url_for('login'), 
                                      data=dict(email='test@example.com', password='testpassword'),
                                      follow_redirects=True)
    assert login_response.status_code == 200
    
    # Submit divination
    divination_post = test_client.post(url_for('divination'), 
                                       data=dict(num_cartas=3, submit='Realizar Leitura'),
                                       follow_redirects=True)
    
    # Find the results link
    results_link = None
    for link in divination_post.get_data(as_text=True).split():
        if 'ver_resultado' in link:
            results_link = link
            break
    
    assert results_link is not None
    
    # Test results page
    results_response = test_client.get(results_link)
    assert results_response.status_code == 200
    assert b'Resultado da sua leitura Tarot' in results_response.data

def test_privacy_policy(test_client):
    response = test_client.get(url_for('privacy'))
    assert response.status_code == 200
    assert b'Política de Privacidade' in response.data
    assert b'proteção de dados' in response.data

def test_terms_of_service(test_client):
    response = test_client.get(url_for('terms'))
    assert response.status_code == 200
    assert b'Termos de Serviço' in response.data
    assert b'limitação de responsabilidade' in response.data

def test_admin_page(test_client, test_user):
    login_response = test_client.post(url_for('login'), 
                                      data=dict(email='test@example.com', password='testpassword'),
                                      follow_redirects=True)
    assert login_response.status_code == 200
    
    response = test_client.get(url_for('admin'), 
                              data=dict(username='testuser'))
    assert response.status_code == 200
    assert b'Administração do Sistema' in response.data