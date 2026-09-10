from abc import ABC, abstractmethod
from typing import List, Tuple

from src.logs.events.exceptions import SinkTemporaryError
from src.logs.events.schema import Event


class BaseSink(ABC):

    """ Delivery target of a batch read from the event stream.

        A record is a (stream id, event) pair: the consumer acks by
        stream id, the sink sends the event.

        send() is the template method. Every transport error goes
        through _handle_error(), so the consumer sees only
        SinkTemporaryError and SinkPermanentError. """

    name = ''

    def send(self, records: List[Tuple[str, Event]]) -> None:
        if not records:
            return
        try:
            self._send(records)
        except Exception as exc:
            self._handle_error(exc, records)
            # _handle_error has to raise. A subclass that returns
            # instead would report a batch as delivered and the
            # consumer would ack records nobody received.
            raise SinkTemporaryError(
                f'{type(self).__name__} did not classify '
                f'the delivery error: {exc!r}',
            ) from exc

    @abstractmethod
    def _send(self, records: List[Tuple[str, Event]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def _handle_error(
        self,
        exc: Exception,
        records: List[Tuple[str, Event]],
    ) -> None:

        """ Classify the transport error and raise a pipeline one. """

        raise NotImplementedError
