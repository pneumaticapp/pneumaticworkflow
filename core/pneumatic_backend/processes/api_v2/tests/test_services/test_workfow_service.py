# import pytz
# import pytest
# from datetime import timedelta
# from django.utils import timezone
# from pneumatic_backend.analytics.actions import WorkflowActions
# from pneumatic_backend.processes.models import (
#     KickoffValue,
#     FieldTemplate,
#     FileAttachment,
#     Workflow,
#     Template,
#     FieldTemplateSelection,
#     ConditionTemplate,
#     RuleTemplate,
#     PredicateTemplate,
#     Predicate,
#     TaskPerformer,
#     RawDueDateTemplate,
#     WorkflowEvent,
# )
# from pneumatic_backend.processes.tests.fixtures import (
#     create_test_user,
#     create_test_template,
#     create_test_account,
#     create_test_workflow,
#     create_test_guest,
# )
# from pneumatic_backend.processes.api_v2.serializers.workflow.events import (
#     TaskEventJsonSerializer
# )
# from pneumatic_backend.utils.validation import ErrorCode
# from pneumatic_backend.processes.messages import workflow as messages
# from pneumatic_backend.processes.enums import (
#     WorkflowStatus,
#     PerformerType,
#     FieldType,
#     PredicateOperator,
#     DueDateRule,
#     WorkflowEventType,
# )
# from pneumatic_backend.processes.services.workflow_action import (
#     WorkflowActionService
# )
# from pneumatic_backend.accounts.services import (
#     UserInviteService
# )
# from pneumatic_backend.accounts.enums import (
#     SourceType,
#     BillingPlanType, Language, UserDateFormat, Timezone,
# )
# from pneumatic_backend.authentication.enums import AuthTokenType
# from pneumatic_backend.processes.enums import DirectlyStatus
# from pneumatic_backend.processes.api_v2.services.templates\
#     .integrations import TemplateIntegrationsService
# from pneumatic_backend.authentication.services import GuestJWTAuthService
# from pneumatic_backend.accounts.messages import MSG_A_0037
# from pneumatic_backend.generics.messages import MSG_GE_0007
# from pneumatic_backend.processes.messages.workflow import (
#     MSG_PW_0030,
#     MSG_PW_0028
# )
# from pneumatic_backend.processes.consts import WORKFLOW_NAME_LENGTH
# from pneumatic_backend.utils.dates import date_format
# from pneumatic_backend.processes.api_v2.services import WorkflowService
#
#
# pytestmark = pytest.mark.django_db

#
# def test_create_instance__name_too_long__string_abbreviation(mocker):
#
#     long_name = 'a' * (WORKFLOW_NAME_LENGTH + 1)
#     short_name = f'{"a"* WORKFLOW_NAME_LENGTH}...'
#
# def test_create_kickoff(self, mocker):
#
#     user = create_test_user()
#     template = create_test_template(user, is_active=True)
#     kickoff_field = FieldTemplate.objects.create(
#         name='Kickoff name',
#         type=FieldType.STRING,
#         kickoff=template.kickoff_instance,
#         template=template,
#     )
#
#     task = template.tasks.get(number=1)
#     task.description = 'With kickoff {{%s}}' % kickoff_field.api_name
#     task.save()
#
#     data = {
#         'template': template.id,
#         'name': 'Process name',
#         'kickoff': {
#             kickoff_field.api_name: 'kick'
#         }
#     }
#     serializer = slz(
#         data=data,
#         context={
#             'user': user,
#             'account': user.account
#         }
#     )
#     serializer.is_valid(raise_exception=True)
#     workflow = serializer.save()
#
#     task = workflow.current_task_instance
#
#     assert task.description == 'With kickoff kick'
#
# def test_create_kickoff_data_not_provided_on_required(self, mocker):
#
#     user = create_test_user()
#     template = create_test_template(user, is_active=True)
#     kickoff_field = FieldTemplate.objects.create(
#         name='Kickoff name',
#         type=FieldType.STRING,
#         kickoff=template.kickoff_instance,
#         is_required=True,
#         template=template,
#     )
#
#     task = template.tasks.get(number=1)
#     task.description = 'With kickoff {{%s}}' % kickoff_field.api_name
#     task.save()
#
#     name = 'Process name'
#     data = {
#         'template': template.id,
#         'name': name,
#         'kickoff': {
#             kickoff_field.api_name: None
#         }
#     }
#     serializer = slz(
#         data=data,
#         context={
#             'user': user,
#             'account': user.account
#         }
#     )
#     serializer.is_valid(raise_exception=True)
#     with pytest.raises(ValidationError) as ex:
#         serializer.save()
#
#     # assert
#     assert ex.value.detail['code'] == ErrorCode.VALIDATION_ERROR
#     assert ex.value.detail['message'] == messages.MSG_PW_0023
#     assert ex.value.detail['details']['reason'] == messages.MSG_PW_0023
#     assert ex.value.detail['details']['api_name'] == (
#         kickoff_field.api_name
#     )
#
# def test_create_kickoff_field_required(self, mocker):
#
#     user = create_test_user()
#     template = create_test_template(user, is_active=True)
#     kickoff_field = FieldTemplate.objects.create(
#         name='Kickoff name',
#         type=FieldType.STRING,
#         kickoff=template.kickoff_instance,
#         is_required=True,
#         template=template,
#     )
#
#     task = template.tasks.get(number=1)
#     task.description = 'With kickoff {{%s}}' % kickoff_field.api_name
#
#     name = 'Process name'
#     data = {
#         'template': template.id,
#         'name': name
#     }
#     serializer = slz(
#         data=data,
#         context={
#             'user': user,
#             'account': user.account
#         }
#     )
#     serializer.is_valid(raise_exception=True)
#     with pytest.raises(ValidationError) as ex:
#         serializer.save()
#
#     # assert
#     assert ex.value.detail['code'] == ErrorCode.VALIDATION_ERROR
#     assert ex.value.detail['message'] == messages.MSG_PW_0023
#     assert ex.value.detail['details']['reason'] == messages.MSG_PW_0023
#     assert ex.value.detail['details']['api_name'] == (
#         kickoff_field.api_name
#     )
#
# def test_create_kickoff_field_string_value_invalid(self, mocker):
#
#     user = create_test_user()
#     template = create_test_template(user, is_active=True)
#     kickoff_field = FieldTemplate.objects.create(
#         name='Kickoff name',
#         type=FieldType.STRING,
#         kickoff=template.kickoff_instance,
#         template=template,
#     )
#
#     task = template.tasks.get(number=1)
#     task.description = 'With kickoff {{%s}}' % kickoff_field.api_name
#
#     name = 'Process name'
#     data = {
#         'template': template.id,
#         'name': name,
#         'kickoff': {
#             kickoff_field.api_name: (
#                 'Some text that much more than 140 '
#                 'digits and can not be validate by '
#                 'function of validation for string '
#                 'types of kickoff. Must raise '
#                 'exception.'
#             )
#         }
#     }
#     serializer = slz(
#         data=data,
#         context={
#             'user': user,
#             'account': user.account
#         }
#     )
#     serializer.is_valid(raise_exception=True)
#     with pytest.raises(ValidationError) as ex:
#         serializer.save()
#
#     # assert
#     message = messages.MSG_PW_0026(140)
#     assert ex.value.detail['code'] == ErrorCode.VALIDATION_ERROR
#     assert ex.value.detail['message'] == message
#     assert ex.value.detail['details']['reason'] == message
#     assert ex.value.detail['details']['api_name'] == (
#         kickoff_field.api_name
#     )
#
# def test_create_kickoff_checkbox__ok(self, mocker):
#
#     user = create_test_user()
#     template = create_test_template(user, is_active=True)
#     kickoff_field = FieldTemplate.objects.create(
#         name='Kickoff name',
#         type=FieldType.CHECKBOX,
#         kickoff=template.kickoff_instance,
#         template=template,
#     )
#     checkbox_one = FieldTemplateSelection.objects.create(
#         value='much',
#         field_template=kickoff_field,
#         template=template,
#     )
#     checkbox_two = FieldTemplateSelection.objects.create(
#         value='congratulations',
#         field_template=kickoff_field,
#         template=template,
#     )
#
#     task = template.tasks.get(number=1)
#     task.description = 'With kickoff {{%s}}' % kickoff_field.api_name
#     task.save()
#
#     data = {
#         'template': template.id,
#         'name': 'Process name',
#         'kickoff': {
#             kickoff_field.api_name: [
#                 checkbox_one.api_name,
#                 checkbox_two.api_name
#             ]
#         }
#     }
#     serializer = slz(
#         data=data,
#         context={
#             'user': user,
#             'account': user.account
#         }
#     )
#     serializer.is_valid(raise_exception=True)
#     workflow = serializer.save()
#
#     task = workflow.current_task_instance
#
#     assert task.description == 'With kickoff much, congratulations'
#
# def test_create_kickoff_checkbox_wrong_ids(self, mocker):
#
#     user = create_test_user()
#     template = create_test_template(user, is_active=True)
#     kickoff_field = FieldTemplate.objects.create(
#         name='Kickoff name',
#         type=FieldType.CHECKBOX,
#         kickoff=template.kickoff_instance,
#         template=template,
#     )
#     checkbox_one = FieldTemplateSelection.objects.create(
#         value='much',
#         field_template=kickoff_field,
#         template=template,
#     )
#     FieldTemplateSelection.objects.create(
#         value='congratulations',
#         field_template=kickoff_field,
#         template=template,
#     )
#
#     task = template.tasks.get(number=1)
#     task.description = 'With kickoff {{%s}}' % kickoff_field.api_name
#     task.save()
#
#     data = {
#         'template': template.id,
#         'name': 'Process name',
#         'kickoff': {
#             kickoff_field.api_name: [checkbox_one.api_name, 123]
#         }
#     }
#     serializer = slz(
#         data=data,
#         context={
#             'user': user,
#             'account': user.account
#         }
#     )
#     serializer.is_valid(raise_exception=True)
#     with pytest.raises(ValidationError) as ex:
#         serializer.save()
#
#     # assert
#     assert ex.value.detail['code'] == ErrorCode.VALIDATION_ERROR
#     assert ex.value.detail['message'] == messages.MSG_PW_0030
#     assert ex.value.detail['details']['reason'] == messages.MSG_PW_0030
#     assert ex.value.detail['details']['api_name'] == (
#         kickoff_field.api_name
#     )
#
# def test_create_kickoff_radio_in_text__ok(self, mocker):
#
#     user = create_test_user()
#     template = create_test_template(user, is_active=True)
#     kickoff_field = FieldTemplate.objects.create(
#         name='Kickoff name',
#         type=FieldType.RADIO,
#         kickoff=template.kickoff_instance,
#         template=template,
#     )
#     selection = FieldTemplateSelection.objects.create(
#         value='much',
#         field_template=kickoff_field,
#         template=template,
#     )
#
#     task = template.tasks.get(number=1)
#     task.description = 'With kickoff {{%s}}' % kickoff_field.api_name
#     task.save()
#
#     data = {
#         'template': template.id,
#         'name': 'Process name',
#         'kickoff': {
#             kickoff_field.api_name: selection.api_name
#         }
#     }
#     serializer = slz(
#         data=data,
#         context={
#             'user': user,
#             'account': user.account
#         }
#     )
#     serializer.is_valid(raise_exception=True)
#     workflow = serializer.save()
#
#     task = workflow.current_task_instance
#
#     assert task.description == 'With kickoff much'
#
# def test_create_kickoff_radio_wrong_api_name__validation_error(
#     self,
#     mocker
# ):
#
#     user = create_test_user()
#     template = create_test_template(user, is_active=True)
#     kickoff_field = FieldTemplate.objects.create(
#         name='Kickoff name',
#         type=FieldType.RADIO,
#         kickoff=template.kickoff_instance,
#         template=template,
#     )
#     FieldTemplateSelection.objects.create(
#         value='much',
#         field_template=kickoff_field,
#         template=template,
#     )
#
#     task = template.tasks.get(number=1)
#     task.description = 'With kickoff {{%s}}' % kickoff_field.api_name
#     task.save()
#
#     data = {
#         'template': template.id,
#         'name': 'Process name',
#         'kickoff': {
#             kickoff_field.api_name: 'wrong-api-name'
#         }
#     }
#     serializer = slz(
#         data=data,
#         context={
#             'user': user,
#             'account': user.account
#         }
#     )
#     serializer.is_valid(raise_exception=True)
#     with pytest.raises(ValidationError) as ex:
#         serializer.save()
#
#     # assert
#     assert ex.value.detail['code'] == ErrorCode.VALIDATION_ERROR
#     assert ex.value.detail['message'] == messages.MSG_PW_0028
#     assert ex.value.detail['details']['reason'] == messages.MSG_PW_0028
#     assert ex.value.detail['details']['api_name'] == (
#         kickoff_field.api_name
#     )
#
# def test_create_kickoff_date(self, mocker):
#
#     user = create_test_user()
#     template = create_test_template(user, is_active=True)
#     kickoff_field = FieldTemplate.objects.create(
#         name='Kickoff name',
#         type=FieldType.DATE,
#         kickoff=template.kickoff_instance,
#         template=template,
#     )
#
#     task = template.tasks.get(number=1)
#     task.description = 'With kickoff {{%s}}' % kickoff_field.api_name
#     task.save()
#
#     data = {
#         'template': template.id,
#         'name': 'Process name',
#         'kickoff': {
#             kickoff_field.api_name: '06/25/2020'
#         }
#     }
#     serializer = slz(
#         data=data,
#         context={
#             'user': user,
#             'account': user.account
#         }
#     )
#     serializer.is_valid(raise_exception=True)
#     workflow = serializer.save()
#
#     task = workflow.current_task_instance
#
#     assert task.description == 'With kickoff 06/25/2020'
#
# def test_create_kickoff_date_wrong_format(self, mocker):
#
#     user = create_test_user()
#     template = create_test_template(user, is_active=True)
#     kickoff_field = FieldTemplate.objects.create(
#         name='Kickoff name',
#         type=FieldType.DATE,
#         kickoff=template.kickoff_instance,
#         template=template,
#     )
#
#     task = template.tasks.get(number=1)
#     task.description = 'With kickoff {{%s}}' % kickoff_field.api_name
#     task.save()
#
#     data = {
#         'template': template.id,
#         'name': 'Process name',
#         'kickoff': {
#             kickoff_field.api_name: '2020-13-25'
#         }
#     }
#     serializer = slz(
#         data=data,
#         context={
#             'user': user,
#             'account': user.account
#         }
#     )
#     serializer.is_valid(raise_exception=True)
#     with pytest.raises(ValidationError) as ex:
#         serializer.save()
#
#     # assert
#     assert ex.value.detail['code'] == ErrorCode.VALIDATION_ERROR
#     assert ex.value.detail['message'] == messages.MSG_PW_0033
#     assert ex.value.detail['details']['reason'] == messages.MSG_PW_0033
#     assert ex.value.detail['details']['api_name'] == (
#         kickoff_field.api_name
#     )
#
# def test_create_kickoff_url(self, mocker):
#
#     user = create_test_user()
#     template = create_test_template(user, is_active=True)
#     kickoff_field = FieldTemplate.objects.create(
#         name='Kickoff name',
#         type=FieldType.URL,
#         kickoff=template.kickoff_instance,
#         template=template,
#     )
#
#     task = template.tasks.get(number=1)
#     task.description = 'With kickoff {{%s}}' % kickoff_field.api_name
#     task.save()
#
#     data = {
#         'template': template.id,
#         'name': 'Process name',
#         'kickoff': {
#             kickoff_field.api_name: 'https://pneumatic.app'
#         }
#     }
#     serializer = slz(
#         data=data,
#         context={
#             'user': user,
#             'account': user.account
#         }
#     )
#     serializer.is_valid(raise_exception=True)
#     workflow = serializer.save()
#
#     task = workflow.current_task_instance
#     expected = (
#         f'With kickoff [{kickoff_field.name}]'
#         f'(https://pneumatic.app)'
#     )
#     assert task.description == expected
#
# def test_create_kickoff_wrong_url(self, mocker):
#
#     user = create_test_user()
#     template = create_test_template(user, is_active=True)
#     kickoff_field = FieldTemplate.objects.create(
#         name='Kickoff name',
#         type=FieldType.URL,
#         kickoff=template.kickoff_instance,
#         template=template,
#     )
#
#     task = template.tasks.get(number=1)
#     task.description = 'With kickoff {{%s}}' % kickoff_field.api_name
#     task.save()
#
#     data = {
#         'template': template.id,
#         'name': 'Process name',
#         'kickoff': {
#             kickoff_field.api_name: 'some body once told me'
#         }
#     }
#     serializer = slz(
#         data=data,
#         context={
#             'user': user,
#             'account': user.account
#         }
#     )
#     serializer.is_valid(raise_exception=True)
#     with pytest.raises(ValidationError) as ex:
#         serializer.save()
#
#     # assert
#     assert ex.value.detail['code'] == ErrorCode.VALIDATION_ERROR
#     assert ex.value.detail['message'] == messages.MSG_PW_0035
#     assert ex.value.detail['details']['reason'] == messages.MSG_PW_0035
#     assert ex.value.detail['details']['api_name'] == (
#         kickoff_field.api_name
#     )
#
# def test_create_task_output(self, mocker):
#     # arrange
#
#     user = create_test_user()
#     template = create_test_template(user, is_active=True)
#     task = template.tasks.get(number=1)
#     output_field = FieldTemplate.objects.create(
#         name='Field name',
#         type=FieldType.RADIO,
#         task=task,
#         is_required=True,
#         template=template,
#     )
#     FieldTemplateSelection.objects.create(
#         field_template=output_field,
#         value='First',
#         template=template,
#     )
#     FieldTemplateSelection.objects.create(
#         field_template=output_field,
#         value='Second',
#         template=template,
#     )
#
#     data = {
#         'template': template.id,
#         'name': 'Process name',
#     }
#     serializer = slz(
#         data=data,
#         context={
#             'user': user,
#             'account': user.account
#         }
#     )
#     serializer.is_valid(raise_exception=True)
#
#     # act
#     workflow = serializer.save()
#
#     # assert
#     task = workflow.current_task_instance
#     task_output = task.output.first()
#
#     assert task_output.is_required == output_field.is_required
#     assert task_output.name == output_field.name
#     assert task_output.type == output_field.type
#     assert task_output.selections.count() == 2
#
# def test_create_workflow_starter(self, mocker):
#
#         user = create_test_user()
#         template = create_test_template(user, is_active=True)
#         first_task = template.tasks.get(number=1)
#         first_task.description = 'Some description'
#         first_task.delete_raw_performers()
#         first_task.add_raw_performer(
#             performer_type=PerformerType.WORKFLOW_STARTER
#         )
#         first_task.save()
#         data = {
#             'template': template.id,
#             'name': 'Valar dahaeris'
#         }
#         serializer = slz(
#             data=data,
#             context={
#                 'user': user,
#                 'account': user.account
#             }
#         )
#         serializer.is_valid(raise_exception=True)
#         workflow = serializer.save()
#         task = workflow.current_task_instance
#
#         assert workflow.template == template
#         assert workflow.tasks_count == template.tasks_count
#         assert task.description_template == first_task.description
#         assert task.performers.first() == user
