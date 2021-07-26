import requests
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List
from pydantic.error_wrappers import ValidationError

from .db_connection import DatabaseConnection
from .logging.logger import ApiLogger
from .config.parse_config_files import AuthConfig
from .client import Client
from ._auth.auth_flows import RefreshingToken, AuthCodeRequest
from .logging.logger import info_logger, debug_logger
from .spotify_data.dataclasses import SpotifyHistory, SpotifySong
from .config.configure_requests import configure_request

conf_requests = configure_request()

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


    def get_auth_code(self, scope: str) -> AuthCodeRequest:
        return AuthCodeRequest(
            client = self.client, 
            auth_config = self.auth_config,
            scope = scope)

    def get_refreshing_token(
            self, auth_code_request: AuthCodeRequest) -> RefreshingToken:

        return RefreshingToken(
            auth_code_request= auth_code_request
        )

    def authenticate(self, scope: str) -> RefreshingToken:

        auth_code_request = self.get_auth_code(scope)
        return self.get_refreshing_token(
            auth_code_request=auth_code_request)

    def get_request(self, endpoint:str, params: dict = None) -> dict:
        url = f'{endpoint}'
        return conf_requests.get(url=url, headers=self.get_req_header, params=params)

class ClientCredentialsFlow(SpotifyConnection):
    token_url = 'https://accounts.spotify.com/api/token'
    def __init__(self) -> None:
        info_logger.info(f'Instantiate ClientCredentialsFlow')
        self.token_response = self.authenticate()
        self.get_req_header = {
            "Authorization": "Bearer " + self.extract_token()
        }

    @ApiLogger('Athenticate in Client Credentials Flow')
    def authenticate(self) -> dict:
        headers = {'Authorization': f'Basic {self.client.get_auth_string()}'}
        data = {'grant_type': 'client_credentials'}
        return conf_requests.post(
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
    def get_playlist(self, playlistId) -> requests.Response:
        return self.conn.get_request(
            endpoint= f'https://api.spotify.com/v1/playlists/{playlistId}',
        )

    @ApiLogger('Sending Play History Request')
    def _get_play_history_req(
            self, start_point_unix_ms: int) -> requests.Response:

        params = {
            'limit': 20,
            'after': start_point_unix_ms
        }
        return self.conn.get_request(
            endpoint = 'https://api.spotify.com/v1/me/player/recently-played/',
            params = params,
        )

    def _get_play_history(self, start_point_unix_ms: int) -> SpotifyHistory:
        history_resp = self._get_play_history_req(
            start_point_unix_ms=start_point_unix_ms)
        try:
            return SpotifyHistory(**history_resp.json())
        except ValidationError as e:
            info_logger.exception(f'SpotifyHistory parsing failed on ' + 
                                  f'\n{history_resp.json()}\n')
            raise e


    def get_full_play_history(
            self, start_point_unix_ms: int) -> List[SpotifySong]:

        history = self._get_play_history(
            start_point_unix_ms=start_point_unix_ms)
        history_list = [history]
        while not history_list[-1].is_last:
            history_list.append(self._get_play_history(
                start_point_unix_ms=history_list[-1].cursors.after))
        return [item for hist in history_list for item in hist.items]

    def get_new_play_history(
            self, 
            database_conn: DatabaseConnection,
            fallback_datetime: datetime = datetime(
                2021, 7, 24, 10, 0, tzinfo=timezone.utc)
                ) -> List[SpotifySong]:
        try:
            start_point = database_conn.find_newest()
            start_point_ts = round(start_point.timestamp() * 1000)
            info_logger.info(f'Load play history after {start_point}')
        except:
            info_logger.warning('No existing start point found in MongoDB, ' + 
                                f'use fallback timestamp {fallback_datetime}')
            start_point_ts = round(fallback_datetime.timestamp() * 1000)

        return self.get_full_play_history(start_point_ts)