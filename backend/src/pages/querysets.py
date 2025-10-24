from django.db.models import QuerySet

from src.pages.enums import PageType


class PageQuerySet(QuerySet):

    def public(self):
        return self.filter(slug__in=PageType.PUBLIC_TYPES)
