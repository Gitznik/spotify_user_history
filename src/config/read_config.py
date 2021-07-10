import yaml
import os

class YamlConfig:
    def __init__(self) -> None:
        self.read_secrets()

    def load_config(self, file_name:str = 'spotify_secrets.yml') -> dict:
        filepath = os.path.join(
            os.path.dirname(__file__), file_name)
        with open(filepath) as configuration:
            return (yaml.full_load(configuration))

    def read_secrets(self):
        config = self.load_config()
        self.client_id = config['client-information']['client-id']
        self.client_secret = config['client-information']['client-secret']