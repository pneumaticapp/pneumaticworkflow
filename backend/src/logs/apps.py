from django.apps import AppConfig

from src.logs.events.registry import validate_registry


class LogsConfig(AppConfig):

    name = 'src.logs'

    def ready(self):

        """ Check the event declaration table while the process is
            starting.

            A duplicated name, a name that is not "domain.action", a
            category that does not exist or a constant of an events
            class left out of the table are all silent in production:
            the events land in a type or a category nobody can query.
            Failing here turns every one of them into a deployment that
            refuses to start.
        """

        validate_registry()
