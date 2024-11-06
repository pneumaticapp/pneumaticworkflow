from rest_framework.pagination import LimitOffsetPagination


class WorkflowPagination(LimitOffsetPagination):
    default_limit = 15
    max_limit = 1000
