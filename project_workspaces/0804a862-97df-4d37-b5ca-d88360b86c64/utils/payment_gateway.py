from abc import ABC, abstractmethod
import os

# Substitua pelas suas credenciais reais (NÃO as coloque em código-fonte em produção!)
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")  # Usar variáveis de ambiente
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET")


class PaymentGateway(ABC):

    @abstractmethod
    def process_payment(self, amount, description, user_info):
        pass


class StripeGateway(PaymentGateway):

    def __init__(self, api_key=STRIPE_API_KEY):
        import stripe
        stripe.api_key = api_key
        self.stripe = stripe

    def process_payment(self, amount, description, user_info):
        try:
            payment_intent = self.stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Stripe usa centavos
                currency="brl",  # ou outra moeda
                payment_method_types=["card"],
                description=description,
                metadata={"user_id": user_info.get("id")},  # Se houver um ID de usuário
            )
            return payment_intent.client_secret, None  # Retorna o client_secret para o frontend
        except Exception as e:
            return None, str(e)  # Retorna None e a mensagem de erro


class PayPalGateway(PaymentGateway):

    def __init__(self, client_id=PAYPAL_CLIENT_ID, client_secret=PAYPAL_CLIENT_SECRET):
        import paypalrestsdk
        paypalrestsdk.configure({
            "mode": "sandbox",  # ou "live" para produção
            "client_id": client_id,
            "client_secret": client_secret
        })
        self.paypal = paypalrestsdk

    def process_payment(self, amount, description, user_info):
        payment = self.paypal.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": "http://localhost:5000/payment/success",  # Substituir pela sua URL
                "cancel_url": "http://localhost:5000/payment/cancel"  # Substituir pela sua URL
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": description,
                        "price": str(amount),
                        "currency": "BRL",  # Ou outra moeda
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": str(amount),
                    "currency": "BRL"
                },
                "description": description
            }]
        })
        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    return link.href, None # Retorna a URL de aprovação do PayPal
        else:
            return None, payment.error  # Retorna None e o erro do PayPal




def get_payment_gateway(gateway_name="stripe"): # Padrão para Stripe
    if gateway_name.lower() == "stripe":
        return StripeGateway()
    elif gateway_name.lower() == "paypal":
        return PayPalGateway()
    else:
        raise ValueError("Gateway de pagamento inválido.")