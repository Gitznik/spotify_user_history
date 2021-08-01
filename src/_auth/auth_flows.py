from abc import ABC, abstractmethod
from typing import List

from ..errors.token_errors import InvalidAccessTokenError, LostRefreshTokenError, MissingScopeError
from ..request_utils import ApiLogger
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

    @abstractmethod
    def check_scope(scope: str):
        pass

    @abstractmethod
    def reset_refreshing_token(scope: str):
        pass

class AuthorizationCodeFlow(AuthFlow):
    auth_config = AuthConfig()
    def __init__(self, scope: str = 'user-read-private') -> None:
        self.scope = scope
        info_logger.info(f'Instantiate AuthCodeFlow for scope {scope}')
        self.refreshing_token = self.authenticate(scope)
        info_logger.info(f'AuthCodeFlow for scope {scope} successfull')

    @property
    def get_req_header(self):
        return {
            "Authorization": "Bearer " + self.refreshing_token.get_access_token()
        }

    def reset_refreshing_token(self, scope: str) -> None:
        self.refreshing_token.access_token.delete_tokens()
        self.scope += f' {scope}'
        self.refreshing_token = self.authenticate(self.scope)

    def get_auth_code(self, scope: str) -> AuthCodeRequest:
        return AuthCodeRequest(
            client = self.client, 
            auth_config = self.auth_config,
            scope = scope)

    def get_refreshing_token(
            self, auth_code_request: AuthCodeRequest) -> RefreshingToken:
        try:
            return RefreshingToken(
                auth_code_request= auth_code_request
            )
        except LostRefreshTokenError as e:
            info_logger.warning(e)
            try:
                return RefreshingToken(
                    auth_code_request= auth_code_request
                )
            except:
                info_logger.exception()
                raise

    def authenticate(self, scope: str) -> RefreshingToken:

        auth_code_request = self.get_auth_code(scope)
        return self.get_refreshing_token(
            auth_code_request=auth_code_request)

    def get_request(self, endpoint:str, params: dict = None) -> dict:
        url = f'{endpoint}'
        return conf_requests.get(url=url, headers=self.get_req_header, params=params)

    def check_scope(self, scope: str):
        authorized_scopes = self.refreshing_token._retrieve_access_token().scopes
        if scope not in authorized_scopes:
            raise MissingScopeError(
                msg='Not authorized for required scope', scope=scope)
        

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

    def get_request(self, endpoint:str, params: dict = None) -> dict:
        url = f'{endpoint}'
        return conf_requests.get(url=url, headers=self.get_req_header, params=params)

    def check_scope(scope: str):
        pass