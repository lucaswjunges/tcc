import unittest
from utils import shuffle_deck, deal_cards

class TestUtils(unittest.TestCase):

    def test_shuffle_deck(self):
        deck = list(range(78))  # Simulate a deck of 78 tarot cards
        shuffled_deck = shuffle_deck(deck.copy())
        self.assertNotEqual(deck, shuffled_deck)  # Check if the deck has been shuffled
        self.assertEqual(len(deck), len(shuffled_deck))  # Ensure all cards are still present

    def test_deal_cards(self):
        deck = list(range(78))
        num_cards = 3
        dealt_cards, remaining_deck = deal_cards(deck.copy(), num_cards)
        self.assertEqual(len(dealt_cards), num_cards)  # Check correct number of cards dealt
        self.assertEqual(len(remaining_deck), len(deck) - num_cards) # Check remaining deck size
        self.assertNotIn(dealt_cards, remaining_deck) # Ensure dealt cards are removed from the deck


    def test_deal_cards_empty_deck(self):
        deck = []
        num_cards = 3
        dealt_cards, remaining_deck = deal_cards(deck.copy(), num_cards)
        self.assertEqual(len(dealt_cards), 0)
        self.assertEqual(len(remaining_deck), 0)

    def test_deal_cards_more_cards_than_deck(self):
        deck = list(range(5))
        num_cards = 10
        dealt_cards, remaining_deck = deal_cards(deck.copy(), num_cards)
        self.assertEqual(len(dealt_cards), len(deck)) # Should deal all available cards
        self.assertEqual(len(remaining_deck), 0) # Remaining deck should be empty