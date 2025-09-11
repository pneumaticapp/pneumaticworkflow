from src.generics.querysets import BaseQuerySet


class IntegrationsQuerySet(BaseQuerySet):
    def active(self):
        return self.filter(is_active=True)
