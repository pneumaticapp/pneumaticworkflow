from typing import Dict, NamedTuple, Callable
from typing_extensions import TypedDict


class ProviderConfig(TypedDict):

    name: str
    slug: str
    base_url: str
    handler: Callable
    endpoints: Dict[str, str]


class FieldTag(NamedTuple):

    """ A <field> tag of the agent answer """

    value: str
    attrs: Dict[str, str]
