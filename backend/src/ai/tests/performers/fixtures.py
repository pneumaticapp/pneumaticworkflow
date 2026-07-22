"""Fixture shaped like the runtime task output-field descriptions —
carries ``is_hidden`` and renders choice selections as display-value
strings, which is also what task completion expects back. Ported from
the ai-performer demo's test fixtures (validated live against the
Pneumatic API)."""

from src.ai.performers.output_fields import (
    is_fillable,
    resolve_output_fields,
)

TASK_OUTPUT = [
    {
        'api_name': 'f-text', 'name': 'Comments', 'type': 'text',
        'is_required': False, 'is_hidden': False, 'description': '',
        'selections': [],
    },
    {
        'api_name': 'f-str', 'name': 'Version', 'type': 'string',
        'is_required': True, 'is_hidden': False, 'description': '',
        'selections': [],
    },
    {
        'api_name': 'f-url', 'name': 'PR link', 'type': 'url',
        'is_required': False, 'is_hidden': False, 'description': '',
        'selections': [],
    },
    {
        'api_name': 'f-date', 'name': 'Due', 'type': 'date',
        'is_required': False, 'is_hidden': False, 'description': '',
        'selections': [],
    },
    {
        'api_name': 'f-num', 'name': 'Score', 'type': 'number',
        'is_required': False, 'is_hidden': False, 'description': '',
        'selections': [],
    },
    {
        'api_name': 'f-radio', 'name': 'Ready?', 'type': 'radio',
        'is_required': True, 'is_hidden': False, 'description': '',
        'selections': ['Yes', 'No'],
    },
    {
        'api_name': 'f-opt-radio', 'name': 'Mood', 'type': 'radio',
        'is_required': False, 'is_hidden': False, 'description': '',
        'selections': ['Good', 'Bad'],
    },
    {
        'api_name': 'f-check', 'name': 'Options', 'type': 'checkbox',
        'is_required': False, 'is_hidden': False, 'description': '',
        'selections': ['Skip review', 'Notify'],
    },
    {
        'api_name': 'f-file', 'name': 'Report', 'type': 'file',
        'is_required': False, 'is_hidden': False, 'description': '',
        'selections': [],
    },
    {
        'api_name': 'f-hidden', 'name': 'Hidden', 'type': 'text',
        'is_required': True, 'is_hidden': True, 'description': '',
        'selections': [],
    },
]


def fillable_fields():
    return [
        field for field in resolve_output_fields(TASK_OUTPUT)
        if is_fillable(field)
    ]
