from json.decoder import JSONDecodeError
from logging import info
from requests.models import HTTPError
from ..logging.logger import info_logger

class SpotifyHttpError(Exception):
    def __init__(self, e: HTTPError, msg: str = ''):
        original_error = str(e)
        try:
            spotify_error = e.response.json()['error']['message']
        except JSONDecodeError as err:
            info_logger.warning(
                'Unable to parse spotify error response body' , exc_info=True)
            spotify_error = e.response.text
        self.msg = f'{original_error} --- {spotify_error} --- {msg}'
        super().__init__(self.msg)