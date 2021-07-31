import logging
import logging.config
import yaml

with open('src/logging/log_conf.yaml', 'r') as conf:
    config = yaml.safe_load(conf.read())
    logging.config.dictConfig(config)

info_logger = logging.getLogger('infoLogger')
debug_logger = logging.getLogger('debugLogger')
api_logger = logging.getLogger('apiLogger')