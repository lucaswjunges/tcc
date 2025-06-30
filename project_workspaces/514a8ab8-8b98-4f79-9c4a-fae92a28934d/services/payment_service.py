from config import Config
import stripe

stripe.api_key = Config.STRIPE_SECRET_KEY

class PaymentService:

    @staticmethod
    def create_checkout_session(line_items, success_url, cancel_url):
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return checkout_session
        except Exception as e:
            print(f"Error creating checkout session: {e}")
            return None

    @staticmethod
    def retrieve_session(session_id):
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session
        except Exception as e:
            print(f"Error retrieving session: {e}")
            return None


    @staticmethod
    def create_product(name, description, price):
      try:
          product = stripe.Product.create(
              name=name,
              description=description,
          )
          price = stripe.Price.create(
              unit_amount=price,
              currency="brl", # ou outra moeda
              recurring=None, # para pagamento único
              product=product.id,
          )
          return product, price
      except Exception as e:
          print(f"Error creating product/price: {e}")
          return None, None