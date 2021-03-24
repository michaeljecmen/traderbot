"""Custom exceptions module for the traderbot ecosystem."""

class TraderbotException(Exception):
    def __init__(self, message='an exception was thrown'):
        self.message = message
        super().__init__(self.message)
    

class ConfigException(TraderbotException):
    def __init__(self, message='your config.json file was malformed'):
        super().__init__(message=message)


class APIException(TraderbotException):
    def __init__(self, message='your API usage was incorrect'):
        super().__init__(message=message)