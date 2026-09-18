from typing import Dict, Type
from typing_extensions import TypedDict
from src.ai.services.handlers.base import BaseHandler


class ProviderConfig(TypedDict):

    name: str
    slug: str
    base_url: str
    handler: Type[BaseHandler]
    endpoints: Dict[str, str]
