from types import FunctionType
from typing import Union
from requests.exceptions import HTTPError
from requests.models import Response
import time

from .errors.http_errors import SpotifyHttpError
from .logging.logger import api_logger, info_logger, debug_logger

def ApiLogger(msg:str = None, err_handling: bool = True):
    def decorator(func: FunctionType):
        def wrapper(*args, **kwargs):
            api_logger.info(f'Starting Api Call: {msg}')
            try:
                result = func(*args, **kwargs)
                api_logger.info(f'Finished Api Call: {msg}')
                return result
            except HTTPError as e:
                try:
                    api_logger.warning(
                        f'Received error status code in {func.__name__}')
                    result = RequestErrorFactory(
                        e, func, *args, **kwargs).evaluate_action()
                    if type(result) is not SpotifyHttpError:
                        return result
                    raise result
                except SpotifyHttpError as e:
                    api_logger.exception('Could not handle API error')
                    raise e from None
            except:
                api_logger.exception(
                    f'Encountered an unexpected exception in {func.__name__}')
                raise
        return wrapper
    return decorator

class RequestErrorFactory:

    def __init__(
            self, 
            error: HTTPError, 
            func: FunctionType, 
            *args, **kwargs) -> None:
        self.error = error
        self.func = func
        self.response = self.error.response
        self.request = self.error.request
        self.status_code = self.response.status_code

        self.evaluate_action(*args, **kwargs)

    def unauthorized(self) -> SpotifyHttpError:
        debug_logger.debug('Trying to resolve unauthorized request error')
        msg = ''' Please make sure you are using a authentification flow with
        access to the data you are requesting, and a matching scope./n
        If you are accessing another users data, you may not be authorized to 
        do so.'''
        return self.create_error(msg)


    def not_found(self, *args, **kwargs) -> Union[SpotifyHttpError, Response]:
        debug_logger.debug('Trying to resolve object not found error')
        self.wait()
        try:
            return self.func(*args, **kwargs)
        except:
            msg = ''' The requested resource was not found. This did not
            resolve after waiting for one minute'''
            return self.create_error(msg)

    def rate_limited(self, *args, **kwargs):
        debug_logger.debug('Trying to resolve Rate Limited error')
        try:
            retry_after = self.response.headers['Retry-After']
        except KeyError as e:
            msg = ''' There was a rate limited error, but no retry time was 
            provided by the Spotify API. Please retry after a few minutes'''
            return self.create_error(msg)

        self.wait(retry_after)
        return self.func(*args, **kwargs)

    def wait(self, seconds:int = 60) -> None:
        time.sleep(seconds)

    def create_error(self, msg: str = '') -> SpotifyHttpError:
        return SpotifyHttpError(e = self.error, msg = msg)

    def evaluate_action(self, *args, **kwargs):
        status = self.status_code
        debug_logger.debug(f'Evaluating action for code {status}')
        if status in [401, 403]:
            return self.unauthorized()
        if status == 404:
            return self.not_found(*args, **kwargs)
        if status == 429:
            return self.rate_limited(*args, **kwargs)
        debug_logger.debug(
            'No exception handling found for this error code, ' + 
            'raise generic error')
        return self.create_error()
