import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from app.controllers.reading_controller import ReadingController

class TestReadingController(unittest.TestCase):

    def setUp(self):
        app = Flask(__name__)
        app.config['TESTING'] = True
        self.app = app.test_client()
        self.controller = ReadingController()

    @patch('app.controllers.reading_controller.ReadingService')
    def test_get_reading(self, mock_service):
        mock_reading = {'cards': ['The Fool', 'The Magician'], 'interpretation': 'A new beginning and great potential.'}
        mock_service.get_reading.return_value = mock_reading

        response = self.controller.get_reading()

        self.assertEqual(response[0], mock_reading)
        self.assertEqual(response[1], 200)
        mock_service.get_reading.assert_called_once()

    @patch('app.controllers.reading_controller.ReadingService')
    def test_get_reading_error(self, mock_service):
        mock_service.get_reading.side_effect = Exception('Database error')

        response = self.controller.get_reading()

        self.assertEqual(response[1], 500)
        self.assertIn('error', response[0].keys())
        mock_service.get_reading.assert_called_once()


    @patch('app.controllers.reading_controller.ReadingService')
    def test_save_reading(self, mock_service):
        mock_reading_data = {'cards': ['The Fool', 'The Magician'], 'interpretation': 'A new beginning and great potential.', 'user_id': 1}
        mock_service.save_reading.return_value = True

        response = self.controller.save_reading(mock_reading_data)

        self.assertEqual(response[1], 201)
        mock_service.save_reading.assert_called_once_with(mock_reading_data)

    @patch('app.controllers.reading_controller.ReadingService')
    def test_save_reading_error(self, mock_service):
        mock_reading_data = {'cards': ['The Fool', 'The Magician'], 'interpretation': 'A new beginning and great potential.', 'user_id': 1}
        mock_service.save_reading.side_effect = Exception('Database error')

        response = self.controller.save_reading(mock_reading_data)

        self.assertEqual(response[1], 500)
        self.assertIn('error', response[0].keys())
        mock_service.save_reading.assert_called_once_with(mock_reading_data)


    @patch('app.controllers.reading_controller.ReadingService')
    def test_get_past_readings(self, mock_service):
        mock_readings = [{'cards': ['The Fool', 'The Magician'], 'interpretation': 'A new beginning', 'date': '2024-07-26'},
                         {'cards': ['The Empress', 'The Emperor'], 'interpretation': 'Power and stability', 'date': '2024-07-25'}]
        mock_service.get_past_readings.return_value = mock_readings
        mock_request = MagicMock()
        mock_request.args.get.return_value = "1"


        response = self.controller.get_past_readings(mock_request)

        self.assertEqual(response[0], mock_readings)
        self.assertEqual(response[1], 200)
        mock_service.get_past_readings.assert_called_once_with("1")
        mock_request.args.get.assert_called_with('user_id')



    @patch('app.controllers.reading_controller.ReadingService')
    def test_get_past_readings_error(self, mock_service):
        mock_service.get_past_readings.side_effect = Exception('Database error')
        mock_request = MagicMock()
        mock_request.args.get.return_value = "1"

        response = self.controller.get_past_readings(mock_request)

        self.assertEqual(response[1], 500)
        self.assertIn('error', response[0].keys())
        mock_service.get_past_readings.assert_called_once_with("1")
        mock_request.args.get.assert_called_with('user_id')



if __name__ == '__main__':
    unittest.main()