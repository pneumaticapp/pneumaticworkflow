from django.conf import settings
from src.ai.services.handlers.openai import OpenAIHandler


class OpenRouterHandler(OpenAIHandler):

    def _auth_headers(self) -> dict:
        headers = super()._auth_headers()
        headers['HTTP-Referer'] = settings.FRONTEND_URL
        headers['X-Title'] = 'Pneumatic'
        return headers

    def _is_chat_model(self, item: dict) -> bool:
        architecture = item.get('architecture') or {}
        output_modalities = architecture.get('output_modalities', ['text'])
        return 'text' in output_modalities
