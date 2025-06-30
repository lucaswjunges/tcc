import unittest
from tarot.tarot_functions import (
    shuffle_deck,
    deal_cards,
    interpret_card,
    get_spread,
)


class TestTarotFunctions(unittest.TestCase):

    def setUp(self):
        self.deck = list(range(78))  # Representando um baralho de 78 cartas

    def test_shuffle_deck(self):
        shuffled_deck = shuffle_deck(self.deck.copy())
        self.assertNotEqual(self.deck, shuffled_deck)  # Verifica se o baralho foi embaralhado
        self.assertEqual(len(self.deck), len(shuffled_deck))  # Verifica se o número de cartas permanece o mesmo

    def test_deal_cards(self):
        num_cards = 3
        dealt_cards = deal_cards(self.deck, num_cards)
        self.assertEqual(len(dealt_cards), num_cards)  # Verifica se o número correto de cartas foi distribuído
        # Verifica se as cartas distribuídas foram removidas do baralho
        self.assertEqual(len(self.deck), 78 - num_cards)

    def test_interpret_card(self):
        # Testa a interpretação de uma carta específica (exemplo)
        interpretation = interpret_card(0, upright=True)  # Carta 0 na posição vertical
        self.assertIsNotNone(interpretation)  # Verifica se a interpretação não é nula
        self.assertIsInstance(interpretation, str)  # Verifica se a interpretação é uma string

        interpretation = interpret_card(0, upright=False)  # Carta 0 na posição invertida
        self.assertIsNotNone(interpretation)
        self.assertIsInstance(interpretation, str)
        # idealmente, testar com mais cartas e posições em um contexto real de leitura

    def test_get_spread(self):
        spread_name = "three_card"
        spread = get_spread(spread_name)
        self.assertIsNotNone(spread)  # Verifica se o spread existe
        self.assertIn("name", spread)
        self.assertIn("positions", spread)
        # Verifica se as posições esperadas estão presentes no spread
        self.assertEqual(len(spread["positions"]), 3)