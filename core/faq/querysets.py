from django.db.models import QuerySet


class FaqItemQuerySet(QuerySet):

    def active(self):
        return self.filter(is_active=True)
