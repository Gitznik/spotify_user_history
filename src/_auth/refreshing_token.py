import json
import yaml
from urllib.parse import urlencode, urlparse, parse_qs
from abc import ABC, abstractmethod
import requests
import datetime

from ..config.parse_config_files import AuthConfig
from ..client import Client

class Token(ABC):
    def _set_access_token_expiry(self, expires_in):
        expires_in_delta = datetime.timedelta(seconds = expires_in)
        return datetime.datetime.now(datetime.timezone.utc) + expires_in_delta

    def is_expired(self):
        return self.expires_at < datetime.datetime.now(datetime.timezone.utc)

class AccessToken(Token):
    created_at = datetime.datetime.now()
    def __init__(self, acess_token_content) -> None:
        self.access_token_content = acess_token_content
        self.expires_at = self._set_access_token_expiry(
            self.access_token_content['expires_in'])
        self.save_tokens()

    @property
    def access_token(self):
        return self.access_token_content['access_token']

    @property
    def refresh_token(self):
        return self.access_token_content['refresh_token']

    def save_tokens(self):
        token_information = self.access_token_content
        token_information['expires_at'] = self.expires_at.strftime("%Y-%m-%d %H:%M:%S %Z")
        with open('tokens.json', 'w') as file:
            json.dump(token_information, file, indent=2)       
            

class AuthCodeRequest:
    auth_url = 'https://accounts.spotify.com/authorize'

    def __init__(
            self, 
            client: Client, 
            auth_config: AuthConfig,
            scope: str) -> None:
        self.client = client
        self.auth_config = auth_config
        self.scope = scope

    @property
    def auth_code(self) -> str:
        if self.scope in self.auth_config.scopes:
            return self.auth_config.config[self.scope]
        auth_code = self.prompt_user_authorization()
        self.auth_config.add_auth_code(
            scope = self.scope,
            auth_code=auth_code
        )
        return auth_code

    def prompt_user_authorization(self):
        auth_url = self.create_auth_url()
        print(f'Please visit this URL: {auth_url}')
        redirected_url = input(
            'Please paste the URL you were redirected to:').strip()
        return self.parse_url_param(redirected_url, 'code')

    def create_auth_url(self) -> str:
        params = {
            'client_id': self.client.client_config.client_id,
            'response_type': 'code',
            'redirect_uri': self.client.client_config.redirect_url,
            'scope': self.scope,
            'show_dialog': 'false',
        }
        return self.auth_url + '?' + urlencode(params)

    def parse_url_param(self, url, param):
        query = urlparse(url).query
        code = parse_qs(query).get(param, None)
        return code[0]
        

class RefreshingToken:
    token_url = 'https://accounts.spotify.com/api/token'

    def __init__(
            self, 
            auth_code_request: AuthCodeRequest) -> None:
        self.auth_code_request = auth_code_request
        self.access_token = self._return_access_token()

    def get_access_token(self):
        if self.access_token.is_expired():
            self.access_token = self._return_access_token(refresh = True)
        return self.access_token.access_token

    def _request_access_token(self, refresh = False):
        if refresh:
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
            }
        else:
            data = {
                'grant_type': 'authorization_code',
                'code': self.auth_code_request.auth_code,
                'redirect_uri': self.auth_code_request.client.client_config.redirect_url,
            }

        headers = {
            'Authorization': f'Basic {self.auth_code_request.client.get_auth_string()}'
        }

        return requests.post(
            self.token_url, 
            data = data,
            headers = headers,
            )

    def _return_access_token(self, refresh = False):
        access_token_response = self._request_access_token(refresh)

        if access_token_response.status_code == 400:
            if access_token_response.json()['error_description'] == \
                    'Authorization code expired' or 'Invalid authorization code':
                self.auth_code_request.auth_config.remove_auth_code(
                    self.auth_code_request.scope)
                access_token_response = self._request_access_token()

        return AccessToken(access_token_response.json())
