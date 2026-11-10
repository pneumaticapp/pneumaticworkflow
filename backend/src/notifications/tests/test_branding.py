from types import SimpleNamespace
from unittest.mock import Mock, patch
from xml.etree import ElementTree

from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles import finders
from django.template.loader import get_template
from django.test import SimpleTestCase, override_settings

from src.ai.services.handlers.openrouter import OpenRouterHandler
from src.branding import (
    ORGANIZATION_NAME,
    ORGANIZATION_NAME_AR,
    PRODUCT_NAME,
    PRODUCT_NAME_AR,
)
from src.notifications.clients.smtp import SMTPEmailClient
from src.notifications.enums import EmailType


@override_settings(
    FRONTEND_URL='https://example.test',
    STATICFILES_STORAGE=(
        'django.contrib.staticfiles.storage.StaticFilesStorage'
    ),
)
class DisplayBrandingTests(SimpleTestCase):
    """Rendering and mocks only: no account, session, database or delivery."""

    def smtp_client(self):
        client = object.__new__(SMTPEmailClient)
        client.account_id = 0
        client.connection = Mock()
        return client

    def test_default_email_templates_use_the_ministry_identity(self):
        data = {
            'link': 'https://example.test/task',
            'unsubscribe_link': 'https://example.test/unsubscribe',
        }
        original = data.copy()
        client = self.smtp_client()
        cases = (
            (EmailType.RESET_PASSWORD, 'auth.html'),
            (EmailType.NEW_TASK, 'tasks.html'),
            (EmailType.COMPLETE_WORKFLOW, 'workflows.html'),
            (EmailType.TASKS_DIGEST, 'digests.html'),
        )
        for code, filename in cases:
            with self.subTest(filename=filename):
                _, html = client._get_default_template(code, filename, data)
                self.assertIn('row-footer', html)
                self.assertIn(PRODUCT_NAME, html)
                self.assertIn(PRODUCT_NAME_AR, html)
                self.assertIn(ORGANIZATION_NAME, html)
                self.assertIn(ORGANIZATION_NAME_AR, html)
                self.assertIn('https://example.test/unsubscribe', html)
                self.assertNotIn('Pneumatic', html)
                self.assertNotIn('pneumatic.app', html)
                self.assertNotIn('Dallas', html)
                self.assertNotIn('apps.apple.com', html)
                self.assertNotIn('play.google.com', html)
        self.assertEqual(data, original)

    def test_explicit_account_logo_remains_available(self):
        _, html = self.smtp_client()._get_default_template(
            EmailType.RESET_PASSWORD,
            'auth.html',
            {'logo_lg': 'https://example.test/custom-logo.png'},
        )
        self.assertIn('src="https://example.test/custom-logo.png"', html)
        self.assertIn(ORGANIZATION_NAME, html)

    def test_saved_template_override_is_rendered_without_rebranding(self):
        client = self.smtp_client()
        template = SimpleNamespace(
            subject='Pneumatic notice for {{ name }}',
            content='<p>Pneumatic {{ name }}</p>',
        )
        with patch(
            'src.notifications.clients.smtp.'
            'EmailTemplateModel.objects.filter',
        ) as select, patch(
            'src.notifications.clients.smtp.EmailMessage',
        ) as email:
            select.return_value.first.return_value = template
            client.send_email(
                to='reader@example.test',
                template_code=EmailType.RESET_PASSWORD,
                message_data={'name': 'Example'},
                user_id=0,
            )
        self.assertEqual(
            email.call_args.kwargs['subject'],
            'Pneumatic notice for Example',
        )
        self.assertEqual(
            email.call_args.kwargs['body'],
            '<p>Pneumatic Example</p>',
        )
        email.return_value.send.assert_called_once()

    def test_default_subject_and_fallback_use_the_product_name(self):
        client = self.smtp_client()
        self.assertEqual(
            client._get_default_subject(EmailType.MENTION, {}),
            f'You have been mentioned on {PRODUCT_NAME}',
        )
        _, html = client._get_fallback_template(EmailType.NEW_TASK, {})
        self.assertIn(PRODUCT_NAME, html)
        self.assertIn(ORGANIZATION_NAME, html)
        self.assertNotIn('Pneumatic', html)

    def test_workflow_name_subject_is_not_rebranded(self):
        subject = self.smtp_client()._get_default_subject(
            EmailType.NEW_TASK,
            {'workflow_name': 'Pneumatic import review'},
        )
        self.assertEqual(subject, 'Pneumatic import review')

    def test_admin_and_api_display_titles(self):
        self.assertIn(PRODUCT_NAME_AR, admin.site.site_header)
        self.assertIn(ORGANIZATION_NAME_AR, admin.site.site_header)
        self.assertIn(PRODUCT_NAME, admin.site.site_title)
        self.assertEqual(
            settings.SPECTACULAR_SETTINGS['TITLE'],
            f'{PRODUCT_NAME} Workflow API',
        )
        html = get_template('scalar_ui.html').render({})
        self.assertIn('Masarat API Documentation', html)
        self.assertIn('/static/branding/eagle-gold.svg', html)
        self.assertNotIn('Pneumatic', html)

    def test_official_eagle_is_available_to_staticfiles(self):
        filename = finders.find('branding/eagle-gold.svg')
        self.assertTrue(filename)
        eagle = ElementTree.parse(filename).getroot()
        self.assertEqual(eagle.attrib['viewBox'], '0 0 222.63 169.56')
        style = eagle.find('{http://www.w3.org/2000/svg}defs').find(
            '{http://www.w3.org/2000/svg}style',
        )
        self.assertIn('#b9a77a', style.text)

    def test_provider_attribution_uses_product_name_only(self):
        handler = object.__new__(OpenRouterHandler)
        with patch(
            'src.ai.services.handlers.openai.OpenAIHandler._auth_headers',
            return_value={'Authorization': 'Bearer test-only'},
        ):
            headers = handler._auth_headers()
        self.assertEqual(headers, {
            'Authorization': 'Bearer test-only',
            'HTTP-Referer': 'https://example.test',
            'X-Title': PRODUCT_NAME,
        })
