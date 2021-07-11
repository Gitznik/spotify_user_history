import requests
import base64
from abc import ABC, abstractmethod

from .config.parse_config_files import ClientConfig, AuthConfig
from ._auth.refreshing_token import RefreshingToken

auth_url = 'https://accounts.spotify.com/authorize'
token_url = 'https://accounts.spotify.com/api/token'
base_url = 'https://api.spotify.com/v1/'

client_config = ClientConfig()
auth_config = AuthConfig()

class SpotifyConnection(ABC):
    @abstractmethod
    def authenticate():
        pass

    @abstractmethod
    def get_request():
        pass

class AuthorizationCodeFlow(SpotifyConnection):
    def __init__(self, scope: str = 'user-read-private') -> None:
        self.auth = self.authenticate(scope)

    def authenticate(self, scope):
        return RefreshingToken(
            client_config = client_config, 
            auth_config = auth_config,
            scope = scope)

    def get_request():
        pass

class ClientCredentialsFlow(SpotifyConnection):
    def __init__(self) -> None:
        self.token_response = self.authenticate()
        self.get_req_header = {
            "Authorization": "Bearer " + self.extract_token()
        }

    def auth_string_creator(self) -> None:
        client = f'{client_config.client_id}:{client_config.client_secret}'
        return base64.b64encode(
            client.encode('ascii')
            ).decode('ascii')

    def authenticate(self):
        headers = {'Authorization': f'Basic {self.auth_string_creator()}'}
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