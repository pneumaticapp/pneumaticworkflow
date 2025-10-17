from typing import List, Optional

from typing_extensions import TypedDict

from src.accounts.enums import SourceType


class InviteData(TypedDict):

    invited_from: SourceType.LITERALS
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    photo: Optional[str]
    groups: Optional[List[int]]
