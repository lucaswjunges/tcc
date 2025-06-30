import unittest
from unittest.mock import patch, MagicMock

from services.payment_service import PaymentService
from config import Config


class TestPaymentService(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.payment_gateway_mock = MagicMock()
        self.payment_service = PaymentService(self.config, self.payment_gateway_mock)

    @patch('services.payment_service.PaymentGateway')
    def test_process_payment_successful(self, MockPaymentGateway):
        mock_gateway = MockPaymentGateway.return_value
        mock_gateway.process_payment.return_value = True

        user_id = 1
        amount = 10.0
        payment_method = "credit_card"

        result = self.payment_service.process_payment(user_id, amount, payment_method)

        self.assertTrue(result)
        mock_gateway.process_payment.assert_called_once_with(user_id, amount, payment_method)


    @patch('services.payment_service.PaymentGateway')
    def test_process_payment_failed(self, MockPaymentGateway):
        mock_gateway = MockPaymentGateway.return_value
        mock_gateway.process_payment.return_value = False

        user_id = 1
        amount = 10.0
        payment_method = "paypal"

        result = self.payment_service.process_payment(user_id, amount, payment_method)

        self.assertFalse(result)
        mock_gateway.process_payment.assert_called_once_with(user_id, amount, payment_method)

    @patch('services.payment_service.PaymentGateway')
    def test_process_payment_exception(self, MockPaymentGateway):
        mock_gateway = MockPaymentGateway.return_value
        mock_gateway.process_payment.side_effect = Exception("Payment gateway error")

        user_id = 1
        amount = 10.0
        payment_method = "paypal"

        with self.assertRaises(Exception) as context:
            self.payment_service.process_payment(user_id, amount, payment_method)

        self.assertIn("Payment gateway error", str(context.exception))


if __name__ == '__main__':
    unittest.main()