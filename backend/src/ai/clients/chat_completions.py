import json
import re
import time
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
)

import requests

RETRYABLE_STATUSES = frozenset({408, 429, 500, 502, 503, 504})
MAX_ATTEMPTS = 3
BACKOFF_BASE_SEC = 0.25
DEFAULT_TIMEOUT_SEC = 120

# Not every model accepts `response_format: json_schema`; the ones that
# don't reject the request outright. We can only find out by asking.
_UNSUPPORTED_SCHEMA = re.compile(
    r'response_format|json_schema|structured',
    re.IGNORECASE,
)

# Models that ignore `response_format` still tend to wrap JSON in a
# code fence.
_JSON_FENCE = re.compile(r'```(?:json)?\s*([\s\S]*?)```')


class AIClientError(Exception):

    def __init__(
        self,
        message: str,
        status: Optional[int] = None,
        detail: str = '',
    ):
        super().__init__(message)
        self.status = status
        self.detail = detail


class AIRequestError(AIClientError):

    """The HTTP request failed, or the provider embedded an error in
    a 200 body."""


class AITruncatedOutputError(AIClientError):

    """The output was cut off by max_tokens. Retrying at the same cap
    buys the same cutoff, and half a JSON object must not reach the
    parser looking like a model mistake."""


class AIEmptyResponseError(AIClientError):

    """The provider returned a well-formed response with no content."""


class AIInvalidJsonError(AIClientError):

    """The model was asked for JSON but returned something else."""


def extract_json(content: str) -> Any:
    candidates = [content]
    fenced = _JSON_FENCE.search(content)
    if fenced:
        candidates.append(fenced.group(1))
    first = content.find('{')
    last = content.rfind('}')
    if first != -1 and last > first:
        candidates.append(content[first:last + 1])
    for candidate in candidates:
        try:
            return json.loads(candidate.strip())
        except ValueError:
            continue
    raise AIInvalidJsonError(
        f'model did not return JSON: {content[:500]}',
    )


class ChatCompletionsClient:

    """Single entry point for every model, speaking the OpenAI
    chat-completions shape. OpenRouter serves it for all providers, so
    agents differ only by their model slug; a different base_url points
    the same client at a customer-held endpoint.

    Pass `schema` to constrain the response to a JSON object and get it
    back parsed. `user_content` is a plain string, or a list of content
    blocks when the prompt carries images."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout_sec: float = DEFAULT_TIMEOUT_SEC,
        referer: Optional[str] = None,
        title: Optional[str] = None,
        max_attempts: int = MAX_ATTEMPTS,
    ):
        if not api_key:
            raise AIClientError('ChatCompletionsClient: missing api_key')
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout_sec = timeout_sec
        self.referer = referer
        self.title = title
        self.max_attempts = max_attempts
        # Usage of the last completed HTTP call: the served model name
        # and token counts. Survives truncated/empty-output errors —
        # those tokens were still consumed.
        self.last_usage: Optional[Dict] = None

    def call_model(
        self,
        model: str,
        user_content: Union[str, List[Dict]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        schema: Optional[Dict] = None,
    ) -> Any:
        if not model:
            raise AIClientError('call_model: missing model')

        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': user_content})

        use_schema = schema is not None
        last_error = None
        attempt = 1
        while attempt <= self.max_attempts:
            try:
                content = self._post_completion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    schema=schema if use_schema else None,
                )
            except (requests.Timeout, requests.ConnectionError) as ex:
                if attempt >= self.max_attempts:
                    raise
                last_error = ex
                self._backoff(attempt)
                attempt += 1
            except AIRequestError as ex:
                if use_schema and _is_unsupported_schema_error(ex):
                    # The fallback deserves a full set of attempts; the
                    # prompt asks for JSON either way, so unconstrained
                    # models still parse.
                    use_schema = False
                    continue
                if (
                    ex.status in RETRYABLE_STATUSES
                    and attempt < self.max_attempts
                ):
                    last_error = ex
                    self._backoff(attempt)
                    attempt += 1
                    continue
                raise
            else:
                if schema is not None:
                    return extract_json(content)
                return content
        raise last_error

    def _post_completion(
        self,
        model: str,
        messages: List[Dict],
        temperature: Optional[float],
        max_tokens: Optional[int],
        schema: Optional[Dict],
    ) -> str:
        headers = {'Authorization': f'Bearer {self.api_key}'}
        if self.referer:
            headers['HTTP-Referer'] = self.referer
        if self.title:
            headers['X-Title'] = self.title

        body = {'model': model, 'messages': messages}
        if temperature is not None:
            body['temperature'] = temperature
        if max_tokens is not None:
            body['max_tokens'] = max_tokens
        if schema is not None:
            body['response_format'] = {
                'type': 'json_schema',
                'json_schema': {
                    'name': 'task_output',
                    'strict': True,
                    'schema': schema,
                },
            }

        response = requests.post(
            f'{self.base_url}/chat/completions',
            headers=headers,
            json=body,
            timeout=self.timeout_sec,
        )
        if not response.ok:
            detail = response.text or ''
            raise AIRequestError(
                f'{model} request failed: '
                f'{response.status_code} {detail}'.strip(),
                status=response.status_code,
                detail=detail,
            )

        payload = response.json()

        # OpenRouter surfaces upstream provider failures in a 200 body;
        # carry the embedded code so a transient upstream 429/502 is
        # retried like a real one.
        error = payload.get('error')
        if error:
            detail = json.dumps(error)
            raise AIRequestError(
                f'{model} returned an error: {detail}',
                status=error.get('code'),
                detail=detail,
            )

        usage = payload.get('usage') or {}
        self.last_usage = {
            'model': payload.get('model'),
            'prompt_tokens': usage.get('prompt_tokens'),
            'completion_tokens': usage.get('completion_tokens'),
        }

        choices = payload.get('choices') or [{}]
        choice = choices[0]
        if choice.get('finish_reason') == 'length':
            raise AITruncatedOutputError(
                f'{model} output was cut off by max_tokens — raise '
                f'max_tokens for this agent',
            )
        content = (choice.get('message') or {}).get('content')
        if not isinstance(content, str) or not content:
            raise AIEmptyResponseError(
                f'{model} returned no content: {json.dumps(payload)}',
            )
        return content

    @staticmethod
    def _backoff(attempt: int):
        time.sleep(2 ** attempt * BACKOFF_BASE_SEC)


def _is_unsupported_schema_error(ex: AIRequestError) -> bool:
    return (
        ex.status == 400
        and bool(_UNSUPPORTED_SCHEMA.search(ex.detail or ''))
    )
