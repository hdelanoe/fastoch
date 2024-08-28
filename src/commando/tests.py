from django.conf import settings
from django.test import TestCase

class NeonDBTestCase(TestCase):

    def test_db_url(self):
        DATABASE_URL = settings.DATABASE_URL
        self.assertIn("neon.tech", DATABASE_URL)