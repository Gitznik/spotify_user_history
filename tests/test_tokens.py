import datetime
import os
import unittest
from unittest import mock
import json

from src._auth.tokens import AccessToken


access_token_content = {
    "access_token": "access",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_token": "refresh",
    "scope": "scope",
    "expires_at": "2021-01-01T01:00:00+00:00"
}

class TestAccessToken(unittest.TestCase):

    @mock.patch.object(AccessToken, '_get_now', return_value=datetime.datetime(2021, 1, 1, 0, 0, 0, 000000, tzinfo=datetime.timezone.utc))
    def setUp(self, mock_get_now) -> None:
        self.token = AccessToken(access_token_content)
    
    def tearDown(self) -> None:
        os.remove('./src/config/tokens.json')

    def test_set_access_token_expiry(self):
        self.assertEqual(self.token.expires_at, datetime.datetime(2021, 1, 1, 1, 0, tzinfo=datetime.timezone.utc))

    @mock.patch.object(AccessToken, '_get_now', return_value=datetime.datetime(2021, 1, 1, 0, 0, 0, 000000, tzinfo=datetime.timezone.utc))
    def test_is_expired_false(self, mock_get_now):
        self.assertFalse(self.token.is_expired())

    def test_is_expired_true(self):
        self.token.expires_at = datetime.datetime(2020, 1, 1, 0, 0, 0, 000000, tzinfo=datetime.timezone.utc)
        self.assertTrue(self.token.is_expired())

    @mock.patch.object(AccessToken, '_get_now', return_value=datetime.datetime(2021, 1, 1, 0, 0, 0, 000000, tzinfo=datetime.timezone.utc))
    def test_load_from_cache(self, mock_get_now):
        self.token = AccessToken(access_token_content, load_from_cache=True)
        self.assertFalse(self.token.is_expired())

    def test_access_token_property(self):
        self.assertEqual(self.token.access_token, access_token_content['access_token'])

    def test_refresh_token_property(self):
        self.assertEqual(self.token.refresh_token, access_token_content['refresh_token'])

    def test_save_tokens(self):
        access_token_content_copy = access_token_content.copy()
        with open('./src/config/tokens.json', 'r') as file:
            access_token_content_created = json.load(file)
        self.assertEqual(access_token_content_created, access_token_content_copy)   


if __name__ == '__main__':
    unittest.main()