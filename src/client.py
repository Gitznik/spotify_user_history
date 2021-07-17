from .config.parse_config_files import ClientConfig
import base64


class Client:
    client_config = ClientConfig()

    def get_auth_string(self) -> None:
        client = f'{self.client_config.client_id}:{self.client_config.client_secret}'
        return base64.b64encode(
            client.encode('ascii')
            ).decode('ascii')