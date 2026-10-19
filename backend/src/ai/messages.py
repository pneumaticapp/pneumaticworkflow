from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

MSG_AI_0001 = _('Connection to AI provider failed.')
MSG_AI_0002 = _('AI provider request failed.')
MSG_AI_0003 = _('Failed to parse AI provider response.')
MSG_AI_0004 = _('An AI agent with this name already exists.')
MSG_AI_0005 = _('Cannot delete an AI provider that is used by AI agents.')
MSG_AI_0006 = lambda error: format_lazy(
    _(
        'Failed to get the models list ({error}), '
        'the vendor may not be compatible with the OpenAI protocol.',
    ),
    error=error,
)
MSG_AI_0007 = lambda error: format_lazy(
    _(
        'Failed to execute the chat request ({error}), '
        'the vendor may not be compatible with the OpenAI protocol.',
    ),
    error=error,
)
MSG_AI_0008 = lambda model: format_lazy(
    _('The request to the model "{model}" returned an empty response.'),
    model=model,
)
MSG_AI_0009 = lambda attempts, report: format_lazy(
    _(
        'I could not complete the task in {attempts} attempts: '
        'my answer did not pass the validation. '
        'The details are in the report {report}',
    ),
    attempts=attempts,
    report=report,
)
MSG_AI_0010 = lambda attempts: format_lazy(
    _('The agent failed to complete the task in {attempts} attempts.'),
    attempts=attempts,
)
MSG_AI_0011 = lambda attempts, error: format_lazy(
    _(
        'I could not complete the task in {attempts} attempts. '
        'Please complete it manually or check the agent provider settings. '
        'Error: {error}',
    ),
    attempts=attempts,
    error=error,
)
MSG_AI_0012 = lambda reason: format_lazy(
    _('The AI provider blocked the request ({reason}).'),
    reason=reason,
)
MSG_AI_0013 = lambda attempts, error: format_lazy(
    _(
        'I could not reply to the comment in {attempts} attempts. '
        'Error: {error}',
    ),
    attempts=attempts,
    error=error,
)
MSG_AI_0014 = _(
    'None of the provider models responded to the test request. '
    'Check the provider settings.',
)
MSG_AI_0015 = lambda model: format_lazy(
    _(
        'The selected model "{model}" returned an error. '
        'Try choosing another model.',
    ),
    model=model,
)
MSG_AI_0016 = lambda error: format_lazy(
    _(
        'The AI provider rejected the credentials. Error: {error}',
    ),
    error=error,
)
MSG_AI_0017 = lambda error: format_lazy(
    _(
        'The AI provider denied access to the requested resource. '
        'Error: {error}',
    ),
    error=error,
)
MSG_AI_0018 = _(
    'The provider address is not allowed: '
    'only public internet addresses can be used.',
)
