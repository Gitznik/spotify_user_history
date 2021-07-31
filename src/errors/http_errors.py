from requests.models import HTTPError

class SpotifyHttpError(Exception):
    def __init__(self, e: HTTPError, msg: str = ''):
        original_error = str(e)
        spotify_error = e.response.json()['error']['message']
        self.msg = f'{original_error} --- {spotify_error} --- {msg}'
        super().__init__(self.msg)