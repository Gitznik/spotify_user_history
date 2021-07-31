import json
from abc import ABC, abstractmethod
import datetime
import os

from ..logging.logger import info_logger, debug_logger
from ..errors.token_errors import (
    InvalidAccessTokenError, LostRefreshTokenError)
from ..errors.errors import InvalidDirectoryError


class Token(ABC):
    
    def _get_now(self) -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc)

    def _set_access_token_expiry(self, expires_in: int) -> datetime.datetime:
        expires_in_delta = datetime.timedelta(seconds = expires_in)
        return self._get_now() + expires_in_delta

    def is_expired(self) -> bool:
        return self.expires_at < self._get_now()

class AccessToken(Token):
    def __init__(
            self, 
            access_token_content: dict, 
            load_from_cache: bool = False) -> None:

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
    def access_token(self) -> str:
        try:
            return self.access_token_content['access_token']
        except:
            raise InvalidAccessTokenError('Saved Access Token invalid')

    @property
    def refresh_token(self) -> str:
        _refresh_token = self.access_token_content.get('refresh_token')
        if not _refresh_token:
            return self.load_refresh_token()
        return _refresh_token

    def save_refresh_token(self, refresh_token: str) -> None:
        try:
            with open('./src/config/refresh_token.json', 'w') as file:
                file.write(refresh_token)
        except FileNotFoundError:
            raise InvalidDirectoryError(
                'Directory for saving the refresh token does not exist')

    def load_refresh_token(self) -> str:
        try:
            with open('./src/config/refresh_token.json', 'r') as file:
                return file.read()
        except FileNotFoundError:
            self.delete_tokens()
            info = '''
                Refresh token could not be recovered. 
                Deleted saved access token.
                '''
            raise LostRefreshTokenError(info)

    def save_tokens(self) -> None:
        debug_logger.debug('Saving token to cache')
        token_information = self.access_token_content
        token_information['expires_at'] = self.expires_at.isoformat()
        try:
            with open('./src/config/tokens.json', 'w') as file:
                json.dump(token_information, file, indent=2)
        except FileNotFoundError:
            raise InvalidDirectoryError(
                'Directory for saving the access token does not exist')

    def delete_tokens(self) -> None:
        os.remove('./src/config/tokens.json')