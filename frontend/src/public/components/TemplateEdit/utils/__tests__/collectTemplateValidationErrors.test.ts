import { collectTemplateValidationErrors } from '../collectTemplateValidationErrors';
import { initialTemplate } from '../../../../redux/template/reducer';
import { intlMock } from '../../../../__stubs__/intlMock';
import { makeExtraField } from '../../../../__stubs__/fields.factory';
import { makeFieldsetBindingClient } from '../../../../__stubs__/fieldsets.factory';
import { makeKickoffClient, makeTemplateTaskClient } from '../../../../__stubs__/templates.factory';
import { ETaskFormParts } from '../../types';
import { EConditionAction, EConditionLogicOperations, EConditionOperators } from '../../TaskForm/Conditions/types';
import { EExtraFieldType, ETaskPerformerType, ITemplateClient } from '../../../../types/template';

const performer = { apiName: 'performer-1', label: 'Ann', type: ETaskPerformerType.User, sourceId: '1' };

const makeTemplate = (overrides: Partial<ITemplateClient>): ITemplateClient => ({
  ...initialTemplate.data,
  ...overrides,
});

const formatMessage = intlMock.formatMessage;

describe('collectTemplateValidationErrors', () => {
  it('returns no errors for a valid template', () => {
    const template = makeTemplate({ tasks: [makeTemplateTaskClient({ rawPerformers: [performer] })] });

    expect(collectTemplateValidationErrors(template, formatMessage)).toEqual([]);
  });

  it('locates invalid kickoff fields and fieldsets', () => {
    const template = makeTemplate({
      kickoff: makeKickoffClient({
        fields: [makeExtraField({ apiName: 'field-empty-name', name: '', type: EExtraFieldType.String })],
        fieldsets: [makeFieldsetBindingClient({ apiNameBinding: 'fieldset-1', title: '' })],
      }),
      tasks: [makeTemplateTaskClient({ rawPerformers: [performer] })],
    });

    expect(
      collectTemplateValidationErrors(template, formatMessage).map(({ apiName, message, target }) => ({
        apiName,
        message,
        target,
      })),
    ).toEqual([
      {
        apiName: 'field-empty-name',
        message: formatMessage({ id: 'validation.kickoff-form-field-name-empty' }),
        target: { taskUuid: null, section: null, elementApiName: 'field-empty-name' },
      },
      {
        apiName: 'fieldset-1',
        message: formatMessage({ id: 'validation.fieldset-title-empty' }),
        target: { taskUuid: null, section: null, elementApiName: 'fieldset-1' },
      },
    ]);
  });

  it('opens performers for a task without performers and locates incomplete conditions in task order', () => {
    const first = makeTemplateTaskClient({ apiName: 'task-1', uuid: 'uuid-1', number: 1, rawPerformers: [] });
    const second = makeTemplateTaskClient({
      apiName: 'task-2',
      uuid: 'uuid-2',
      number: 2,
      rawPerformers: [performer],
      conditions: [
        {
          apiName: 'condition-1',
          order: 0,
          action: EConditionAction.SkipTask,
          rules: [
            {
              ruleApiName: 'rule-1',
              predicateApiName: 'predicate-1',
              logicOperation: EConditionLogicOperations.And,
              field: 'field-1',
              fieldType: EExtraFieldType.String,
              operator: EConditionOperators.Equal,
              value: '',
            },
          ],
        },
      ],
    });
    const template = makeTemplate({ tasks: [second, first] });

    expect(collectTemplateValidationErrors(template, formatMessage).map(({ target }) => target)).toEqual([
      { taskUuid: 'uuid-1', section: ETaskFormParts.AssignPerformers, elementApiName: 'task-1' },
      { taskUuid: 'uuid-2', section: ETaskFormParts.CheckIf, elementApiName: 'predicate-1' },
    ]);
  });
});
