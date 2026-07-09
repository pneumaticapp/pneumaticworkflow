from unittest.mock import Mock

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.utils import translation
from rest_framework.request import Request

from src.authentication.locale import (
    install_api_locale_activation,
    resolve_request_language,
)


@pytest.mark.parametrize('language', ['en', 'ru', 'de'])
def test_resolve_request_language__authenticated_user(language):
    django_request = RequestFactory().get('/')
    drf_request = Request(django_request)
    drf_request.user = Mock(is_anonymous=False, language=language)

    assert resolve_request_language(drf_request) == language


def test_resolve_request_language__anonymous_uses_accept_language():
    django_request = RequestFactory().get(
        '/',
        HTTP_ACCEPT_LANGUAGE='de',
    )
    drf_request = Request(django_request)
    drf_request.user = AnonymousUser()

    assert resolve_request_language(drf_request) == 'de'


def test_resolve_request_language__activates_translation():
    django_request = RequestFactory().get('/')
    drf_request = Request(django_request)
    drf_request.user = Mock(is_anonymous=False, language='ru')

    translation.activate(resolve_request_language(drf_request))
    try:
        assert translation.get_language() == 'ru'
    finally:
        translation.deactivate()


def test_install_api_locale_activation__hooks_perform_authentication():
    from rest_framework.views import APIView

    install_api_locale_activation()

    assert getattr(
        APIView.perform_authentication,
        '_locale_hook_installed',
        False,
    )
