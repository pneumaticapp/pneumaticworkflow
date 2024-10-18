from typing import Optional, List
from typing_extensions import TypedDict
from pneumatic_backend.accounts.enums import SourceType


class InviteData(TypedDict):

    invited_from: SourceType
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    photo: Optional[str]
    groups: Optional[List[int]]
