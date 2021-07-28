from abc import ABC, abstractmethod
from typing import List

from ..errors.token_errors import InvalidAccessTokenError
from ..logging.logger import ApiLogger
from ..config.parse_config_files import AuthConfig
from ..client import Client
from .._auth.token_requests import RefreshingToken, AuthCodeRequest
from ..logging.logger import info_logger, debug_logger
from ..config.configure_requests import configure_request

conf_requests = configure_request()

class AuthFlow(ABC):
    client = Client()

    @abstractmethod
    def authenticate():
        pass

    @abstractmethod
    def get_request():
        pass

class AuthorizationCodeFlow(AuthFlow):
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

class ClientCredentialsFlow(AuthFlow):
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
        try:
            return self.token_response['access_token']
        except KeyError as err:
            raise InvalidAccessTokenError(str(err)) from err