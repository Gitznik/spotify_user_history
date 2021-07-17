import requests
from abc import ABC, abstractmethod

from .config.parse_config_files import AuthConfig
from .client import Client
from ._auth.refreshing_token import RefreshingToken, AuthCodeRequest

auth_url = 'https://accounts.spotify.com/authorize'
token_url = 'https://accounts.spotify.com/api/token'
base_url = 'https://api.spotify.com/v1/'

class SpotifyConnection(ABC):
    client = Client()

    @abstractmethod
    def authenticate():
        pass

    @abstractmethod
    def get_request():
        pass

class AuthorizationCodeFlow(SpotifyConnection):
    auth_config = AuthConfig()
    def __init__(self, scope: str = 'user-read-private') -> None:
        self.refreshing_token = self.authenticate(scope)

    def get_auth_code(self, scope):
        return AuthCodeRequest(
            client = self.client, 
            auth_config = self.auth_config,
            scope = scope)

    def get_refreshing_token(self, auth_code_request):
        return RefreshingToken(
            auth_code_request= auth_code_request
        )

    def authenticate(self, scope):
        auth_code_request = self.get_auth_code(scope)
        return self.get_refreshing_token(
            auth_code_request=auth_code_request)

    def get_request():
        pass

class ClientCredentialsFlow(SpotifyConnection):
    def __init__(self) -> None:
        self.token_response = self.authenticate()
        self.get_req_header = {
            "Authorization": "Bearer " + self.extract_token()
        }

    def authenticate(self):
        headers = {'Authorization': f'Basic {self.client.get_auth_string()}'}
        data = {'grant_type': 'client_credentials'}
        return requests.post(token_url, headers = headers, data = data).json()

    def extract_token(self) -> str:
        return self.token_response['access_token']

    def get_request(self, endpoint:str, id: str) -> dict:
        url = f'{endpoint}{id}'
        return requests.get(url=url, headers=self.get_req_header)


class SpotifyInteraction:
    def __init__(self, connection: SpotifyConnection = ClientCredentialsFlow()) -> None:
        self.conn = connection

    def get_playlist(self, playlistId):
        return self.conn.get_request(
            endpoint= 'https://api.spotify.com/v1/playlists/',
            id = playlistId
        )