import datetime
import os
import unittest
from unittest import mock
import json
import requests_mock
from unittest.case import TestCase

from src._auth.auth_flows import AuthCodeRequest, RefreshingToken
from src.config.parse_config_files import AuthConfig
from src.client import Client

class MockAuthConfig(AuthConfig):
    def remove_auth_code(self, scope: str) -> None:
        pass

class AccessToken:
    def __init__(self, access_token_content, load_from_cache):
        self.access_token_content = access_token_content
        self.load_from_cache = load_from_cache

mock_auth_config = MockAuthConfig()

client = Client()
client.client_config.client_id = 'mock_id'
client.client_config.client_secret = 'mock_secret'
client.client_config.redirect_url = 'https://mock_url.de/'

access_token_content = {
    "access_token": "access",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_token": "refresh",
    "scope": "scope",
    "expires_at": "2021-01-01T01:00:00+00:00"
}

class MockAuthCodeRequest:
    auth_code = 'test_code'
    client = client
    scope = 'test_scope'
    auth_config = mock_auth_config

    def remove_auth_code(self):
        pass
    
mock_auth = MockAuthCodeRequest()

class TestAuthCodeRequest(TestCase):

    @mock.patch(
        'builtins.input', 
        create= True, 
        return_value = 'https://localhost:8080/?code=test_code')
    def test_promt_user_authorization(self, mock_input):
        auth_code_request = AuthCodeRequest(client = client, auth_config=mock_auth_config, scope=None)
        self.assertEqual(auth_code_request._prompt_user_authorization(), 'test_code')

    @mock.patch(
        'builtins.input', 
        create= True, 
        return_value = 'https://localhost:8080/?code=test_code')
    def test_create_auth_url(self, mock_input):
        auth_code_request = AuthCodeRequest(client = client, auth_config=mock_auth_config, scope=None)
        self.assertEqual(
            auth_code_request._create_auth_url(), 
            'https://accounts.spotify.com/authorize?client_id=mock_id' +
            '&response_type=code&redirect_uri=https%3A%2F%2Fmock_url.de%2F' +
            '&scope=None&show_dialog=false')


class TestRefreshingToken(TestCase):
    
    @mock.patch.object(RefreshingToken, '_load_new_access_token', return_value = 'test_token')
    @mock.patch.object(RefreshingToken, '_load_existing_access_token', side_effect = ValueError())
    def test_retrieve_access_token_no_existing_token(self, mock_new_token, mock_existing_token):
        refreshing_token = RefreshingToken(
            auth_code_request=MockAuthCodeRequest())
        self.assertEqual(refreshing_token.access_token, 'test_token')
        self.assertEqual(refreshing_token._retrieve_access_token(refresh=True), 'test_token')

    @mock.patch.object(RefreshingToken, '_load_existing_access_token', return_value = 'existing_token')
    def test_retrieve_access_token_existing_token(self, mock_existing_token):
        refreshing_token = RefreshingToken(
            auth_code_request=MockAuthCodeRequest())
        self.assertEqual(refreshing_token.access_token, 'existing_token')

    @mock.patch.object(RefreshingToken, '_load_existing_access_token', return_value = 'existing_token')
    @requests_mock.Mocker()
    def test_request_access_token(self, mock_existing_token, request_mocker):
        
        request_mocker.post(
            'https://accounts.spotify.com/api/token', 
            text='resp', 
            status_code=200)

        refreshing_token = RefreshingToken(
            auth_code_request=MockAuthCodeRequest())

        r = refreshing_token._request_access_token()
        self.assertEqual(r.status_code, 200)   

    @mock.patch.object(RefreshingToken, '_load_existing_access_token', return_value = 'existing_token')
    @requests_mock.Mocker()
    def test_load_new_access_token_exception(self, mock_existing_token, request_mocker):
        
        request_mocker.post(
            'https://accounts.spotify.com/api/token', 
            text='resp', 
            status_code=400)
            
        refreshing_token = RefreshingToken(
            auth_code_request=MockAuthCodeRequest())

        with self.assertRaises(ValueError):
            refreshing_token._load_new_access_token()



if __name__ == '__main__':
    unittest.main()