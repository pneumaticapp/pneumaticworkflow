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
            the third leaks a field past the redaction rule of the
            collector. Failing here turns every one of them into a
            deployment that refuses to start.
        """

        validate_registry()
