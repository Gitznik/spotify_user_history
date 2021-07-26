from ..logging.logger import info_logger

class InvalidAccessTokenError(Exception):
    def __init__(self, msg):
        self.msg = msg
        info_logger.exception(msg)
        super().__init__(self.msg)

class LostRefreshTokenError(Exception):
    def __init__(self, msg):
        self.msg = msg
        info_logger.exception(msg)
        super().__init__(self.msg)

class InvalidDirectoryError(Exception):
    def __init__(self, msg):
        self.msg = msg
        info_logger.exception(msg)
        super().__init__(self.msg)