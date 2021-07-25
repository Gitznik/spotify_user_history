import json
from abc import ABC, abstractmethod
import datetime
from ..logging.logger import info_logger, debug_logger


class Token(ABC):
    
    def _get_now(self):
        return datetime.datetime.now(datetime.timezone.utc)

    def _set_access_token_expiry(self, expires_in):
        expires_in_delta = datetime.timedelta(seconds = expires_in)
        return self._get_now() + expires_in_delta

    def is_expired(self):
        return self.expires_at < self._get_now()

class AccessToken(Token):
    def __init__(self, access_token_content, load_from_cache = False) -> None:
        self.access_token_content = access_token_content
        if not load_from_cache:
            info_logger.info('Instantiate fresh Access token')
            self.expires_at = self._set_access_token_expiry(
                self.access_token_content['expires_in'])
            if self.access_token_content.get('refresh_token'):
                self.save_refresh_token(access_token_content['refresh_token'])
        else:
            self.expires_at = datetime.datetime.fromisoformat(
                access_token_content['expires_at'])
            info_logger.info('Instantiate Access token from cache')
        self.save_tokens()

    @property
    def access_token(self):
        try:
            return self.access_token_content['access_token']
        except:
            info_logger.exception('Saved Access Token invalid', exc_info=True)

    @property
    def refresh_token(self):
        _refresh_token = self.access_token_content.get('refresh_token')
        if not _refresh_token:
            return self.load_refresh_token()
        return _refresh_token

    def save_refresh_token(self, refresh_token):
        with open('./src/config/refresh_token.json', 'w') as file:
            file.write(refresh_token)

    def load_refresh_token(self):
        with open('./src/config/refresh_token.json', 'r') as file:
            return file.read()

    def save_tokens(self):
        debug_logger.debug('Saving token to cache')
        token_information = self.access_token_content
        token_information['expires_at'] = self.expires_at.isoformat()
        with open('./src/config/tokens.json', 'w') as file:
            json.dump(token_information, file, indent=2)       