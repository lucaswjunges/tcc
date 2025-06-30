from django.test import TestCase
from .models import Spread, Card, Reading

class SpreadModelTest(TestCase):
    def test_spread_creation(self):
        spread = Spread.objects.create(name="Three Card Spread", description="Past, Present, Future")
        self.assertEqual(str(spread), "Three Card Spread")
        self.assertEqual(spread.positions_number, 3)  # Default value

    def test_spread_string_representation(self):
        spread = Spread(name="Celtic Cross")
        self.assertEqual(str(spread), "Celtic Cross")


class CardModelTest(TestCase):
    def test_card_creation(self):
        card = Card.objects.create(name="The Fool", description="New beginnings, innocence, spontaneity", arcana="Major")
        self.assertEqual(str(card), "The Fool")

    def test_card_string_representation(self):
        card = Card(name="The Magician")
        self.assertEqual(str(card), "The Magician")


class ReadingModelTest(TestCase):
    def setUp(self):
        self.spread = Spread.objects.create(name="Simple Spread", description="A simple spread")
        self.card1 = Card.objects.create(name="The Magician", description="Manifestation, resourcefulness", arcana="Major")
        self.card2 = Card.objects.create(name="The High Priestess", description="Intuition, sacred knowledge", arcana="Major")

    def test_reading_creation(self):
        reading = Reading.objects.create(spread=self.spread)
        reading.cards.add(self.card1, through_defaults={'position': 1})
        reading.cards.add(self.card2, through_defaults={'position': 2})

        self.assertEqual(reading.cards.count(), 2)
        self.assertEqual(reading.spread, self.spread)

    def test_reading_card_positions(self):
        reading = Reading.objects.create(spread=self.spread)
        reading.cards.add(self.card1, through_defaults={'position': 1})
        reading.cards.add(self.card2, through_defaults={'position': 2})


        card1_position = reading.readingcard_set.get(card=self.card1).position
        card2_position = reading.readingcard_set.get(card=self.card2).position

        self.assertEqual(card1_position, 1)
        self.assertEqual(card2_position, 2)