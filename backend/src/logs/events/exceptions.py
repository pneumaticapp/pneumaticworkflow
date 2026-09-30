from typing import Optional


class EventsError(Exception):

    """ Base error of the events pipeline. """


class UnknownEventTypeError(EventsError):

    """ Event type is not declared in the registry. """


class SinkTemporaryError(EventsError):

    """ Delivery failed, the batch has to be retried and not acked.

        retry_after is the pause the receiver asked for, in seconds,
        and None when it asked for none: the consumer prefers it over
        its own backoff. """

    def __init__(self, *args, retry_after: Optional[float] = None):
        super().__init__(*args)
        self.retry_after = retry_after


class SinkPermanentError(EventsError):

    """ Delivery failed for good, the batch goes to the dead letter. """
