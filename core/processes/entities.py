from typing import Optional, List
from typing_extensions import TypedDict


class TemplateIntegrationsData(TypedDict):

    id: int
    shared: bool
    zapier: bool
    api: bool
    webhooks: bool


class PrivateTemplateIntegrationsData(TemplateIntegrationsData):

    shared_date_tsp: Optional[str]
    zapier_date_tsp: Optional[str]
    api_date_tsp: Optional[str]
    webhooks_date_tsp: Optional[str]


class TaskData(TypedDict):

    name: str
    description: str
    raw_due_date: Optional[dict]


class LibraryTemplateData(TypedDict):

    name: str
    description: str
    category: str
    kickoff: Optional[dict]
    tasks: List[TaskData]
