from django.test import RequestFactory, SimpleTestCase, override_settings
from django.utils import translation
from rest_framework.exceptions import ValidationError

from src.accounts.enums import Language
from src.accounts.serializers.user import UserSerializer


class SyrianArabicLanguageTests(SimpleTestCase):

    def test_profile_accepts_syrian_arabic_for_every_deployment_language(self):
        for language in Language.VALUES:
            with self.subTest(language=language):
                with override_settings(LANGUAGE_CODE=language):
                    field = UserSerializer().fields['language']
                    self.assertEqual(
                        field.run_validation(Language.ar_sy),
                        Language.ar_sy,
                    )
                    self.assertEqual(
                        field.to_representation(Language.ar_sy),
                        Language.ar_sy,
                    )

    def test_non_russian_deployments_keep_russian_language_restricted(self):
        for language in Language.EURO_VALUES:
            with self.subTest(language=language):
                with override_settings(LANGUAGE_CODE=language):
                    field = UserSerializer().fields['language']
                    with self.assertRaises(ValidationError):
                        field.run_validation(Language.ru)

    @override_settings(LANGUAGE_CODE=Language.ru)
    def test_russian_deployment_accepts_existing_languages_and_syrian_arabic(self):
        field = UserSerializer().fields['language']
        for language in Language.VALUES:
            with self.subTest(language=language):
                self.assertEqual(field.run_validation(language), language)

    def test_profile_rejects_unsupported_language(self):
        field = UserSerializer().fields['language']
        with self.assertRaises(ValidationError):
            field.run_validation('xx')

    def test_syrian_arabic_uses_rtl_direction(self):
        with translation.override(Language.ar_sy):
            self.assertTrue(translation.get_language_bidi())

    @override_settings(
        LANGUAGE_CODE=Language.en,
        LANGUAGES=Language.EURO_CHOICES,
    )
    def test_accept_language_selects_syrian_arabic(self):
        request = RequestFactory().get(
            '/',
            HTTP_ACCEPT_LANGUAGE='ar-SY,ar;q=0.9,en;q=0.8',
        )
        self.assertEqual(
            translation.get_language_from_request(request),
            Language.ar_sy,
        )
