from typing import Optional, Union

from src.authentication.enums import AuthTokenType
from src.logs.events.emitter import emit
from src.logs.events.enums import ActorType
from src.logs.events.schema import Actor, EventObject


class EventEmitMixin:

    """ Publishing an event from a service that knows who is acting.

        The service brings the actor, the caller of _publish names
        the event and the object it is about. Without this the actor
        and the object of every event were built again at each call
        site, and each site had to remember that a service running
        without a user is a background job, not an anonymous person.

        A view publishes through AuditEventService instead: there the
        request is at hand and the actor comes from it. """

    user = None
    auth_type: AuthTokenType.LITERALS = AuthTokenType.USER

    def _publish(
        self,
        event_type: str,
        *,
        account_id: int,
        object_type: str,
        object_id: Optional[Union[int, str]] = None,
        payload: Optional[dict] = None,
        actor: Optional[Actor] = None,
        **fields,
    ) -> None:

        """ Anything else an event may carry (workflow_id, task_id,
            ts) goes through fields, straight to emit().

            actor names somebody other than the person the service
            acts for: accepting an invite is done by the invited
            person, while the service is built around them as its
            request user. """

        emit(
            event_type,
            account_id=account_id,
            actor=actor or self._event_actor(),
            event_object=EventObject(type=object_type, id=object_id),
            payload=payload,
            **fields,
        )

    def _event_actor(self) -> Actor:

        """ The person the service acts for, or the system when it
            acts for nobody: a background job, a task of the queue,
            a management command. """

        if self.user is None:
            return Actor(type=ActorType.SYSTEM)
        return Actor.from_user(self.user, self.auth_type)
