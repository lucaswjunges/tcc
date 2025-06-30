from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from src.models import Order, ReadingType, PaymentMethod, db
from src.utils import send_payment_email, generate_invoice
import stripe
import os
from datetime import datetime, timedelta

payment_bp = Blueprint('payment', __name__)

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

@payment_bp.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    if request.method == 'POST':
        # Get form data
        reading_type_id = request.form.get('reading_type')
        payment_method = request.form.get('payment_method')
        card_details = request.form.get('card_details')
        
        # Validate form
        if not reading_type_id or not payment_method or not card_details:
            flash('Por favor, preencha todos os campos.', 'error')
            return redirect(url_for('payment.payment'))
        
        # Get reading type
        reading_type = ReadingType.query.get(reading_type_id)
        if not reading_type:
            flash('Tipo de leitura não encontrado.', 'error')
            return redirect(url_for('payment.payment'))
        
        # Calculate price
        price = reading_type.price
        
        # Process payment
        try:
            # Create Stripe payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=price * 100,  # Amount in cents
                currency='brl',
                payment_method_types=['card'],
                description=f'Leitura de Tarô {reading_type.name}'
            )
            
            # Process payment with Stripe
            stripe.PaymentIntent.confirm(
                payment_intent.id,
                payment_method=payment_method
            )
            
            # Create order
            order = Order(
                user_id=current_user.id,
                reading_type_id=reading_type_id,
                price=price,
                status='paid',
                payment_date=datetime.now()
            )
            db.session.add(order)
            db.session.commit()
            
            # Send payment confirmation email
            send_payment_email(current_user.email, order)
            
            # Generate invoice
            generate_invoice(order)
            
            flash('Pagamento realizado com sucesso!', 'success')
            return redirect(url_for('order.success', order_id=order.id))
            
        except Exception as e:
            flash(f'Erro ao processar pagamento: {str(e)}', 'error')
            return redirect(url_for('payment.payment'))
    
    # Get all reading types for the dropdown
    reading_types = ReadingType.query.all()
    
    return render_template('payment.html', reading_types=reading_types)

@payment_bp.route('/order/success/<int:order_id>')
@login_required
def success(order_id):
    order = Order.query.get(order_id)
    if order and order.user_id == current_user.id and order.status == 'paid':
        return render_template('order_success.html', order=order)
    return redirect(url_for('home.index'))

@payment_bp.route('/order/cancel/<int:order_id>')
@login_required
def cancel(order_id):
    order = Order.query.get(order_id)
    if order and order.user_id == current_user.id and order.status == 'created':
        db.session.delete(order)
        db.session.commit()
        return render_template('order_cancel.html')
    return redirect(url_for('home.index'))