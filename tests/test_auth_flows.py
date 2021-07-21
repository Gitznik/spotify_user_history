import datetime
import os
import unittest
from unittest import mock
import json
from unittest.case import TestCase

from src._auth.auth_flows import AuthCodeRequest, RefreshingToken
from src.config.parse_config_files import AuthConfig
from src.client import Client


auth_config = AuthConfig()
client = Client()
client.client_config.client_id = 'mock_id'
client.client_config.client_secret = 'mock_secret'
client.client_config.redirect_url = 'https://mock_url.de/'

class TestAuthCodeRequest(TestCase):
    @mock.patch(
        'builtins.input', 
        create= True, 
        return_value = 'https://localhost:8080/?code=test_code')
    def test_promt_user_authorization(self, mock_input):
        auth_code_request = AuthCodeRequest(client = client, auth_config=auth_config, scope=None)
        self.assertEqual(auth_code_request._prompt_user_authorization(), 'test_code')

    @mock.patch(
        'builtins.input', 
        create= True, 
        return_value = 'https://localhost:8080/?code=test_code')
    def test_create_auth_url(self, mock_input):
        auth_code_request = AuthCodeRequest(client = client, auth_config=auth_config, scope=None)
        self.assertEqual(
            auth_code_request._create_auth_url(), 
            'https://accounts.spotify.com/authorize?client_id=mock_id' +
            '&response_type=code&redirect_uri=https%3A%2F%2Fmock_url.de%2F' +
            '&scope=None&show_dialog=false')