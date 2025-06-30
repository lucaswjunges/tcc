import unittest
from io import StringIO
from unittest.mock import patch
from reading import Reading

class TestReading(unittest.TestCase):

    def test_reading_creation(self):
        reading = Reading(spread="Celtic Cross", cards=["The Fool", "The Magician"], interpretation="A new beginning with great potential.")
        self.assertEqual(reading.spread, "Celtic Cross")
        self.assertEqual(reading.cards, ["The Fool", "The Magician"])
        self.assertEqual(reading.interpretation, "A new beginning with great potential.")

    @patch('sys.stdout', new_callable=StringIO)
    def test_reading_display(self):
        reading = Reading(spread="Three Card Spread", cards=["The Empress", "The Emperor", "The Hierophant"], interpretation="Balance, authority, and tradition.")
        reading.display()
        expected_output = (
            "Spread: Three Card Spread\n"
            "Cards: The Empress, The Emperor, The Hierophant\n"
            "Interpretation: Balance, authority, and tradition.\n"
        )
        self.assertEqual(sys.stdout.getvalue(), expected_output)

    def test_reading_to_dict(self):
        reading = Reading(spread="One Card Draw", cards=["The Lovers"], interpretation="A choice must be made.")
        expected_dict = {
            "spread": "One Card Draw",
            "cards": ["The Lovers"],
            "interpretation": "A choice must be made."
        }
        self.assertEqual(reading.to_dict(), expected_dict)

    def test_generate_random_reading_returns_reading_object(self):
        # This test assumes there's some logic to generate a random reading
        # and that the 'generate_random_reading' function exists within the 'reading' module.
        # Adjust the import and function call if necessary.
        from reading import generate_random_reading
        reading = generate_random_reading()
        self.assertIsInstance(reading, Reading)
        self.assertIsNotNone(reading.spread)
        self.assertIsNotNone(reading.cards)
        self.assertIsNotNone(reading.interpretation)


if __name__ == '__main__':
    unittest.main()