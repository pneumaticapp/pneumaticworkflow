from django.apps import AppConfig

from src.logs.events.registry import validate_registry


class LogsConfig(AppConfig):

    name = 'src.logs'

    def ready(self) -> None:

        """ Check the event declaration table while the process is
            starting.

            A duplicated name, a name that is not "domain.action" or a
            personal data path that resolves to nothing are all silent
            in production: the first two give a type nobody can query,
            the third sends a personal field outside the pii.*
            namespace that names one. Failing here turns every one of
            them into a deployment that refuses to start.

            The receiver of the admin site log is connected here and
            not by a decorator: the module imports LogEntry, which is
            not importable before the apps are loaded.
        """

        validate_registry()
        from django.contrib.admin.models import LogEntry  # noqa: PLC0415
        from django.db.models.signals import post_save  # noqa: PLC0415

        from src.logs.events.admin_site import (  # noqa: PLC0415
            publish_log_entry,
        )
        post_save.connect(
            publish_log_entry,
            sender=LogEntry,
            dispatch_uid='src.logs.events.admin_site.publish_log_entry',
        )
