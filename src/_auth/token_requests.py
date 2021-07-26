from urllib.parse import urlencode, urlparse, parse_qs
import json

from ..config.parse_config_files import AuthConfig
from ..client import Client
from .tokens import AccessToken
from ..logging.logger import ApiLogger, info_logger, debug_logger, api_logger
from ..config.configure_requests import configure_request

conf_requests = configure_request()

class AuthCodeRequest:
    auth_url = 'https://accounts.spotify.com/authorize'

    def __init__(
            self, 
            client: Client, 
            auth_config: AuthConfig,
            scope: str) -> None:
        info_logger.info(f'Creating new Auth Code Request for scope {scope}')
        self.client = client
        self.auth_config = auth_config
        self.scope = scope

    @property
    def auth_code(self) -> str:
        if self.scope in self.auth_config.scopes:
            info_logger.info('Aquire existing authentification code')
            return self.auth_config.config[self.scope]
        auth_code = self._prompt_user_authorization()
        self.auth_config.add_auth_code(
            scope = self.scope,
            auth_code=auth_code
        )
        return auth_code

    def _prompt_user_authorization(self):
        info_logger.info(
            f'Prompting user for authorization for scope {self.scope}')
        auth_url = self._create_auth_url()
        print(f'Please visit this URL: {auth_url}')
        redirected_url = input(
            'Please paste the URL you were redirected to:').strip()
        return self._parse_url_param(redirected_url, 'code')

    def _create_auth_url(self) -> str:
        debug_logger.debug('Creating URL for user authorization')
        params = {
            'client_id': self.client.client_config.client_id,
            'response_type': 'code',
            'redirect_uri': self.client.client_config.redirect_url,
            'scope': self.scope,
            'show_dialog': 'false',
        }
        return self.auth_url + '?' + urlencode(params)

    def _parse_url_param(self, url, param):
        try:
            query = urlparse(url).query
            code = parse_qs(query).get(param, None)
            info_logger.info(f'New authentification code for {self.scope} aquired')
            return code[0]
        except ValueError as err:
            info_logger.exception(str(err))
            raise
        

class RefreshingToken:
    token_url = 'https://accounts.spotify.com/api/token'

    def __init__(
            self, 
            auth_code_request: AuthCodeRequest) -> None:
        info_logger.info(
            f'Instantiate RefreshingToken for scope {auth_code_request.scope}')
        self.auth_code_request = auth_code_request
        self.access_token = self._retrieve_access_token()

    def get_access_token(self):
        info_logger.info('Request access token')
        if self.access_token.is_expired():
            info_logger.info(
                'Access token expired, retrieve new access token')
            self.access_token = self._retrieve_access_token(refresh = True)
        return self.access_token.access_token

    @ApiLogger(msg='Acquire access token')
    def _request_access_token(self, refresh = False):
        if refresh:
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.access_token.refresh_token,
            }
        else:
            data = {
                'grant_type': 'authorization_code',
                'code': self.auth_code_request.auth_code,
                'redirect_uri': self.auth_code_request.client.client_config.redirect_url,
            }
            self.auth_code_request.auth_config.remove_auth_code(
                self.auth_code_request.scope)

        headers = {
            'Authorization': f'Basic {self.auth_code_request.client.get_auth_string()}'
        }

        return conf_requests.post(
            self.token_url, 
            data = data,
            headers = headers,
            )

    def _load_new_access_token(self, refresh = False):
        access_token_response = self._request_access_token(refresh)
        
        if access_token_response.status_code != 200:
            raise ValueError('Acces token could not be retrieved')
        return AccessToken(access_token_response.json())

    def _load_existing_access_token(self):
        with open('./src/config/tokens.json', 'r') as file:
            access_token_content = json.load(file)
            return AccessToken(
                access_token_content=access_token_content,
                load_from_cache=True)

    def _retrieve_access_token(self, refresh = False):
        if refresh:
            info_logger.info(
                'Aquire new access token with existing refreshing token')
            return self._load_new_access_token(refresh)
        try:
            info_logger.info(
                'Try Load existing access token')
            return self._load_existing_access_token()
        except:
            info_logger.info(
                'Aquire new access token without existing refreshing token')
            return self._load_new_access_token(refresh)
