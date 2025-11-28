from typing import NamedTuple, Optional

from typing_extensions import TypedDict


class UserData(TypedDict):

    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    company_name: Optional[str]
    photo: Optional[str]
    job_title: Optional[str]


class SSOConfigData(NamedTuple):

    client_id: str
    client_secret: str
    domain: str
    redirect_uri: str
