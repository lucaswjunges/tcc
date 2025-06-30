import unittest
from unittest.mock import patch, Mock

from services.tarot_service import TarotService

class TestTarotService(unittest.TestCase):

    @patch('services.tarot_service.TarotDeck')
    def setUp(self, MockTarotDeck):
        self.mock_deck = MockTarotDeck.return_value
        self.tarot_service = TarotService()

    def test_draw_cards(self):
        num_cards = 3
        self.mock_deck.draw_cards.return_value = ['Card 1', 'Card 2', 'Card 3']
        cards = self.tarot_service.draw_cards(num_cards)
        self.assertEqual(len(cards), num_cards)
        self.mock_deck.draw_cards.assert_called_once_with(num_cards)

    @patch('services.tarot_service.TarotSpread')
    def test_perform_reading(self, MockTarotSpread):
        spread_name = "Celtic Cross"
        cards = ['Card 1', 'Card 2', 'Card 3']
        self.mock_deck.draw_cards.return_value = cards
        mock_spread = MockTarotSpread.return_value
        mock_spread.interpret.return_value = "This is a test reading."

        reading = self.tarot_service.perform_reading(spread_name)

        MockTarotSpread.assert_called_once_with(spread_name, cards)
        mock_spread.interpret.assert_called_once()
        self.assertEqual(reading, "This is a test reading.")


    @patch('services.tarot_service.db')
    def test_save_reading(self, mock_db):
        reading = "This is a test reading."
        user_id = 1

        self.tarot_service.save_reading(reading, user_id)

        mock_db.session.add.assert_called_once()  # Check if add is called
        mock_db.session.commit.assert_called_once() # Check if commit is called


    def test_get_available_spreads(self):
        spreads = self.tarot_service.get_available_spreads()
        self.assertIsInstance(spreads, list)
        # Add assertions based on your actual available spreads


if __name__ == '__main__':
    unittest.main()