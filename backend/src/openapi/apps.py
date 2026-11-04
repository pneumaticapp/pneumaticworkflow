from django.apps import AppConfig


class OpenApiConfig(AppConfig):
    name = 'src.openapi'
    verbose_name = 'API documentation'

    def ready(self) -> None:
        from src.openapi import auth_extensions  # noqa: F401, PLC0415
        from src.openapi import field_extensions  # noqa: F401, PLC0415
        from src.openapi import view_extensions  # noqa: F401, PLC0415
