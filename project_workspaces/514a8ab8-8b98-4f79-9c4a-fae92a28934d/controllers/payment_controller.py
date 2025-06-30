from flask import Blueprint, request, jsonify, render_template
from config import db
from models import Payment, Reading
import stripe

payment_bp = Blueprint('payment', __name__)

stripe.api_key = 'YOUR_STRIPE_SECRET_KEY' # Substitua pela sua chave secreta do Stripe

@payment_bp.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    try:
        data = request.get_json()
        reading_id = data.get('reading_id')
        reading = Reading.query.get(reading_id)

        if not reading:
            return jsonify({'error': 'Leitura não encontrada'}), 404
        
        if reading.payment_status == 'paid':
            return jsonify({'error': 'Leitura já paga'}), 400

        intent = stripe.PaymentIntent.create(
            amount=int(reading.price * 100), # Valor em centavos
            currency='brl', # ou outra moeda
            automatic_payment_methods={
                'enabled': True,
            },
            metadata={'reading_id': reading_id}
        )
        return jsonify({'clientSecret': intent['client_secret']})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@payment_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, 'YOUR_STRIPE_ENDPOINT_SECRET' # Substitua pelo seu endpoint secret do Stripe
        )
    except ValueError as e:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return 'Invalid signature', 400

    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        reading_id = payment_intent['metadata'].get('reading_id')

        reading = Reading.query.get(reading_id)
        if reading:
            reading.payment_status = 'paid'
            payment = Payment(
                reading_id=reading_id,
                stripe_payment_id=payment_intent['id'],
                amount=payment_intent['amount'] / 100
            )
            db.session.add(payment)
            db.session.commit()
            # Aqui você pode adicionar lógica para enviar um email de confirmação, etc.


    return 'Success', 200


@payment_bp.route('/success/<int:reading_id>')
def success(reading_id):
    reading = Reading.query.get(reading_id)
    if not reading:
      return "Leitura não encontrada", 404

    return render_template('payment/success.html', reading=reading)


@payment_bp.route('/cancel')
def cancel():
    return render_template('payment/cancel.html')