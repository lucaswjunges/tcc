from django.test import TestCase, Client
from django.urls import reverse

class TestViews(TestCase):

    def setUp(self):
        self.client = Client()

    def test_index_view(self):
        url = reverse('index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_reading_view_get(self):
        url = reverse('reading')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reading.html')

    def test_reading_view_post(self):
        url = reverse('reading')
        data = {} # Add any necessary POST data here, like choices or payment info if applicable
        response = self.client.post(url, data)
        # Assertions based on expected behavior after POST request, like redirect or context data
        # Example: self.assertEqual(response.status_code, 302) 
        # Example: self.assertRedirects(response, reverse('some_other_view'))

    def test_about_view(self):
        url = reverse('about')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about.html')

    # Add more tests for other views like contact, legal, payment confirmation, etc. as needed


    # Example of a test checking context data within a specific view
    # def test_reading_view_context(self):
    #     url = reverse('reading')
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIn('spread', response.context) # Assuming 'spread' is a key in context data

    # Example of testing a 404 error for an invalid URL
    # def test_invalid_url(self):
    #     response = self.client.get('/invalid_url/') 
    #     self.assertEqual(response.status_code, 404)