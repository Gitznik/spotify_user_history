import yaml
import os
from abc import ABC, abstractmethod

from ..errors.config_errors import MissingConfigError
from ..errors.errors import InvalidDirectoryError

class YamlConfig(ABC):
    def __init__(self, file_name: str) -> None:
        self.file_path = os.path.join(
            os.path.dirname(__file__), file_name)

    def load_config(self) -> dict:
        try:
            with open(self.file_path, 'r') as configuration:
                return (yaml.full_load(configuration))
        except FileNotFoundError:
            raise MissingConfigError(f'Config at {self.file_path} missing.')

    @abstractmethod
    def read_secrets():
        pass

class ClientConfig(YamlConfig):
    def __init__(self, file_name: str = 'spotify_secrets.yml') -> None:
        super().__init__(file_name)
        self.read_secrets()

    def read_secrets(self):
        config = self.load_config()
        self.client_id = config['client-information']['client-id']
        self.client_secret = config['client-information']['client-secret']
        self.redirect_url = config['client-information']['redirect_url']

class AuthConfig(YamlConfig):
    def __init__(self, file_name: str = 'auth_codes_secrets.yml') -> None:
        super().__init__(file_name)
        self.read_secrets()

    def read_secrets(self):
        config = self.load_config()
        self.config = config or {}
        self.scopes = config.keys() if config else []

    def add_auth_code(self, scope: str, auth_code: str) -> None:
        self.config[scope] = auth_code
        self.save_auth_codes()

    def remove_auth_code(self, scope: str) -> None:
        self.config.pop(scope)
        self.save_auth_codes()

    def save_auth_codes(self):
        try:
            with open(self.file_path, 'w') as configuration:
                return (yaml.dump(self.config, configuration, default_flow_style = False))
        except FileNotFoundError:
            InvalidDirectoryError(
                f'Excpected directory for saving' + 
                f'{self.file_path} does not exist')