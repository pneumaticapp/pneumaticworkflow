from typing import Optional
from typing_extensions import TypedDict


class ValidationErrorData(TypedDict):

    code: str
    message: str
    details: Optional[dict]
