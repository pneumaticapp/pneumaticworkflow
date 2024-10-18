from typing import Optional


class BaseServiceException(Exception):

    default_message = None

    def __init__(self, message: Optional[str] = None):
        message = message or self.default_message
        if message is None:
            raise Exception(
                'You should specify "message" or "default_message" attribute'
            )
        super().__init__()
        self.message = message


class BaseApiNameException(BaseServiceException):

    def __init__(self, api_name: str, message: Optional[str] = None):
        self.api_name = api_name
        super().__init__(message)
