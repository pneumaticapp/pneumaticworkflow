from django.contrib.auth import get_user_model

from pneumatic_backend.generics.querysets import BaseQuerySet


UserModel = get_user_model()


class DeviceQuerySet(BaseQuerySet):

    def by_user(self, user_id: int):
        return self.filter(user_id=user_id)

    def active(self):
        return self.filter(is_active=True)

    def delete_by_token(self, token: str):
        return self.filter(token=token).delete()

    def app(self):
        return self.filter(is_app=True)

    def browser(self):
        return self.filter(is_app=False)
