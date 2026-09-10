class EventsError(Exception):

    """ Base error of the events pipeline. """


class UnknownEventTypeError(EventsError):

    """ Event type is not declared in the registry. """


class SinkTemporaryError(EventsError):

    """ Delivery failed, the batch has to be retried and not acked. """


class SinkPermanentError(EventsError):

    """ Delivery failed for good, the batch goes to the dead letter. """
