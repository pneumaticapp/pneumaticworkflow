"""Exercise the actual browser merge, including the 3.1/3.0 boundary."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from drf_spectacular.validation import validate_schema


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js required')
def test_scalar_merge__nullable_examples_and_refs__valid():
    # arrange
    template = Path(__file__).resolve().parents[2] / 'templates/scalar_ui.html'
    core = {
        'openapi': '3.0.3',
        'info': {'title': 'Core', 'version': '1'},
        'paths': {},
        'components': {'schemas': {'Error': {'type': 'object'}}},
    }
    files = {
        'openapi': '3.1.0',
        'security': [{'tokenAuth': []}],
        'components': {
            'securitySchemes': {
                'tokenAuth': {
                    'type': 'http',
                    'scheme': 'bearer',
                },
            },
            'schemas': {
                'Error': {
                    'type': 'object',
                    'properties': {
                        'details': {
                            'anyOf': [
                                {'$ref': '#/components/schemas/Details'},
                                {'type': 'null'},
                            ],
                        },
                    },
                },
                'Details': {'type': 'object'},
            },
        },
        'paths': {
            '/files/download': {
                'get': {
                    'parameters': [
                        {
                            'name': 'Range',
                            'in': 'header',
                            'schema': {
                                'anyOf': [
                                    {'type': 'string'},
                                    {'type': 'null'},
                                ],
                                'examples': ['bytes=0-1023'],
                            },
                        },
                    ],
                    'responses': {
                        '200': {
                            'description': 'File',
                            'content': {
                                'application/octet-stream': {
                                    'schema': {
                                        'type': 'string',
                                        'format': 'binary',
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    }
    program = r"""
const fs = require('fs');
const vm = require('vm');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const html = fs.readFileSync(input.template, 'utf8');
const source = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const context = {};
vm.createContext(context);
vm.runInContext(source.slice(0, source.lastIndexOf('\n      loadSchema()')),
                context);
process.stdout.write(JSON.stringify(context.mergeSchemas(input.core,
                                                       input.files)));
"""

    # act
    result = subprocess.run(
        [shutil.which('node'), '-e', program],
        input=json.dumps(
            {
                'template': str(template),
                'core': core,
                'files': files,
            },
        ),
        text=True,
        capture_output=True,
        check=True,
        timeout=15,
    )
    merged = json.loads(result.stdout)

    # assert
    validate_schema(merged)
    parameter = merged['paths']['/files/download']['get']['parameters'][0]
    assert parameter['schema'] == {
        'type': 'string',
        'nullable': True,
        'example': 'bytes=0-1023',
    }
    details = merged['components']['schemas']['FilesError']['properties'][
        'details'
    ]
    assert details['anyOf'] == [
        {'$ref': '#/components/schemas/Details'},
        {'type': 'object', 'nullable': True, 'enum': [None]},
    ]
    assert merged['paths']['/files/download']['get']['security'] == [
        {'tokenAuth': []},
    ]
