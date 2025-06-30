import pytest
from unittest.mock import patch, MagicMock
from flask import url_for
from src.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_homepage(client):
    response = client.get(url_for('main.home'))
    assert response.status_code == 200
    assert b"Tarot Card Readings" in response.data

def test_about(client):
    response = client.get(url_for('main.about'))
    assert response.status_code == 200
    assert b"About Our Service" in response.data

def test_readings(client):
    response = client.get(url_for('main.readings'))
    assert response.status_code == 200
    assert b"Tarot Reading Options" in response.data

def test_booking(client):
    response = client.get(url_for('main.booking'))
    assert response.status_code == 200
    assert b"Book Your Reading" in response.data

def test_privacy(client):
    response = client.get(url_for('main.privacy'))
    assert response.status_code == 200
    assert b"Privacy Policy" in response.data

def test_terms(client):
    response = client.get(url_for('main.terms'))
    assert response.status_code == 200
    assert b"Terms of Service" in response.data

def test_payment_failure(client):
    with patch('src.app.payments.process_payment') as mock_process:
        mock_process.side_effect = Exception("Payment failed")
        response = client.post(url_for('main.process_booking'), json={
            'name': 'Test Client',
            'email': 'test@example.com',
            'payment_method': 'credit_card',
            'amount': 50
        })
        assert response.status_code == 400
        assert b"Payment failed" in response.data

def test_payment_success(client):
    with patch('src.app.payments.process_payment') as mock_process:
        mock_process.return_value = True
        response = client.post(url_for('main.process_booking'), json={
            'name': 'Test Client',
            'email': 'test@example.com',
            'payment_method': 'credit_card',
            'amount': 50
        })
        assert response.status_code == 200
        assert b"Booking confirmed" in response.data

def test_read_tarot_cards(client):
    with patch('src.app.tarot_deck.draw_cards') as mock_draw:
        mock_draw.return_value = ['The Fool', 'The Magician', 'The High Priestess']
        response = client.get(url_for('tarot.read_cards'))
        assert response.status_code == 200
        assert b"The Fool" in response.data
        assert b"The Magician" in response.data
        assert b"The High Priestess" in response.data

def test_insufficient_funds(client):
    with patch('src.app.payments.process_payment') as mock_process:
        mock_process.side_effect = Exception("Insufficient funds")
        response = client.post(url_for('main.process_booking'), json={
            'name': 'Test Client',
            'email': 'test@example.com',
            'payment_method': 'credit_card',
            'amount': 50
        })
        assert response.status_code == 400
        assert b"Insufficient funds" in response.data

def test_session_timeout(client):
    response = client.get(url_for('main.reading_result'), follow_redirects=True)
    assert response.status_code == 200
    assert b"Your session has expired" in response.data
    assert url_for('main.home') in response.location

def test_rate_limiting(client):
    with patch('src.app.limiter.limit') as mock_limit:
        mock_limit.return_value = MagicMock()
        mock_limit.return_value.__enter__ = MagicMock()
        mock_limit.return_value.__exit__ = MagicMock()
        for _ in range(20):
            client.post(url_for('main.process_booking'), json={
                'name': 'Test Client',
                'email': 'test@example.com',
                'payment_method': 'credit_card',
                'amount': 50
            })
        response = client.post(url_for('main.process_booking'), json={
            'name': 'Test Client',
            'email': 'test@example.com',
            'payment_method': 'credit_card',
            'amount': 50
        })
        assert response.status_code == 429
        assert b"Too many requests" in response.data