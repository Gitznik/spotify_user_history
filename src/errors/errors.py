from ..logging.logger import info_logger

class InvalidDirectoryError(Exception):
    def __init__(self, msg):
        self.msg = msg
        info_logger.exception(msg)
        super().__init__(self.msg)

class ConfigFileMissing(Exception):
    def __init__(self, msg):
        self.msg = msg
        info_logger.exception(msg)
        super().__init__(self.msg)