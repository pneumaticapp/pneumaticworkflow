"""Static API reference content, safe to import while settings load."""

API_DESCRIPTION = """
Use the Pneumatic API to run workflows, manage tasks, and work with files.

For operations that accept API keys, copy your key from **Integrations** and
send it as `Authorization: Bearer <api_key>`. Each operation lists its
authentication requirements.
"""

HEADER_SECURITY_SCHEMES = {
    'publicTemplateAuth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-Public-Authorization',
        'description': (
            'Public or embedded template token. Enter the complete value '
            '`Token <public_id_or_embed_id>`, including the Token prefix. '
            'Only operations allowing public template access accept it.'
        ),
    },
    'guestAuth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-Guest-Authorization',
        'description': (
            'Raw guest JWT from a guest task link; do not add Bearer. '
            'Access is restricted to the assigned task and permitted '
            'workflow operations.'
        ),
    },
}
