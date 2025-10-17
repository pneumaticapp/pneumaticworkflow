from typing_extensions import TypedDict

from src.analytics.customerio.enums import MetricType


class WebHookUserData(TypedDict):

    id: int


class WebHookMetricData(TypedDict):

    identifiers: WebHookUserData


class WebHookData(TypedDict):

    metric: MetricType
    data: WebHookMetricData
