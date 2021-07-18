import json
from abc import ABC, abstractmethod
import datetime

class Token(ABC):
    def _set_access_token_expiry(self, expires_in):
        expires_in_delta = datetime.timedelta(seconds = expires_in)
        return datetime.datetime.now(datetime.timezone.utc) + expires_in_delta

    def is_expired(self):
        return self.expires_at < datetime.datetime.now(datetime.timezone.utc)

class AccessToken(Token):
    created_at = datetime.datetime.now()
    def __init__(self, access_token_content, load_from_cache = False) -> None:
        self.access_token_content = access_token_content
        if not load_from_cache:
            self.expires_at = self._set_access_token_expiry(
                self.access_token_content['expires_in'])
        else:
            self.expires_at = datetime.datetime.fromisoformat(
                access_token_content['expires_at'])
        self.save_tokens()

    @property
    def access_token(self):
        return self.access_token_content['access_token']

    @property
    def refresh_token(self):
        return self.access_token_content['refresh_token']

    def save_tokens(self):
        token_information = self.access_token_content
        token_information['expires_at'] = self.expires_at.isoformat()
        with open('./src/config/tokens.json', 'w') as file:
            json.dump(token_information, file, indent=2)       