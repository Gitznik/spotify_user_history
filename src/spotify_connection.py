import requests
from abc import ABC, abstractmethod

from .logging.logger import ApiLogger
from .config.parse_config_files import AuthConfig
from .client import Client
from ._auth.auth_flows import RefreshingToken, AuthCodeRequest
from .logging.logger import info_logger, debug_logger


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
        info_logger.info(f'Instantiate AuthCodeFlow for scope {scope}')
        self.refreshing_token = self.authenticate(scope)
        self.get_req_header = {
            "Authorization": "Bearer " + self.refreshing_token.get_access_token()
        }
        info_logger.info(f'AuthCodeFlow for scope {scope} successfull')


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

    def get_request(self, endpoint:str, id: str) -> dict:
        url = f'{endpoint}{id}'
        return requests.get(url=url, headers=self.get_req_header)

class ClientCredentialsFlow(SpotifyConnection):
    token_url = 'https://accounts.spotify.com/api/token'
    def __init__(self) -> None:
        info_logger.info(f'Instantiate ClientCredentialsFlow')
        self.token_response = self.authenticate()
        self.get_req_header = {
            "Authorization": "Bearer " + self.extract_token()
        }

    @ApiLogger('Athenticate in Client Credentials Flow')
    def authenticate(self):
        headers = {'Authorization': f'Basic {self.client.get_auth_string()}'}
        data = {'grant_type': 'client_credentials'}
        return requests.post(
            self.token_url, headers = headers, data = data).json()

    def extract_token(self) -> str:
        return self.token_response['access_token']


class SpotifyInteraction:
    def __init__(
            self, 
            connection: SpotifyConnection) -> None:
        info_logger.info(f'Instantiate SpotifyInteraction')
        self.conn = connection

    @ApiLogger('Sending Playlist Request')
    def get_playlist(self, playlistId):
        return self.conn.get_request(
            endpoint= 'https://api.spotify.com/v1/playlists/',
            id = playlistId
        )
