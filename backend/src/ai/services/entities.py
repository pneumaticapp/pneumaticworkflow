from typing import Dict, Callable
from typing_extensions import TypedDict


class ProviderConfig(TypedDict):

    name: str
    slug: str
    base_url: str
    handler: Callable
    endpoints: Dict[str, str]
