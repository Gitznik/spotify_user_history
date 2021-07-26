from ..logging.logger import info_logger

class MissingConfigError(Exception):
    def __init__(self, msg):
        self.msg = msg
        info_logger.exception(msg)
        super().__init__(self.msg)