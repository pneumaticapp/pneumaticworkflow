from typing import Optional
from pneumatic_backend.generics.exceptions import BaseServiceException
from pneumatic_backend.payment import messages


class WebhookServiceException(BaseServiceException):

    def __init__(
        self,
        message: Optional[str] = None,
        **kwargs: dict
    ):
        super().__init__(message)
        self.details = kwargs


class StripeServiceException(BaseServiceException):

    def __init__(
        self,
        message: Optional[str] = None,
        **kwargs: dict
    ):
        super().__init__(message)
        self.details = kwargs


class DecreaseSubscription(StripeServiceException):

    default_message = messages.MSG_BL_0004


class SubscriptionNotExist(StripeServiceException):

    default_message = messages.MSG_BL_0005


class MultipleSubscriptionsNotAllowed(StripeServiceException):

    default_message = messages.MSG_BL_0006


class NoEffectPurchase(StripeServiceException):

    default_message = messages.MSG_BL_0007


class NotExistentPrice(StripeServiceException):

    default_message = messages.MSG_BL_0003

    def __init__(self, code: str):
        super().__init__()
        self.message = self.default_message(code)


class CardError(StripeServiceException):

    default_message = messages.MSG_BL_0008


class PaymentError(StripeServiceException):

    default_message = messages.MSG_BL_0009


class ChangeCurrencyDisallowed(StripeServiceException):

    default_message = messages.MSG_BL_0010


class SubsMaxQuantityReached(StripeServiceException):

    default_message = messages.MSG_BL_0011

    def __init__(self, quantity: int, product_name: str):
        super().__init__()
        self.message = messages.MSG_BL_0011(quantity, product_name)


class SubsMinQuantityReached(StripeServiceException):

    default_message = messages.MSG_BL_0012

    def __init__(self, quantity: int, product_name):
        super().__init__()
        self.message = messages.MSG_BL_0012(quantity, product_name)


class MaxQuantityReached(StripeServiceException):

    default_message = messages.MSG_BL_0013

    def __init__(self, quantity: int, product_name: str):
        super().__init__()
        self.message = messages.MSG_BL_0013(quantity, product_name)


class MinQuantityReached(StripeServiceException):

    default_message = messages.MSG_BL_0014

    def __init__(self, quantity: int, product_name: str):
        super().__init__()
        self.message = messages.MSG_BL_0014(quantity, product_name)


class UnsupportedPlan(StripeServiceException):

    default_message = messages.MSG_BL_0015


class PurchaseArchivedPrice(StripeServiceException):

    default_message = messages.MSG_BL_0016


class NotFoundAccountForSubscription(StripeServiceException):

    default_message = messages.MSG_BL_0017


class BillingSyncDisabled(StripeServiceException):

    default_message = messages.MSG_BL_0018


class AccountNotFound(WebhookServiceException):

    default_message = messages.MSG_BL_0019


class AccountOwnerNotFound(WebhookServiceException):

    default_message = messages.MSG_BL_0020
