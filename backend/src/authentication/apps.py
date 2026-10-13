from django.apps import AppConfig


class AuthConfig(AppConfig):
    name = 'src.authentication'
    verbose_name = 'Auth'

    def ready(self):
        # Authentication schemes reference user and MCP models.
        from src.authentication import schema  # noqa: F401, PLC0415
