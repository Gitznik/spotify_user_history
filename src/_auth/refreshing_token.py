import yaml
from urllib.parse import urlencode, urlparse, parse_qs

from ..config.parse_config_files import ClientConfig, AuthConfig

class RefreshingToken:
    auth_url = 'https://accounts.spotify.com/authorize'
    token_url = 'https://accounts.spotify.com/api/token'

    def __init__(
            self, 
            client_config: ClientConfig, 
            auth_config: AuthConfig,
            scope: str) -> None:
        self.client_config = client_config
        self.auth_config = auth_config
        self.scope = scope
        self.auth_code = self.get_auth_code()

    def prompt_user_authorization(self):
        auth_url = self.create_auth_url()
        print(f'Please visit this URL: {auth_url}')
        redirected_url = input(
            'Please paste the URL you were redirected to:').strip()
        return self.parse_url_param(redirected_url, 'code')

    def create_auth_url(self) -> str:
        params = {
            'client_id': self.client_config.client_id,
            'response_type': 'code',
            'redirect_uri': self.client_config.redirect_url,
            'scope': self.scope,
            'show_dialog': 'false',
        }
        return self.auth_url + '?' + urlencode(params)

    def parse_url_param(self, url, param):
        query = urlparse(url).query
        code = parse_qs(query).get(param, None)
        return code[0]

    def get_auth_code(self) -> str:
        if self.scope in self.auth_config.scopes:
            return self.auth_config.config[self.scope]
        auth_code = self.prompt_user_authorization()
        self.auth_config.add_auth_code(
            scope = self.scope,
            auth_code=auth_code
        )
        return auth_code