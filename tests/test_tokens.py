import datetime
from os import access
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
    
    @mock.patch.object(AccessToken, 'save_tokens', return_value=True)
    def test_save_token(self, mock_save_token):
        token = AccessToken(access_token_content)

        result = token.save_tokens()
        self.assertTrue(result)

    @mock.patch.object(AccessToken, 'save_tokens', return_value=False)
    @mock.patch.object(AccessToken, '_get_now', return_value=datetime.datetime(2021, 1, 1, 0, 0, 0, 000000, tzinfo=datetime.timezone.utc))
    def test_set_access_token_expiry(self, mock_save_token, mock_get_now):
        token = AccessToken(access_token_content)
        self.assertEqual(token.expires_at, datetime.datetime(2021, 1, 1, 1, 0, tzinfo=datetime.timezone.utc))

    @mock.patch.object(AccessToken, 'save_tokens', return_value=False)
    @mock.patch.object(AccessToken, '_get_now', return_value=datetime.datetime(2021, 1, 1, 0, 0, 0, 000000, tzinfo=datetime.timezone.utc))
    def test_is_expired_false(self, mock_save_token, mock_get_now):
        token = AccessToken(access_token_content)
        self.assertFalse(token.is_expired())

    @mock.patch.object(AccessToken, 'save_tokens', return_value=False)
    @mock.patch.object(AccessToken, '_get_now', return_value=datetime.datetime(2021, 1, 1, 0, 0, 0, 000000, tzinfo=datetime.timezone.utc))
    def test_is_expired_true(self, mock_save_token, mock_get_now):
        token = AccessToken(access_token_content)
        token.expires_at = datetime.datetime(2020, 1, 1, 0, 0, 0, 000000, tzinfo=datetime.timezone.utc)
        self.assertTrue(token.is_expired())

    @mock.patch.object(AccessToken, 'save_tokens', return_value=False)
    @mock.patch.object(AccessToken, '_get_now', return_value=datetime.datetime(2021, 1, 1, 0, 0, 0, 000000, tzinfo=datetime.timezone.utc))
    def test_load_from_cache(self, mock_save_token, mock_get_now):
        token = AccessToken(access_token_content, load_from_cache=True)
        self.assertFalse(token.is_expired())

    @mock.patch.object(AccessToken, 'save_tokens', return_value=False)
    def test_access_token_property(self, mock_save_token):
        token = AccessToken(access_token_content)
        self.assertEqual(token.access_token, access_token_content['access_token'])

    @mock.patch.object(AccessToken, 'save_tokens', return_value=False)
    def test_refresh_token_property(self, mock_save_token):
        token = AccessToken(access_token_content)
        self.assertEqual(token.refresh_token, access_token_content['refresh_token'])

    @mock.patch.object(AccessToken, '_get_now', return_value=datetime.datetime(2021, 1, 1, 0, 0, 0, 000000, tzinfo=datetime.timezone.utc))
    def test_save_tokens(self, mock_get_now):
        token = AccessToken(access_token_content)
        access_token_content_copy = access_token_content.copy()
        with open('./src/config/tokens.json', 'r') as file:
            access_token_content_created = json.load(file)
        self.assertEqual(access_token_content_created, access_token_content_copy)   


if __name__ == '__main__':
    unittest.main()