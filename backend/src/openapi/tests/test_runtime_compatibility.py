"""Nullable OpenAPI metadata must not change serializer behavior."""

from copy import deepcopy
from datetime import date
from types import SimpleNamespace
from typing import Type

import pytest
from django.urls import path
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.views import APIView

from src.accounts.serializers.mixins import VacationSerializer
from src.accounts.serializers.user import (
    UserPrivilegesSerializer,
    UserSerializer,
    UserWebsocketSerializer,
)
from src.authentication.serializers import ContextUserSerializer
from src.openapi.tests.test_review_contract import _validate
from src.processes.serializers.workflows.events import TaskEventJsonSerializer
from src.processes.serializers.workflows.task import (
    TaskRevertSerializer,
    TaskSerializer,
    WorkflowCurrentTaskSerializer,
)
from src.processes.serializers.workflows.workflow import (
    WorkflowDetailsSerializer,
)

pytestmark = pytest.mark.django_db

RESPONSE_FIELDS = [
    (VacationSerializer, ('start_date', 'end_date')),
    (UserSerializer, ('vacation',)),
    (UserPrivilegesSerializer, ('vacation',)),
    (UserWebsocketSerializer, ('vacation',)),
    (ContextUserSerializer, ('vacation',)),
    (TaskEventJsonSerializer, ('output', 'fieldsets', 'sub_workflow')),
    (WorkflowCurrentTaskSerializer, ('delay',)),
    (WorkflowDetailsSerializer, ('kickoff',)),
]


def _schema_view(serializer: Type[serializers.Serializer]) -> Type[APIView]:
    class SchemaView(APIView):
        permission_classes = []

        @extend_schema(responses=serializer)
        def get(self, request: object) -> None:
            raise AssertionError('Schema generation must not call the view')

    return SchemaView


@pytest.fixture(scope='module')
def nullable_response_schema() -> tuple:
    patterns = []
    for index, (serializer, fields) in enumerate(RESPONSE_FIELDS):
        attributes = {'__module__': __name__}
        if hasattr(serializer, 'Meta'):
            projection_fields = fields
            if issubclass(serializer, UserSerializer):
                projection_fields = (*fields, 'language')
            attributes['Meta'] = type(
                'Meta', (serializer.Meta,), {'fields': projection_fields},
            )
        projection = type(
            f'Compat{serializer.__name__}', (serializer,), attributes,
        )
        view = _schema_view(projection).as_view()
        patterns.append(path(f'compat-{index}', view))
    schema = SchemaGenerator(patterns=patterns).get_schema(
        request=None, public=True,
    )
    properties = {}
    for index, (serializer, _fields) in enumerate(RESPONSE_FIELDS):
        operation = schema['paths'][f'/compat-{index}']['get']
        response = operation['responses']['200']
        reference = response['content']['application/json']['schema']['$ref']
        name = reference.rsplit('/', 1)[1]
        component = schema['components']['schemas'][name]
        properties[serializer] = component['properties']
    return schema, properties


@pytest.mark.parametrize('serializer,field_name', [
    (serializer, name)
    for serializer, names in RESPONSE_FIELDS for name in names
])
def test_nullable_response__metadata_only__runtime_flags_unchanged(
    nullable_response_schema, serializer, field_name,
) -> None:
    # arrange
    field = serializer().fields[field_name]
    document, properties = nullable_response_schema

    # act
    _validate(document, properties[serializer][field_name], None)

    # assert
    assert field.read_only is True
    assert field.allow_null is False
    assert serializer().fields[field_name].allow_null is False


@pytest.mark.parametrize('state', ['missing', 'null', 'date'])
def test_vacation_dates__original_serialization__preserved(state) -> None:
    # arrange
    values = {'absence_status': 'vacation', 'substitute_group_id': None}
    expected = {'absence_status': 'vacation', 'substitute_user_ids': []}
    if state != 'missing':
        value = None if state == 'null' else date(2026, 1, 1)
        values.update(start_date=value, end_date=value)
        rendered = None if value is None else '2026-01-01'
        expected.update(start_date=rendered, end_date=rendered)

    # act
    data = VacationSerializer(instance=SimpleNamespace(**values)).data

    # assert
    assert data == expected


@pytest.mark.parametrize('serializer', [
    UserSerializer, UserPrivilegesSerializer,
    UserWebsocketSerializer, ContextUserSerializer,
])
@pytest.mark.parametrize('missing', [True, False])
def test_vacation_relation__missing_vs_null__original_behavior(
    serializer, missing,
) -> None:
    # arrange
    projection = type('VacationProjection', (serializers.Serializer,), {
        'vacation': deepcopy(serializer().fields['vacation']),
    })
    values = {} if missing else {'vacation': None}

    # act
    data = projection(instance=values).data

    # assert
    assert data == ({} if missing else {'vacation': None})


@pytest.mark.parametrize('serializer,field_name', [
    (TaskSerializer, 'delay'), (TaskRevertSerializer, 'comment'),
])
def test_preexisting_nullable_fields__remain_unchanged(
    serializer, field_name,
) -> None:
    assert serializer().fields[field_name].allow_null is True
