from django.utils import translation
from rest_framework_simplejwt.authentication import JWTAuthentication


class PneumaticJWTAuthentication(JWTAuthentication):

    def authenticate(self, request):
        result = super().authenticate(request)
        if result:
            user, _ = result
            translation.activate(user.language)
        return result
