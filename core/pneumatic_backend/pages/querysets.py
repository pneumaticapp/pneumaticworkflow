from django.db.models import QuerySet
from pneumatic_backend.pages.enums import PageType


class PageQuerySet(QuerySet):

    def public(self):
        return self.filter(slug__in=PageType.PUBLIC_TYPES)
