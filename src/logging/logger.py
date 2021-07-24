import logging
import logging.config
from types import FunctionType
import yaml

with open('src/logging/log_conf.yaml', 'r') as conf:
    config = yaml.safe_load(conf.read())
    logging.config.dictConfig(config)

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
            except:
                api_logger.exception(f'Encountered an exception in {func.__name__}')
        return wrapper
    return decorator
