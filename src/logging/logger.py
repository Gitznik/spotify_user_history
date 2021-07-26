import logging
import logging.config
from types import FunctionType
import yaml
from requests.exceptions import HTTPError

from ..errors.errors import ConfigFileMissing

try:
    with open('src/logging/log_conf.yaml', 'r') as conf:
        config = yaml.safe_load(conf.read())
        logging.config.dictConfig(config)
except FileNotFoundError:
    raise ConfigFileMissing('Log config file missing.')

info_logger = logging.getLogger('infoLogger')
debug_logger = logging.getLogger('debugLogger')
api_logger = logging.getLogger('apiLogger')


def ApiLogger(msg:str = None):
    def decorator(func: FunctionType):
        def wrapper(*args, **kwargs):
            api_logger.info(f'Starting Api Call: {msg}')
            try:
                result = func(*args, **kwargs)
                api_logger.info(f'Finished Api Call: {msg}')
                return result
            except HTTPError as e:
                api_logger.exception(f'Received error status code in {func.__name__}')
                raise e
            except:
                api_logger.exception(f'Encountered an unexpected exception in {func.__name__}')
                raise
        return wrapper
    return decorator
