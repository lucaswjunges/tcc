import unittest
from flask import url_for
from main import app

class TestRoutes(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        self.client = app.test_client()
        self.assertEqual(len(app.url_map), 10)

    def test_home_page(self):
        response = self.client.get(url_for('home'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Home Page', str(response.data))

    def test_about_page(self):
        response = self.client.get(url_for('about'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('About Us', str(response.data))

    def test_services_page(self):
        response = self.client.get(url_for('services'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Tarot Services', str(response.data))

    def test_read_page(self):
        response = self.client.get(url_for('read'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Book a Reading', str(response.data))

    def test_pricing_page(self):
        response = self.client.get(url_for('pricing'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Pricing', str(response.data))

    def test_gallery_page(self):
        response = self.client.get(url_for('gallery'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Gallery', str(response.data))

    def test_contact_page(self):
        response = self.client.get(url_for('contact'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Contact Us', str(response.data))

    def test_privacy_policy(self):
        response = self.client.get(url_for('privacy_policy'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Privacy Policy', str(response.data))

    def test_terms_conditions(self):
        response = self.client.get(url_for('terms_conditions'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Terms and Conditions', str(response.data))

    def test_read_results(self):
        response = self.client.get(url_for('read_results', reading_id='123'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Your Tarot Reading Results', str(response.data))

if __name__ == '__main__':
    unittest.main()