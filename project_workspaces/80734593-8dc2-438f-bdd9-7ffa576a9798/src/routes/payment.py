from flask import Blueprint, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
import os
import stripe
from datetime import datetime, timedelta
from .models import User, Transaction, Reading
from . import db
from .email_service import send_payment_receipt

payment_bp = Blueprint('payment', __name__)

# Configure Stripe with your secret key
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Create a Stripe PaymentIntent as a test
# This would be replaced with actual payment processing in production
def create_stripe_payment(amount, currency='brl'):
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=amount * 100,  # Stripe expects amount in cents
            currency=currency,
            payment_method_types=['card'],
            description='Tarot Reading Service'
        )
        return payment_intent
    except Exception as e:
        print(f"Stripe Payment Error: {str(e)}")
        return None

@payment_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    try:
        # Get the price from query parameters
        price_id = request.form.get('price_id')
        if not price_id:
            return jsonify(error="Missing price ID"), 400

        # Get the current user
        user = current_user

        # Get the price details from the database
        price = Price.query.get(price_id)
        if not price:
            return jsonify(error="Invalid price ID"), 400

        # Calculate the amount based on the price
        amount = price.amount

        # Create a Stripe Checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                price_data=stripe.PriceData.create(
                    currency='brl',
                    product_data=stripe.ProductData.create(
                        name=f'Tarot Reading ({price.name})',
                    ),
                    unit_amount=amount * 100,
                ),
                quantity=1,
            }],
            mode='payment',
            success_url=url_for('payment.success', _external=True),
            cancel_url=url_for('payment.cancel', _external=True),
            metadata={'user_id': user.id, 'price_id': price_id}
        )

        return jsonify({ 'url': session.url })

    except Exception as e:
        print(f"Checkout Session Error: {str(e)}")
        return jsonify(error="Could not create checkout session"), 500

@payment_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    event = None
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ.get('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except KeyError:
        return jsonify(error="Missing Stripe-Signature header"), 400

    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        handle_payment_success(payment_intent)
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        handle_payment_failure(payment_intent)
    else:
        print('Unhandled event type {}'.format(event['type']))

    return jsonify(success=True)

def handle_payment_success(payment_intent):
    # Get the user ID from metadata
    user_id = payment_intent['metadata']['user_id']
    price_id = payment_intent['metadata']['price_id']
    
    user = User.query.get(user_id)
    if not user:
        return
    
    # Get the price details
    price = Price.query.get(price_id)
    if not price:
        return
    
    # Create a new transaction
    transaction = Transaction(
        user_id=user_id,
        amount=price.amount,
        price_id=price_id,
        status='completed',
        payment_id=payment_intent['id'],
        payment_type='card',
        currency='brl',
        created_at=datetime.utcnow()
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    # Create a new reading request
    reading = Reading(
        user_id=user_id,
        price_id=price_id,
        status='pending',
        requested_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=14)
    )
    
    db.session.add(reading)
    db.session.commit()
    
    # Send payment receipt email
    send_payment_receipt(user.email, price.name, price.amount, payment_intent['id'])

def handle_payment_failure(payment_intent):
    user_id = payment_intent['metadata']['user_id']
    # Handle failed payment (log, notify user, etc.)
    pass

@payment_bp.route('/success')
def success():
    # In a real application, you would retrieve the payment details from the session or database
    # For this example, we'll just redirect to the dashboard
    return redirect(url_for('main.dashboard'))

@payment_bp.route('/cancel')
def cancel():
    return redirect(url_for('main.dashboard'))

@payment_bp.route('/price/<price_id>')
@login_required
def get_price_details(price_id):
    price = Price.query.get(price_id)
    if not price:
        return jsonify(error="Price not found"), 404
    
    return jsonify({
        'name': price.name,
        'description': price.description,
        'amount': price.amount,
        'duration': price.duration
    })