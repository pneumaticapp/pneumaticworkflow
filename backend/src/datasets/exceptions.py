from src.generics.exceptions import BaseServiceException
from src.datasets.messages import MSG_DS_0001


class DataSetServiceException(BaseServiceException):

    pass


class DataSetNameNotUniqueException(DataSetServiceException):

    default_message = MSG_DS_0001
